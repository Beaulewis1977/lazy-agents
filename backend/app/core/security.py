"""
Security utilities for authentication and encryption.
"""

import base64
import secrets
from functools import lru_cache

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> bool:
    """Verify API key from header."""
    if not settings.API_KEY:
        if settings.is_development or settings.ALLOW_NO_API_KEY:
            return True
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server misconfiguration: API key not set",
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
