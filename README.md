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

Python 3.11+. No model API. `sciguard repair --diff-only` prints a diff; it does not write the input YAML. B0 is live only when pinned BIDS Validator **3.0.2** is available (`bids-validator` 3.0.2 or `bids-validator-deno` 3.0.2). Node `bids-validator` 1.15.0 is not the pin. `sciguard b0 --s0` points at `shared/data/external/ds000003/` when a real gzip T1w is present; it does not copy NIfTI and does not invent PASS. B1 is live when `cwltool` is importable (File probe, no execute); otherwise recorded.

Optional agent transport (same `validate`): `python -m sciguard.mcp`

```bash
pytest tests
```

[Methods](docs/SciGuard_Methods.md) · Apache-2.0
