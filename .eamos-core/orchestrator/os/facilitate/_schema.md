# Facilitate / Follow-up Schema

The `facilitate` and `follow-up` phases (RFC-0001 §4) around the **non-delegable**
`human-runs-the-room` gate (RFC-0001 §8). Implemented by [`tools/facilitate.py`](../../../tools/facilitate.py).

## prep (before the room)

`facilitate.py prep <manifest> [--minutes N]` → a **timeboxed agenda** + a **facilitation script**
(talking points per item), grounded from the deck-IR (same ledger, assumed values stay labeled).
The agent prepares; it does **not** run the meeting.

## human-runs-the-room (the gate)

A human runs the live session. There is no artifact boundary here — so the gate is enforced *by
construction*: `followup` refuses to run without `--outcomes`. The agent never fabricates what was
decided in the room.

## follow-up (after the room)

`facilitate.py followup <manifest> --outcomes <file> --store <store> [--out <minutes>]` consumes the
**human-captured outcomes** and produces **minutes** (decision log + action items with owner+due),
then **carries them into the series store** (RFC-0001 §9) — the loop closes; the next instance
inherits them.

### outcomes file (captured by a human)

```yaml
instance: "<id>"
decisions: [ "<decision>", ... ]
actions:   [ { action: "<text>", owner: "<who>", due: "<date>" }, ... ]
notes:     "<free text>"
```

## Invariant

The outcomes are the room's; the agent only structures them. Combined with grounding (RFC-0001 §6),
EAMOS never invents a fact **or** an outcome — it frames what humans provide.
