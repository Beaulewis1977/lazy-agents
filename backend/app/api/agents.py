"""
Agent CRUD API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.agent import Agent

router = APIRouter(dependencies=[Depends(verify_api_key)])


# =============================================================================
# Schemas
# =============================================================================

class AgentCreate(BaseModel):
    """Schema for creating an agent."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model: str = "gpt-4o-mini"
    system_prompt: Optional[str] = None
    temperature: float = Field(0.7, ge=0, le=2)
    skills: List[str] = []
    integrations: List[str] = []
    schedule: Optional[str] = None
    memory_enabled: bool = True


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    skills: Optional[List[str]] = None
    integrations: Optional[List[str]] = None
    schedule: Optional[str] = None
    memory_enabled: Optional[bool] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""
    id: str
    name: str
    description: Optional[str]
    status: str
    model: str
    system_prompt: Optional[str]
    temperature: float
    skills: List[str]
    integrations: List[str]
    schedule: Optional[str]
    memory_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    total_runs: int
    successful_runs: int

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get("", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all agents."""
    query = select(Agent).offset(skip).limit(limit)
    if status:
        query = query.where(Agent.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent."""
    agent = Agent(**agent_data.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an agent by ID."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    await db.delete(agent)
    await db.commit()


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    input_data: dict = {},
    db: AsyncSession = Depends(get_db),
):
    """Trigger an agent execution."""
    from app.runtime.agent_executor import AgentExecutor
    from app.api.websocket import emit_execution_log

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Get API keys from request if provided
    api_keys = {}
    if "api_keys" in input_data:
        api_keys = input_data.pop("api_keys")

    # Execute the agent
    executor = AgentExecutor(db)

    # Add WebSocket log callback
    async def log_callback(log_entry):
        await emit_execution_log(
            log_entry["execution_id"],
            log_entry["level"],
            log_entry["message"],
            log_entry["source"],
        )
    executor.add_log_callback(log_callback)

    try:
        execution = await executor.execute(
            agent_id=agent_id,
            input_data=input_data,
            trigger="manual",
            api_keys=api_keys,
        )

        return {
            "message": f"Agent {agent.name} executed",
            "agent_id": agent_id,
            "execution_id": execution.id,
            "status": execution.status,
            "output": execution.output_data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}",
        )


@router.get("/{agent_id}/config")
async def get_agent_config(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get complete agent configuration including skill details."""
    from app.models.skill import Skill
    from app.models.integration import Integration
    from app.runtime.scheduler import agent_scheduler

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Load skill details
    skill_details = []
    if agent.skills:
        skills_result = await db.execute(select(Skill).where(Skill.id.in_(agent.skills)))
        skill_details = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "parameters": s.parameters,
            }
            for s in skills_result.scalars().all()
        ]

    # Load integration details
    integration_details = []
    if agent.integrations:
        integrations_result = await db.execute(
            select(Integration).where(Integration.id.in_(agent.integrations))
        )
        integration_details = [
            {
                "id": i.id,
                "name": i.name,
                "type": i.type,
                "status": i.status,
            }
            for i in integrations_result.scalars().all()
        ]

    # Get schedule info
    next_run = agent_scheduler.get_next_run(agent_id)

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "status": agent.status,
        "model": agent.model,
        "system_prompt": agent.system_prompt,
        "temperature": agent.temperature,
        "memory_enabled": agent.memory_enabled,
        "schedule": agent.schedule,
        "next_scheduled_run": next_run.isoformat() if next_run else None,
        "skills": skill_details,
        "integrations": integration_details,
        "stats": {
            "total_runs": agent.total_runs,
            "successful_runs": agent.successful_runs,
            "success_rate": (
                (agent.successful_runs / agent.total_runs * 100)
                if agent.total_runs > 0 else 0
            ),
            "last_run_at": agent.last_run_at.isoformat() if agent.last_run_at else None,
        },
    }
