"""sciguard CLI. Offline. No model API. Does not execute the DAG."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from baselines.bids_b0 import probe_b0, probe_b0_s0
from validation.check import check_workflow, suggest_repair


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sciguard",
        description="Read-only preflight checker for neuroimaging workflow edges.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="evaluate a declared workflow DAG")
    validate.add_argument("workflow", type=Path, help="workflow YAML")
    validate.add_argument(
        "--report",
        type=Path,
        default=None,
        help="optional JSON report path (does not write the workflow)",
    )
    repair = sub.add_parser(
        "repair",
        help="emit a G4 unified diff; never writes the input YAML",
    )
    repair.add_argument("workflow", type=Path, help="workflow YAML (read-only)")
    repair.add_argument(
        "--diff-only",
        action="store_true",
        help="required: print a unified diff; do not write the input file",
    )
    repair.add_argument(
        "--report",
        type=Path,
        default=None,
        help="optional path for the diff (use reports/; never the input YAML)",
    )
    b0 = sub.add_parser(
        "b0",
        help="B0 BIDS Validator probe (layout/sidecar; not SciGuard edges)",
    )
    b0.add_argument(
        "--s0",
        action="store_true",
        help=(
            "point at shared/data/external/ds000003 if a real gzip T1w is "
            "present (never copy NIfTI)"
        ),
    )
    b0.add_argument(
        "--report",
        type=Path,
        default=None,
        help="optional JSON report path",
    )
    return parser


def validate_command(workflow: Path, report: Path | None) -> int:
    result = check_workflow(workflow)
    text = json.dumps(result, indent=2, sort_keys=False)
    print(text)
    if report is not None:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text + "\n", encoding="utf-8")
    return 0


def _refuse_if_input_target(workflow: Path, target: Path | None) -> bool:
    if target is None:
        return False
    try:
        return target.resolve() == workflow.resolve()
    except OSError:
        return False


def repair_command(
    workflow: Path,
    diff_only: bool,
    report: Path | None,
) -> int:
    if not diff_only:
        print(
            "sciguard repair requires --diff-only (G4: never write the input YAML)",
            file=sys.stderr,
        )
        return 2
    if _refuse_if_input_target(workflow, report):
        print("refusing to write the input YAML", file=sys.stderr)
        return 2

    before = workflow.read_bytes()
    proposal = suggest_repair(workflow)
    if workflow.read_bytes() != before:
        raise RuntimeError("repair --diff-only must not write the input YAML")

    recheck = proposal.get("recheck") or check_workflow(workflow)
    if workflow.read_bytes() != before:
        raise RuntimeError("repair --diff-only must not write the input YAML")

    text = proposal["diff"]
    if not text.endswith("\n"):
        text += "\n"
    print(text, end="")

    if report is not None:
        if _refuse_if_input_target(workflow, report):
            print("refusing to write the input YAML", file=sys.stderr)
            return 2
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text, encoding="utf-8")

    if workflow.read_bytes() != before:
        raise RuntimeError("repair --diff-only must not write the input YAML")
    if recheck.get("graph_status") == "reject":
        return 0
    return 0


def b0_command(*, s0: bool, report: Path | None) -> int:
    """Print the B0 probe. Never a scientific-correctness certificate."""
    result = probe_b0_s0() if s0 else probe_b0()
    result["certificate_of_scientific_correctness"] = False
    text = json.dumps(result, indent=2, sort_keys=False)
    print(text)
    if report is not None:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate_command(args.workflow, args.report)
    if args.command == "repair":
        return repair_command(args.workflow, args.diff_only, args.report)
    if args.command == "b0":
        return b0_command(s0=args.s0, report=args.report)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
