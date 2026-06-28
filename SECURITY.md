# Security Policy

## Scope

EAMOS is a **markdown/YAML meeting operating system** with a small, dependency-free Python core
(`tools/render.py`, `eamos_lint.py`, `series.py`, `intake.py`, `facilitate.py`, `yamlmini.py`) plus
optional cosmetic emitters that need third-party libraries only when used (`emit_pptx`/`emit_docx`/
`emit_xlsx` → python-pptx / python-docx / openpyxl; `emit_md`/`emit_svg` are dependency-free). It has
no runtime service. Its security surface:

- **the tooling** — e.g. a path-traversal or arbitrary-write in the renderer/emitters
  (manifest-driven output paths), or a code-execution vector in a tool;
- **the installer** — `setup/setup.{sh,ps1,command,bat}` download and extract a release bundle. They
  **verify the bundle's SHA256 (fail-closed)**, refuse absolute / `..` paths and symlink/hardlink
  entries (tar-slip), and extract **additively** (never overwrite). A weakness in that chain is in scope;
- **the supply chain** — the GitHub Actions the workflows pin, and the optional cosmetic
  dependencies above (the deterministic core stays dependency-free);
- **the data surface (EAMOS-specific)** — meeting material is among the most sensitive enterprise
  data (board financials, comp/PIP, incidents, M&A; RFC-0001 §11). The **confidentiality posture** is
  the data-safety control: per-cell `pii`/`phi`/`sensitive` tags, `render.py --redact` egress masking,
  the `confidentiality` gate (regulatory regimes → mandatory gates; no sensitive cell in a `public`
  meeting), and grounding-by-labeling (the machine never fabricates a value). A profile/template or a
  gate weakness that would **leak a sensitive value** or **render an insecure default** is in scope.

## Supported versions

EAMOS follows Semantic Versioning. It is **pre-1.0**; only `main` (and, once cut, the latest release)
receives fixes.

| Version | Supported |
|---------|-----------|
| latest `main` | ✅ |
| anything older | ❌ |

## Reporting a vulnerability

**Do not open a public issue or PR for a security problem.** Report it privately via
[GitHub private vulnerability reporting](https://github.com/danielPoloWork/pgs-eamos/security/advisories/new)
(the repository's **Security** tab → *Report a vulnerability*), to `danielPoloWork`.

Please include:

- the affected commit (or `main` at a given date) and your platform / Python version;
- a minimal reproduction — a failing `tools/` invocation, a manifest that triggers it, or a crafted
  bundle for an installer issue is ideal;
- the observed impact and, if known, the root cause. **Never** attach real confidential meeting data —
  use a minimal synthetic manifest.

## What to expect

1. **Acknowledgement** of the report.
2. **Triage & fix under embargo** on a private branch / draft advisory.
3. **Coordinated disclosure**: the fix lands, then the advisory is published; if it changed an
   emitted default or a gate, the change is recorded in the relevant ADR under
   [`.eamos-core/docs/adr/`](.eamos-core/docs/adr/).

Thank you for reporting responsibly.
