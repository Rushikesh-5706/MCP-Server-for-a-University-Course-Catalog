"""FastMCP server entrypoint for the University Course Catalog.

Design note: the MCP Python SDK v2 exposes MCPServer (formerly FastMCP in older SDK
versions) directly in mcp.server. This server uses MCPServer with
transport="streamable-http" rather than mounting the MCP app inside a separate
FastAPI/Starlette instance. Mounting via .mount() is a known open bug in older SDK
releases — it breaks routing on the MCP endpoint. Using MCPServer.run() directly
avoids this entirely and is the recommended path for HTTP transport.

The /health route is added with @mcp.custom_route() so it lives on the same
Starlette app that MCPServer manages internally, keeping everything on one port.
"""

from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server import MCPServer

mcp = MCPServer("University Course Catalog")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# Registration is via side-effect: importing these modules calls register_*
# with the mcp instance defined above. The import must happen after `mcp`
# is defined but before mcp.run() is called.
from src.tools import register_tools        # noqa: E402
from src.resources import register_resources  # noqa: E402
from src.prompts import register_prompts    # noqa: E402

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


if __name__ == "__main__":
    from data.seed import ensure_seeded

    ensure_seeded()
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
