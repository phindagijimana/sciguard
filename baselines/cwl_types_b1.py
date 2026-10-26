"""B1 — honest CWL / Nipype File-type check.

CWL SALAD ``File`` and Nipype ``File`` traits accept two NIfTI Files as
compatible (Gorgolewski et al., 2011; Common Workflow Language). File-format
and schema validity are not coordinate-space identity, atlas identity,
transform ``from``/``to``, or label-preserving interpolation.

Semantic types on fully annotated graphs belong to WINGS (Gil et al., 2011),
Kepler OWL (Ratcliffe, Squire, Kearney, 2010), and APE/EDAM (Kasalica &
Lamprecht, 2020). Per-step file-size / RAM / timeout constraints belong to
Schintke et al., FGCS 2024. This residual is File-class compatibility only.

If ``cwltool`` is importable, call its File-type check on a File+File
CommandLineTool (no execute). Else if ``nipype`` is importable, call the
Nipype ``File`` trait. Otherwise keep the recorded File-type contract and
``baseline_mode: recorded``. Do not claim those packages were imported
unless the used_* flag is true.

SciGuard τ (and SciCap node annotations) bind ``space`` / ``atlas`` /
``value_type`` on top of this File class. That is G2, not B1.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any

import yaml

_HERE = Path(__file__).resolve().parents[1]
FILE_PROBE_CWL = _HERE / "fixtures" / "cwl" / "file_types_probe.cwl"

# Residual vs SciGuard (G2): File is File. Transform-effect T is not a CWL type.
SEMANTIC_TYPES_OWNER = (
    "WINGS / Kepler OWL / APE-EDAM own semantic composition; "
    "Schintke VCs own per-step file-size/RAM constraints — not this residual"
)

NIFTI_KINDS = frozenset(
    {"parcellation", "diffusion_reference", "tractogram", "nifti", "image"}
)
FILE_KINDS = NIFTI_KINDS | {"spatial_transform", "file"}
DIRECTORY_KINDS = frozenset({"directory", "Directory"})

# CWL File.format is a hint (often EDAM). Format mismatch is still File vs File
# unless a schema constrains it. Honest B1: two Files are compatible.
CWL_FILE = {"class": "File"}
CWL_NIFTI = {"class": "File", "format": "nifti"}
CWL_TRANSFORM = {"class": "File", "format": "transform"}
CWL_DIRECTORY = {"class": "Directory"}


def cwltool_installed() -> bool:
    return importlib.util.find_spec("cwltool") is not None


def nipype_installed() -> bool:
    return importlib.util.find_spec("nipype") is not None


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _cwl_type(artifact: dict[str, Any]) -> dict[str, str]:
    explicit = artifact.get("cwl_class") or artifact.get("class")
    if isinstance(explicit, str) and explicit in {"File", "Directory"}:
        if explicit == "Directory":
            return dict(CWL_DIRECTORY)
        kind = str(artifact.get("kind") or "").strip().lower()
        if kind in NIFTI_KINDS or artifact.get("format") == "nifti":
            return dict(CWL_NIFTI)
        if kind == "spatial_transform":
            return dict(CWL_TRANSFORM)
        return dict(CWL_FILE)
    kind = str(artifact.get("kind") or "").strip().lower()
    if kind in DIRECTORY_KINDS:
        return dict(CWL_DIRECTORY)
    if kind in NIFTI_KINDS:
        return dict(CWL_NIFTI)
    if kind == "spatial_transform":
        return dict(CWL_TRANSFORM)
    if kind in FILE_KINDS:
        return dict(CWL_FILE)
    # Default neuroimaging artifact on these graphs: File (NIfTI).
    return dict(CWL_NIFTI)


def _compatible(left: dict[str, str], right: dict[str, str]) -> bool:
    """Recorded CWL/Nipype File contract: File accepts File. Directory does not."""
    if left["class"] != right["class"]:
        return False
    return left["class"] == "File"


def _call_cwltool_file_check() -> dict[str, Any] | None:
    """Call installed cwltool File-type validation. None if not importable.

    Loads the File+File probe CWL. Does not execute a command or add an engine.
    """
    if not cwltool_installed():
        return None
    extra: dict[str, Any] = {
        "baseline_mode": "cwltool",
        "used_cwltool": True,
        "cwltool_installed": True,
        "contract": "cwltool-file-type",
    }
    try:
        from cwltool.context import LoadingContext
        from cwltool.load_tool import (
            fetch_document,
            resolve_and_validate_document,
        )

        loading = LoadingContext()
        try:
            loading, _workflowobj, uri = fetch_document(str(FILE_PROBE_CWL), loading)
        except TypeError:
            loading, _workflowobj, uri = fetch_document(
                str(FILE_PROBE_CWL), loadingContext=loading
            )
        try:
            loading, uri = resolve_and_validate_document(loading, _workflowobj, uri)
        except TypeError:
            loading, uri = resolve_and_validate_document(
                loading, _workflowobj, uri=uri
            )
        extra["cwltool_call"] = "cwltool.load_tool.resolve_and_validate_document"
        extra["cwltool_file_tool"] = str(FILE_PROBE_CWL)
        extra["cwltool_uri"] = str(uri)
    except Exception as exc:  # recorded-or-real: keep File-class result
        extra["cwltool_error"] = str(exc)
        extra["cwltool_call"] = "failed"
    return extra


def _call_nipype_file_check() -> dict[str, Any] | None:
    """Call installed Nipype File trait. None if not importable."""
    if not nipype_installed():
        return None
    extra: dict[str, Any] = {
        "baseline_mode": "nipype",
        "used_nipype": True,
        "nipype_installed": True,
        "contract": "nipype-file-trait",
    }
    try:
        from nipype.interfaces.base import File as NipypeFile

        trait = NipypeFile(exists=False)
        extra["nipype_call"] = "nipype.interfaces.base.File"
        extra["nipype_file_trait"] = type(trait).__name__
    except Exception as exc:
        extra["nipype_error"] = str(exc)
        extra["nipype_call"] = "failed"
    return extra


def _artifacts(document: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for edge in document.get("edges") or []:
        if isinstance(edge, dict) and isinstance(edge.get("artifact"), dict):
            found.append(edge["artifact"])
    for node in document.get("nodes") or []:
        if isinstance(node, dict) and isinstance(node.get("artifact"), dict):
            found.append(node["artifact"])
    return found


def check_b1(source: Path | str | dict[str, Any]) -> dict[str, Any]:
    """Apply the B1 CWL/Nipype File-type contract. Never a SciGuard verdict."""
    if isinstance(source, dict):
        document = copy.deepcopy(source)
        path: Path | None = None
    else:
        path = Path(source)
        loaded = _load_yaml(path)
        if not isinstance(loaded, dict):
            raise ValueError("B1 workflow document must be a mapping")
        document = loaded

    typed = [_cwl_type(artifact) for artifact in _artifacts(document)]
    compatible = True
    reasons: list[str] = []
    files = [item for item in typed if item["class"] == "File"]
    directories = [item for item in typed if item["class"] == "Directory"]
    if directories and files:
        compatible = False
        reasons.append("CWL File is not compatible with CWL Directory")
    for i, left in enumerate(typed):
        for right in typed[i + 1 :]:
            if not _compatible(left, right) and left["class"] != right["class"]:
                compatible = False
                reasons.append(
                    f"{left['class']} is not type-compatible with {right['class']}"
                )

    nifti_files = [item for item in typed if item.get("format") == "nifti"]
    two_niftis_ok = len(nifti_files) >= 2 and all(
        _compatible(nifti_files[0], other) for other in nifti_files[1:]
    )

    result = {
        "arm": "B1",
        "tool": "cwl_nipype_file_types",
        "contract": "cwl_salad_file_and_nipype_file",
        "cwltool_installed": cwltool_installed(),
        "nipype_installed": nipype_installed(),
        "used_cwltool": False,
        "used_nipype": False,
        "baseline_mode": "recorded",
        "file_types_compatible": compatible,
        "two_nifti_files_compatible": two_niftis_ok or (
            compatible and len(nifti_files) >= 2
        ),
        "accepted": compatible,
        "types": typed,
        "reasons": reasons,
        "semantic_types_owner": SEMANTIC_TYPES_OWNER,
        "checks_space": False,
        "checks_atlas": False,
        "checks_transform_direction": False,
        "emits_unknown_class": False,
        "source": str(path) if path is not None else None,
        "certificate_of_scientific_correctness": False,
        "note": (
            "Two NIfTI Files are compatible. CWL/Nipype File types do not "
            "check space, atlas, or transform direction. Semantic types are "
            "owned by WINGS/Kepler/APE; this residual is File class only."
        ),
    }
    live = _call_cwltool_file_check()
    if live is None:
        live = _call_nipype_file_check()
    if live:
        result.update(live)
        if result.get("used_cwltool"):
            result["note"] = (
                "Called cwltool File-type check on a File+File CWL tool "
                "(no execute). File still does not check space, atlas, or "
                "transform direction."
            )
        elif result.get("used_nipype"):
            result["note"] = (
                "Called Nipype File trait (exists=False). File still does "
                "not check space, atlas, or transform direction."
            )
    result["certificate_of_scientific_correctness"] = False
    return result


def probe_b1(source: Path | str | dict[str, Any] | None = None) -> dict[str, Any]:
    """B1 probe: cwltool File-type check if importable, else Nipype, else recorded."""
    if source is None:
        source = {
            "edges": [
                {"artifact": {"kind": "parcellation"}},
                {"artifact": {"kind": "diffusion_reference"}},
            ]
        }
    return check_b1(source)
