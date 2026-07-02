#!/usr/bin/env python3
"""Self-lint for EAMOS — the quality bar EAMOS imposes on its output, imposed first on itself.

Dependency-free (stdlib + yamlmini + render). Runs the structural gates on a meeting manifest by
composing its deck-IR and checking it. The gates are *structural* and decidable by design
(RFC-0001 §6) — the deck-IR is the determinism boundary, so the checks never reason over prose.

    python tools/eamos_lint.py orchestrator/examples/qbr-c-level.yaml

Every gate is a pure function returning its findings as (gate, message) tuples (#60): no hidden
module state, so two manifests can be linted in one process and a single gate unit-tests with no
cleanup. `run_all` aggregates; the two gates that inspect other gates' results (rubric's grounding
requirement, confidentiality's mandatory gates) receive them as an explicit parameter — the
ordering lives in the signature, not in a comment.

Gates:
  manifest-schema            — every manifest key is in the schema vocabulary (os/manifest/schema.yaml):
                               unknown top-level / identity / cell keys and content keys that match
                               no composed section fail by path; archetype + altitude are required.
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
MANIFEST_SCHEMA = os.path.join(os.path.dirname(TOOLS), "orchestrator", "os", "manifest", "schema.yaml")


def load_manifest_schema():
    """The manifest vocabulary (#59), or {} if absent (the gate is then vacuous)."""
    if not os.path.exists(MANIFEST_SCHEMA):
        return {}
    with open(MANIFEST_SCHEMA, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def gate_manifest_schema(manifest, archetype):
    """Schema-as-data validation of the manifest itself (#59). Every axis of the system is data
    validated by a gate — this one covers the single most important input. Without it a typo'd key
    vanishes silently: a bad cell field un-labels an assumption, a bad section key renders an empty
    section, a bad top-level key disables a feature. Failures name the offending path."""
    findings = []
    schema = load_manifest_schema()
    if not schema:
        return findings
    allowed_top = set(schema.get("top_level", []) or [])
    for key in sorted(manifest or {}):
        if allowed_top and key not in allowed_top:
            findings.append(("manifest-schema", f"unknown top-level key '{key}'"))

    ident_spec = schema.get("identity", {}) or {}
    ident = manifest.get("identity") or {}
    for req in ident_spec.get("required", []) or []:
        if not ident.get(req):
            findings.append(("manifest-schema",
                             f"identity.{req} is required — a defaulted {req} is a guess, not intake"))
    allowed_ident = set(ident_spec.get("required", []) or []) | set(ident_spec.get("optional", []) or [])
    for key in sorted(ident):
        if allowed_ident and key not in allowed_ident:
            findings.append(("manifest-schema", f"unknown identity key 'identity.{key}'"))

    allowed_cell = set(schema.get("input_cell", []) or [])
    if allowed_cell:
        # Merge every policy-declared redact tag: a new regime's tag never needs a schema edit.
        for spec in (render.load_policy().get("regimes", {}) or {}).values():
            allowed_cell.update((spec or {}).get("redact_tags", []) or [])
        for key, cell in sorted((manifest.get("inputs") or {}).items()):
            if not isinstance(cell, dict):
                continue
            for field in sorted(cell):
                if field not in allowed_cell:
                    findings.append(("manifest-schema", f"unknown cell field 'inputs.{key}.{field}'"))

    # A content key must address a section of the composed structure (archetype + function pack,
    # BEFORE altitude shaping — content for an altitude-dropped section is still addressable).
    sections = {s["id"] for s in render.apply_function(
        archetype.get("structure", []) or [], render.load_function(ident.get("function", "")))}
    for key in sorted(manifest.get("content") or {}):
        if key not in sections:
            findings.append(("manifest-schema",
                             f"content key '{key}' does not match any section of the composed structure"))
    return findings


def _has_substance(slide):
    """A slide has substance iff at least one block carries a non-empty text field (#52)."""
    for block in slide.get("blocks", []) or []:
        for field, value in block.items():
            if field != "type" and isinstance(value, str) and value.strip():
                return True
    return False


def gate_completeness(deck_ir, archetype):
    findings = []
    required = [s["id"] for s in archetype.get("structure", []) or [] if s.get("required")]
    slides = {s["id"]: s for s in deck_ir.get("slides", [])}
    for sid in required:
        slide = slides.get(sid)
        if slide is None:
            findings.append(("completeness", f"required section '{sid}' is missing from the deck-IR"))
        elif not _has_substance(slide):
            findings.append(("completeness", f"required section '{sid}' has no content blocks (empty slide)"))
        elif not slide.get("title") or slide.get("title") == sid:
            findings.append(("completeness",
                             f"required section '{sid}' has no title (the raw section id would render as the heading)"))
    return findings


def gate_grounding_labeled(deck_ir, acc, ledger):
    findings = []
    for key in sorted(acc["unresolved"]):
        findings.append(("grounding-labeled", f"binding '{{{{{key}}}}}' does not resolve to any inputs-ledger cell"))
    for key in sorted(acc.get("invalid_provenance", ())):   # fail closed (#53): rendered as assumed
        prov = (ledger.get(key) or {}).get("provenance")
        findings.append(("grounding-labeled",
                         f"cell '{key}' provenance '{prov}' is not one of sourced|assumed"))
    appendix_keys = {a["binding"] for a in deck_ir.get("review_appendix", [])}
    for key in sorted(acc["assumed"]):
        cell = ledger.get(key, {})
        if key not in appendix_keys:
            findings.append(("grounding-labeled", f"assumed value '{key}' is used but not in the review appendix"))
        if not str(cell.get("assumption", "")).strip():
            findings.append(("grounding-labeled", f"assumed value '{key}' has no 'assumption' note"))
        if cell.get("review_required") is not True:
            findings.append(("grounding-labeled", f"assumed value '{key}' is missing 'review_required: true'"))
    return findings


def gate_audience_fit(deck_ir, archetype):
    findings = []
    altitude = deck_ir.get("altitude", "")
    shaping = (archetype.get("altitude_shaping", {}) or {}).get(altitude, {}) or {}
    budget = shaping.get("max_slides")
    n = len(deck_ir.get("slides", []))
    if isinstance(budget, int) and n > budget:
        findings.append(("audience-fit", f"{n} slides exceed the {altitude} budget of {budget}"))
    return findings


def gate_params_in_bounds(manifest, archetype):
    findings = []
    altitude = (manifest.get("identity") or {}).get("audience_altitude", "")
    bounds = (archetype.get("deliverable_bounds", {}) or {}).get(altitude, {}) or {}
    for d in manifest.get("deliverables", []) or []:
        dtype = d.get("type")
        dbounds = bounds.get(dtype, {}) or {}
        for param, rule in dbounds.items():
            allow = rule.get("allow") if isinstance(rule, dict) else None
            if allow is not None and d.get(param) is not None and d[param] not in allow:
                findings.append(("deliverable-params-in-bounds",
                                 f"{dtype}.{param}='{d[param]}' not allowed at {altitude} (allow: {allow})"))
    return findings


def gate_no_action_considered(manifest, archetype):
    """The solution-space baseline (RFC-0001 §13; #30): any meeting that compares options (a section
    of kind `option_list`) must include the *no-action* option, so the often-ignored 'do nothing'
    baseline is always on the table. Structural + decidable, altitude-independent: one option in the
    section's content carries `no_action: true`. Vacuous (passes) for archetypes with no solution
    space — only `decision` declares an option_list today."""
    findings = []
    content = manifest.get("content", {}) or {}
    for sec in archetype.get("structure", []) or []:
        if sec.get("kind") != "option_list":
            continue
        c = content.get(sec["id"], {}) if isinstance(content, dict) else {}
        options = (c or {}).get("options", []) or []
        if not any(isinstance(o, dict) and o.get("no_action") for o in options):
            findings.append(("no-action-considered",
                             f"option_list section '{sec['id']}' has no no-action option "
                             "(flag one option `no_action: true` so the baseline is compared)"))
    return findings


def gate_classification_valid(manifest):
    """Phase-B classification (#27): if a meeting carries `discovery_intake.classification`, its
    cluster / complexity / decision_risk must be values the taxonomy (os/intake/classification.yaml)
    allows. Structural + decidable; an absent classification passes (it is optional intake)."""
    findings = []
    di = manifest.get("discovery_intake") or {}
    cls = di.get("classification") if isinstance(di, dict) else None
    if not isinstance(cls, dict):
        return findings
    tax = render.load_classification()
    for dim in ("cluster", "complexity", "decision_risk"):
        allowed = tax.get(dim, []) or []
        val = cls.get(dim)
        if val is not None and allowed and val not in allowed:
            findings.append(("classification-valid",
                             f"discovery_intake.classification.{dim}='{val}' not in {allowed}"))
    return findings


def gate_questions_valid():
    """Phase-C data integrity (RFC-0003, #28): the adaptive question tree + routing cannot drift from
    the taxonomy. Structural + decidable, manifest-independent (it validates the shipped os/intake
    data). Vacuous if the files are absent. Checks: every `clusters` key is a taxonomy cluster; every
    question has id + ask + a level in `levels`; routing complexity keys + level values are valid;
    every escalation rule references a taxonomy-valid cluster + decision_risk."""
    findings = []
    tree, routing = render.load_questions(), render.load_routing()
    if not tree and not routing:
        return findings
    tax = render.load_classification()
    clusters = set(tax.get("cluster", []) or [])
    risks = set(tax.get("decision_risk", []) or [])
    complexities = set(tax.get("complexity", []) or [])
    levels = set(tree.get("levels", []) or [])
    groups = [("common", tree.get("common", []))] + list((tree.get("clusters", {}) or {}).items())
    for name, qs in groups:
        if name != "common" and clusters and name not in clusters:
            findings.append(("questions-valid", f"question tree cluster '{name}' is not in the taxonomy"))
        for q in qs or []:
            if not (isinstance(q, dict) and q.get("id") and q.get("ask")):
                findings.append(("questions-valid", f"a question in '{name}' is missing id/ask"))
            elif levels and q.get("level") not in levels:
                findings.append(("questions-valid",
                                 f"question '{q.get('id')}' has level '{q.get('level')}' not in {sorted(levels)}"))
    for comp, lvl in (routing.get("by_complexity", {}) or {}).items():
        if complexities and comp not in complexities:
            findings.append(("questions-valid", f"routing by_complexity key '{comp}' is not a taxonomy complexity"))
        if levels and lvl not in levels:
            findings.append(("questions-valid", f"routing by_complexity['{comp}']='{lvl}' is not a level"))
    for rule in (routing.get("escalate_to_architecture", []) or []):
        if clusters and rule.get("cluster") not in clusters:
            findings.append(("questions-valid", f"escalation cluster '{rule.get('cluster')}' is not in the taxonomy"))
        if risks and rule.get("decision_risk") not in risks:
            findings.append(("questions-valid",
                             f"escalation decision_risk '{rule.get('decision_risk')}' is not in the taxonomy"))
    return findings


def gate_topology_valid(manifest):
    """Topology integrity (RFC-0004, #22): if a manifest has a `topology:` block, every edge from/to
    references a declared node id, and every node `kind` / edge `pattern` is in the architecture
    deliverable's vocabulary. Structural + decidable; absent topology passes. (Node-label grounding
    is handled at render in build_topology_ir — labeled + into the topology review appendix.)"""
    findings = []
    spec = manifest.get("topology")
    if not isinstance(spec, dict):
        return findings
    vocab = (render.load_deliverable("architecture") or {}).get("vocab", {}) or {}
    kinds, patterns = set(vocab.get("node_kind", []) or []), set(vocab.get("edge_pattern", []) or [])
    node_ids = set()
    for nd in spec.get("nodes", []) or []:
        node_ids.add(nd.get("id"))
        if kinds and nd.get("kind") not in kinds:
            findings.append(("topology-valid",
                             f"node '{nd.get('id')}' kind '{nd.get('kind')}' not in {sorted(kinds)}"))
    for e in spec.get("edges", []) or []:
        for end in ("from", "to"):
            if e.get(end) not in node_ids:
                findings.append(("topology-valid", f"edge {end}='{e.get(end)}' references an undeclared node"))
        if patterns and e.get("pattern") not in patterns:
            findings.append(("topology-valid",
                             f"edge '{e.get('from')}'->'{e.get('to')}' pattern '{e.get('pattern')}' not in {sorted(patterns)}"))
    return findings


def gate_registry_params(manifest):
    """Every deliverable's params are within the registry's declared enums (RFC-0002 §4)."""
    findings = []
    for d in manifest.get("deliverables", []) or []:
        if not isinstance(d, dict):
            continue
        dtype = d.get("type")
        reg = render.load_deliverable(dtype)
        if reg is None:
            findings.append(("deliverable-params", f"deliverable type '{dtype}' has no registry entry"))
            continue
        params = reg.get("params", {}) or {}
        for k, v in d.items():
            if k == "type":
                continue
            spec = params.get(k)
            if spec is None:
                findings.append(("deliverable-params", f"{dtype}.{k} is not a declared param of '{dtype}'"))
                continue
            enum = spec.get("enum") if isinstance(spec, dict) else None
            if enum is not None and v not in enum:
                findings.append(("deliverable-params", f"{dtype}.{k}='{v}' not in {enum}"))
    return findings


def gate_confidentiality(manifest, failed_gate_ids):
    """The enterprise lens (RFC-0001 §11): regimes are known, their mandatory gates are green, and
    no redact-tagged cell sits in a `public`-classified meeting. `failed_gate_ids` is the explicit
    dependency on the other gates' results (#60) — the runner passes what already failed."""
    findings = []
    policy = render.load_policy()
    if not policy:
        return findings
    regimes = (manifest.get("context", {}) or {}).get("regulatory", []) or []
    classification = manifest.get("classification") or policy.get("default")
    for r in regimes:
        spec = (policy.get("regimes", {}) or {}).get(r)
        if spec is None:
            findings.append(("confidentiality", f"unknown regulatory regime '{r}' (not in the policy)"))
            continue
        for g in spec.get("mandatory_gates", []) or []:
            if g in failed_gate_ids:
                findings.append(("confidentiality", f"{r} makes gate '{g}' mandatory, but it failed"))
    if classification == "public":
        tags = render.redact_tags_for(manifest, policy)
        for key, cell in (manifest.get("inputs", {}) or {}).items():
            if isinstance(cell, dict) and any(cell.get(t) for t in tags):
                findings.append(("confidentiality", f"sensitive cell '{key}' in a 'public'-classified meeting"))
    return findings


def gate_rubric(manifest, deck_ir, failed_gate_ids):
    """Score the deck-IR against the data rubric (RFC-0001 §10). Structural + language-agnostic, so
    a non-English board deck passes in its own output_lang (M7). `failed_gate_ids` is the explicit
    dependency for the rubric's grounding requirement (#60)."""
    findings = []
    rubric = {}
    if os.path.exists(RUBRIC):
        with open(RUBRIC, encoding="utf-8") as fh:
            rubric = yamlmini.load_yaml(fh.read())
    ident = manifest.get("identity", {}) or {}
    arch, alt = ident.get("archetype", ""), ident.get("audience_altitude", "")
    crit = (rubric.get(arch, {}) or {}).get(alt)
    if not crit:
        return findings                          # no rubric cell yet — skip (the matrix grows over time)
    present = {s["id"] for s in deck_ir.get("slides", [])}
    for sid in crit.get("require_sections", []) or []:
        if sid not in present:
            findings.append(("rubric", f"{arch}@{alt}: rubric requires section '{sid}'"))
    cap = crit.get("max_slides")
    if isinstance(cap, int) and len(deck_ir.get("slides", [])) > cap:
        findings.append(("rubric", f"{arch}@{alt}: {len(deck_ir['slides'])} slides exceed the rubric's {cap}"))
    if crit.get("grounding") and "grounding-labeled" in failed_gate_ids:
        findings.append(("rubric", f"{arch}@{alt}: rubric requires grounding-labeled green"))
    return findings


def run_all(manifest, archetype, deck_ir, acc, ledger):
    """Run every gate and aggregate the findings, in the CLI's reporting order. The two gates that
    inspect other gates' results receive them as a parameter — no hidden ordering contract (#60)."""
    findings = []
    findings += gate_manifest_schema(manifest, archetype)
    findings += gate_completeness(deck_ir, archetype)
    findings += gate_grounding_labeled(deck_ir, acc, ledger)
    findings += gate_audience_fit(deck_ir, archetype)
    findings += gate_params_in_bounds(manifest, archetype)
    findings += gate_no_action_considered(manifest, archetype)
    findings += gate_classification_valid(manifest)
    findings += gate_questions_valid()
    findings += gate_topology_valid(manifest)
    findings += gate_registry_params(manifest)
    findings += gate_rubric(manifest, deck_ir, {g for g, _ in findings})
    findings += gate_confidentiality(manifest, {g for g, _ in findings})
    return findings


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    if len(sys.argv) < 2:
        print("usage: eamos_lint.py <manifest.yaml>")
        return 2
    manifest = yamlmini.load_yaml(_cli.read_text(sys.argv[1], "manifest"))
    # A missing archetype is reported red by gate_manifest_schema (#59); 'review' here only
    # scaffolds the remaining checks so the whole report still prints.
    archetype = render.load_archetype((manifest.get("identity") or {}).get("archetype") or "review")
    deck_ir, acc = render.build_deck_ir(manifest, archetype)
    ledger = render.scorecard_ledger(manifest)   # include computed scorecard totals (#23) for grounding

    findings = run_all(manifest, archetype, deck_ir, acc, ledger)
    if findings:
        print("eamos_lint: FAIL\n")
        for gate, msg in findings:
            print(f"  [{gate}] {msg}")
        print(f"\n{len(findings)} gate failure(s).")
        return 1
    print(f"eamos_lint: OK — all gates green "
          f"({len(deck_ir['slides'])} slides, {len(deck_ir['review_appendix'])} to verify)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
