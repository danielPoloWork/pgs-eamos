# Contributing to EAMOS

EAMOS is **owner-governed**: anyone — a human collaborator or an AI agent — may *propose* changes,
but only the owner (`@danielPoloWork`) decides what lands on `main`. The full agent contract is
[`AGENTS.md`](AGENTS.md); the machine-readable policy is
[`.eamos-core/orchestrator/os/git/git.yaml`](.eamos-core/orchestrator/os/git/git.yaml).

## The flow

| Step | Who |
|------|-----|
| Create a feature branch `<type>/<short-kebab>`; stage, commit (Conventional Commits), push | Agent / contributor |
| **Draft** a pull request (filled template, metadata set) | Agent / contributor |
| Review, request changes, **open / mark ready**, **squash-merge** | **Owner** |

Never push to `main`. One logical change per PR; one PR at a time.

## Every PR must be exhaustive

This is the bar (mirrors EADOS). A PR is not ready to review until:

- **Assignee** set (`@me`).
- **Exactly one type label** (`documentation`, `enhancement`, `bug`, …).
- **Milestone** assigned (the `Mx` it belongs to).
- **Body** uses [the template](.github/PULL_REQUEST_TEMPLATE.md) and **crosslinks its RFC and its
  milestone item** (the `required_crosslinks` policy).
- **Verification** section ticked: `eamos_lint` green on the reference manifest, render-smoke
  deterministic (two renders byte-identical), `py_compile` clean.

## Commits

Conventional Commits with a scope from `git.yaml` (e.g. `feat(render):`, `docs(rfc):`,
`feat(deck-ir):`). Co-author trailers welcome.

## Design before code

A feature is preceded by an RFC under `.eamos-core/docs/rfc/`; a non-trivial decision is recorded
as an ADR under `.eamos-core/docs/adr/`. On-disk artifacts are English (RFC-0001 §7).
