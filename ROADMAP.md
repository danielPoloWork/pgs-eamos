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

**Status.** ✅ **complete.** Deterministic core + gates in the baseline; the **full deliverable
bundle** ships from one deck-IR — `emit_md` (deck / agenda), `emit_pptx` (board deck),
`emit_docx` (read-alone pre-read with a KPI table) — all in `output_lang`, assumed values flagged
in amber, with the "verify before the room" appendix.

## M2 — The archetype grammar

> Covers RFC §3 (axes + overlays).

**Goal.** Generalize from one archetype to the ~8, with altitude/function overlays applied by a
deterministic composition engine (base archetype + ordered overlays, never a cross-product).

**Items.** the remaining archetype profiles; the overlay schema + altitude overlays
(`c-level / vp / manager / ic`); the composition engine in `render.py`; `audience-fit` gate.

**Exit gate.** the same reference meeting renders correctly at two altitudes; a second archetype
(decision/steering) renders end-to-end.

**Status.** ✅ both met — `qbr-c-level` renders at c-level (leads with decisions) vs manager
(detail-first order) from one manifest; `esc-decision` renders end-to-end through the new
`decision` archetype, the c-level overlay dropping `context_framing`. Overlay engine = drop →
reorder → cap, deterministic.

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

**Status.** ✅ **exit gate met.** The deliverable **registry** (`os/deliverables/`, params as
validated enums), the **infographic-IR** + `emit_svg` (deterministic, dependency-free SVG), the
**data-IR** + `emit_xlsx` (KPI table, assumed cells yellow-highlighted, zero formulas), and the
`deliverable-params` + `deliverable-params-in-bounds` gates ship. The QBR renders as a
**speaker-deck, a professional infographic, and a KPI table from one ledger** — ARR proven
**identical across all three** (no divergence, RFC-0002 §7).

**Extras (complete).** `graph-IR` (mind map → `emit_svg`) and `quiz-IR` (graded with required
citations / un-scored discussion → `emit_md`) ship too. **All six IR families now exist** —
slide · doc · graph · infographic · data · quiz — every one a deterministic projection of the same
ledger (ARR identical across deck, infographic, table, mind map, and quiz). The facilitation
deliverables shipped in M6.

## M3 — Function packs

> Covers RFC §3 (axis 3).

**Goal.** Content packs per department (Eng / Product / Sales / Marketing / CS / HR / Finance /
R&D / Ops), including the regulated sections some functions add (HR comp/PIP).

**Exit gate.** an RCA @ Manager × Engineering and a QBR @ C-level × Finance both render from the
same archetypes with only the function pack swapped.

**Status.** ✅ **exit gate met.** Function packs (`orchestrator/functions/`, axis 3) compose as an
overlay — archetype → **function** → altitude — inserting a department's regulated section.
`qbr-finance` (review × c-level × **finance**) gains `variance_attestation` (SOX); `rca-eng`
(the new **post-mortem** archetype × manager × **engineering**) gains `reliability_notes` (SLO).
Proven swappable: the same review manifest with `--function finance` vs `--function engineering`
differs **only** in that one section. `render.py --function` override; deterministic.

## M4 — The series manifest (the moat)

> Covers RFC §9. **Pulled forward** of its instinctive position because it is the moat and the
> second-largest technical risk after grounding.

**Goal.** A persistent, reference-based series manifest carrying open actions, the decision log, a
rolling risk register, and KPI history across instances of a recurring meeting.

**Items.** the series-identity key (RFC §16 Q2); carry-forward of actions/decisions/risks/KPIs;
the `series-updated` gate; the Q3 QBR opening pre-populated from the Q2 instance.

**Exit gate.** a two-instance series (Q2 → Q3) where Q3 opens knowing Q2's decisions, open
actions, and KPI deltas.

**Status.** ✅ **exit gate met.** The series store (`os/series/`), `series.py close|open`, and the
manifest's `series_id` / `instance` / `carry_forward` ship. Closing **Q2** writes the store; opening
**Q3** surfaces Q2's decisions, the still-open actions (with owners), and **KPI movement**
(ARR 11.8M€ → 12.4M€ ↑, NRR 105% → 108% ↑). Store + digest deterministic; the store never invents a
number (KPI history = the instance's sourced ledger cells). This is the capability EADOS does **not**
demonstrate — the moat.

## M5 — Intake & integrations

> Covers RFC-0001 §2-G3, §15-M5; RFC-0002 §6 (the source-reorganization primitive).

**Goal.** Make providing material easy: the **source-reorganization** primitive (ingest an
uploaded deck / pasted KPIs / notes → normalize into the typed ledger: dedupe, tag, group by
topic/author, mark `sourced`), plus optional connectors (Jira / Notion / Sheets). Everything lands
in the inputs ledger.

**Exit gate.** a meeting prepared from an uploaded prior deck + a pasted KPI table, with zero
hand-entry of numbers.

**Status.** ✅ **exit gate met** (foundational primitive). `tools/intake.py` reorganizes a **pasted
KPI table** (CSV) + the **prior instance** (the series store = the prior deck's data) into a
paste-ready, deduped, tagged `inputs:` ledger — every cell `sourced`, **zero hand-entry**. Demo:
the Q3 ledger comes from `q3-kpis.csv` (current wins on dedup) + the Q2 store (gap-fills
`nrr_target`); deterministic, round-trips into a manifest. Remaining (later): live connectors
(Jira / Notion / Sheets) and a foreign-deck extractor via the `pptx`/`docx` skills.

## M6 — Live facilitation & post-meeting

> Covers RFC §4 (facilitate / follow-up), §8 (human-runs-the-room).

**Goal.** Live agenda + timeboxing, minute-taking, action capture → minutes / decision log /
follow-up, feeding the series manifest. The `human-runs-the-room` gate stays non-delegable.

**Exit gate.** a facilitated session produces minutes + a decision log + action items with
owner+due, all carried into the series manifest.

**Status.** ✅ **exit gate met.** `tools/facilitate.py prep` produces a timeboxed agenda + a
facilitation script (talking points grounded from the deck-IR, assumed values still labeled);
`followup` consumes **human-captured outcomes** → minutes (decision log + action items with
owner+due) and **carries them into the series store** (Q3 lands in the store with its decisions +
owner/due actions). The `human-runs-the-room` gate is enforced **by construction** — `followup`
refuses to run without `--outcomes`; the agent never invents the room's outcomes. This closes the
lifecycle: intake → render → facilitate(prep) → [human runs] → followup → series store → next instance.

## M7+ — Quality, localization, confidentiality hardening

> Covers RFC §10 (rubric/gates), §7 (localization), §11 (enterprise lens).

**Goal.** Per-archetype×altitude rubrics as data; localization norms per region; the
confidentiality posture (what leaves the machine, data residency, redaction) hardened; regulatory
context switching mandatory gates on.

**Exit gate.** the confidentiality posture documented and gate-enforced; a non-English board deck
passes the rubric in its `output_lang`.

**Status.** ✅ **exit gate met.** Confidentiality is **data** (`os/confidentiality/policy.yaml`):
regimes → mandatory gates + redact tags; classifications public→restricted. Enforced by the
`confidentiality` gate (regimes known; **SOX → `grounding-labeled` non-skippable**; no sensitive
cell in a `public` meeting) and `render.py --redact` (masks `pii`/`phi`/`sensitive` cells in the
shared ledger → **every projection redacted identically**; the named counterparty never leaks). The
**rubric is data** (`eval/rubric.yaml`) scored by the `rubric` gate — structural + language-agnostic,
so the **Italian** board deck passes in its `output_lang`. `os/localization/regions.yaml` carries the
per-region formality/format norms. Remaining (later): per-region format application, data-residency
connectors, the M2b extras (graph-IR / quiz-IR).

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
