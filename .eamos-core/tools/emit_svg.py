#!/usr/bin/env python3
"""EAMOS emit_svg: infographic-IR -> a deterministic SVG infographic.

The cosmetic hop for the infographic-IR (RFC-0002 §3) — and the rare one that is BOTH cosmetic and
**deterministic + dependency-free**: SVG is text, so this stays in the spirit of the core (same IR
-> same bytes). The generative layer (if any) touches content only; the LAYOUT is one of a small set
of canonical templates (RFC-0002 §11-1), so the render is reproducible. `professional` ships first.

    python tools/render.py manifest.yaml --ir infographic --out build/info-ir.json
    python tools/emit_svg.py build/info-ir.json --out build/infographic.svg

Assumed stats are drawn in amber (the grounding signal, RFC-0001 §6); a footer lists the count to
verify before the room.
"""

import argparse
import json
import os
import sys

# Per visual_style palette (background, accent, body, amber, muted, card). Unknown styles fall back
# to professional. Layout is shared; only the palette/theme changes (RFC-0002 §11-1).
THEMES = {
    "professional": ("#FFFFFF", "#1E2761", "#2B2B2B", "#B86B00", "#707070", "#EEF1F7"),
    "scientific":   ("#FFFFFF", "#0B3D5C", "#22303A", "#B8860B", "#5A6B73", "#EAF1F5"),
}
LABELS = {
    "it": {"decisions": "Decisioni richieste", "target": "target", "verify": "valori da verificare"},
    "en": {"decisions": "Decisions required", "target": "target", "verify": "to verify"},
}


def _lab(lang, key):
    return LABELS.get(lang, LABELS["en"]).get(key, LABELS["en"][key])


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def wrap(text, max_chars):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def _text(x, y, lines, size, fill, weight="normal", line_h=None):
    line_h = line_h or int(size * 1.25)
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else line_h}">{esc(t)}</tspan>' for i, t in enumerate(lines)
    )
    return (f'<text x="{x}" y="{y}" font-family="Calibri, Arial, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{spans}</text>'), y + line_h * (len(lines) - 1)


def build_svg(ir):
    lang = ir.get("output_lang", "en")
    bg, accent, body, amber, muted, card = THEMES.get(ir.get("visual_style"), THEMES["professional"])
    orient = ir.get("orientation", "portrait")
    W, H = {"landscape": (1160, 820), "square": (940, 940)}.get(orient, (820, 1160))
    cols = 3 if orient == "landscape" else 2
    m, gap = 50, 24
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
             f'<rect width="{W}" height="{H}" fill="{bg}"/>']

    # Title.
    seg, _ = _text(m, 78, wrap(ir.get("title", ""), (W - 2 * m) // 17), 30, accent, "bold", 36)
    parts.append(seg)
    y = 78 + 36 * len(wrap(ir.get("title", ""), (W - 2 * m) // 17)) + 8

    # Lead.
    if ir.get("lead"):
        seg, y2 = _text(m, y + 18, wrap(ir["lead"], (W - 2 * m) // 9), 16, body, "normal", 22)
        parts.append(seg)
        y = y2 + 34

    # Stat grid.
    col_w = (W - 2 * m - (cols - 1) * gap) // cols
    card_h = 104
    stats = ir.get("stats", [])
    for i, s in enumerate(stats):
        col, row = i % cols, i // cols
        x = m + col * (col_w + gap)
        cy = y + row * (card_h + gap)
        val_color = amber if s.get("assumed") else accent
        parts.append(f'<rect x="{x}" y="{cy}" width="{col_w}" height="{card_h}" rx="10" fill="{card}"/>')
        seg, _ = _text(x + 16, cy + 28, wrap(s.get("label", ""), (col_w - 32) // 8), 13, muted, "bold")
        parts.append(seg)
        seg, _ = _text(x + 16, cy + 66, [esc(s.get("value", ""))], 30, val_color, "bold")
        parts.append(seg)
        if s.get("target"):
            seg, _ = _text(x + 16, cy + 90, [f'{_lab(lang, "target")}: {esc(s["target"])}'], 12, muted)
            parts.append(seg)
    if stats:
        y = y + ((len(stats) + cols - 1) // cols) * (card_h + gap) + 12

    # Decision asks.
    if ir.get("asks"):
        seg, _ = _text(m, y + 24, [_lab(lang, "decisions")], 18, accent, "bold")
        parts.append(seg)
        y += 40
        for a in ir["asks"]:
            lines = wrap("•  " + a, (W - 2 * m) // 9)
            seg, y2 = _text(m, y + 16, lines, 15, body, "normal", 21)
            parts.append(seg)
            y = y2 + 26

    # Verify footer.
    n = len(ir.get("review_appendix", []))
    if n:
        seg, _ = _text(m, H - 36, [f'⚠ {n} {_lab(lang, "verify")}'], 14, amber, "bold")
        parts.append(seg)

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


def build_mindmap_svg(ir):
    """A deterministic horizontal mind map from a graph-IR: root → branches → leaves."""
    bg, accent, body, amber, muted, card = THEMES["professional"]
    branches = ir.get("branches", [])
    row_h = 46
    rows = sum(max(1, len(b.get("leaves", []))) for b in branches) or 1
    W, H = 1180, max(280, rows * row_h + 70)
    rx, bx, lx = 30, 380, 700
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
             f'<rect width="{W}" height="{H}" fill="{bg}"/>']
    root_y = H // 2

    def box(x, y, w, text, fill, txt, size=14, bold=False):
        parts.append(f'<rect x="{x}" y="{y - 17}" width="{w}" height="34" rx="8" fill="{fill}"/>')
        parts.append(f'<text x="{x + 12}" y="{y + 5}" font-family="Calibri, Arial, sans-serif" '
                     f'font-size="{size}" font-weight="{"bold" if bold else "normal"}" '
                     f'fill="{txt}">{esc(text)}</text>')

    def link(x1, y1, x2, y2):
        mx = (x1 + x2) // 2
        parts.append(f'<path d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}" stroke="{muted}" '
                     f'fill="none" stroke-width="1.5"/>')

    box(rx, root_y, 320, _trunc(ir.get("root", ""), 46), accent, "#FFFFFF", 15, True)
    y = 40
    for b in branches:
        leaves = b.get("leaves", []) or []
        span = max(1, len(leaves)) * row_h
        by = y + span // 2
        link(rx + 320, root_y, bx, by)
        box(bx, by, 300, _trunc(b.get("label", ""), 40), card, accent, 14, True)
        ly = y + row_h // 2
        for leaf in leaves:
            link(bx + 300, by, lx, ly)
            col = amber if "⟨" in str(leaf) else body
            parts.append(f'<text x="{lx}" y="{ly + 5}" font-family="Calibri, Arial, sans-serif" '
                         f'font-size="13" fill="{col}">{esc(_trunc(leaf, 52))}</text>')
            ly += row_h
        y += span
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Emit an SVG from an infographic-IR or graph-IR.")
    ap.add_argument("ir_json", help="path to an infographic-IR or graph-IR (mindmap) JSON file")
    ap.add_argument("--out", help="output .svg path (default: stdout)")
    args = ap.parse_args()

    with open(args.ir_json, encoding="utf-8") as fh:
        ir = json.load(fh)
    is_map = ir.get("deliverable") == "mindmap"
    svg = build_mindmap_svg(ir) if is_map else build_svg(ir)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        n = len(ir.get("branches", [])) if is_map else len(ir.get("stats", []))
        print(f"emit_svg: OK — {'mindmap' if is_map else 'infographic'} ({n} "
              f"{'branches' if is_map else 'stats'}) -> {args.out}")
    else:
        sys.stdout.write(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
