"""Wave 3 slice: G3 fixtures, second contract, repair --diff-only, B0 pin.

Keeps wave 1–2 gold. Certificate stays false. Omitted space stays UNKNOWN.
No unsafe-acceptance number. No model API.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from baselines.bids_b0 import check_b0, pinned_bids_validator_version
from validation.check import check_workflow, suggest_repair
from validation.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
CONTRACTS = ROOT / "contracts"

VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
OTHER = FIXTURES / "invalid" / "other_subject_transform.yaml"
LINEAR = FIXTURES / "invalid" / "linear_on_labels.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"
RESAMPLE = CONTRACTS / "resample_discrete_labels.yaml"


def _by_rule(report: dict, rule: str) -> list[dict]:
    return [item for item in report["edges"] if item["rule"] == rule]


def test_other_subject_transform_fail_lineage() -> None:
    report = check_workflow(OTHER)
    assert report["certificate_of_scientific_correctness"] is False
    assert report["auto_accepted"] is False
    assert report["graph_status"] == "reject"
    lineage = _by_rule(report, "RULE-LINEAGE")
    assert lineage
    assert any(item["status"] == "FAIL" for item in lineage)


def test_linear_on_labels_fail_or_needs_review_interp() -> None:
    report = check_workflow(LINEAR)
    assert report["certificate_of_scientific_correctness"] is False
    assert report["auto_accepted"] is False
    interp = _by_rule(report, "RULE-INTERP")
    assert interp
    assert any(item["status"] in {"FAIL", "NEEDS_REVIEW"} for item in interp)
    assert report["graph_status"] == "reject"


def test_second_contract_resample_requires_nearest_and_fires_interp() -> None:
    assert RESAMPLE.is_file()
    contract = yaml.safe_load(RESAMPLE.read_text(encoding="utf-8"))
    assert isinstance(contract, dict)
    assert contract.get("operation") == "resample_discrete_labels"
    blob = yaml.safe_dump(contract).lower()
    assert "nearest" in blob
    document = yaml.safe_load(LINEAR.read_text(encoding="utf-8"))
    assert document["operations"][0]["contract"] == "resample_discrete_labels"
    report = check_workflow(LINEAR)
    assert _by_rule(report, "RULE-INTERP")
    assert _by_rule(report, "RULE-LINEAGE")


def test_other_subject_fires_rule_lineage() -> None:
    report = check_workflow(OTHER)
    assert _by_rule(report, "RULE-LINEAGE")
    assert any(item["status"] == "FAIL" for item in _by_rule(report, "RULE-LINEAGE"))


def test_repair_diff_only_does_not_write_input_recheck_still_fail(
    tmp_path: Path, capsys
) -> None:
    for fixture in (NO_XFM, OTHER, LINEAR):
        original = fixture.read_bytes()
        sink = tmp_path / f"{fixture.stem}.repair.diff"
        assert main(["repair", "--diff-only", str(fixture), "--report", str(sink)]) == 0
        assert fixture.read_bytes() == original
        captured = capsys.readouterr()
        assert "---" in captured.out
        assert "+++" in captured.out
        assert sink.is_file()
        assert sink.read_bytes() != original
        recheck = check_workflow(fixture)
        assert recheck["graph_status"] == "reject"
        assert recheck["certificate_of_scientific_correctness"] is False
        assert fixture.read_bytes() == original


def test_repair_helper_and_cli_leave_other_subject_bytes_unchanged() -> None:
    original = OTHER.read_bytes()
    proposal = suggest_repair(OTHER)
    assert OTHER.read_bytes() == original
    assert proposal["writes_input"] is False
    assert proposal["input_unchanged"] is True
    assert proposal["recheck"]["graph_status"] == "reject"
    assert "subject" in proposal["diff"] or "LINEAGE" in proposal["diff"] or "same_subject" in proposal["diff"]


def test_repair_refuses_to_write_input_path() -> None:
    original = LINEAR.read_bytes()
    assert main(["repair", "--diff-only", str(LINEAR), "--report", str(LINEAR)]) == 2
    assert LINEAR.read_bytes() == original


def test_repair_without_diff_only_does_not_write_input() -> None:
    original = OTHER.read_bytes()
    assert main(["repair", str(OTHER)]) == 2
    assert OTHER.read_bytes() == original


def test_certificate_false_and_omitted_space_still_unknown() -> None:
    omitted = check_workflow(SPACE_OMITTED)
    assert omitted["certificate_of_scientific_correctness"] is False
    assert omitted["auto_accepted"] is False
    space = _by_rule(omitted, "RULE-SPACE-002")
    assert space
    assert all(item["status"] == "UNKNOWN" for item in space)
    assert not any(item["status"] == "FAIL" for item in omitted["edges"])
    assert omitted["graph_status"] == "not_auto_accepted"
    for path in (VALID, OTHER, LINEAR, NO_XFM):
        report = check_workflow(path)
        assert report["certificate_of_scientific_correctness"] is False
        assert "unsafe_acceptance_rate" not in report


def test_b0_pin_vs_shared_302_not_run_on_yaml_graphs() -> None:
    assert pinned_bids_validator_version() == "3.0.2"
    report = check_b0(OTHER)
    assert report["recorded_pin"] == "3.0.2"
    assert report["pin_run_on_input"] is False
    assert report["bids_validator_invoked"] is False
    if report["bids_validator_installed"]:
        installed = str(report["bids_validator_version"] or "")
        if "3.0.2" in installed:
            assert report["pin_matched"] is True
        else:
            assert report["pin_matched"] is False
    else:
        assert report["pin_matched"] is False
    assert "unsafe_acceptance" not in report
    assert "unsafe_acceptance_rate" not in report
    assert "3.0.2 pin was not run" in report["note"] or "not run" in report["note"]
