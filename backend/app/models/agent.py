"""
Agent database model.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Agent(Base):
    """AI Agent entity."""
    
    __tablename__ = "agents"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status: active, paused, error
    status: Mapped[str] = mapped_column(String(50), default="active")
    
    # LLM configuration
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(default=0.7)
    
    # Skills and integrations (stored as JSON arrays of IDs)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    integrations: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Scheduling
    schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # cron
    
    # Memory
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Stats
    total_runs: Mapped[int] = mapped_column(default=0)
    successful_runs: Mapped[int] = mapped_column(default=0)
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
