# Archetype Profile Schema

An archetype profile (`archetypes/<archetype>.yaml`) is the **deep structure** of one meeting
archetype, expressed as data (RFC-0001 §3, axis 1). It is independent of audience, function, and
language: the same archetype renders at any altitude, for any function, in any output language.
This is what lets EAMOS cover ~40 "meeting types" with ~8 archetypes × overlays.

Every profile **must** define every key below; a profile missing a key is incomplete and the
renderer must refuse it (quality bar).

```yaml
archetype:    <id, e.g. review | decision | planning | post-mortem | retrospective | ...>
display_name: <human name, e.g. "Review / Status">

# The ordered deep structure. `kind` selects how render.py builds the section's blocks; a
# `required` section is never dropped by altitude shaping (the completeness gate enforces it).
structure:
  - { id: <section-id, stable English key>, kind: <block-kind>, required: <true|false> }

# Altitude shaping = the per-altitude overlay (axis 2): same base structure, composed differently.
# Applied deterministically as drop -> reorder -> slide-budget cap; never a cross-product (RFC §3).
altitude_shaping:
  <altitude>:
    max_slides: <int>                  # caps the deck (audience-fit gate)
    jargon:     <none|some|full>       # advisory
    lead_with:  <recommendation|detail>
    drop:       [<section-id>, ...]    # remove sections — a `required` section is never dropped
    order:      [<section-id>, ...]    # stable reorder: listed ids lead, unlisted keep their order

# Deliverable-parameter bounds by altitude (RFC-0002 §5) — the enterprise guardrail. A requested
# deliverable param outside `allow` fails the deliverable-params-in-bounds gate.
deliverable_bounds:
  <altitude>:
    <deliverable-type>: { <param>: { allow: [<value>, ...] } }

gates: [<gate-id>, ...]      # the gates this archetype asserts (RFC-0001 §10)
```

## Block kinds (the renderer's vocabulary)

| kind | manifest `content` shape | deck-IR blocks |
|------|--------------------------|----------------|
| `summary` | `lead`, `points: [..]` | `lead`, `bullet` |
| `kpi_table` | `rows: [{metric_binding, target_binding?}]` | `kpi_row` |
| `prose` | `body` | `prose` |
| `risk_list` | `risks: [{risk, ask}]` | `risk` |
| `decision_list` | `decisions: [..]` | `decision` |
| `option_list` | `options: [{name, pro, con}]` | `option` |
| `decision_contract` | `next_step`, `residual_risks: [..]` | `next_step`, `residual_risk` |

## Authoring guidance

- **Mirror the reference.** `review.yaml` is the ground truth (reverse-engineered from the QBR @
  C-level reference). A new archetype matches its *shape* and *rigor*, not its sections.
- **Section ids are English and stable** (RFC-0001 §7) so gates and overlays are language-stable;
  only the rendered titles/prose (from the manifest `content`) are localized.
- **Never special-case a renderer.** A new block kind is added to the renderer's vocabulary once,
  as data-driven behavior — not as an archetype-specific branch.
