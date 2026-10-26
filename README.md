# SciGuard

`sciguard validate` returns **PASS**, **FAIL**, **UNKNOWN**, or **NEEDS_REVIEW** on workflow edges. Omitted `space` is UNKNOWN, not FAIL.

Not a workflow engine or a correctness certificate.

## Go

```bash
git clone https://github.com/phindagijimana/sciguard.git
cd sciguard && pip install -e .
sciguard validate fixtures/invalid/labels_t1w_to_dwi_no_transform.yaml
sciguard validate fixtures/unknown/space_omitted.yaml
```

Python 3.11+. No model API. `sciguard repair --diff-only` prints a diff; it does not write the input YAML.

```bash
pytest tests
```

[Methods](docs/SciGuard_Methods.md) · Apache-2.0
