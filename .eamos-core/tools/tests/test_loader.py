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

REFS = ["qbr-c-level", "esc-decision", "qbr-finance", "rca-eng", "board-confidential"]


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
