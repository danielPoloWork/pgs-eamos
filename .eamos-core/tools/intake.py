#!/usr/bin/env python3
"""EAMOS intake — the source-reorganization primitive (RFC-0002 §6; RFC-0001 §15-M5).

Dependency-free (stdlib + yamlmini). The foundational half of intake: ingest provided material and
**normalize it into the typed inputs ledger** — dedupe, tag by source, mark every cell `sourced` —
so the manifest's numbers come from material, never hand-entry. The output is a paste-ready
`inputs:` block (RFC-0001 §6). Connectors (Jira / Notion / Sheets) and a foreign-deck extractor are
later additions; the structured sources here are a **pasted KPI table** (CSV) and the **prior
instance** (the series store — the prior deck's data, RFC-0001 §9).

    python tools/intake.py --csv examples/intake/q3-kpis.csv --series build/series.json --out build/ledger.yaml

Dedup rule: the **current** source (CSV) wins over the prior one (series); prior fills gaps. Every
emitted cell is `provided: true, provenance: sourced` — assumed values are added later, by hand,
only where material is genuinely missing (RFC-0001 §6).
"""

import argparse
import csv
import json
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import _cli      # noqa: E402  (utf8_stdio, #54)
import yamlmini  # noqa: E402
import render    # noqa: E402  (shared loaders for the intake taxonomy / question tree / routing)


def _titleize(key):
    return key.split(".", 1)[-1].replace("_", " ").replace("-", " ").strip().capitalize()


def from_csv(path):
    """A pasted/exported KPI table -> cells. Header (case-insensitive): key,value[,label,source]."""
    cells = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        norm = {(k or "").strip().lower(): k for k in (reader.fieldnames or [])}
        if "key" not in norm or "value" not in norm:
            raise ValueError(f"{path}: CSV needs at least 'key' and 'value' columns")
        for row in reader:
            key = (row[norm["key"]] or "").strip()
            if not key:
                continue
            cells[key] = {
                "label": (row.get(norm.get("label", ""), "") or "").strip() or _titleize(key),
                "value": (row[norm["value"]] or "").strip(),
                "source": (row.get(norm.get("source", ""), "") or "").strip() or f"{os.path.basename(path)} (pasted table)",
                "via": "intake/csv",
            }
    return cells


def from_series(path):
    """The prior instance's KPIs (the series store, RFC-0001 §9) -> cells (the prior deck's data)."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        store = json.load(fh)
    series_id = store.get("series_id", "series")
    instances = store.get("instances", []) or []
    cells = {}
    for key, hist in (store.get("kpi_history", {}) or {}).items():
        prior = next((i for i in reversed(instances) if i in hist), None)
        if prior is None:
            continue
        cells[key] = {"label": _titleize(key), "value": str(hist[prior]),
                      "source": f"prior instance {series_id}@{prior}", "via": "intake/series"}
    return cells


def _slug(label):
    return "kpi." + (re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "x")


def from_deck(path):
    """An uploaded .pptx deck -> cells (the foreign-deck connector). Optional: needs python-pptx
    (the cosmetic dep); the CSV/series sources stay dependency-free. Extracts 'Label: value' lines
    whose value looks like a metric; marked/assumed values (⟨…⟩) are skipped, not re-imported."""
    try:
        from pptx import Presentation
    except ImportError:
        raise SystemExit("intake --deck needs python-pptx (pip install python-pptx); "
                         "the --csv / --series sources are dependency-free.")
    cells = {}
    for slide in Presentation(path).slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                line = "".join(r.text for r in para.runs).strip().lstrip("•-– ").strip()
                m = re.match(r"^(.+?):\s+(.+)$", line)
                if not m:
                    continue
                value = re.split(r"\s*\(", m.group(2))[0].strip()       # drop a trailing "(target: …)"
                if not re.match(r"^[~<>]?\s*\d", value) or len(value) > 24:
                    continue                                            # value must look metric-like
                cells[_slug(m.group(1).strip())] = {
                    "label": m.group(1).strip(), "value": value,
                    "source": f"{os.path.basename(path)} (uploaded deck)", "via": "intake/deck"}
    return cells


def reorganize(csv_paths, series_path, deck_paths=None):
    """Merge sources into one normalized ledger. Precedence (later wins): series → deck → csv — the
    prior instance fills gaps, an uploaded deck refines, the pasted table is authoritative."""
    ledger, prov = {}, {"overridden": 0}
    sources = (("series", from_series, [series_path] if series_path else []),
               ("deck", from_deck, deck_paths or []),
               ("csv", from_csv, csv_paths or []))
    for _name, fn, paths in sources:
        for p in paths:
            for key, cell in fn(p).items():
                if key in ledger:
                    prov["overridden"] += 1
                ledger[key] = cell                   # later source wins (dedupe)
    prov["gap_filled"] = sum(1 for c in ledger.values() if c["via"] == "intake/series")
    return ledger, prov


def select_questions(classification, tree, routing):
    """Phase-C adaptive selection (RFC-0003, #28). Deterministic, pure (no IO/clock/randomness):
    resolve the interview DEPTH from the classification (the `by_complexity` base, raised to
    `architecture` if an `escalate_to_architecture` rule matches), then return the `common` + the
    cluster's questions whose `level` is at or below that depth, in level order. Returns (depth, [q])."""
    levels = tree.get("levels", []) or []
    cluster = (classification or {}).get("cluster")
    depth = (routing.get("by_complexity", {}) or {}).get((classification or {}).get("complexity"))
    for rule in (routing.get("escalate_to_architecture", []) or []):
        if (rule.get("cluster") == cluster
                and rule.get("decision_risk") == (classification or {}).get("decision_risk")):
            depth = "architecture"
            break
    max_i = levels.index(depth) if depth in levels else (len(levels) - 1 if levels else 0)
    picked = list(tree.get("common", []) or []) + list((tree.get("clusters", {}) or {}).get(cluster, []) or [])
    sel = [q for q in picked if isinstance(q, dict) and q.get("level") in levels
           and levels.index(q["level"]) <= max_i]
    sel.sort(key=lambda q: levels.index(q["level"]))   # stable: keep authoring order within a level
    return depth, sel


def questions_op(manifest_path):
    """Print the adaptive question set for a classified manifest — the Phase-C interview script for
    the #32 'targeted questions' phase. The agent asks these; the human answers (-> discovery_intake)."""
    with open(manifest_path, encoding="utf-8") as fh:
        m = yamlmini.load_yaml(fh.read())
    di = m.get("discovery_intake") or {}
    cls = di.get("classification") if isinstance(di, dict) else None
    if not isinstance(cls, dict) or not cls.get("cluster"):
        print("intake --questions: the manifest has no discovery_intake.classification "
              "(classify it first — Phase B, #27).")
        return 1
    depth, sel = select_questions(cls, render.load_questions(), render.load_routing())
    out = [f"# Targeted questions — {cls.get('cluster')} "
           f"(complexity {cls.get('complexity')} · decision-risk {cls.get('decision_risk')} · depth: {depth})", ""]
    out += [f"- [{q.get('level')}] {q.get('ask')}" for q in sel]
    sys.stdout.write("\n".join(out) + "\n")
    return 0


def emit_yaml(ledger):
    out = ["# Generated by intake.py — paste into a manifest's `inputs:` (RFC-0001 §6). Zero hand-entry.",
           "inputs:"]
    for key in sorted(ledger):
        c = ledger[key]
        out.append(f"  {key}:")
        out.append(f'    label: "{c["label"]}"')
        out.append(f'    value: "{c["value"]}"')
        out.append("    provided: true")
        out.append(f'    source: "{c["source"]}"')
        out.append("    provenance: sourced")
        out.append(f"    via: {c['via']}")
    return "\n".join(out) + "\n"


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    ap = argparse.ArgumentParser(description="Reorganize provided material into a typed inputs ledger.")
    ap.add_argument("--csv", action="append", help="a pasted/exported KPI table (repeatable)")
    ap.add_argument("--series", help="a series store JSON (the prior instance's data)")
    ap.add_argument("--deck", action="append", help="an uploaded .pptx deck (needs python-pptx)")
    ap.add_argument("--out", help="output path for the YAML inputs fragment (default: stdout)")
    ap.add_argument("--questions", metavar="MANIFEST",
                    help="Phase C (RFC-0003): print the adaptive question set for a classified manifest")
    args = ap.parse_args()
    if args.questions:
        return questions_op(args.questions)
    if not (args.csv or args.series or args.deck):
        ap.error("provide at least one source: --csv, --series, and/or --deck (or --questions <manifest>)")

    ledger, prov = reorganize(args.csv, args.series, args.deck)
    text = emit_yaml(ledger)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"intake: OK — {len(ledger)} sourced cells -> {args.out} "
              f"({prov['overridden']} deduped, {prov['gap_filled']} from prior instance)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
