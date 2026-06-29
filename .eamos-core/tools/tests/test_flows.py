#!/usr/bin/env python3
"""Tests for the cross-cutting flows: series store, intake, facilitate, and redaction."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
CORE = os.path.dirname(TOOLS)
EX = os.path.join(CORE, "orchestrator", "examples")
sys.path.insert(0, TOOLS)
import yamlmini    # noqa: E402
import render      # noqa: E402
import series      # noqa: E402
import intake      # noqa: E402
import facilitate  # noqa: E402

try:
    import pptx  # noqa: F401
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

Q2 = os.path.join(EX, "series", "qbr-q2-2026.yaml")
Q3 = os.path.join(EX, "qbr-c-level.yaml")
OUTCOMES = os.path.join(EX, "series", "qbr-q3-outcomes.yaml")
CSV = os.path.join(EX, "intake", "q3-kpis.csv")
BOARD = os.path.join(EX, "board-confidential.yaml")
ESC = os.path.join(EX, "esc-decision.yaml")


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def _json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


class TestSeries(unittest.TestCase):
    def test_close_then_open_carries_forward(self):
        with tempfile.TemporaryDirectory() as d:
            store = os.path.join(d, "s.json")
            self.assertEqual(quiet(series.close, Q2, store), 0)
            s = _json(store)
            self.assertIn("Q2-2026", s["instances"])
            self.assertTrue(s["decision_log"])
            digest = os.path.join(d, "cf.json")
            self.assertEqual(quiet(series.open_, Q3, store, digest), 0)
            cf = _json(digest)
            self.assertTrue(cf["prior_decisions"])
            self.assertTrue(cf["open_actions"])
            arr = next(x for x in cf["kpi_movement"] if x["kpi"] == "kpi.arr")
            self.assertEqual((arr["prior"], arr["current"], arr["direction"]), ("11.8M€", "12.4M€", "up"))


class TestIntake(unittest.TestCase):
    def test_reorg_dedupe_and_gap_fill(self):
        with tempfile.TemporaryDirectory() as d:
            store = os.path.join(d, "s.json")
            quiet(series.close, Q2, store)
            ledger, prov = intake.reorganize([CSV], store)
            self.assertEqual(ledger["kpi.arr"]["via"], "intake/csv")        # current (CSV) wins dedupe
            self.assertEqual(ledger["kpi.arr"]["value"], "12.4M€")
            self.assertEqual(ledger["kpi.nrr_target"]["via"], "intake/series")  # gap-filled from prior
            self.assertGreaterEqual(prov["overridden"], 1)


class TestAdaptiveQuestions(unittest.TestCase):
    def _data(self):
        return render.load_questions(), render.load_routing()

    def test_high_complexity_reaches_architecture(self):
        tree, routing = self._data()
        cls = {"cluster": "system_replacement", "complexity": "high", "decision_risk": "high"}
        depth, sel = intake.select_questions(cls, tree, routing)
        self.assertEqual(depth, "architecture")
        ids = [q["id"] for q in sel]
        self.assertIn("integrations", ids)                  # the architecture-level question is asked
        self.assertEqual(ids[:2], ["intent", "current_pain"])   # common surface questions lead

    def test_low_complexity_stays_surface(self):
        tree, routing = self._data()
        cls = {"cluster": "integration", "complexity": "low", "decision_risk": "low"}
        depth, sel = intake.select_questions(cls, tree, routing)
        self.assertEqual(depth, "surface")
        self.assertNotIn("realtime", [q["id"] for q in sel])    # the architecture question is skipped

    def test_escalation_overrides_low_complexity(self):
        tree, routing = self._data()
        cls = {"cluster": "integration", "complexity": "low", "decision_risk": "high"}
        depth, _ = intake.select_questions(cls, tree, routing)
        self.assertEqual(depth, "architecture")             # escalate rule {integration, high} fires

    def test_questions_op_on_vendor_prework(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = intake.questions_op(os.path.join(EX, "vendor-prework.yaml"))
        self.assertEqual(rc, 0)
        self.assertIn("What no longer scales?", buf.getvalue())   # system_replacement, depth architecture


class TestFacilitate(unittest.TestCase):
    def test_followup_requires_outcomes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(quiet(facilitate.followup, Q3, None, os.path.join(d, "s.json"), None), 1)

    def test_followup_carries_outcomes_into_store(self):
        with tempfile.TemporaryDirectory() as d:
            store = os.path.join(d, "s.json")
            rc = quiet(facilitate.followup, Q3, OUTCOMES, store, os.path.join(d, "m.md"))
            self.assertEqual(rc, 0)
            s = _json(store)
            q3 = [a for a in s["open_actions"] if a["from"] == "Q3-2026"]
            self.assertEqual(len(q3), 2)
            self.assertTrue(all(a.get("owner") and a.get("due") for a in q3))

    def test_prep_runs(self):
        self.assertEqual(quiet(facilitate.prep, Q3, 60), 0)

    def test_prep_renders_attendee_roster(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = facilitate.prep(ESC, 60)          # esc-decision.yaml carries an attendees roster
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("Partecipanti", out)          # roster header (output_lang it)
        self.assertIn("Sponsor / Business owner", out)
        self.assertIn("RACI: A", out)
        self.assertIn("entra da raccomandazione", out)   # the vendor joins late on purpose

    def test_prep_without_roster_renders_nothing(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = facilitate.prep(Q3, 60)           # qbr-c-level.yaml has no attendees block
        self.assertEqual(rc, 0)
        self.assertNotIn("RACI:", buf.getvalue())  # absent roster → nothing rendered

    def test_prep_discovery_decision_template(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = facilitate.prep(ESC, 75, template="discovery-decision")
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        for phase in ("Raccolta input", "Classificazione dal vivo", "Domande mirate",
                      "Sintesi strutturata", "Inquadramento decisione"):
            self.assertIn(phase, out)              # the five flow phases (output_lang it)
        self.assertIn("Partecipanti", out)         # the roster header still leads (#25)

    def test_template_boxes_clamp_to_range(self):
        t = facilitate.TIMEBOX_TEMPLATES["discovery-decision"]
        self.assertEqual(sum(facilitate._template_boxes(t, 75)), 75)
        self.assertEqual(sum(facilitate._template_boxes(t, 60)), 60)    # min total (10/5/20/10/15)
        self.assertEqual(sum(facilitate._template_boxes(t, 80)), 80)    # max total (targeted at 40)
        self.assertEqual(sum(facilitate._template_boxes(t, 120)), 80)   # caps at 80
        self.assertEqual(sum(facilitate._template_boxes(t, 30)), 60)    # floors at 60


class TestRedaction(unittest.TestCase):
    def test_pii_cell_masked_and_no_leak(self):
        m = _yaml(BOARD)
        n = render.apply_redaction(m, render.load_policy())
        self.assertGreaterEqual(n, 1)
        cell = m["inputs"]["kpi.churn_named_account"]
        self.assertIn("redatto", cell["value"])
        self.assertNotIn("Rossi", cell["value"])


@unittest.skipUnless(HAS_PPTX, "python-pptx not installed (the deck connector is optional)")
class TestIntakeDeck(unittest.TestCase):
    def test_deck_roundtrip(self):
        import emit_pptx
        m = _yaml(Q3)
        deck_ir, _ = render.build_deck_ir(m, render.load_archetype(m["identity"]["archetype"]))
        with tempfile.TemporaryDirectory() as d:
            pptx_path = os.path.join(d, "deck.pptx")
            emit_pptx.build_pptx(deck_ir, pptx_path)
            cells = intake.from_deck(pptx_path)
        self.assertIn("kpi.arr", cells)                 # the deck's KPIs extract back into the ledger
        self.assertEqual(cells["kpi.arr"]["value"], "12.4M€")
        self.assertEqual(cells["kpi.arr"]["via"], "intake/deck")


if __name__ == "__main__":
    unittest.main()
