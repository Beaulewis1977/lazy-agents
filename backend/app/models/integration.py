"""
Integration database model.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Integration(Base):
    """External service integration."""

    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Type: github, discord, slack, notion, webhook, etc.
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # User-friendly name
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status: connected, disconnected, error
    status: Mapped[str] = mapped_column(String(50), default="connected")

    # Encrypted credentials (stored as encrypted JSON)
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Permissions/scopes
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Configuration (non-sensitive settings)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, type={self.type}, name={self.name})>"
