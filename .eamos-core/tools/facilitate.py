#!/usr/bin/env python3
"""EAMOS facilitate — the facilitate / follow-up phases (RFC-0001 §4, §8).

Dependency-free (stdlib + yamlmini + render + series). Two ops around the non-delegable
`human-runs-the-room` gate (RFC-0001 §8):

  prep      — the timeboxed agenda + facilitation script (talking points per item), grounded from
              the deck-IR. The agent prepares; the human runs the room. `--template` swaps the
              generic per-section agenda for a named meeting-flow (e.g. discovery-decision, #32).
  followup  — minutes + decision log + action items (owner+due) from the human-captured OUTCOMES,
              then carries them into the series store (the loop closes; the next instance inherits).

The gate is enforced by construction: `followup` REQUIRES `--outcomes` (what a human captured in the
room). The agent never invents what was decided — exactly the grounding stance applied to the room.

    python tools/facilitate.py prep     orchestrator/examples/qbr-c-level.yaml --minutes 60
    python tools/facilitate.py followup orchestrator/examples/qbr-c-level.yaml \
        --outcomes orchestrator/examples/series/qbr-q3-outcomes.yaml --store build/series.json --out build/minutes.md
"""

import argparse
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import yamlmini  # noqa: E402
import render    # noqa: E402
import series    # noqa: E402

LABELS = {
    "it": {"agenda": "Agenda", "script": "Script di facilitazione", "min": "min", "obj": "Obiettivo",
           "talk": "Punti da toccare", "minutes": "Verbale", "decisions": "Decisioni",
           "actions": "Azioni", "owner": "owner", "due": "scadenza", "notes": "Note",
           "attendees": "Partecipanti", "joins_at": "entra da",
           "input_gathering": "Raccolta input", "live_classification": "Classificazione dal vivo",
           "targeted_questions": "Domande mirate", "structured_synthesis": "Sintesi strutturata",
           "decision_framing": "Inquadramento decisione"},
    "en": {"agenda": "Agenda", "script": "Facilitation script", "min": "min", "obj": "Objective",
           "talk": "Talking points", "minutes": "Minutes", "decisions": "Decisions",
           "actions": "Action items", "owner": "owner", "due": "due", "notes": "Notes",
           "attendees": "Attendees", "joins_at": "joins at",
           "input_gathering": "Input gathering", "live_classification": "Live classification",
           "targeted_questions": "Targeted questions", "structured_synthesis": "Structured synthesis",
           "decision_framing": "Decision framing"},
}


def _lab(lang, k):
    return LABELS.get(lang, LABELS["en"]).get(k, LABELS["en"][k])


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def _flatten(block):
    t = block.get("type")
    if t in ("lead", "bullet", "prose", "decision", "next_step", "residual_risk"):
        return block.get("text", "")
    if t == "kpi_row":
        s = f"{block.get('label', '')}: {block.get('value', '')}"
        return s + (f" (target {block['target']})" if block.get("target") else "")
    if t == "risk":
        return f"{block.get('risk', '')} → {block.get('ask', '')}"
    if t == "option":
        return f"{block.get('name', '')} (pro {block.get('pro', '')}; con {block.get('con', '')})"
    return ""


def _timeboxes(n, total):
    base = max(5, (total // n // 5) * 5) if n else total
    boxes = [base] * n
    boxes[-1] += total - sum(boxes)            # last item absorbs the remainder
    return boxes


# Named timebox templates: the meeting FLOW as data — (phase id, min, max minutes). The flexible
# phase(s) (min != max) absorb the slack so the total tracks --minutes within the template's range.
TIMEBOX_TEMPLATES = {
    # Discovery -> decision flow (#32): the 10/5/20-40/10/15 phases (60–80 min total — the fixed 40
    # plus the flexible targeted-questions 20–40); targeted-questions absorbs the --minutes slack.
    "discovery-decision": [
        ("input_gathering",      10, 10),
        ("live_classification",   5,  5),
        ("targeted_questions",   20, 40),
        ("structured_synthesis", 10, 10),
        ("decision_framing",     15, 15),
    ],
}


def _template_boxes(template, minutes):
    """Minutes per phase: each starts at its minimum; the flexible phases (min != max) absorb the
    remaining budget up to their max, so the total self-clamps to the template's range."""
    boxes = [lo for _, lo, _ in template]
    extra = minutes - sum(boxes)
    for i, (_, lo, hi) in enumerate(template):
        if hi > lo and extra > 0:
            add = min(extra, hi - lo)
            boxes[i] += add
            extra -= add
    return boxes


def _roster(attendees, lang):
    """The optional attendee roster / RACI (manifest `attendees:`), rendered into the agenda header.
    Structural and non-fabricating: an absent or empty roster renders nothing. `raci` and `from_phase`
    are each optional per attendee; a late-joining actor (e.g. a vendor) carries its phase."""
    rows = [a for a in (attendees or []) if isinstance(a, dict) and a.get("role")]
    if not rows:
        return []
    out = [f"**{_lab(lang, 'attendees')}**", ""]
    for a in rows:
        line = f"- {a['role']}"
        if a.get("raci"):
            line += f" — RACI: {a['raci']}"
        if a.get("from_phase"):
            line += f"  ·  {_lab(lang, 'joins_at')} {a['from_phase']}"
        out.append(line)
    out.append("")
    return out


def prep(manifest_path, minutes, template=None):
    m = _load(manifest_path)
    archetype = render.load_archetype(m.get("identity", {}).get("archetype", "review"))
    deck_ir, _ = render.build_deck_ir(m, archetype)
    lang = deck_ir.get("output_lang", "en")
    slides = deck_ir.get("slides", [])
    boxes = _timeboxes(len(slides), minutes)

    out = [f"# {_lab(lang, 'agenda')} — {m.get('objective', '')}", ""]
    out += _roster(m.get("attendees"), lang)   # optional roster / RACI in the agenda header (#25)
    tmpl = TIMEBOX_TEMPLATES.get(template)     # a named meeting-flow template, e.g. discovery-decision (#32)
    clock = 0
    if tmpl:                                   # phase-based agenda (the flow); the script stays per-section
        for (pid, _, _), box in zip(tmpl, _template_boxes(tmpl, minutes)):
            out.append(f"- {clock:>3}–{clock + box:<3} {_lab(lang, 'min')}  ·  {_lab(lang, pid)}")
            clock += box
    else:                                      # generic agenda: one timebox per deck section
        for s, box in zip(slides, boxes):
            out.append(f"- {clock:>3}–{clock + box:<3} {_lab(lang, 'min')}  ·  {s.get('title', s.get('id'))}")
            clock += box
    out += ["", f"# {_lab(lang, 'script')}", ""]
    for s, box in zip(slides, boxes):
        out.append(f"## {s.get('title', s.get('id'))}" + ("" if tmpl else f"  ({box} {_lab(lang, 'min')})"))
        out.append(f"*{_lab(lang, 'talk')}:*")
        for b in s.get("blocks", []):
            line = _flatten(b)
            if line:
                out.append(f"- {line}")
        out.append("")
    text = "\n".join(out).rstrip() + "\n"
    sys.stdout.write(text)
    return 0


def followup(manifest_path, outcomes_path, store_path, out):
    if not outcomes_path:
        print("facilitate: FAIL — followup requires --outcomes (what a human captured in the room). "
              "The agent never invents the room's outcomes (human-runs-the-room, RFC-0001 §8).")
        return 1
    m = _load(manifest_path)
    ident = m.get("identity", {}) or {}
    series_id, instance = ident.get("series_id"), ident.get("instance")
    lang = (m.get("context", {}) or {}).get("output_lang", "en")
    ledger = m.get("inputs", {}) or {}
    o = _load(outcomes_path)
    decisions = o.get("decisions", []) or []
    actions = o.get("actions", []) or []

    # Minutes (decision log + action items with owner+due).
    md = [f"# {_lab(lang, 'minutes')} — {m.get('series_name') or m.get('objective', '')}",
          f"*{series_id} · {instance}*", ""]
    md.append(f"## {_lab(lang, 'decisions')}")
    md += [f"- {d}" for d in decisions] or ["- —"]
    md.append("")
    md.append(f"## {_lab(lang, 'actions')}")
    for a in actions:
        md.append(f"- [ ] {a.get('action', '')} — {_lab(lang, 'owner')}: {a.get('owner', '?')}, "
                  f"{_lab(lang, 'due')}: {a.get('due', '?')}")
    md.append("")
    if o.get("notes"):
        md += [f"## {_lab(lang, 'notes')}", o["notes"], ""]
    minutes_text = "\n".join(md).rstrip() + "\n"

    # Carry into the series store (the loop closes).
    store = series._load_store(store_path)
    store["series_id"] = series_id
    if instance not in store["instances"]:
        store["instances"].append(instance)
    for d in decisions:
        store["decision_log"].append({"instance": instance, "decision": d})
    for i, a in enumerate(actions, 1):
        store["open_actions"].append({"id": f"{instance}-A{i}", "from": instance, "status": "open",
                                      "action": a.get("action", ""), "owner": a.get("owner", ""),
                                      "due": a.get("due", "")})
    for key, cell in ledger.items():
        if key.startswith("kpi.") and isinstance(cell, dict):
            store["kpi_history"].setdefault(key, {})[instance] = (
                "" if cell.get("value") is None else str(cell.get("value")))
    series._write_store(store, store_path)

    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(minutes_text)
    sys.stdout.write(minutes_text)
    print(f"\nfacilitate: OK — {len(decisions)} decisions, {len(actions)} actions carried into "
          f"{store_path} (instance {instance})")
    return 0


def main():
    ap = argparse.ArgumentParser(description="EAMOS facilitate / follow-up.")
    ap.add_argument("op", choices=["prep", "followup"])
    ap.add_argument("manifest")
    ap.add_argument("--minutes", type=int, default=60, help="(prep) total meeting length")
    ap.add_argument("--template", choices=sorted(TIMEBOX_TEMPLATES),
                    help="(prep) timebox template, e.g. discovery-decision (default: per-section)")
    ap.add_argument("--outcomes", help="(followup) human-captured outcomes YAML (required)")
    ap.add_argument("--store", help="(followup) series store JSON to carry outcomes into")
    ap.add_argument("--out", help="(followup) path to write the minutes")
    args = ap.parse_args()
    if args.op == "prep":
        return prep(args.manifest, args.minutes, args.template)
    return followup(args.manifest, args.outcomes, args.store, args.out)


if __name__ == "__main__":
    sys.exit(main())
