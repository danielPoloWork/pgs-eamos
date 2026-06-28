# Deliverable Registry Schema

Each deliverable type is a file `deliverables/<type>.yaml`, validated by the lint. The registry —
not code — defines what EAMOS can produce and which parameter values are legal (RFC-0002 §4). A
meeting's `deliverables:` list (in the manifest) selects from it; the UI affordances become
**validated enums in data** (the `deliverable-params` gate rejects a value outside the declared set).

```yaml
type:       <id, e.g. presentation | infographic | table_chart | mindmap | report | interview_quiz>
ir_family:  <slide-IR | doc-IR | graph-IR | infographic-IR | data-IR | quiz-IR>
params:
  <param>: { enum: [<value>, ...], default: <value> }   # an enumerated, validated parameter
  <param>: { kind: free_text }                            # a free-text intent (shapes form, not facts)
emitter:    <emit_pptx | emit_docx | emit_md | emit_svg | emit_xlsx>
layouts:    [<id>, ...]    # (infographic only) the canonical deterministic templates (6–8)
```

## Invariants

- **Every legal param value is in the data.** A manifest deliverable param that names a value
  outside the registry `enum` fails the `deliverable-params` gate (RFC-0002 §4).
- **`archetype × altitude` may narrow the registry** (RFC-0002 §5): the archetype's
  `deliverable_bounds` can `allow` only a subset at a given altitude (the `deliverable-params-in-bounds`
  gate). The intent field may choose *within* the bounds, never beyond.
- **One ledger feeds every projection** (RFC-0002 §7): a value cannot diverge between the deck, the
  infographic, and the table — they all bind the same inputs-ledger cell.
