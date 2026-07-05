# EAMOS — 企业级智能体会议操作系统

*简报与会议引导的工厂。*

[![CI](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml/badge.svg)](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml)
[![Downloads](https://img.shields.io/github/downloads/danielPoloWork/pgs-eamos/total.svg)](https://github.com/danielPoloWork/pgs-eamos/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../../../LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg)](https://www.conventionalcommits.org/)
[![status: pre-1.0](https://img.shields.io/badge/status-pre--1.0-orange.svg)](../../../../ROADMAP.md)
[![grounding: labeled, never fabricated](https://img.shields.io/badge/grounding-labeled%2C%20never%20fabricated-success.svg)](../../../docs/rfc/0001-eamos-meeting-os.md)

> **🌐 Translations:** [English](../../../../README.md) · [日本語](../ja/README.md) —
> 本文译自英文源（**英文为准**）。翻译政策与时效：[`.eamos-core/docs/i18n/`](../README.md)。

EAMOS 把你提供的输入，转化为一场企业会议所需的**材料与调度**——预读材料、演示稿、引导脚本、纪要、
决策与行动日志——适用于任意规模的公司、任意部门、任意受众层级与任意输出语言。

它是 **EADOS 模式的第二个实例**：同一套机器（访谈 → 清单（manifest）→ 配置档 → 模板 → 渲染 →
门禁 → 角色），面向另一类产出重新定位。EADOS 渲染受治理的**代码仓库**，EAMOS 渲染会议**物料包**。
原则一致：**知识即数据，而非代码**——新增一种会议原型、一个受众层级、一个职能包或一个门禁，都是编辑
一份经校验的 YAML，绝不是在代码里写特例。

## 它是什么（不是什么）

- **它构建、组织并综合**你提供的输入。它**不编造**。当材料缺失时，它可以专业地补全——但该值会被
  **明确标注**（`⟨… — 待核实⟩`）并汇入“进会议室前需核实”的附录。你来调整与复核；机器绝不暗中杜撰。
- **智能体起草；由人来呈现与引导。** EAMOS 绝不把材料直接发给真实高管，也绝不主持现场会议。当你把
  board deck 带进会议室时，它才算“发布”。
- **它不是 BI 工具。** EAMOS 只消费你提供或粘贴的数字；它并不拥有这些数据。

## 工作原理

一套小而可组合的语法（RFC §3），而非一份会议类型目录：

| 维度 | 示例 |
|------|------|
| **原型**（深层结构，约 8 种） | decision/steering · review/status · planning · discovery · post-mortem · retrospective · alignment · 1:1 |
| **受众层级** | board/c-level → vp/director → manager/lead → ic |
| **职能** | Eng · Product · Sales · Marketing · CS · HR · Finance · R&D · Ops |
| **公司情境** | 规模 · 行业 · 合规（SOX/GDPR/HIPAA）· 框架（SAFe/Scrum）· 正式度 · **输出语言** |

QBR 不是一个类型——它是 `review @ c-level × finance × {情境}`。渲染路径是**确定性的**：会议清单被
渲染为一个带类型的 **deck-IR**，门禁在该 IR 上运行，而 `pptx`/`docx`/`xlsx` 技能只是最后的装饰性
一跳（RFC §5）。

## 护城河

绝大多数企业会议都是周期性的。**持久化的系列清单**会延续未决行动、决策日志、滚动风险登记表与 KPI
历史——于是 Q3 的 QBR 一开场就已知道 Q2 决定了什么、KPI 如何变化。一个提示词外壳做不到这一点。

## 状态

早期阶段。设计依据为 [RFC-0001](../../../docs/rfc/0001-eamos-meeting-os.md) 与
[RFC-0002](../../../docs/rfc/0002-deliverable-catalogue-and-ir-families.md)；计划见
[ROADMAP.md](../../../../ROADMAP.md)。**M1**（QBR @ C-level 参考会议）已端到端、确定性地完成渲染——
清单 → deck-IR → Markdown 演示稿 + `.pptx` board deck，门禁全绿；**M2**（可组合的原型语法）进行中。

## 仓库

完整的智能体契约见 [AGENTS.md](../../../../AGENTS.md)。全部工厂机件位于 `.eamos-core/` 之下——
使用方用一行即可忽略它。如何参与贡献（以及“详尽 PR”的标准）：[CONTRIBUTING.md](../../../../CONTRIBUTING.md)。

## 致谢

- **所有者与维护者：** Daniel Polo（[@danielPoloWork](https://github.com/danielPoloWork)）。
- **架构：** **EADOS** 模式的第二个实例——数据优先（schema-first）、机械化门禁、持久化清单、终审门禁
  由人把守。
- **构建工具：** [Anthropic Claude](https://www.anthropic.com/claude) / Claude Code。装饰性的
  `.pptx` 一跳使用 [python-pptx](https://python-pptx.readthedocs.io/)——可选，位于零依赖核心之外。

## 许可与归属

MIT——见 [LICENSE](../../../../LICENSE)。© 2026 Daniel Polo。EAMOS 实行**所有者治理**：任何人都可
*提议*变更，只有所有者能将其合入 `main`。
