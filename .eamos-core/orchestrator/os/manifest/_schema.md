# Meeting Manifest Schema

The meeting manifest is the single source of truth for one meeting (RFC-0001 §3, §6). It resolves
the four axes, carries the **typed inputs ledger** (grounding), and holds the per-section content.
The reference instance is [`examples/qbr-c-level.yaml`](../../examples/qbr-c-level.yaml).

```yaml
schema_version: <int>

identity:
  series_name:       <str>          # the stable series name (RFC-0001 §9, series identity)
  archetype:         <archetype id> # axis 1 — selects archetypes/<archetype>.yaml
  audience_altitude: <altitude>     # axis 2
  function:          <function>     # axis 3

context:                            # axis 4
  company_size: <str>
  industry:     <str>
  regulatory:   [<REGIME>, ...]     # e.g. SOX, GDPR, HIPAA — may switch on mandatory gates
  framework:    <str>               # e.g. SAFe, Scrum
  formality:    <low|medium|high>
  output_lang:  <ISO code>          # rendered prose language; section ids stay English (RFC §7)

objective: <str>                    # localized

deliverables:                       # the bundle requested (RFC-0002 §4); params validated as enums
  - { type: <deliverable-type>, <param>: <value>, ... }

# The typed inputs ledger (RFC-0001 §6). Every quantitative/factual claim is a cell; prose binds
# cells with {{key}}. `sourced` renders plainly; `assumed` renders labeled + into the appendix.
inputs:
  <key>:                            # e.g. kpi.arr
    label:           <str>          # human label (used by kpi_table)
    value:           <str>
    provided:        <true|false>
    source:          <str>          # required when provided/sourced
    provenance:      <sourced|assumed>
    assumption:      <str>          # required when assumed
    fill_from:       <str>          # where to get the real value (assumed)
    review_required: <true>         # required when assumed

# Content authored once, per section (keys match the archetype's structure ids). Prose is in
# output_lang and binds the ledger via {{key}}; the shape per section follows the section's kind
# (see archetypes/_schema.md → block kinds).
content:
  <section-id>: { ... }
```

## Invariants

- **Numbers live only in the ledger** (RFC-0001 §6). Prose never states a figure inline; it binds
  a cell. This is what makes `grounding-labeled` a structural, decidable gate.
- **Every assumed cell is fully labeled**: `assumption` + `review_required: true` (+ ideally
  `fill_from`). The gate rejects an assumed cell missing these.
- **Output language is data** (`context.output_lang`); the manifest's content is authored in it.
  System artifacts and section ids stay English.
