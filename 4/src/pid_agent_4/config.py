"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """P&ID agent settings, loaded from environment or .env."""

    model_config = SettingsConfigDict(env_prefix="PID_AGENT_", extra="ignore")

    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "PID_AGENT_OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
        ),
    )
    model: str = "x-ai/grok-4.6"
    base_url: str | None = None  # override OpenRouter server URL if needed

    output_dir: Path = Path("./out")
    overlap: float = 0.15
    dpi: int = 150
    split_count: int = 3

    max_retries: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 30
    request_timeout: int = 120
    llm_max_tokens: int = 4096
    log_level: str = "INFO"

    def split_output_dir(self) -> Path:
        return self.output_dir / "splits"
