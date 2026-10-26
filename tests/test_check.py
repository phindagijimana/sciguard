"""Five gold fixtures. No model API. Omitted space is UNKNOWN, not FAIL."""

from __future__ import annotations

import json
from pathlib import Path

from validation.check import check_workflow, suggest_repair
from validation.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"

VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
REVERSED = FIXTURES / "invalid" / "transform_reversed.yaml"
DK_AS_DKT = FIXTURES / "invalid" / "dk_as_dkt.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"


def _by_rule(report: dict, rule: str) -> list[dict]:
    return [item for item in report["edges"] if item["rule"] == rule]


def test_valid_dkt_to_dwi_no_fail_space_pass() -> None:
    report = check_workflow(VALID)
    assert report["certificate_of_scientific_correctness"] is False
    assert report["auto_accepted"] is False
    assert report["graph_status"] in {"eligible", "not_auto_accepted"}
    assert not any(item["status"] == "FAIL" for item in report["edges"])
    space = _by_rule(report, "RULE-SPACE-002")
    assert space
    assert all(item["status"] == "PASS" for item in space)


def test_labels_t1w_to_dwi_no_transform_fail() -> None:
    report = check_workflow(NO_XFM)
    assert report["graph_status"] == "reject"
    assert report["certificate_of_scientific_correctness"] is False
    space = _by_rule(report, "RULE-SPACE-002")
    assert space
    assert any(item["status"] == "FAIL" for item in space)
    assert any("no transform" in item["reason"] for item in space)


def test_space_omitted_is_unknown_not_fail() -> None:
    report = check_workflow(SPACE_OMITTED)
    assert report["auto_accepted"] is False
    assert report["certificate_of_scientific_correctness"] is False
    space = _by_rule(report, "RULE-SPACE-002")
    assert space
    assert all(item["status"] == "UNKNOWN" for item in space)
    assert not any(item["status"] == "FAIL" for item in space)
    assert not any(
        item["status"] == "FAIL" for item in report["edges"]
    ), "omitted space must not become a graph FAIL"
    assert report["graph_status"] == "not_auto_accepted"


def test_transform_reversed_fail() -> None:
    report = check_workflow(REVERSED)
    assert report["graph_status"] == "reject"
    xfm = _by_rule(report, "RULE-XFM-DIR")
    assert xfm
    assert any(item["status"] == "FAIL" for item in xfm)
    assert any("reversed" in item["reason"] for item in xfm)


def test_dk_declared_as_dkt_fail() -> None:
    report = check_workflow(DK_AS_DKT)
    assert report["graph_status"] == "reject"
    atlas = _by_rule(report, "RULE-ATLAS")
    assert atlas
    assert any(item["status"] == "FAIL" for item in atlas)


def test_certificate_never_true_on_five_fixtures() -> None:
    for path in (VALID, NO_XFM, REVERSED, DK_AS_DKT, SPACE_OMITTED):
        report = check_workflow(path)
        assert report["certificate_of_scientific_correctness"] is False


def test_repair_helper_does_not_write_input_yaml() -> None:
    original = NO_XFM.read_bytes()
    proposal = suggest_repair(NO_XFM)
    assert NO_XFM.read_bytes() == original
    assert proposal["writes_input"] is False
    assert proposal["requires_recheck"] is True
    assert "spatial_transform" in proposal["diff"]


def test_cli_validate_stdout_and_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    assert main(["validate", str(NO_XFM), "--report", str(report_path)]) == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["graph_status"] == "reject"
    assert payload["certificate_of_scientific_correctness"] is False
    assert NO_XFM.read_bytes()  # input still present; CLI writes report only
