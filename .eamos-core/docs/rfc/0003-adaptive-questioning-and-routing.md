# RFC-0003: Adaptive questioning & intelligent routing (Phase C)

- **Status:** Proposed (2026-06-29) — awaiting owner ratification. **Design-before-code** (AGENTS §7).
- **Date:** 2026-06-29
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** [RFC-0001](0001-eamos-meeting-os.md) §6 (grounding), §8 (human-runs-the-room), §3 (axes);
  classification taxonomy ([`os/intake/classification.yaml`](../../orchestrator/os/intake/classification.yaml), #27);
  the L0/L1/L2 capture layer (`discovery_intake`, #29); the discovery-decision timebox (#32).
  Tracks issue #28 under the Solution-Discovery epic (#21).

> **How to read this.** #27 decides *what kind of problem this is* (cluster × complexity ×
> decision-risk). #29 captures *the answers* (intent / domain / constraints). This RFC designs the
> **bridge** between them — the **branching question tree** that decides *which questions to ask, and
> how deep to go*, driven by the classification. It is the framework's Phase C, the "cuore", and the
> single largest gap: today it exists only as a soft agent rule (AGENTS §5.1), not as encoded data.

---

## 0. Summary

A **branching question tree as data** plus a **routing table as data**, both under `os/intake/`.
The classification (#27) selects a **depth** and a set of **layers**; within that envelope the agent
reveals questions **level by level** — *each answer opens only the next needed level*, never the
whole tree up front. The tree is keyed by problem cluster; routing maps `complexity` (and escalation
rules over `cluster × decision_risk`) to the deepest level asked. A deterministic **selector**
(`tools/intake.py questions`) turns `(classification, tree, routing)` into the ordered questions for
the room. The agent *selects* questions; the **human answers** (the answers populate
`discovery_intake`); nothing is fabricated. This is grounding (RFC-0001 §6) and human-runs-the-room
(§8) applied to intake: data-driven, deterministic, gate-checkable.

## 1. Context & problem

The framework is L0/L1/L2 intake → **B classify** → **C question/route** → D normalize → E options →
F score → G decide. EAMOS now has B (#27) and the capture schema for A (#29), F (#23), E (#30), G
(#31), and the conduct slot for C (the "targeted questions" phase of the #32 timebox). What is
missing is C itself: the logic that, given a classification, asks *the right questions to the right
depth*. Encoding it as a generator or a prompt would re-introduce the very thing EAMOS factored out
— behavior in code instead of data. It must be **data + a deterministic selector**, like every other
axis (RFC-0001 §3, §13).

## 2. The model — tree + routing as data

```
classification (#27)            question tree (cluster -> leveled questions)
 cluster/complexity/risk ──┐         │
                           ▼         ▼
                    routing table ──> selector (tools/intake.py questions)
                           │              │  deterministic: (classification, tree, routing) -> questions
                           ▼              ▼
                    depth + layers   ordered questions for the room  ──(human answers)──> discovery_intake (#29)
```

### 2.1 Question tree (`os/intake/questions.yaml`)

```yaml
levels: [surface, deeper, architecture]   # the depth ladder; routing caps the deepest level asked
common:                                   # asked for every cluster (ties to discovery_intake L0/L1)
  - { id: intent,       level: surface, ask: "Which capability is sought (not the tool)?" }
  - { id: current_pain, level: surface, ask: "Where does it hurt today?" }
clusters:
  system_replacement:
    - { id: not_scale,      level: surface,      ask: "What no longer scales?" }
    - { id: missing,        level: deeper,       ask: "Which features are missing?" }
    - { id: why_not_extend, level: deeper,       ask: "Why not extend the existing system?" }
    - { id: integrations,   level: architecture, ask: "Which systems must it keep talking to?" }
  integration:
    - { id: which_systems,  level: surface,      ask: "Which systems must talk?" }
    - { id: data_flows,     level: deeper,       ask: "What data flows between them?" }
    - { id: realtime,       level: architecture, ask: "Real-time or batch?" }
  process_optimization:
    - { id: where_breaks,   level: surface,      ask: "Where does the process break?" }
    - { id: how_manual,     level: deeper,       ask: "How manual is it today?" }
    - { id: touches,        level: deeper,       ask: "Which systems does it touch?" }
  # ... data_platform, workflow_automation, compliance_regulatory (authored the same way)
```

- **Levels encode depth.** `surface` is always asked; `deeper`/`architecture` are gated by routing.
- **Progressive disclosure.** The selector emits questions ordered by level; the agent asks a level,
  captures answers, then asks the next routed level — never the whole tree at once.
- **English on disk** (RFC-0001 §7); `ask` prose is localized at the point of use (interview_lang),
  not stored localized — these are stable ids.

### 2.2 Routing table (`os/intake/routing.yaml`)

```yaml
by_complexity:                       # the base depth from the classification's complexity
  low:  surface
  med:  deeper
  high: architecture                 # the deep-architecture layer
escalate_to_architecture:            # force architecture even below `high` complexity
  - { cluster: integration,        decision_risk: high }   # core-business + high integration
  - { cluster: system_replacement, decision_risk: high }
  - { cluster: compliance_regulatory, decision_risk: high }
```

- **Low impact/complexity skips the deep-architecture layer; core-business + high integration
  activates it** — exactly the issue's rule, now as data. The escalation list is the only
  cross-dimension coupling; everything else is the `complexity → level` ladder.

### 2.3 The selector (`tools/intake.py questions`)

A pure function `(classification, tree, routing) → [questions]`: resolve the deepest level (the
`by_complexity` base, raised to `architecture` if an `escalate_*` rule matches), then return
`common` + the cluster's questions whose `level ≤ that depth`, in level order. Deterministic (sorted,
no clocks/IO/randomness), so the same classification yields the same interview every time. Exposed as
a new op on the existing intake tool (the intake home), printing a paste-ready question list for the
#32 "targeted questions" phase.

## 3. Discipline (non-negotiable)

- **The agent selects; the human answers.** The selector chooses *which* questions; the maintainer
  answers them; answers are hand-entered into `discovery_intake` (#29). The agent never fabricates an
  answer — grounding (RFC-0001 §6) and human-runs-the-room (§8) applied to intake.
- **Data, not code.** No per-cluster branch in a tool; the tree and routing are validated YAML.
  Authoring a new cluster's branch is editing `questions.yaml`, never a renderer/selector change.
- **Deterministic & reproducible.** Same classification → same selected questions.

## 4. Gate

`questions-valid` (structural, decidable): every `clusters:` key is a taxonomy cluster (#27); every
question has `id` + `ask` + a `level ∈ levels`; every routing value is a valid `level`, and every
`escalate_*` rule references taxonomy-valid `cluster`/`decision_risk`. Mirrors `classification-valid`:
the tree cannot drift from the taxonomy.

## 5. What ships after ratification (the implementation PR)

1. `os/intake/questions.yaml` — the tree (all six clusters + `common`).
2. `os/intake/routing.yaml` — the routing table.
3. `tools/intake.py questions` — the deterministic selector op.
4. `eamos_lint.py` — the `questions-valid` gate.
5. A reference: `vendor-prework` (classified `system_replacement / high / high`) → the selector
   returns the **architecture-depth** question set; a low-complexity manifest returns only `surface`.
6. Tests — selection depth per classification; escalation rules; gate teeth; determinism.

## 6. Alternatives considered

- **A prompt/LLM that "asks good questions".** Rejected: non-deterministic, ungated, behavior-in-code
  — the anti-pattern RFC-0001 §13 exists to prevent. The tree is the deterministic substitute.
- **A full matrix `(cluster × complexity × decision_risk) → depth`.** Rejected as over-specified:
  27 cells to author and maintain. The `complexity → level` ladder + a short escalation list captures
  the same intent with far less surface and is easier to reason about.
- **A free decision-graph (arbitrary per-answer branching).** Deferred: `depends_on`/`opens`
  answer-gated follow-ups can be added later if a cluster needs them; the leveled tree covers the
  issue's examples without it.

## 7. Out of scope

Pattern matching over past cases and what-if simulation are the **advanced variant (#33, deferred)**.
Automatic (ML) inference of the classification is out: the classification is a human/agent judgment
validated by `classification-valid` (#27); this RFC consumes it, it does not infer it.

## 8. Open questions

1. **Answer-gated follow-ups (`opens`/`depends_on`)** — include in v1 or defer to a later RFC? This
   draft defers them (the leveled tree suffices for the issue's examples).
2. **Selector home** — a new op on `tools/intake.py` (proposed) vs a standalone `tools/intake_questions.py`.
3. **Localization of `ask`** — localize at print time from a per-language table, or keep English and
   let the agent translate in the room? (Leaning: English ids on disk, agent localizes in interview_lang.)
