"""
Security utilities for authentication and encryption.
"""

import base64
import copy
import re
import secrets
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

REDACTED_VALUE = "***REDACTED***"
SENSITIVE_KEY_TERMS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "authorization",
    "credential",
    "private_key",
    "access_key",
    "client_secret",
)

AUTH_HEADER_PATTERN = re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:bearer\s+)?([^\s,;]+)")
KEY_VALUE_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s,;]+)"
)
BEARER_TOKEN_PATTERN = re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._\-]+)")


def mask_secret_value(value: Any) -> str:
    """Return a deterministic masked value for any secret-like input."""
    if value is None:
        return REDACTED_VALUE
    if isinstance(value, str) and not value:
        return REDACTED_VALUE
    return REDACTED_VALUE


def _is_sensitive_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    normalized = key.lower().replace("-", "_")
    return any(term in normalized for term in SENSITIVE_KEY_TERMS)


def redact_sensitive_string(value: str) -> str:
    """Redact token-like segments in free-form strings."""
    redacted = AUTH_HEADER_PATTERN.sub(f"authorization={REDACTED_VALUE}", value)
    redacted = KEY_VALUE_SECRET_PATTERN.sub(r"\1=" + REDACTED_VALUE, redacted)
    redacted = BEARER_TOKEN_PATTERN.sub("bearer " + REDACTED_VALUE, redacted)
    return redacted


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact sensitive fields in dict/list/string payloads."""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if _is_sensitive_key(key):
                redacted[key] = mask_secret_value(item)
            else:
                redacted[key] = redact_sensitive_data(item)
        return redacted

    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item) for item in value)

    if isinstance(value, str):
        return redact_sensitive_string(value)

    # Keep primitives and unknown objects unchanged.
    return copy.deepcopy(value)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> bool:
    """Verify API key from header."""
    if settings.API_KEY is None:
        if settings.is_development:
            # Development mode can run without API auth.
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API authentication not configured",
        )

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    if not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


def validate_security_configuration() -> None:
    """Validate security settings at startup."""
    if not settings.is_development:
        if settings.SECRET_KEY.startswith("change-me-"):
            raise RuntimeError("SECRET_KEY must be changed in non-development mode")
        if settings.SECRET_KEY_SALT.startswith(b"change-me-"):
            raise RuntimeError("SECRET_KEY_SALT must be changed in non-development mode")

    if not settings.API_KEY and not (settings.is_development or settings.ALLOW_NO_API_KEY):
        raise RuntimeError("API_KEY must be set in non-development mode")


# Encryption for secrets storage
@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    """Get Fernet instance for encryption."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.SECRET_KEY_SALT,
        iterations=1_200_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    """Encrypt a secret value."""
    fernet = get_fernet()
    return fernet.encrypt(value.encode()).decode()


def decrypt_secret(encrypted_value: str) -> str:
    """Decrypt a secret value."""
    fernet = get_fernet()
    return fernet.decrypt(encrypted_value.encode()).decode()


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"la-{secrets.token_urlsafe(32)}"
