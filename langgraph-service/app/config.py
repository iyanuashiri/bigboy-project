import os
from functools import lru_cache
from pathlib import Path

from decouple import Config, RepositoryEnv, config
from pydantic_settings import BaseSettings, SettingsConfigDict

# bigboy-project/ (parent of langgraph-service/)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_env_path = _REPO_ROOT / ".env"
if _env_path.is_file():
    config = Config(RepositoryEnv(str(_env_path)))


def sync_langsmith_env_from_decouple() -> None:
    """
    LangChain / LangSmith read tracing settings from os.environ.
    python-decouple does not populate os.environ, so copy known keys from .env via config().
    Non-empty decouple values override existing os.environ entries for these keys only.
    """
    keys = (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
        "LANGCHAIN_WORKSPACE_ID",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_ENDPOINT",
        "LANGSMITH_TRACING",
    )
    for key in keys:
        raw = config(key, default="")
        val = str(raw).strip() if raw is not None else ""
        if val:
            os.environ[key] = val

    # LangChain prefers LANGCHAIN_API_KEY; accept LANGSMITH_API_KEY alone in .env
    if not os.environ.get("LANGCHAIN_API_KEY", "").strip():
        smith = str(config("LANGSMITH_API_KEY", default="")).strip()
        if smith:
            os.environ["LANGCHAIN_API_KEY"] = smith

    if not os.environ.get("LANGCHAIN_PROJECT", "").strip():
        proj = str(config("LANGSMITH_PROJECT", default="")).strip()
        if proj:
            os.environ["LANGCHAIN_PROJECT"] = proj

    if os.environ.get("LANGCHAIN_API_KEY", "").strip() and not str(
        os.environ.get("LANGCHAIN_TRACING_V2", "")
    ).strip():
        os.environ["LANGCHAIN_TRACING_V2"] = "true"


sync_langsmith_env_from_decouple()


def bedrock_credentials_configured() -> bool:
    return bool(
        str(config("AWS_ACCESS_KEY_ID", default="")).strip()
        and str(config("AWS_SECRET_ACCESS_KEY", default="")).strip()
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8765
    research_service_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
