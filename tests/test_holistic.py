"""Same five graphs through B0/B1 and sciguard validate. No certificate. No model API."""

from __future__ import annotations

from pathlib import Path

from baselines.bids_b0 import check_b0
from baselines.cwl_types_b1 import check_b1
from validation.check import check_workflow
from validation.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"

VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
REVERSED = FIXTURES / "invalid" / "transform_reversed.yaml"
DK_AS_DKT = FIXTURES / "invalid" / "dk_as_dkt.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"
FIVE = (VALID, NO_XFM, REVERSED, DK_AS_DKT, SPACE_OMITTED)


def _by_rule(report: dict, rule: str) -> list[dict]:
    return [item for item in report["edges"] if item["rule"] == rule]


def _b0_silent_on_edges(report: dict) -> None:
    assert report["checks_dag_edges"] is False
    assert report["checks_transform_direction"] is False
    assert report["checks_atlas_identity"] is False
    assert report["emits_unknown_class"] is False
    assert "RULE-SPACE-002" not in report["rules_fired"]
    assert "RULE-XFM-DIR" not in report["rules_fired"]
    assert "RULE-ATLAS" not in report["rules_fired"]
    assert not any("UNKNOWN" == item.get("status") for item in report["findings"])


def test_valid_dkt_to_dwi_b0_b1_accept_sciguard_no_fail_not_certificate() -> None:
    b0 = check_b0(VALID)
    b1 = check_b1(VALID)
    sci = check_workflow(VALID)
    assert b0["accepted"] is True
    _b0_silent_on_edges(b0)
    assert b1["file_types_compatible"] is True
    assert b1["accepted"] is True
    assert not any(item["status"] == "FAIL" for item in sci["edges"])
    assert sci["certificate_of_scientific_correctness"] is False
    assert sci["auto_accepted"] is False
    assert sci["graph_status"] in {"eligible", "not_auto_accepted"}


def test_no_transform_b0_not_space002_b1_file_ok_sciguard_fail() -> None:
    b0 = check_b0(NO_XFM)
    b1 = check_b1(NO_XFM)
    sci = check_workflow(NO_XFM)
    _b0_silent_on_edges(b0)
    assert b0["accepted"] is True
    assert not any("SPACE-002" in str(item) for item in b0["findings"])
    assert b1["file_types_compatible"] is True
    assert b1["two_nifti_files_compatible"] is True
    space = _by_rule(sci, "RULE-SPACE-002")
    assert space
    assert any(item["status"] == "FAIL" for item in space)
    assert sci["graph_status"] == "reject"
    assert sci["certificate_of_scientific_correctness"] is False


def test_space_omitted_b0_no_unknown_class_sciguard_unknown_not_accepted() -> None:
    b0 = check_b0(SPACE_OMITTED)
    b1 = check_b1(SPACE_OMITTED)
    sci = check_workflow(SPACE_OMITTED)
    _b0_silent_on_edges(b0)
    assert b0["emits_unknown_class"] is False
    assert b1["emits_unknown_class"] is False
    space = _by_rule(sci, "RULE-SPACE-002")
    assert space
    assert all(item["status"] == "UNKNOWN" for item in space)
    assert not any(item["status"] == "FAIL" for item in sci["edges"])
    assert sci["auto_accepted"] is False
    assert sci["graph_status"] == "not_auto_accepted"
    assert sci["certificate_of_scientific_correctness"] is False


def test_transform_reversed_b0_b1_silent_sciguard_xfm_dir() -> None:
    b0 = check_b0(REVERSED)
    b1 = check_b1(REVERSED)
    sci = check_workflow(REVERSED)
    _b0_silent_on_edges(b0)
    assert b0["accepted"] is True
    assert b1["file_types_compatible"] is True
    xfm = _by_rule(sci, "RULE-XFM-DIR")
    assert xfm
    assert any(item["status"] == "FAIL" for item in xfm)
    assert any("reversed" in item["reason"] for item in xfm)
    assert sci["graph_status"] == "reject"
    assert sci["certificate_of_scientific_correctness"] is False


def test_dk_as_dkt_b0_b1_silent_if_filenames_ok_sciguard_atlas() -> None:
    b0 = check_b0(DK_AS_DKT)
    b1 = check_b1(DK_AS_DKT)
    sci = check_workflow(DK_AS_DKT)
    _b0_silent_on_edges(b0)
    assert b0["accepted"] is True
    assert b1["file_types_compatible"] is True
    atlas = _by_rule(sci, "RULE-ATLAS")
    assert atlas
    assert any(item["status"] == "FAIL" for item in atlas)
    assert sci["graph_status"] == "reject"
    assert sci["certificate_of_scientific_correctness"] is False


def test_certificate_false_and_cli_on_same_five_graphs() -> None:
    for path in FIVE:
        b0 = check_b0(path)
        b1 = check_b1(path)
        sci = check_workflow(path)
        assert sci["certificate_of_scientific_correctness"] is False
        assert b0["arm"] == "B0"
        assert b1["arm"] == "B1"
        assert "unsafe_acceptance_rate" not in b0
        assert "unsafe_acceptance_rate" not in b1
        assert main(["validate", str(path)]) == 0
