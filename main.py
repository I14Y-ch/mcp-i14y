"""mcp-i14y — MCP server for the Swiss I14Y Interoperability Platform."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from mcp.server.transport_security import TransportSecuritySettings

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from helpers.env_config import get_server_host, get_server_port
from tools import register_tools

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Sentry (optional) ─────────────────────────────────────────────────────────
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=float(os.getenv("SENTRY_SAMPLE_RATE", "0.1")),
    )
    logger.info("Sentry error tracking enabled.")

# ── MCP Server ─────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "mcp-i14y",
    instructions=(
        "You are connected to the Swiss I14Y Interoperability Platform. "
        "Use the available tools to list and retrieve datasets, data services, "
        "concepts (codelists), public services, and catalogs published by Swiss "
        "federal and cantonal bodies. All data is returned in the language(s) "
        "available on the platform (DE, FR, IT, EN)."
    ),
    host="0.0.0.0",
    port=get_server_port(),
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "mcp.i14y.d.c.bfs.admin.ch",
            "mcp.i14y.d.c.bfs.admin.ch:443",
            "ca-iop-mcp.livelybeach-69b99234.switzerlandnorth.azurecontainerapps.io",
            "ca-iop-mcp.livelybeach-69b99234.switzerlandnorth.azurecontainerapps.io:443",
            "localhost",
            "localhost:*",
            "127.0.0.1",
            "127.0.0.1:*",
        ],
        allowed_origins=[
            "https://mcp.i14y.d.c.bfs.admin.ch",
            "https://ca-iop-mcp.livelybeach-69b99234.switzerlandnorth.azurecontainerapps.io",
            "http://localhost:*",
            "http://127.0.0.1:*",
        ],
    ),
)
register_tools(mcp)


# ── Health endpoint ────────────────────────────────────────────────────────────
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "platform": "i14y", "version": "0.1.0"})

async def test(request: Request) -> JSONResponse:
    return JSONResponse({"test":"ok"})


# ── Accept header compatibility middleware ─────────────────────────────────────
class MCPAcceptPatchMiddleware:
    """Patch Accept header for /mcp requests to satisfy FastMCP's strict validation.

    Claude Code VS Code extension sends only 'Accept: application/json'.
    FastMCP 1.26+ requires both 'application/json' and 'text/event-stream'.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("path", "").startswith("/mcp"):
            headers = list(scope["headers"])
            for i, (k, v) in enumerate(headers):
                if k.lower() == b"accept":
                    decoded = v.decode()
                    if "text/event-stream" not in decoded:
                        headers[i] = (k, (decoded + ", text/event-stream").encode())
                    break
            else:
                headers.append((b"accept", b"application/json, text/event-stream"))
            scope = {**scope, "headers": headers}
        await self.app(scope, receive, send)


# ── ASGI app ───────────────────────────────────────────────────────────────────
from starlette.applications import Starlette

_mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: Starlette):
    # Propagate the MCP app's lifespan so its session manager task group is initialized
    async with _mcp_app.router.lifespan_context(_mcp_app):
        yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/health", health),
        Route("/test", test),
    ],
)

# Mount MCP app at root so /mcp path is preserved (Starlette strips mount prefix)
app.mount("/", _mcp_app)

# Wrap with compatibility middleware for Claude Code VS Code extension
app = MCPAcceptPatchMiddleware(app)

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    host = get_server_host()
    port = get_server_port()
    logger.info("Starting mcp-i14y on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)
