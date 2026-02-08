"""
Execution database models.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Execution(Base):
    """Record of an agent execution."""

    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Reference to agent
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"))

    # Trigger: manual, schedule, webhook, event
    trigger: Mapped[str] = mapped_column(String(50), default="manual")

    # Status: pending, running, success, failed, cancelled
    status: Mapped[str] = mapped_column(String(50), default="pending")

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Input/Output
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Error info
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Token usage
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)

    # Cost (in USD cents)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    # Relationship to steps
    steps: Mapped[List["ExecutionStep"]] = relationship(
        "ExecutionStep",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Execution(id={self.id}, agent_id={self.agent_id}, status={self.status})>"


class ExecutionStep(Base):
    """Individual step within an execution."""

    __tablename__ = "execution_steps"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    execution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("executions.id"),
    )

    # Step order
    step_number: Mapped[int] = mapped_column(Integer)

    # Type: llm_call, skill_execution, tool_use
    step_type: Mapped[str] = mapped_column(String(50))

    # Name (e.g., skill ID or description)
    name: Mapped[str] = mapped_column(String(255))

    # Status: pending, running, success, failed
    status: Mapped[str] = mapped_column(String(50), default="pending")

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Input/Output
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    execution: Mapped["Execution"] = relationship("Execution", back_populates="steps")

    def __repr__(self) -> str:
        return f"<ExecutionStep(id={self.id}, step={self.step_number}, type={self.step_type})>"
