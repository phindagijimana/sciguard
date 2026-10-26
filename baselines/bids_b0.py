"""B0 — BIDS Validator as a filename / sidecar checker.

Recorded contract (Gorgolewski et al., 2016; BIDS specification; BIDS
Validator FAQ): dataset layout, filename entity/suffix/extension rules, and
sidecar schema. The ``space-``, ``tpl-``, and ``atlas-`` entities are naming
and sidecar rules. Nonstandard template spaces may require SpatialReference.

This arm does **not** evaluate DAG edges, transform ``from``/``to``, or atlas
identity (DK used as DKT). It has **no** ``UNKNOWN`` class for a missing
scientific field on an edge. It never emits ``RULE-SPACE-002``.

If pinned BIDS Validator **3.0.2** is available — PATH ``bids-validator``
whose version is 3.0.2, or ``bids-validator-deno`` 3.0.2 (PyPI / Deno
bundle) — the B0 probe invokes that pin on the JSON/sidecar tree (no
NIfTI). When ``shared/data/external/ds000003/`` is present with a real
gzip T1w (magic ``\\x1f\\x8b``, not a git-annex pointer), ``probe_b0_s0``
invokes the same pin on that tree. The tree is **not copied** into this
folder. A Node ``1.15.0`` binary on PATH is **not** the pin and is never
invoked. SciGuard workflow YAML graphs are not BIDS datasets; those stay
``baseline_mode: recorded``. Do not claim the pin was executed unless the
invoked CLI matches 3.0.2. Do not invent PASS when the pin reports a
schema error.

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
NODE_LEGACY_NOT_THE_PIN = "1.15.0"
_HERE = Path(__file__).resolve().parents[1]
_SHARED_PINS = Path(__file__).resolve().parents[2] / "shared" / "pins.yaml"
SIDECAR_TREE = _HERE / "fixtures" / "sidecar_tree"
S0_TREE = _HERE.parent / "shared" / "data" / "external" / "ds000003"
S0_T1W = S0_TREE / "sub-01" / "anat" / "sub-01_T1w.nii.gz"
S0_ACCESSION = "ds000003"
GZIP_MAGIC = b"\x1f\x8b"
_ANNEX_POINTER_BYTES = 1024
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


def _version_text(binary: str) -> str | None:
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


def bids_validator_version() -> str | None:
    """PATH ``bids-validator --version`` only. 1.15.0 here is not the pin."""
    binary = bids_validator_on_path()
    if binary is None:
        return None
    return _version_text(binary)


def _path_is_pin(path_norm: str | None, pin: str) -> bool:
    return bool(
        path_norm
        and path_norm == pin
        and path_norm != NODE_LEGACY_NOT_THE_PIN
    )


def _find_pinned_binary() -> tuple[str | None, str | None, str | None]:
    """Return (binary, raw version, resolver) only for pin 3.0.2.

    Never returns the Node 1.15.0 ``bids-validator`` on PATH.
    """
    pin = pinned_bids_validator_version()
    path_bin = bids_validator_on_path()
    if path_bin:
        raw = _version_text(path_bin)
        if _path_is_pin(_normalize_version(raw), pin):
            return path_bin, raw, "path"
    deno_bin = shutil.which("bids-validator-deno")
    if deno_bin:
        raw = _version_text(deno_bin)
        if _normalize_version(raw) == pin:
            return deno_bin, raw, "bids-validator-deno"
    return None, None, None


def pin_status() -> dict[str, Any]:
    """Record installed validator vs pin 3.0.2. Not an unsafe-acceptance rate."""
    pin = pinned_bids_validator_version()
    path_bin = bids_validator_on_path()
    path_raw = _version_text(path_bin) if path_bin else None
    path_norm = _normalize_version(path_raw)
    pinned_bin, pinned_raw, resolver = _find_pinned_binary()
    matched = pinned_bin is not None
    path_legacy = path_norm == NODE_LEGACY_NOT_THE_PIN
    reason = None
    if not matched:
        if path_legacy:
            reason = (
                "PATH bids-validator is 1.15.0; pin is 3.0.2 (Deno/JSR / "
                "bids-validator-deno). 1.15.0 is not the pin. B0 stays recorded."
            )
        elif path_bin:
            reason = (
                f"PATH bids-validator is {path_norm or path_raw!r}; pin is {pin}. "
                "A Node 1.15.0 binary is not the pin. B0 stays recorded."
            )
        else:
            reason = (
                f"Pinned bids-validator {pin} not available. B0 stays recorded."
            )
    return {
        "recorded_pin": pin,
        "bids_validator_installed": path_bin is not None or pinned_bin is not None,
        "bids_validator_version": pinned_raw or path_raw,
        "path_bids_validator": path_bin,
        "path_bids_validator_version": path_raw,
        "path_is_pin": _path_is_pin(path_norm, pin),
        "pin_binary": pinned_bin,
        "pin_resolver": resolver,
        "pin_matched": matched,
        "pin_miss": not matched,
        "pin_miss_reason": reason,
        "pin_run_on_input": False,
        "legacy_node_1150_is_not_the_pin": True,
    }


def pinned_bids_validator_on_path() -> bool:
    """True only when PATH ``bids-validator`` itself is the 3.0.2 pin."""
    return bool(pin_status()["path_is_pin"])


def pinned_bids_validator_available() -> bool:
    """True when pin 3.0.2 can be invoked (PATH or bids-validator-deno)."""
    return bool(pin_status()["pin_matched"])


def _is_real_gzip_t1w(path: Path) -> bool:
    """True only for a gzip NIfTI. Reject git-annex / LFS pointer stubs."""
    try:
        if not path.is_file() or path.stat().st_size < _ANNEX_POINTER_BYTES:
            return False
        head = path.read_bytes()[:4]
    except OSError:
        return False
    return head.startswith(GZIP_MAGIC)


def s0_tree_status() -> dict[str, Any]:
    """Point at shared S0. Never download. Never copy NIfTI into this folder."""
    desc = S0_TREE / "dataset_description.json"
    t1w = S0_T1W
    desc_present = desc.is_file()
    t1w_present = t1w.is_file()
    real_gzip = _is_real_gzip_t1w(t1w)
    annex = False
    if t1w_present and not real_gzip:
        try:
            blob = t1w.read_bytes()[:200]
        except OSError:
            blob = b""
        annex = (
            t1w.stat().st_size < _ANNEX_POINTER_BYTES
            or blob.startswith(b"..")
            or blob.startswith(b"/annex")
            or b"git-annex" in blob
        )
    if not S0_TREE.is_dir() or not desc_present:
        reason = (
            "shared/data/external/ds000003 is absent; pytest does not "
            "download; B0-on-S0 skipped"
        )
    elif not t1w_present:
        reason = (
            "S0 dataset_description.json is present but T1w is missing; "
            "B0-on-S0 skipped"
        )
    elif not real_gzip:
        reason = (
            "S0 T1w is not real gzip (annex pointer or other stub); "
            "treat as absent"
        )
    else:
        reason = (
            "public T1w present under shared/data/external/ds000003 "
            "(gzip); not copied into 02_SciGuard"
        )
    return {
        "accession": S0_ACCESSION,
        "path": str(S0_TREE),
        "t1w": str(t1w),
        "tree_present": S0_TREE.is_dir() and desc_present,
        "desc_present": desc_present,
        "t1w_present": t1w_present,
        "t1w_real_gzip": real_gzip,
        "t1w_annex_pointer": annex,
        "t1w_bytes": t1w.stat().st_size if t1w_present else 0,
        "bytes_in_git": False,
        "copied_s0": False,
        "download_in_pytest": False,
        "reason": reason,
    }


def _finding(
    code: str,
    severity: str,
    message: str,
    *,
    sub_code: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """BIDS-style finding. Never a SciGuard status or rule id."""
    row: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    if sub_code:
        row["sub_code"] = sub_code
    if location:
        row["location"] = location
    return row


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
        "path_bids_validator": pins["path_bids_validator"],
        "path_bids_validator_version": pins["path_bids_validator_version"],
        "path_is_pin": pins["path_is_pin"],
        "pin_binary": pins["pin_binary"],
        "pin_resolver": pins["pin_resolver"],
        "pin_matched": pins["pin_matched"],
        "pin_miss": pins["pin_miss"],
        "pin_miss_reason": pins["pin_miss_reason"],
        "pin_run_on_input": False,
        "legacy_node_1150_is_not_the_pin": True,
        "baseline_mode": "recorded",
        "dataset_present": False,
        "accepted": True,
        "findings": [],
        "rules_fired": [],
        "emits_unknown_class": False,
        "checks_dag_edges": False,
        "checks_transform_direction": False,
        "checks_atlas_identity": False,
        "certificate_of_scientific_correctness": False,
        "note": (
            "BIDS Validator checks dataset layout and sidecar schema, not "
            "DAG edges, transform direction, or atlas identity."
        ),
    }
    report.update(overrides)
    report["certificate_of_scientific_correctness"] = False
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


def _parse_validator_payload(payload: Any) -> list[dict[str, Any]]:
    """Parse BIDS Validator 3.x issues.issues and legacy errors/warnings."""
    findings: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return findings
    issues = payload.get("issues")
    if not isinstance(issues, dict):
        return findings
    items = issues.get("issues")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            findings.append(
                _finding(
                    str(item.get("code") or item.get("key") or "BIDS"),
                    str(item.get("severity") or "warning"),
                    str(
                        item.get("issueMessage")
                        or item.get("reason")
                        or item.get("message")
                        or item
                    ),
                    sub_code=(
                        str(item["subCode"]) if item.get("subCode") else None
                    ),
                    location=(
                        str(item["location"]) if item.get("location") else None
                    ),
                )
            )
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
    return findings


def _tree_has_real_gzip_nifti(path: Path) -> bool:
    for child in path.rglob("*"):
        name = child.name.lower()
        if child.is_file() and (name.endswith(".nii.gz") or name.endswith(".nii")):
            if _is_real_gzip_t1w(child) or (
                name.endswith(".nii") and child.stat().st_size >= _ANNEX_POINTER_BYTES
            ):
                return True
    return False


def _run_bids_validator(
    dataset: Path, *, ignore_nifti_headers: bool | None = None
) -> dict[str, Any]:
    pins = pin_status()
    binary = pins["pin_binary"]
    if binary is None:
        raise RuntimeError("pinned bids-validator 3.0.2 is not available")
    invoked_version = _normalize_version(_version_text(binary))
    if invoked_version == NODE_LEGACY_NOT_THE_PIN or invoked_version != pins[
        "recorded_pin"
    ]:
        raise RuntimeError(
            f"refusing to invoke {binary!r} as the pin "
            f"(version {invoked_version!r}; pin is {pins['recorded_pin']})"
        )
    if ignore_nifti_headers is None:
        ignore_nifti_headers = not _tree_has_real_gzip_nifti(dataset)
    argv = [binary, str(dataset)]
    if ignore_nifti_headers:
        argv.append("--ignoreNiftiHeaders")
    if pins["pin_resolver"] == "bids-validator-deno":
        argv.append("--format")
        argv.append("json")
    else:
        argv.append("--json")
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=120,
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
    findings = _parse_validator_payload(payload)
    if payload is None and proc.returncode != 0:
        findings.append(
            _finding(
                "BIDS_VALIDATOR",
                "error",
                (proc.stderr or proc.stdout or "bids-validator failed").strip()[:500],
            )
        )
    accepted = not any(item["severity"] == "error" for item in findings)
    return _empty_report(
        tool=Path(binary).name,
        bids_validator_invoked=True,
        bids_validator_version=pins["bids_validator_version"],
        pin_matched=True,
        pin_miss=False,
        pin_run_on_input=True,
        pin_binary=binary,
        pin_resolver=pins["pin_resolver"],
        baseline_mode="bids-validator",
        dataset_present=True,
        accepted=accepted,
        findings=findings,
        ignore_nifti_headers=ignore_nifti_headers,
        validator_argv=argv,
        note=(
            f"Invoked pin {pins['recorded_pin']} via {pins['pin_resolver']} "
            f"({binary}). This is still layout/sidecar conformance, not "
            "DAG-edge checking. PATH Node 1.15.0 was not invoked. "
            "accepted reflects validator errors only; not a scientific PASS."
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
        if pinned_bids_validator_available():
            return _run_bids_validator(
                path,
                ignore_nifti_headers=not _tree_has_real_gzip_nifti(path),
            )
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
                if child.suffix == ".json":
                    try:
                        sidecar = json.loads(child.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        findings.append(
                            _finding("SIDECAR", "error", f"invalid JSON sidecar: {child.name}")
                        )
                        continue
                    if isinstance(sidecar, dict):
                        findings.extend(_check_sidecar(sidecar, child.name))
        pins = pin_status()
        note = pins["pin_miss_reason"] or (
            "BIDS sidecar tree; pinned bids-validator 3.0.2 not available. "
            "Applied the recorded layout/sidecar contract. A Node 1.15.0 "
            "binary is not the pin."
        )
        return _empty_report(
            dataset_present=True,
            baseline_mode="recorded",
            accepted=not any(item["severity"] == "error" for item in findings),
            findings=findings,
            note=note,
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


def probe_b0(tree: Path | str | None = None) -> dict[str, Any]:
    """B0 probe on a JSON/sidecar tree (no NIfTI).

    If pinned BIDS Validator 3.0.2 is available, invoke it. Else recorded
    filename/sidecar contract and ``baseline_mode: recorded``. Node 1.15.0
    on PATH is not the pin.
    """
    target = Path(tree) if tree is not None else SIDECAR_TREE
    if not target.is_dir():
        raise FileNotFoundError(f"B0 sidecar tree missing: {target}")
    if any(
        child.is_file()
        and (
            child.suffix.lower() == ".nii"
            or "".join(child.suffixes[-2:]).lower() == ".nii.gz"
            or child.name.lower().endswith(".nii.gz")
        )
        for child in target.rglob("*")
    ):
        raise ValueError("B0 sidecar tree must not contain NIfTI bytes")
    return check_b0(target)


def probe_b0_s0() -> dict[str, Any]:
    """Live B0 on shared S0 when a real gzip T1w is present.

    Points at ``shared/data/external/ds000003/``. Never copies NIfTI.
    Never downloads. Node 1.15.0 is not invoked. Do not invent PASS:
    if the pin reports a schema error, ``accepted`` stays false.
    """
    status = s0_tree_status()
    extras: dict[str, Any] = {
        "s0_accession": status["accession"],
        "s0_path": status["path"],
        "s0_present": status["tree_present"],
        "t1w_path": status["t1w"],
        "t1w_present": status["t1w_present"],
        "t1w_real_gzip": status["t1w_real_gzip"],
        "t1w_annex_pointer": status["t1w_annex_pointer"],
        "t1w_bytes": status["t1w_bytes"],
        "copied_s0": False,
        "bytes_in_git": False,
        "download_in_pytest": False,
        "checks_dag_edges": False,
    }
    if not status["tree_present"] or not status["t1w_real_gzip"]:
        return _empty_report(
            baseline_mode="skipped",
            skip_reason=status["reason"],
            accepted=False,
            dataset_present=status["tree_present"],
            **extras,
            note=(
                f"{status['reason']}. Not a fabricated PASS. "
                "B0-on-S0 did not run."
            ),
        )
    if not pinned_bids_validator_available():
        pins = pin_status()
        reason = pins["pin_miss_reason"] or (
            "Pinned bids-validator 3.0.2 not available. Live B0 on S0 "
            "not run; not a fabricated PASS. A Node 1.15.0 binary is "
            "not the pin."
        )
        return _empty_report(
            dataset_present=True,
            baseline_mode="skipped",
            skip_reason=reason,
            accepted=False,
            **extras,
            note=reason,
        )
    report = _run_bids_validator(S0_TREE, ignore_nifti_headers=False)
    report.update(extras)
    report["skip_reason"] = None
    errors = [item for item in report["findings"] if item["severity"] == "error"]
    report["accepted"] = not errors
    report["certificate_of_scientific_correctness"] = False
    report["note"] = (
        f"Live B0 on shared S0 {S0_TREE} via pin {report['recorded_pin']} "
        f"({report.get('pin_resolver')}; {report.get('pin_binary')}). "
        "Not copied into 02_SciGuard. Layout/sidecar conformance only; "
        "not DAG-edge checking. PATH Node 1.15.0 was not invoked. "
        "accepted is false if the pin reported any error — do not "
        "rewrite that as PASS."
    )
    return report
