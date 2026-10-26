"""Wave 6: live B0 on S0 when a real gzip T1w is present. No NIfTI copy.

Node 1.15.0 is not the pin. Certificate stays false. Repair stays --diff-only.
FAIL on no-transform; UNKNOWN on omitted space. Do not invent PASS.
"""

from __future__ import annotations

import json
from pathlib import Path

from baselines.bids_b0 import (
    NODE_LEGACY_NOT_THE_PIN,
    S0_TREE,
    SIDECAR_TREE,
    pin_status,
    pinned_bids_validator_available,
    probe_b0,
    probe_b0_s0,
    s0_tree_status,
)
from validation.check import check_workflow
from validation.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"
VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
PYTEST_YML = ROOT / ".github" / "workflows" / "pytest.yml"


def _nifti_under(tree: Path) -> list[Path]:
    hits: list[Path] = []
    if not tree.is_dir():
        return hits
    for child in tree.rglob("*"):
        if not child.is_file():
            continue
        name = child.name.lower()
        if name.endswith(".nii") or name.endswith(".nii.gz"):
            hits.append(child)
    return hits


def _by_rule(report: dict, rule: str) -> list[dict]:
    return [item for item in report["edges"] if item["rule"] == rule]


def test_no_nifti_copied_into_sciguard() -> None:
    assert _nifti_under(ROOT) == []
    assert _nifti_under(FIXTURES) == []
    assert not (ROOT / "data" / "external").exists()
    assert not (ROOT / "ds000003").exists()
    assert "shared/data/external" in str(S0_TREE)
    assert "02_SciGuard" not in S0_TREE.parts or S0_TREE.parts[-4:] == (
        "shared",
        "data",
        "external",
        "ds000003",
    )


def test_pytest_yml_kept_fails_on_nifti_in_git() -> None:
    assert PYTEST_YML.is_file()
    text = PYTEST_YML.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in text
    assert "nii" in text.lower()
    assert "pytest" in text


def test_sidecar_probe_still_json_only() -> None:
    assert SIDECAR_TREE.is_dir()
    assert _nifti_under(SIDECAR_TREE) == []
    report = probe_b0()
    assert report["arm"] == "B0"
    assert report["certificate_of_scientific_correctness"] is False
    assert report["checks_dag_edges"] is False


def test_labels_no_transform_still_fail() -> None:
    report = check_workflow(NO_XFM)
    space = _by_rule(report, "RULE-SPACE-002")
    assert space
    assert any(item["status"] == "FAIL" for item in space)
    assert report["graph_status"] == "reject"
    assert report["certificate_of_scientific_correctness"] is False
    assert report["auto_accepted"] is False


def test_omitted_space_still_unknown() -> None:
    report = check_workflow(SPACE_OMITTED)
    space = _by_rule(report, "RULE-SPACE-002")
    assert space
    assert all(item["status"] == "UNKNOWN" for item in space)
    assert not any(item["status"] == "FAIL" for item in report["edges"])
    assert report["graph_status"] == "not_auto_accepted"
    assert report["auto_accepted"] is False
    assert report["certificate_of_scientific_correctness"] is False


def test_repair_diff_only_never_writes_input() -> None:
    original = NO_XFM.read_bytes()
    assert main(["repair", "--diff-only", str(NO_XFM)]) == 0
    assert NO_XFM.read_bytes() == original
    assert main(["repair", str(NO_XFM)]) == 2
    assert NO_XFM.read_bytes() == original


def test_certificate_always_false() -> None:
    for path in (VALID, NO_XFM, SPACE_OMITTED):
        report = check_workflow(path)
        assert report["certificate_of_scientific_correctness"] is False
    b0 = probe_b0_s0()
    assert b0["certificate_of_scientific_correctness"] is False


def test_b0_on_s0_live_or_honest_skip() -> None:
    """Record the pin on S0. Do not invent PASS. Do not copy bytes."""
    status = s0_tree_status()
    report = probe_b0_s0()
    assert report["arm"] == "B0"
    assert report["recorded_pin"] == "3.0.2"
    assert report["copied_s0"] is False
    assert report["bytes_in_git"] is False
    assert report["download_in_pytest"] is False
    assert report["certificate_of_scientific_correctness"] is False
    assert report["checks_dag_edges"] is False
    assert "RULE-SPACE-002" not in report["rules_fired"]
    assert "unsafe_acceptance_rate" not in report
    assert report["legacy_node_1150_is_not_the_pin"] is True
    path_ver = str(pin_status().get("path_bids_validator_version") or "")
    if NODE_LEGACY_NOT_THE_PIN in path_ver:
        invoked = str(report.get("pin_binary") or "")
        assert "1.15.0" not in invoked
        assert Path(invoked).name != "bids-validator" or report.get("path_is_pin")

    live = (
        status["tree_present"]
        and status["t1w_real_gzip"]
        and pinned_bids_validator_available()
    )
    if live:
        assert report["baseline_mode"] == "bids-validator"
        assert report["bids_validator_invoked"] is True
        assert report["pin_matched"] is True
        assert report["pin_run_on_input"] is True
        assert report["pin_resolver"] in {"path", "bids-validator-deno"}
        assert "3.0.2" in str(report["bids_validator_version"])
        errors = [item for item in report["findings"] if item["severity"] == "error"]
        assert report["accepted"] is (len(errors) == 0)
        # Observed on this OpenNeuro snapshot: Funding must be array.
        # Record that. Do not rewrite accepted to True.
        funding = [
            item
            for item in errors
            if item.get("code") == "JSON_SCHEMA_VALIDATION_ERROR"
            and (
                item.get("sub_code") == "Funding"
                or "Funding" in str(item)
                or "must be array" in str(item.get("message") or "")
            )
        ]
        if funding:
            assert report["accepted"] is False
        assert report["accepted"] is not True or not errors
    else:
        assert report["baseline_mode"] == "skipped"
        assert report["bids_validator_invoked"] is False
        assert report["pin_run_on_input"] is False
        assert report["accepted"] is False
        assert report.get("skip_reason")


def test_cli_b0_s0_does_not_copy_or_certify(tmp_path: Path, capsys) -> None:
    sink = tmp_path / "b0-s0.json"
    assert main(["b0", "--s0", "--report", str(sink)]) == 0
    payload = json.loads(sink.read_text(encoding="utf-8"))
    assert payload["certificate_of_scientific_correctness"] is False
    assert payload["copied_s0"] is False
    captured = capsys.readouterr()
    assert "certificate_of_scientific_correctness" in captured.out
    assert _nifti_under(ROOT) == []
