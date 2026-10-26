"""Stdlib JSON-RPC stdio helper. Copied per package so installs stay independent."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

PROTOCOL_VERSION = "2024-11-05"
CallTool = Callable[[str, dict[str, Any]], Any]


def handle_message(
    message: dict[str, Any],
    *,
    name: str,
    version: str,
    tools: list[dict[str, Any]],
    call_tool: CallTool,
) -> dict[str, Any] | None:
    mid = message.get("id")
    method = message.get("method")
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "initialize":
        return _ok(
            mid,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": name, "version": version},
            },
        )
    if method == "tools/list":
        return _ok(mid, {"tools": tools})
    if method == "tools/call":
        params = message.get("params") or {}
        tool = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            result = call_tool(str(tool), dict(arguments))
            return _ok(
                mid,
                {
                    "content": [
                        {"type": "text", "text": json.dumps(result, default=str)}
                    ],
                    "isError": False,
                },
            )
        except Exception as exc:
            return _ok(
                mid,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
    if method == "ping":
        return _ok(mid, {})
    return {
        "jsonrpc": "2.0",
        "id": mid,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def serve(
    *,
    name: str,
    version: str,
    tools: list[dict[str, Any]],
    call_tool: CallTool,
) -> None:
    stdin = sys.stdin
    while True:
        message = _read_message(stdin)
        if message is None:
            return
        reply = handle_message(
            message,
            name=name,
            version=version,
            tools=tools,
            call_tool=call_tool,
        )
        if reply is not None:
            _write_message(sys.stdout, reply)


def _ok(mid: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _read_message(stdin) -> dict[str, Any] | None:
    header: dict[str, str] = {}
    while True:
        line = stdin.readline()
        if line == "":
            return None
        stripped = line.rstrip("\r\n")
        if stripped.startswith("{"):
            return json.loads(stripped)
        if stripped == "":
            break
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            header[key.strip().lower()] = value.strip()
    length = int(header.get("content-length") or "0")
    body = stdin.read(length)
    if not body:
        return None
    return json.loads(body)


def _write_message(stdout, message: dict[str, Any]) -> None:
    body = json.dumps(message, separators=(",", ":"))
    stdout.write(f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}")
    stdout.flush()
