# EAMOS — エンタープライズ・エージェント型ミーティングOS

*ブリーフィングとファシリテーションのファクトリー。*

[![CI](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml/badge.svg)](https://github.com/danielPoloWork/pgs-eamos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../../../LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg)](https://www.conventionalcommits.org/)
[![status: pre-1.0](https://img.shields.io/badge/status-pre--1.0-orange.svg)](../../../../ROADMAP.md)
[![grounding: labeled, never fabricated](https://img.shields.io/badge/grounding-labeled%2C%20never%20fabricated-success.svg)](../../../docs/rfc/0001-eamos-meeting-os.md)

> **🌐 Translations:** [English](../../../../README.md) · [简体中文](../zh-Hans/README.md) —
> 本書は英語ソースからの翻訳です（**英語が正典**）。翻訳ポリシーと鮮度：[`.eamos-core/docs/i18n/`](../README.md)。

EAMOS は、あなたが渡した入力を、エンタープライズなミーティングのための**資料と進行**——プレリード、
デッキ、ファシリテーション台本、議事録、意思決定・アクションログ——へと変換します。あらゆる規模の企業、
あらゆる部門、あらゆる聴衆の高度（アルティテュード）、あらゆる出力言語に対応します。

これは **EADOS パターンの 2 つ目のインスタンス**です。同じ機械（インタビュー → マニフェスト →
プロファイル → テンプレート → レンダリング → ゲート → ロール）を、別種の成果物に向けて再ターゲットして
います。EADOS がガバナンスされた**リポジトリ**をレンダリングするのに対し、EAMOS はミーティングの
**成果物バンドル**をレンダリングします。原則は同じ——**知識はコードではなくデータ**。新しい会議アーキ
タイプ、聴衆の高度、ファンクションパック、ゲートの追加は、検証済み YAML の編集であって、コード内の特例
ではありません。

## これは何か（そして何ではないか）

- **提供された入力を構成し、構造化し、要約します。** **捏造はしません。** 材料が欠けている場合は
  プロフェッショナルに補完しますが、その値は**明示的にラベル付け**され（`⟨… — 要確認⟩`）、「会議室に
  入る前に確認」する付録に集約されます。調整とレビューはあなたが行い、機械が黙って創作することは
  ありません。
- **エージェントは下書きし、人が提示・進行します。** EAMOS が実在の役員に資料を送ることはなく、ライブ
  の会議を進行することもありません。あなたが board deck を会議室に持ち込んだときに「公開」となります。
- **BI ツールではありません。** EAMOS はあなたが提供または貼り付けた数値を消費するだけで、それらを
  所有しません。

## 仕組み

会議タイプのカタログではなく、小さく組み合わせ可能な文法（RFC §3）です：

| 軸 | 例 |
|----|----|
| **アーキタイプ**（深層構造、約 8 種） | decision/steering · review/status · planning · discovery · post-mortem · retrospective · alignment · 1:1 |
| **聴衆の高度** | board/c-level → vp/director → manager/lead → ic |
| **ファンクション** | Eng · Product · Sales · Marketing · CS · HR · Finance · R&D · Ops |
| **企業コンテキスト** | 規模 · 業界 · 規制（SOX/GDPR/HIPAA）· フレームワーク（SAFe/Scrum）· 形式度 · **出力言語** |

QBR は 1 つのタイプではなく、`review @ c-level × finance × {コンテキスト}` です。レンダリング経路は
**決定的**です。会議マニフェストは型付きの **deck-IR** にレンダリングされ、ゲートはその IR 上で実行され、
`pptx`/`docx`/`xlsx` スキルは最後の装飾的な一手にすぎません（RFC §5）。

## 堀（モート）

エンタープライズの会議はほとんどが繰り返しです。**永続的なシリーズ・マニフェスト**が、未解決アクション、
意思決定ログ、ローリングのリスク登録簿、KPI 履歴を引き継ぎます——その結果、Q3 の QBR は開始時点で
すでに Q2 で何が決まり KPI がどう動いたかを把握しています。プロンプトのラッパーには不可能です。

## ステータス

初期段階。設計の典拠は [RFC-0001](../../../docs/rfc/0001-eamos-meeting-os.md) と
[RFC-0002](../../../docs/rfc/0002-deliverable-catalogue-and-ir-families.md)、計画は
[ROADMAP.md](../../../../ROADMAP.md) です。**M1**（QBR @ C-level の参照会議）はエンドツーエンドかつ
決定的にレンダリングされます——マニフェスト → deck-IR → Markdown デッキ + `.pptx` board deck、
ゲートはすべてグリーン。**M2**（組み合わせ可能なアーキタイプ文法）は進行中です。

## リポジトリ

完全なエージェント契約は [AGENTS.md](../../../../AGENTS.md) にあります。すべてのファクトリー機構は
`.eamos-core/` 配下にあり、利用者は 1 行で無視できます。貢献方法（および「詳細な PR」の基準）：
[CONTRIBUTING.md](../../../../CONTRIBUTING.md)。

## クレジット

- **オーナー兼メンテナー：** Daniel Polo（[@danielPoloWork](https://github.com/danielPoloWork)）。
- **アーキテクチャ：** **EADOS** パターンの 2 つ目のインスタンス——スキーマ優先のデータ、機械的ゲート、
  永続的マニフェスト、そして人が握る最終ゲート。
- **ビルドに使用：** [Anthropic Claude](https://www.anthropic.com/claude) / Claude Code。装飾的な
  `.pptx` の一手は [python-pptx](https://python-pptx.readthedocs.io/) を使用します——任意であり、
  依存ゼロのコアの外側です。

## ライセンスと帰属

MIT——[LICENSE](../../../../LICENSE) を参照。© 2026 Daniel Polo。EAMOS は**オーナー統治**です。誰でも
変更を*提案*できますが、`main` に取り込めるのはオーナーだけです。
