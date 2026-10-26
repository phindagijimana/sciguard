"""Wave 5: pin is BIDS Validator 3.0.2. Live B1 if cwltool. Repair --diff-only.

Node 1.15.0 on PATH is not the pin. Certificate stays false. No Z3. No LLM.
"""

from __future__ import annotations

from pathlib import Path

from baselines.bids_b0 import (
    NODE_LEGACY_NOT_THE_PIN,
    SIDECAR_TREE,
    check_b0,
    pin_status,
    pinned_bids_validator_available,
    pinned_bids_validator_on_path,
    pinned_bids_validator_version,
    probe_b0,
)
from baselines.cwl_types_b1 import check_b1, cwltool_installed, probe_b1
from validation.check import check_workflow
from validation.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"
REVERSED = FIXTURES / "invalid" / "transform_reversed.yaml"
DK_AS_DKT = FIXTURES / "invalid" / "dk_as_dkt.yaml"
OTHER = FIXTURES / "invalid" / "other_subject_transform.yaml"
LINEAR = FIXTURES / "invalid" / "linear_on_labels.yaml"
ALL_GRAPHS = (VALID, NO_XFM, REVERSED, DK_AS_DKT, SPACE_OMITTED, OTHER, LINEAR)


def test_pin_is_302_not_node_1150() -> None:
    assert pinned_bids_validator_version() == "3.0.2"
    pins = pin_status()
    assert pins["recorded_pin"] == "3.0.2"
    assert pins["legacy_node_1150_is_not_the_pin"] is True
    path_ver = str(pins.get("path_bids_validator_version") or "")
    if NODE_LEGACY_NOT_THE_PIN in path_ver:
        assert pins["path_is_pin"] is False
        assert pinned_bids_validator_on_path() is False


def test_b0_probe_live_pin_or_recorded_pin_miss() -> None:
    report = probe_b0()
    assert report["arm"] == "B0"
    assert report["recorded_pin"] == "3.0.2"
    assert report["certificate_of_scientific_correctness"] is False
    assert report["checks_dag_edges"] is False
    assert "RULE-SPACE-002" not in report["rules_fired"]
    assert "unsafe_acceptance_rate" not in report
    path_ver = str(report.get("path_bids_validator_version") or "")
    if NODE_LEGACY_NOT_THE_PIN in path_ver:
        assert report["path_is_pin"] is False
        invoked = str(report.get("pin_binary") or "")
        assert "1.15.0" not in invoked
        assert Path(invoked).name != "bids-validator" or report["path_is_pin"]
    if pinned_bids_validator_available():
        assert report["baseline_mode"] == "bids-validator"
        assert report["bids_validator_invoked"] is True
        assert report["pin_matched"] is True
        assert report["pin_miss"] is False
        assert report["pin_run_on_input"] is True
        assert report["pin_resolver"] in {"path", "bids-validator-deno"}
        assert "3.0.2" in str(report["bids_validator_version"])
        assert "1.15.0" not in str(report.get("pin_resolver") or "")
    else:
        assert report["baseline_mode"] == "recorded"
        assert report["bids_validator_invoked"] is False
        assert report["pin_run_on_input"] is False
        assert report["pin_miss"] is True
        assert report["pin_miss_reason"]
        assert "1.15.0 is not the pin" in report["pin_miss_reason"] or "not the pin" in (
            report["pin_miss_reason"] or ""
        )


def test_b0_yaml_graphs_stay_recorded_even_when_pin_live() -> None:
    report = check_b0(NO_XFM)
    assert report["baseline_mode"] == "recorded"
    assert report["bids_validator_invoked"] is False
    assert report["pin_run_on_input"] is False
    assert report["accepted"] is True
    assert report["certificate_of_scientific_correctness"] is False


def test_b1_live_cwltool_or_recorded() -> None:
    report = probe_b1()
    assert report["arm"] == "B1"
    assert report["certificate_of_scientific_correctness"] is False
    assert report["file_types_compatible"] is True
    assert report["checks_space"] is False
    if cwltool_installed():
        assert report["baseline_mode"] == "cwltool"
        assert report["used_cwltool"] is True
        assert "cwltool" in str(report.get("cwltool_call") or report["contract"])
    else:
        assert report["baseline_mode"] in {"nipype", "recorded"}
        assert report["used_cwltool"] is False
    graph = check_b1(NO_XFM)
    if cwltool_installed():
        assert graph["baseline_mode"] == "cwltool"
    assert graph["accepted"] is True
    assert graph["certificate_of_scientific_correctness"] is False


def test_repair_diff_only_never_writes_input() -> None:
    for fixture in (NO_XFM, OTHER, LINEAR):
        original = fixture.read_bytes()
        assert main(["repair", "--diff-only", str(fixture)]) == 0
        assert fixture.read_bytes() == original
        assert main(["repair", str(fixture)]) == 2
        assert fixture.read_bytes() == original
        assert main(["repair", "--diff-only", str(fixture), "--report", str(fixture)]) == 2
        assert fixture.read_bytes() == original


def test_certificate_always_false_no_z3_no_llm() -> None:
    for path in ALL_GRAPHS:
        report = check_workflow(path)
        assert report["certificate_of_scientific_correctness"] is False
        assert report["auto_accepted"] is False
    b0 = probe_b0()
    b1 = probe_b1()
    assert b0["certificate_of_scientific_correctness"] is False
    assert b1["certificate_of_scientific_correctness"] is False
    tree = Path(__file__).resolve().parents[1]
    for rel in (
        "validation/check.py",
        "validation/cli.py",
        "baselines/bids_b0.py",
        "baselines/cwl_types_b1.py",
    ):
        text = (tree / rel).read_text(encoding="utf-8")
        assert "import z3" not in text
        assert "from z3" not in text
        assert "llm_reviewer" not in text
        assert "def review_with_llm" not in text
    assert SIDECAR_TREE.is_dir()
    assert not any(
        child.name.lower().endswith((".nii", ".nii.gz"))
        for child in SIDECAR_TREE.rglob("*")
        if child.is_file()
    )
