# Function Pack Schema (axis 3)

A function pack (`functions/<function>.yaml`) is the **department content layer** (RFC-0001 §3,
axis 3): it fills function-specific framing and **may add a regulated section** to whatever
archetype is in play. It is orthogonal to the archetype (axis 1) and altitude (axis 2): the same
archetype renders for Finance or Engineering by swapping only the function pack — the M3 exit gate.

```yaml
function:     <id, e.g. finance | engineering | sales | hr | product | ...>
display_name: <human name>
terminology:  { <free key>: <value>, ... }   # informational framing (unit, focus, …)

# Sections this function inserts (axis 3). `after:` anchors the insert to an existing section id;
# if the anchor is absent in the active archetype, the section is appended. Composed BEFORE the
# altitude overlay (RFC-0001 §3): archetype structure → function overlay → altitude overlay.
add_sections:
  - { id: <section-id>, kind: <block-kind>, required: <true|false>, after: <anchor-id> }
```

## Invariants

- **Function fills content; it does not invent facts.** Added sections still bind the manifest's
  ledger (RFC-0001 §6) — grounding is unchanged.
- **Swappable.** Changing only `identity.function` (or `render.py --function`) swaps the function
  layer; the archetype and altitude are untouched. This is what the M3 exit gate checks.
- **Section ids are stable English** (RFC-0001 §7); the manifest provides the localized content.
