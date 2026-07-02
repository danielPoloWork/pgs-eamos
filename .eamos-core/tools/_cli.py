#!/usr/bin/env python3
"""Shared CLI plumbing for the EAMOS tools.

One job (#54): the tools write the grounding markers (`⟨…⟩`, U+27E8), arrows (`→`, `↑`) and
`⟦redacted⟧` to stdout. On Windows, Python's stdio picks the ANSI code page (cp1252) when output
is redirected or piped, so every documented `tool ... > file` workflow crashed with
UnicodeEncodeError — and even the console success line printed mojibake. File writes were already
safe (`open(..., encoding="utf-8")` everywhere); only the stdio hop was broken.
"""

import os
import sys


def read_text(path, what="file"):
    """Read a UTF-8 text file, or exit with one actionable line — a missing input is a user
    error, not a traceback (#58)."""
    if not os.path.isfile(path):
        raise SystemExit(f"error: {what} not found: {path}")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def utf8_stdio():
    """Force UTF-8 stdout/stderr regardless of the platform code page. Call first in every main()."""
    for stream in (sys.stdout, sys.stderr):
        enc = getattr(stream, "encoding", None)
        if enc and enc.lower() not in ("utf-8", "utf8") and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
