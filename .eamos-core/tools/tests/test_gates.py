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
        "planning-release", "retro-sprint", "discovery-product", "one-on-one", "vendor-prework"]


def load(name):
    with open(os.path.join(EXAMPLES, f"{name}.yaml"), encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


def run_gates(m):
    arch = render.load_archetype(m["identity"]["archetype"])
    deck, acc = render.build_deck_ir(m, arch)
    ledger = render.scorecard_ledger(m)   # include computed scorecard totals (#23)
    eamos_lint.failures.clear()
    eamos_lint.gate_completeness(deck, arch)
    eamos_lint.gate_grounding_labeled(deck, acc, ledger)
    eamos_lint.gate_audience_fit(deck, arch)
    eamos_lint.gate_params_in_bounds(m, arch)
    eamos_lint.gate_no_action_considered(m, arch)
    eamos_lint.gate_classification_valid(m)
    eamos_lint.gate_registry_params(m)
    eamos_lint.gate_rubric(m, deck)
    eamos_lint.gate_confidentiality(m)
    return {g for g, _ in eamos_lint.failures}


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

    def test_sox_makes_grounding_mandatory(self):
        m = load("board-confidential")
        m["inputs"]["kpi.arr"] = {"label": "ARR", "provided": False, "provenance": "assumed"}
        ids = run_gates(m)
        self.assertIn("grounding-labeled", ids)
        self.assertIn("confidentiality", ids)   # SOX flags the failed mandatory gate


if __name__ == "__main__":
    unittest.main()
