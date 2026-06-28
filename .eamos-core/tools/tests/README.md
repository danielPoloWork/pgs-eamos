# Tests

Dependency-free (stdlib `unittest`), the bar EAMOS imposes on its output imposed on itself. Run from
the repo root; CI runs the same on every PR.

```bash
python -m unittest discover -s .eamos-core/tools/tests -p "test_*.py"
```

| File | Locks in |
|------|----------|
| `test_loader.py` | the YAML subset (Norway problem, leading zeros, block scalars, flow collections) + every reference manifest parses |
| `test_render.py` | **determinism** (every IR byte-identical across runs), **no divergence** (one ARR across deck/infographic/data/mind-map/quiz), grounding (assumed labeled + in the appendix), overlays (altitude reorders, function swaps one section) |
| `test_gates.py` | the gates **pass** on the references and have **teeth** (unresolved binding, unlabeled assumption, out-of-bounds/undeclared param, PII in a `public` meeting, SOX → grounding mandatory) |
| `test_flows.py` | the series store carry-forward, intake dedupe + gap-fill, facilitation follow-up (+ the no-outcomes gate), and egress redaction (no PII leak) |
