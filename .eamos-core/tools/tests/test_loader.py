#!/usr/bin/env python3
"""Tests for the dependency-free YAML loader (yamlmini) and the reference manifests."""

import os
import sys
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
CORE = os.path.dirname(TOOLS)
EXAMPLES = os.path.join(CORE, "orchestrator", "examples")
sys.path.insert(0, TOOLS)
import yamlmini  # noqa: E402

REFS = ["qbr-c-level", "esc-decision", "qbr-finance", "rca-eng", "board-confidential",
        "planning-release", "retro-sprint", "discovery-product", "one-on-one"]


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yamlmini.load_yaml(fh.read())


class TestSubset(unittest.TestCase):
    def test_scalars(self):
        d = yamlmini.load_yaml('a: 1\nb: true\nc: yes\nd: "08540"\ne: [x, y]\nf: { k: v }\n')
        self.assertEqual(d["a"], 1)                  # int
        self.assertIs(d["b"], True)                  # bool
        self.assertEqual(d["c"], "yes")              # the "Norway problem" — yes is a string
        self.assertEqual(d["d"], "08540")            # leading zero stays a string
        self.assertEqual(d["e"], ["x", "y"])         # flow list
        self.assertEqual(d["f"], {"k": "v"})         # flow map

    def test_colon_in_quoted_value(self):
        d = yamlmini.load_yaml('k: "a: b — c"\n')
        self.assertEqual(d["k"], "a: b — c")

    def test_block_scalar(self):
        d = yamlmini.load_yaml("x: |\n  line1\n  line2\n")
        self.assertEqual(d["x"], "line1\nline2\n")

    def test_tab_indent_rejected(self):
        with self.assertRaises(ValueError):
            yamlmini.load_yaml("a:\n\tb: 1\n")

    def test_multiline_flow_sequence_rejected(self):
        # Wrapping a long flow list is the natural editor reflex — it must raise, not truncate (#55).
        with self.assertRaisesRegex(ValueError, r"line 1: flow collection is not closed"):
            yamlmini.load_yaml("order: [a, b,\n  c]\n")

    def test_multiline_flow_list_item_rejected(self):
        with self.assertRaisesRegex(ValueError, r"line 2: flow collection is not closed"):
            yamlmini.load_yaml("rows:\n  - { metric_binding: kpi.arr,\n      target_binding: kpi.arr_target }\n")

    def test_duplicate_key_rejected(self):
        # A duplicated ledger cell must raise, not silently last-win (#55).
        with self.assertRaisesRegex(ValueError, r"line 3: duplicate key 'k'"):
            yamlmini.load_yaml("inputs:\n  k: 1\n  k: 2\n")

    def test_duplicate_key_in_flow_mapping_rejected(self):
        with self.assertRaisesRegex(ValueError, r"duplicate key 'a' in a flow mapping"):
            yamlmini.load_yaml("m: { a: 1, a: 2 }\n")

    def test_balanced_flow_on_one_line_still_loads(self):
        d = yamlmini.load_yaml('order: [a, b, c]\ncell: { k: "wrapped [not] a flow", n: 1 }\n')
        self.assertEqual(d["order"], ["a", "b", "c"])
        self.assertEqual(d["cell"]["k"], "wrapped [not] a flow")


class TestReferenceManifests(unittest.TestCase):
    def test_parse(self):
        for name in REFS:
            with self.subTest(manifest=name):
                m = load(os.path.join(EXAMPLES, f"{name}.yaml"))
                self.assertIsInstance(m, dict)
                self.assertIn("archetype", m["identity"])
                self.assertIn("output_lang", m["context"])
                self.assertIsInstance(m.get("inputs", {}), dict)
                self.assertIsInstance(m.get("content", {}), dict)


if __name__ == "__main__":
    unittest.main()
