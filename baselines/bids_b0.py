"""B0 — BIDS Validator as a filename / sidecar checker.

Recorded contract (Gorgolewski et al., 2016; BIDS specification; BIDS
Validator FAQ): dataset layout, filename entity/suffix/extension rules, and
sidecar schema. The ``space-``, ``tpl-``, and ``atlas-`` entities are naming
and sidecar rules. Nonstandard template spaces may require SpatialReference.

This arm does **not** evaluate DAG edges, transform ``from``/``to``, or atlas
identity (DK used as DKT). It has **no** ``UNKNOWN`` class for a missing
scientific field on an edge. It never emits ``RULE-SPACE-002``.

If ``bids-validator`` is on PATH and the input is a BIDS dataset directory,
call that binary. SciGuard workflow YAML graphs are not BIDS datasets; those
use the recorded contract only. The shared pin is BIDS Validator 3.0.2; do
not claim that pin was executed unless the invoked CLI reports it.

Do not report an unsafe-acceptance rate from this module. B0 is wired so
that number can be computed later on the same graphs.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

# Residual vs SciGuard (G1/G2): BIDS Validator is not an edge checker and
# does not define UNKNOWN for omitted space. See docs/METHODS_TRACE.md.
RECORDED_PIN = "3.0.2"
_SHARED_PINS = Path(__file__).resolve().parents[2] / "shared" / "pins.yaml"
_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+)")
SCIGUARD_EDGE_RULES = (
    "RULE-SPACE-002",
    "RULE-XFM-DIR",
    "RULE-ATLAS",
    "RULE-INTERP",
    "RULE-LINEAGE",
)
UNKNOWN_CLASS = "UNKNOWN"

_ENTITY_RE = re.compile(r"^([a-zA-Z0-9]+)-([a-zA-Z0-9+]+)$")
_SUFFIX_EXT_RE = re.compile(
    r"^(?P<stem>.+)_(?P<suffix>[a-zA-Z0-9]+)(?P<ext>\.[a-zA-Z0-9.]+)$"
)
_KNOWN_SUFFIX = {
    "T1w",
    "T2w",
    "dwi",
    "bold",
    "dseg",
    "probseg",
    "xfm",
    "mask",
    "events",
}
_KNOWN_EXT = {
    ".nii.gz",
    ".nii",
    ".json",
    ".tsv",
    ".bval",
    ".bvec",
    ".txt",
    ".h5",
    ".mat",
    ".lta",
}
_PATH_KEYS = ("path", "filename", "bids_name", "bids_path")


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def bids_validator_on_path() -> str | None:
    return shutil.which("bids-validator")


def pinned_bids_validator_version() -> str:
    """Pin from shared/pins.yaml; fall back to the recorded 3.0.2 string."""
    if _SHARED_PINS.is_file():
        loaded = yaml.safe_load(_SHARED_PINS.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and loaded.get("bids_validator"):
            return str(loaded["bids_validator"])
    return RECORDED_PIN


def _normalize_version(text: str | None) -> str | None:
    if not text:
        return None
    match = _VERSION_RE.search(text)
    return match.group(1) if match else text.strip() or None


def bids_validator_version() -> str | None:
    binary = bids_validator_on_path()
    if binary is None:
        return None
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError:
        return None
    text = (proc.stdout or proc.stderr or "").strip()
    return text or None


def pin_status() -> dict[str, Any]:
    """Record installed bids-validator vs pin 3.0.2. Not an unsafe-acceptance rate."""
    pin = pinned_bids_validator_version()
    raw = bids_validator_version()
    installed = _normalize_version(raw)
    matched = installed is not None and installed == pin
    return {
        "recorded_pin": pin,
        "bids_validator_installed": bids_validator_on_path() is not None,
        "bids_validator_version": raw,
        "pin_matched": matched,
        "pin_run_on_input": False,
    }


def _finding(code: str, severity: str, message: str) -> dict[str, Any]:
    """BIDS-style finding. Never a SciGuard status or rule id."""
    return {"code": code, "severity": severity, "message": message}


def _empty_report(**overrides: Any) -> dict[str, Any]:
    pins = pin_status()
    report: dict[str, Any] = {
        "arm": "B0",
        "tool": "bids-validator",
        "contract": "filename_and_sidecar_schema",
        "recorded_pin": pins["recorded_pin"],
        "bids_validator_installed": pins["bids_validator_installed"],
        "bids_validator_invoked": False,
        "bids_validator_version": pins["bids_validator_version"],
        "pin_matched": pins["pin_matched"],
        "pin_run_on_input": False,
        "dataset_present": False,
        "accepted": True,
        "findings": [],
        "rules_fired": [],
        "emits_unknown_class": False,
        "checks_dag_edges": False,
        "checks_transform_direction": False,
        "checks_atlas_identity": False,
        "note": (
            "BIDS Validator checks dataset layout and sidecar schema, not "
            "DAG edges, transform direction, or atlas identity."
        ),
    }
    report.update(overrides)
    return report


def _check_bids_filename(name: str) -> list[dict[str, Any]]:
    """Recorded filename contract. space- is optional. No UNKNOWN class."""
    findings: list[dict[str, Any]] = []
    base = Path(name).name
    if any(ch.isspace() for ch in base) or "!" in base:
        findings.append(
            _finding("FILENAME", "error", f"illegal BIDS filename characters: {base}")
        )
        return findings
    parsed = _SUFFIX_EXT_RE.match(base)
    if parsed is None:
        findings.append(
            _finding("FILENAME", "error", f"not a BIDS suffix/extension name: {base}")
        )
        return findings
    suffix = parsed.group("suffix")
    ext = parsed.group("ext")
    stem = parsed.group("stem")
    if suffix not in _KNOWN_SUFFIX:
        findings.append(
            _finding("FILENAME", "error", f"unrecognized BIDS suffix {suffix!r} in {base}")
        )
    if ext not in _KNOWN_EXT:
        findings.append(
            _finding("FILENAME", "error", f"unrecognized BIDS extension {ext!r} in {base}")
        )
    for token in stem.split("_"):
        if token == "":
            findings.append(_finding("FILENAME", "error", f"empty entity in {base}"))
            continue
        match = _ENTITY_RE.match(token)
        if match is None:
            findings.append(
                _finding("FILENAME", "error", f"illegal BIDS entity token {token!r} in {base}")
            )
            continue
        key, label = match.group(1), match.group(2)
        if label == "":
            findings.append(
                _finding("FILENAME", "error", f"empty {key}- label in {base}")
            )
    return findings


def _check_sidecar(sidecar: dict[str, Any], source: str) -> list[dict[str, Any]]:
    """Sidecar types only. Missing space is not UNKNOWN and not an error."""
    findings: list[dict[str, Any]] = []
    for key in ("space", "Space", "SpatialReference", "atlas", "Atlas"):
        if key not in sidecar:
            continue
        value = sidecar[key]
        if value is not None and not isinstance(value, str):
            findings.append(
                _finding(
                    "SIDECAR",
                    "error",
                    f"{key} in {source} must be a string under the BIDS sidecar contract",
                )
            )
    generated = sidecar.get("GeneratedBy")
    if generated is not None and not isinstance(generated, list):
        findings.append(
            _finding(
                "SIDECAR",
                "error",
                f"GeneratedBy in {source} must be an array (BIDS Derivatives)",
            )
        )
    return findings


def _artifacts_from_workflow(document: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for edge in document.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        artifact = edge.get("artifact")
        if isinstance(artifact, dict):
            artifacts.append(artifact)
    for node in document.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        artifact = node.get("artifact")
        if isinstance(artifact, dict):
            artifacts.append(artifact)
    return artifacts


def _contract_on_artifacts(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Filename/sidecar checks only. Do not inspect edge pairs."""
    findings: list[dict[str, Any]] = []
    for artifact in _artifacts_from_workflow(document):
        for key in _PATH_KEYS:
            if key in artifact and isinstance(artifact[key], str) and artifact[key]:
                findings.extend(_check_bids_filename(artifact[key]))
        sidecar = artifact.get("sidecar")
        if isinstance(sidecar, dict):
            findings.extend(_check_sidecar(sidecar, "artifact.sidecar"))
        # Declared τ fields (space, atlas, from_space, label_table) are not
        # BIDS filename entities unless they appear in a path. Do not score
        # them. Do not emit UNKNOWN when space is absent.
    return findings


def _run_bids_validator(dataset: Path) -> dict[str, Any]:
    binary = bids_validator_on_path()
    if binary is None:
        raise RuntimeError("bids-validator is not on PATH")
    proc = subprocess.run(
        [binary, str(dataset), "--json", "--ignoreNiftiHeaders"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    payload: Any = None
    for blob in (proc.stdout, proc.stderr):
        if not blob:
            continue
        try:
            payload = json.loads(blob)
            break
        except json.JSONDecodeError:
            continue
    findings: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        issues = payload.get("issues")
        if isinstance(issues, dict):
            for severity, key in (("error", "errors"), ("warning", "warnings")):
                for item in issues.get(key) or []:
                    if not isinstance(item, dict):
                        continue
                    findings.append(
                        _finding(
                            str(item.get("key") or item.get("code") or "BIDS"),
                            severity,
                            str(item.get("reason") or item.get("message") or item),
                        )
                    )
    elif proc.returncode != 0:
        findings.append(
            _finding(
                "BIDS_VALIDATOR",
                "error",
                (proc.stderr or proc.stdout or "bids-validator failed").strip()[:500],
            )
        )
    accepted = not any(item["severity"] == "error" for item in findings)
    pins = pin_status()
    return _empty_report(
        bids_validator_invoked=True,
        bids_validator_version=pins["bids_validator_version"],
        pin_matched=pins["pin_matched"],
        pin_run_on_input=bool(pins["pin_matched"]),
        dataset_present=True,
        accepted=accepted,
        findings=findings,
        note=(
            "Invoked bids-validator on a BIDS dataset directory. "
            "This is still layout/sidecar conformance, not DAG-edge checking. "
            "pin_run_on_input is true only when the invoked binary matches "
            "shared/pins.yaml 3.0.2."
        ),
    )


def check_b0(source: Path | str | dict[str, Any]) -> dict[str, Any]:
    """Apply the B0 BIDS Validator contract. Never a SciGuard verdict."""
    if isinstance(source, dict):
        document = copy.deepcopy(source)
        findings = _contract_on_artifacts(document)
        return _empty_report(
            accepted=not any(item["severity"] == "error" for item in findings),
            findings=findings,
        note=(
            "Workflow mapping is not a BIDS dataset. Applied the recorded "
            "filename/sidecar contract only. DAG edges were not evaluated. "
            "The 3.0.2 pin was not run on this YAML graph."
        ),
        )

    path = Path(source)
    if path.is_dir() and (path / "dataset_description.json").is_file():
        if bids_validator_on_path() is not None:
            return _run_bids_validator(path)
        findings: list[dict[str, Any]] = []
        desc = json.loads((path / "dataset_description.json").read_text(encoding="utf-8"))
        if not isinstance(desc, dict) or not desc.get("Name") or not desc.get("BIDSVersion"):
            findings.append(
                _finding(
                    "DATASET_DESCRIPTION",
                    "error",
                    "dataset_description.json must declare Name and BIDSVersion",
                )
            )
        for child in path.rglob("*"):
            if child.is_file() and child.name.endswith((".nii", ".nii.gz", ".tsv", ".json")):
                if child.name == "dataset_description.json":
                    continue
                findings.extend(_check_bids_filename(child.name))
        return _empty_report(
            dataset_present=True,
            accepted=not any(item["severity"] == "error" for item in findings),
            findings=findings,
            note=(
                "BIDS dataset directory; bids-validator not on PATH. "
                "Applied the recorded layout/sidecar contract."
            ),
        )

    document = _load_yaml(path)
    if not isinstance(document, dict):
        raise ValueError("B0 workflow document must be a mapping")
    findings = _contract_on_artifacts(document)
    return _empty_report(
        accepted=not any(item["severity"] == "error" for item in findings),
        findings=findings,
        source=str(path),
        note=(
            "Workflow YAML is not a BIDS dataset. Applied the recorded "
            "filename/sidecar contract. BIDS Validator does not evaluate "
            "DAG edges, transform direction, or atlas identity, and has no "
            "UNKNOWN class for omitted space. The 3.0.2 pin was not run "
            "on this YAML graph."
        ),
    )
