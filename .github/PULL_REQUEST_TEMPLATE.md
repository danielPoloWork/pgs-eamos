## Summary

One or two sentences: what changes and why it matters.

## Motivation

Link to the RFC, ADR, or roadmap milestone item that prompted this work. Non-trivial design
decisions need an ADR under [`.eamos-core/docs/adr/`](../.eamos-core/docs/adr/).

## Changes

- bulleted list of meaningful changes (not a file list)

## Verification

- [ ] `python .eamos-core/tools/eamos_lint.py .eamos-core/orchestrator/examples/qbr-c-level.yaml` — all gates green
- [ ] Render-smoke deterministic: `render.py … --out build/deck-ir.json` twice is byte-identical, and `emit_md.py` produces the deck
- [ ] `python -m py_compile` clean on any changed tool
- [ ] Tooling tests pass (`.eamos-core/tools/tests/test_*.py`) where touched

## Documentation Impact

- [ ] `README.md` / `AGENTS.md` updated (if the maintainer-facing surface changed)
- [ ] RFC / ADR added or updated (if a non-trivial design decision was made)
- [ ] `ROADMAP.md` milestone updated (item checked / scope noted)
- [ ] PR metadata set — **assignee + one type label + milestone** (the exhaustiveness bar)

<!-- Crosslinks required (git policy): this PR body must reference its RFC and its milestone item. -->
