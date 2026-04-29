# BigBoy MCP service

A small **[Model Context Protocol](https://modelcontextprotocol.io/)** server (stdio) that **creates and lists** `McpConversationImport` rows on your **BigBoy Django** backend via the REST API:

- `POST /api/v1/mcp-imports/`
- `GET /api/v1/mcp-imports/`
- `GET /api/v1/mcp-imports/{id}/`

This lets assistants (Cursor, Claude Desktop, etc.) **push conversation snapshots** into BigBoy so you can use **Explore → Conversation imports** and **Promote to subject** in the app.

## Setup

1. **Python 3.12+** and [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`.

2. Copy env:

   ```bash
   cp .env.example .env
   ```

3. Set:

   - **`BIGBOY_API_BASE_URL`** — e.g. `http://127.0.0.1:8000/api/v1` (production: your CloudFront/API URL with `/api/v1`).
   - **`BIGBOY_API_TOKEN`** — DRF `Token` string (same scheme as the Vue app: `Authorization: Token <token>`).

4. Install and run:

   ```bash
   cd mcp-service
   uv sync
   uv run python main.py
   ```

   (Use `uv run python main.py` from this directory so `.env` is loaded next to `main.py`.)

## Tools

| Tool | Action |
|------|--------|
| `import_conversation_to_bigboy` | Create a new import (`title`, `transcript`, optional `client_label`, optional `raw_payload_json`). |
| `list_conversation_imports` | List imports for the authenticated user. |
| `get_conversation_import` | Fetch one import by `import_id` (excerpt of transcript in the response). |

## Wire into an MCP client (example: Cursor)

Run from this directory so `.env` is found, or export env vars in the config.

```json
{
  "mcpServers": {
    "bigboy": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/absolute/path/to/bigboy-project/mcp-service",
      "env": {
        "BIGBOY_API_BASE_URL": "http://127.0.0.1:8000/api/v1",
        "BIGBOY_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Related code

- Model: `backend/bigboy/sources/models.py` — `McpConversationImport`
- API: `backend/bigboy/sources/api/v1/views.py` — `McpConversationImportListCreateView`
