#!/usr/bin/env python3
"""EAMOS series — the persistent series store (the moat, RFC-0001 §9).

Dependency-free (stdlib + yamlmini + render). A recurring meeting must not forget what the last
instance decided. `close` writes an instance into the series store; `open` reads the store to
pre-populate the next instance with prior decisions, still-open actions, rolling risks, and KPI
movement. Keyed by `identity.series_id` (stable across instances). Store format: os/series/_schema.md.

    python tools/series.py close orchestrator/examples/series/qbr-q2-2026.yaml --store build/series.json
    python tools/series.py open  orchestrator/examples/qbr-c-level.yaml        --store build/series.json
"""

import argparse
import json
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import _cli      # noqa: E402  (utf8_stdio, #54)
import yamlmini  # noqa: E402
import render    # noqa: E402  (reuse resolve_text + the ledger model)

ARROW = {"up": "↑", "down": "↓", "flat": "→", "unknown": "·"}


def _load(path):
    return yamlmini.load_yaml(_cli.read_text(path, "manifest"))


def _num(s):
    """Best-effort numeric parse of a KPI string for direction (handles €, %, ~, commas, K/M/B)."""
    if not isinstance(s, str):
        return None
    t = s.strip().replace("~", "").replace(",", "").replace("€", "").replace("%", "").replace(" ", "")
    mult = 1.0
    if t[-1:] in "kKmMbB":
        mult = {"k": 1e3, "m": 1e6, "b": 1e9}[t[-1].lower()]
        t = t[:-1]
    try:
        return float(t) * mult
    except ValueError:
        return None


def _direction(prior, current):
    a, b = _num(prior), _num(current)
    if a is None or b is None:
        return "unknown"
    return "up" if b > a else ("down" if b < a else "flat")


def _new_store(series_id):
    return {"series_id": series_id, "instances": [], "decision_log": [],
            "open_actions": [], "rolling_risks": [], "kpi_history": {}}


def _resolved(text, ledger, lang):
    return render.resolve_text(text, ledger, render._new_acc(), lang)


def close(manifest_path, store_path):
    m = _load(manifest_path)
    ident = m.get("identity", {}) or {}
    series_id = ident.get("series_id")
    instance = ident.get("instance")
    if not series_id or not instance:
        print("series: FAIL — manifest needs identity.series_id and identity.instance")
        return 1
    ledger = m.get("inputs", {}) or {}
    content = m.get("content", {}) or {}
    lang = (m.get("context", {}) or {}).get("output_lang", "en")

    store = _load_store(store_path)
    if store.get("series_id") not in (None, series_id):
        print(f"series: FAIL — store is for '{store.get('series_id')}', not '{series_id}'")
        return 1
    store["series_id"] = series_id
    if instance not in store["instances"]:
        store["instances"].append(instance)
    # Re-closing the same instance replaces, never appends (#56): a re-run — crash recovery, a
    # corrected manifest, a second attempt — first drops what this instance previously wrote, so
    # the store the next instance pre-reads from cannot be silently poisoned by duplicates.
    store["decision_log"] = [d for d in store["decision_log"] if d.get("instance") != instance]
    store["open_actions"] = [a for a in store["open_actions"] if a.get("from") != instance]

    # Carry by section KIND (RFC-0005, #24), so the moat spans archetypes (not just review): every
    # decision_list section -> the decision log (the shortlist / asks); every risk_list -> open
    # actions + rolling risks. Backward-compatible — review's decisions_required IS a decision_list
    # and its risks_and_asks IS a risk_list, so an existing series carries identically.
    structure = render.load_archetype(ident.get("archetype", "review")).get("structure", []) or []
    for sec in structure:
        if sec.get("kind") != "decision_list":
            continue
        for d in (content.get(sec["id"], {}) or {}).get("decisions", []) or []:
            store["decision_log"].append({"instance": instance, "decision": _resolved(d, ledger, lang)})

    ai = 0
    for sec in structure:
        if sec.get("kind") != "risk_list":
            continue
        for r in (content.get(sec["id"], {}) or {}).get("risks", []) or []:
            ai += 1
            store["open_actions"].append({
                "id": f"{instance}-A{ai}", "from": instance, "status": "open",
                "action": _resolved(r.get("ask", ""), ledger, lang),
                "context": _resolved(r.get("risk", ""), ledger, lang)})
            rtext = _resolved(r.get("risk", ""), ledger, lang)
            if not any(x["risk"] == rtext for x in store["rolling_risks"]):
                store["rolling_risks"].append({"risk": rtext, "since": instance, "status": "open"})

    for key, cell in ledger.items():
        if key.startswith("kpi.") and isinstance(cell, dict):
            store["kpi_history"].setdefault(key, {})[instance] = (
                "" if cell.get("value") is None else str(cell.get("value")))

    _write_store(store, store_path)
    print(f"series: OK — closed {instance} into {store_path} "
          f"({len(store['decision_log'])} decisions, "
          f"{sum(1 for a in store['open_actions'] if a['status'] == 'open')} open actions, "
          f"{len(store['kpi_history'])} KPIs)")
    return 0


def fold_feedback(store, altitude, instance, feedback):
    """Fold a followup's material_feedback into store['preferences'] (RFC-0007 §3, #67).
    Keyed altitude → deliverable → tag, each with instance provenance and a derived count.
    Replace-by-instance (#56): this instance is first removed from every tag, so a re-run is
    idempotent. `verdict: accepted` with no tags clears the deliverable's accumulated tags —
    satisfaction is signal too (RFC-0007 §10-2)."""
    prefs = store.get("preferences") or {}
    alt = prefs.get(altitude) or {}
    for dtype in list(alt):
        for tag in list(alt[dtype]):
            insts = [i for i in alt[dtype][tag].get("instances", []) if i != instance]
            if insts:
                alt[dtype][tag] = {"count": len(insts), "instances": insts}
            else:
                del alt[dtype][tag]
        if not alt[dtype]:
            del alt[dtype]
    for dtype in sorted(feedback or {}):
        block = feedback[dtype] or {}
        tags = block.get("tags") or []
        if block.get("verdict") == "accepted" and not tags:
            alt.pop(dtype, None)
            continue
        for tag in tags:
            rec = alt.setdefault(dtype, {}).setdefault(tag, {"count": 0, "instances": []})
            rec["instances"].append(instance)
            rec["count"] = len(rec["instances"])
    if alt:
        prefs[altitude] = alt
    else:
        prefs.pop(altitude, None)
    if prefs:
        store["preferences"] = prefs
    else:
        store.pop("preferences", None)


def compile_preferences(store, manifest):
    """Compile the accumulated tags for this manifest's altitude into a `preferences_applied`
    proposal (RFC-0007 §4, #67). Deterministic: within a tag group the most recent instance wins
    (ties break on tag name); deltas come from the vocabulary's fixed table; a max_slides_pct is
    concretized against the archetype's altitude budget (tighten-only by construction). Returns {}
    when there is nothing to propose. The proposal is only ever PRINTED — the maintainer writes it
    into the manifest and confirms; the memory never applies itself."""
    vocab = render.load_feedback_tags().get("tags") or {}
    ident = manifest.get("identity") or {}
    altitude = ident.get("audience_altitude", "")
    alt = (store.get("preferences") or {}).get(altitude) or {}
    if not alt or not vocab:
        return {}
    order = {inst: i for i, inst in enumerate(store.get("instances", []))}

    def recency(tags, tag):
        return max([order.get(i, -1) for i in tags[tag].get("instances", [])] or [-1])

    budget = None
    if ident.get("archetype"):
        shaping = (render.load_archetype(ident["archetype"]).get("altitude_shaping", {}) or {})
        budget = (shaping.get(altitude, {}) or {}).get("max_slides")

    proposal, instances = {}, set()
    for dtype in sorted(alt):
        tags = alt[dtype]
        winners = {}
        for tag in sorted(tags):
            g = (vocab.get(tag) or {}).get("group", tag)
            if g not in winners or (recency(tags, tag), tag) > (recency(tags, winners[g]), winners[g]):
                winners[g] = tag
        deltas = {}
        for tag in sorted(winners.values()):
            deltas.update((vocab.get(tag) or {}).get("delta") or {})
            instances.update(tags[tag].get("instances", []))
        entry = {}
        pct = deltas.get("max_slides_pct")
        if isinstance(pct, int) and isinstance(budget, int):
            entry["max_slides"] = max(1, budget * pct // 100)
        if deltas.get("order_lead"):
            entry["order_lead"] = deltas["order_lead"]
        if entry:
            proposal[dtype] = entry
        if deltas.get("drop_deliverable"):
            proposal.setdefault("drop_deliverables", []).append(dtype)
    if not proposal:
        return {}
    proposal["from_instances"] = sorted(instances)
    return proposal


def open_(manifest_path, store_path, out):
    m = _load(manifest_path)
    ident = m.get("identity", {}) or {}
    instance = ident.get("instance", "")
    ledger = m.get("inputs", {}) or {}
    cf = m.get("carry_forward", {}) or {}
    store = _load_store(store_path)

    movements = []
    for key, cell in ledger.items():
        hist = store.get("kpi_history", {}).get(key)
        if not (key.startswith("kpi.") and isinstance(cell, dict) and hist):
            continue
        prior_inst = next((i for i in reversed(store.get("instances", [])) if i in hist), None)
        if prior_inst is None:
            continue
        prior, current = hist[prior_inst], ("" if cell.get("value") is None else str(cell.get("value")))
        movements.append({"kpi": key, "label": cell.get("label", key), "from_instance": prior_inst,
                          "prior": prior, "current": current, "direction": _direction(prior, current)})

    digest = {
        "series_id": store.get("series_id", ident.get("series_id")),
        "instance": instance,
        "from_instance": cf.get("from_instance"),
        "prior_decisions": store.get("decision_log", []) if cf.get("decisions") else [],
        "open_actions": [a for a in store.get("open_actions", []) if a.get("status") == "open"]
                        if cf.get("open_actions") else [],
        "rolling_risks": [r for r in store.get("rolling_risks", []) if r.get("status") == "open"]
                         if cf.get("rolling_risks") else [],
        "kpi_movement": movements if cf.get("kpi_history") else [],
    }
    proposal = compile_preferences(store, m)
    if proposal:                                 # only when there is something to propose (#67)
        digest["preferences_proposal"] = proposal
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(digest, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    _print_digest(digest)
    return 0


def _print_digest(d):
    print(f"# Carry-forward — {d['instance']} (series {d['series_id']}, from {d['from_instance']})\n")
    if d["prior_decisions"]:
        print("## Prior decisions")
        for x in d["prior_decisions"]:
            print(f"- [{x['instance']}] {x['decision']}")
        print()
    if d["open_actions"]:
        print("## Open actions carried in")
        for a in d["open_actions"]:
            line = f"- [{a['id']}] {a['action']}"
            if a.get("context"):                   # close-derived actions carry the risk; followup ones don't
                line += f"  — context: {a['context']}"
            print(line)
        print()
    if d["kpi_movement"]:
        print("## KPI movement")
        for k in d["kpi_movement"]:
            print(f"- {k['label']}: {k['prior']} → {k['current']} {ARROW.get(k['direction'], '·')}")
        print()
    p = d.get("preferences_proposal")
    if p:
        print(f"## Learned preferences (from {', '.join(p['from_instances'])})")
        print("Paste into the manifest and confirm it — the memory never applies itself (RFC-0007):")
        print()
        print("preferences_applied:")
        print(f"  from_instances: [{', '.join(p['from_instances'])}]")
        for dtype in sorted(k for k in p if k not in ("from_instances", "drop_deliverables")):
            fields = ", ".join(f"{k}: {v}" for k, v in sorted(p[dtype].items()))
            print(f"  {dtype}: {{ {fields} }}")
        if p.get("drop_deliverables"):
            print(f"  drop_deliverables: [{', '.join(sorted(p['drop_deliverables']))}]")
        print()


def _load_store(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return _new_store(None)


def _write_store(store, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(store, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    ap = argparse.ArgumentParser(description="EAMOS series store — close/open a recurring meeting.")
    ap.add_argument("op", choices=["close", "open"])
    ap.add_argument("manifest")
    ap.add_argument("--store", required=True, help="path to the series store JSON")
    ap.add_argument("--out", help="(open) path to write the carry-forward digest JSON")
    args = ap.parse_args()
    return close(args.manifest, args.store) if args.op == "close" else open_(args.manifest, args.store, args.out)


if __name__ == "__main__":
    sys.exit(main())
