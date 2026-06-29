#!/usr/bin/env python3
"""Tests for render: determinism, no-divergence across IR families, grounding, and overlays."""

import json
import os
import sys
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
CORE = os.path.dirname(TOOLS)
EXAMPLES = os.path.join(CORE, "orchestrator", "examples")
sys.path.insert(0, TOOLS)
import yamlmini  # noqa: E402
import render    # noqa: E402

REFS = ["qbr-c-level", "esc-decision", "qbr-finance", "rca-eng", "board-confidential",
        "planning-release", "retro-sprint", "discovery-product", "one-on-one", "vendor-prework"]


def load(name):
    with open(os.path.join(EXAMPLES, f"{name}.yaml"), encoding="utf-8") as fh:
        m = yamlmini.load_yaml(fh.read())
    return m, render.load_archetype(m["identity"]["archetype"])


def _arr(builder_out):
    return builder_out


class TestDeterminism(unittest.TestCase):
    def test_all_ir_byte_identical(self):
        for name in REFS:
            m, arch = load(name)
            for builder in (render.build_deck_ir, render.build_infographic_ir,
                            render.build_data_ir, render.build_graph_ir, render.build_quiz_ir):
                with self.subTest(manifest=name, ir=builder.__name__):
                    a, _ = builder(m, arch)
                    b, _ = builder(m, arch)
                    self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))


class TestNoDivergence(unittest.TestCase):
    def test_arr_identical_across_projections(self):
        m, arch = load("qbr-c-level")
        deck, _ = render.build_deck_ir(m, arch)
        info, _ = render.build_infographic_ir(m, arch)
        data, _ = render.build_data_ir(m, arch)
        mind, _ = render.build_graph_ir(m, arch)
        quiz, _ = render.build_quiz_ir(m, arch)
        arr_deck = next(b["value"] for s in deck["slides"] for b in s["blocks"] if b.get("label") == "ARR")
        arr_info = next(s["value"] for s in info["stats"] if s["label"] == "ARR")
        arr_data = next(r["value"] for r in data["rows"] if r["label"] == "ARR")
        arr_mind = next(l.split(": ", 1)[1] for b in mind["branches"] for l in b["leaves"] if l.startswith("ARR:"))
        arr_quiz = next(q["a"] for q in quiz["questions"] if "ARR" in q.get("q", "") and q["kind"] == "graded")
        self.assertEqual({arr_deck, arr_info, arr_data, arr_mind, arr_quiz}, {"12.4M€"})


class TestGrounding(unittest.TestCase):
    def test_assumed_labeled_and_in_appendix(self):
        m, arch = load("qbr-c-level")
        deck, acc = render.build_deck_ir(m, arch)
        texts = " ".join(b.get("text", "") for s in deck["slides"] for b in s["blocks"])
        self.assertIn("⟨", texts)                              # assumed value is labeled
        self.assertTrue(deck["review_appendix"])               # and collected for review
        self.assertIn("kpi.churn_q3", {a["binding"] for a in deck["review_appendix"]})

    def test_sourced_value_is_plain(self):
        m, arch = load("qbr-c-level")
        deck, _ = render.build_deck_ir(m, arch)
        arr = next(b["value"] for s in deck["slides"] for b in s["blocks"] if b.get("label") == "ARR")
        self.assertEqual(arr, "12.4M€")                        # sourced -> no marker


class TestDecisionContract(unittest.TestCase):
    def test_decision_contract_renders_through_md(self):
        import emit_md
        m, arch = load("esc-decision")
        deck, _ = render.build_deck_ir(m, arch)
        dc = next(s for s in deck["slides"] if s["kind"] == "decision_contract")   # Phase G section present
        types = [b["type"] for b in dc["blocks"]]
        self.assertIn("next_step", types)                          # the chosen next step
        self.assertGreaterEqual(types.count("residual_risk"), 1)   # ≥1 residual risk (distinct from mitigations)
        md = emit_md.render_md(deck)
        self.assertIn("Prossimo passo", md)                        # next_step label (output_lang it)
        self.assertIn("Rischio residuo", md)                       # residual_risk label


class TestPreWorkPack(unittest.TestCase):
    def test_pack_composes_onto_decision(self):
        m, arch = load("vendor-prework")                  # decision archetype, function: pre-work
        deck, _ = render.build_deck_ir(m, arch)
        ids = [s["id"] for s in deck["slides"]]
        for sid in ("use_case_matrix", "moscow_requirements", "architectural_constraints"):
            self.assertIn(sid, ids)                        # the pack's three sections compose in
        self.assertLess(ids.index("use_case_matrix"), ids.index("options"))   # pre-work precedes options


class TestDiscoveryIntake(unittest.TestCase):
    def test_l0_l1_l2_typed_capture(self):
        m, _ = load("esc-decision")
        di = m["discovery_intake"]
        self.assertTrue(di["intent"])                                   # L0 — intent present
        self.assertIsInstance(di["domain"]["stakeholders"], list)       # L1 — domain framing typed
        self.assertIsInstance(di["domain"]["existing_systems"], list)
        self.assertTrue(di["domain"]["current_pain"])
        self.assertIsInstance(di["constraints"]["dependencies"], list)  # L2 — constraints typed
        self.assertTrue(di["constraints"]["budget_range"])


class TestOverlays(unittest.TestCase):
    def test_altitude_reorders(self):
        m, arch = load("qbr-c-level")
        c, _ = render.build_deck_ir(m, arch, altitude="c-level")
        mgr, _ = render.build_deck_ir(m, arch, altitude="manager")
        c_ids = [s["id"] for s in c["slides"]]
        mgr_ids = [s["id"] for s in mgr["slides"]]
        self.assertNotEqual(c_ids, mgr_ids)                    # altitude changes the order
        self.assertEqual(c_ids[1], "decisions_required")       # c-level leads with the ask

    def test_function_swap_only_changes_one_section(self):
        m, arch = load("qbr-c-level")
        fin, _ = render.build_deck_ir(m, arch, function="finance")
        eng, _ = render.build_deck_ir(m, arch, function="engineering")
        fin_ids = {s["id"] for s in fin["slides"]}
        eng_ids = {s["id"] for s in eng["slides"]}
        self.assertIn("variance_attestation", fin_ids)
        self.assertIn("reliability_notes", eng_ids)
        self.assertEqual(fin_ids - {"variance_attestation"}, eng_ids - {"reliability_notes"})


if __name__ == "__main__":
    unittest.main()
