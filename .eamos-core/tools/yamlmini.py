#!/usr/bin/env python3
"""Minimal, dependency-free YAML loader for EAMOS.

Lifted from the EADOS factory renderer (`pgs-eaao/.eados-core/tools/render.py`) — the same
proven, stdlib-only subset, extracted here so `render.py` and `eamos_lint.py` share one loader.

Supported subset: block/flow mappings and sequences, block-style mapping items, double-quoted
scalars WITH escapes (\\n \\t \\r \\0 \\" \\\\ \\/), single-quoted scalars with '' escaping,
`|` (clip) / `|-` (strip) / `|+` (keep) block scalars, and int / true / false / null / ~ literals.
Deliberate, safer-for-a-manifest deviations from YAML 1.1:
  * yes/no/on/off are NOT booleans (avoids the "Norway problem"); only true/false are.
  * unquoted decimals/exponents stay strings (versions like 1.22 are not coerced).
Out of scope: folded `>` scalars, anchors, tags, multi-document streams.
What the subset can't parse fails LOUDLY (a line-numbered ValueError), never silently (#55): a
flow collection wrapped across lines and a duplicated mapping key both raise — the manifest is
the one file whose integrity the grounding model depends on.
"""

import re


def _strip_comment(text):
    out, q, i = [], None, 0
    while i < len(text):
        c = text[i]
        if q:
            out.append(c)
            if c == "\\" and q == '"' and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'":
            q = c
            out.append(c)
        elif c == "#" and (i == 0 or text[i - 1] == " "):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


def _split_top(text, sep=","):
    parts, depth, q, buf, i = [], 0, None, [], 0
    while i < len(text):
        c = text[i]
        if q:
            buf.append(c)
            if c == "\\" and q == '"' and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'":
            q = c
            buf.append(c)
        elif c in "[{":
            depth += 1
            buf.append(c)
        elif c in "]}":
            depth -= 1
            buf.append(c)
        elif c == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    if buf:
        parts.append("".join(buf))
    return parts


def _flow_unbalanced(s):
    """True iff s opens a flow collection that does not close on the same line (quote-aware, #55)."""
    if not s or s[0] not in "[{":
        return False
    depth, q, i = 0, None, 0
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\" and q == '"':
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        i += 1
    return depth != 0


_DQ_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0",
               '"': '"', "\\": "\\", "/": "/", " ": " "}


def _unescape_double(body):
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append(_DQ_ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _scalar(s):
    s = s.strip()
    if s == "":
        return ""
    if s[0] == "[" and s[-1] == "]":
        inner = s[1:-1].strip()
        return [_scalar(x) for x in _split_top(inner)] if inner else []
    if s[0] == "{" and s[-1] == "}":
        inner, d = s[1:-1].strip(), {}
        if inner:
            for pair in _split_top(inner):
                k, _, v = pair.partition(":")
                k = k.strip()
                if k in d:
                    raise ValueError(f"duplicate key '{k}' in a flow mapping")
                d[k] = _scalar(v.strip())
        return d
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return _unescape_double(s[1:-1])
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        if re.fullmatch(r"-?0\d+", s):
            return s
        return int(s)
    return s


_DOC_MARKERS = ("---", "...")


def _reject_unsupported(text):
    seen_content = False
    for num, raw in enumerate(text.split("\n"), 1):
        s = raw.strip()
        if s in _DOC_MARKERS:
            if seen_content or s == "...":
                raise ValueError(
                    f"line {num}: multi-document streams / '...' end markers are not supported; "
                    "the file must be a single YAML document"
                )
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in lead:
            raise ValueError(f"line {num}: tab indentation is not valid YAML — use spaces")
        if s and not s.startswith("#"):
            seen_content = True


def load_yaml(text):
    _reject_unsupported(text)
    lines = text.split("\n")
    n = len(lines)
    pos = [0]

    def indent_of(line):
        return len(line) - len(line.lstrip(" "))

    def skip_blanks():
        while pos[0] < n:
            s = lines[pos[0]].strip()
            if s and not s.startswith("#") and s != "---":
                return
            pos[0] += 1

    def parse_block_scalar(parent_indent, chomp=""):
        collected, base = [], None
        while pos[0] < n:
            line = lines[pos[0]]
            if line.strip() == "":
                collected.append("")
                pos[0] += 1
                continue
            if indent_of(line) <= parent_indent:
                break
            if base is None:
                base = indent_of(line)
            collected.append(line[min(base, indent_of(line)):])
            pos[0] += 1
        if chomp == "+":
            return ("\n".join(collected) + "\n") if collected else ""
        while collected and collected[-1] == "":
            collected.pop()
        if not collected:
            return ""
        body = "\n".join(collected)
        return body if chomp == "-" else body + "\n"

    def parse_map(indent, first_line=None):
        result = {}
        while True:
            skip_blanks()
            if pos[0] >= n:
                break
            line = first_line if first_line is not None else lines[pos[0]]
            first_line = None
            ind = indent_of(line)
            if ind != indent or line.strip().startswith("- "):
                break
            key, _, val = _strip_comment(line.strip()).partition(":")
            key, val = key.strip(), val.strip()
            if key in result:
                raise ValueError(f"line {pos[0] + 1}: duplicate key '{key}'")
            if _flow_unbalanced(val):
                raise ValueError(f"line {pos[0] + 1}: flow collection is not closed on one line "
                                 "(multiline flow is not supported)")
            pos[0] += 1
            if val in ("|", "|-", "|+"):
                result[key] = parse_block_scalar(indent, val[1:])
            elif val == "":
                skip_blanks()
                if pos[0] < n:
                    nxt = lines[pos[0]]
                    nind = indent_of(nxt)
                    is_item = nxt.strip().startswith("- ")
                    if is_item and nind == indent:
                        result[key] = parse_list(indent)
                    elif nind > indent:
                        result[key] = parse_list(nind) if is_item else parse_map(nind)
                    else:
                        result[key] = None
                else:
                    result[key] = None
            else:
                result[key] = _scalar(val)
        return result

    def parse_list(indent):
        items = []
        while True:
            skip_blanks()
            if pos[0] >= n:
                break
            line = lines[pos[0]]
            if indent_of(line) != indent or not line.strip().startswith("- "):
                break
            after_dash = line[indent + 1:]
            key_col = indent + 1 + (len(after_dash) - len(after_dash.lstrip(" ")))
            content = line[key_col:]
            if re.match(r"[A-Za-z0-9_]+\s*:(\s|$)", content):
                items.append(parse_map(key_col, first_line=" " * key_col + content))
            else:
                item = _strip_comment(content.strip())
                if _flow_unbalanced(item):
                    raise ValueError(f"line {pos[0] + 1}: flow collection is not closed on one line "
                                     "(multiline flow is not supported)")
                items.append(_scalar(item))
                pos[0] += 1
        return items

    skip_blanks()
    return parse_map(0)


if __name__ == "__main__":
    import json
    import sys
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(json.dumps(load_yaml(fh.read()), indent=2, ensure_ascii=False))
