"""Locked G1–G5 methods. Cite literature residuals. No model API. No G6."""

from __future__ import annotations

from pathlib import Path

from baselines.bids_b0 import check_b0
from validation.check import MISSING, check_workflow, normalize_tau

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"

VALID = FIXTURES / "valid" / "dkt_to_dwi_with_transform.yaml"
NO_XFM = FIXTURES / "invalid" / "labels_t1w_to_dwi_no_transform.yaml"
REVERSED = FIXTURES / "invalid" / "transform_reversed.yaml"
DK_AS_DKT = FIXTURES / "invalid" / "dk_as_dkt.yaml"
SPACE_OMITTED = FIXTURES / "unknown" / "space_omitted.yaml"


def _by_rule(report: dict, rule: str) -> list[dict]:
    return [item for item in report["edges"] if item["rule"] == rule]


def test_g2_transform_effect_rewrites_space_preserves_atlas_and_value_type() -> None:
    """G2: effect T may rewrite space; must preserve atlas and value_type."""
    report = check_workflow(VALID)
    assert report["propagated"]
    tau = report["propagated"][0]["tau"]
    assert tau["space"] == "subject_DWI"
    assert tau["atlas"] == "DesikanKillianyTourville"
    assert tau["value_type"] == "discrete_labels"
    interp = _by_rule(report, "RULE-INTERP")
    assert interp
    assert all(item["status"] == "PASS" for item in interp)


def test_g2_never_infers_omitted_space() -> None:
    """G2: normalize declared τ. Absent field stays unknown. Never infer."""
    tau = normalize_tau({"kind": "parcellation", "atlas": "DesikanKilliany"})
    assert tau["space"] is MISSING or tau["space"] == MISSING
    assert tau["kind"] == "parcellation"
    omitted = check_workflow(SPACE_OMITTED)
    space = _by_rule(omitted, "RULE-SPACE-002")
    assert space
    assert all(item["status"] == "UNKNOWN" for item in space)
    assert not any(item["status"] == "FAIL" for item in omitted["edges"])


def test_g2_no_transform_does_not_rewrite_space() -> None:
    """Without a validated chain, T does not rewrite labels into DWI space."""
    report = check_workflow(NO_XFM)
    assert report["propagated"]
    tau = report["propagated"][0]["tau"]
    assert tau["space"] == "subject_T1w"
    assert tau["atlas"] == "DesikanKilliany"
    assert tau["value_type"] == "discrete_labels"
    space = _by_rule(report, "RULE-SPACE-002")
    assert any(item["status"] == "FAIL" for item in space)


def test_g3_corpus_split_exists_no_unsafe_acceptance_rate() -> None:
    """G3: valid / invalid / unknown fixtures kept. Primary number is later."""
    assert VALID.is_file()
    assert NO_XFM.is_file()
    assert REVERSED.is_file()
    assert DK_AS_DKT.is_file()
    assert SPACE_OMITTED.is_file()
    b0 = check_b0(NO_XFM)
    sci = check_workflow(NO_XFM)
    assert b0["accepted"] is True
    assert sci["graph_status"] == "reject"
    assert "unsafe_acceptance" not in b0
    assert "unsafe_acceptance_rate" not in b0
    assert "unsafe_acceptance_rate" not in sci


def test_g3_wave3_other_subject_and_linear_fixtures_exist() -> None:
    """G3 mutation family: other-subject transform; linear interpolation on labels."""
    other = FIXTURES / "invalid" / "other_subject_transform.yaml"
    linear = FIXTURES / "invalid" / "linear_on_labels.yaml"
    assert other.is_file()
    assert linear.is_file()
    other_report = check_workflow(other)
    linear_report = check_workflow(linear)
    assert any(item["rule"] == "RULE-LINEAGE" and item["status"] == "FAIL" for item in other_report["edges"])
    assert any(
        item["rule"] == "RULE-INTERP" and item["status"] in {"FAIL", "NEEDS_REVIEW"}
        for item in linear_report["edges"]
    )
    assert "unsafe_acceptance_rate" not in other_report
    assert "unsafe_acceptance_rate" not in linear_report


def test_g5_certificate_always_false_on_locked_methods() -> None:
    """G5: scoped soundness only. No scientific-correctness certificate."""
    for path in (VALID, NO_XFM, REVERSED, DK_AS_DKT, SPACE_OMITTED):
        report = check_workflow(path)
        assert report["certificate_of_scientific_correctness"] is False
        assert report["auto_accepted"] is False
