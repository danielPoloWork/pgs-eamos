# RFC-0004: A 7th IR family — the topology / target-architecture diagram

- **Status:** Proposed (2026-06-29) — awaiting owner ratification. **Design-before-code** (AGENTS §7).
- **Date:** 2026-06-29
- **Author:** Enterprise Project Architect (tech-lead role)
- **Reviewers:** Owner (`@danielPoloWork`)
- **Approver:** Owner
- **Related:** **Extends [RFC-0002](0002-deliverable-catalogue-and-ir-families.md)** §3 (IR families),
  §4 (registry), §5 (params-in-bounds), §7 (no divergence); [RFC-0001](0001-eamos-meeting-os.md) §6
  (grounding), §13 (no renderer special-casing). Tracks issue #22; consumed by the vendor-selection
  recipe (#24).

> **How to read this.** RFC-0002 defined **six** IR families (slide · doc · graph · infographic ·
> data · quiz). The enterprise-architect deliverable for a build-vs-buy meeting — the **target
> architecture diagram** (boxes-and-arrows: systems + integration flows) — fits none of them. A mind
> map is the closest and it is the wrong shape: it has untyped nodes and no typed edges. This RFC adds
> the **7th family**, `topology-IR`, the same way RFC-0002 added the others: author once, project
> deterministically, gate on the IR, emit via an existing cosmetic hop. No renderer special case.

---

## 0. Summary

A **7th IR family — `topology-IR`** — projects a typed inputs ledger into a **system topology**:
**typed nodes** (systems) and **typed edges** (integration patterns). It is a deterministic
projection like every other family (RFC-0002 §2): nodes/edges bind the same ledger, so a system or an
integration cannot diverge from what the deck or the data-IR says (§7). Grounding is unchanged
(RFC-0001 §6): a node/edge sourced from material renders plain; an **assumed** one renders flagged
(amber) and its key lands in the review appendix. It is emitted through the **existing `emit_svg`**
hop (a third deterministic SVG layout, beside the mind map and the infographic), validated by a new
`topology-valid` gate. Node kinds and edge patterns are **validated enums** (RFC-0002 §5 discipline),
so the diagram's vocabulary cannot drift.

## 1. Context & problem

A real build-vs-buy / vendor-selection meeting needs a *target architecture diagram*: the systems
(ERP / PLM / CAD / SSO / AD / the new platform / the vendor) and the integration flows between them
(REST, event-driven, batch), with data-residency and ownership visible. `emit_svg` today projects
only `graph-IR` (mind map) and `infographic-IR`; neither models a graph with **typed nodes** and
**typed edges**. Forcing it into a mind map loses the types and the directed integration semantics.
Building a one-off diagram generator would re-introduce behavior-in-code (RFC-0001 §13). The answer is
the RFC-0002 pattern, applied once more.

## 2. The model — author once, project to a topology

```
inputs ledger (systems as cells, sourced/assumed)        manifest `topology:` (nodes + edges)
                    └──────────────┬──────────────────────────────┘
                                   ▼
                          build_topology_ir (render.py)   ── deterministic, grounded
                                   │
                                   ▼
                              topology-IR  ── nodes[] (typed) + edges[] (typed) + review_appendix
                                   │
                                   ▼
                              emit_svg  ── a 3rd canonical SVG layout (deterministic, dependency-free)
```

### 2.1 The manifest `topology:` block

A top-level structured block (like `scorecard:`, #23). Nodes bind the ledger; edges connect node ids
with a validated pattern.

```yaml
topology:
  nodes:
    - { id: platform, label: sys.platform, kind: app }       # `label` is a ledger key (grounded)
    - { id: erp,      label: sys.erp,      kind: erp }
    - { id: sso,      label: sys.sso,      kind: sso }
    - { id: vendorx,  label: sys.vendorx,  kind: external }
  edges:
    - { from: platform, to: erp,     pattern: rest }
    - { from: platform, to: sso,     pattern: rest }
    - { from: platform, to: vendorx, pattern: event }        # an edge may bind a cell / be assumed
```

- **Nodes are grounded.** `label` is a ledger key; a `sourced` cell renders plain, an `assumed` cell
  renders flagged + into the appendix (RFC-0001 §6) — exactly like every other IR.
- **Edges are typed.** `pattern` is a validated enum; an edge may carry an optional `label`/binding or
  an `assumed: true` flag for an integration that is proposed but not confirmed.

### 2.2 The topology-IR (the determinism boundary)

```yaml
deliverable: architecture
output_lang: <iso>
title: <objective>
nodes:
  - { id: <str>, label: <resolved str>, kind: <enum>, assumed: <bool> }
edges:
  - { from: <id>, to: <id>, pattern: <enum>, label: <resolved str?>, assumed: <bool> }
review_appendix: [ { binding, value, assumption, fill_from }, ... ]   # sorted by key
```

Deterministic serialization (JSON, insertion order, appendix sorted by key) — same manifest → same
IR → same SVG bytes (RFC-0002 §3).

### 2.3 The registry entry + vocabularies

A new deliverable type `architecture` in `os/deliverables/architecture.yaml` (RFC-0002 §4): `ir_family:
topology-IR`, `emitter: emit_svg`, layout params as validated enums (e.g. `layout: [layered, hub]`),
and the content **vocabularies**:

```yaml
vocab:
  node_kind:    [app, erp, plm, cad, sso, ad, data_store, external]
  edge_pattern: [rest, event, batch, file]
```

### 2.4 emit_svg — a third deterministic layout

`emit_svg` gains a topology layout beside the mind map and infographic. **Deterministic placement**:
node positions are a pure function of declaration order (a canonical layered/hub grid — no
force-directed, no randomness, no clocks), so the render is reproducible (RFC-0002 §11-1). Edges are
drawn as directed connectors labeled with their pattern; assumed nodes/edges are amber (the grounding
signal, RFC-0001 §6); a footer lists the count to verify. Stays dependency-free (SVG is text).

## 3. Gate

`topology-valid` (structural, decidable): every edge `from`/`to` references a declared node id; every
`kind`/`pattern` is in the registry vocabulary; every node `label` resolves to a ledger cell (an
assumed one must be labeled + in the appendix, via the existing grounding gate). Mirrors
`classification-valid` / `questions-valid`: the diagram cannot reference an undeclared system or an
out-of-vocabulary pattern.

## 4. No divergence (RFC-0002 §7)

Because nodes bind the **same ledger** the deck and the data-IR bind, a system's name or a cost
attached to it cannot differ between the architecture diagram and the scorecard. The topology-IR is a
peer projection, not a parallel source of truth.

## 5. What ships after ratification (the implementation PR)

1. `os/deliverables/architecture.yaml` — the registry entry + vocabularies.
2. `render.py` — `build_topology_ir(manifest, …)` (grounded, deterministic) + `--ir topology`.
3. `emit_svg.py` — the topology layout (deterministic, dependency-free).
4. `eamos_lint.py` — the `topology-valid` gate.
5. A reference: a `topology:` block on `vendor-prework` (platform ↔ ERP/SSO/vendor), gate-green; one
   assumed node to exercise the appendix.
6. Tests — determinism (byte-identical SVG); grounding (assumed node flagged + in appendix); gate
   teeth (edge to an undeclared node; out-of-vocab pattern).

## 6. Alternatives considered

- **Reuse `graph-IR` (mind map).** Rejected: untyped nodes, undirected/untyped edges — it cannot carry
  system kinds or integration patterns. Wrong shape, as the issue notes.
- **A Graphviz/mermaid dependency.** Rejected: breaks dependency-free (AGENTS §9) and determinism
  (layout engines reorder). A small canonical SVG layout keeps both.
- **A free node-placement (x/y in the manifest).** Rejected: placement is presentation, not content;
  the maintainer authors *what connects to what*, the layout is derived deterministically.

## 7. Out of scope

Auto-discovery of the topology from logs/CMDB; interactive/zoomable diagrams; layout beyond the
canonical templates (the generative layer touches content only, RFC-0002 §11-1). Multiple diagrams
per meeting can come later; v1 is one topology per manifest.

## 8. Open questions

1. **Edge grounding** — must every edge bind a ledger cell, or is a bare `{from,to,pattern}` (with an
   optional `assumed: true`) enough? (Draft: nodes bind cells; edges optional — an integration is
   often a design statement, not a sourced figure.)
2. **Layout set** — ship one layout (`layered`) in v1 and add `hub` later, or both at once? (Draft:
   one — `layered` — to keep the first cut small.)
3. **Naming** — `architecture` (deliverable type) + `topology-IR` (family), or unify on one term?
   (Draft: `architecture` deliverable → `topology-IR`, mirroring `table_chart` → `data-IR`.)
