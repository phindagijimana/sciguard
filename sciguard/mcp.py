"""Optional stdio MCP transport. Calls sciguard.validate only.

Not a Coala/Nipoppy product. Default path is still `sciguard validate`.
No model API.
"""

from __future__ import annotations

from sciguard import __version__
from sciguard.agent import TOOLS, call_tool
from sciguard.mcp_stdio import handle_message as _handle
from sciguard.mcp_stdio import serve

SERVER = "sciguard"


def handle_message(message: dict) -> dict | None:
    return _handle(
        message,
        name=SERVER,
        version=__version__,
        tools=TOOLS,
        call_tool=call_tool,
    )


def main() -> None:
    serve(name=SERVER, version=__version__, tools=TOOLS, call_tool=call_tool)


if __name__ == "__main__":
    main()
