# Limitations that can become methods

SciGuard / Paper 2 · 26 October 2026

Same filter as SciCap: a limitation is a method only if it yields a representation, decision rule, or evaluation protocol that still stands after CWL, Nipype, BIDS Validator, WINGS/Kepler, and LLM review are granted. The locked Paper 2 protocol is [`SciGuard_Methods.md`](SciGuard_Methods.md).

**Filter**

| Keep as a method | Discard as a feature gap |
|---|---|
| Partial-evidence rule on a DAG edge | “They do not do connectomics” |
| Transform-effect propagation you can ablate | “Add Z3” / “wrap FreeSurfer” |
| Unsafe-acceptance scoring with an UNKNOWN class | “A few obvious bad workflows rejected” |
| Repair that cannot silently pass | A new workflow engine or MCP server |

SciCap owns **single-tool** late binding and invoke (`ALLOW`/`REJECT`/`ABSTAIN`). SciGuard owns **edges and paths** on a workflow graph. Do not republish M1–M4 as Paper 2 methods.

---

## 1. What the closest systems cannot do

| System | Limitation | Why it is not already SciGuard |
|---|---|---|
| CWL / SALAD | Schema and file-format checks. Hints may be ignored. No space, atlas, interpolation, transform direction. | File-valid ≠ scientifically composable. That mismatch is the object. |
| Nipype | Typed interfaces and DAG wiring. Does not check coordinate-space or atlas identity across tools. | Import as a baseline, not a competitor to beat by wrapping it. |
| BIDS Validator / BIDS Apps | Dataset layout and app invocation. Not cross-tool semantic compatibility. | Conformance is arm B0. SciGuard starts after BIDS passes. |
| Boutiques | Invocation schema. No composition language (by design). | Single-tool syntax. Composition is out of scope for them. |
| WINGS / Kepler OWL types | Semantic types and even auto-shims. Require **complete** ontology annotation. Rarely used in exploratory science (Schintke et al., 2024). | Semantic types are not new. **Partial evidence** is. |
| Validity constraints (Schintke et al., *FGCS* 2024) | File size, resources, content sanity, timeouts. Authors say semantic ontologies are too heavy for changing science. VCs are per-step, not space/atlas chains. | Closest general constraint primitive. Residual: neuroimaging-dependent types + UNKNOWN. |
| APE / EDAM | Ontology composition from Topic/Operation/Format. No transform direction or label interpolation. | Paper 2 may reuse EDAM-style annotation style, not the taxonomy. |
| LLM workflow review / VeriFlow | “Semantic” often means intent alignment, not scientific types. Uncalibrated; may accept invalid graphs. | Required control arm, not a method to copy. |
| Kepler auto-shim | Inserts adapters to fix type mismatches. Can hide a scientific error. | SciGuard must **not** auto-repair. |
| NEURA (bioRxiv 2026) | Proof-carrying check of **claims** vs tool outputs and domain axioms (stats, atlas anatomy, p-values). Plans and reports, not edge-level preflight with UNKNOWN. | High related work. Different object: claim audit vs composition preflight. |
| Brain Researcher (2026) | Claim verdicts after execution. | Adjacent. SciGuard is read-only preflight. |
| SciCap (Paper 1) | One capability, one instance. | Necessary input types. Not composition. |

NEURA is the 2026 paper that will be cited against you. Answer in one sentence: NEURA asks whether a **reported finding** is backed by tool evidence; SciGuard asks whether a **declared workflow edge** is scientifically legal given (possibly incomplete) artifact metadata.

---

## 2. Methods worth keeping (Paper 2)

### G1. Partial-evidence composition checking

**Limitation.** Schintke et al. (2024): semantic workflow systems need every file and task annotated in one ontology, which exploratory work will not do. WINGS/Kepler therefore either do not run or treat missing types as failure.

**Method.** Four-valued status on each edge and rule:

| Status | Meaning |
|---|---|
| `PASS` | Required predicates established |
| `FAIL` | Contradiction demonstrated |
| `UNKNOWN` | Evidence missing; not a pass |
| `NEEDS_REVIEW` | Policy requires a human, not a scientific verdict |

Missing `space` is `UNKNOWN`, not `FAIL`. A workflow with any `FAIL` is rejected. A workflow with only `PASS`+`UNKNOWN` is not “valid”; it is **not auto-accepted**. Policy can require review. Never issue a scientific-correctness certificate.

**Test.** Forty percent of the corpus should be incomplete-evidence cases whose gold label is `UNKNOWN`. Primary metric still uses reference-**invalid** cases (unsafe acceptance). Report the auto-accepted set’s residual error separately.

**Why this is a method.** It is the answer to “semantic types already exist.” They exist for fully annotated graphs. SciGuard is built for the graphs agents actually emit.

### G2. Dependent types plus transform-effect propagation

**Limitation.** CWL and Nipype treat two NIfTI integers as compatible. A DK parcellation in `subject_T1w` wired to a DWI tractogram is file-legal and scientifically illegal unless a validated, same-subject, correctly oriented transform is on the path. Label maps resampled with continuous interpolation are a second silent class.

**Method.** Each artifact has a dependent type

`τ = (kind, modality, space, atlas, value_type, units, transform_ancestry, qc)`

Each operation has input predicates `P`, output predicates `Q`, and an effect `T` (for example: rewrite `space`, preserve `atlas`, require `value_type=discrete_labels` ⇒ nearest-neighbor). The checker:

1. Normalizes declared types (never infers missing fields as true).
2. Propagates known effects along edges.
3. Evaluates spatial, atlas, interpolation, lineage, and pipeline-state rules.
4. Records which rules did not run.

Do not claim a new type theory. Claim a **closed neuroimaging effect model** whose necessity is shown by ablating transform-direction and interpolation families (blueprint H3).

**Test.** Mutations: space flip, transform reverse, subject/session swap, DK↔DKT, interpolation change, missing transform. Gold = invalid. BIDS Validator + CWL/Nipype types should miss a large share; SciGuard should not, without inflating false rejection.

### G3. Mutation corpus with an UNKNOWN class and unsafe-acceptance primary

**Limitation.** Prior semantic-workflow papers show hand examples. Agent papers score plan plausibility. NEURA injects claim hallucinations, not composition mutations. Nobody reports **unsafe acceptance of invalid workflows** against a strong native-validator baseline.

**Method.** Expert-reviewed corpus, split by parent workflow (mutations are not independent):

- valid
- invalid, by error family
- incomplete / UNKNOWN

Comparators, same graphs: BIDS Validator + engine types (B0), tool-native checks (B1), LLM review (B2), SciGuard rules only (B3), agent+SciGuard (B4).

**Primary endpoint.** Unsafe acceptance = invalid configurations accepted as executable / all reference-invalid configurations, with a confidence interval. Also report valid-acceptance (over-refusal) and UNKNOWN coverage.

**Why this is a method.** The evaluation protocol is part of the contribution. Without it, SciGuard is a rule pack.

### G4. Repair that cannot silently pass

**Limitation.** Kepler inserts shims. LLM agents “fix” YAML. Either can introduce a new space or atlas error and look improved.

**Method.**

- Preflight is read-only by default.
- A repair is a diff plus a required full re-check.
- Execution of a repair needs explicit approval.
- Score **unsafe repair** and **overcorrection** separately from detection.

**Test.** Experiment E3 in the blueprint: necessary change vs unsafe repair vs overcorrection.

### G5. Scoped soundness, not “scientific validity”

**Limitation.** Reviewers will read any checker as a validity certificate. Metadata can be wrong; image-level QC is out of band.

**Method.** Prove at most one closed property, for example: *if declared space predicates are correct and mandatory transform evidence is present, contradictory spaces are `FAIL`.* Everything else is empirical. `UNKNOWN` and `NEEDS_REVIEW` stay visible. Clinical use is out of scope.

This is a claim-discipline method. It keeps the paper honest and blocks Nature Methods language you cannot support.

---

## 3. Methods that belong next door

| Method | Owner |
|---|---|
| Late binding and invoke ALLOW/REJECT/ABSTAIN on one tool | **SciCap (Paper 1)** |
| Public agent benchmark / false-success leaderboard | **NeuroAgentBench (Paper 3)** |
| Claim-level proof carrying after execution | NEURA / Brain Researcher; cite, do not clone |
| Validity constraints for file size, RAM, timeouts | Schintke et al.; reuse if useful, not a result |
| New workflow engine or CWL replacement | Not a paper |

SciGuard may **consume** SciCap contracts as node annotations. It may not treat SciCap’s invoke RCT as its own finding.

---

## 4. Feature gaps that look like methods but are not

- “Connectomics is missing from WINGS / CWL.” Domain port.
- “We used Z3.” Implementation option; the blueprint already says so.
- “We reject a handful of toy mismatches.” Not an evaluation.
- “LLM reviews the DAG.” Control arm B2.
- “We validate BIDS.” B0.
- “Global soundness of scientific inference.” False and out of scope.
- “Auto-generate the rule pack from papers.” Attractive, derivative of SciToolAgent’s roadmap, and unsafe for a preflight gate.

---

## 5. Recommended methods stack

1. **Representation (G2):** dependent artifact types + operation effects, bound to BIDS/NIDM terms, imported from SciCap/CWL/Nipype where possible.
2. **Decision rule (G1 + G5):** `PASS` / `FAIL` / `UNKNOWN` / `NEEDS_REVIEW` on edges; fail closed on `FAIL`; never certify validity; scoped soundness only.
3. **Repair (G4):** suggest, re-validate, approve.
4. **Evaluation (G3):** mutation corpus; unsafe acceptance vs B0/B1/B2; ablate transform-direction and interpolation.

Default venue if the pilot moves unsafe acceptance without killing valid acceptance: **Imaging Neuroscience**. *IEEE TMI* only with measured connectome distortion (materiality experiment E5). *Nature Methods* only with a second biomedical domain and biological consequence — not the design target.

---

## 6. Pilot that decides these are real methods

| Case | Gold | Method under test |
|---|---|---|
| Valid DKT→DWI chain with documented transform | `PASS` | G2, over-refusal |
| Labels in T1w wired to DWI tractogram, no transform | `FAIL` | G2 vs BIDS/CWL |
| Transform present but `from`/`to` reversed | `FAIL` | G2 transform-direction ablation |
| Transform from another subject | `FAIL` | G2 lineage |
| DK labels used as DKT | `FAIL` | G2 atlas |
| Discrete labels, linear interpolation | `FAIL` or `NEEDS_REVIEW` | G2 interpolation ablation |
| Space field omitted | `UNKNOWN`, not auto-accepted | G1 |
| LLM says “looks fine” on a space-mismatch DAG | B2 accepts; B3 rejects | G3 |
| Agent rewrites the YAML and flips atlas | Repair re-check `FAIL` | G4 |

**Go.** B3 reduces unsafe acceptance vs B0/B1/B2; valid acceptance stays high; `UNKNOWN` cases are not scored as `FAIL`; held-out tool or atlas still works.  
**No-go.** Gains vanish when native Nipype/BIDS checks are configured honestly, or almost every real graph is `UNKNOWN`.

---

## 7. Decision

Turn **partial-evidence checking**, **transform-effect types**, **unsafe-acceptance evaluation**, and **non-silent repair** into the Paper 2 methods. Leave single-tool invoke to SciCap, the public agent suite to NeuroAgentBench, and claim-level proof carrying to NEURA. That is the limitation set this field will grant SciGuard.
