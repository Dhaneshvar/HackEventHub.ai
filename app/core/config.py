"""Configuration loaded from environment variables via pydantic-settings."""

from __future__ import annotations

import enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderName(enum.StrEnum):
    OLLAMA = "ollama"
    AZURE = "azure"
    ATHENA = "athena"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""

    @property
    def allowed_user_ids(self) -> set[int]:
        if not self.telegram_allowed_user_ids:
            return set()
        return {
            int(uid.strip()) for uid in self.telegram_allowed_user_ids.split(",") if uid.strip()
        }

    # --- Dashboard ---
    dashboard_token: str = ""

    # --- TinyFish ---
    tinyfish_api_key: str = ""
    tinyfish_daily_budget_agent: int = 10
    tinyfish_daily_budget_fetch: int = 100

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"

    # --- Azure OpenAI ---
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_key: str = ""
    azure_use_entra_id: bool = False

    # --- Athena ---
    athena_base_url: str = ""
    athena_api_key: str = ""
    athena_model: str = "default"
    athena_auth_header: str = "Authorization"
    athena_auth_scheme: str = "Bearer"

    # --- General ---
    contact_email: str = ""
    tz: str = "UTC"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./data/opportunity_agent.db"

    # --- LLM active provider ---
    active_llm_provider: LLMProviderName = LLMProviderName.OLLAMA
    fallback_llm_providers: str = ""

    @property
    def fallback_provider_list(self) -> list[LLMProviderName]:
        if not self.fallback_llm_providers:
            return []
        return [
            LLMProviderName(p.strip()) for p in self.fallback_llm_providers.split(",") if p.strip()
        ]

    # --- Server ---
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False


settings = Settings()
