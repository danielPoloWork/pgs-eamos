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
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


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
            print(f"- [{a['id']}] {a['action']}  — context: {a['context']}")
        print()
    if d["kpi_movement"]:
        print("## KPI movement")
        for k in d["kpi_movement"]:
            print(f"- {k['label']}: {k['prior']} → {k['current']} {ARROW.get(k['direction'], '·')}")
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
