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

A *foreign* (non-EAMOS) uploaded deck is extracted via the `pptx`/`docx` skills into the same shape —
a later connector; the primitive itself stays dependency-free and structured.

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
