"""HTTP API for the research LangGraph agent."""

from __future__ import annotations

import os
import traceback
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# LangSmith env sync runs when app.config loads; import before graph/langchain.
from app.config import Settings, bedrock_credentials_configured, config, get_settings
from app.graph import run_research

app = FastAPI(title="Bigboy LangGraph research", version="0.1.0")


def verify_service_key(
    settings: Settings = Depends(get_settings),
    x_research_service_key: str | None = Header(default=None, alias="X-Research-Service-Key"),
) -> None:
    expected = (settings.research_service_api_key or "").strip()
    if not expected:
        return
    if (x_research_service_key or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Research-Service-Key")


class ResearchRunRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=50_000)
    thread_id: str | None = Field(
        default=None,
        max_length=120,
        description="Optional LangGraph thread id for resume / idempotency mapping.",
    )


class ResultBlock(BaseModel):
    title: str
    body: str


class ResearchRunResponse(BaseModel):
    thread_id: str
    status: str
    result_blocks: list[ResultBlock]
    error_message: str | None = None


@app.get("/health")
def health() -> dict:
    ok = bedrock_credentials_configured()
    return {
        "status": "ok",
        "bedrock_configured": ok,
        "aws_region": str(config("AWS_REGION_NAME", default="")).strip() or None,
        "bedrock_model_id": str(config("BEDROCK_MODEL_ID", default="")).strip() or None,
        "langsmith_tracing_env": bool(str(os.environ.get("LANGCHAIN_TRACING_V2", "")).strip()),
        "langsmith_api_key_set": bool(str(os.environ.get("LANGCHAIN_API_KEY", "")).strip()),
        "langchain_project": str(os.environ.get("LANGCHAIN_PROJECT", "")).strip() or None,
    }


@app.post("/v1/research/run", response_model=ResearchRunResponse, dependencies=[Depends(verify_service_key)])
def post_research_run(
    body: ResearchRunRequest,
) -> ResearchRunResponse:
    if not bedrock_credentials_configured():
        raise HTTPException(
            status_code=503,
            detail="AWS Bedrock is not configured: set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (e.g. in bigboy-project/.env).",
        )
    try:
        thread_id, payload = run_research(query=body.query, thread_id=body.thread_id)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001 — surface agent failures to API clients
        return ResearchRunResponse(
            thread_id=body.thread_id or "",
            status="failed",
            result_blocks=[],
            error_message=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
        )

    blocks = payload.get("result_blocks") or []
    normalized = [
        ResultBlock(title=str(b.get("title", "Section")), body=str(b.get("body", "")))
        for b in blocks
        if isinstance(b, dict)
    ]
    status = str(payload.get("status") or "failed")
    err = payload.get("error_message")
    err_out = str(err).strip() if err else None
    if status == "failed" and not err_out:
        err_out = "Workflow returned failed status."

    return ResearchRunResponse(
        thread_id=thread_id,
        status=status,
        result_blocks=normalized,
        error_message=err_out,
    )


def run() -> None:
    s = get_settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=False)


if __name__ == "__main__":
    run()
