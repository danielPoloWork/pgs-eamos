#!/usr/bin/env python3
"""Self-lint for EAMOS — the quality bar EAMOS imposes on its output, imposed first on itself.

Dependency-free (stdlib + yamlmini + render). Runs the structural gates on a meeting manifest by
composing its deck-IR and checking it. The gates are *structural* and decidable by design
(RFC-0001 §6) — the deck-IR is the determinism boundary, so the checks never reason over prose.

    python tools/eamos_lint.py orchestrator/examples/qbr-c-level.yaml

Gates:
  completeness               — every archetype-required section is present in the deck-IR, has
                               substantive content blocks, and carries a real (non-id) title.
  grounding-labeled          — every binding resolves; every assumed value is labeled and listed
                               in the review appendix with an assumption + review_required flag;
                               every provenance is in the enum (anything else fails closed, #53).
  audience-fit               — the rendered deck respects the altitude slide budget.
  deliverable-params-in-bounds — requested deliverable params are within the archetype's bounds.
  no-action-considered       — any solution space (an option_list) includes the no-action baseline.
  classification-valid       — a problem-type classification (if present) uses taxonomy-allowed values.
  questions-valid            — the adaptive question tree + routing stay consistent with the taxonomy.
  topology-valid             — a topology diagram's edges/kinds/patterns are declared and in-vocabulary.
"""

import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import _cli      # noqa: E402  (utf8_stdio, #54)
import render  # noqa: E402  (reuses the loader + build_deck_ir)
import yamlmini  # noqa: E402

RUBRIC = os.path.join(os.path.dirname(TOOLS), "eval", "rubric.yaml")

failures = []  # (gate, message)


def fail(gate, message):
    failures.append((gate, message))


def _has_substance(slide):
    """A slide has substance iff at least one block carries a non-empty text field (#52)."""
    for block in slide.get("blocks", []) or []:
        for field, value in block.items():
            if field != "type" and isinstance(value, str) and value.strip():
                return True
    return False


def gate_completeness(deck_ir, archetype):
    required = [s["id"] for s in archetype.get("structure", []) or [] if s.get("required")]
    slides = {s["id"]: s for s in deck_ir.get("slides", [])}
    for sid in required:
        slide = slides.get(sid)
        if slide is None:
            fail("completeness", f"required section '{sid}' is missing from the deck-IR")
        elif not _has_substance(slide):
            fail("completeness", f"required section '{sid}' has no content blocks (empty slide)")
        elif not slide.get("title") or slide.get("title") == sid:
            fail("completeness",
                 f"required section '{sid}' has no title (the raw section id would render as the heading)")


def gate_grounding_labeled(deck_ir, acc, ledger):
    for key in sorted(acc["unresolved"]):
        fail("grounding-labeled", f"binding '{{{{{key}}}}}' does not resolve to any inputs-ledger cell")
    for key in sorted(acc.get("invalid_provenance", ())):   # fail closed (#53): rendered as assumed
        prov = (ledger.get(key) or {}).get("provenance")
        fail("grounding-labeled",
             f"cell '{key}' provenance '{prov}' is not one of sourced|assumed")
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
    altitude = (manifest.get("identity") or {}).get("audience_altitude", "")
    bounds = (archetype.get("deliverable_bounds", {}) or {}).get(altitude, {}) or {}
    for d in manifest.get("deliverables", []) or []:
        dtype = d.get("type")
        dbounds = bounds.get(dtype, {}) or {}
        for param, rule in dbounds.items():
            allow = rule.get("allow") if isinstance(rule, dict) else None
            if allow is not None and d.get(param) is not None and d[param] not in allow:
                fail("deliverable-params-in-bounds",
                     f"{dtype}.{param}='{d[param]}' not allowed at {altitude} (allow: {allow})")


def gate_no_action_considered(manifest, archetype):
    """The solution-space baseline (RFC-0001 §13; #30): any meeting that compares options (a section
    of kind `option_list`) must include the *no-action* option, so the often-ignored 'do nothing'
    baseline is always on the table. Structural + decidable, altitude-independent: one option in the
    section's content carries `no_action: true`. Vacuous (passes) for archetypes with no solution
    space — only `decision` declares an option_list today."""
    content = manifest.get("content", {}) or {}
    for sec in archetype.get("structure", []) or []:
        if sec.get("kind") != "option_list":
            continue
        c = content.get(sec["id"], {}) if isinstance(content, dict) else {}
        options = (c or {}).get("options", []) or []
        if not any(isinstance(o, dict) and o.get("no_action") for o in options):
            fail("no-action-considered",
                 f"option_list section '{sec['id']}' has no no-action option "
                 "(flag one option `no_action: true` so the baseline is compared)")


def gate_classification_valid(manifest):
    """Phase-B classification (#27): if a meeting carries `discovery_intake.classification`, its
    cluster / complexity / decision_risk must be values the taxonomy (os/intake/classification.yaml)
    allows. Structural + decidable; an absent classification passes (it is optional intake)."""
    di = manifest.get("discovery_intake") or {}
    cls = di.get("classification") if isinstance(di, dict) else None
    if not isinstance(cls, dict):
        return
    tax = render.load_classification()
    for dim in ("cluster", "complexity", "decision_risk"):
        allowed = tax.get(dim, []) or []
        val = cls.get(dim)
        if val is not None and allowed and val not in allowed:
            fail("classification-valid",
                 f"discovery_intake.classification.{dim}='{val}' not in {allowed}")


def gate_questions_valid():
    """Phase-C data integrity (RFC-0003, #28): the adaptive question tree + routing cannot drift from
    the taxonomy. Structural + decidable, manifest-independent (it validates the shipped os/intake
    data). Vacuous if the files are absent. Checks: every `clusters` key is a taxonomy cluster; every
    question has id + ask + a level in `levels`; routing complexity keys + level values are valid;
    every escalation rule references a taxonomy-valid cluster + decision_risk."""
    tree, routing = render.load_questions(), render.load_routing()
    if not tree and not routing:
        return
    tax = render.load_classification()
    clusters = set(tax.get("cluster", []) or [])
    risks = set(tax.get("decision_risk", []) or [])
    complexities = set(tax.get("complexity", []) or [])
    levels = set(tree.get("levels", []) or [])
    groups = [("common", tree.get("common", []))] + list((tree.get("clusters", {}) or {}).items())
    for name, qs in groups:
        if name != "common" and clusters and name not in clusters:
            fail("questions-valid", f"question tree cluster '{name}' is not in the taxonomy")
        for q in qs or []:
            if not (isinstance(q, dict) and q.get("id") and q.get("ask")):
                fail("questions-valid", f"a question in '{name}' is missing id/ask")
            elif levels and q.get("level") not in levels:
                fail("questions-valid", f"question '{q.get('id')}' has level '{q.get('level')}' not in {sorted(levels)}")
    for comp, lvl in (routing.get("by_complexity", {}) or {}).items():
        if complexities and comp not in complexities:
            fail("questions-valid", f"routing by_complexity key '{comp}' is not a taxonomy complexity")
        if levels and lvl not in levels:
            fail("questions-valid", f"routing by_complexity['{comp}']='{lvl}' is not a level")
    for rule in (routing.get("escalate_to_architecture", []) or []):
        if clusters and rule.get("cluster") not in clusters:
            fail("questions-valid", f"escalation cluster '{rule.get('cluster')}' is not in the taxonomy")
        if risks and rule.get("decision_risk") not in risks:
            fail("questions-valid", f"escalation decision_risk '{rule.get('decision_risk')}' is not in the taxonomy")


def gate_topology_valid(manifest):
    """Topology integrity (RFC-0004, #22): if a manifest has a `topology:` block, every edge from/to
    references a declared node id, and every node `kind` / edge `pattern` is in the architecture
    deliverable's vocabulary. Structural + decidable; absent topology passes. (Node-label grounding
    is handled at render in build_topology_ir — labeled + into the topology review appendix.)"""
    spec = manifest.get("topology")
    if not isinstance(spec, dict):
        return
    vocab = (render.load_deliverable("architecture") or {}).get("vocab", {}) or {}
    kinds, patterns = set(vocab.get("node_kind", []) or []), set(vocab.get("edge_pattern", []) or [])
    node_ids = set()
    for nd in spec.get("nodes", []) or []:
        node_ids.add(nd.get("id"))
        if kinds and nd.get("kind") not in kinds:
            fail("topology-valid", f"node '{nd.get('id')}' kind '{nd.get('kind')}' not in {sorted(kinds)}")
    for e in spec.get("edges", []) or []:
        for end in ("from", "to"):
            if e.get(end) not in node_ids:
                fail("topology-valid", f"edge {end}='{e.get(end)}' references an undeclared node")
        if patterns and e.get("pattern") not in patterns:
            fail("topology-valid",
                 f"edge '{e.get('from')}'->'{e.get('to')}' pattern '{e.get('pattern')}' not in {sorted(patterns)}")


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


def gate_confidentiality(manifest):
    """The enterprise lens (RFC-0001 §11): regimes are known, their mandatory gates are green, and
    no redact-tagged cell sits in a `public`-classified meeting."""
    policy = render.load_policy()
    if not policy:
        return
    failed_ids = {g for g, _ in failures}
    regimes = (manifest.get("context", {}) or {}).get("regulatory", []) or []
    classification = manifest.get("classification") or policy.get("default")
    for r in regimes:
        spec = (policy.get("regimes", {}) or {}).get(r)
        if spec is None:
            fail("confidentiality", f"unknown regulatory regime '{r}' (not in the policy)")
            continue
        for g in spec.get("mandatory_gates", []) or []:
            if g in failed_ids:
                fail("confidentiality", f"{r} makes gate '{g}' mandatory, but it failed")
    if classification == "public":
        tags = render.redact_tags_for(manifest, policy)
        for key, cell in (manifest.get("inputs", {}) or {}).items():
            if isinstance(cell, dict) and any(cell.get(t) for t in tags):
                fail("confidentiality", f"sensitive cell '{key}' in a 'public'-classified meeting")


def gate_rubric(manifest, deck_ir):
    """Score the deck-IR against the data rubric (RFC-0001 §10). Structural + language-agnostic, so
    a non-English board deck passes in its own output_lang (M7)."""
    rubric = {}
    if os.path.exists(RUBRIC):
        with open(RUBRIC, encoding="utf-8") as fh:
            rubric = yamlmini.load_yaml(fh.read())
    ident = manifest.get("identity", {}) or {}
    arch, alt = ident.get("archetype", ""), ident.get("audience_altitude", "")
    crit = (rubric.get(arch, {}) or {}).get(alt)
    if not crit:
        return                                   # no rubric cell yet — skip (the matrix grows over time)
    present = {s["id"] for s in deck_ir.get("slides", [])}
    for sid in crit.get("require_sections", []) or []:
        if sid not in present:
            fail("rubric", f"{arch}@{alt}: rubric requires section '{sid}'")
    cap = crit.get("max_slides")
    if isinstance(cap, int) and len(deck_ir.get("slides", [])) > cap:
        fail("rubric", f"{arch}@{alt}: {len(deck_ir['slides'])} slides exceed the rubric's {cap}")
    if crit.get("grounding") and "grounding-labeled" in {g for g, _ in failures}:
        fail("rubric", f"{arch}@{alt}: rubric requires grounding-labeled green")


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    if len(sys.argv) < 2:
        print("usage: eamos_lint.py <manifest.yaml>")
        return 2
    manifest = yamlmini.load_yaml(_cli.read_text(sys.argv[1], "manifest"))
    archetype = render.load_archetype((manifest.get("identity") or {}).get("archetype", "review"))
    deck_ir, acc = render.build_deck_ir(manifest, archetype)
    ledger = render.scorecard_ledger(manifest)   # include computed scorecard totals (#23) for grounding

    gate_completeness(deck_ir, archetype)
    gate_grounding_labeled(deck_ir, acc, ledger)
    gate_audience_fit(deck_ir, archetype)
    gate_params_in_bounds(manifest, archetype)
    gate_no_action_considered(manifest, archetype)
    gate_classification_valid(manifest)
    gate_questions_valid()
    gate_topology_valid(manifest)
    gate_registry_params(manifest)
    gate_rubric(manifest, deck_ir)
    gate_confidentiality(manifest)   # last: it inspects the other gates' results

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
