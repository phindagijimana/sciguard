# SciGuard methods trace (wave 2)

Paper 2 · planning document · 26 October 2026 · no confirmatory result claimed

This traces locked G1–G5 onto the public tools they reuse and the literature residual they do not own. It does not replace [`SciGuard_Methods.md`](SciGuard_Methods.md). It does not invent G6. It does not describe SciGuard as a workflow engine.

**Residual (locked).** Partial-evidence status on edges plus a closed transform-effect model. Not semantic types. WINGS, Kepler, CWL, Nipype, BIDS Validator, APE/EDAM, Schintke validity constraints, and NEURA already occupy those slots.

Bibliographic seeds are in [`SciGuard_Literature_Map.md`](SciGuard_Literature_Map.md). Re-lock author/volume/page before any manuscript.

---

## Trace

| Method | Public tool reused | Literature residual | Test |
|---|---|---|---|
| G1 | BIDS Validator / CWL types | four-valued status; missing space = UNKNOWN | `test_check.py` |
| G2 | Nipype/CWL File + SciCap τ | transform-effect propagation | `test_methods.py` |
| G3 | mutation fixtures | primary later = unsafe acceptance vs B0 | fixtures kept |
| G4 | Kepler anti-pattern | repair = diff, never write YAML | `test_check.py` |
| G5 | WINGS/APE ontologies | scoped soundness only; no certificate | cert is always false |

---

## What the public tool already owns

| Tool | Citation | What SciGuard must not claim |
|---|---|---|
| BIDS Validator | BIDS (Gorgolewski et al., 2016); living validator FAQ | Dataset layout, filename `space-`/`atlas-` entities, sidecar schema. Arm **B0**, not the product. |
| CWL / SALAD File | Common Workflow Language user guide | File/schema class. Two NIfTI Files are compatible. Not space, atlas, or transform direction. |
| Nipype File traits | Gorgolewski et al., 2011, *Front Neuroinform* | Python/file class on interfaces. Arm **B1** with CWL File. Do not rebuild Nipype. |
| WINGS | Gil et al., 2011, *IEEE Intelligent Systems* | Semantic constraints on fully annotated components. Blocker for “semantic types are new.” |
| Kepler OWL + shims | Ratcliffe, Squire, Kearney, 2010, iEMSs | Detect incompatible bindings; auto-insert adapters. **G4 anti-pattern:** do not write the workflow. |
| APE / EDAM | Kasalica & Lamprecht, 2020; bio.tools | Ontology composition (Topic / Operation / Data / Format). Do not claim SAT synthesis. |
| Schintke VCs | Schintke et al., 2024, *FGCS* 157:82–97 | Per-step file size, RAM, timeout. Closest general constraint primitive; not τ/`UNKNOWN`. |
| NEURA | Xie et al., 2026, bioRxiv 10.64898/2026.04.27.721217 | Claim audit after a run. Cite only. SciGuard is composition preflight, not proof-carrying claims. |

SciCap τ field names (`space`, `atlas`, `modality`, `value_type`) may annotate nodes. SciCap’s invoke RCT is not a SciGuard finding.

---

## Residual per method

### G1 — four-valued status

BIDS Validator reports errors and warnings on filenames and sidecars. CWL/Nipype File types accept or reject a class. Neither defines `UNKNOWN` when `space` is omitted on a declared edge. SciGuard returns exactly one of `PASS` / `FAIL` / `UNKNOWN` / `NEEDS_REVIEW`. Missing `space` is `UNKNOWN`, not `FAIL`. `PASS`+`UNKNOWN` is not auto-accepted. Implemented in `schema/status.yaml` and `validation/check.py`. Tests: `tests/test_check.py`.

### G2 — dependent type τ and effect T

Nipype/CWL File plus SciCap/BIDS/NIDM field names are the substrate. The residual is transform-effect propagation: rewrite `space` when a validated same-path transform is present; preserve `atlas` and `value_type`; require nearest-neighbor when `value_type=discrete_labels`; never infer a missing field. Implemented in `schema/artifact_type.yaml`, `contracts/map_labels_to_diffusion.yaml`, and `validation/check.py`. Tests: `tests/test_methods.py`.

### G3 — mutation corpus; primary later

The five gold graphs stay split as valid / invalid / unknown. Arm B0 is now wired on those same graphs so **unsafe acceptance** (invalid configurations accepted as executable / all reference-invalid configurations) can be computed later. This document does not report that number. Fixtures: `fixtures/{valid,invalid,unknown}/`. Tests: corpus existence in `tests/test_methods.py`; behavioral contrast in `tests/test_holistic.py`.

### G4 — repair is a diff

Kepler-style auto-shims hide a scientific error. A SciGuard repair is a unified diff plus a mandatory full re-check. `suggest_repair` must not write the input YAML. Tests: `tests/test_check.py`.

### G5 — scoped soundness, no certificate

WINGS and APE can reject illegal combinations when the ontology annotation is complete. SciGuard claims at most scoped soundness on declared space predicates. `certificate_of_scientific_correctness` is always `false`. Tests: `tests/test_check.py`, `tests/test_methods.py`, `tests/test_holistic.py`.

---

## Holistic contrast (behavioral, not a result table)

Same five graphs through B0/B1 and `sciguard validate` (`tests/test_holistic.py`):

| Graph | B0 / B1 | SciGuard |
|---|---|---|
| valid DKT→DWI + transform | accept / File types ok | no FAIL; not a certificate |
| labels T1w→DWI, no transform | B0 does not SPACE-002; B1 File ok | FAIL `RULE-SPACE-002` |
| space omitted | B0 has no UNKNOWN class | UNKNOWN, not auto-accepted |
| transform reversed | B0/B1 silent | FAIL `RULE-XFM-DIR` |
| DK as DKT | B0/B1 silent if filenames ok | FAIL `RULE-ATLAS` |

No model API. No fabricated unsafe-acceptance number.

---

## Wave 3 (this slice)

G3 fixtures added: `fixtures/invalid/other_subject_transform.yaml` (`RULE-LINEAGE` FAIL) and `fixtures/invalid/linear_on_labels.yaml` (`RULE-INTERP` FAIL or `NEEDS_REVIEW`). Second contract: `contracts/resample_discrete_labels.yaml` (nearest-neighbor required). `sciguard repair --diff-only` emits a unified diff and re-checks the unrepaired input; it does not write the input YAML. B0 records installed `bids-validator` versus `shared/pins.yaml` `3.0.2` (`pin_matched: false` if they differ). The pin is not claimed to have been run on YAML graphs. Unsafe-acceptance is still not computed. The wave 1–2 five gold graphs and their tests stay.

---

## Go-gate (methods §5; not a confirmatory result)

Honest BIDS Validator (filename/sidecar) and Nipype/CWL File types do not already catch the invalid family as specified: T1w labels→DWI with no transform, reversed `from`/`to`, DK used as DKT, and omitted `space` as `UNKNOWN` rather than `FAIL`. If a later honest B0/B1 configuration already rejects that family, SciGuard is a rule pack and the methods-paper gate fails.
