# RFC-0007: Preference memory — learning material-shaping preferences from room feedback

- **Status:** Accepted (ratified by the owner, 2026-07-02). **Design-before-code** (AGENTS §7).
- **Date:** 2026-07-02
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** [RFC-0001](0001-eamos-meeting-os.md) §6 (grounding), §8 (human-runs-the-room), §9
  (the series moat); [RFC-0006](0006-advanced-variant.md) (the advisor — same retrieval-not-prediction
  shape); builds on `facilitate followup` (M6, the outcomes capture), the series store (#24, #56
  idempotency), altitude shaping + `deliverable_bounds` (RFC-0002 §5), and the manifest-schema gate
  (#59). Tracks issue #67.

> **How to read this.** EAMOS remembers **facts** (series store) and **precedents** (advisor
> repository, RFC-0006) — but nothing captures **how the audience wants material shaped**. If the
> CFO rejects the Q2 deck as too long and table-averse, the Q3 deck opens with exactly the same
> shaping. This RFC designs a **deterministic preference memory** — no ML, fully in-pattern:
> a closed tag vocabulary (data) → an audited fold into the series store → a compile step that
> writes the deltas **into the manifest, visibly, at intake** → a gate. The system never adapts
> silently: `manifest-confirmed` stays the human checkpoint, applied to the machine's own memory.

---

## 0. Summary

Four small pieces, one per station of the existing loop:

- **Capture** — `facilitate followup` accepts an optional `material_feedback:` block in the
  outcomes YAML: per deliverable, a `verdict` enum + tags from a **closed vocabulary**
  (`os/advisor/feedback-tags.yaml`). Tags are structural and gateable; free text is not.
- **Store** — `followup` folds the tags into a new `preferences` section of the series store,
  keyed by altitude × deliverable × tag, each with **instance provenance and a count** — memory
  with an audit trail, idempotent under re-runs (#56 semantics).
- **Apply** — `series open` compiles the accumulated tags into **shaping deltas** via a fixed
  table in the same vocabulary file (`too_long → max_slides −25%`), prints them as a proposal,
  and the maintainer writes them into the manifest as an explicit `preferences_applied:` block.
  Render applies that block as one more deterministic overlay — **after** the altitude overlay.
- **Gate** — `preferences-valid`: every tag in vocabulary; every compiled delta **tightens, never
  violates** the archetype's altitude budget and `deliverable_bounds`.

No new IR family, no new tool — extensions to `facilitate.py`, `series.py`, `render.py`,
`eamos_lint.py`, plus one vocabulary file.

## 1. Context & problem

The rubric is static data and the gates are structural minimums — neither is *learned taste*. The
feedback loop for document preferences does not exist: the room's reaction to the material dies in
the minutes' free-text notes. The trap is to reach for free-text sentiment or an LLM summary of
"what the CFO said" — that re-opens the fabrication door exactly where trust matters most (the
system would be *inferring* a preference and acting on it invisibly). The house rules give us a
better shape: **closed vocabulary as data, deterministic application, provenance, a gate, and a
human checkpoint** — the same shape as RFC-0006's advisor.

## 2. Capture — `material_feedback` in the outcomes YAML

The outcomes file is already the one artifact a **human** authors after the room
(human-runs-the-room, RFC-0001 §8). It gains an optional block:

```yaml
material_feedback:                       # optional; absent = no signal (not "accepted")
  presentation: { verdict: edited,   tags: [too_long, lead_with_numbers] }
  mindmap:      { verdict: rejected, tags: [drop_deliverable] }
```

- `verdict: accepted | edited | rejected` — the coarse outcome of the material in the room.
- `tags` — only values from `os/advisor/feedback-tags.yaml`. Unknown tags fail loudly at
  `followup` time (the loader philosophy, #55) — a typo must not silently become a non-preference.

### 2.1 The vocabulary (`os/advisor/feedback-tags.yaml`)

One file: the closed tag set **and** the deterministic delta each tag compiles to — knowledge is
data, adding a tag never touches code. Draft v1 vocabulary:

```yaml
version: 1
tags:
  too_long:          { group: length,  delta: { max_slides_scale: 0.75 } }
  too_detailed:      { group: depth,   delta: { max_slides_scale: 0.85 } }
  too_shallow:       { group: depth,   delta: { max_slides_scale: 1.0 } }    # advisory: never widens
  lead_with_numbers: { group: lead,    delta: { order_lead: kpi_table } }    # section KIND to front
  lead_with_risks:   { group: lead,    delta: { order_lead: risk_list } }
  drop_deliverable:  { group: bundle,  delta: { drop_deliverable: true } }   # the tagged deliverable
  add_preread:       { group: bundle,  delta: { add_deliverable: doc } }
  tone_more_formal:  { group: tone,    delta: {} }                           # advisory-only in v1
```

`group` makes conflicts decidable: within a group, **the most recent instance's tag wins** (the
CFO's latest reaction outranks an older one). Deltas are deliberately conservative — a preference
may **tighten** shaping (fewer slides, reorder, drop a deliverable) but never widen a budget or
add depth the altitude forbids (see §5).

## 3. Store — the `preferences` section of the series store

`followup` folds the block into the store (same file as decisions/actions — one moat):

```json
"preferences": {
  "c-level": {
    "presentation": {
      "too_long":          { "count": 1, "instances": ["Q2-2026"] },
      "lead_with_numbers": { "count": 2, "instances": ["Q2-2026", "Q3-2026"] }
    },
    "mindmap": { "drop_deliverable": { "count": 1, "instances": ["Q2-2026"] } }
  }
}
```

Keyed by **altitude** (a board's taste is not a team's), then deliverable, then tag. Provenance is
the instance list; the count is derived but stored for the digest. **Replace-by-instance** (#56):
re-running `followup` for the same instance first removes that instance from every tag before
re-adding — `followup ×2` stays byte-identical to `×1`.

## 4. Apply — compiled into the manifest, confirmed by a human

**The memory never acts invisibly.** `series open` (the carry-forward digest) compiles the
accumulated tags for the manifest's altitude via the vocabulary table and prints the proposal:

```
## Learned preferences (c-level, from Q2-2026, Q3-2026)
- presentation: max_slides 12 → 9 (too_long), lead with KPI section (lead_with_numbers ×2)
- mindmap: drop from the bundle (drop_deliverable)
Apply by adding the `preferences_applied:` block below to the manifest, then confirm it.
```

The maintainer pastes (or the agent drafts, pre-confirmation) an **explicit manifest block**:

```yaml
preferences_applied:                     # written at intake; part of manifest-confirmed
  from_instances: [Q2-2026, Q3-2026]
  presentation: { max_slides: 9, order_lead: kpi_table }
  drop_deliverables: [mindmap]
```

`render.py` applies this block as one more deterministic overlay, **after** the altitude overlay
(base structure → function pack → altitude → preferences). Render never reads the series store:
the manifest stays the single source of truth, `manifest-confirmed` covers the adaptation, and the
render path stays pure. The deck-IR needs no new fields — the overlay only changes what the
existing fields contain.

## 5. Gate — `preferences-valid`

Structural, decidable, in `eamos_lint.py` (per-gate findings, #60):

- every key/tag in `material_feedback` (outcomes, checked at followup) and every field of
  `preferences_applied` (manifest, checked at lint) is in the vocabulary / schema;
- `max_slides` may only **tighten** the altitude budget (`≤` the archetype's `altitude_shaping`
  cap) — a learned preference may narrow, never violate, the guardrails;
- `order_lead` names a section kind present in the composed structure; a dropped deliverable is in
  the manifest's bundle; an added one has a registry entry (`deliverable_bounds` still apply);
- `drop` never removes a `required` section (the completeness gate's invariant is untouched).

`manifest-schema` (#59) gains `preferences_applied` in `top_level` — one data edit.

## 6. Discipline (non-negotiable)

- **Human-gated adaptation.** The compile step *proposes*; the block enters the manifest only via
  the maintainer; `manifest-confirmed` covers it. The system never reshapes silently.
- **Deterministic & dependency-free.** Tags, not sentiment; a fixed compile table, not inference;
  counts + provenance, not scores. Same store + same manifest → same proposal, byte for byte.
- **Grounded memory.** Every preference traces to a named instance's captured outcomes — the
  grounding stance (RFC-0001 §6) applied to the machine's own memory.
- **Tighten-only.** A preference can make material shorter, reordered, or leaner — never longer
  than the altitude budget, never outside `deliverable_bounds`.

## 7. What ships after ratification (the implementation PRs)

1. `os/advisor/feedback-tags.yaml` (vocabulary + deltas) and the `material_feedback` /
   `preferences_applied` schema additions (`os/series/_schema.md`, `os/manifest/schema.yaml`).
2. `facilitate.py followup` — validate + fold `material_feedback` into `preferences`
   (replace-by-instance).
3. `series.py open` — compile + print the proposal block in the carry-forward digest.
4. `render.py` — the `preferences_applied` overlay after altitude shaping.
5. `eamos_lint.py` — `gate_preferences_valid`; reference outcomes file gains a feedback block.
6. Tests: fold idempotency, conflict resolution (group + recency), tighten-only enforcement,
   compile determinism, the overlay end-to-end on the reference series.

## 8. Scope ladder (v1 boundary)

**v1 is per-series only** — the memory lives in one series store, keyed by altitude, with clean
provenance. The tempting next step — rolling preferences up to `(altitude × function)` defaults
across series ("all our C-level decks should lead with numbers") — is **explicitly deferred to its
own RFC**: cross-series inference is where fabrication risk re-enters (whose taste is it, on what
evidence?), and it needs an ownership/consent model first.

## 9. Alternatives considered

- **Free-text feedback + LLM interpretation.** Rejected: non-deterministic, ungated, and it makes
  the system *infer* a preference and act on it — the silent-adaptation failure mode this design
  exists to prevent.
- **Auto-apply from the store at render time.** Rejected: hidden state breaks the manifest as the
  single source of truth and bypasses `manifest-confirmed`. The compile-into-the-manifest step is
  the whole safety story.
- **Mutating the rubric.** Rejected: the rubric is the shared quality bar (what *good* looks
  like); preferences are one audience's taste. Conflating them lets taste erode the bar.
- **Storing preferences in the advisor repository.** Rejected: the repository is cross-series
  precedent retrieval (RFC-0006); preferences are per-series state with instance provenance — the
  series store's exact semantics.

## 10. Open questions

1. **Application threshold** — apply a tag from `count ≥ 1`, or require `≥ 2` (a repeated signal)
   before it compiles to a delta? (Draft: **≥ 1 for `bundle` tags, ≥ 1 for `lead`, ≥ 1 for
   `length`** — the human confirms anyway; revisit if proposals feel twitchy.)
2. **Decay / reset** — does `verdict: accepted` with no tags clear the accumulated tags for that
   deliverable (the audience is satisfied), or does memory only grow? (Draft: **accepted clears
   the deliverable's tags** — satisfaction is signal too.)
3. **Digest ergonomics** — should `series open` emit the ready-to-paste YAML block (draft: yes) or
   only the prose proposal?
4. **`tone_*` tags** — advisory-only in v1 (recorded, surfaced, no delta). Promote to a delta once
   a structural lever exists (e.g. a formality-driven chrome variant)?

## 11. Implementation notes (post-ratification)

Three refinements made while implementing, all within the ratified design:

- **`max_slides_pct` (int) instead of `max_slides_scale` (float)** — yamlmini deliberately keeps
  unquoted decimals as strings (the version-number rule), so the vocabulary carries an integer
  percentage (`75` = scale to 75%).
- **`add_preread` is advisory-only in v1** — there is no `doc` deliverable registry type (the
  pre-read is a projection of the presentation deck-IR), and the gate requires an added
  deliverable to be registered. The tag is recorded and surfaced; it compiles to no delta until a
  registry type exists.
- **§5 "a dropped deliverable is in the manifest's bundle" clarified as drop-honored** — the gate
  fails when a deliverable listed in `drop_deliverables` is *still* in the bundle (the learned
  drop entered the manifest but was not honored). The inverse reading would force keeping the
  deliverable just to declare its drop.
