"""FastMCP server entrypoint for the University Course Catalog.

Design note: The server uses FastMCP directly rather than mounting it inside
a separate FastAPI application. Mounting via FastAPI's .mount() is a known
open bug in the MCP Python SDK — it breaks routing on the MCP endpoint.
Using FastMCP's own run(transport="streamable-http") avoids this entirely
and is the recommended path for HTTP transport.

The /health route is added with @mcp.custom_route() so it lives on the same
Starlette app that FastMCP manages internally, keeping everything on one port.
"""

import os
import sys

# Ensure the repo root is on sys.path so `src` and `data` are importable
# whether the script is invoked as `python src/main.py` or as a module.
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("University Course Catalog", host="0.0.0.0", port=8080)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# Registration is via side-effect: importing these modules calls register_*
# with the mcp instance defined above. The import must happen after `mcp`
# is defined but before mcp.run() is called.
from src.tools import register_tools          # noqa: E402
from src.resources import register_resources  # noqa: E402
from src.prompts import register_prompts      # noqa: E402

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


if __name__ == "__main__":
    from data.seed import ensure_seeded

    ensure_seeded()
    mcp.run(transport="streamable-http")
