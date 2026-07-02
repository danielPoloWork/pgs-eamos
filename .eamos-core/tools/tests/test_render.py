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
        "planning-release", "retro-sprint", "discovery-product", "one-on-one", "vendor-prework",
        "vendor-selection"]


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
                            render.build_data_ir, render.build_graph_ir, render.build_quiz_ir,
                            render.build_topology_ir):
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

    def test_invalid_provenance_renders_labeled(self):
        m, arch = load("qbr-c-level")
        m["inputs"]["kpi.arr"]["provenance"] = "asumed"        # typo must fail closed (#53)
        deck, acc = render.build_deck_ir(m, arch)
        arr = next(b["value"] for s in deck["slides"] for b in s["blocks"] if b.get("label") == "ARR")
        self.assertIn("⟨", arr)                                # labeled, not plain
        self.assertIn("kpi.arr", acc["invalid_provenance"])
        self.assertIn("kpi.arr", {a["binding"] for a in deck["review_appendix"]})

    def test_invalid_provenance_fails_closed_across_projections(self):
        m, arch = load("qbr-c-level")
        m["inputs"]["kpi.arr"]["provenance"] = "Assumed"       # wrong case is not the enum (#53)
        info, _ = render.build_infographic_ir(m, arch)
        self.assertTrue(next(s for s in info["stats"] if s["label"] == "ARR")["assumed"])
        data, _ = render.build_data_ir(m, arch)
        self.assertTrue(next(r for r in data["rows"] if r["label"] == "ARR")["assumed"])
        quiz, _ = render.build_quiz_ir(m, arch)
        q = next(q for q in quiz["questions"] if q["kind"] == "graded" and "ARR" in q["q"])
        self.assertTrue(q["assumed"])

    def test_es_deliverable_is_fully_localized(self):
        # An output_lang the chrome doesn't fully cover used to render MIXED-language (#61):
        # Spanish marker, English headings. Now every chrome string localizes together.
        import emit_md
        m, arch = load("qbr-c-level")
        m["context"]["output_lang"] = "es"
        deck, _ = render.build_deck_ir(m, arch)
        md = emit_md.render_md(deck)
        self.assertIn("por verificar", md)                     # grounding marker
        self.assertIn("Riesgo", md)                            # chrome label
        self.assertIn("Verificar antes de la reunión", md)     # review appendix heading
        self.assertNotIn("Verify before the room", md)         # no English fallback leaks

    def test_fr_verify_marker_and_chrome(self):
        import emit_md
        m, arch = load("qbr-c-level")
        m["context"]["output_lang"] = "fr"
        deck, _ = render.build_deck_ir(m, arch)
        md = emit_md.render_md(deck)
        self.assertIn("à vérifier", md)
        self.assertIn("Risque", md)
        self.assertNotIn("Verify before the room", md)

    def test_invalid_provenance_fails_closed_in_topology(self):
        m, arch = load("vendor-prework")
        m["inputs"]["sys.platform"]["provenance"] = "asumed"   # typo must fail closed (#53)
        topo, acc = render.build_topology_ir(m, arch)
        self.assertTrue(next(n for n in topo["nodes"] if n["id"] == "platform")["assumed"])
        self.assertIn("sys.platform", acc["invalid_provenance"])


class TestIRVersion(unittest.TestCase):
    def test_every_projection_is_stamped(self):
        m, arch = load("qbr-c-level")
        for builder in (render.build_deck_ir, render.build_infographic_ir, render.build_data_ir,
                        render.build_graph_ir, render.build_quiz_ir, render.build_topology_ir):
            with self.subTest(ir=builder.__name__):
                ir, _ = builder(m, arch)
                self.assertEqual(ir["ir_version"], render.IR_VERSION)   # versioned contract (#62)
                self.assertEqual(ir["generator"], "eamos-render")


class TestDeliverableParams(unittest.TestCase):
    """The registry knobs must change the output — validated-but-dead is worse than undeclared (#63)."""

    def _quiz_graded(self, count):
        m, arch = load("qbr-c-level")
        for i in range(7):                        # 5 real kpi cells + 7 synthetic = 12 graded candidates
            m["inputs"][f"kpi.zz{i}"] = {"label": f"Z{i}", "value": str(i), "provided": True,
                                         "source": "x", "provenance": "sourced"}
        next(d for d in m["deliverables"] if d["type"] == "interview_quiz")["count"] = count
        quiz, _ = render.build_quiz_ir(m, arch)
        return quiz["questions"]

    def test_quiz_count_caps_graded_questions(self):
        for count, expected in (("short", 5), ("standard", 10), ("long", 12)):
            with self.subTest(count=count):
                graded = [q for q in self._quiz_graded(count) if q["kind"] == "graded"]
                self.assertEqual(len(graded), expected)

    def test_quiz_count_never_caps_discussion(self):
        qs = self._quiz_graded("short")
        self.assertEqual(len([q for q in qs if q["kind"] == "discussion"]), 2)   # both decisions kept

    def test_quiz_cap_is_stable_under_manifest_reordering(self):
        a = [q["q"] for q in self._quiz_graded("short") if q["kind"] == "graded"]
        m, arch = load("qbr-c-level")
        m["inputs"] = dict(reversed(list(m["inputs"].items())))                  # same cells, new order
        for i in range(7):
            m["inputs"][f"kpi.zz{i}"] = {"label": f"Z{i}", "value": str(i), "provided": True,
                                         "source": "x", "provenance": "sourced"}
        next(d for d in m["deliverables"] if d["type"] == "interview_quiz")["count"] = "short"
        quiz, _ = render.build_quiz_ir(m, arch)
        self.assertEqual([q["q"] for q in quiz["questions"] if q["kind"] == "graded"], a)

    def test_mindmap_orientation_changes_layout(self):
        import emit_svg
        m, arch = load("qbr-c-level")
        mind, _ = render.build_graph_ir(m, arch)
        self.assertEqual(mind["orientation"], "horizontal")     # qbr requests horizontal
        horiz = emit_svg.build_mindmap_svg(mind)
        next(d for d in m["deliverables"] if d["type"] == "mindmap")["orientation"] = "vertical"
        mind_v, _ = render.build_graph_ir(m, arch)
        self.assertEqual(mind_v["orientation"], "vertical")
        vert = emit_svg.build_mindmap_svg(mind_v)
        self.assertNotEqual(horiz, vert)                        # the knob changes the output
        self.assertEqual(vert, emit_svg.build_mindmap_svg(mind_v))   # and stays deterministic


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


class TestTopology(unittest.TestCase):
    def test_topology_ir_nodes_edges_grounding_and_svg(self):
        import emit_svg
        m, arch = load("vendor-prework")
        ir, _ = render.build_topology_ir(m, arch)
        self.assertEqual((len(ir["nodes"]), len(ir["edges"])), (4, 3))
        node_ids = {n["id"] for n in ir["nodes"]}
        self.assertTrue(all(e["from"] in node_ids and e["to"] in node_ids for e in ir["edges"]))
        vendorx = next(n for n in ir["nodes"] if n["id"] == "vendorx")
        self.assertTrue(vendorx["assumed"])                       # the vendor system is assumed
        self.assertIn("⟨", vendorx["label"])                      # rendered labeled
        self.assertIn("sys.vendorx", {a["binding"] for a in ir["review_appendix"]})  # + in the appendix
        svg = emit_svg.build_topology_svg(ir)
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("ERP aziendale", svg)                       # a sourced node renders plain


class TestScorecard(unittest.TestCase):
    def test_totals_computed_and_sourced(self):
        m, _ = load("vendor-prework")
        led = render.scorecard_ledger(m)
        self.assertEqual(led["total.build"]["value"], "2.5")   # 0.4*2 + 0.35*2 + 0.25*4
        self.assertEqual(led["total.buy"]["value"], "4.1")     # 0.4*4 + 0.35*5 + 0.25*3
        self.assertEqual(led["total.build"]["provenance"], "sourced")
        self.assertTrue(led["total.buy"]["computed"])

    def test_total_identical_across_projections(self):
        m, arch = load("vendor-prework")
        deck, _ = render.build_deck_ir(m, arch)
        data, _ = render.build_data_ir(m, arch)
        deck_buy = next(b["value"] for s in deck["slides"] for b in s["blocks"] if b.get("label") == "Buy (vendor X)")
        data_buy = next(r["value"] for r in data["rows"] if r["label"] == "Buy (vendor X)")
        self.assertEqual(deck_buy, data_buy)                   # no divergence (one ledger, RFC-0002 §7)
        self.assertEqual(deck_buy, "4.1")

    def test_assumed_input_propagates_to_total(self):
        m, arch = load("vendor-prework")
        m["inputs"]["sc.buy.cost"]["provenance"] = "assumed"   # one score becomes assumed
        m["inputs"]["sc.buy.cost"]["assumption"] = "stima preliminare"
        m["inputs"]["sc.buy.cost"]["review_required"] = True
        self.assertEqual(render.scorecard_ledger(m)["total.buy"]["provenance"], "assumed")  # propagates
        deck, acc = render.build_deck_ir(m, arch)
        self.assertIn("total.buy", acc["assumed"])             # marked assumed on render
        buy = next(b["value"] for s in deck["slides"] for b in s["blocks"] if b.get("label") == "Buy (vendor X)")
        self.assertIn("⟨", buy)                                # rendered labeled
        self.assertIn("total.buy", {a["binding"] for a in deck["review_appendix"]})  # + in the appendix


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
