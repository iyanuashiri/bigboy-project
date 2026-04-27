"""Research workflow using LangGraph functional API (@entrypoint / @task)."""

from __future__ import annotations

# Load decouple + sync LangSmith vars into os.environ before any LangChain imports.
from app.config import config

from langchain_aws import ChatBedrock
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task

_checkpointer = InMemorySaver()


def _chat_model() -> ChatBedrock:
    access_key = str(config("AWS_ACCESS_KEY_ID", default="")).strip()
    secret_key = str(config("AWS_SECRET_ACCESS_KEY", default="")).strip()
    if not access_key or not secret_key:
        raise RuntimeError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set (e.g. in bigboy-project/.env).")

    region = str(config("AWS_REGION_NAME", default="us-east-2")).strip() or "us-east-2"
    model_id = str(
        config("BEDROCK_MODEL_ID", default="global.amazon.nova-2-lite-v1:0")
    ).strip() or "global.amazon.nova-2-lite-v1:0"

    return ChatBedrock(
        model_id=model_id,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


@task
def summarize_research(query: str) -> str:
    model = _chat_model()
    out = model.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You are a careful research assistant. Write a clear, accurate summary "
                    "of what the user asked for. Use short sections with bullets where helpful. "
                    "If you lack specific facts, say so and give general guidance."
                ),
            },
            {"role": "user", "content": query},
        ]
    )
    return (out.content or "").strip()


@task
def suggest_next_steps(query: str) -> str:
    model = _chat_model()
    out = model.invoke(
        [
            {
                "role": "system",
                "content": (
                    "List concrete next steps the user could take to go deeper on their topic: "
                    "experiments, reading, data to gather, or validation steps. "
                    "Use a numbered list; keep it practical."
                ),
            },
            {"role": "user", "content": query},
        ]
    )
    return (out.content or "").strip()


@entrypoint(checkpointer=_checkpointer)
def research_workflow(inputs: dict) -> dict:
    """
    Functional workflow: parallel-ish LLM tasks, merged into result_blocks
    compatible with Django ResearchRun.result_blocks.
    """
    query = (inputs.get("query") or "").strip()
    if not query:
        return {
            "status": "failed",
            "result_blocks": [],
            "error_message": "Missing or empty query.",
        }

    summary_future = summarize_research(query)
    steps_future = suggest_next_steps(query)
    summary = summary_future.result()
    steps = steps_future.result()

    return {
        "status": "succeeded",
        "result_blocks": [
            {"title": "Summary", "body": summary},
            {"title": "Suggested next steps", "body": steps},
        ],
        "error_message": "",
    }


def run_research(*, query: str, thread_id: str | None = None) -> tuple[str, dict]:
    """
    Invoke the compiled entrypoint. Returns (thread_id, payload_dict).
    """
    tid = thread_id or str(uuid7())
    config = {"configurable": {"thread_id": tid}}
    result = research_workflow.invoke({"query": query}, config=config)
    return tid, result
