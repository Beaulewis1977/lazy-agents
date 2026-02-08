"""
Security utilities for authentication and encryption.
"""

import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from cryptography.fernet import Fernet

from app.core.config import settings


# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """Verify API key from header."""
    if settings.API_KEY is None:
        # No API key configured, allow all requests (development mode)
        return True
    
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


# Encryption for secrets storage
def get_fernet() -> Fernet:
    """Get Fernet instance for encryption."""
    # Derive key from secret key (in production, use a proper key derivation)
    key = settings.SECRET_KEY.encode()[:32].ljust(32, b'=')
    import base64
    key = base64.urlsafe_b64encode(key)
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
