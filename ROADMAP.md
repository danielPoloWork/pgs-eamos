# EAMOS — Roadmap

The living plan. It **covers** [RFC-0001](.eamos-core/docs/rfc/0001-eamos-meeting-os.md) and
[RFC-0002](.eamos-core/docs/rfc/0002-deliverable-catalogue-and-ir-families.md) — the meeting-domain
analogue of EADOS's `roadmap-covers-rfcs` gate: every milestone traces to RFC sections, and no
milestone ships work an RFC has not ratified.

**Delivery discipline (from EADOS):** ship **one reference meeting end-to-end first**, then
generalize. QBR @ C-level is the reference instance — the analogue of `pbr-cpp-memory-pool`.
**Track:** enterprise-deterministic (a typed manifest → reproducible render → gate-checked
projections), **not** RAG-synthesis over arbitrary sources.

`[x]` shipped on `main` · `[ ]` open. A milestone is checked when its **exit gate** is green.

---

## Status at a glance

- [x] **M1** — Spine + reference meeting (QBR @ C-level), end-to-end
- [x] **M2** — Archetype grammar (overlay engine + 7 archetypes)
- [x] **M2b** — Deliverable families (all six IR families)
- [x] **M3** — Function packs (axis 3)
- [x] **M4** — Series manifest — the moat
- [x] **M5** — Intake & integrations (primitive + connectors)
- [x] **M6** — Live facilitation & post-meeting
- [x] **M7** — Quality, localization, confidentiality hardening
- [x] **Hardening** — dependency-free test suite (25 tests) in CI

**Backlog (open, out of the core):**

- [ ] Jira / Notion API connectors (need credentials; contract documented)
- [ ] Per-region format application (date/decimal) at render time
- [ ] Data-residency connectors / egress controls beyond redaction
- [ ] Function packs **archetype-aware** (so a pack's section only lands where it fits)
- [ ] More function packs (Sales · Marketing · CS · HR · Finance · Product · R&D · Ops) + rubric cells
- [ ] More rubric cells (every archetype × altitude) + per-region localization norms applied

> **Not pursued (deliberate):** NotebookLM-style broad ingestion (PDF/URL/audio + RAG) and
> chat-Q&A-over-corpus. EAMOS stays on the enterprise-deterministic track.

---

## [x] M1 — Spine + reference meeting (QBR @ C-level), end-to-end

> Covers RFC-0001 §4 (lifecycle), §5 (deck-IR), §6 (grounding), §7 (language), §12-F3 (reference);
> RFC-0002 §3 (slide-IR + doc-IR).

- [x] **Exit gate** — `grounding-labeled` + `completeness` green on `qbr-c-level.yaml`; bundle opens with the review appendix; scored vs the rubric.
- [x] `os/workflow/workflow.yaml` — the 6-phase state machine (intake → … → follow-up)
- [x] `review` archetype + `_schema`; the meeting-manifest schema; `examples/qbr-c-level.yaml` (typed inputs ledger)
- [x] `os/deck-ir/_schema.md` + `tools/render.py` (deterministic deck-IR)
- [x] `emit_md` (deck/agenda) + `emit_pptx` (board deck) + `emit_docx` (read-alone pre-read w/ KPI table) — the full bundle from one IR
- [x] `tools/eamos_lint.py` — `completeness`, `grounding-labeled`, `audience-fit`
- [x] `eval/rubric.md` (narrative) — what a good board deck looks like

## [x] M2 — Archetype grammar

> Covers RFC-0001 §3 (axes + overlays).

- [x] **Exit gate** — the same manifest renders at two altitudes; a second archetype renders end-to-end.
- [x] Overlay engine in `render.py` — drop → reorder → slide-cap, deterministic, never a cross-product
- [x] Altitude overlays (`c-level / vp / manager / ic`); `audience-fit` gate
- [x] `decision` archetype + `examples/esc-decision.yaml`
- [x] **Archetype library: seven** — `review` · `decision` · `post-mortem` · `planning` · `retrospective` · `discovery` · `one_on_one` (the last `confidential` by default), each with a gate-green reference manifest

## [x] M2b — Deliverable families

> Covers RFC-0002 §3–§5 (IR families, the deliverable registry, params-in-bounds).

- [x] **Exit gate** — the QBR renders as a speaker-deck **and** infographic **and** KPI table from one ledger, no value diverging.
- [x] Deliverable **registry** (`os/deliverables/`) — params as validated enums
- [x] `infographic-IR` + `emit_svg` (deterministic, dependency-free SVG)
- [x] `data-IR` + `emit_xlsx` (KPI table; assumed cells yellow-highlighted; zero formulas)
- [x] `graph-IR` (mind map → `emit_svg`) + `quiz-IR` (graded w/ citation + discussion → `emit_md`)
- [x] `deliverable-params` + `deliverable-params-in-bounds` gates
- [x] **All six IR families** — slide · doc · graph · infographic · data · quiz — ARR proven identical across all of them

## [x] M3 — Function packs

> Covers RFC-0001 §3 (axis 3).

- [x] **Exit gate** — an RCA @ Manager × Engineering and a QBR @ C-level × Finance render, swapping only the function pack.
- [x] `os/functions/` packs (axis 3); `apply_function` + `composed_structure` (archetype → function → altitude); `render.py --function`
- [x] `finance` (adds `variance_attestation`/SOX) + `engineering` (adds `reliability_notes`/SLO) packs
- [x] `post-mortem` archetype; `examples/qbr-finance.yaml` + `examples/rca-eng.yaml`
- [ ] Remaining departments as packs (Sales · Marketing · CS · HR · Finance · Product · R&D · Ops)

## [x] M4 — Series manifest (the moat)

> Covers RFC-0001 §9.

- [x] **Exit gate** — a two-instance series (Q2 → Q3) where Q3 opens knowing Q2's decisions, open actions, KPI movement.
- [x] Series store (`os/series/`) + `tools/series.py close|open`
- [x] Manifest `series_id` / `instance` / `carry_forward`
- [x] Carry-forward: decision log, open actions, rolling risks, **KPI movement** (↑/↓) — never invents a number (history = sourced cells)

## [x] M5 — Intake & integrations

> Covers RFC-0001 §2-G3, §15-M5; RFC-0002 §6.

- [x] **Exit gate** — a meeting prepared from an uploaded prior deck + a pasted KPI table, zero hand-entry of numbers.
- [x] Source-reorganization primitive (`tools/intake.py`) — pasted KPI **CSV** + **prior instance** (series store) → paste-ready, deduped, tagged, all-`sourced` ledger
- [x] **Foreign-deck extractor** `--deck <file.pptx>` + pluggable connector interface (`path → cells`; precedence series → deck → csv); proven by a round-trip
- [x] **Sheets** = CSV export (documented; no native client needed)
- [ ] Live **Jira / Notion** API connectors (need credentials; documented behind the same contract)

## [x] M6 — Live facilitation & post-meeting

> Covers RFC-0001 §4 (facilitate / follow-up), §8 (human-runs-the-room).

- [x] **Exit gate** — a facilitated session produces minutes + a decision log + action items (owner+due), all carried into the series manifest.
- [x] `facilitate.py prep` — timeboxed agenda + facilitation script (talking points grounded from the deck-IR)
- [x] `facilitate.py followup` — minutes (decision log + owner/due actions) from human-captured outcomes → carried into the series store
- [x] `human-runs-the-room` gate — enforced **by construction** (`followup` refuses without `--outcomes`; the agent never invents the room's outcomes)

## [x] M7 — Quality, localization, confidentiality hardening

> Covers RFC-0001 §10 (rubric/gates), §7 (localization), §11 (enterprise lens).

- [x] **Exit gate** — confidentiality posture documented + gate-enforced; a non-English board deck passes the rubric in its `output_lang`.
- [x] Confidentiality as **data** (`os/confidentiality/policy.yaml`) — regimes → mandatory gates + redact tags; classifications public→restricted
- [x] `confidentiality` gate (SOX → `grounding-labeled` non-skippable; no sensitive cell in a `public` meeting) + `render.py --redact` egress (one ledger → every projection redacted; no PII leak)
- [x] Rubric as **data** (`eval/rubric.yaml`) + `rubric` gate (structural, language-agnostic → the Italian board deck passes)
- [x] Localization norms (`os/localization/regions.yaml`)
- [x] **Test suite** (`tools/tests/`, 25 tests, run in CI) — determinism, no-divergence, grounding, overlays, gate-teeth, series/intake/facilitate, redaction
- [ ] Per-region format application at render time (date/decimal)
- [ ] Data-residency controls beyond redaction

---

## Cross-cutting backlog

- [ ] Function packs **archetype-aware** — a pack's `add_sections` should only land in relevant archetypes (today they apply to all; worked around in the references)
- [ ] More rubric cells (every archetype × altitude); apply the per-region localization norms
- [ ] More reference meetings (a non-QBR flagship); `tools/tests/` coverage as features land

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
| M7 | RFC-0001 §7, §10, §11 |
