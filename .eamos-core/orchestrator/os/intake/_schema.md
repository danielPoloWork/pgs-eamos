# Intake / Source-Reorganization Schema

The **source-reorganization primitive** (RFC-0002 §6; RFC-0001 §15-M5): ingest provided material →
normalize into the typed inputs ledger (RFC-0001 §6) so a meeting's numbers come from material, not
hand-entry. Implemented by [`tools/intake.py`](../../../tools/intake.py); the foundational half of
M5 (connectors are the later half).

## Sources (this slice)

| Source | Flag | Becomes |
|--------|------|---------|
| **Pasted KPI table** | `--csv <file>` | one cell per row; header (case-insensitive) `key,value[,label,source]` |
| **Prior instance** | `--series <store.json>` | the prior deck's KPIs (the series store, RFC-0001 §9) |
| **Uploaded deck** | `--deck <file.pptx>` | metric-looking `Label: value` lines → cells (needs python-pptx) |

## Connectors

Each source is a **connector**: a function `path → {key: {label, value, source, via}}`. Built-in:
`from_csv`, `from_series`, `from_deck` (the `.pptx` extractor — the only one needing python-pptx; the
CSV/series paths stay dependency-free). Precedence on a key collision (later wins): **series → deck →
csv** — the prior fills gaps, an uploaded deck refines, the pasted table is authoritative.

To add a connector (Jira / Notion / Sheets), implement one function returning the same cell shape:
- **Sheets** → export to CSV and use `--csv` (no new code).
- **Jira / Notion** → an API client returning cells (`via: intake/jira` …); the call + auth are
  environment-specific and live behind the same `path → cells` contract. Not bundled (no creds) — the
  contract is the extension point.

## Rules

- **Every emitted cell is `provided: true, provenance: sourced`** with a `source` and a `via:` tag
  (which ingestion path produced it). Assumed values are *never* invented here — they are added by
  hand later, only where material is genuinely missing (RFC-0001 §6).
- **Dedupe**: on a key collision, the **current** source (CSV) wins over the **prior** one (series);
  the prior fills gaps. Deterministic (sorted keys → reproducible fragment).
- The output is a paste-ready `inputs:` block; the maintainer drops it into the manifest.

## Output cell

```yaml
inputs:
  <key>:
    label:      "<human label>"
    value:      "<value>"
    provided:   true
    source:     "<where it came from>"
    provenance: sourced
    via:        intake/csv | intake/series
```

## Classification (Phase B, #27)

A second, distinct intake slice: the **classifier as data**. Before any solution talk, a meeting is
classified by *problem type* (not by meeting archetype, which axis 1 already covers). The taxonomy —
the dimensions and their allowed values — lives in [`classification.yaml`](classification.yaml):

| Dimension | Values |
|-----------|--------|
| `cluster` | process_optimization · system_replacement · integration · data_platform · workflow_automation · compliance_regulatory |
| `complexity` | low · med · high |
| `decision_risk` | low · med · high |

A meeting records its classification in `discovery_intake.classification` (manifest schema). The
`classification-valid` gate rejects any value outside the taxonomy. The classification is the input
to **routing depth** (Phase C, #28): e.g. low impact/complexity skips the deep-architecture layer;
core-business + high integration activates it. English on disk (RFC-0001 §7) — stable ids.

