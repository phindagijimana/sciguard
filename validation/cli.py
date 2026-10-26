"""sciguard CLI. Offline. No model API. Does not execute the DAG."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate_command(args.workflow, args.report)
    if args.command == "repair":
        return repair_command(args.workflow, args.diff_only, args.report)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
