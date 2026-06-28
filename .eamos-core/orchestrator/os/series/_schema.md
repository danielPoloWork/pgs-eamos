# Series Store Schema (the moat)

The **series store** is the persistent, reference-based state of a *recurring* meeting series
(RFC-0001 §9) — the one capability EADOS does not demonstrate, and the product's moat. It carries
forward, across instances, the things a recurring meeting must not forget: decisions, still-open
actions, rolling risks, and KPI history. It is **state**, written by `tools/series.py close` and
read by `tools/series.py open`; it is keyed by the manifest's stable `identity.series_id`
(RFC-0001 §16-Q2), not by the per-instance `series_name`.

The store is JSON (machine state, deterministic: `sort_keys`, `ensure_ascii=False`).

```json
{
  "series_id": "<stable slug, e.g. platform-bu-business-review>",
  "instances": ["<instance id>", "..."],          // ordered history, e.g. ["Q2-2026"]
  "decision_log": [ { "instance": "<id>", "decision": "<resolved text>" } ],
  "open_actions": [ { "id": "<instance>-A<n>", "action": "<text>", "context": "<the risk>",
                      "from": "<instance>", "status": "open|closed" } ],
  "rolling_risks": [ { "risk": "<text>", "since": "<instance>", "status": "open|closed" } ],
  "kpi_history":  { "<kpi key>": { "<instance>": "<value>", "...": "..." } }
}
```

## Manifest fields that drive it

- `identity.series_id` — the stable key (same across Q2, Q3, …).
- `identity.instance` — this instance (e.g. `Q3-2026`).
- `carry_forward:` — what an opening instance pulls from the store (`from_instance`, `decisions`,
  `open_actions`, `rolling_risks`, `kpi_history`).

## Invariants

- **English keys, output-language values.** Keys are stable English; decision/action text is the
  instance's `output_lang` (resolved against that instance's ledger).
- **`series-updated` (the gate).** `close` advances the store (a new instance + its decisions /
  actions / KPIs); opening the next instance must see them. The two-instance loop (Q2 → Q3) is the
  M4 exit gate.
- **One ledger still rules.** KPI values in the history are the instance's sourced ledger cells —
  the store never invents a number.
