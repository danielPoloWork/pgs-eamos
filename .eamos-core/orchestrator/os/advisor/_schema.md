# Decision Repository Schema (the advisor — RFC-0006, #33)

The **decision repository** is a cross-series, append-only store of closed decisions. It is the
corpus behind **pattern matching** (similar past case → similar solution) — distinct from the series
store (the moat, RFC-0001 §9), which is per-series. Written by `tools/advisor.py record`; read by
`advisor.py match`. Deterministic and dependency-free (no ML / embeddings — retrieval, not
prediction).

```json
{
  "records": [
    {
      "series_id": "<slug>",
      "instance": "<str>",
      "date": "<str?>",
      "classification": { "cluster": "<#27 cluster>", "complexity": "<low|med|high>", "decision_risk": "<low|med|high>" },
      "recommendation": "<resolved recommendation prose — the choice>",
      "next_step": "<resolved decision-contract next_step (#31)>",
      "residual_risks": ["<resolved residual risk>", ...]
    }
  ]
}
```

## Matching (deterministic)

`match` scores every record against a new manifest's `discovery_intake.classification` (#27) by
**matching dimensions**:

```
score = 3·[same cluster] + 1·[same complexity] + 1·[same decision_risk]
```

and returns the records by `(score desc, recency desc)` — a stable, reproducible ranking (recency =
later position in `records`). It surfaces each match's `recommendation`, `next_step`, and
`residual_risks`. A match is a real recorded decision or there is none (grounding, RFC-0001 §6).

## What-if (deterministic)

`simulate` does not touch the repository: it overrides named scorecard weight/score cells (`--set
key=value`) on a copy of the manifest and re-runs the computed-scorecard projection (#23,
`render.scorecard_ledger`), reporting each option's `baseline → simulated` total and any change of
winner. Pure recomputation — no randomness.

## Invariants

- **Advisory, human-gated** (RFC-0001 §8): the tools inform; the human decides. No auto-decision.
- **Deterministic**: same repository + manifest → same ranking; same overrides → same totals.
- **Grounded**: matches are recorded decisions; simulations are the real scorecard re-run.
