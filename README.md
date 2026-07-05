# EAMOS — Enterprise Agentic Meeting OS

*The briefing & facilitation factory.*

[![CI](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml/badge.svg)](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml)
[![Downloads](https://img.shields.io/github/downloads/danielPoloWork/pgs-eamos/total.svg)](https://github.com/danielPoloWork/pgs-eamos/releases)
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
the `pptx`/`docx`/`xlsx` skills are only the cosmetic last hop (RFC §5). How context flows through
that path, station by station: [the context engine](#the-context-engine). Every tool and flag:
[the CLI reference](.eamos-core/docs/cli.md).

## The context engine

EAMOS never passes your meeting context through a prompt — it **compiles** it. Context moves
through four typed stations, and each hop is validated by a gate:

1. **The inputs ledger** (`inputs:` in the manifest) — every number and fact you provide is a
   typed cell with `label`, `value`, `source`, and `provenance: sourced | assumed`. Prose never
   contains a number; it binds a cell with `{{key}}`. `tools/intake.py` builds this ledger from
   pasted CSVs, a prior instance's series store, or an uploaded deck — zero hand-entry.
2. **The meeting manifest** — the ledger plus the four axes (archetype × altitude × function ×
   company context) and the authored content. One file, one source of truth, validated against a
   schema (`manifest-schema`) and confirmed by a human before anything renders
   (`manifest-confirmed`).
3. **The IR** (`tools/render.py`) — a deterministic, versioned JSON projection per deliverable
   (deck, infographic, KPI table, mind map, quiz, topology) over the *same* ledger, so a number
   cannot diverge between the deck and the one-pager. Sourced values render plain; anything else
   renders labeled `⟨… — to verify⟩` (fail-closed) and is collected into a review appendix.
4. **The gates** (`tools/eamos_lint.py`) — structural checks on the IR and the manifest
   (completeness, labeled grounding, audience fit, confidentiality, …). Only a green IR reaches
   the cosmetic last hop (the `emit_*.py` tools — Markdown, PPTX, DOCX, SVG, XLSX — themed by
   data tokens).

Same manifest in, same bytes out — the CI proves it on every push, on Linux and Windows.

### Sourced vs assumed, visibly

One cell of the reference manifest is missing real material, so it is marked `assumed`:

```yaml
kpi.churn_q3:
  value: "~4.2%"
  provenance: assumed        # missing material, filled professionally — never silently
  assumption: "stimato dal trend H1; placeholder — adattare e verificare prima della sala"
  review_required: true
```

Every deliverable renders it **labeled, never plain** — this line is from the rendered deck:

```text
- **Churn logo Q3**: ⟨~4.2% — da verificare⟩
```

The `⟨…⟩` marker survives into the deck, the pre-read, the infographic (amber), the sheet
(highlighted), and the "verify before the room" appendix — and the `grounding-labeled` gate turns
red if a label or an appendix entry is missing. A typo'd provenance is treated as assumed
(fail-closed), so a value is plain only when it is *explicitly* sourced.

## Try it in 60 seconds

From a clone (the repo is private until GTM — see the installer note below for the bundle path):

```sh
git clone https://github.com/danielPoloWork/pgs-eamos.git
cd pgs-eamos/.eamos-core

python tools/render.py orchestrator/examples/qbr-c-level.yaml --out build/deck-ir.json
python tools/eamos_lint.py orchestrator/examples/qbr-c-level.yaml
python tools/emit_md.py build/deck-ir.json --out build/deck.md
python tools/facilitate.py prep orchestrator/examples/qbr-c-level.yaml --minutes 60
```

That renders the reference QBR into a gated deck-IR, lints it (all gates green), emits the
Markdown deck, and prints a timeboxed facilitation script. **No dependencies — stdlib Python**
(3.12+). `pip install python-pptx` only if you want the `.pptx` hop
(`python tools/emit_pptx.py build/deck-ir.json --out build/deck.pptx`). The full tool-by-tool
reference: [`.eamos-core/docs/cli.md`](.eamos-core/docs/cli.md).

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

Pre-1.0, feature-complete through **M8**: the whole loop — manifest → IR → gates → deck,
pre-read, infographic, KPI sheet, quiz, topology — renders end-to-end and deterministically, with
the series store, intake, facilitation, the advisor, and the guided installer shipped. The design
of record is [RFC-0001](.eamos-core/docs/rfc/0001-eamos-meeting-os.md) and
[RFC-0002](.eamos-core/docs/rfc/0002-deliverable-catalogue-and-ir-families.md); the plan and the
milestone log are in [ROADMAP.md](ROADMAP.md).

## Repository

The full agent contract is [AGENTS.md](AGENTS.md). All factory machinery lives under
`.eamos-core/` — a consumer ignores it with a single line.

**Contributing:** how to contribute (and the exhaustive-PR bar) is in
[CONTRIBUTING.md](CONTRIBUTING.md); bugs and feature requests go through the
[issue forms](https://github.com/danielPoloWork/pgs-eamos/issues/new/choose) (a bug needs the
manifest + the exact command; a feature names its axis). We follow the
[Contributor Covenant](CODE_OF_CONDUCT.md); security reports: [SECURITY.md](SECURITY.md).

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
