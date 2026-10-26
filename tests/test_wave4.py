"""Wave 4: B0/B1 recorded-or-real probes. Repair stays --diff-only. Certificate false."""

from __future__ import annotations

from pathlib import Path

from baselines.bids_b0 import (
    SIDECAR_TREE,
    check_b0,
    pin_status,
    pinned_bids_validator_available,
    probe_b0,
)
from baselines.cwl_types_b1 import (
    check_b1,
    cwltool_installed,
    nipype_installed,
    probe_b1,
)
from validation.check import check_workflow
from validation.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"
OTHER = FIXTURES / "invalid" / "other_subject_transform.yaml"
LINEAR = FIXTURES / "invalid" / "linear_on_labels.yaml"
REVERSED = FIXTURES / "invalid" / "transform_reversed.yaml"
DK_AS_DKT = FIXTURES / "invalid" / "dk_as_dkt.yaml"
ALL_GRAPHS = (VALID, NO_XFM, REVERSED, DK_AS_DKT, SPACE_OMITTED, OTHER, LINEAR)


def _no_nifti_under(tree: Path) -> list[Path]:
    return [
        child
        for child in tree.rglob("*")
        if child.is_file()
        and (
            child.suffix.lower() == ".nii"
            or "".join(child.suffixes[-2:]).lower() == ".nii.gz"
            or child.name.lower().endswith(".nii.gz")
        )
    ]


def test_sidecar_tree_is_json_only_no_nifti() -> None:
    assert SIDECAR_TREE.is_dir()
    assert (SIDECAR_TREE / "dataset_description.json").is_file()
    assert (SIDECAR_TREE / "sub-01" / "anat" / "sub-01_T1w.json").is_file()
    assert _no_nifti_under(SIDECAR_TREE) == []
    assert _no_nifti_under(ROOT / "fixtures") == []


def test_b0_probe_recorded_or_pinned_validator() -> None:
    report = probe_b0()
    pins = pin_status()
    assert report["arm"] == "B0"
    assert report["recorded_pin"] == "3.0.2"
    assert report["checks_dag_edges"] is False
    assert "unsafe_acceptance" not in report
    assert "unsafe_acceptance_rate" not in report
    if pinned_bids_validator_available():
        assert report["baseline_mode"] == "bids-validator"
        assert report["bids_validator_invoked"] is True
        assert report["pin_matched"] is True
        assert report["pin_run_on_input"] is True
        assert report["pin_resolver"] in {"path", "bids-validator-deno"}
        assert report["legacy_node_1150_is_not_the_pin"] is True
    else:
        assert report["baseline_mode"] == "recorded"
        assert report["bids_validator_invoked"] is False
        assert report["pin_run_on_input"] is False
        assert pins["pin_matched"] is False
        if pins.get("path_bids_validator_version") and "1.15.0" in str(
            pins["path_bids_validator_version"]
        ):
            assert pins["path_is_pin"] is False
    assert "RULE-SPACE-002" not in report["rules_fired"]


def test_b0_yaml_graphs_stay_recorded() -> None:
    report = check_b0(NO_XFM)
    assert report["baseline_mode"] == "recorded"
    assert report["bids_validator_invoked"] is False
    assert report["pin_run_on_input"] is False
    assert report["accepted"] is True


def test_b1_probe_recorded_or_cwltool_or_nipype() -> None:
    report = probe_b1()
    assert report["arm"] == "B1"
    assert report["checks_space"] is False
    assert report["file_types_compatible"] is True
    assert report["two_nifti_files_compatible"] is True
    assert "unsafe_acceptance_rate" not in report
    if cwltool_installed():
        assert report["baseline_mode"] == "cwltool"
        assert report["used_cwltool"] is True
    elif nipype_installed():
        assert report["baseline_mode"] == "nipype"
        assert report["used_nipype"] is True
    else:
        assert report["baseline_mode"] == "recorded"
        assert report["used_cwltool"] is False
        assert report["used_nipype"] is False


def test_b1_check_on_no_transform_same_mode() -> None:
    report = check_b1(NO_XFM)
    if cwltool_installed():
        assert report["baseline_mode"] == "cwltool"
    elif nipype_installed():
        assert report["baseline_mode"] == "nipype"
    else:
        assert report["baseline_mode"] == "recorded"
    assert report["accepted"] is True
    assert report["checks_transform_direction"] is False


def test_repair_diff_only_still_does_not_write_input() -> None:
    original = NO_XFM.read_bytes()
    assert main(["repair", "--diff-only", str(NO_XFM)]) == 0
    assert NO_XFM.read_bytes() == original
    assert main(["repair", str(NO_XFM)]) == 2
    assert NO_XFM.read_bytes() == original


def test_certificate_always_false_on_graphs_and_probes() -> None:
    for path in ALL_GRAPHS:
        report = check_workflow(path)
        assert report["certificate_of_scientific_correctness"] is False
        assert report.get("certificate_of_scientific_correctness") is not True
    b0 = probe_b0()
    b1 = probe_b1()
    assert b0.get("certificate_of_scientific_correctness") in {None, False}
    assert b1.get("certificate_of_scientific_correctness") in {None, False}
