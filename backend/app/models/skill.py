"""
Skill database model.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Skill(Base):
    """Reusable skill/action that agents can perform."""
    
    __tablename__ = "skills"
    
    # Use semantic ID like "github.list_issues"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Category for grouping (e.g., "github", "discord", "file")
    category: Mapped[str] = mapped_column(String(50), default="general")
    
    # Parameters schema (JSON Schema format)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Required integration (e.g., "github", "discord")
    integration_required: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Implementation
    # For built-in skills, this references a Python function
    # For custom skills, this contains the code/workflow definition
    implementation_type: Mapped[str] = mapped_column(String(50), default="builtin")
    implementation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source path for filesystem-loaded skills
    source_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Is this a built-in skill or user-created?
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    
    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name})>"
