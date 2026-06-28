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
DELIVERABLES = os.path.join(CORE, "orchestrator", "os", "deliverables")

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


def apply_overlays(structure, shaping):
    """Compose the effective section list: base structure + the altitude overlay (RFC-0001 §3).

    Deterministic; never a cross-product. Order of operations: drop -> reorder -> slide-budget cap.
    A `required` section is never dropped (the completeness gate depends on this). `order` is a
    stable reordering — listed ids lead, in that order; unlisted sections keep their relative order.
    """
    secs = [s for s in structure if s.get("required") or s["id"] not in set(shaping.get("drop", []) or [])]
    order = shaping.get("order")
    if order:
        rank = {sid: i for i, sid in enumerate(order)}
        secs.sort(key=lambda s: rank.get(s["id"], len(order)))   # stable: unlisted keep order
    cap = shaping.get("max_slides")
    if isinstance(cap, int) and len(secs) > cap:
        kept, opt_budget = [], cap - sum(1 for s in secs if s.get("required"))
        for s in secs:
            if s.get("required"):
                kept.append(s)
            elif opt_budget > 0:
                kept.append(s)
                opt_budget -= 1
        secs = kept
    return secs


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
    elif kind == "option_list":
        for o in c.get("options", []) or []:
            blocks.append({"type": "option",
                           "name": resolve_text(o.get("name", ""), ledger, acc, lang),
                           "pro": resolve_text(o.get("pro", ""), ledger, acc, lang),
                           "con": resolve_text(o.get("con", ""), ledger, acc, lang)})
    return slide


def load_archetype(name):
    path = os.path.join(ARCHETYPES, f"{name}.yaml")
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def load_deliverable(dtype):
    """The registry entry for a deliverable type (RFC-0002 §4), or None if undeclared."""
    path = os.path.join(DELIVERABLES, f"{dtype}.yaml")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def _resolve_params(reg, requested):
    """Merge a deliverable's requested params over the registry defaults."""
    params = (reg or {}).get("params", {}) or {}
    out = {k: (spec.get("default") if isinstance(spec, dict) else None) for k, spec in params.items()}
    for k, v in (requested or {}).items():
        if k != "type":
            out[k] = v
    return out


def _find_deliverable(manifest, dtype):
    for d in manifest.get("deliverables", []) or []:
        if isinstance(d, dict) and d.get("type") == dtype:
            return d
    return {"type": dtype}


def build_deck_ir(manifest, archetype, altitude=None):
    """Compose the deck-IR and return (deck_ir, acc). Pure and deterministic.

    `altitude` overrides the manifest's audience_altitude — lets one manifest render at several
    altitudes (the M2 exit gate: the same meeting renders correctly at two altitudes)."""
    acc = _new_acc()
    ident = manifest.get("identity", {}) or {}
    ctx = manifest.get("context", {}) or {}
    ledger = manifest.get("inputs", {}) or {}
    content = manifest.get("content", {}) or {}
    lang = ctx.get("output_lang", "en")
    altitude = altitude or ident.get("audience_altitude", "")
    shaping = (archetype.get("altitude_shaping", {}) or {}).get(altitude, {}) or {}

    deliverables = manifest.get("deliverables", []) or [{"type": "presentation"}]
    deliverable = deliverables[0] if isinstance(deliverables, list) and deliverables else {}

    # Compose the effective structure via the altitude overlay (drop/reorder/cap), then render
    # each section. The overlay is deterministic and never a cross-product (RFC-0001 §3).
    structure = archetype.get("structure", []) or []
    effective = apply_overlays(structure, shaping)
    slides = [_build_section(sec, content, ledger, acc, lang) for sec in effective]

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


def build_infographic_ir(manifest, archetype, altitude=None):
    """Project the same grounded content into an infographic-IR (RFC-0002 §2, §3). A peer of
    build_deck_ir over the SAME ledger — so a value cannot diverge between the deck and the
    infographic (RFC-0002 §7). Picks the headline stats, the lead, and the decision asks."""
    acc = _new_acc()
    ident = manifest.get("identity", {}) or {}
    ctx = manifest.get("context", {}) or {}
    ledger = manifest.get("inputs", {}) or {}
    content = manifest.get("content", {}) or {}
    lang = ctx.get("output_lang", "en")
    altitude = altitude or ident.get("audience_altitude", "")
    shaping = (archetype.get("altitude_shaping", {}) or {}).get(altitude, {}) or {}
    effective = apply_overlays(archetype.get("structure", []) or [], shaping)

    lead, stats, asks = "", [], []
    for sec in effective:
        c = content.get(sec["id"], {}) if isinstance(content, dict) else {}
        c = c if isinstance(c, dict) else {}
        kind = sec.get("kind")
        if kind == "summary" and not lead:
            lead = resolve_text(c.get("lead", ""), ledger, acc, lang)
        elif kind == "kpi_table":
            for row in c.get("rows", []) or []:
                mk = row.get("metric_binding")
                cell = ledger.get(mk) if isinstance(ledger, dict) else None
                if not isinstance(cell, dict):
                    acc["unresolved"].add(mk)
                    stats.append({"label": mk, "value": "??", "assumed": False})
                    continue
                acc["used"].add(mk)                       # register provenance for the appendix
                assumed = cell.get("provenance") == "assumed"
                if assumed:
                    acc["assumed"][mk] = cell
                stat = {"label": cell.get("label", mk),   # raw value + a flag; the SVG colors amber
                        "value": "" if cell.get("value") is None else str(cell.get("value")),
                        "assumed": assumed}
                if row.get("target_binding"):
                    stat["target"] = resolve_value(row["target_binding"], ledger, acc, lang)
                stats.append(stat)
        elif kind == "decision_list":
            asks = [resolve_text(d, ledger, acc, lang) for d in (c.get("decisions", []) or [])]

    reg = load_deliverable("infographic")
    params = _resolve_params(reg, _find_deliverable(manifest, "infographic"))
    review_appendix = [
        {"binding": k, "value": "" if ledger[k].get("value") is None else str(ledger[k].get("value")),
         "assumption": ledger[k].get("assumption", ""), "fill_from": ledger[k].get("fill_from", "")}
        for k in sorted(acc["assumed"])
    ]
    info_ir = {
        "deliverable": "infographic",
        "orientation": params.get("orientation", "portrait"),
        "visual_style": params.get("visual_style", "professional"),
        "detail": params.get("detail", "standard"),
        "output_lang": lang,
        "title": manifest.get("objective", ""),
        "lead": lead,
        "stats": stats,
        "asks": asks,
        "review_appendix": review_appendix,
    }
    return info_ir, acc


def build_data_ir(manifest, archetype, altitude=None):
    """Project the KPI rows into a data-IR (RFC-0002 §3) — the table/chart family. A peer of the
    deck-IR over the SAME ledger (§7): the KPI table cannot diverge from the deck or infographic.
    Each row carries its source (for the hardcode-provenance note) and an assumed flag."""
    acc = _new_acc()
    ident = manifest.get("identity", {}) or {}
    ctx = manifest.get("context", {}) or {}
    ledger = manifest.get("inputs", {}) or {}
    content = manifest.get("content", {}) or {}
    lang = ctx.get("output_lang", "en")
    altitude = altitude or ident.get("audience_altitude", "")
    shaping = (archetype.get("altitude_shaping", {}) or {}).get(altitude, {}) or {}
    effective = apply_overlays(archetype.get("structure", []) or [], shaping)

    rows = []
    for sec in effective:
        c = content.get(sec["id"], {}) if isinstance(content, dict) else {}
        c = c if isinstance(c, dict) else {}
        if sec.get("kind") != "kpi_table":
            continue
        for row in c.get("rows", []) or []:
            mk = row.get("metric_binding")
            cell = ledger.get(mk) if isinstance(ledger, dict) else None
            if not isinstance(cell, dict):
                acc["unresolved"].add(mk)
                rows.append({"label": mk, "value": "??", "target": "", "source": "", "assumed": False})
                continue
            acc["used"].add(mk)
            assumed = cell.get("provenance") == "assumed"
            if assumed:
                acc["assumed"][mk] = cell
            rows.append({
                "label": cell.get("label", mk),
                "value": "" if cell.get("value") is None else str(cell.get("value")),
                "target": resolve_value(row["target_binding"], ledger, acc, lang) if row.get("target_binding") else "",
                "source": cell.get("source") or cell.get("fill_from") or "",
                "assumed": assumed,
            })

    reg = load_deliverable("table_chart")
    params = _resolve_params(reg, _find_deliverable(manifest, "table_chart"))
    review_appendix = [
        {"binding": k, "value": "" if ledger[k].get("value") is None else str(ledger[k].get("value")),
         "assumption": ledger[k].get("assumption", ""), "fill_from": ledger[k].get("fill_from", "")}
        for k in sorted(acc["assumed"])
    ]
    return {
        "deliverable": "table_chart",
        "chart": params.get("chart", "none"),
        "output_lang": lang,
        "title": manifest.get("objective", ""),
        "rows": rows,
        "review_appendix": review_appendix,
    }, acc


def main():
    ap = argparse.ArgumentParser(description="Render an EAMOS meeting manifest into an IR.")
    ap.add_argument("manifest", help="path to a meeting manifest (e.g. examples/qbr-c-level.yaml)")
    ap.add_argument("--out", help="output path for the IR JSON (default: stdout)")
    ap.add_argument("--altitude", help="override the manifest's audience_altitude (e.g. manager)")
    ap.add_argument("--ir", choices=["deck", "infographic", "data"], default="deck",
                    help="which IR projection to emit (default: deck)")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = yamlmini.load_yaml(fh.read())
    archetype = load_archetype(manifest.get("identity", {}).get("archetype", "review"))
    if args.ir == "infographic":
        ir, acc = build_infographic_ir(manifest, archetype, altitude=args.altitude)
        kind_note = f"{len(ir['stats'])} stats"
    elif args.ir == "data":
        ir, acc = build_data_ir(manifest, archetype, altitude=args.altitude)
        kind_note = f"{len(ir['rows'])} rows"
    else:
        ir, acc = build_deck_ir(manifest, archetype, altitude=args.altitude)
        kind_note = f"{len(ir['slides'])} slides"

    text = json.dumps(ir, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"Render: OK — {args.ir}-IR -> {args.out} "
              f"({kind_note}, {len(ir['review_appendix'])} to verify)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
