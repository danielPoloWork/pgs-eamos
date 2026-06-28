#!/usr/bin/env python3
"""EAMOS render: meeting manifest + archetype profile -> deterministic deck-IR (RFC-0001 §5).

Dependency-free (stdlib + the shared yamlmini loader). The determinism boundary lives here: this
step is reproducible and gate-checkable; the cosmetic IR -> binary hop (emit_*.py) is downstream.

    python tools/render.py orchestrator/examples/qbr-c-level.yaml --out build/deck-ir.json

Pipeline: compose the structure from the archetype (applying altitude shaping), resolve every
binding against the manifest's typed inputs ledger (sourced -> plain; assumed -> labeled + into the
review appendix), and emit the deck-IR as deterministic JSON.
"""

import argparse
import json
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import yamlmini  # noqa: E402

CORE = os.path.dirname(TOOLS)
ARCHETYPES = os.path.join(CORE, "orchestrator", "archetypes")

BIND_RE = re.compile(r"\{\{\s*([a-z][a-z0-9_.]*)\s*\}\}")
# The "verify before the room" label for an assumed value, by output language (RFC-0001 §6).
VERIFY_LABEL = {"it": "da verificare", "en": "to verify", "es": "por verificar", "fr": "à vérifier"}


def _new_acc():
    return {"used": set(), "assumed": {}, "unresolved": set()}


def _mark(value, lang):
    return f"⟨{value} — {VERIFY_LABEL.get(lang, VERIFY_LABEL['en'])}⟩"


def resolve_value(key, ledger, acc, lang):
    """Render one ledger cell: plain if sourced, labeled if assumed; records provenance in acc."""
    cell = ledger.get(key)
    if not isinstance(cell, dict):
        acc["unresolved"].add(key)
        return f"⟨{key}: ??⟩"
    acc["used"].add(key)
    value = "" if cell.get("value") is None else str(cell.get("value"))
    if cell.get("provenance") == "assumed":
        acc["assumed"][key] = cell
        return _mark(value, lang)
    return value


def resolve_text(text, ledger, acc, lang):
    """Substitute {{binding}} tokens in a prose string against the ledger."""
    if not isinstance(text, str):
        return text
    return BIND_RE.sub(lambda m: resolve_value(m.group(1), ledger, acc, lang), text)


def _build_section(sec, content, ledger, acc, lang):
    """Turn one archetype section + its manifest content into a deck-IR slide."""
    kind = sec.get("kind")
    c = content.get(sec["id"]) if isinstance(content, dict) else None
    c = c if isinstance(c, dict) else {}
    slide = {"id": sec["id"], "kind": kind, "title": c.get("title", sec["id"]), "blocks": []}
    blocks = slide["blocks"]

    if kind == "summary":
        if c.get("lead"):
            blocks.append({"type": "lead", "text": resolve_text(c["lead"], ledger, acc, lang)})
        for p in c.get("points", []) or []:
            blocks.append({"type": "bullet", "text": resolve_text(p, ledger, acc, lang)})
    elif kind == "kpi_table":
        for row in c.get("rows", []) or []:
            mk = row.get("metric_binding")
            cell = ledger.get(mk) if isinstance(ledger, dict) else None
            label = cell.get("label", mk) if isinstance(cell, dict) else mk
            entry = {"type": "kpi_row", "label": label,
                     "value": resolve_value(mk, ledger, acc, lang)}
            if row.get("target_binding"):
                entry["target"] = resolve_value(row["target_binding"], ledger, acc, lang)
            blocks.append(entry)
    elif kind == "prose":
        blocks.append({"type": "prose", "text": resolve_text(c.get("body", ""), ledger, acc, lang)})
    elif kind == "risk_list":
        for r in c.get("risks", []) or []:
            blocks.append({"type": "risk",
                           "risk": resolve_text(r.get("risk", ""), ledger, acc, lang),
                           "ask": resolve_text(r.get("ask", ""), ledger, acc, lang)})
    elif kind == "decision_list":
        for d in c.get("decisions", []) or []:
            blocks.append({"type": "decision", "text": resolve_text(d, ledger, acc, lang)})
    return slide


def load_archetype(name):
    path = os.path.join(ARCHETYPES, f"{name}.yaml")
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def build_deck_ir(manifest, archetype):
    """Compose the deck-IR and return (deck_ir, acc). Pure and deterministic."""
    acc = _new_acc()
    ident = manifest.get("identity", {}) or {}
    ctx = manifest.get("context", {}) or {}
    ledger = manifest.get("inputs", {}) or {}
    content = manifest.get("content", {}) or {}
    lang = ctx.get("output_lang", "en")
    altitude = ident.get("audience_altitude", "")
    shaping = (archetype.get("altitude_shaping", {}) or {}).get(altitude, {}) or {}

    deliverables = manifest.get("deliverables", []) or [{"type": "presentation"}]
    deliverable = deliverables[0] if isinstance(deliverables, list) and deliverables else {}

    # Compose every section; required sections are never dropped. Altitude max_slides caps the
    # deck by dropping optional sections from the end (audience-fit gate then verifies the count).
    structure = archetype.get("structure", []) or []
    slides = [_build_section(sec, content, ledger, acc, lang) for sec in structure]
    max_slides = shaping.get("max_slides")
    if isinstance(max_slides, int) and len(slides) > max_slides:
        required_ids = {s["id"] for s in structure if s.get("required")}
        kept, optional_budget = [], max_slides - len(required_ids)
        for slide, sec in zip(slides, structure):
            if sec.get("required"):
                kept.append(slide)
            elif optional_budget > 0:
                kept.append(slide)
                optional_budget -= 1
        slides = kept

    review_appendix = [
        {"binding": k,
         "value": "" if ledger[k].get("value") is None else str(ledger[k].get("value")),
         "assumption": ledger[k].get("assumption", ""),
         "fill_from": ledger[k].get("fill_from", "")}
        for k in sorted(acc["assumed"])
    ]

    deck_ir = {
        "deliverable": deliverable.get("type", "presentation"),
        "format": deliverable.get("format", "speaker"),
        "length": deliverable.get("length", "medium"),
        "archetype": archetype.get("archetype", ""),
        "altitude": altitude,
        "output_lang": lang,
        "objective": manifest.get("objective", ""),
        "lead_with": shaping.get("lead_with", ""),
        "slides": slides,
        "review_appendix": review_appendix,
    }
    return deck_ir, acc


def main():
    ap = argparse.ArgumentParser(description="Render an EAMOS meeting manifest into a deck-IR.")
    ap.add_argument("manifest", help="path to a meeting manifest (e.g. examples/qbr-c-level.yaml)")
    ap.add_argument("--out", help="output path for the deck-IR JSON (default: stdout)")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = yamlmini.load_yaml(fh.read())
    archetype = load_archetype(manifest.get("identity", {}).get("archetype", "review"))
    deck_ir, acc = build_deck_ir(manifest, archetype)

    text = json.dumps(deck_ir, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"Render: OK — deck-IR -> {args.out} "
              f"({len(deck_ir['slides'])} slides, {len(deck_ir['review_appendix'])} to verify)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
