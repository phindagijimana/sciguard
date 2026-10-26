"""Honest B0 / B1 public comparators. No unsafe-acceptance number. No model API."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from baselines.bids_b0 import check_b0
from baselines.cwl_types_b1 import SEMANTIC_TYPES_OWNER, check_b1

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_b0_does_not_emit_space002_on_labels_to_dwi_no_transform() -> None:
    """B0 is not an edge checker. labels→DWI without a transform is silent."""
    report = check_b0(NO_XFM)
    assert report["arm"] == "B0"
    assert report["checks_dag_edges"] is False
    assert report["emits_unknown_class"] is False
    assert "RULE-SPACE-002" not in report["rules_fired"]
    assert not any(
        item.get("rule") == "RULE-SPACE-002" or item.get("code") == "RULE-SPACE-002"
        for item in report["findings"]
    )
    assert not any("SPACE-002" in str(item) for item in report["findings"])
    assert report["accepted"] is True
    assert "unsafe_acceptance" not in report
    assert "unsafe_acceptance_rate" not in report


def test_b1_file_types_accept_two_niftis_on_no_transform_graph() -> None:
    """CWL/Nipype File: two NIfTIs are compatible. Not a semantic type check."""
    report = check_b1(NO_XFM)
    assert report["arm"] == "B1"
    assert report["used_cwltool"] is False
    assert report["used_nipype"] is False
    assert report["file_types_compatible"] is True
    assert report["two_nifti_files_compatible"] is True
    assert report["accepted"] is True
    assert report["checks_space"] is False
    assert "WINGS" in SEMANTIC_TYPES_OWNER
    assert "APE" in SEMANTIC_TYPES_OWNER
    assert "Schintke" in SEMANTIC_TYPES_OWNER
    nifti = [item for item in report["types"] if item.get("format") == "nifti"]
    assert len(nifti) >= 2
    assert all(item["class"] == "File" for item in nifti)


def test_b0_does_not_emit_unknown_for_omitted_space_on_an_edge() -> None:
    """Omitted space is not a native BIDS Validator UNKNOWN class."""
    report = check_b0(SPACE_OMITTED)
    assert report["emits_unknown_class"] is False
    assert "UNKNOWN" not in {item.get("severity") for item in report["findings"]}
    assert "UNKNOWN" not in {item.get("status") for item in report["findings"]}
    assert "UNKNOWN" not in {item.get("code") for item in report["findings"]}
    assert report["accepted"] is True
    assert "unsafe_acceptance_rate" not in report


def test_b0_is_not_a_strawman_rejects_illegal_bids_filename() -> None:
    """Filename/sidecar contract still fires when a BIDS path is present."""
    document = _load(NO_XFM)
    document = copy.deepcopy(document)
    document["edges"][0]["artifact"]["path"] = "not a bids name!!!.foo"
    report = check_b0(document)
    assert report["accepted"] is False
    assert report["checks_dag_edges"] is False
    assert any(item["code"] == "FILENAME" for item in report["findings"])
    assert "RULE-SPACE-002" not in report["rules_fired"]


def test_b0_version_pin_matched_false_when_binary_differs_from_302() -> None:
    """If bids-validator is on PATH, record version vs shared/pins.yaml 3.0.2."""
    from baselines.bids_b0 import pinned_bids_validator_version

    assert pinned_bids_validator_version() == "3.0.2"
    report = check_b0(NO_XFM)
    assert report["recorded_pin"] == "3.0.2"
    assert report["pin_run_on_input"] is False
    assert report["bids_validator_invoked"] is False
    if not report["bids_validator_installed"]:
        assert report["pin_matched"] is False
    elif report["bids_validator_version"] and "3.0.2" not in str(
        report["bids_validator_version"]
    ):
        assert report["pin_matched"] is False
    assert "unsafe_acceptance" not in report
    assert "unsafe_acceptance_rate" not in report


def test_b1_is_not_a_strawman_rejects_file_vs_directory() -> None:
    """CWL File vs Directory is a real native-type mismatch."""
    document = _load(NO_XFM)
    document = copy.deepcopy(document)
    document["edges"][1]["artifact"]["cwl_class"] = "Directory"
    report = check_b1(document)
    assert report["file_types_compatible"] is False
    assert report["accepted"] is False
    assert report["checks_space"] is False
