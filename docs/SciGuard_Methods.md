# SciGuard methods

Paper 2 protocol · 26 October 2026 · planning document, no results claimed

This is the locked methods stack for SciGuard. It follows the blueprint and the limitations-to-methods filter. SciGuard is a **read-only preflight checker for workflow edges**, not a new workflow engine, not BIDS validation, and not a scientific-validity certificate.

Related documents: [blueprint](Paper_2_Semantic_Workflow_Verification_Blueprint.pdf) · [limitations to methods](SciGuard_Limitations_to_Methods.md)

SciCap owns single-tool late binding and `ALLOW` / `REJECT` / `ABSTAIN`. SciGuard owns **edges and paths** on a declared DAG.

---

## 1. Scope

**Question.** For neuroimaging workflow specifications, do dependent scientific types plus deterministic, partial-evidence checking reduce unsafe acceptance of invalid compositions compared with file/schema validation and LLM-only review, while still accepting valid workflows?

**Unit.** One declared workflow graph `G = (V, E)`: operations `V` and artifact connections `E`. SciGuard decides, per edge and per rule, whether the wiring is known-legal, known-illegal, or under-evidenced.

**First domain.** T1w + diffusion MRI structural connectomics (DK/DKT atlas chains): coordinate spaces, transform direction, atlas identity, label-preserving interpolation, subject lineage.

**Non-scope.** Single-tool invoke (Paper 1). Public agent benchmark (Paper 3). Claim-level proof carrying after execution (NEURA). Clinical diagnosis. Image-quality certification. Global soundness of scientific inference.

---

## 2. The five methods

These are the Paper 2 methods. They are not optional product features.

### G1. Partial-evidence composition checking

Every rule and every edge returns exactly one of:

| Status | Meaning | Auto-accept? |
|---|---|---|
| `PASS` | Required predicates established | Eligible |
| `FAIL` | Contradiction demonstrated | No |
| `UNKNOWN` | Evidence missing | No |
| `NEEDS_REVIEW` | Policy requires a human; not a scientific verdict | No |

Missing `space` is `UNKNOWN`, not `FAIL`. A graph with any `FAIL` is rejected. A graph with only `PASS` + `UNKNOWN` is **not valid** and is **not auto-accepted**. Never issue a scientific-correctness certificate.

### G2. Dependent types plus transform-effect propagation

Each artifact has a dependent type

`τ = (kind, modality, space, atlas, value_type, units, transform_ancestry, qc)`

Each operation has input predicates `P`, output predicates `Q`, and an effect `T` (rewrite `space`, preserve `atlas`, require nearest-neighbor when `value_type=discrete_labels`). The checker:

1. Normalizes declared types. Never infers a missing field as true.
2. Propagates known effects along edges.
3. Evaluates spatial, atlas, interpolation, lineage, and pipeline-state rules.
4. Records which rules did not run.

Reuse BIDS/NIDM terms. Do not invent a parallel ontology. Do not claim a new type theory. The empirical claim is that **transform-direction and interpolation families** account for a substantial share of detections (ablate them).

### G3. Mutation corpus and unsafe-acceptance primary

Expert-reviewed configurations, split by parent workflow (mutations are not independent):

- valid
- invalid, by error family
- incomplete / `UNKNOWN`

**Required comparators, same graphs**

| Arm | What it is |
|---|---|
| B0 | BIDS Validator + engine file/schema types (CWL or Nipype as configured) |
| B1 | Tool-native invocation checks |
| B2 | LLM scientific review, equal metadata and budget |
| B3 | SciGuard rules only (no LLM) |
| B4 | Agent planning with SciGuard enforcement |
| B5 | Expert-curated workflow where feasible (time reported) |

**Primary endpoint (pre-register).** Unsafe acceptance = invalid configurations accepted as executable / all reference-invalid configurations, with a 95% interval.

Also report valid acceptance (over-refusal), `UNKNOWN` coverage, and residual error among auto-accepted graphs. One primary contrast: **B0 vs B3**.

### G4. Repair that cannot silently pass

Preflight is read-only. A repair is a diff. The full checker must run again. Execution needs explicit approval. Score **unsafe repair** and **overcorrection** separately from detection. No LLM repair applied automatically to user data.

### G5. Scoped soundness

At most one formal property, for example: *if declared space predicates are correct and mandatory transform evidence is present, contradictory spaces are `FAIL`.* Image QC, statistics, and clinical inference remain out of band. `UNKNOWN` and `NEEDS_REVIEW` stay visible. Research use only.

---

## 3. Representation (what is implemented)

| Object | Location |
|---|---|
| Artifact type `τ` | `schema/` |
| Operation contracts (`P`, `Q`, `T`) | `contracts/` |
| Versioned predicates | `rules/` |
| Graph normalize → propagate → evaluate | `validation/` |
| `PASS`/`FAIL`/`UNKNOWN`/`NEEDS_REVIEW` reports | `reports/` |
| Valid / invalid / unknown fixtures | `fixtures/` |
| Frozen evaluation, separate version | `benchmark/` |

Interfaces (proposed, not implemented):

```text
sciguard validate workflow.yaml --policy dwi-connectome --report report.json
sciguard explain RULE-SPACE-002
```

The checker must run with no model API configured.

---

## 4. Primary and secondary endpoints

**Primary.** Unsafe acceptance rate of reference-invalid workflow specifications (G3).

**Secondary**

- Valid acceptance rate
- Sensitivity / specificity under a predeclared `UNKNOWN` policy
- Per-error-family recall (space, transform direction, atlas, interpolation, lineage, missing step)
- `UNKNOWN` / `NEEDS_REVIEW` coverage
- Residual error among auto-accepted graphs
- Repair success, unsafe repair, overcorrection
- Runtime overhead vs a full pipeline run
- Held-out tool / atlas / dataset transfer

Paired graphs across arms. Cluster by parent workflow. McNemar or paired bootstrap. Do not treat mutations of one parent as independent tasks.

---

## 5. Pilot that decides the methods are real

| Case | Gold | Method under test |
|---|---|---|
| Valid DKT→DWI chain with documented transform | `PASS` | G2, over-refusal |
| T1w labels wired to DWI tractogram, no transform | `FAIL` | G2 vs B0 |
| Transform present, `from`/`to` reversed | `FAIL` | G2 ablation |
| Transform from another subject | `FAIL` | G2 lineage |
| DK labels used as DKT | `FAIL` | G2 atlas |
| Discrete labels, linear interpolation | `FAIL` or `NEEDS_REVIEW` | G2 interpolation ablation |
| Space field omitted | `UNKNOWN`, not auto-accepted | G1 |
| LLM accepts a space-mismatch DAG | B2 accepts; B3 rejects | G3 |
| Agent rewrites YAML and flips atlas | Repair re-check `FAIL` | G4 |

**Go.** B3 reduces unsafe acceptance vs B0/B1/B2; valid acceptance stays high; `UNKNOWN` is not scored as `FAIL`; at least one held-out tool or atlas still works.  
**No-go for a methods paper.** Gains vanish when native BIDS/Nipype/CWL checks are configured honestly, or almost every real graph is `UNKNOWN`. Then publish software or contribute rules upstream.

---

## 6. Boundaries with the other papers

| Method | Owner |
|---|---|
| G1–G5 as specified above | **SciGuard (Paper 2)** |
| Late binding and invoke `ALLOW`/`REJECT`/`ABSTAIN` | SciCap (Paper 1) |
| Public artifact-level agent benchmark | NeuroAgentBench (Paper 3) |
| Claim-level proof carrying after execution | NEURA / Brain Researcher; cite only |
| File-size / resource validity constraints | Schintke et al. 2024; reuse if useful |
| Generic CWL/Boutiques→MCP adapter | Coala / Nipoppy; not a result |

SciGuard may consume SciCap contracts as node annotations. It may not treat SciCap’s invoke RCT as its own finding.

---

## 7. Journal gates (locked with the methods)

These methods are enough for a specialist methods paper. They are not, by themselves, a Nature-family contribution.

| If the confirmatory study shows… | Venue |
|---|---|
| Unsafe acceptance drops vs honest B0/B1/B2; valid acceptance holds; connectomics-only | **Write to *Imaging Neuroscience*** |
| Usable checker, weak incremental detection | *SoftwareX* or *JOSS* |
| Measured downstream connectome distortion prevented (E5) plus a novel imaging rule family | Reconsider *IEEE Transactions on Medical Imaging* |
| Second biomedical domain, independent labs, biological consequence | Reconsider *Nature Methods* only then |
| General constraint framework beyond imaging | *Nature Computational Science* remains a stretch, not a plan |

**Do not design the project as a Nature paper.** Default target is *Imaging Neuroscience*. NEURA already occupies “deterministic verification for neuroimaging agents” in 2026; the manuscript must say SciGuard is **composition preflight**, not claim audit.

---

## 8. What these methods are not

Do not describe SciGuard as any of the following:

- A new workflow engine or CWL replacement
- BIDS validation
- An SMT/Z3 result (solver is an implementation option)
- Global scientific-validity or clinical clearance
- The first semantic type system (WINGS, Kepler, OWL-S)
- Claim-level proof carrying (NEURA)
- Single-tool capability contracts (SciCap)
- An LLM that reviews workflows (that is arm B2)

---

## 9. Implementation correspondence

| Method | Location |
|---|---|
| G1 four-valued status | `schema/` status enum; `validation/`; `reports/` |
| G2 types and effects | `schema/`; `contracts/`; `rules/` (spatial, atlas, interpolation, lineage) |
| G3 corpus and scoring | `fixtures/{valid,invalid,unknown}/`; `benchmark/` |
| G4 repair re-check | `validation/` post-repair path; no implicit file writes |
| G5 scoped soundness | `docs/` claim boundary; tests that missing evidence ≠ `FAIL` |

Rule definitions are versioned and cited. Synthetic and public data only in the public package. No PHI in demos.
