"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings."""

    database_url: str = Field(
        default="sqlite:///./data/app.db",
        description="SQLAlchemy compatible database URL.",
    )
    chroma_path: Path = Field(
        default=Path("data/vectorstore"),
        description="Storage path for the local vector store.",
    )
    embedding_provider: str = Field(
        default="local", description="Provider for embeddings (local/openai/etc.)."
    )
    local_embedding_dimension: int = Field(
        default=384, description="Vector dimension used by the local embedding stub."
    )
    llm_model: str = Field(
        default="grok-2",
        description="Name of the LLM model used for drafting responses.",
    )
    answer_tone: List[str] = Field(
        default_factory=lambda: ["friendly", "concise"],
        description="Permitted tones for generated answers.",
    )
    max_context_snippets: int = Field(
        default=3, description="How many knowledge snippets to attach to an answer."
    )
    openai_api_key: Optional[str] = Field(
        default=None, description="Optional OpenAI API key for embeddings or completions."
    )
    xai_api_key: Optional[str] = Field(
        default=None, description="Optional xAI API key used for Grok responses."
    )
    embedding_model: Optional[str] = Field(
        default=None, description="Identifier for the embedding model."
    )
    verify_token: str = Field(
        default="dev-verify-token",
        description="Token expected from Meta webhook verification.",
    )
    page_id: Optional[str] = Field(
        default=None, description="Facebook Page ID tied to this automation."
    )
    page_access_token: Optional[str] = Field(
        default=None, description="Long-lived page access token for reply delivery."
    )
    graph_api_base_url: AnyUrl = Field(
        default="https://graph.facebook.com/v18.0",
        description="Base URL for Messenger Graph API calls.",
    )
    environment: str = Field(
        default="development",
        description="Arbitrary environment label (development/staging/production).",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    @field_validator("answer_tone", mode="before")
    @classmethod
    def parse_answer_tone(cls, value: List[str] | str | None) -> List[str]:
        """Support comma-separated env values."""
        if value is None:
            return ["friendly", "concise"]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
