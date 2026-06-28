# EAMOS — Roadmap

The living plan. It **covers** [RFC-0001](.eamos-core/docs/rfc/0001-eamos-meeting-os.md) and
[RFC-0002](.eamos-core/docs/rfc/0002-deliverable-catalogue-and-ir-families.md) — the meeting-domain
analogue of EADOS's `roadmap-covers-rfcs` gate: every milestone traces to RFC sections, and no
milestone ships work an RFC has not ratified.

**Delivery discipline (from EADOS):** ship **one reference meeting end-to-end first**, then
generalize. QBR @ C-level is the reference instance — the analogue of `pbr-cpp-memory-pool`.

Legend — exit gate per milestone is the transition the milestone must make green.

---

## M1 — Spine + reference meeting (QBR @ C-level), end-to-end

> Covers RFC-0001 §4 (lifecycle), §5 (deck-IR), §6 (grounding), §7 (language), §12-F3 (reference);
> RFC-0002 §3 (ships **slide-IR + doc-IR** — the board deck in both modes, pre-read, agenda).

**Goal.** Prove the whole machine on one meeting: a maintainer chats (in their language) →
EAMOS resolves the QBR @ C-level archetype → writes the meeting manifest (with the inputs ledger)
→ renders the deck-IR → emits a board deck (PPTX) + pre-read (DOCX) + agenda (MD), all in
`output_lang`, with assumed values labeled and a review appendix.

**Items.**
1. `orchestrator/os/workflow/workflow.yaml` — the 6-phase state machine (intake → … → follow-up),
   schema + the reference instance.
2. `orchestrator/archetypes/_schema.md` + `archetypes/review.yaml` — the first archetype profile
   (structure + altitude shaping), mirroring EADOS's profile schema.
3. The **meeting manifest** schema + `orchestrator/examples/qbr-c-level.yaml` — the reference
   manifest (the analogue of `reference.yaml`), including the typed inputs ledger.
4. `orchestrator/os/deck-ir/_schema.md` — the deterministic deck-IR.
5. `tools/render.py` — manifest + archetype → deck-IR (EADOS renderer adapted).
6. `tools/emit_pptx.py` / `emit_docx.py` / `emit_md.py` — the cosmetic IR → binary hop via the
   `pptx`/`docx` skills.
7. `tools/eamos_lint.py` — self-lint with the first gates: `completeness`, `grounding-labeled`.
8. `eval/rubric.md` — "what good looks like" for a board deck (1-page exec summary, decision-ask,
   options+trade-offs, financial impact, clear recommendation).

**Exit gate.** `grounding-labeled` + `completeness` green on `qbr-c-level.yaml`; the rendered
bundle opens and contains the review appendix; the run scores against the rubric.

## M2 — The archetype grammar

> Covers RFC §3 (axes + overlays).

**Goal.** Generalize from one archetype to the ~8, with altitude/function overlays applied by a
deterministic composition engine (base archetype + ordered overlays, never a cross-product).

**Items.** the remaining archetype profiles; the overlay schema + altitude overlays
(`c-level / vp / manager / ic`); the composition engine in `render.py`; `audience-fit` gate.

**Exit gate.** the same reference meeting renders correctly at two altitudes; a second archetype
(decision/steering) renders end-to-end.

## M2b — Deliverable families

> Covers RFC-0002 §3–§5 (IR families, the deliverable registry, params-in-bounds).

**Goal.** Extend beyond slide-IR + doc-IR to the full catalogue: mind maps (`graph-IR`),
infographics (`infographic-IR`), tables/charts (`data-IR`), interview quizzes (`quiz-IR`), each as
a deterministic projection of the same grounded content.

**Items.** the deliverable registry `orchestrator/os/deliverables/*.yaml` (params as validated
enums); the `emit_svg` / `emit_xlsx` emitters; the `deliverable-params-in-bounds` gate (bounds set
by archetype × altitude); the facilitation deliverables (`facilitation_script`, `agenda`).

**Exit gate.** the reference QBR renders as a speaker-deck **and** a professional infographic
**and** a KPI table from one ledger, with no value diverging between them.

## M3 — Function packs

> Covers RFC §3 (axis 3).

**Goal.** Content packs per department (Eng / Product / Sales / Marketing / CS / HR / Finance /
R&D / Ops), including the regulated sections some functions add (HR comp/PIP).

**Exit gate.** an RCA @ Manager × Engineering and a QBR @ C-level × Finance both render from the
same archetypes with only the function pack swapped.

## M4 — The series manifest (the moat)

> Covers RFC §9. **Pulled forward** of its instinctive position because it is the moat and the
> second-largest technical risk after grounding.

**Goal.** A persistent, reference-based series manifest carrying open actions, the decision log, a
rolling risk register, and KPI history across instances of a recurring meeting.

**Items.** the series-identity key (RFC §16 Q2); carry-forward of actions/decisions/risks/KPIs;
the `series-updated` gate; the Q3 QBR opening pre-populated from the Q2 instance.

**Exit gate.** a two-instance series (Q2 → Q3) where Q3 opens knowing Q2's decisions, open
actions, and KPI deltas.

## M5 — Intake & integrations

> Covers RFC-0001 §2-G3, §15-M5; RFC-0002 §6 (the source-reorganization primitive).

**Goal.** Make providing material easy: the **source-reorganization** primitive (ingest an
uploaded deck / pasted KPIs / notes → normalize into the typed ledger: dedupe, tag, group by
topic/author, mark `sourced`), plus optional connectors (Jira / Notion / Sheets). Everything lands
in the inputs ledger.

**Exit gate.** a meeting prepared from an uploaded prior deck + a pasted KPI table, with zero
hand-entry of numbers.

## M6 — Live facilitation & post-meeting

> Covers RFC §4 (facilitate / follow-up), §8 (human-runs-the-room).

**Goal.** Live agenda + timeboxing, minute-taking, action capture → minutes / decision log /
follow-up, feeding the series manifest. The `human-runs-the-room` gate stays non-delegable.

**Exit gate.** a facilitated session produces minutes + a decision log + action items with
owner+due, all carried into the series manifest.

## M7+ — Quality, localization, confidentiality hardening

> Covers RFC §10 (rubric/gates), §7 (localization), §11 (enterprise lens).

**Goal.** Per-archetype×altitude rubrics as data; localization norms per region; the
confidentiality posture (what leaves the machine, data residency, redaction) hardened; regulatory
context switching mandatory gates on.

**Exit gate.** the confidentiality posture documented and gate-enforced; a non-English board deck
passes the rubric in its `output_lang`.

---

## Traceability (milestone → RFC)

| Milestone | RFC sections |
|-----------|--------------|
| M1 | RFC-0001 §4, §5, §6, §7, §12-F3 · RFC-0002 §3 (slide-IR + doc-IR) |
| M2 | RFC-0001 §3 |
| M2b | RFC-0002 §3, §4, §5 |
| M3 | RFC-0001 §3 |
| M4 | RFC-0001 §9 |
| M5 | RFC-0001 §2-G3 · RFC-0002 §6 |
| M6 | RFC-0001 §4, §8 |
| M7+ | RFC-0001 §7, §10, §11 |
