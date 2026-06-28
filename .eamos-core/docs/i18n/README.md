# Translations

**English is the source of truth** for every on-disk artifact (RFC-0001 §7). The files here are
**derived** from the English sources and may lag; when a translation and its source disagree, the
**English source wins**. Freshness is tracked in [translation-status.md](translation-status.md).

Note the distinction (RFC-0001 §7): this i18n folder localizes the *project's own documentation*.
It is unrelated to a meeting's `output_lang` — the language EAMOS *renders deliverables in*, which
is a manifest field, not a translation of the system.

## Available translations

| Target | File | Source |
|--------|------|--------|
| 简体中文 (`zh-Hans`) | [zh-Hans/README.md](zh-Hans/README.md) | [`README.md`](../../../README.md) |
| 日本語 (`ja`) | [ja/README.md](ja/README.md) | [`README.md`](../../../README.md) |

## Adding or updating a translation

1. Translate from the English source; keep headings, anchors, and links intact (adjust only the
   relative depth of paths).
2. Record the source commit + date in [translation-status.md](translation-status.md).
3. When an English source changes, its translations are **stale** until refreshed — the CI
   freshness check (a later milestone) will flag them.
