"""
Application configuration using Pydantic Settings.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from the backend directory
_env_file = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "LazyAgents"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/lazy-agents.db"

    # Security
    SECRET_KEY: str = "change-me-in-production-please"
    API_KEY: str | None = None

    # LLM Providers
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    OLLAMA_BASE_URL: str | None = None

    # Default model
    DEFAULT_MODEL: str = "gpt-4o-mini"

    # Integrations
    GITHUB_TOKEN: str | None = None
    DISCORD_BOT_TOKEN: str | None = None
    SLACK_BOT_TOKEN: str | None = None
    SLACK_SIGNING_SECRET: str | None = None
    NOTION_API_KEY: str | None = None

    # Redis (optional)
    REDIS_URL: str | None = None

    # Agent execution
    MAX_AGENT_EXECUTION_TIME: int = 300  # seconds
    MAX_TOKENS_PER_REQUEST: int = 4096

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"

    @property
    def available_providers(self) -> list[str]:
        """Get list of configured LLM providers."""
        providers = []
        if self.OPENAI_API_KEY:
            providers.append("openai")
        if self.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if self.GOOGLE_API_KEY:
            providers.append("google")
        if self.OPENROUTER_API_KEY:
            providers.append("openrouter")
        if self.OLLAMA_BASE_URL:
            providers.append("ollama")
        return providers


# Create global settings instance
settings = Settings()
