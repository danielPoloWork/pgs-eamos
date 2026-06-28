# EAMOS — Enterprise Agentic Meeting OS

*La fabbrica di briefing e facilitazione.*

[![CI](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml/badge.svg)](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../../../LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg)](https://www.conventionalcommits.org/)
[![status: pre-1.0](https://img.shields.io/badge/status-pre--1.0-orange.svg)](../../../../ROADMAP.md)
[![grounding: etichettato, mai inventato](https://img.shields.io/badge/grounding-etichettato%2C%20mai%20inventato-success.svg)](../../../docs/rfc/0001-eamos-meeting-os.md)

> **🌐 Lingue · Languages:** [English](../../../../README.md) — questa è una traduzione della fonte
> inglese (che resta la fonte di verità). Policy e freschezza: [`.eamos-core/docs/i18n/`](../README.md).

EAMOS trasforma gli input di chi prepara la riunione nel **materiale e nella regia** di una riunione
enterprise — pre-read, deck, script di facilitazione, verbale, log di decisioni e azioni — per
qualsiasi dimensione d'azienda, reparto, altitudine di audience e lingua di output.

È la **seconda istanza del pattern EADOS**: la stessa macchina (intervista → manifest → profili →
template → render → gate → ruoli), ri-targettizzata su una diversa classe di output. Dove EADOS
renderizza *repository* governati, EAMOS renderizza *bundle* di riunione. Il principio è lo stesso:
**la conoscenza è dato, non codice** — aggiungere un archetipo di riunione, un'altitudine, un
function pack o un gate significa editare uno YAML validato, mai un caso speciale nel codice.

## Cos'è (e cosa non è)

- **Inquadra, struttura e sintetizza** l'input che fornisci. **Non inventa.** Quando il materiale
  manca, può colmare il vuoto in modo professionale — ma il valore è reso **etichettato**
  (`⟨… — da verificare⟩`) e raccolto in un'appendice "da verificare prima della sala". Tu adatti e
  revisioni; la macchina non inventa mai in silenzio.
- **L'agente drafta; l'umano presenta e facilita.** EAMOS non invia mai materiale a dirigenti veri e
  non conduce mai una riunione dal vivo. Un board deck è "pubblicato" quando lo porti tu in sala.
- **Non è uno strumento di BI.** EAMOS consuma i numeri che fornisci o incolli; non li possiede.

## Come funziona

Una piccola grammatica componibile (RFC §3), non un catalogo di tipi di riunione:

| Asse | Esempi |
|------|--------|
| **Archetipo** (struttura profonda, ~8) | decision/steering · review/status · planning · discovery · post-mortem · retrospective · alignment · 1:1 |
| **Altitudine audience** | board/c-level → vp/director → manager/lead → ic |
| **Funzione** | Eng · Product · Sales · Marketing · CS · HR · Finance · R&D · Ops |
| **Contesto azienda** | dimensione · settore · regolatorio (SOX/GDPR/HIPAA) · framework (SAFe/Scrum) · formalità · **lingua di output** |

Un QBR non è un tipo — è `review @ c-level × finance × {contesto}`. Il percorso di render è
**deterministico**: il meeting manifest viene reso in un **deck-IR** tipizzato, i gate girano
sull'IR, e gli skill `pptx`/`docx`/`xlsx` sono solo l'ultimo hop cosmetico (RFC §5).

## Il moat

Quasi tutte le riunioni enterprise sono ricorrenti. Il **manifest di serie persistente** porta
avanti azioni aperte, il log delle decisioni, un registro rischi rolling e lo storico dei KPI — così
il QBR del Q3 si apre già sapendo cosa fu deciso al Q2 e come si sono mossi i KPI. Un wrapper di
prompt non può farlo.

## Stato

Iniziale. Il design di riferimento è [RFC-0001](../../../docs/rfc/0001-eamos-meeting-os.md) e
[RFC-0002](../../../docs/rfc/0002-deliverable-catalogue-and-ir-families.md); il piano è
[ROADMAP.md](../../../../ROADMAP.md). **M1** (il riferimento QBR @ C-level) rende end-to-end e in
modo deterministico — manifest → deck-IR → deck Markdown + board deck `.pptx`, gate verdi; **M2**
(la grammatica componibile degli archetipi) è in corso.

## Repository

Il contratto completo dell'agente è [AGENTS.md](../../../../AGENTS.md). Tutta la macchina di
fabbrica vive sotto `.eamos-core/` — un consumer la ignora con una sola riga. Come contribuire (e la
barra della PR esaustiva): [CONTRIBUTING.md](../../../../CONTRIBUTING.md).

## Credits

- **Owner & maintainer:** Daniel Polo ([@danielPoloWork](https://github.com/danielPoloWork)).
- **Architettura:** la seconda istanza del pattern **EADOS** — dati schema-first, gate meccanici, un
  manifest persistente e il gate terminale in mano all'umano.
- **Costruito con** [Anthropic Claude](https://www.anthropic.com/claude) / Claude Code. L'hop
  cosmetico `.pptx` usa [python-pptx](https://python-pptx.readthedocs.io/) — opzionale, fuori dal
  core dependency-free.

## Licenza & proprietà

MIT — vedi [LICENSE](../../../../LICENSE). © 2026 Daniel Polo. EAMOS è **owner-governed**: chiunque
può *proporre* modifiche, solo l'owner le porta su `main`.
