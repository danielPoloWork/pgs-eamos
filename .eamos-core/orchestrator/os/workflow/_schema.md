# Workflow Schema (the meeting lifecycle state machine)

The meeting lifecycle (RFC-0001 §4) as data: states are phases; transitions are **gated and never
automatic**; each phase is opt-in, resumable, and role-owned. A gate with `human: true` is
**non-delegable** — an agent never crosses it (RFC-0001 §8).

```yaml
version: <int>
states:  [<phase>, ...]          # the ordered phase ids
initial: <phase>
phases:
  <phase>:
    produces: <what this phase outputs>
    owner:    <role id from authority>
    gate:     { id: <gate-id>, human: <true|false> }   # the terminal gate of this phase
    next:     <phase | null>     # null = terminal phase
```

## Invariants

- **Human holds the terminal gate.** `manifest-confirmed` (intake) and `human-runs-the-room`
  (facilitate) are `human: true` and never crossed by an agent.
- **No phase auto-advances.** The gate is the only path forward; a failed gate means fix-and-retry,
  never silence-and-proceed.
- **Versioned**, so the schema can evolve while the persistent series manifest references a version.
