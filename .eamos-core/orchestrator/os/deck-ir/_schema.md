# Deck-IR Schema (the determinism boundary)

The deck-IR is the **deterministic intermediate representation** of a deliverable (RFC-0001 §5,
generalized to six IR families by RFC-0002 §3). `render.py` produces it from the manifest +
archetype; the gates run **on the IR**; the cosmetic `emit_*` hop turns it into Markdown / PPTX /
DOCX / SVG / XLSX. Same manifest → same IR → same bytes.

```yaml
ir_version:   <int>                               # the IR contract version (#62); emitters refuse a mismatch
generator:    eamos-render                        # provenance of the artifact
deliverable:  <type, e.g. presentation>           # from the manifest's deliverables[] (RFC-0002 §4)
format:       <e.g. speaker | detailed>           # presentation render mode
length:       <short | medium | long>
archetype:    <archetype id>
altitude:     <audience altitude>
output_lang:  <ISO code; rendered prose language>
objective:    <the meeting objective, localized>
lead_with:    <recommendation | detail>           # from altitude_shaping
slides:
  - id:    <section id, stable English key>
    kind:  <block kind>
    title: <localized section title>
    blocks:
      - { type: lead,     text: <str> }
      - { type: bullet,   text: <str> }
      - { type: kpi_row,  label: <str>, value: <str>, target: <str?> }
      - { type: prose,    text: <str> }
      - { type: risk,     risk: <str>, ask: <str> }
      - { type: decision, text: <str> }
      - { type: option,   name: <str>, pro: <str>, con: <str>, no_action: <bool?> }  # no-action baseline (#30)
      - { type: next_step,     text: <str> }   # decision_contract (Phase G): the chosen next step
      - { type: residual_risk, text: <str> }   # decision_contract: risk remaining after mitigation
review_appendix:                                   # the "verify before the room" list (RFC-0001 §6)
  - { binding: <ledger-key>, value: <str>, assumption: <str>, fill_from: <str> }
```

## Invariants

- **Bindings are resolved, not deferred.** Every `value`/`text` is final text. A value from a
  `sourced` ledger cell renders plainly; a value from an `assumed` cell renders **labeled**
  (`⟨value — <verify-label>⟩`) and its key appears in `review_appendix`. There are no live
  `{{bindings}}` left in the IR (the `grounding-labeled` gate enforces this).
- **Slide order is the archetype's structure order**, after altitude `max_slides` capping (which
  never drops a `required` section).
- **Deterministic serialization.** JSON, `indent=2`, `ensure_ascii=False`, insertion order;
  `review_appendix` sorted by binding key. No clocks, no randomness, no filesystem order.
- **Versioned contract (#62).** Every projection (all six IR families) stamps `ir_version` +
  `generator`. `ir_version` increments on **any breaking change to block/field shapes**; every
  emitter validates it before rendering and refuses a mismatch (or an absent field — a pre-#62
  artifact) with *"re-render the manifest"* — a persisted `build/*.json` outlives tool runs, and a
  silent mis-render is worse than a one-command re-render.
