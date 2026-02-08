"""
Agent CRUD API endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import redact_sensitive_data, redact_sensitive_string, verify_api_key
from app.models.agent import Agent
from app.models.execution import Execution

router = APIRouter(dependencies=[Depends(verify_api_key)])


# =============================================================================
# Schemas
# =============================================================================


class AgentCreate(BaseModel):
    """Schema for creating an agent."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    model: str = "gpt-4o-mini"
    system_prompt: str | None = None
    temperature: float = Field(0.7, ge=0, le=2)
    skills: list[str] = []
    integrations: list[str] = []
    schedule: str | None = None
    memory_enabled: bool = True


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0, le=2)
    skills: list[str] | None = None
    integrations: list[str] | None = None
    schedule: str | None = None
    memory_enabled: bool | None = None


class AgentResponse(BaseModel):
    """Schema for agent response."""

    id: str
    name: str
    description: str | None
    status: str
    model: str
    system_prompt: str | None
    temperature: float
    skills: list[str]
    integrations: list[str]
    schedule: str | None
    memory_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None
    total_runs: int
    successful_runs: int

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================


@router.get("")
async def list_agents(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    include_last_execution: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all agents with optional last execution data."""
    query = select(Agent).offset(skip).limit(limit)
    if status:
        query = query.where(Agent.status == status)

    result = await db.execute(query)
    agents = result.scalars().all()

    # If include_last_execution is True, fetch last execution for each agent
    if include_last_execution:
        agents_with_execution = []
        for agent in agents:
            agent_dict = AgentResponse.model_validate(agent).model_dump()

            # Query for the most recent execution for this agent
            exec_query = (
                select(Execution)
                .where(Execution.agent_id == agent.id)
                .order_by(desc(Execution.created_at))
                .limit(1)
            )
            exec_result = await db.execute(exec_query)
            last_execution = exec_result.scalar_one_or_none()

            # Add last_execution data if it exists
            if last_execution:
                agent_dict["last_execution"] = {
                    "id": last_execution.id,
                    "status": last_execution.status,
                    "trigger": last_execution.trigger,
                    "started_at": last_execution.started_at.isoformat()
                    if last_execution.started_at
                    else None,
                    "completed_at": last_execution.completed_at.isoformat()
                    if last_execution.completed_at
                    else None,
                    "tokens_input": last_execution.tokens_input,
                    "tokens_output": last_execution.tokens_output,
                    "error_message": last_execution.error_message,
                }
            else:
                agent_dict["last_execution"] = None

            agents_with_execution.append(agent_dict)

        return agents_with_execution

    # Default behavior - return AgentResponse list
    return [AgentResponse.model_validate(agent) for agent in agents]


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
    input_data: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger an agent execution."""
    if input_data is None:
        input_data = {}
    from app.api.websocket import emit_execution_log
    from app.runtime.agent_executor import AgentExecutor

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Get API keys from request if provided
    request_input = dict(input_data or {})
    api_keys = {}
    if "api_keys" in request_input:
        api_keys = request_input.pop("api_keys")

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
            input_data=request_input,
            trigger="manual",
            api_keys=api_keys,
        )

        return {
            "message": f"Agent {agent.name} executed",
            "agent_id": agent_id,
            "execution_id": execution.id,
            "status": execution.status,
            "output": redact_sensitive_data(execution.output_data),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {redact_sensitive_string(str(e))}",
        ) from e


@router.get("/{agent_id}/config")
async def get_agent_config(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get complete agent configuration including skill details."""
    from app.models.integration import Integration
    from app.models.skill import Skill
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
                (agent.successful_runs / agent.total_runs * 100) if agent.total_runs > 0 else 0
            ),
            "last_run_at": agent.last_run_at.isoformat() if agent.last_run_at else None,
        },
    }
