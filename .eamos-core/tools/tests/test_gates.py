#!/usr/bin/env python3
"""Tests that the gates pass on good manifests and have teeth on bad ones."""

import os
import sys
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
CORE = os.path.dirname(TOOLS)
EXAMPLES = os.path.join(CORE, "orchestrator", "examples")
sys.path.insert(0, TOOLS)
import yamlmini    # noqa: E402
import render      # noqa: E402
import eamos_lint  # noqa: E402

REFS = ["qbr-c-level", "esc-decision", "qbr-finance", "rca-eng", "board-confidential",
        "planning-release", "retro-sprint", "discovery-product", "one-on-one", "vendor-prework",
        "vendor-selection"]


def load(name):
    with open(os.path.join(EXAMPLES, f"{name}.yaml"), encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def run_findings(m):
    arch = render.load_archetype(m["identity"]["archetype"])
    deck, acc = render.build_deck_ir(m, arch)
    ledger = render.scorecard_ledger(m)   # include computed scorecard totals (#23)
    return eamos_lint.run_all(m, arch, deck, acc, ledger)   # pure: no global state to clear (#60)


def run_gates(m):
    return {g for g, _ in run_findings(m)}


def _deliverable(m, dtype):
    return next(d for d in m["deliverables"] if d.get("type") == dtype)


class TestGood(unittest.TestCase):
    def test_reference_manifests_pass(self):
        for name in REFS:
            with self.subTest(manifest=name):
                self.assertEqual(run_gates(load(name)), set())


class TestTeeth(unittest.TestCase):
    def test_unresolved_binding(self):
        m = load("qbr-c-level")
        m["content"]["variance_commentary"]["body"] = "spettro {{kpi.ghost}}"
        self.assertIn("grounding-labeled", run_gates(m))

    def test_assumed_missing_review_required(self):
        m = load("qbr-c-level")
        m["inputs"]["kpi.churn_q3"]["review_required"] = False
        self.assertIn("grounding-labeled", run_gates(m))

    def test_invalid_classification(self):
        m = load("vendor-prework")
        m["discovery_intake"]["classification"]["cluster"] = "teleportation"   # not in the taxonomy
        self.assertIn("classification-valid", run_gates(m))

    def test_question_tree_drift(self):
        orig = render.load_questions
        render.load_questions = lambda: {"levels": ["surface"], "clusters": {"teleportation": []}}
        try:
            findings = eamos_lint.gate_questions_valid()            # tree cluster not in the taxonomy
            self.assertIn("questions-valid", {g for g, _ in findings})
        finally:
            render.load_questions = orig

    def test_topology_edge_to_undeclared_node(self):
        m = load("vendor-prework")
        m["topology"]["edges"].append({"from": "platform", "to": "ghost", "pattern": "rest"})
        self.assertIn("topology-valid", run_gates(m))

    def test_topology_out_of_vocab_pattern(self):
        m = load("vendor-prework")
        m["topology"]["edges"][0]["pattern"] = "telepathy"     # not in edge_pattern vocab
        self.assertIn("topology-valid", run_gates(m))

    def test_no_action_baseline_required(self):
        m = load("esc-decision")
        for o in m["content"]["options"]["options"]:
            o.pop("no_action", None)                       # strip the no-action flag from every option
        self.assertIn("no-action-considered", run_gates(m))

    def test_param_out_of_bounds(self):
        m = load("qbr-c-level")
        _deliverable(m, "infographic")["visual_style"] = "bricks"   # board allows only professional/scientific
        self.assertIn("deliverable-params-in-bounds", run_gates(m))

    def test_undeclared_param(self):
        m = load("qbr-c-level")
        _deliverable(m, "infographic")["color"] = "blue"            # not a declared registry param
        self.assertIn("deliverable-params", run_gates(m))

    def test_confidentiality_public_with_pii(self):
        m = load("board-confidential")
        m["classification"] = "public"
        self.assertIn("confidentiality", run_gates(m))

    def test_typoed_cell_field_fails_schema(self):
        m = load("qbr-c-level")
        m["inputs"]["kpi.arr"]["provenence"] = m["inputs"]["kpi.arr"].pop("provenance")   # typo (#59)
        findings = run_findings(m)
        self.assertIn("manifest-schema", {g for g, _ in findings})
        msgs = [msg for g, msg in findings if g == "manifest-schema"]
        self.assertTrue(any("inputs.kpi.arr.provenence" in msg for msg in msgs))   # path-named

    def test_typoed_content_key_fails_schema(self):
        m = load("qbr-c-level")
        m["content"]["exec_sumary"] = m["content"].pop("exec_summary")             # typo (#59)
        self.assertIn("manifest-schema", run_gates(m))

    def test_typoed_top_level_key_fails_schema(self):
        m = load("qbr-c-level")
        m["carry_foward"] = m.pop("carry_forward")                                 # typo (#59)
        self.assertIn("manifest-schema", run_gates(m))

    def test_missing_archetype_fails_schema(self):
        m = load("qbr-c-level")
        del m["identity"]["archetype"]                    # a defaulted archetype is a guess (#59)
        arch = render.load_archetype("review")
        msgs = [msg for _, msg in eamos_lint.gate_manifest_schema(m, arch)]
        self.assertTrue(any("identity.archetype is required" in msg for msg in msgs))

    def test_unknown_identity_key_fails_schema(self):
        m = load("qbr-c-level")
        m["identity"]["archetyp"] = "review"                                       # typo (#59)
        self.assertIn("manifest-schema", run_gates(m))

    def test_policy_redact_tags_stay_valid_cell_fields(self):
        m = load("board-confidential")                    # carries pii-tagged cells
        self.assertNotIn("manifest-schema", run_gates(m))

    def test_typoed_provenance_fails_closed(self):
        m = load("qbr-c-level")
        m["inputs"]["kpi.arr"]["provenance"] = "asumed"     # one keystroke from silent fabrication (#53)
        findings = run_findings(m)
        self.assertIn("grounding-labeled", {g for g, _ in findings})
        msgs = [msg for g, msg in findings if g == "grounding-labeled"]
        self.assertTrue(any("not one of sourced|assumed" in msg for msg in msgs))

    def test_missing_provenance_fails_closed(self):
        m = load("qbr-c-level")
        del m["inputs"]["kpi.arr"]["provenance"]
        self.assertIn("grounding-labeled", run_gates(m))

    def test_empty_manifest_fails_completeness_per_required_section(self):
        m = load("qbr-c-level")
        m["content"], m["inputs"] = {}, {}          # an all-empty manifest must not ship green (#52)
        findings = run_findings(m)
        self.assertIn("completeness", {g for g, _ in findings})
        msgs = [msg for g, msg in findings if g == "completeness"]
        self.assertEqual(len(msgs), 5)              # one message per empty required review section

    def test_empty_required_section_fails_completeness(self):
        m = load("qbr-c-level")
        m["content"]["variance_commentary"]["body"] = ""
        self.assertIn("completeness", run_gates(m))

    def test_untitled_required_section_fails_completeness(self):
        m = load("qbr-c-level")
        del m["content"]["exec_summary"]["title"]   # title falls back to the raw section id
        self.assertIn("completeness", run_gates(m))

    def test_sox_makes_grounding_mandatory(self):
        m = load("board-confidential")
        m["inputs"]["kpi.arr"] = {"label": "ARR", "provided": False, "provenance": "assumed"}
        ids = run_gates(m)
        self.assertIn("grounding-labeled", ids)
        self.assertIn("confidentiality", ids)   # SOX flags the failed mandatory gate


class TestUserErrors(unittest.TestCase):
    def test_empty_identity_does_not_crash_gates(self):
        arch = render.load_archetype("review")
        m = load("qbr-c-level")
        m["identity"] = None                       # `identity:` present but empty (#58)
        eamos_lint.gate_params_in_bounds(m, arch)  # must not raise AttributeError
        deck, _ = render.build_deck_ir(m, arch)
        self.assertTrue(deck["slides"])


if __name__ == "__main__":
    unittest.main()
