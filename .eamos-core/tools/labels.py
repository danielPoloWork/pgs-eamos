#!/usr/bin/env python3
"""Shared chrome-label loader (#61) — the three-tier language model's chrome as data.

os/localization/labels.yaml is the single source of truth for every rendered chrome string: the
grounding-marker suffix, the redaction mask, the deck / sheet / SVG / quiz / facilitation labels.
It replaces eight duplicated in-code tables that had already drifted (RFC-0001 §7): adding a
language is a one-file data edit, and the labels-valid gate enforces that every language defines
every key — a language is supported when ALL chrome exists, half-localized is worse than honestly
unsupported.

Namespaces preserve intentional per-deliverable differences (the .docx uses title-case "Target",
the sheet says "Source / note"): core, md, quiz_md, pptx, docx, svg, xlsx, facilitate.
"""

import os

TOOLS = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(os.path.dirname(TOOLS), "orchestrator", "os", "localization", "labels.yaml")
FALLBACK = "en"

_cache = None


def load():
    """The full labels table (cached), or {} if the file is absent."""
    global _cache
    if _cache is None:
        if os.path.exists(PATH):
            import yamlmini
            with open(PATH, encoding="utf-8") as fh:
                _cache = yamlmini.load_yaml(fh.read())
        else:
            _cache = {}
    return _cache


def table(lang, ns):
    """The `ns` label table for `lang`; missing keys fall back per-key to English."""
    data = load()
    base = (data.get(FALLBACK) or {}).get(ns) or {}
    cur = (data.get(lang) or {}).get(ns) or {}
    return {**base, **cur}


def lab(lang, ns, key):
    """One chrome label; '' only if the key is unknown to the fallback too (labels-valid catches it)."""
    return table(lang, ns).get(key, "")
