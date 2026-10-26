# SciGuard

`sciguard validate` returns **PASS**, **FAIL**, **UNKNOWN**, or **NEEDS_REVIEW** on workflow edges. Omitted `space` is UNKNOWN, not FAIL.

Not a workflow engine or a correctness certificate.

## Go

```bash
pip install git+https://github.com/phindagijimana/sciguard.git
sciguard validate fixtures/invalid/labels_t1w_to_dwi_no_transform.yaml
```

```python
from sciguard import validate
validate("workflow.yaml")
```

Python 3.11+. No model API. `sciguard repair --diff-only` prints a diff; it does not write the input YAML.

Optional agent transport (same `validate`): `python -m sciguard.mcp`

```bash
pytest tests
```

[Methods](docs/SciGuard_Methods.md) · Apache-2.0
