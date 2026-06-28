# ADR-0001: EAMOS is the second instance of the EADOS pattern

- **Status:** Accepted
- **Date:** 2026-06-28
- **Deciders:** Owner (`@danielPoloWork`), Enterprise Project Architect
- **Related:** [RFC-0001](../rfc/0001-eamos-meeting-os.md), EADOS `RFC-0001`

## Context

The owner runs an enterprise agentic-OS family. EADOS proved a reusable pattern in the domain of
governed software repositories: *interview → manifest → profiles → templates → render → gate →
roles*, all schema-first, with the principle **knowledge is data, not code**, a reference-based
manifest as state, deterministic routing, and humans holding every terminal gate.

We want a system that prepares, facilitates, and follows up enterprise meetings for any company,
department, audience altitude, and output language. The question is whether to design it from
scratch or to **re-instance** the EADOS pattern in the new domain.

## Decision

**EAMOS is built as the second instance of the EADOS pattern, not a fork and not a from-scratch
design.** We reuse the *spine* (schema-first data + mechanical gates, persistent manifest,
authority ≠ persona, human-terminated gates, reference-first delivery discipline) and build a new
*body* for the meeting domain:

- meeting **archetypes** (data) instead of language profiles;
- a deterministic **deck-IR** as the render target instead of a source tree;
- a **meeting lifecycle** state machine instead of the software lifecycle;
- a **three-tier language model** (interview / output / English-on-disk);
- a **grounding-by-labeling** model over a typed inputs ledger;
- a **persistent series manifest** for recurring meetings (net-new vs. EADOS).

The implementation stack is **Python, dependency-free** (mirroring EADOS), the repo is a **lean
skeleton modeled on EADOS** under `.eamos-core/`, and the MVP anchor is one reference meeting,
**QBR @ C-level** (the analogue of `pbr-cpp-memory-pool`).

## Consequences

**Easier.** Family coherence (a maintainer who knows EADOS knows EAMOS); the schema-first + lint
discipline ports directly; the EADOS renderer and the reference-first milestone discipline are
proven assets.

**Harder.** The meeting lifecycle, the deck-IR, the grounding model, and the series manifest are
net-new and must be built — "reuse the spine" is not "reuse the code". The deck-IR adds an
indirection (manifest → IR → binary) that the team must hold to in order to keep the render
deterministic.

**Watch.** EADOS and EAMOS sit side by side in the same parent directory and differ by one letter
(`pgs-eados` / `pgs-eamos`); the one-letter acronym collision is a known daily operational tax
(see RFC-0001). Revisit a distinct product name before any go-to-market.

## EADOS-pattern claims this ADR relies on (verified against `pgs-eaao`)

- The canonical five-step loop — EADOS `AGENTS.md` §5.
- "Knowledge is data, not code" — EADOS `orchestrator/os/README.md`.
- "Human holds the terminal gate" — same.
- `roadmap-covers-rfcs` gate — EADOS `orchestrator/os/plan/plan.yaml`.
- Authority/persona separation + escalation ladder — EADOS `orchestrator/os/authority/authority.yaml`.
