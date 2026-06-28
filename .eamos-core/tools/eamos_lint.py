#!/usr/bin/env python3
"""Self-lint for EAMOS — the quality bar EAMOS imposes on its output, imposed first on itself.

Dependency-free (stdlib + yamlmini + render). Runs the structural gates on a meeting manifest by
composing its deck-IR and checking it. The gates are *structural* and decidable by design
(RFC-0001 §6) — the deck-IR is the determinism boundary, so the checks never reason over prose.

    python tools/eamos_lint.py orchestrator/examples/qbr-c-level.yaml

Gates:
  completeness               — every archetype-required section is present in the deck-IR.
  grounding-labeled          — every binding resolves; every assumed value is labeled and listed
                               in the review appendix with an assumption + review_required flag.
  audience-fit               — the rendered deck respects the altitude slide budget.
  deliverable-params-in-bounds — requested deliverable params are within the archetype's bounds.
"""

import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import render  # noqa: E402  (reuses the loader + build_deck_ir)
import yamlmini  # noqa: E402

failures = []  # (gate, message)


def fail(gate, message):
    failures.append((gate, message))


def gate_completeness(deck_ir, archetype):
    required = [s["id"] for s in archetype.get("structure", []) or [] if s.get("required")]
    present = {s["id"] for s in deck_ir.get("slides", [])}
    for sid in required:
        if sid not in present:
            fail("completeness", f"required section '{sid}' is missing from the deck-IR")


def gate_grounding_labeled(deck_ir, acc, ledger):
    for key in sorted(acc["unresolved"]):
        fail("grounding-labeled", f"binding '{{{{{key}}}}}' does not resolve to any inputs-ledger cell")
    appendix_keys = {a["binding"] for a in deck_ir.get("review_appendix", [])}
    for key in sorted(acc["assumed"]):
        cell = ledger.get(key, {})
        if key not in appendix_keys:
            fail("grounding-labeled", f"assumed value '{key}' is used but not in the review appendix")
        if not str(cell.get("assumption", "")).strip():
            fail("grounding-labeled", f"assumed value '{key}' has no 'assumption' note")
        if cell.get("review_required") is not True:
            fail("grounding-labeled", f"assumed value '{key}' is missing 'review_required: true'")


def gate_audience_fit(deck_ir, archetype):
    altitude = deck_ir.get("altitude", "")
    shaping = (archetype.get("altitude_shaping", {}) or {}).get(altitude, {}) or {}
    budget = shaping.get("max_slides")
    n = len(deck_ir.get("slides", []))
    if isinstance(budget, int) and n > budget:
        fail("audience-fit", f"{n} slides exceed the {altitude} budget of {budget}")


def gate_params_in_bounds(manifest, archetype):
    altitude = manifest.get("identity", {}).get("audience_altitude", "")
    bounds = (archetype.get("deliverable_bounds", {}) or {}).get(altitude, {}) or {}
    for d in manifest.get("deliverables", []) or []:
        dtype = d.get("type")
        dbounds = bounds.get(dtype, {}) or {}
        for param, rule in dbounds.items():
            allow = rule.get("allow") if isinstance(rule, dict) else None
            if allow is not None and d.get(param) is not None and d[param] not in allow:
                fail("deliverable-params-in-bounds",
                     f"{dtype}.{param}='{d[param]}' not allowed at {altitude} (allow: {allow})")


def gate_registry_params(manifest):
    """Every deliverable's params are within the registry's declared enums (RFC-0002 §4)."""
    for d in manifest.get("deliverables", []) or []:
        if not isinstance(d, dict):
            continue
        dtype = d.get("type")
        reg = render.load_deliverable(dtype)
        if reg is None:
            fail("deliverable-params", f"deliverable type '{dtype}' has no registry entry")
            continue
        params = reg.get("params", {}) or {}
        for k, v in d.items():
            if k == "type":
                continue
            spec = params.get(k)
            if spec is None:
                fail("deliverable-params", f"{dtype}.{k} is not a declared param of '{dtype}'")
                continue
            enum = spec.get("enum") if isinstance(spec, dict) else None
            if enum is not None and v not in enum:
                fail("deliverable-params", f"{dtype}.{k}='{v}' not in {enum}")


def main():
    if len(sys.argv) < 2:
        print("usage: eamos_lint.py <manifest.yaml>")
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        manifest = yamlmini.load_yaml(fh.read())
    archetype = render.load_archetype(manifest.get("identity", {}).get("archetype", "review"))
    deck_ir, acc = render.build_deck_ir(manifest, archetype)
    ledger = manifest.get("inputs", {}) or {}

    gate_completeness(deck_ir, archetype)
    gate_grounding_labeled(deck_ir, acc, ledger)
    gate_audience_fit(deck_ir, archetype)
    gate_params_in_bounds(manifest, archetype)
    gate_registry_params(manifest)

    if failures:
        print("eamos_lint: FAIL\n")
        for gate, msg in failures:
            print(f"  [{gate}] {msg}")
        print(f"\n{len(failures)} gate failure(s).")
        return 1
    print(f"eamos_lint: OK — all gates green "
          f"({len(deck_ir['slides'])} slides, {len(deck_ir['review_appendix'])} to verify)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
