# SciGuard

Read-only preflight for workflow **edges**. Status is **PASS**, **FAIL**, **UNKNOWN**, or **NEEDS_REVIEW**. Omitted `space` is UNKNOWN, not FAIL. This is not a scientific-correctness certificate.

Not a workflow engine. BIDS Validator and CWL File types are the public baseline.

## Install

```bash
pip install -e .
```

Python 3.11+. No model API.

## Use

```bash
sciguard validate fixtures/invalid/labels_t1w_to_dwi_no_transform.yaml
sciguard validate fixtures/unknown/space_omitted.yaml
sciguard repair --diff-only fixtures/invalid/linear_on_labels.yaml
```

Repair prints a diff. It never writes the input YAML.

## Tests

```bash
pytest tests
```

## Docs

- [Methods](docs/SciGuard_Methods.md) (G1–G5)
- [Literature map](docs/SciGuard_Literature_Map.md)
- [Methods trace](docs/METHODS_TRACE.md)

Apache-2.0.
