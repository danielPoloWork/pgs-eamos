# EAMOS Evaluation Rubric

"What good looks like", as data the `review-passed` gate scores against (RFC-0001 §10). The rubric
is **per archetype × altitude** — a board deck and a manager status share the `review` archetype
but a different bar. This file seeds the reference instance; M7 generalizes it to every cell.

## review @ c-level (board deck) — the M1 reference bar

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 1 | **One-page exec summary** | the deck leads with a `summary` section; ≤ 3 bullets + a lead |
| 2 | **Explicit recommendation** | `lead_with: recommendation` honored — the ask leads, not the data |
| 3 | **KPI vs target** | every headline KPI shows value *and* target (variance is visible) |
| 4 | **Decisions are explicit** | a `decision_list` section states the asks as decisions, not topics |
| 5 | **Financial impact present** | the objective and decisions reference the financial figures (bound) |
| 6 | **No unsourced numbers** | `grounding-labeled` green: every figure sourced, or labeled + in the appendix |
| 7 | **Altitude fit** | `audience-fit` green: within the c-level slide budget; jargon `none` |
| 8 | **Review appendix** | if any value is assumed, a "verify before the room" appendix lists it |

## Scoring

- Criteria 6–8 are **gate-backed** (mechanically checked by `eamos_lint.py`) — non-negotiable.
- Criteria 1–5 are **structural-advisory** for M1 (checked by section presence/shape); they become
  mechanical as the rubric data model matures (M7).
- A run **passes** when all gate-backed criteria are green and no structural criterion is missing.

## Authoring guidance

- Mirror this table when adding a cell (e.g. `post-mortem @ manager`): keep the gate-backed core
  (grounding, audience-fit, completeness) and adjust the archetype-specific criteria.
- Never encode a number-fabrication shortcut as "good". The bar is *structure, framing, rigor* —
  never invented facts (RFC-0001 §3, §6).
