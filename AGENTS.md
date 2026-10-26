# Agent instructions — SciGuard (Paper 2)

Read [`docs/SciGuard_Methods.md`](docs/SciGuard_Methods.md) before writing code. This folder is a **read-only preflight checker for workflow edges**, not a workflow engine and not a scientific-validity certificate.

Program build plan: [`../docs/BUILD_PLAN.md`](../docs/BUILD_PLAN.md) · S0: [`../shared/AGENTS.md`](../shared/AGENTS.md) · SciCap types may be imported as node annotations.

## Mission

On a declared DAG, return `PASS` / `FAIL` / `UNKNOWN` / `NEEDS_REVIEW` per edge and per rule. Missing `space` is `UNKNOWN`, not `FAIL`. Any `FAIL` rejects the graph. `PASS`+`UNKNOWN` is not auto-accepted.

## Do not build

- Nipype, CWL, Nextflow, or Slurm.
- Auto-repair that writes the workflow (Kepler-style shims). A repair is a diff + mandatory re-check (G4).
- Z3 as the paper. A solver is optional later.
- An LLM reviewer (that is evaluation arm B2).
- BIDS validation as the product (that is arm B0).
- SciCap’s invoke RCT claimed as a SciGuard finding.

## Locked methods you must implement

| ID | Rule |
|---|---|
| G1 | Four-valued status. No scientific-correctness certificate. |
| G2 | Dependent type `τ`; operation effect `T` (rewrite space, preserve atlas/value_type, nearest-neighbor on discrete labels). Never infer missing fields. |
| G3 | Fixtures split valid / invalid / unknown. Primary number later = unsafe acceptance. |
| G4 | Repair = diff + full re-check. No implicit file writes. |
| G5 | At most scoped soundness on declared space predicates. |

## Reuse

Existing files (do not replace; implement against them):

- [`schema/status.yaml`](schema/status.yaml)
- [`schema/artifact_type.yaml`](schema/artifact_type.yaml)
- [`contracts/map_labels_to_diffusion.yaml`](contracts/map_labels_to_diffusion.yaml)
- [`rules/RULE-SPACE-002.yaml`](rules/RULE-SPACE-002.yaml)

BIDS Validator as a subprocess comparator later. Native Nipype/CWL types as the honest B1/B0 baseline — call them, do not reimplement.

## Target tree

```text
schema/status.yaml
schema/artifact_type.yaml
schema/workflow.schema.json   # add: nodes, edges, artifact τ on edges
contracts/map_labels_to_diffusion.yaml
rules/RULE-SPACE-002.yaml
rules/RULE-XFM-DIR.yaml       # from/to reversed → FAIL
rules/RULE-ATLAS.yaml         # DK used as DKT → FAIL
rules/RULE-INTERP.yaml        # discrete + linear → FAIL or NEEDS_REVIEW
rules/RULE-LINEAGE.yaml       # other subject → FAIL
validation/check.py           # normalize → propagate → evaluate
validation/cli.py
reports/
fixtures/valid/dkt_to_dwi_with_transform.yaml
fixtures/invalid/labels_t1w_to_dwi_no_transform.yaml
fixtures/invalid/transform_reversed.yaml
fixtures/unknown/space_omitted.yaml
tests/test_check.py
pyproject.toml                # console_script: sciguard
```

## Workflow document (v0)

```yaml
workflow_id: demo-001
operations:
  - id: map1
    contract: map_labels_to_diffusion
edges:
  - from: labels
    to: map1.labels
    artifact:
      kind: parcellation
      space: subject_T1w          # omit → UNKNOWN
      atlas: DesikanKilliany
      value_type: discrete_labels
  - from: tractogram
    to: map1.reference
    artifact:
      kind: diffusion_reference
      space: subject_DWI
  # transform edge present or absent
```

## CLI

```text
sciguard validate fixtures/invalid/labels_t1w_to_dwi_no_transform.yaml --report report.json
```

Stdout / report JSON:

```json
{
  "workflow_id": "demo-001",
  "graph_status": "reject",
  "auto_accepted": false,
  "edges": [
    {"id": "labels→map1", "status": "FAIL", "rule": "RULE-SPACE-002", "reason": "space mismatch, no transform evidence"}
  ],
  "certificate_of_scientific_correctness": false
}
```

`graph_status`: `reject` if any FAIL; `not_auto_accepted` if only PASS+UNKNOWN; `eligible` only if every required rule is PASS and policy allows.

## First vertical slice (must pass)

| Fixture | Gold |
|---|---|
| Valid DKT→DWI with documented same-subject transform | no FAIL; eligible or PASS on space rules |
| Labels in T1w → DWI, no transform | `FAIL` (RULE-SPACE-002) |
| `space` omitted on labels | `UNKNOWN`, `auto_accepted: false` |
| Transform `from`/`to` reversed | `FAIL` |
| DK declared as DKT | `FAIL` |

## Checker algorithm

1. Load workflow, contracts, rules.
2. Normalize declared `τ` on each artifact. Absent field → `unknown`, not a default space.
3. Propagate known effects `T` along edges (space may change; atlas and `value_type` must not).
4. Evaluate each rule. Record rules that did not run.
5. Apply [`schema/status.yaml`](schema/status.yaml) graph policy.

## Tests

`tests/test_check.py` with no model API. The five fixtures above. Assert omitted space ≠ FAIL. Assert repair helper, if present, does not write the input YAML.

## Boundaries

- Single-tool invoke → SciCap.
- Scoring an executed agent → NeuroAgentBench.
- NEURA-style claim audit after a run → cite only.

## Done when

- `sciguard validate` runs offline on the five fixtures.
- `UNKNOWN` is not scored as `FAIL`.
- No certificate field is ever true.

Stop. Do not add Z3, an LLM arm, or a UI until methods §5 is re-read.
