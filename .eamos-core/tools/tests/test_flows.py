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

Q2 = os.path.join(EX, "series", "qbr-q2-2026.yaml")
Q3 = os.path.join(EX, "qbr-c-level.yaml")
OUTCOMES = os.path.join(EX, "series", "qbr-q3-outcomes.yaml")
CSV = os.path.join(EX, "intake", "q3-kpis.csv")
BOARD = os.path.join(EX, "board-confidential.yaml")


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


class TestRedaction(unittest.TestCase):
    def test_pii_cell_masked_and_no_leak(self):
        m = _yaml(BOARD)
        n = render.apply_redaction(m, render.load_policy())
        self.assertGreaterEqual(n, 1)
        cell = m["inputs"]["kpi.churn_named_account"]
        self.assertIn("redatto", cell["value"])
        self.assertNotIn("Rossi", cell["value"])


if __name__ == "__main__":
    unittest.main()
