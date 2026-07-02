#!/usr/bin/env python3
"""EAMOS advisor — the advanced variant (RFC-0006, #33): pattern matching + what-if simulation.

Dependency-free (stdlib + yamlmini + render). Two ADVISORY, DETERMINISTIC tools over data EAMOS
already produces — no ML, no embeddings, no Monte-Carlo. The agent surfaces; the human decides
(human-runs-the-room, RFC-0001 §8).

  record    — append a closed decision (its classification #27 + the decision contract #31) to the
              cross-series decision repository (os/advisor/_schema.md).
  match     — rank repository records by classification similarity to a new manifest, surfacing what
              was decided in similar past cases (retrieval, not prediction — RFC-0001 §6).
  simulate  — override scorecard weights/scores (--set key=value) and re-run the computed scorecard
              (#23) to report the ranking delta (does the winner change?). Never edits the manifest.

    python tools/advisor.py record   examples/vendor-selection.yaml --repo build/repo.json
    python tools/advisor.py match    examples/vendor-selection.yaml --repo examples/advisor/decision-repository.json
    python tools/advisor.py simulate examples/vendor-selection.yaml --set w.integ=0.5 --set w.tco=0.3 --set w.ttv=0.2
"""

import argparse
import copy
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import _cli      # noqa: E402  (utf8_stdio, #54)
import yamlmini  # noqa: E402
import render    # noqa: E402  (reuse scorecard_ledger + resolve_text + the ledger model)


def _load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def _classification(manifest):
    di = manifest.get("discovery_intake") or {}
    return (di.get("classification") or {}) if isinstance(di, dict) else {}


def _resolved(text, ledger, lang):
    return render.resolve_text(text, ledger, render._new_acc(), lang)


def _load_repo(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"records": []}


def record(manifest_path, repo_path, date=""):
    """Append this manifest's closed decision to the repository. Returns the record."""
    m = _load_yaml(manifest_path)
    ident = m.get("identity", {}) or {}
    lang = (m.get("context", {}) or {}).get("output_lang", "en")
    ledger = render.scorecard_ledger(m)
    content = m.get("content", {}) or {}
    contract = content.get("decision_contract", {}) or {}
    rec = {
        "series_id": ident.get("series_id") or ident.get("series_name", ""),
        "instance": ident.get("instance", ""),
        "date": date,
        "classification": _classification(m),
        "recommendation": _resolved((content.get("recommendation", {}) or {}).get("body", ""), ledger, lang),
        "next_step": _resolved(contract.get("next_step", ""), ledger, lang),
        "residual_risks": [_resolved(r, ledger, lang) for r in (contract.get("residual_risks", []) or [])],
    }
    repo = _load_repo(repo_path)
    repo.setdefault("records", []).append(rec)
    os.makedirs(os.path.dirname(os.path.abspath(repo_path)), exist_ok=True)
    with open(repo_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(repo, indent=2, ensure_ascii=False) + "\n")
    print(f"advisor: OK — recorded {rec['series_id']}@{rec['instance']} "
          f"({len(repo['records'])} in repository)")
    return rec


def _score(query, rec_cls):
    """Classification similarity: 3·cluster + 1·complexity + 1·decision_risk (matching dimensions)."""
    q, r = query or {}, rec_cls or {}
    return (3 * (q.get("cluster") is not None and q.get("cluster") == r.get("cluster"))
            + (q.get("complexity") is not None and q.get("complexity") == r.get("complexity"))
            + (q.get("decision_risk") is not None and q.get("decision_risk") == r.get("decision_risk")))


def match(manifest_path, repo_path, top=3):
    """Rank repository records by similarity to this manifest's classification. Returns the ranked
    list of (score, record). Stable: (score desc, recency desc) where recency = position in records."""
    query = _classification(_load_yaml(manifest_path))
    records = _load_repo(repo_path).get("records", []) or []
    ranked = sorted(((_score(query, r.get("classification")), i, r) for i, r in enumerate(records)),
                    key=lambda t: (t[0], t[1]), reverse=True)
    hits = [(s, r) for s, i, r in ranked if s > 0][:top]
    cl = query
    print(f"# Similar past cases — cluster {cl.get('cluster')} · complexity {cl.get('complexity')} "
          f"· decision-risk {cl.get('decision_risk')}\n")
    if not hits:
        print("_no comparable precedent in the repository_")
    for s, r in hits:
        c = r.get("classification", {})
        print(f"- [{s}/5] {r.get('series_id')}@{r.get('instance')} "
              f"({c.get('cluster')}/{c.get('complexity')}/{c.get('decision_risk')}): {r.get('recommendation')}")
        if r.get("next_step"):
            print(f"    next step: {r['next_step']}")
        for rr in r.get("residual_risks", []) or []:
            print(f"    residual: {rr}")
    return [(s, r) for s, r in hits]


def _winner(totals):
    """The option name with the highest numeric total (ties → first by declaration order)."""
    best, name = None, None
    for n, v in totals:
        try:
            f = float(str(v).replace(",", "."))
        except (ValueError, TypeError):
            continue
        if best is None or f > best:
            best, name = f, n
    return name


def _totals(manifest):
    led = render.scorecard_ledger(manifest)
    out = []
    for opt in (manifest.get("scorecard", {}) or {}).get("options", []) or []:
        cell = led.get(opt.get("total"))
        out.append((opt.get("name"), cell.get("value") if isinstance(cell, dict) else None))
    return out


def simulate(manifest_path, sets):
    """Override scorecard cells (sets: 'key=value' strings) and re-run the #23 computation. Returns
    {baseline, simulated, baseline_winner, simulated_winner}. Pure: the manifest is never edited."""
    m = _load_yaml(manifest_path)
    base = _totals(m)
    overrides = {}
    m2 = copy.deepcopy(m)
    for s in sets or []:
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in (m2.get("inputs", {}) or {}) and isinstance(m2["inputs"][k], dict):
            m2["inputs"][k]["value"] = v
            overrides[k] = v
    sim = _totals(m2)
    bw, sw = _winner(base), _winner(sim)
    print(f"# What-if — overrides: {overrides or '(none)'}\n")
    sim_map = dict(sim)
    for name, bval in base:
        print(f"- {name}: {bval} → {sim_map.get(name)}")
    flag = "  ⚠ winner changed" if bw != sw else ""
    print(f"\nwinner: {bw} → {sw}{flag}")
    return {"baseline": base, "simulated": sim, "baseline_winner": bw, "simulated_winner": sw}


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    ap = argparse.ArgumentParser(description="EAMOS advisor — pattern matching & what-if simulation.")
    ap.add_argument("op", choices=["record", "match", "simulate"])
    ap.add_argument("manifest")
    ap.add_argument("--repo", help="decision repository JSON (record/match)")
    ap.add_argument("--date", default="", help="(record) optional date tag, e.g. 2026-06")
    ap.add_argument("--set", action="append", dest="sets", metavar="key=value",
                    help="(simulate) override a scorecard weight/score cell (repeatable)")
    ap.add_argument("--top", type=int, default=3, help="(match) how many precedents to show")
    args = ap.parse_args()
    if args.op == "record":
        if not args.repo:
            ap.error("record needs --repo")
        record(args.manifest, args.repo, args.date)
    elif args.op == "match":
        if not args.repo:
            ap.error("match needs --repo")
        match(args.manifest, args.repo, args.top)
    else:
        simulate(args.manifest, args.sets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
