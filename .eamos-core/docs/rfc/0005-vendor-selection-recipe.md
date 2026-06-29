# RFC-0005: The vendor-selection recipe (discovery → decision)

- **Status:** Proposed (2026-06-30) — awaiting owner ratification. **Design-before-code** (AGENTS §7).
- **Date:** 2026-06-30
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** [RFC-0001](0001-eamos-meeting-os.md) §9 (the series moat), §13 (no bespoke profiles);
  composes the pre-work pack (#26), the computed scorecard (#23), the topology diagram (#22),
  the decision contract (#31), the no-action baseline (#30), and the intake chain (#27/#28/#29).
  Tracks issue #24, the **capstone** of the Solution-Discovery epic (#21).

> **How to read this.** A real vendor-selection agenda spans **two** archetypes: *context +
> requirements* (`discovery`) and *options + scoring + decision* (`decision`). No single archetype
> covers all six phases, and authoring a bespoke `vendor-selection` profile is exactly the
> per-meeting-type anti-pattern RFC-0001 §13 rejects. This RFC settles **how to compose** the recipe
> from the pieces already shipped — and picks **bundle vs series** (the issue's open decision).

---

## 0. Summary

The vendor-selection recipe is **composition, never a new profile** (§13). Two delivery models, both
shipped, with **series the recommended model for real procurement**:

- **Bundle** — one `decision` instance composing the `pre-work` pack (#26) + the computed scorecard
  (#23) + the topology diagram (#22) + the decision contract (#31) + the no-action baseline (#30),
  over a full inputs ledger (criteria, weights, TCO, integration effort). The one-shot decision.
  Works today (it is `vendor-prework.yaml` taken to the actual decision meeting).
- **Series** — two instances linked by `series_id`: `discovery` (requirements) → `decision`
  (scoring/decision), with carry-forward of the shortlist, open actions, and risks through the
  series store (the moat, RFC-0001 §9). The right shape for real procurement (requirements are
  gathered, then vendors are scored against them in a later meeting).

The series needs one small enabler: **`series.close` must carry by section *kind*** (`decision_list`
→ decisions, `risk_list` → open actions/risks), not by the hardcoded review-archetype ids it uses
today. That one change makes the moat archetype-general — and is backward-compatible.

## 1. Context & problem

`esc-decision.yaml` proves a single decision meeting; `vendor-prework.yaml` proves the pre-work pack
+ scorecard + topology composed onto `decision`. What is missing is the **recipe**: the documented,
gate-green, test-covered way to run a full vendor selection — and the decision of whether that is one
meeting (bundle) or a series. The trap is a `vendor-selection` archetype that hard-codes the agenda;
that re-introduces the profile explosion RFC-0001 §3/§13 eliminated. The answer is to **compose**.

## 2. The recipe — composition over a profile

```
        L0/L1/L2 intake (#29) · classify (#27) · adaptive questions (#28)
                                   │
        ┌──────────────────────────┴───────────────────────────┐
   discovery instance (requirements)              decision instance (scoring + decide)
   problem · assumptions · use-cases ·            options(+no-action #30) · weighted
   MoSCoW · constraints  (pre-work #26)           scorecard(#23) · topology(#22) ·
                                   │              recommendation · decision contract(#31)
                                   └────────── series store (moat, §9) ──────────┘
                                          shortlist · open actions · risks carried forward
```

- **Archetypes stay generic.** `discovery` carries requirements; `decision` carries options/scoring;
  the **`pre-work` pack** (axis 3) adds the use-case matrix / MoSCoW / constraints to either. No new
  archetype, no renderer branch (§13).
- **The pieces already exist.** This RFC adds reference manifests + the one `series.close` enabler;
  it ships **no new IR family and no new gate**.

## 3. Decision: bundle *and* series (series recommended)

| | Bundle | Series |
|---|---|---|
| Instances | 1 (`decision`) | 2 (`discovery` → `decision`) |
| When | a one-shot buy decision; requirements already known | real procurement; requirements gathered first, vendors scored later |
| Moat (§9) | — | shortlist / actions / risks carried forward |
| Cost | lowest | the series store + the `series.close` enabler |

Both are valuable; we ship both as references. **Series is the recommended model** for an enterprise
vendor selection (it is why the series store exists). The bundle is the lightweight fallback.

## 4. The one enabler — `series.close` carries by kind

Today `series.close` reads two hardcoded review-archetype sections (`decisions_required`,
`risks_and_asks`). A `decision` manifest (`decision_ask`, `risks_and_mitigations`) would carry
**nothing**. Fix: load the archetype and carry from sections **by kind** —

- every `decision_list` section → the decision log (the shortlist / asks);
- every `risk_list` section → open actions + rolling risks.

This is archetype-general (review's `decisions_required` *is* a `decision_list`; its `risks_and_asks`
*is* a `risk_list`), so the existing QBR series carries exactly as before — **backward-compatible**,
verified by the existing series test.

## 5. Carry-forward of the scorecard / shortlist

v1 carries the **shortlist** as the discovery instance's decisions (the vendors to evaluate) and its
risks/asks as open actions — through the kind-based `series.close` above. The **scorecard** is
*computed in the decision instance* (#23) from the requirements gathered, so it does not need to be
stored to be reproducible. A typed `shortlist` / `scorecard` carry block on the store is a possible
later enhancement (§8) — not needed for the recipe to work.

## 6. What ships after ratification (the implementation PR)

1. `tools/series.py` — `close` carries by section kind (`decision_list` / `risk_list`); the QBR
   series still carries identically.
2. `examples/vendor-selection.yaml` — the **bundle** reference: `decision` @ c-level/vp × `pre-work`,
   richer than `esc-decision` (criteria, weights, TCO, integration effort), with the scorecard,
   topology, no-action, and decision contract — gate-green.
3. `examples/series/vendor-req.yaml` + `examples/series/vendor-decision.yaml` — the **series**:
   `discovery` requirements → `decision` scoring, `series_id`-linked; a close→open round-trip carries
   the shortlist + open actions forward.
4. Tests — both references gate-green; the series carry-forward proven; `series.close` backward-compat.

## 7. Out of scope

A controlled-demo middle instance (the 3-instance variant) — the 2-instance series proves the moat;
a third instance is more of the same. Pattern-matching / what-if over past selections is the
deferred advanced variant (#33). Stacking the `pre-work` pack with a department function pack is the
known "function packs archetype-aware / stackable" backlog item, untouched here.

## 8. Open questions

1. **Typed carry block** — add a `shortlist` / `scorecard` block to the series store, or keep
   carrying the shortlist as decisions + open actions? (Draft: **keep**; revisit if a real series
   needs the structured scorecard carried.)
2. **Bundle altitude** — c-level (board sign-off) or vp (the working decision)? (Draft: **vp**, with
   the c-level overlay available; the board variant is one `--altitude c-level` away.)
3. **Series instance count in the reference** — 2 (draft) vs 3 (adds a controlled-demo instance).
