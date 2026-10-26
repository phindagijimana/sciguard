# SciGuard literature map

**Paper 2 — composition preflight for workflow edges**  
Scoping review and novelty matrix · 26 October 2026 · search cutoff 26 October 2026

**Status.** Deep literature map for claim-setting, not a PRISMA systematic review and not a finding that SciGuard works. No confirmatory unsafe-acceptance number is reported here. Re-run the searches and lock bibliographic metadata before any manuscript submission.

**Bottom line.** Semantic types, workflow engines, and file/schema validators already exist. CWL, Nipype, BIDS Validator, WINGS, Kepler, Schintke validity constraints, APE/EDAM, and NEURA occupy those slots. A new engine, a new ontology, or a scientific-correctness certificate is not a defensible contribution. The only claim that still looks testable is whether **partial-evidence checking plus transform-effect propagation** on a declared DAG reduces unsafe acceptance of invalid compositions versus honest native types and LLM review.

---

## 1. Search protocol

### 1.1 Sources queried on 26 October 2026

Web search over publisher sites, arXiv, PubMed/PMC, official specifications, and GitHub, using Paper 2 Boolean clusters plus snowball from the locked methods and the SciCap map.

| Cluster | Query family | What it was meant to catch |
|---|---|---|
| A | scientific workflow + semantic / ontology / type system + composition | WINGS, Kepler OWL types, OWL-S, APE, EDAM |
| B | workflow validity / constraints / conformance + Nextflow / CWL / Nipype | Schintke VCs, CWL SALAD, Nipype traits |
| C | BIDS Validator + derivatives + space / atlas | layout/schema baseline (arm B0) |
| D | neuroimaging agent + proof-carrying / claim verification | NEURA, Brain Researcher |
| E | auto-shim / adapter insertion + Kepler / type correction | G4 anti-pattern |

### 1.2 What this map is not

- Not an exhaustive ACM / IEEE / PubMed screen with recorded inclusion counts.
- Not a measurement of unsafe acceptance on any corpus.
- Not a claim that 2026 preprints will remain the version of record.
- Peer-review status of NEURA and Brain Researcher must be rechecked at submission.

### 1.3 How to read threat levels

| Level | Meaning for SciGuard |
|---|---|
| **Blocker** | Already implements the object SciGuard would otherwise call novel. Do not claim that object. |
| **High** | Same job, different encoding. Must be a baseline or a hard differentiator. |
| **Must-cite baseline** | Fair experimental comparator (especially B0/B1). |
| **Adjacent** | Method or evaluation lesson; different object. |
| **Reuse** | Call this tool or vocabulary; do not replace it. |

---

## 2. Landscape in five layers

SciGuard sits on edges of a declared DAG. Novelty has to survive all five layers, not just “agents need a checker.”

```
Layer 5  Claim audit after execution (NEURA, Brain Researcher)
Layer 4  Constraint primitives for DAWs (Schintke VCs)
Layer 3  Ontology-complete composition (WINGS, Kepler, APE/EDAM)
Layer 2  Neuroimaging data conformance (BIDS Validator, BIDS Derivatives)
Layer 1  Executable types (Nipype traits, CWL SALAD, Boutiques)
```

Paper 2’s locked remainder is **not** Layer 1–3 semantic types. It is four-valued status on incomplete graphs (G1) plus a closed transform-effect model (G2) scored as unsafe acceptance (G3).

---

## 3. Layer 1 — executable types (honest B0 / B1)

These systems already type files and invocations. SciGuard must treat them as the control condition, not as missing infrastructure.

### 3.1 Nipype (Gorgolewski et al., 2011)

Typed Python interfaces, DAG wiring, plugins, provenance. Interface traits reject wrong Python/file classes. They do not check coordinate-space identity, atlas identity, transform `from`/`to`, or label-preserving interpolation across tools.

**SciGuard must not rebuild Nipype.** Import native types as arm B1. The residual is scientific edge predicates Nipype does not evaluate.

### 3.2 CWL / SALAD

CommandLineTool + Workflow, SALAD schema validation, Docker/Apptainer, richer types than Boutiques, optional semantic annotations. Hints may be ignored. File-format and schema validity are not space, atlas, interpolation, or transform direction.

**Positioning.** File-valid ≠ scientifically composable. That mismatch is the object. Do not write a CWL replacement.

### 3.3 Boutiques (Glatard et al., 2018)

Invocation schema by design: no composition language. Single-tool syntax belongs to SciCap (Paper 1). Composition is out of Boutiques’ scope.

### 3.4 What Layer 1 implies

If SciGuard’s paper is “we type workflow YAML and reject bad files,” reviewers will cite Nipype + CWL and reject. The intervention has to be **edge rules that native File/schema types do not fire**, measured against those types configured honestly.

---

## 4. Layer 2 — BIDS Validator (arm B0, not the product)

BIDS Validator interprets the BIDS schema: filename entity/suffix/extension rules, sidecar REQUIRED/RECOMMENDED fields and types, TSV columns, and conditional checks. BIDS Validator 2 validates Derivatives layout and metadata (for example `GeneratedBy`). The `space-`, `tpl-`, and `atlas-` entities are **dataset naming and sidecar** rules. Nonstandard template spaces require `SpatialReference` metadata.

BIDS Validator does **not** decide whether a declared workflow edge may wire a T1w parcellation to a DWI tractogram, whether a transform’s `from`/`to` is reversed, or whether DK labels are being used as DKT on a path.

**Required response.** Conformance is arm B0. SciGuard starts after BIDS would pass (or on graphs that are not BIDS datasets at all). Do not describe SciGuard as BIDS validation.

---

## 5. Layer 3 — ontology-complete semantic composition

This is the lineage that already owns “semantic types.” SciGuard cannot claim that object.

### 5.1 WINGS (Gil et al., *IEEE Intelligent Systems*, 2011)

Workflow representations carry semantic constraints on datasets and components. WINGS selects components, datasets, and parameters; rejects invalid combinations; propagates metadata to products. This is scientific composition checking in 2011-era form.

**Positioning.** Semantic constraints on workflow components are not new. WINGS assumes an annotated design space. SciGuard is built for the incomplete graphs agents emit.

### 5.2 Kepler OWL types and auto-shims (Bowers et al.; Ratcliffe, Squire, Kearney, iEMSs 2010)

OWL-typed operators and data; detect incompatible bindings; insert adapters/shims (unit conversion, interpolation). Directly anticipates “file type matches, scientific type does not.”

Kepler-style **auto-repair hides a scientific error**. That is the G4 anti-pattern: SciGuard must not write the workflow. A repair is a diff plus a mandatory full re-check.

### 5.3 APE / EDAM (Kasalica & Lamprecht, 2020; bio.tools)

APE synthesizes workflows from an OWL/EDAM domain model (Topic, Operation, Data, Format) plus annotated tool inputs/outputs; SAT-based composition; optional CWL export. EDAM and bio.tools already annotate life-science tools at registry scale.

APE/EDAM do **not** first-class transform direction or label-preserving interpolation. Paper 2 may reuse EDAM-style annotation *style*, not the taxonomy, and must not claim ontology composition as novel.

### 5.4 What Layer 3 implies

“Semantic types already exist” is true for **fully annotated** graphs. Schintke et al. (2024) state the complementary fact: exploratory work will not maintain one complete ontology, so WINGS/Kepler-class systems either do not run or treat missing types as failure. That is G1’s opening, not a feature gap.

---

## 6. Layer 4 — Schintke validity constraints (closest general primitive)

Schintke et al., “Validity constraints for data analysis workflows,” *Future Generation Computer Systems* 157:82–97 (August 2024), doi:10.1016/j.future.2024.03.037.

VCs make hidden DAW assumptions explicit (file size, memory, threads, timeouts, content sanity). A Nextflow prototype adds `require` / `promise` task directives. Authors argue that full semantic ontologies are too heavy for changing science. VCs are **per-step** integrity/conformance, not neuroimaging space/atlas/transform chains, and they do not define an `UNKNOWN` class for missing scientific fields.

**Positioning.** Closest general constraint primitive. Residual: dependent types `τ`, effect `T`, and four-valued partial evidence. Reuse VCs if useful for resources; do not republish them as a SciGuard result.

---

## 7. Layer 5 — claim audit after a run (cite only)

### 7.1 NEURA (Xie et al., bioRxiv 30 April 2026, doi:10.64898/2026.04.27.721217)

Proof-carrying check of **reported claims** against tool-derived evidence and domain axioms (planning, stats, atlas anatomy). Plans and reports, not edge-level preflight with `UNKNOWN`. This is the 2026 paper that will be cited against SciGuard.

**One-sentence differentiator (locked).** NEURA asks whether a reported finding is backed by tool evidence; SciGuard asks whether a declared workflow edge is scientifically legal given (possibly incomplete) artifact metadata.

Do not clone NeuroEval numbers as a SciGuard finding. Do not describe SciGuard as hallucination-resistant automation.

### 7.2 Brain Researcher (2026; arXiv:2608.19902)

Claim cards after execution: accepted / qualified / revised / blocked / rejected / deferred. Adjacent object: claim verdicts, not read-only composition preflight.

### 7.3 SciCap (Paper 1)

One capability, one instance, `ALLOW` / `REJECT` / `ABSTAIN`. Necessary node annotations. Not composition. Do not republish SciCap’s invoke RCT as a SciGuard result.

---

## 8. Field-by-field residual (the decisive matrix)

“Gap” means *not first-class on a widely used composition or dataset validator that would see an agent-emitted DAG*, not “the science does not exist.”

| SciGuard object | Covered by | Residual gap? |
|---|---|---|
| File / schema / filename validity | CWL SALAD, Nipype traits, BIDS Validator, Boutiques | No |
| Dataset `space-` / `atlas-` naming | BIDS Derivatives, BIDS Validator | No — that is B0 |
| Semantic types on fully annotated graphs | WINGS, Kepler OWL, OWL-S | No |
| Ontology composition (Topic/Operation/Format) | APE, EDAM, bio.tools | No |
| Per-step file size / RAM / timeout | Schintke VCs | No — reuse if needed |
| Auto-shim / silent repair | Kepler correction service | **Anti-pattern (G4)** |
| Claim vs tool evidence after a run | NEURA, Brain Researcher | No — different object |
| Single-tool scientific fields | SciCap | No — consume, do not republish |
| Missing `space` as a first-class `UNKNOWN` | Treated as failure or ignored in Layer 1–3 | **Yes — G1** |
| Transform direction + interpolation effect `T` | Not in CWL/Nipype/BIDS/APE | **Yes — G2** |
| Unsafe acceptance vs honest B0/B1/B2 | Not reported for this invalid family | **Yes — G3 (unevaluated)** |

**Honest unique-ish remainder:** partial-evidence status on edges, plus a closed neuroimaging effect model (space rewrite, atlas/`value_type` preserve, nearest-neighbor on discrete labels), scored so `UNKNOWN` is not `FAIL`.

---

## 9. What would not be novel (do not write these sentences)

- “We introduce semantic types for scientific workflows.” (WINGS, Kepler)
- “We validate BIDS.” (BIDS Validator)
- “We typed Nipype/CWL interfaces.” (2011 / living specs)
- “We compose tools from an ontology.” (APE/EDAM)
- “We add validity constraints for file size and runtime.” (Schintke et al., 2024)
- “We proof-check neuroimaging claims.” (NEURA)
- “We auto-repair illegal edges.” (Kepler shims; forbidden by G4)
- “We built a workflow engine.” (out of scope)

---

## 10. Remaining testable claim

**Primary (keep).** On a mutation corpus split by parent workflow, SciGuard rules (B3) reduce **unsafe acceptance** of reference-invalid compositions relative to BIDS Validator + honest CWL/Nipype types (B0) and LLM review (B2), while valid acceptance stays high and omitted `space` is scored `UNKNOWN`, not `FAIL`.

**Necessary controls**

1. Same graphs across arms. Mutations of one parent are not independent tasks.
2. B0 configured honestly — do not strip native types to create a strawman.
3. No model API in the B3 path.
4. Ablate transform-direction and interpolation families (methods H3).
5. Repair arm emits a diff and re-checks; never writes the input YAML.

If those comparisons are flat, SciGuard is a rule pack, not a methods paper. Publish software or contribute rules upstream.

---

## 11. Work-by-work novelty matrix

| Work | Year | Layer | Threat | SciGuard must add or test |
|---|---|---|---|---|
| OWL-S | 2004 | Semantic | Blocker for “IOPE is new” | Partial evidence, not a new service ontology |
| WINGS | 2011 | Semantic | **Blocker for semantic constraints** | `UNKNOWN` on incomplete graphs; agent-emitted DAGs |
| Nipype | 2011 | Executable | Must-cite B1 | Space/atlas/transform rules Nipype traits omit |
| Kepler OWL + shims | 2010 | Semantic | **High**; G4 anti-pattern | Diff + re-check; no file-writing repair |
| BIDS / BIDS Apps | 2016–17 | Neuro data | Reuse / B0 | Bind `τ` to BIDS/NIDM terms |
| BIDS Validator | living | Conformance | **Must-cite B0** | Edges, not filenames |
| CWL / SALAD | living | Executable | **Must-cite B0** | Transform-effect, not schema |
| EDAM / bio.tools | living | Semantic | High | Space/atlas/xform, not Topic/Operation |
| APE | 2020 | Composition | High | Do not claim SAT synthesis |
| Schintke VCs | 2024 | Constraints | **High** | Dependent types + `UNKNOWN`, not file/RAM VCs |
| SciCap | 2026 | Single tool | Adjacent | Consume node `τ`; do not steal invoke RCT |
| NEURA | 2026 | Claim audit | **High** | Preflight edges ≠ proof-carrying claims |
| Brain Researcher | 2026 | Claim audit | Adjacent | Cite; do not clone claim cards |

---

## 12. Annotated seed bibliography (verified starting set)

Links checked as live search hits on 26 October 2026. Export into a citation manager and lock author/volume/page before submission.

1. Gorgolewski et al. (2011). Nipype. *Front Neuroinform*. https://doi.org/10.3389/fninf.2011.00013  
2. Gorgolewski et al. (2016). BIDS. *Sci Data*. https://doi.org/10.1038/sdata.2016.44  
3. Gorgolewski et al. (2017). BIDS Apps. *PLOS Comput Biol*. https://doi.org/10.1371/journal.pcbi.1005209  
4. Common Workflow Language / SALAD. https://www.commonwl.org/user_guide/  
5. BIDS specification, derivatives, `space-` / `atlas-`. https://bids-specification.readthedocs.io/  
6. BIDS Validator (what it checks). https://github.com/bids-standard/bids-validator/blob/main/docs/user_guide/faq.md  
7. Gil et al. (2011). WINGS. *IEEE Intelligent Systems*. https://doi.org/10.1109/MIS.2010.9  
8. Ratcliffe, Squire, Kearney (2010). Semantic validation and correction of scientific workflows (Kepler). iEMSs. https://scholarsarchive.byu.edu/iemssconference/2010/all/283  
9. Schintke et al. (2024). Validity constraints for data analysis workflows. *Future Generation Computer Systems* 157:82–97. https://doi.org/10.1016/j.future.2024.03.037  
10. Kasalica & Lamprecht (2020). APE. https://pmc.ncbi.nlm.nih.gov/articles/PMC7304703/  
11. EDAM / bio.tools annotation. https://bio.tools  
12. Xie et al. (2026). NEURA. bioRxiv. https://doi.org/10.64898/2026.04.27.721217  
13. Brain Researcher (2026). arXiv:2608.19902. https://arxiv.org/html/2608.19902  
14. Glatard et al. (2018). Boutiques. *GigaScience*. https://doi.org/10.1093/gigascience/giy016  

---

## 13. Go-gate note (methods §5; not a result)

**Question.** Do honest BIDS / Nipype / CWL types already catch the invalid family (T1w labels→DWI with no transform; reversed `from`/`to`; DK used as DKT; omitted `space`)?

**What is known from the literature, not from a SciGuard experiment.** BIDS Validator checks dataset filenames and sidecars, not declared DAG edges. Nipype traits and CWL SALAD check file/schema classes. Two NIfTI integers remain compatible. Omitted `space` is not a native `UNKNOWN` class. Kepler/WINGS catch type mismatches only when the ontology annotation is complete; they do not define SciGuard’s four-valued policy.

**What is not yet measured.** Arm B0 has not been wired on these YAML graphs. No unsafe-acceptance rate is claimed. If a later honest B0/B1 configuration already rejects the invalid family, SciGuard is a rule pack and the methods-paper gate fails.

---

## 14. Immediate next actions

1. Keep `sciguard validate` model-free. Do not add Z3, an LLM arm, or a UI until methods §5 is re-read.
2. Wire BIDS Validator and native Nipype/CWL types as comparators on the **same** graphs (B0/B1), without weakening them.
3. Freeze the mutation corpus split by parent workflow before any confirmatory table.

---

**Decision for the research program.** Start SciGuard as a **read-only preflight and evaluation protocol**, not as a new engine. Residual = partial-evidence + transform-effect, not semantic types. If B3 does not beat honest B0/B1/B2, offer the rules upstream.
