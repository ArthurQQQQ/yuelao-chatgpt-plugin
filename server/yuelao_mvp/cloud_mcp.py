"""Serve a deployment snapshot over HTTP for a tunnel or an HTTPS gateway."""

from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import sqlite3

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from .case_mcp import build_server
from .case_rag import DEPLOY_SNAPSHOT_VERSION


def create_app():
    path = Path(os.environ.get("YUELAO_CASE_DB", "cases.sqlite3")).resolve()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA user_version").fetchone()[0] != DEPLOY_SNAPSHOT_VERSION:
            raise ValueError("YUELAO_CASE_DB must point to a deployment snapshot")
        if not db.execute("SELECT 1 FROM compact_cases LIMIT 1").fetchone():
            raise ValueError("The deployment snapshot has no case cards")
    server = build_server(path)

    @server.custom_route("/healthz", methods=["GET"])
    async def health(_: Request):
        return JSONResponse({"status": "ok", "service": "yuelao-cases"})

    hosts = ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*"]
    hosts.extend(value.strip() for value in os.environ.get("YUELAO_ALLOWED_HOSTS", "").split(",") if value.strip())
    security = TransportSecuritySettings(allowed_hosts=hosts, allowed_origins=["https://chatgpt.com"])
    return server.streamable_http_app(stateless_http=True, json_response=True, max_request_body_size=32768,
                                      transport_security=security)
