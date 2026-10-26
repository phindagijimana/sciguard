"""Normalize declared τ, propagate operation effects T, evaluate G1–G5 rules.

Read-only. Missing fields stay unknown. Never issues a scientific-correctness
certificate. Does not execute a workflow engine or call a model API.
"""

from __future__ import annotations

import copy
import difflib
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "workflow.schema.json"
CONTRACTS_DIR = ROOT / "contracts"
RULES_DIR = ROOT / "rules"

MISSING = "unknown"  # declared-field sentinel (never infer)
PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"  # G1 status; missing evidence is not FAIL
NEEDS_REVIEW = "NEEDS_REVIEW"

STATUSES = (PASS, FAIL, UNKNOWN, NEEDS_REVIEW)

DK_FAMILY = "DesikanKilliany"
DKT_FAMILY = "DesikanKillianyTourville"

ATLAS_ALIASES = {
    "desikankilliany": DK_FAMILY,
    "dk": DK_FAMILY,
    "desikan-killiany": DK_FAMILY,
    "desikan_killiany": DK_FAMILY,
    "desikankillianytourville": DKT_FAMILY,
    "dkt": DKT_FAMILY,
    "desikan-killiany-tourville": DKT_FAMILY,
    "desikan_killiany_tourville": DKT_FAMILY,
}

LINEAR_INTERP = {
    "linear",
    "trilinear",
    "bilinear",
    "cubic",
    "bspline",
    "b-spline",
    "b_spline",
    "continuous",
}
NEAREST_INTERP = {
    "nearest",
    "nearest_neighbor",
    "nearest-neighbour",
    "nearest_neighbour",
    "nn",
    "genericlabel",
}

REQUIRED_RULES = (
    "RULE-SPACE-002",
    "RULE-XFM-DIR",
    "RULE-ATLAS",
    "RULE-INTERP",
    "RULE-LINEAGE",
)


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _is_absent(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _declared(container: dict[str, Any] | None, *keys: str) -> Any:
    """Return the first present field, or MISSING. Do not default a missing key."""
    if not isinstance(container, dict):
        return MISSING
    for key in keys:
        if key not in container:
            continue
        value = container[key]
        if _is_absent(value):
            return MISSING
        if isinstance(value, str) and value.strip().lower() == MISSING:
            return MISSING
        return value
    return MISSING


def _is_unknown(value: Any) -> bool:
    return value is MISSING or value == MISSING or _is_absent(value)


def _as_tri_bool(value: Any) -> Any:
    if _is_unknown(value):
        return MISSING
    if value is True or value == 1:
        return True
    if value is False or value == 0:
        return False
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes"}:
            return True
        if lowered in {"false", "no"}:
            return False
    return MISSING


def _norm_space(value: Any) -> Any:
    if _is_unknown(value):
        return MISSING
    return str(value).strip()


def _atlas_family(value: Any) -> Any:
    if _is_unknown(value):
        return MISSING
    key = str(value).strip().lower().replace(" ", "")
    if key in ATLAS_ALIASES:
        return ATLAS_ALIASES[key]
    compact = key.replace("-", "").replace("_", "")
    return ATLAS_ALIASES.get(compact, str(value).strip())


def normalize_tau(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Bind declared artifact fields. Absent → unknown. Never infer."""
    artifact = raw if isinstance(raw, dict) else {}
    ancestry = artifact.get("transform_ancestry")
    ancestry = ancestry if isinstance(ancestry, dict) else {}
    return {
        "kind": _declared(artifact, "kind"),
        "modality": _declared(artifact, "modality"),
        "space": _norm_space(_declared(artifact, "space")),
        "atlas": _atlas_family(_declared(artifact, "atlas")),
        "atlas_identity": _atlas_family(
            _declared(artifact, "label_table", "atlas_identity", "source_atlas")
        ),
        "value_type": _declared(artifact, "value_type"),
        "units": _declared(artifact, "units"),
        "interpolation": _declared(artifact, "interpolation"),
        "subject": _declared(artifact, "subject", "subject_id"),
        "qc": _declared(artifact, "qc"),
        "from_space": _norm_space(
            _declared(artifact, "from_space")
            if "from_space" in artifact
            else _declared(ancestry, "from_space")
        ),
        "to_space": _norm_space(
            _declared(artifact, "to_space")
            if "to_space" in artifact
            else _declared(ancestry, "to_space")
        ),
        "same_subject": _as_tri_bool(
            artifact["same_subject"]
            if "same_subject" in artifact
            else ancestry.get("same_subject", MISSING)
        ),
        "verified": _as_tri_bool(
            artifact["verified"]
            if "verified" in artifact
            else ancestry.get("verified", MISSING)
        ),
    }


def _edge_id(edge: dict[str, Any]) -> str:
    if edge.get("id"):
        return str(edge["id"])
    return f"{edge.get('from', '?')}→{edge.get('to', '?')}"


def _split_port(target: str) -> tuple[str, str | None]:
    if "." in target:
        operation_id, port = target.split(".", 1)
        return operation_id, port
    return target, None


def _load_contract(name: Any) -> dict[str, Any] | None:
    if _is_unknown(name):
        return None
    path = CONTRACTS_DIR / f"{name}.yaml"
    if not path.is_file():
        return None
    loaded = _load_yaml(path)
    return loaded if isinstance(loaded, dict) else None


def _load_workflow_schema() -> dict[str, Any]:
    import json

    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _finding(
    edge_id: str,
    rule: str,
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {"id": edge_id, "status": status, "rule": rule, "reason": reason}


def _spaces_equal(left: Any, right: Any) -> bool:
    if _is_unknown(left) or _is_unknown(right):
        return False
    return str(left) == str(right)


def _interp_class(value: Any) -> Any:
    if _is_unknown(value):
        return MISSING
    key = str(value).strip().lower().replace(" ", "_")
    if key in LINEAR_INTERP:
        return "linear"
    if key in NEAREST_INTERP:
        return "nearest_neighbor"
    return key


def _collect_operation_ports(
    operation: dict[str, Any],
    edges: list[dict[str, Any]],
) -> dict[str, dict[str, Any] | None]:
    op_id = operation["id"]
    ports: dict[str, dict[str, Any] | None] = {
        "labels": None,
        "reference": None,
        "transform": None,
    }
    for edge in edges:
        target_op, port = _split_port(str(edge.get("to", "")))
        if target_op != op_id:
            continue
        kind = edge["tau"]["kind"]
        if port == "labels" or kind == "parcellation":
            ports["labels"] = edge
        elif port in {"reference", "ref"} or kind in {
            "diffusion_reference",
            "tractogram",
            "anatomical_reference",
        }:
            ports["reference"] = edge
        elif port == "transform" or kind == "spatial_transform":
            ports["transform"] = edge
    return ports


def _validated_transform_chain(
    labels: dict[str, Any],
    reference: dict[str, Any],
    transform: dict[str, Any],
) -> Any:
    """True / False / UNKNOWN — never infer a missing direction as valid."""
    src = labels["space"]
    dst = reference["space"]
    frm = transform["from_space"]
    to = transform["to_space"]
    if any(_is_unknown(v) for v in (src, dst, frm, to)):
        return UNKNOWN
    return _spaces_equal(frm, src) and _spaces_equal(to, dst)


def _propagate(
    labels: dict[str, Any],
    reference: dict[str, Any],
    transform: dict[str, Any] | None,
    chain_ok: Any,
) -> dict[str, Any]:
    """Effect T: may rewrite space; must preserve atlas and value_type."""
    out = copy.deepcopy(labels)
    if chain_ok is True and transform is not None:
        out["space"] = reference["space"]
        out["transform_ancestry"] = {
            "from_space": transform["from_space"],
            "to_space": transform["to_space"],
            "same_subject": transform["same_subject"],
            "verified": transform["verified"],
        }
    return out


def _eval_space(ports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    labels = ports["labels"]
    reference = ports["reference"]
    transform = ports["transform"]
    if labels is None or reference is None:
        return _finding(
            "graph",
            "RULE-SPACE-002",
            UNKNOWN,
            "labels or diffusion reference edge missing",
        )
    edge_id = _edge_id(labels)
    src = labels["tau"]["space"]
    dst = reference["tau"]["space"]
    if _is_unknown(src) or _is_unknown(dst):
        return _finding(
            edge_id,
            "RULE-SPACE-002",
            UNKNOWN,
            "space omitted or unknown; not scored as FAIL",
        )
    if _spaces_equal(src, dst):
        return _finding(
            edge_id,
            "RULE-SPACE-002",
            PASS,
            "declared spaces match",
        )
    if transform is None:
        return _finding(
            edge_id,
            "RULE-SPACE-002",
            FAIL,
            "space mismatch, no transform evidence",
        )
    chain = _validated_transform_chain(
        labels["tau"], reference["tau"], transform["tau"]
    )
    if chain is UNKNOWN:
        return _finding(
            edge_id,
            "RULE-SPACE-002",
            UNKNOWN,
            "transform present but from/to or endpoint space incomplete",
        )
    if chain:
        return _finding(
            edge_id,
            "RULE-SPACE-002",
            PASS,
            "validated same-path transform chain",
        )
    return _finding(
        edge_id,
        "RULE-SPACE-002",
        FAIL,
        "space mismatch, transform chain not validated",
    )


def _eval_xfm(ports: dict[str, dict[str, Any] | None]) -> dict[str, Any] | None:
    labels = ports["labels"]
    reference = ports["reference"]
    transform = ports["transform"]
    if transform is None:
        return None
    if labels is None or reference is None:
        return _finding(
            _edge_id(transform),
            "RULE-XFM-DIR",
            UNKNOWN,
            "transform present but labels or reference missing",
        )
    edge_id = _edge_id(transform)
    src = labels["tau"]["space"]
    dst = reference["tau"]["space"]
    frm = transform["tau"]["from_space"]
    to = transform["tau"]["to_space"]
    if any(_is_unknown(v) for v in (src, dst, frm, to)):
        return _finding(
            edge_id,
            "RULE-XFM-DIR",
            UNKNOWN,
            "transform direction fields incomplete",
        )
    if _spaces_equal(frm, src) and _spaces_equal(to, dst):
        return _finding(
            edge_id,
            "RULE-XFM-DIR",
            PASS,
            "transform from/to matches labels→reference",
        )
    if _spaces_equal(frm, dst) and _spaces_equal(to, src):
        return _finding(
            edge_id,
            "RULE-XFM-DIR",
            FAIL,
            "transform from/to reversed",
        )
    return _finding(
        edge_id,
        "RULE-XFM-DIR",
        FAIL,
        "transform from/to contradicts labels and reference spaces",
    )


def _eval_atlas(ports: dict[str, dict[str, Any] | None]) -> dict[str, Any] | None:
    labels = ports["labels"]
    if labels is None:
        return None
    declared = labels["tau"]["atlas"]
    identity = labels["tau"]["atlas_identity"]
    if _is_unknown(identity):
        return None
    edge_id = _edge_id(labels)
    if _is_unknown(declared):
        return _finding(
            edge_id,
            "RULE-ATLAS",
            UNKNOWN,
            "atlas identity present but declared atlas omitted",
        )
    if declared == identity:
        return _finding(
            edge_id,
            "RULE-ATLAS",
            PASS,
            "declared atlas matches label-table identity",
        )
    return _finding(
        edge_id,
        "RULE-ATLAS",
        FAIL,
        f"atlas identity mismatch: {identity} used as {declared}",
    )


def _contract_requires_nearest(contract: dict[str, Any] | None) -> bool:
    """True when the loaded contract requires nearest-neighbor on labels."""
    if not isinstance(contract, dict):
        return False
    effect = contract.get("effect") or contract.get("operation_effect") or {}
    if isinstance(effect, dict):
        required = effect.get("interpolation_if_discrete_labels") or effect.get(
            "interpolation"
        )
        if _interp_class(required) == "nearest_neighbor":
            return True
    inputs = contract.get("inputs")
    if isinstance(inputs, dict):
        labels_in = inputs.get("labels")
        if isinstance(labels_in, dict) and _interp_class(
            labels_in.get("interpolation")
        ) == "nearest_neighbor":
            return True
    pre = contract.get("preconditions") or []
    blob = " ".join(str(item) for item in pre) if isinstance(pre, list) else str(pre)
    return "nearest_neighbor" in blob


def _eval_interp(
    operation: dict[str, Any],
    ports: dict[str, dict[str, Any] | None],
    contract: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    labels = ports["labels"]
    if labels is None:
        return None
    value_type = labels["tau"]["value_type"]
    interpolation = _declared(operation, "interpolation")
    if _is_unknown(interpolation):
        interpolation = labels["tau"]["interpolation"]
    if ports["transform"] is not None and _is_unknown(interpolation):
        interpolation = ports["transform"]["tau"]["interpolation"]
    edge_id = _edge_id(labels)
    if _is_unknown(value_type):
        return None
    if value_type != "discrete_labels":
        return _finding(
            edge_id,
            "RULE-INTERP",
            PASS,
            "value_type is not discrete_labels",
        )
    klass = _interp_class(interpolation)
    if _is_unknown(klass):
        return _finding(
            edge_id,
            "RULE-INTERP",
            UNKNOWN,
            "discrete labels, interpolation omitted",
        )
    if klass == "nearest_neighbor":
        return _finding(
            edge_id,
            "RULE-INTERP",
            PASS,
            "nearest-neighbor interpolation on discrete labels",
        )
    if klass == "linear":
        reason = "discrete labels with linear/continuous interpolation"
        if _contract_requires_nearest(contract):
            name = contract.get("operation") if isinstance(contract, dict) else None
            if name:
                reason = f"{reason}; {name} requires nearest_neighbor"
        return _finding(
            edge_id,
            "RULE-INTERP",
            FAIL,
            reason,
        )
    return _finding(
        edge_id,
        "RULE-INTERP",
        NEEDS_REVIEW,
        f"discrete labels with undeclared interpolation class {interpolation!r}",
    )


def _eval_lineage(
    ports: dict[str, dict[str, Any] | None],
    contract: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    labels = ports["labels"]
    reference = ports["reference"]
    transform = ports["transform"]
    if labels is None:
        return None
    subjects = [labels["tau"]["subject"]]
    edge_id = _edge_id(labels)
    if reference is not None:
        subjects.append(reference["tau"]["subject"])
    same_subject = MISSING
    if transform is not None:
        subjects.append(transform["tau"]["subject"])
        same_subject = transform["tau"]["same_subject"]
        edge_id = _edge_id(transform)
    known = [s for s in subjects if not _is_unknown(s)]
    if same_subject is False:
        reason = "transform declared as different subject"
        if isinstance(contract, dict) and contract.get("operation"):
            reason = f"{reason}; {contract['operation']} requires same-subject lineage"
        return _finding(
            edge_id,
            "RULE-LINEAGE",
            FAIL,
            reason,
        )
    if len(set(known)) > 1:
        reason = "subject ids differ across labels, reference, or transform"
        if isinstance(contract, dict) and contract.get("operation"):
            reason = f"{reason}; {contract['operation']} requires same-subject lineage"
        return _finding(
            edge_id,
            "RULE-LINEAGE",
            FAIL,
            reason,
        )
    if same_subject is True or (known and len(set(known)) == 1 and len(known) >= 2):
        return _finding(
            edge_id,
            "RULE-LINEAGE",
            PASS,
            "same-subject lineage established",
        )
    if transform is None and not known:
        return None
    return _finding(
        edge_id,
        "RULE-LINEAGE",
        UNKNOWN,
        "subject lineage not fully declared",
    )


def _graph_policy(findings: list[dict[str, Any]]) -> tuple[str, bool]:
    statuses = {item["status"] for item in findings}
    if FAIL in statuses:
        return "reject", False
    if statuses <= {PASS} and findings:
        return "eligible", False
    return "not_auto_accepted", False


def check_workflow(workflow: Path | str | dict[str, Any]) -> dict[str, Any]:
    """Run normalize → propagate → evaluate. Certificate is always false."""
    source_path: Path | None = None
    if isinstance(workflow, dict):
        document = copy.deepcopy(workflow)
    else:
        source_path = Path(workflow)
        document = _load_yaml(source_path)
    if not isinstance(document, dict):
        raise ValueError("workflow document must be a mapping")

    jsonschema.validate(document, _load_workflow_schema())

    nodes = {
        str(node["id"]): node
        for node in document.get("nodes") or []
        if isinstance(node, dict) and node.get("id")
    }
    operations = [
        op for op in document.get("operations") or [] if isinstance(op, dict)
    ]
    raw_edges = [e for e in document.get("edges") or [] if isinstance(e, dict)]

    edges: list[dict[str, Any]] = []
    for raw in raw_edges:
        artifact = raw.get("artifact")
        if not isinstance(artifact, dict):
            node = nodes.get(str(raw.get("from", "")))
            artifact = (node or {}).get("artifact")
        tau = normalize_tau(artifact if isinstance(artifact, dict) else {})
        edges.append({**raw, "tau": tau})

    findings: list[dict[str, Any]] = []
    ran: set[str] = set()
    propagated: list[dict[str, Any]] = []

    for operation in operations:
        ports = _collect_operation_ports(operation, edges)
        contract = _load_contract(operation.get("contract"))
        space = _eval_space(ports)
        findings.append(space)
        ran.add("RULE-SPACE-002")

        xfm = _eval_xfm(ports)
        if xfm is not None:
            findings.append(xfm)
            ran.add("RULE-XFM-DIR")

        atlas = _eval_atlas(ports)
        if atlas is not None:
            findings.append(atlas)
            ran.add("RULE-ATLAS")

        interp = _eval_interp(operation, ports, contract)
        if interp is not None:
            findings.append(interp)
            ran.add("RULE-INTERP")

        lineage = _eval_lineage(ports, contract)
        if lineage is not None:
            findings.append(lineage)
            ran.add("RULE-LINEAGE")

        labels = ports["labels"]
        reference = ports["reference"]
        transform = ports["transform"]
        chain = UNKNOWN
        if labels is not None and reference is not None and transform is not None:
            chain = _validated_transform_chain(
                labels["tau"], reference["tau"], transform["tau"]
            )
        if labels is not None and reference is not None:
            out_tau = _propagate(
                labels["tau"],
                reference["tau"],
                transform["tau"] if transform is not None else None,
                chain,
            )
            if contract is not None:
                must_preserve = ["atlas", "value_type"]
                for field in must_preserve:
                    if (
                        not _is_unknown(labels["tau"][field])
                        and out_tau[field] != labels["tau"][field]
                    ):
                        findings.append(
                            _finding(
                                _edge_id(labels),
                                "RULE-ATLAS" if field == "atlas" else "RULE-INTERP",
                                FAIL,
                                f"operation effect illegally rewrote {field}",
                            )
                        )
                        ran.add("RULE-ATLAS" if field == "atlas" else "RULE-INTERP")
            propagated.append(
                {
                    "operation": operation["id"],
                    "output": "labels_dwi",
                    "tau": out_tau,
                }
            )

    graph_status, auto_accepted = _graph_policy(findings)
    return {
        "workflow_id": document.get("workflow_id"),
        "graph_status": graph_status,
        "auto_accepted": auto_accepted,
        "edges": findings,
        "rules_not_run": [rule for rule in REQUIRED_RULES if rule not in ran],
        "propagated": propagated,
        "source": str(source_path) if source_path is not None else None,
        "certificate_of_scientific_correctness": False,
    }


def _edge_artifact(edge: dict[str, Any]) -> dict[str, Any]:
    artifact = edge.get("artifact")
    return artifact if isinstance(artifact, dict) else {}


def _propose_document(
    document: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """In-memory G4 proposal. Caller must not write this over the input."""
    proposed = copy.deepcopy(document)
    fail_rules = {item["rule"] for item in findings if item["status"] == FAIL}
    operations = [
        op for op in (proposed.get("operations") or []) if isinstance(op, dict)
    ]
    edges = [edge for edge in (proposed.get("edges") or []) if isinstance(edge, dict)]

    if "RULE-INTERP" in fail_rules:
        for operation in operations:
            operation["interpolation"] = "nearest_neighbor"
        for edge in edges:
            artifact = _edge_artifact(edge)
            if not artifact:
                continue
            if artifact.get("value_type") == "discrete_labels" or _interp_class(
                artifact.get("interpolation")
            ) == "linear":
                artifact["interpolation"] = "nearest_neighbor"
                edge["artifact"] = artifact

    if "RULE-XFM-DIR" in fail_rules:
        for edge in edges:
            artifact = _edge_artifact(edge)
            if artifact.get("kind") == "spatial_transform":
                artifact["from_space"], artifact["to_space"] = (
                    artifact.get("to_space"),
                    artifact.get("from_space"),
                )
                edge["artifact"] = artifact

    if "RULE-ATLAS" in fail_rules:
        for edge in edges:
            artifact = _edge_artifact(edge)
            identity = artifact.get("label_table") or artifact.get("atlas_identity")
            if identity:
                artifact["atlas"] = identity
                edge["artifact"] = artifact

    if "RULE-LINEAGE" in fail_rules:
        label_subject = None
        for edge in edges:
            artifact = _edge_artifact(edge)
            if artifact.get("kind") == "parcellation" and artifact.get("subject"):
                label_subject = artifact.get("subject")
                break
        for edge in edges:
            artifact = _edge_artifact(edge)
            if not artifact:
                continue
            if label_subject:
                artifact["subject"] = label_subject
            if artifact.get("kind") == "spatial_transform":
                artifact["same_subject"] = True
            edge["artifact"] = artifact

    if "RULE-SPACE-002" in fail_rules:
        has_xfm = any(
            _edge_artifact(edge).get("kind") == "spatial_transform" for edge in edges
        )
        if not has_xfm and operations:
            op_id = operations[0].get("id", "map1")
            labels_space = None
            ref_space = None
            subject = None
            for edge in edges:
                artifact = _edge_artifact(edge)
                kind = artifact.get("kind")
                if kind == "parcellation":
                    labels_space = artifact.get("space")
                    subject = artifact.get("subject") or subject
                elif kind in {
                    "diffusion_reference",
                    "tractogram",
                    "anatomical_reference",
                }:
                    ref_space = artifact.get("space")
                    subject = artifact.get("subject") or subject
            xfm: dict[str, Any] = {
                "kind": "spatial_transform",
                "same_subject": True,
                "verified": True,
            }
            if labels_space:
                xfm["from_space"] = labels_space
            if ref_space:
                xfm["to_space"] = ref_space
            if subject:
                xfm["subject"] = subject
            edges.append(
                {
                    "id": f"xfm→{op_id}",
                    "from": "transform",
                    "to": f"{op_id}.transform",
                    "artifact": xfm,
                }
            )
            proposed["edges"] = edges

    return proposed


def _annotation_lines(findings: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for finding in findings:
        if finding["status"] != FAIL:
            continue
        rule = finding["rule"]
        if rule == "RULE-SPACE-002":
            lines.append(
                "+ add edge: spatial_transform from_space=labels.space "
                "to_space=reference.space same_subject=true"
            )
        elif rule == "RULE-XFM-DIR":
            lines.append("+ swap transform.from_space with transform.to_space")
        elif rule == "RULE-ATLAS":
            lines.append("+ set artifact.atlas to artifact.label_table (or the reverse)")
        elif rule == "RULE-INTERP":
            lines.append("+ set interpolation: nearest_neighbor")
        elif rule == "RULE-LINEAGE":
            lines.append("+ restrict transform and reference to the labels subject")
        else:
            lines.append(f"+ inspect {rule}: {finding['reason']}")
    return lines


def _unified_diff(from_name: str, to_name: str, before: str, after: str) -> str:
    if not before.endswith("\n"):
        before += "\n"
    if not after.endswith("\n"):
        after += "\n"
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=from_name,
            tofile=to_name,
        )
    )


def suggest_repair(workflow: Path | str) -> dict[str, Any]:
    """Return a suggested unified diff. Never writes the input workflow (G4)."""
    path = Path(workflow)
    before = path.read_bytes()
    report = check_workflow(path)
    after = path.read_bytes()
    if after != before:
        raise RuntimeError("suggest_repair must not write the workflow YAML")

    document = _load_yaml(path)
    if not isinstance(document, dict):
        raise ValueError("workflow document must be a mapping")
    proposed = _propose_document(document, report["edges"])
    proposed_text = yaml.safe_dump(proposed, sort_keys=False, allow_unicode=True)
    body = _unified_diff(
        path.name,
        f"{path.name}.repair-proposal",
        before.decode("utf-8"),
        proposed_text,
    )
    notes = [
        "# G4: proposal only. Re-run sciguard validate after a human applies this.",
        "# This helper does not write the input file.",
        f"# recheck_unrepaired: {report['graph_status']}",
    ]
    annotations = _annotation_lines(report["edges"])
    if not body.startswith("---"):
        notes = [f"--- {path.name}", f"+++ {path.name}.repair-proposal", *notes]
    parts = ["\n".join(notes), body.rstrip("\n")]
    if annotations:
        parts.append("\n".join(annotations))
    diff = "\n".join(part for part in parts if part) + "\n"

    recheck = check_workflow(path)
    after_recheck = path.read_bytes()
    if after_recheck != before:
        raise RuntimeError("suggest_repair must not write the workflow YAML")

    return {
        "diff": diff,
        "requires_recheck": True,
        "writes_input": False,
        "input_unchanged": after_recheck == before,
        "report": report,
        "recheck": recheck,
    }
