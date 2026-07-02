# CLI reference

Every tool is **stdlib Python** — no install step. Run from `.eamos-core/` so the relative paths
in the examples resolve. All tools force UTF-8 stdio (safe to pipe on Windows), refuse a missing
input file with one actionable line, and validate the IR contract version before emitting (#62).
The optional binary hops need `pip install python-pptx` / `python-docx` / `openpyxl`.

The pipeline in one line:

```
intake.py → (manifest, by hand + confirm) → render.py → eamos_lint.py → emit_*.py
                        ↑ series.py open                    facilitate.py / advisor.py
```

## `render.py` — manifest → IR

```
python tools/render.py <manifest.yaml> [--ir deck|infographic|data|mindmap|quiz|topology]
                       [--out PATH] [--altitude A] [--function F] [--redact]
```

| Flag | Meaning |
|---|---|
| `--ir` | which IR projection to emit (default `deck`); all six project the **same** ledger |
| `--out` | output path for the IR JSON (default: stdout) |
| `--altitude` | override the manifest's `audience_altitude` (render one manifest at several altitudes) |
| `--function` | override the manifest's function pack |
| `--redact` | egress redaction: mask `pii`/`phi`/`sensitive` cells per the confidentiality policy |

## `eamos_lint.py` — the gates

```
python tools/eamos_lint.py <manifest.yaml>
```

Composes the deck-IR and runs every gate (manifest-schema, completeness, grounding-labeled,
audience-fit, deliverable-params, no-action-considered, classification/questions/topology/labels
validity, rubric, confidentiality). Exit 0 = all green; exit 1 lists each failure as
`[gate] message`.

## `intake.py` — sources → typed inputs ledger

```
python tools/intake.py [--csv FILE]... [--series STORE.json] [--deck FILE.pptx]... [--out PATH]
python tools/intake.py --questions <manifest.yaml>
```

| Flag | Meaning |
|---|---|
| `--csv` | a pasted/exported KPI table (repeatable) |
| `--series` | a series store JSON — the prior instance gap-fills |
| `--deck` | an uploaded `.pptx` to extract KPIs from (needs python-pptx; repeatable) |
| `--out` | where to write the YAML `inputs:` fragment (default: stdout) |
| `--questions` | Phase C: print the adaptive question set for a classified manifest |

Precedence on merge (later wins): series → deck → csv. Every emitted cell is
`provenance: sourced`; assumed cells are added later, by hand.

## `series.py` — the persistent series store (the moat)

```
python tools/series.py close <manifest.yaml> --store STORE.json
python tools/series.py open  <manifest.yaml> --store STORE.json [--out DIGEST.json]
```

`close` writes an instance's decisions / open actions / rolling risks / KPI history into the
store (idempotent: re-closing the same instance replaces, never duplicates). `open` prints the
carry-forward digest the next instance pre-reads.

## `facilitate.py` — the regie

```
python tools/facilitate.py prep     <manifest.yaml> [--minutes N] [--template discovery-decision]
python tools/facilitate.py followup <manifest.yaml> --outcomes OUTCOMES.yaml [--store STORE.json] [--out MINUTES.md]
```

`prep` prints a timeboxed agenda + per-section facilitation script (attendee roster / RACI if the
manifest carries one). `followup` turns **human-captured** outcomes into minutes and carries them
into the series store — the agent never invents the room's outcomes.

## `advisor.py` — precedents & what-if

```
python tools/advisor.py record   <manifest.yaml> --repo REPO.json [--date 2026-06]
python tools/advisor.py match    <manifest.yaml> --repo REPO.json [--top 3]
python tools/advisor.py simulate <manifest.yaml> --set w.tco=0.3 [--set key=value]...
```

`record` files a closed decision (replace-by-instance). `match` ranks past cases by
classification similarity. `simulate` re-weights a scorecard and reports whether the winner flips.

## Emitters — IR → deliverable (the cosmetic last hop)

```
python tools/emit_md.py   <deck-ir.json|quiz-ir.json> [--out PATH]     # Markdown (deterministic)
python tools/emit_svg.py  <info|mindmap|topology-ir.json> [--out PATH] # SVG (deterministic)
python tools/emit_pptx.py <deck-ir.json> --out deck.pptx               # needs python-pptx
python tools/emit_docx.py <deck-ir.json> --out pre-read.docx           # needs python-docx
python tools/emit_xlsx.py <data-ir.json> --out kpis.xlsx               # needs openpyxl
```

Each emitter checks `ir_version` and refuses a stale artifact ("re-render the manifest"). Colors
and typography come from the theme tokens (`orchestrator/os/themes/`); the amber to-verify color
is reserved and identical across themes.

## `check_docs.py` — the doc-path gate

```
python tools/check_docs.py
```

Fails listing every path referenced by `AGENTS.md` / `README.md` / `CLAUDE.md` that does not
exist in the tree (#65). Runs in CI.
