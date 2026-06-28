# RFC-0002: The deliverable catalogue & IR families

- **Status:** Accepted (2026-06-28). **Frozen for M1**; open questions resolved (§11).
- **Date:** 2026-06-28
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** [RFC-0001](0001-eamos-meeting-os.md) §5 (deck-IR), §6 (grounding), §10 (gates);
  this RFC generalizes the single deck-IR into a family of IRs and adds the deliverable registry.

> **How to read this.** RFC-0001 defined *one* deterministic render target (the deck-IR). The
> maintainer's deliverable set is wider — presentations (two modes), mind maps, reports,
> infographics, tables/charts, interview quizzes, plus source reorganization and facilitation
> documents. This RFC shows that the whole set is **one model — author once, project to many** —
> and never a special case in code. Adding a deliverable type is editing a validated YAML file.

---

## 0. Summary

A meeting produces a **bundle** of deliverables. Each deliverable is a **projection** of the same
grounded content into one of six **IR families**, parameterized by **validated enums**. The
content is authored once (archetype structure + the typed inputs ledger of RFC-0001 §6); every
projection binds the *same* ledger, so a value cannot diverge between the deck and the report. The
grounding-by-labeling rule (RFC-0001 §6) applies unchanged across all families. Deliverable types
live in a data **registry**; their parameters are bounded by `archetype × altitude` so the
enterprise posture is not undermined by "creative" options; the free-text **intent** field shapes
form and emphasis only — never facts.

## 1. Context & problem

RFC-0001 §5 modeled a single `deliverable: decision_deck` with one deck-IR. The maintainer
requires, on demand: (1) presentations in two formats — **detailed** (full text, read-alone /
email) and **speaker** (clean, key points) — with a length parameter; (2) mind maps; (3) reports;
(4) infographics with orientation / visual-style / detail-level parameters; (5) tables & charts;
(6) interview quizzes generated from sources. Plus: a function that **reorganizes the sources**,
and **facilitation documents** (a step-by-step "how to run the meeting and what to say", and the
agenda / scaletta).

The trap is to build six generators. That re-introduces the combinatorial explosion RFC-0001 §3
eliminated, one layer down (render instead of structure).

## 2. The unifying model — author once, project to many

```
inputs ledger (RFC-0001 §6, sourced + assumed)         archetype × overlays (RFC-0001 §3)
                    └──────────────┬───────────────────────────────┘
                                   ▼
                       grounded meeting content
                                   │
        ┌──────────┬──────────┬────┴─────┬───────────┬──────────┐
        ▼          ▼          ▼          ▼           ▼          ▼
     slide-IR    doc-IR    graph-IR  infographic-  data-IR    quiz-IR
                                        IR
        │          │          │          │           │          │
     emit_pptx  emit_docx  emit_svg   emit_svg    emit_xlsx  emit_docx
        ▼          ▼          ▼          ▼           ▼          ▼
   deck (2 modes) report/   mind map  infographic  table+     interview
                  guide/                            chart      quiz
                  agenda/
                  minutes
```

Authoring is grounded once; each projection is a deterministic transform of that content. **One
ledger feeds all projections** — the strongest possible grounding guarantee: the same number
renders identically in the deck, the report, and the infographic because all three bind the same
cell.

## 3. IR families

The deck-IR of RFC-0001 §5 is now **slide-IR**, one of six. All IRs are deterministic, text-based,
gate-checkable; the per-format emitter (driving a `pptx`/`docx`/`xlsx` skill or emitting SVG) is
the cosmetic last hop.

| IR family | Content shape | Emitter → target |
|-----------|---------------|------------------|
| **slide-IR** | sections → slides → blocks (heading/bullet/metric/figure) | `emit_pptx` → PPTX |
| **doc-IR** | sections → prose/list/table blocks | `emit_docx` / `emit_md` → DOCX/MD |
| **graph-IR** | nodes + edges (typed, hierarchical) | `emit_svg` → SVG (mind map) |
| **infographic-IR** | a layout grid of stat/figure/callout cells | `emit_svg` → SVG |
| **data-IR** | typed tables + chart specs (binding into the ledger) | `emit_xlsx` → XLSX + charts |
| **quiz-IR** | questions + answer keys, each bound to a ledger source | `emit_docx` / `emit_md` |

SVG targets (mind map, infographic) are *more* deterministic than PPTX — SVG is text, rendered by
substitution. The determinism boundary (RFC-0001 §14) holds: gates run on the IR, never on the
binary.

## 4. The deliverable registry (data)

Each deliverable type is a file `orchestrator/os/deliverables/<type>.yaml` validated by the lint.
It declares: the IR family it projects to, its parameters (each an enum or free field), and its
grounding policy. The registry, not code, defines what can be produced.

```yaml
# deliverables/presentation.yaml
type: presentation
ir_family: slide-IR
params:
  format:   { enum: [detailed, speaker], default: speaker }   # detailed = read-alone/email; speaker = key points
  length:   { enum: [short, medium, long], default: medium }
  sources:  { kind: ledger_ref, multiple: true }              # binds the inputs ledger (RFC-0001 §6)
  intent:   { kind: free_text }                               # "audience, style, topic" — shapes form, not facts (§7)
emitter: emit_pptx
```

```yaml
# deliverables/infographic.yaml
type: infographic
ir_family: infographic-IR
params:
  orientation:  { enum: [landscape, portrait, square], default: portrait }
  visual_style: { enum: [didactic, bento, bricks, scientific, professional], default: professional }
  detail:       { enum: [concise, standard, detailed], default: standard }
  sources:      { kind: ledger_ref, multiple: true }
  intent:       { kind: free_text }                           # "blue theme, highlight 3 key stats"
emitter: emit_svg
```

The other registry entries (`mindmap`, `report`, `table_chart`, `interview_quiz`,
`facilitation_script`, `agenda`, `minutes`) follow the same shape. The UI affordances the
maintainer listed become **validated enums in data** — the lint rejects a requested value outside
the declared set, which is exactly the EADOS strength applied to render options.

## 5. Parameters bounded by archetype × altitude (the enterprise guardrail)

Free parameters would let a board QBR render as a "playful bricks" infographic — wrong. So
`archetype × altitude` imposes **bounds** on admissible parameter values, as an overlay:

```yaml
# overlay fragment: review @ c-level
deliverable_bounds:
  infographic:
    visual_style: { allow: [professional, scientific] }   # forbids didactic/bento/bricks
    detail:       { allow: [concise, standard] }
  presentation:
    length:       { allow: [short, medium] }               # a board does not read "long"
```

The `intent` field may choose *within* the bounds; it can never exceed them. Gate
`deliverable-params-in-bounds` (structural) enforces this.

## 6. Source reorganization (the ingestion primitive)

"Reorganize the sources" is not a deliverable — it is how material **enters** the inputs ledger,
and it is foundational (everything binds the ledger). The primitive: ingest provided material
(uploaded deck, pasted KPIs, notes, prior minutes) → normalize into the typed ledger — dedupe,
tag, group by topic / author / date, mark each cell `sourced`. Missing-but-needed cells are
created as `assumed` placeholders (RFC-0001 §6). The reorganized ledger is the single substrate
every projection (§2) reads. (This is the foundational half of RFC-0001 §15-M5; the connectors are
the later half.)

## 7. Grounding across projections (the invariant)

The grounding-by-labeling rule (RFC-0001 §6) is **family-agnostic** and applies to every
projection:

- Every factual/quantitative element in any IR is a **binding** into the ledger — never inline
  prose. An infographic's "3 key stats" are three bindings; a quiz's answers cite the ledger
  source they test; a table's cells bind ledger cells.
- A binding to an `assumed` cell renders **labeled** and emits a review-appendix entry.
- The **intent** field shapes form, emphasis, theme, tone — **never facts**. "Highlight the 3 key
  statistics" selects which sourced bindings to feature; it cannot author a statistic. Gate
  `grounding-labeled` runs on every IR, not just the deck.

## 8. Facilitation deliverables

The "how to run the meeting and what to say" guide and the scaletta are first-class **doc-IR**
deliverables tied to the `facilitate` phase (RFC-0001 §4):

- `facilitation_script` — per agenda item: objective, talking points (grounded), the decision/ask,
  anticipated questions, time box. The "what to say" support.
- `agenda` — the timeboxed scaletta of topics, owners, and durations.
- `minutes` — produced in `follow-up`, feeding the series manifest (RFC-0001 §9).

These are non-delegable at runtime in the sense of RFC-0001 §8: EAMOS *drafts* the script; the
human *speaks* it.

## 9. Roadmap impact

- **M1** ships **slide-IR + doc-IR** (board deck in both modes, pre-read, agenda) on the reference
  meeting — unchanged scope, now named as IR families.
- A new **M2b — deliverable families** adds `graph-IR`, `infographic-IR`, `data-IR`, `quiz-IR`,
  their emitters, the deliverable registry, and `deliverable-params-in-bounds`. Slotted after the
  archetype grammar (M2) so bounds-by-altitude exists first.
- **M5** absorbs the source-reorganization primitive as its foundational half.

See [`ROADMAP.md`](../../../ROADMAP.md).

## 10. Alternatives rejected

- **Six bespoke generators** — rejected: re-introduces combinatorial explosion at the render layer;
  replaced by IR families + a data registry (§2–§4).
- **Free-form style parameters** — rejected: lets creative options undermine the enterprise
  posture; replaced by enums bounded by archetype × altitude (§5).
- **Per-deliverable independent content authoring** — rejected: lets the same number diverge
  between deliverables; replaced by author-once-project-many over one ledger (§2, §7).
- **Treating "reorganize sources" as a deliverable** — rejected: it is the ingestion primitive
  feeding the ledger, not an output (§6).

## 11. Resolved decisions

1. **Infographic layout — canonical templates, not free composition.** The `infographic-IR`
   renders into one of **6–8 canonical, deterministic layout templates** (per orientation × a
   small set of compositions); the generative skill touches *content only*, never the layout. This
   keeps the render reproducible and answers the determinism-leak risk by construction. `visual_style`
   selects a pinned theme over the chosen template.
2. **data-IR chart types — four first-class, rest as plugins.** First-class chart specs:
   **Line, Bar, Stacked Bar, Variance/Bullet** — they cover >80% of enterprise meeting cases. Others
   (Scatter, Sankey, Radar, Heatmap, …) arrive later as **plugins**, not in the M-series core.
3. **Quiz — graded vs. discussion.** Two question kinds: **graded** (citation into the ledger
   *required* — preserves traceability where it matters) and **discussion** (citation optional but
   recommended, rendered as un-scored — keeps open didactic cases). The `grounding-labeled` gate
   enforces the citation requirement on `graded` questions only.

## Approval

```
approved-by: Daniel Polo (@danielPoloWork) (2026-06-28)
```

Reviewers (structured findings addressed): Owner — resolved. Design frozen for M1.

## References

- RFC-0001 §5 (deck-IR → generalized here), §6 (grounding), §10 (gates), §14 (determinism boundary).
- `orchestrator/os/deliverables/` — the registry this RFC defines.
