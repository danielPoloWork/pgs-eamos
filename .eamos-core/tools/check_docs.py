#!/usr/bin/env python3
"""Doc-path check (#65): every repo path the top-level docs reference must exist in the tree.

For an agent-first repo the contract is load-bearing documentation — an agent told to load a
persona from a directory that does not exist will fail or, worse, improvise one. This is the doc
equivalent of the gates the repo already believes in: extract every path-looking reference from
AGENTS.md / README.md / CLAUDE.md (markdown link targets, inline-code paths, and AGENTS.md's §4
layout tree) and fail loudly, listing each broken reference.

    python .eamos-core/tools/check_docs.py

A prose path may be written relative to the repo root or to `.eamos-core/` (both are natural in
context); a `*` glob must match at least one file. `build/` outputs are transient by design and
skipped.
"""

import glob as globmod
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import _cli      # noqa: E402  (utf8_stdio, #54)

ROOT = os.path.dirname(os.path.dirname(TOOLS))
DOCS = ("AGENTS.md", "README.md", "CLAUDE.md")
BASES = ("", ".eamos-core")
LINK_RE = re.compile(r"\]\(([^)#?\s]+)\)")
CODE_RE = re.compile(r"`([^`\s]+)`")
TREE_RE = re.compile(r"^([│ ]*)(?:├──|└──)\s+(\S+)")


def _exists(path):
    for base in BASES:
        candidate = os.path.join(ROOT, base, path)
        if "*" in path:
            if globmod.glob(candidate):
                return True
        elif os.path.exists(candidate):
            return True
    return False


def _link_paths(text):
    return [m.group(1) for m in LINK_RE.finditer(text)
            if not m.group(1).startswith(("http://", "https://", "mailto:"))]


def _code_paths(text):
    """Inline-code spans that look like repo paths: contain a '/', no placeholders/options."""
    out = []
    for m in CODE_RE.finditer(text):
        tok = m.group(1)
        if "/" not in tok or tok.startswith(("http", "--", "#", "build/")):
            continue
        if any(c in tok for c in "<>{}$()«⟨"):     # placeholders / prose, not paths
            continue
        out.append(tok.rstrip("/").rstrip(".,;:"))
    return out


def _expand_braces(name):
    m = re.match(r"(.*)\{([^}]*)\}(.*)", name)
    return [f"{m.group(1)}{x}{m.group(3)}" for x in m.group(2).split(",")] if m else [name]


def _tree_paths(text):
    """Paths from AGENTS.md's fenced layout tree: depth = marker column / 4."""
    paths, stack, in_tree = [], [], False
    for line in text.split("\n"):
        if not in_tree and line.strip() == "```text":
            in_tree = True
            continue
        if in_tree and line.strip() == "```":
            break
        m = TREE_RE.match(line) if in_tree else None
        if not m:
            continue
        depth = len(m.group(1)) // 4
        stack = stack[:depth]
        for name in _expand_braces(m.group(2)):
            paths.append("/".join(stack + [name.rstrip("/")]))
        stack.append(m.group(2).rstrip("/"))
    return paths


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    broken = []
    for doc in DOCS:
        text = open(os.path.join(ROOT, doc), encoding="utf-8").read()
        refs = _link_paths(text) + _code_paths(text)
        if doc == "AGENTS.md":
            refs += _tree_paths(text)
        for ref in refs:
            if not _exists(ref):
                broken.append(f"{doc}: '{ref}' does not exist in the tree")
    if broken:
        print("check_docs: FAIL — the docs reference paths that do not exist (#65)\n")
        for b in broken:
            print(f"  {b}")
        print(f"\n{len(broken)} broken reference(s).")
        return 1
    print("check_docs: OK — every doc-referenced path resolves")
    return 0


if __name__ == "__main__":
    sys.exit(main())
