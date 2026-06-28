# EAMOS — Enterprise Agentic Meeting OS

*The briefing & facilitation factory.*

[![CI](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml/badge.svg)](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg)](https://www.conventionalcommits.org/)
[![status: pre-1.0](https://img.shields.io/badge/status-pre--1.0-orange.svg)](ROADMAP.md)
[![grounding: labeled, never fabricated](https://img.shields.io/badge/grounding-labeled%2C%20never%20fabricated-success.svg)](.eamos-core/docs/rfc/0001-eamos-meeting-os.md)

> **🌐 Translations:** [简体中文](.eamos-core/docs/i18n/zh-Hans/README.md) · [日本語](.eamos-core/docs/i18n/ja/README.md)
> — derived from this English source (the source of truth). Policy & freshness:
> [`.eamos-core/docs/i18n/`](.eamos-core/docs/i18n/README.md).

EAMOS turns a maintainer's inputs into the **material and the regie** for an enterprise meeting —
pre-read, deck, facilitation script, minutes, decision and action log — for any company size,
department, audience altitude, and output language.

It is the **second instance of the EADOS pattern**: the same machine (interview → manifest →
profiles → templates → render → gate → roles), re-targeted to a different class of output. Where
EADOS renders governed *repositories*, EAMOS renders meeting *bundles*. The principle is the same:
**knowledge is data, not code** — adding a meeting archetype, an audience altitude, a function pack,
or a gate is editing a validated YAML file, never a special case in code.

## What it is (and is not)

- **It frames, structures, and synthesizes** input you provide. It **does not fabricate.** When
  material is missing, it may fill the gap professionally — but the value is rendered **labeled**
  (`⟨… — da verificare⟩`) and collected into a "verify before the room" appendix. You adapt and
  review; the machine never invents silently.
- **The agent drafts; the human presents and facilitates.** EAMOS never sends material to real
  executives and never runs a live meeting. A board deck is "published" when you carry it into the
  room.
- **Not a BI tool.** EAMOS consumes the numbers you provide or paste; it does not own them.

## How it works

A small composable grammar (RFC §3), not a catalogue of meeting types:

| Axis | Examples |
|------|----------|
| **Archetype** (deep structure, ~8) | decision/steering · review/status · planning · discovery · post-mortem · retrospective · alignment · 1:1 |
| **Audience altitude** | board/c-level → vp/director → manager/lead → ic |
| **Function** | Eng · Product · Sales · Marketing · CS · HR · Finance · R&D · Ops |
| **Company context** | size · sector · regulatory (SOX/GDPR/HIPAA) · framework (SAFe/Scrum) · formality · **output language** |

A QBR is not a type — it is `review @ c-level × finance × {context}`. The render path is
**deterministic**: the meeting manifest renders into a typed **deck-IR**, gates run on the IR, and
the `pptx`/`docx`/`xlsx` skills are only the cosmetic last hop (RFC §5).

## The moat

Most enterprise meetings recur. The **persistent series manifest** carries forward open actions, the
decision log, a rolling risk register, and KPI history — so the Q3 QBR opens already knowing what Q2
decided and how the KPIs moved. A prompt wrapper cannot do this.

## Install (consumer)

Drop the EAMOS machine into a repo from a published release — **download + placement only**, not the
agent init:

```sh
# macOS / Linux
curl -fsSL https://github.com/danielPoloWork/pgs-eamos/releases/latest/download/setup.sh | sh
```
```powershell
# Windows (PowerShell)
irm https://github.com/danielPoloWork/pgs-eamos/releases/latest/download/setup.ps1 | iex
```

Or download `setup.sh` / `setup.ps1` and run with flags (`--help` — new-vs-existing repo, path, ref).
The installer **verifies the bundle's SHA256** (fail-closed) and extracts it **additively** (never
overwrites). Double-click `setup.command` (macOS) or `setup.bat` (Windows).

> Needs a published GitHub release. The repo is **private until GTM** — until then, build a bundle
> locally (`git archive --format=tar.gz -o bundle.tar.gz HEAD`) and install with
> `sh setup/setup.sh --from bundle.tar.gz`.

## Status

Early. The design of record is [RFC-0001](.eamos-core/docs/rfc/0001-eamos-meeting-os.md) and
[RFC-0002](.eamos-core/docs/rfc/0002-deliverable-catalogue-and-ir-families.md); the plan is
[ROADMAP.md](ROADMAP.md). **M1** (the QBR @ C-level reference) renders end-to-end and
deterministically — manifest → deck-IR → Markdown deck + `.pptx` board deck, gates green;
**M2** (the composable archetype grammar) is in progress.

## Repository

The full agent contract is [AGENTS.md](AGENTS.md). All factory machinery lives under
`.eamos-core/` — a consumer ignores it with a single line. How to contribute (and the exhaustive-PR
bar): [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

- **Owner & maintainer:** Daniel Polo ([@danielPoloWork](https://github.com/danielPoloWork)).
- **Architecture:** the second instance of the **EADOS** pattern — schema-first data, mechanical
  gates, a persistent manifest, and a human-held terminal gate.
- **Built with** [Anthropic Claude](https://www.anthropic.com/claude) / Claude Code. The cosmetic
  `.pptx` hop uses [python-pptx](https://python-pptx.readthedocs.io/) — optional, outside the
  dependency-free core.

## License & ownership

MIT — see [LICENSE](LICENSE). © 2026 Daniel Polo. EAMOS is **owner-governed**: anyone may *propose*
changes, only the owner lands them on `main`.
