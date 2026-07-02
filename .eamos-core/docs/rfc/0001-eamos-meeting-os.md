# RFC-0001: EAMOS — the agentic meeting operating system

- **Status:** Accepted (2026-06-28) — direction ratified by [ADR-0001](../adr/0001-eamos-second-instance-of-the-eados-pattern.md); this is the living design. **Frozen for M1.**
- **Date:** 2026-06-28
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** EADOS `RFC-0001` (the pattern this re-instances), ADR-0001 (EAMOS as the second
  instance), the machine-readable specs under [`orchestrator/os/`](../../orchestrator/os/), `AGENTS.md`,
  [`ROADMAP.md`](../../../ROADMAP.md) (the plan that covers this RFC).

> **How to read this.** This RFC is the master design for EAMOS. It ratifies *what* we build and
> *why*; the normative *data* lives in the machine-readable specs under `orchestrator/os/` and the
> archetype profiles under `orchestrator/archetypes/`. The milestones (§15) sequence the build
> behind one reference meeting so the system is proven end-to-end before it is generalized.
> EAMOS is the **second instance of the EADOS pattern**: same machine (interview → manifest →
> profiles → templates → render → gate → roles), different class of output (meeting material
> instead of governed repositories).

---

## 0. Summary

EAMOS is a **phase-based agentic meeting operating system**: an opt-in pipeline —
`intake → structure → draft → review → facilitate → follow-up` — that turns a maintainer's
inputs into the **material and the regie** for an enterprise meeting (briefing, deck,
facilitation script, minutes, decision/action log), for any company, department, altitude, and
output language.

It re-uses the EADOS spine — *knowledge is data, not code*; a persistent, reference-based
manifest as state; deterministic routing; humans hold every terminal gate — and replaces the
*body*: meeting **archetypes** instead of language profiles, a deliverable **deck-IR** instead of
a source tree, and a meeting lifecycle instead of a software lifecycle.

Three decisions define the system and are resolved here:

1. **Composable grammar, not a meeting catalogue** (§3). A meeting is a point in a small space
   of orthogonal-ish axes (archetype × altitude × function × company-context), composed by
   **overlays**, not a hand-written profile per meeting type.
2. **A deterministic deck-IR is the keystone** (§5). The agent renders a typed intermediate
   representation — not a `.pptx` directly — so the render is reproducible and the quality gates
   are *structural* (decidable, dependency-free), exactly like EADOS renders `project.yaml`.
3. **EAMOS frames and structures; it labels what it invents** (§6). Provided data is bound by
   source; missing data may be filled *professionally* but is rendered with a visible marker and
   collected into a "verify before the room" checklist. The grounding gate is a **labeling**
   gate, not a prohibition.

Everything is *data + gates*, so adding a new archetype, altitude, function pack, or gate is
editing a validated YAML file — never a special case in code.

## 1. Context & problem

The owner runs an enterprise agentic-OS family. EADOS proved the pattern in one domain
(governed software repositories). EAMOS targets a second, high-value domain: the **preparation,
facilitation, and follow-up of enterprise meetings** — QBRs, steering/decision boards, planning,
reviews, retrospectives, post-mortems, alignment syncs, all-hands, 1:1s — across any company
size, sector, regulatory regime, framework, and **output language**.

The naive framings are both wrong:

- A **"make-a-deck-with-AI" wrapper** — fabricates numbers, has no state across recurring
  meetings, and dies the first time it invents a KPI in a board deck (in a SOX context, a
  liability, not a feature).
- A **catalogue of 40+ meeting types** — mixes the organizational axis (Exec / Product /
  Engineering) with the ceremony axis (QBR / Retro / Post-mortem), so every new meeting is a new
  profile → combinatorial explosion of near-duplicates.

The architectural review (this RFC) concluded EAMOS must be **declarative data enforced by
mechanical gates**, re-using the EADOS spine and rebuilding only the parts the meeting domain
genuinely changes: the lifecycle state machine, the deck-IR render target, the grounding model,
and the three-tier language model.

## 2. Goals / non-goals

**Goals.** (G1) One opt-in phase pipeline for the meeting lifecycle. (G2) A **composable grammar**
of ~8 archetypes shaped by altitude/function/context overlays — not a meeting catalogue. (G3) A
**deterministic deck-IR** as the render target, so the render is reproducible and the gates are
structural. (G4) A **grounding model** that binds sourced data and labels assumed data (G_safety).
(G5) A **three-tier language model**: interview language, output language, English on disk. (G6)
A **persistent, reference-based series manifest** carrying decisions / open actions / rolling
risks / KPI history across recurring meetings — the moat (§9). (G7) Persona ≠ authority; the
human holds the room (§8). (G8) Machine-readable specs (`workflow`, `authority`, `deck-ir`,
`gate`) with schemas + lint, and archetype profiles as data.

**Non-goals.** (N1) A runtime kernel / scheduler / live transcription engine — "Operating System"
means the opinionated governance layer that decides how meeting material flows, declarative and
human-gated. (N2) Autonomous delivery of material to real executives — the agent **drafts**, the
human **presents**. (N3) A data-warehouse / BI tool — EAMOS consumes inputs the maintainer
provides or pastes; it does not own the source-of-truth for numbers. (N4) Inventing facts
silently — invention is allowed only *labeled* (§6).

## 3. The composable grammar (axes + overlays)

A meeting is **not** a profile. It is a point in a small space, composed by overlays:

- **Axis 1 — Archetype** (the deep structure; ~8, reusable everywhere):
  `decision/steering` · `review/status` · `planning` · `discovery/workshop` ·
  `retrospective/post-mortem` · `alignment/sync` · `informational/broadcast` ·
  `development/1:1`.
- **Axis 2 — Audience altitude** (`board/c-level → vp/director → manager/lead → ic`): governs
  depth, length, jargon, what to lead with, what to show/hide.
- **Axis 3 — Function** (Eng, Product, Sales, Marketing, CS, HR, Finance, R&D, Ops): fills
  *content*, occasionally adds a regulated section.
- **Axis 4 — Company context** (size, sector, regulatory [SOX/GDPR/HIPAA], framework
  [SAFe/Scrum/Kanban], formality, **output language**).

**Critical correction to the naive model: the axes are not a clean cross-product.** Altitude
*removes/reorders* sections (a board "review" drops what a manager "review" keeps); function can
*add* a regulated section (an HR 1:1 has comp/PIP structure an Eng RCA does not). So a meeting is
a **base archetype + ordered overlays** that may add / remove / reorder sections — exactly the
mechanism EADOS already uses for per-domain workflow overlays and the `domains/*` axis. The
composition engine applies overlays deterministically; it never multiplies profiles.

A QBR is therefore not a type — it is `review @ c-level × finance/whole-company × {context}`. An
RCA is `post-mortem @ manager × engineering`. ~40 "meeting types" collapse into ~8 archetypes ×
overlays.

## 4. The phase model (meeting lifecycle state machine)

The pipeline is a state machine defined as data in `orchestrator/os/workflow/workflow.yaml`.
States are phases; transitions are **gated and never automatic**; each phase is opt-in,
resumable, and owned by a role.

| Phase | What it produces | Terminal gate |
|-------|------------------|---------------|
| **intake** | the meeting manifest (axes resolved) + the `inputs` ledger (what material exists) | `manifest-confirmed` (human) |
| **structure** | the deck-IR skeleton for each deliverable (sections per archetype × overlays) | `structure-complete` |
| **draft** | the deck-IR filled — sourced bindings + labeled assumptions | `grounding-labeled` |
| **review** | quality pass against the rubric (completeness, audience-fit) | `review-passed` |
| **facilitate** | live agenda, timeboxing, minute/decision/action capture | `human-runs-the-room` (human) |
| **follow-up** | minutes, decision log, action items → carried into the series manifest | `series-updated` |

> **Note (not in EADOS): the human-gate has no clean artifact boundary in `facilitate`.** The
> "publish" act of a meeting is a human speaking in a room. EAMOS therefore treats `facilitate`
> as **human-driven by construction**: the agent prepares the live agenda and captures notes, but
> the gate `human-runs-the-room` is non-delegable — an agent never runs a live meeting with real
> people. This is the meeting-domain analogue of EADOS's "agent drafts, human publishes". See §8.

This lifecycle is **net-new** — it does not transfer from EADOS's `init → design → plan →
scaffold → audit → refactor` (a software lifecycle). Only the *shape* (gated, resumable,
role-owned, human-terminated) transfers.

## 5. The deck-IR (the keystone)

> **Generalized by [RFC-0002](0002-deliverable-catalogue-and-ir-families.md).** The deck-IR is one
> of **six IR families** (slide / doc / graph / infographic / data / quiz). A meeting produces a
> *bundle* of deliverables, each a projection of the same grounded content into one IR family,
> parameterized by validated enums. Everything below about the deck-IR holds for every family.

EADOS's render is trustworthy because it is **deterministic**: `render.py` substitutes
`{{PLACEHOLDER}}` → text, same manifest → same bytes, and a gate checks the result. A `.pptx`
produced directly by an LLM-driven skill has neither property. **The fix: the agent renders a
typed intermediate representation — the deck-IR — and the skill is only the last hop IR → binary.**
The gates run on the IR, never on the binary.

```yaml
# deck-ir/<deliverable>.yaml — deterministic, gate-checkable, output-language-tagged
deliverable: decision_deck
archetype: review
altitude: c-level
output_lang: it
sections:                       # produced by archetype structure + overlays (§3)
  - id: exec_summary
    kind: summary
    blocks:
      - { type: heading, text: "Sintesi esecutiva" }
      - { type: metric, binding: kpi.arr_qoq }      # ref into the inputs ledger (§6)
  - id: kpi_vs_target
    kind: table
    rows:
      - { label: "ARR", binding: kpi.arr, target_binding: kpi.arr_target }
review_appendix: auto          # the "verify before the room" checklist (§6) is generated here
```

A renderer (`tools/render.py`, the EADOS renderer adapted) resolves bindings against the inputs
ledger and emits the deck-IR; a thin per-format emitter (`emit_pptx.py` / `emit_docx.py` …)
drives the `pptx`/`docx`/`xlsx`/`pdf` skills as the final, *non-load-bearing* step. The
determinism boundary is the deck-IR: everything upstream is reproducible and gated; only the
cosmetic binary render is generative.

## 6. Grounding model (sourced inputs + labeled assumptions)

The grounding gate cannot be the semantic check "no unsourced numbers in prose" — that is an NLP
problem over free text, not a structural check like EADOS's `roadmap-covers-rfcs`. We make it
structural by **changing the authoring model**: numbers never live in prose; they are typed
bindings resolved from an **inputs ledger**.

```yaml
# the inputs ledger, part of the meeting manifest
inputs:
  kpi.arr:
    value: "12.4M€"
    provided: true
    source: "dashboard-CS / Q3 export"
    provenance: sourced
  kpi.churn_q3:
    provided: false
    provenance: assumed          # filled professionally because material was missing
    value: "~4.2%"
    assumption: "stimato dal trend H1; placeholder — adattare e verificare"
    review_required: true
```

**Render rule.** A binding resolving to `provenance: sourced` renders the value plainly. A binding
resolving to `provenance: assumed` renders the value with a **visible marker** (e.g. `⟨~4.2% — da
verificare⟩`) and emits an entry into the deliverable's **review appendix**.

**Gate `grounding-labeled` (structural, decidable, dependency-free).** It checks: (a) every
binding referenced by a deck-IR resolves to an input in the ledger; (b) every `assumed` input
carries `assumption` + `review_required: true`; (c) the rendered deliverable contains the review
appendix listing every assumed value with its source-to-fill. This honors the maintainer's
requirement — *invent professionally when material is missing, but flag it for adaptation and
review* — without ever fabricating silently.

## 7. Language model (three tiers)

A genuine difference from EADOS, where on-disk artifacts are *always* English. EAMOS separates
three languages:

| Tier | Field | Default | Rule |
|------|-------|---------|------|
| **Interview** | `interview_lang` | maintainer's choice at runtime | the chat with the agent; chosen first, before intake |
| **Output** | `manifest.context.output_lang` | maintainer's choice | the rendered deliverables (a Milan board → `it`); formality/structure norms vary by region |
| **On disk** | — | always English | RFCs, ADRs, AGENTS, archetype profiles, schemas, the deck-IR *structure* (section ids are stable English keys; rendered *text* is `output_lang`) |

`interview_lang` and `output_lang` are independent (an Italian maintainer may prepare an English
board deck). Section *ids* stay English so gates and overlays are language-stable; only rendered
prose is localized.

## 8. Role & authority model (persona ≠ authority)

EAMOS keeps EADOS's separation of **persona** (who the agent is) from **authority** (who may
draft/approve/own what), and the invariant *humans hold every terminal gate*.

- **Persona** — specialized agents under `agent/*.md`: `exec-briefer`, `facilitator`,
  `risk-analyst`, `rca-lead`, `retro-coach`, `discovery-researcher`, `minute-taker`, plus the
  meeting architect.

> **Erratum (2026-07, #65).** As built, the `agent/*.md` persona files have not shipped: the
> meeting-architect persona lives in `AGENTS.md`, and the specialized personas are tracked in the
> ROADMAP backlog. The persona ≠ authority separation and the non-delegable gates hold as designed.
- **Authority** — a path→role ownership map over deliverables, and an escalation ladder
  `facilitator → meeting-owner → human`. The non-delegable gates: `manifest-confirmed`,
  `human-runs-the-room`. The agent **never sends material to real executives** and **never runs a
  live meeting** — it drafts; the human presents and facilitates. A board deck is "published" when
  the human carries it into the room — the meeting analogue of cutting a GitHub Release.

## 9. The persistent series manifest (the moat)

Most enterprise meetings are **recurring** (QBR quarterly, planning biweekly, 1:1 monthly). The
**series manifest** carries forward, across instances: open action items, the decision log, a
rolling risk register, and KPI history. The Q3 QBR opens already knowing what Q2 decided, which
actions are still open, and how the KPIs moved.

> **Honest note.** This is the one major capability EADOS does *not* demonstrate — its manifest is
> single-shot (render once, hand off). The series manifest is **net-new engineering**, not a
> transfer. That is precisely why it is defensible: it is not commodity, and a prompt wrapper
> cannot produce it. It is prioritized early (§15, M4-pulled-forward) because it is both the moat
> and the second-largest technical risk after grounding.

## 10. Quality gates & rubric

Gates are data in `orchestrator/os/gate/`. The rubric ("what 'good' looks like" per
archetype × altitude) is data too, mirroring EADOS's `eval/rubric.md`. Initial gates:
`manifest-confirmed`, `structure-complete`, `grounding-labeled` (§6), `audience-fit` (altitude
shaping respected: slide budget, jargon level, lead-with), `completeness` (every archetype-
required section present), `review-passed`, `human-runs-the-room`, `series-updated`.

> **Erratum (2026-07, #65).** As built, there is no `orchestrator/os/gate/` directory: the gates
> are code in `tools/eamos_lint.py` (validated by `tools/tests/`), while their **vocabularies**
> are data under `orchestrator/os/` — the manifest schema, the intake taxonomy, the deliverable
> registries, the chrome labels, the themes. "Gates as data" is tracked in the ROADMAP backlog.
> The rubric is data as designed (`eval/rubric.yaml`).

## 11. Enterprise lens (confidentiality & regulatory)

Meeting material is among the most sensitive enterprise data: board financials, comp/layoffs (HR),
security incidents (post-mortems), M&A (steering). The posture is designed **from day one**, not
bolted on: explicit stance on *what leaves the machine and to where*, data residency, and
redaction; the "defensive-only + human-gate" culture is the starting point. `regulatory` is a
first-class context field that can switch on mandatory gates (e.g. SOX → `grounding-labeled` is
non-skippable).

## 12. The fork decisions (resolved)

| # | Decision | Resolution |
|---|----------|------------|
| F1 | Implementation stack | **Python, dependency-free** (stdlib), mirroring EADOS; the `pptx`/`docx`/`xlsx` skills are Python, so the IR→binary hop is native. |
| F2 | Repo bootstrap | **Lean skeleton modeled on EADOS** (`.eamos-core/`, hand-built), not a full EADOS factory render — the meeting lifecycle differs enough that a software-delivery scaffold would be pruned. |
| F3 | Reference meeting (the MVP anchor) | **QBR / Business Review @ C-level** — the analogue of `pbr-cpp-memory-pool`: most stable structure, highest willingness-to-pay, stresses grounding immediately. |

## 13. Alternatives rejected

- **Render `.pptx` directly from a skill** — rejected: loses determinism and gate-checkability,
  the property that makes the render trustworthy (§5).
- **A profile per meeting type** — rejected: combinatorial explosion; replaced by archetype +
  overlays (§3).
- **`no-unsourced-numbers` as a hard prohibition** — rejected: undecidable as a structural lint
  over prose, and the maintainer needs professional invention when material is missing; replaced
  by the labeling gate over a typed inputs ledger (§6).
- **Reusing EADOS's `init→…→refactor` lifecycle** — rejected: it is a software lifecycle; the
  meeting lifecycle is genuinely different and is rebuilt (§4).

## 14. Render pipeline (determinism boundary)

```
meeting manifest (axes + inputs ledger)
      │  intake → structure
      ▼
deck-IR  ──────────────────────────  ← gates run HERE (deterministic, structural)
      │  draft (bindings resolved) → review
      ▼
emit_pptx.py / emit_docx.py / emit_md.py   ← pptx/docx/xlsx skills, cosmetic last hop only
      ▼
bundle of materials (output_lang)
```

## 15. Roadmap → milestones

The detailed, living plan is [`ROADMAP.md`](../../../ROADMAP.md) (the analogue of the
`roadmap-covers-rfcs` gate: the roadmap covers this RFC's sections). Summary:

- **M1 — spine + reference meeting (QBR @ C-level), end-to-end.** chat → meeting manifest →
  deck-IR → board deck (PPTX) + pre-read (DOCX) + agenda (MD). Gates: `completeness`,
  `grounding-labeled`. Proves §4–§6 on one meeting.
- **M2 — the archetype grammar.** Generalize to the ~8 archetypes + altitude/function overlays
  (§3).
- **M3 — function packs** (Eng/Product/Sales/HR…): content packs per department.
- **M4 — the series manifest** (carry-forward decisions/actions/risks/KPIs) — the moat (§9).
- **M5 — intake & integrations** (upload deck, paste KPIs, optional Jira/Notion/Sheets).
- **M6 — live facilitation & post-meeting** (live agenda, timeboxing, minute/decision/action
  capture).
- **M7+ — quality gates, rubric, localization, confidentiality hardening** (§11).

## 16. Open questions

1. **Deck-IR fidelity vs. skill freedom.** How rigid is the IR? Too rigid → ugly decks; too loose
   → determinism leaks. M1 must find the line on the reference meeting.
2. **Series identity.** What is the stable key for a recurring series across renames/reorgs?
3. **Redaction model.** Per-deliverable, per-audience redaction — gate or render-time transform?
4. **Skill determinism.** How much of the binary render can be pinned (templates, themes) so two
   runs of the same deck-IR produce visually-stable output?

## Approval

Filled by the approver **after** review (this is the `rfc-approved` gate's record):

```
approved-by: Daniel Polo (@danielPoloWork) (2026-06-28)
```

Reviewers (structured findings addressed): Owner — resolved. Design frozen for M1.

## References

- EADOS `RFC-0001` — the pattern this re-instances.
- ADR-0001 — EAMOS as the second instance of the EADOS pattern.
- `orchestrator/os/` — the machine-readable specs this RFC elaborates.
- `ROADMAP.md` — the plan that covers this RFC.
