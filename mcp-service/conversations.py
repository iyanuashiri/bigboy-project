"""BigBoy MCP server — posts conversation imports to the Django API (`/api/v1/mcp-imports/`).

Configure:
  BIGBOY_API_BASE_URL  e.g. http://127.0.0.1:8000/api/v1  (no trailing slash)
  BIGBOY_API_TOKEN     DRF token: ``Authorization: Token <key>``

Get a token via registration/login in the app or ``/api/v1/`` auth endpoints.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from decouple import config
from mcp.server.fastmcp import FastMCP

# Load .env from mcp-service directory when running as script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

mcp = FastMCP("bigboy-mcp")


def _api_base() -> str:
    raw = config(
        "BIGBOY_API_BASE_URL",
        default="http://127.0.0.1:8000/api/v1",
    ).strip()
    return raw.rstrip("/")


def _api_token() -> str:
    return config("BIGBOY_API_TOKEN", default="").strip()


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Token {_api_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _format_drf_error(status: int, data: Any) -> str:
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail is not None:
            if isinstance(detail, list):
                return f"API error {status}: {detail}"
            return f"API error {status}: {detail}"
        return f"API error {status}: {json.dumps(data)[:2000]}"
    if isinstance(data, str):
        return f"API error {status}: {data[:2000]}"
    return f"API error {status}."


def _format_import_row(item: dict[str, Any]) -> str:
    iid = item.get("id", "?")
    title = item.get("title", "")
    st = item.get("status", "")
    created = item.get("created_at", "")
    label = (item.get("client_label") or "")[:40]
    return f"  id={iid}  status={st}  client={label!r}  created={created}\n     title: {title[:80]}"


async def _request_json(
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    if not _api_token():
        return 0, {
            "ok": False,
            "user": "Set BIGBOY_API_TOKEN to your Django REST token (see README).",
        }

    base = _api_base()
    p = path if path.startswith("/") else f"/{path}"
    url = f"{base}{p}"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.request(
                method,
                url,
                headers=_headers(),
                json=json_body,
                timeout=60.0,
            )
        except httpx.RequestError as e:
            return 0, {"ok": False, "user": f"Could not reach BigBoy API: {e!s}"}
    try:
        data = r.json() if r.content else None
    except Exception:
        data = {"raw": r.text[:5000]}
    return r.status_code, data


@mcp.tool()
async def import_conversation_to_bigboy(
    title: str,
    transcript: str,
    client_label: str = "mcp",
    raw_payload_json: str = "",
) -> str:
    """Create a **MCP conversation import** in BigBoy (POST /mcp-imports/).

    The Explore UI lists these under Conversation imports; you can **Promote to subject** from there.

    Args:
        title: Short title for this import (required by the API).
        transcript: Flattened conversation text (user + assistant lines, or tool log).
        client_label: Provenance, e.g. claude-desktop, cursor, mcp.
        raw_payload_json: Optional JSON string for extra structured data (tool I/O, metadata).
    """
    title = (title or "").strip()[:255]
    if not title:
        return "title is required."

    body: dict[str, Any] = {
        "title": title,
        "transcript": (transcript or "").strip(),
        "client_label": (client_label or "mcp").strip()[:120],
        "raw_payload": {},
    }
    raw = (raw_payload_json or "").strip()
    if raw:
        try:
            body["raw_payload"] = json.loads(raw)
        except json.JSONDecodeError as e:
            return f"raw_payload_json is not valid JSON: {e}"

    status, data = await _request_json("POST", "/mcp-imports/", body)
    if status == 0:
        return str(data.get("user", data))
    if 200 <= status < 300 and isinstance(data, dict) and "id" in data:
        iid = data["id"]
        st = data.get("status", "")
        return (
            f"Import created in BigBoy.\n"
            f"  id: {iid}\n"
            f"  status: {st}\n"
            f"  title: {data.get('title', title)!r}\n"
            f"Open Explore → Conversation imports, or use get_conversation_import(id={iid})."
        )
    return _format_drf_error(status, data)


@mcp.tool()
async def list_conversation_imports() -> str:
    """List your MCP conversation imports (newest first, GET /mcp-imports/)."""
    status, data = await _request_json("GET", "/mcp-imports/")
    if status == 0:
        return str(data.get("user", data))
    if status != 200:
        return _format_drf_error(status, data)
    if not isinstance(data, list):
        return f"Unexpected list response: {str(data)[:2000]}"
    if not data:
        return "No conversation imports yet. Use import_conversation_to_bigboy first."
    lines = ["Your BigBoy MCP imports:"]
    for item in data[:30]:
        if isinstance(item, dict):
            lines.append(_format_import_row(item))
    if len(data) > 30:
        lines.append(f"  … and {len(data) - 30} more (showing first 30).")
    return "\n".join(lines)


@mcp.tool()
async def get_conversation_import(import_id: int) -> str:
    """Fetch one import by id (GET /mcp-imports/{id}/)."""
    if import_id < 1:
        return "import_id must be a positive integer."
    status, data = await _request_json("GET", f"/mcp-imports/{import_id}/")
    if status == 0:
        return str(data.get("user", data))
    if status == 200 and isinstance(data, dict):
        lines = [
            f"Import #{data.get('id')}",
            f"  title: {data.get('title', '')}",
            f"  status: {data.get('status', '')}",
            f"  client_label: {data.get('client_label', '')}",
            f"  created_at: {data.get('created_at', '')}",
            f"  transcript (excerpt):",
        ]
        tr = (data.get("transcript") or "").strip()
        ex = tr[:4000] + ("…" if len(tr) > 4000 else "")
        lines.append(ex or "(empty)")
        rp = data.get("raw_payload")
        if rp:
            lines.append(f"  raw_payload keys: {list(rp) if isinstance(rp, dict) else type(rp).__name__}")
        return "\n".join(lines)
    if status == 404:
        return f"No import {import_id} (or you do not have access)."
    return _format_drf_error(status, data)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
