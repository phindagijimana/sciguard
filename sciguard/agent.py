"""Agent call contract. Same function as `sciguard validate`. Not a workflow engine."""

from __future__ import annotations

from typing import Any

from sciguard import validate

TOOLS: list[dict[str, Any]] = [
    {
        "name": "validate",
        "description": (
            "Read-only preflight on workflow edges. "
            "Returns PASS / FAIL / UNKNOWN / NEEDS_REVIEW. "
            "Omitted space is UNKNOWN. Never certifies scientific correctness."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "Path to workflow YAML",
                },
            },
            "required": ["workflow"],
        },
    }
]


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name != "validate":
        raise ValueError(f"unknown tool: {name}")
    return validate(arguments["workflow"])
