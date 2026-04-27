# LangGraph service (bigboy-project)

Standalone **FastAPI** app that runs a **LangGraph functional workflow** (`@entrypoint` / `@task`) for **research briefs**. It uses **Amazon Bedrock** (via `langchain-aws`) for chat completions, exposes a small **HTTP API**, and is designed to sit beside the Django **`backend/`** and Vue **`frontend-vue/`** folders in the monorepo.

The Django API calls this service when users create a **research run** (see backend `LANGGRAPH_SERVICE_*` settings and `invoke_research_agent`).

## What it does

- Accepts a natural-language **query**.
- Runs two Bedrock-backed **tasks** in parallel (summary + suggested next steps), then merges them into **`result_blocks`**: a list of `{ "title", "body" }` objects aligned with the Django **`ResearchRun.result_blocks`** shape.
- Persists workflow state in an **in-memory** LangGraph checkpointer (`InMemorySaver`) keyed by **`thread_id`** (you can pass your own id, e.g. the Django research run primary key).

## Project layout

| Path | Role |
|------|------|
| `pyproject.toml` | Dependencies and project metadata (`uv` / `pip` install from this directory). |
| `app/config.py` | Loads **`bigboy-project/.env`** with **python-decouple**, syncs **LangSmith** vars into `os.environ`, Pydantic settings for bind host/port and optional API key. |
| `app/graph.py` | LangGraph **`@entrypoint`** + **`@task`** workflow and **`run_research()`**. |
| `app/main.py` | FastAPI app, **`/health`**, **`POST /v1/research/run`**, Uvicorn entrypoint. |

## Requirements

- Python **3.11+** (see `pyproject.toml`).
- **uv** (recommended) or another installer.
- AWS credentials with permission to invoke the chosen **Bedrock** chat model in the configured region.

## Setup

From **`langgraph-service/`**:

```bash
uv sync
```

Configuration is read from the **monorepo root** **`../.env`** when that file exists (same file the Django backend typically uses). You can also rely on process environment variables.

## Run the server

```bash
cd langgraph-service
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Or:

```bash
uv run python -m app.main
```

Default bind: **`0.0.0.0:8765`** (overridable via Pydantic settings / env — see below).

## HTTP API

### `GET /health`

Liveness and configuration hints (no secrets): Bedrock keys present, AWS region, Bedrock model id from env, LangSmith tracing flags.

### `POST /v1/research/run`

Runs the research workflow.

**JSON body**

| Field | Type | Notes |
|-------|------|--------|
| `query` | string | Required, 1–50_000 characters. |
| `thread_id` | string or null | Optional; defaults to a new UUID. Use a stable id (e.g. Django `ResearchRun.id`) if you want checkpoint continuity per run. |

**Response** (`200`)

| Field | Type |
|-------|------|
| `thread_id` | string |
| `status` | `"succeeded"` or `"failed"` |
| `result_blocks` | `[{ "title", "body" }, …]` |
| `error_message` | string or null |

**Errors**

- **`503`** if Bedrock AWS keys are not configured.
- **`401`** if `RESEARCH_SERVICE_API_KEY` is set in the service environment but the request omits or mismatches the header **`X-Research-Service-Key`**.

## Environment variables

### AWS (required for `/v1/research/run`)

| Variable | Purpose |
|----------|---------|
| `AWS_ACCESS_KEY_ID` | IAM access key. |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key. |
| `AWS_REGION_NAME` | Region (default in code: `us-east-2`). |
| `BEDROCK_MODEL_ID` | Bedrock chat model id (default: `global.amazon.nova-2-lite-v1:0`). |

### Service HTTP (optional)

| Variable | Purpose |
|----------|---------|
| `HOST` | Bind host (Pydantic `Settings.host`, default `0.0.0.0`). |
| `PORT` | Bind port (default `8765`). |
| `RESEARCH_SERVICE_API_KEY` | If set, clients must send matching **`X-Research-Service-Key`**. |

### LangSmith (optional)

LangChain reads tracing from **`os.environ`**. Values in **`bigboy-project/.env`** are copied into the environment at startup for keys such as:

`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_WORKSPACE_ID`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`, `LANGSMITH_TRACING`.

If **`LANGCHAIN_API_KEY`** is set but **`LANGCHAIN_TRACING_V2`** is not, tracing is turned on by setting **`LANGCHAIN_TRACING_V2=true`**. **`LANGSMITH_API_KEY`** alone is mapped to **`LANGCHAIN_API_KEY`** when the latter is empty.

## Integration with the Django backend

In **`backend/config/settings.py`** (and your root **`.env`**):

- **`LANGGRAPH_SERVICE_URL`** — Base URL of this service (e.g. `http://127.0.0.1:8765`).
- **`LANGGRAPH_SERVICE_API_KEY`** — Optional; must match **`RESEARCH_SERVICE_API_KEY`** here if you protect the research endpoint.
- **`LANGGRAPH_SERVICE_TIMEOUT`** — HTTP client timeout in seconds (default `120`).

Creating a **research run** via the Django API triggers a synchronous `POST` to **`{LANGGRAPH_SERVICE_URL}/v1/research/run`**; the response is persisted on **`ResearchRun`** (`result_blocks`, `graph_run_id` / `thread_id`, status, errors).

## Stack reference

- **FastAPI** + **Uvicorn**
- **LangGraph** functional API (`langgraph.func.entrypoint`, `task`, `InMemorySaver`)
- **LangChain** + **langchain-aws** (`ChatBedrock`)

## Development notes

- This service is **not** a Django app; deploy and scale it separately from **`backend/`**.
- The checkpointer is **in-memory**; restarts clear LangGraph checkpoint state. For durable threads across restarts, swap in a persistent checkpointer later.
- For heavier research, consider moving the Django call to a **background worker** so HTTP does not block for the full Bedrock duration.
