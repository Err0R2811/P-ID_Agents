"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """P&ID agent settings, loaded from environment or .env."""

    model_config = SettingsConfigDict(env_prefix="PID_AGENT_", extra="ignore")

    openai_api_key: str = ""
    model: str = "gpt-4o"
    base_url: str | None = None  # for OpenAI-compatible endpoints

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
