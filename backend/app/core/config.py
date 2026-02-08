"""
Application configuration using Pydantic Settings.
"""

from pathlib import Path

from pydantic import field_validator
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
    SECRET_KEY_SALT: bytes = b"change-me-salt-in-production"
    API_KEY: str | None = None
    ALLOW_NO_API_KEY: bool = False

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

    @field_validator("SECRET_KEY_SALT", mode="before")
    @classmethod
    def _validate_secret_key_salt(cls, value: str | bytes) -> bytes:
        """Ensure SECRET_KEY_SALT is loaded as bytes with minimum entropy length."""
        salt = value if isinstance(value, bytes) else value.encode("utf-8")
        if len(salt) < 16:
            raise ValueError("SECRET_KEY_SALT must be at least 16 bytes")
        return salt

    @property
    def is_production_like(self) -> bool:
        """Check if runtime should enforce production security posture."""
        return not self.is_development

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

_INSECURE_SECRET_KEY_VALUES = {
    "",
    "change-me-in-production-please",
    "changeme",
    "secret",
    "default",
}
_MIN_SECRET_KEY_LENGTH = 32


def _is_secret_key_secure(secret_key: str) -> bool:
    candidate = secret_key.strip()
    if len(candidate) < _MIN_SECRET_KEY_LENGTH:
        return False
    return candidate.lower() not in _INSECURE_SECRET_KEY_VALUES


def validate_startup_security_settings() -> None:
    """Fail fast on insecure settings outside development mode."""
    if settings.is_development:
        return

    if settings.APP_DEBUG:
        raise ValueError("APP_DEBUG must be false outside development mode")

    if not settings.API_KEY or not settings.API_KEY.strip():
        raise ValueError("API_KEY must be set outside development mode")

    if not _is_secret_key_secure(settings.SECRET_KEY):
        raise ValueError(
            f"SECRET_KEY must be at least {_MIN_SECRET_KEY_LENGTH} chars and non-default outside development mode"
        )
