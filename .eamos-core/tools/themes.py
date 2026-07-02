#!/usr/bin/env python3
"""Theme-token loader (#64) — corporate identity as data.

os/themes/<name>.yaml holds the design tokens (font + palette) a deliverable renders with; the
IR carries the resolved theme name, so the emitters stay IR-driven and an enterprise consumer
restyles every deliverable by adding one YAML file — never by editing an emitter.

The amber "to verify" color is deliberately NOT a token: it is the grounding signal (RFC-0001 §6),
reserved here as a constant — a theme that camouflages assumptions defeats the safety model.
"""

import os

TOOLS = os.path.dirname(os.path.abspath(__file__))
THEMES_DIR = os.path.join(os.path.dirname(TOOLS), "orchestrator", "os", "themes")
DEFAULT = "professional"
AMBER = "B86B00"           # reserved: the grounding signal is identical across themes

_cache = {}


def load(name):
    """The token table for theme `name` (cached); an unknown/absent name falls back to the default."""
    name = name or DEFAULT
    if name not in _cache:
        path = os.path.join(THEMES_DIR, f"{name}.yaml")
        if not os.path.exists(path):
            path = os.path.join(THEMES_DIR, f"{DEFAULT}.yaml")
        import yamlmini
        with open(path, encoding="utf-8") as fh:
            _cache[name] = yamlmini.load_yaml(fh.read())
    return _cache[name]


def color(theme, key):
    """One palette token as a hex string (no '#')."""
    return (theme.get("colors") or {}).get(key, "")


def rgb(hexstr):
    """'1E2761' -> (30, 39, 97) for the binary emitters."""
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))
