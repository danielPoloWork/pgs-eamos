# RFC-0006: The advanced variant — pattern matching & what-if simulation

- **Status:** Proposed (2026-06-30) — awaiting owner ratification. **Design-before-code** (AGENTS §7).
- **Date:** 2026-06-30
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** [RFC-0001](0001-eamos-meeting-os.md) §6 (grounding), §8 (human-runs-the-room), §9 (the
  series moat); builds on the classification (#27), the computed scorecard ([RFC-0003] intake +
  #23), and the decision contract (#31). Tracks issue #33 — the **deferred** advanced variant of the
  Solution-Discovery epic (#21); its dependencies (intake + scoring) have now landed.

> **How to read this.** Everything else in the epic shipped. #33 was deferred until the core intake
> and scoring existed — they now do. This RFC designs the two advanced aids, **both deterministic and
> dependency-free** (no ML, no embeddings): *pattern matching* (what did we decide in similar past
> cases?) and *what-if simulation* (how does the ranking move if a weight changes?). Both are
> **advisory** — the agent surfaces; the human decides (§8).

---

## 0. Summary

Two advisory tools over data EAMOS already produces:

- **Pattern matching** — a **decision repository** records each closed decision (its classification
  #27 + chosen option + decision contract #31). A deterministic `match` ranks past decisions by
  **classification similarity** and surfaces *what was decided, and what residual risk remained*, for
  a similar new case. Retrieval, not prediction — every match is a real past record (RFC-0001 §6).
- **What-if simulation** — a deterministic `simulate` over the scorecard (#23): apply weight/score
  **overrides**, recompute the weighted totals, and report the **ranking delta** (does build overtake
  buy if compliance is weighted higher?). It is the §23 computation re-run on a perturbed ledger — no
  new math, no randomness.

Neither is a deliverable projection or a gate; both are **tools** (`tools/advisor.py`) the architect
runs to inform the human. No new IR family.

## 1. Context & problem

The series store (the moat, §9) carries decisions/actions/risks/KPIs *within a series*. Two questions
it does not answer: (a) *"we faced a similar problem before — what did we choose, and how did it go?"*
across **different** selections, and (b) *"how sensitive is this recommendation to the weights?"*. The
trap is to reach for an LLM/embedding similarity or a Monte-Carlo simulator — both break determinism
and dependency-freedom (AGENTS §9) and turn an auditable aid into a black box. The classification
(#27) and the computed scorecard (#23) already give us **structured** keys to do both deterministically.

## 2. Pattern matching — a deterministic decision repository

### 2.1 The repository (`os/advisor/_schema.md` + a JSON store)

A cross-series append-only store. Each record is written when a decision instance closes:

```yaml
{ series_id, instance, date,
  classification: { cluster, complexity, decision_risk },     # the #27 key
  chosen_option,                                              # from recommendation / decision_ask
  next_step, residual_risks: [..] }                           # the decision contract (#31)
```

Populated by `advisor.py record <manifest> --repo <repo.json>` (reads the manifest's classification +
decision contract; appends a record). Deterministic, no clocks beyond an optional `date` field the
caller passes.

### 2.2 The match (`advisor.py match <manifest> --repo <repo.json>`)

Score every record against the new manifest's classification by **matching dimensions**:

```
score = 3·[same cluster] + 1·[same complexity] + 1·[same decision_risk]
```

Return the top-k by `(score desc, recency desc)` — a stable, reproducible ranking — surfacing each
match's `chosen_option`, `next_step`, and `residual_risks`. The human reads "in 2 past cases of a
high-risk system_replacement we chose *buy*, with lock-in as the residual risk" — and decides. No
fabrication: a match is a past record or there is none.

## 3. What-if simulation — `advisor.py simulate`

`advisor.py simulate <manifest> --set w.compliance=0.5 --set sc.build.tco=4 …` overrides the named
weight/score cells, then re-runs the **#23 computation** (`render.scorecard_ledger` on the perturbed
ledger) and prints, per option, the **baseline total → simulated total** and whether the **winner
changed**:

```
What-if (w.compliance 0.25 → 0.50):
  Build  2.5 → 3.1
  Buy    4.1 → 3.6     winner: Buy → Build ⚠
```

Deterministic (pure recomputation). It never edits the manifest — the override is a transient
sensitivity probe the human uses to test how robust the recommendation is.

## 4. Discipline (non-negotiable)

- **Advisory, human-gated.** Both tools *inform*; the human decides (RFC-0001 §8). The agent does not
  auto-pick an option from a match or a simulation.
- **Deterministic & dependency-free.** Similarity is dimension matching, not embeddings; simulation is
  recomputation, not Monte-Carlo. Same inputs → same output (AGENTS §9).
- **Grounded.** A match is a real recorded decision; a simulation is the real scorecard re-run. No
  invented precedent, no invented number (RFC-0001 §6).

## 5. What ships after ratification (the implementation PR)

1. `os/advisor/_schema.md` — the decision-repository record schema.
2. `tools/advisor.py` — `record` (append a closed decision), `match` (rank similar past cases),
   `simulate` (recompute the scorecard under `--set` overrides).
3. A small reference repository (a couple of recorded decisions) + matching `vendor-selection.yaml` so
   `match` returns a precedent and `simulate` flips the winner under a plausible re-weighting.
4. Tests — match ranking + tie-break determinism; simulate recompute + winner-change detection;
   record round-trip.

## 6. Alternatives considered

- **Embedding / LLM similarity.** Rejected: non-deterministic, ungated, opaque, and a dependency —
  against AGENTS §9 and the determinism boundary. Classification-dimension matching is auditable and
  good enough for "similar case".
- **Monte-Carlo / probabilistic what-if.** Rejected: randomness breaks reproducibility. Deterministic
  override-and-recompute answers the real question ("is the winner robust to the weights?").
- **Fold into the series store.** Rejected: the store is per-series; pattern matching needs a
  cross-series corpus. A distinct repository keeps the moat's semantics clean.

## 7. Out of scope

Ranking past cases by *outcome quality* (we record the decision, not a later success metric — that is
a follow-up once outcomes are tracked). Multi-criteria sensitivity sweeps / tornado charts (v1 does
single-override probes). Any auto-decision.

## 8. Open questions

1. **Repository population** — a dedicated `advisor.py record`, or hook it into `series.close` so a
   decision is recorded automatically on close? (Draft: **dedicated `record`**, to keep the moat and
   the repository decoupled; revisit if double-entry is annoying.)
2. **Repository location** — a committed seed corpus under `os/advisor/` vs a build-time store only.
   (Draft: **build-time store**, with a tiny seed fixture for the reference/tests.)
3. **`simulate` output as a deliverable** — keep it a CLI advisory print (draft), or also project a
   data-IR table later?
