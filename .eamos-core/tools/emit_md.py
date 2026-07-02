#!/usr/bin/env python3
"""EAMOS emit_md: deck-IR -> deterministic Markdown deck.

The cosmetic IR -> text hop (RFC-0001 §14). Markdown is fully deterministic (same IR -> same
bytes); the PPTX hop via the pptx skill comes later and is the only non-deterministic layer.

    python tools/emit_md.py build/deck-ir.json --out build/deck.md
"""

import argparse
import json
import os
import sys

import _cli    # utf8_stdio (#54)
import labels  # chrome labels as data (#61)

SUPPORTED_IR_VERSION = 1   # the IR contract this emitter was written for (#62)


def _lab(lang, key):
    # Template chrome in the deck's output language (the section labels, not the content).
    return labels.lab(lang, "md", key)


def render_md(ir):
    lang = ir.get("output_lang", "en")
    out = []
    title = ir.get("objective") or f"{ir.get('archetype', '')} @ {ir.get('altitude', '')}"
    out.append(f"# {title}")
    out.append("")
    out.append(f"*{ir.get('archetype', '')} · {ir.get('altitude', '')} · "
               f"{ir.get('deliverable', '')}/{ir.get('format', '')} · {lang}*")
    out.append("")

    for i, slide in enumerate(ir.get("slides", []), 1):
        out.append(f"## {i}. {slide.get('title', slide.get('id', ''))}")
        out.append("")
        for b in slide.get("blocks", []):
            t = b.get("type")
            if t == "lead":
                out.append(f"> {b.get('text', '')}")
                out.append("")
            elif t == "bullet":
                out.append(f"- {b.get('text', '')}")
            elif t == "kpi_row":
                line = f"- **{b.get('label', '')}**: {b.get('value', '')}"
                if "target" in b:
                    line += f"  ({_lab(lang, 'target')}: {b['target']})"
                out.append(line)
            elif t == "prose":
                out.append(b.get("text", ""))
                out.append("")
            elif t == "risk":
                out.append(f"- **{_lab(lang, 'risk')}:** {b.get('risk', '')} — "
                           f"**{_lab(lang, 'ask')}:** {b.get('ask', '')}")
            elif t == "decision":
                out.append(f"- {b.get('text', '')}")
            elif t == "option":
                out.append(f"- **{b.get('name', '')}** — {_lab(lang, 'pro')}: {b.get('pro', '')}; "
                           f"{_lab(lang, 'con')}: {b.get('con', '')}")
            elif t == "next_step":
                out.append(f"- **{_lab(lang, 'next_step')}:** {b.get('text', '')}")
            elif t == "residual_risk":
                out.append(f"- **{_lab(lang, 'residual_risk')}:** {b.get('text', '')}")
        out.append("")

    appendix = ir.get("review_appendix", [])
    if appendix:
        out.append(f"## ⚠ {_lab(lang, 'review')}")
        out.append("")
        for a in appendix:
            line = f"- **{a.get('binding', '')}** = {a.get('value', '')}"
            if a.get("assumption"):
                line += f" — {a['assumption']}"
            if a.get("fill_from"):
                line += f" ({_lab(lang, 'fill')}: {a['fill_from']})"
            out.append(line)
        out.append("")

    return "\n".join(out).rstrip() + "\n"




def render_quiz_md(ir):
    lang = ir.get("output_lang", "en")
    t = labels.table(lang, "quiz_md")
    out = [f"# {t['title']} — {ir.get('title', '')}", ""]
    graded = [q for q in ir.get("questions", []) if q.get("kind") == "graded"]
    disc = [q for q in ir.get("questions", []) if q.get("kind") == "discussion"]
    if graded:
        out.append(f"## {t['graded']}")
        for i, q in enumerate(graded, 1):
            out.append(f"{i}. {q.get('q', '')}")
            tag = f" ⟨{t['verify']}⟩" if q.get("assumed") else ""
            out.append(f"   - {t['ans']}: {q.get('a', '')}{tag}  [{t['src']}: {q.get('cite', '')}]")
        out.append("")
    if disc:
        out.append(f"## {t['disc']}")
        for i, q in enumerate(disc, 1):
            out.append(f"{i}. {q.get('q', '')}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main():
    _cli.utf8_stdio()   # Windows: piped stdout must stay UTF-8 (#54)
    ap = argparse.ArgumentParser(description="Emit Markdown from a deck-IR or quiz-IR.")
    ap.add_argument("deck_ir", help="path to a deck-IR or quiz-IR JSON file")
    ap.add_argument("--out", help="output path (default: stdout)")
    args = ap.parse_args()

    with open(args.deck_ir, encoding="utf-8") as fh:
        ir = json.load(fh)
    _cli.require_ir_version(ir, "emit_md", SUPPORTED_IR_VERSION)
    text = render_quiz_md(ir) if ir.get("deliverable") == "interview_quiz" else render_md(ir)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        kind = "quiz" if ir.get("deliverable") == "interview_quiz" else "deck"
        print(f"emit_md: OK — {kind} -> {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
