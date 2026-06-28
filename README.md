# EAMOS — Enterprise Agentic Meeting OS

*The briefing & facilitation factory.*

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

## Status

Greenfield. The design of record is [RFC-0001](.eamos-core/docs/rfc/0001-eamos-meeting-os.md); the
plan is [ROADMAP.md](ROADMAP.md). The first milestone (M1) ships **one** reference meeting —
**QBR @ C-level** — end-to-end, then the grammar generalizes.

## Repository

The full agent contract is [AGENTS.md](AGENTS.md). All factory machinery lives under
`.eamos-core/` — a consumer ignores it with a single line.
