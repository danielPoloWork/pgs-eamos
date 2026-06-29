# Meeting Manifest Schema

The meeting manifest is the single source of truth for one meeting (RFC-0001 §3, §6). It resolves
the four axes, carries the **typed inputs ledger** (grounding), and holds the per-section content.
The reference instance is [`examples/qbr-c-level.yaml`](../../examples/qbr-c-level.yaml).

```yaml
schema_version: <int>

identity:
  series_id:         <slug>         # the STABLE key across instances (RFC-0001 §9, §16-Q2) — the moat
  instance:          <str>          # this instance, e.g. "Q3-2026"
  series_name:       <str>          # human name of this instance (not the key)
  archetype:         <archetype id> # axis 1 — selects archetypes/<archetype>.yaml
  audience_altitude: <altitude>     # axis 2
  function:          <function>     # axis 3

# The moat (RFC-0001 §9). What an opening instance pulls from the prior one's series store
# (os/series/_schema.md), via tools/series.py. Omit for a one-off (non-recurring) meeting.
carry_forward:
  from_instance: <str>              # the prior instance, e.g. "Q2-2026"
  decisions:     <bool>
  open_actions:  <bool>
  rolling_risks: <bool>
  kpi_history:   <bool>

context:                            # axis 4
  company_size: <str>
  industry:     <str>
  regulatory:   [<REGIME>, ...]     # e.g. SOX, GDPR, HIPAA — may switch on mandatory gates
  framework:    <str>               # e.g. SAFe, Scrum
  formality:    <low|medium|high>
  output_lang:  <ISO code>          # rendered prose language; section ids stay English (RFC §7)

objective: <str>                    # localized

# Solution-discovery intake (Phase L0/L1/L2, #29) — the typed capture of *why* a meeting exists,
# before any solution talk. Optional (absent on meetings that don't need it). CAPTURE only: the
# rendered architectural-constraints section is the decision pre-work pack (#26), which reads from
# here. Prose values are localized (output_lang); keys stay English (RFC §7).
discovery_intake:
  intent:   <str>                   # L0 — the capability sought (not the tool); why the request exists
  domain:                           # L1 — domain framing
    stakeholders:     [<str>, ...]
    existing_systems: [<str>, ...]
    current_pain:     <str>
  constraints:                      # L2 — constraints & signals
    volume:       <str>             # users / frequency / data volume
    budget_range: <str>
    timing:       <str>
    dependencies: [<str>, ...]

# Optional attendee roster / RACI (meeting-conduct metadata, not an IR concept). Rendered into the
# agenda header by `facilitate.py prep`; absent → renders nothing. `raci` ∈ {R,A,C,I} and
# `from_phase` (when an actor joins, e.g. a vendor late on purpose) are each optional. Roles are
# localized prose (output_lang); this block is not gate-checked and does not enter the deck-IR.
attendees:
  - { role: <str>, raci: <R|A|C|I>, from_phase: <str> }

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

# Optional weighted scorecard (#23). Criteria × weights × per-option scores → a computed weighted
# total per option. `render.py` computes each total deterministically and injects it as a *computed*
# ledger cell (`computed: true`, source "computed from criteria × weights"); the sheet stays
# formula-free. Provenance propagates: the total is `sourced` iff every weight+score is sourced, else
# `assumed` (labeled + into the review appendix). `weight` and each `scores.<criterion-id>` are
# ledger keys; `total` is the ledger key the computed total is written to (bind it with {{total-key}}).
scorecard:
  criteria:
    - { id: <criterion-id>, label: <str>, weight: <ledger-key> }
  options:
    - { name: <str>, total: <ledger-key>, scores: { <criterion-id>: <ledger-key>, ... } }

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
