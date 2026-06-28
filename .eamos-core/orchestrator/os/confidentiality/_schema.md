# Confidentiality Schema (the enterprise lens)

Meeting material is among the most sensitive enterprise data (RFC-0001 §11). The posture is data,
enforced by two mechanisms: the `confidentiality` gate (eamos_lint) and the `--redact` egress pass
(render). Designed from day one, not bolted on.

## policy.yaml

```yaml
version: <int>
classifications: [public, internal, confidential, restricted]
default: <classification>          # applied when a manifest sets none
regimes:
  <REGIME>:                        # e.g. SOX, GDPR, HIPAA
    mandatory_gates: [<gate-id>]   # gates this regime makes non-skippable
    redact_tags:     [<tag>]       # cell tags this regime redacts on egress (pii, phi, …)
```

## Manifest fields

- `classification:` — `public | internal | confidential | restricted` (defaults from policy).
- Per-cell tags in the ledger: `pii: true`, `phi: true`, `sensitive: true`.

## Enforcement

- **`confidentiality` gate** (lint): every `context.regulatory` regime is known to the policy; its
  `mandatory_gates` ran green; and **no redact-tagged cell appears in a `public`-classified meeting**.
- **`render.py --redact`** (egress): masks every cell carrying an active regime's `redact_tag` (or
  `sensitive: true`) → `⟦redatto⟧` / `⟦redacted⟧`, across **every** projection (one ledger, §7).

## Invariant

Redaction operates on the same typed ledger grounding uses — so EAMOS never leaks a sensitive value
*and* never invents one. What leaves the machine is exactly what the classification permits.
