"""
Executions API endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.execution import Execution, ExecutionStep

router = APIRouter(dependencies=[Depends(verify_api_key)])


# =============================================================================
# Schemas
# =============================================================================

class ExecutionStepResponse(BaseModel):
    """Schema for execution step response."""
    id: str
    step_number: int
    step_type: str
    name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Schema for execution response."""
    id: str
    agent_id: str
    trigger: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    tokens_input: int
    tokens_output: int
    cost_cents: int
    created_at: datetime
    steps: List[ExecutionStepResponse] = []

    class Config:
        from_attributes = True


class ExecutionSummary(BaseModel):
    """Summary of an execution (without steps)."""
    id: str
    agent_id: str
    trigger: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    tokens_input: int
    tokens_output: int
    cost_cents: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints - IMPORTANT: Static paths must come BEFORE path parameters
# =============================================================================

@router.get("", response_model=List[ExecutionSummary])
async def list_executions(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List executions with optional filtering."""
    query = select(Execution).order_by(desc(Execution.created_at)).offset(skip).limit(limit)
    
    if agent_id:
        query = query.where(Execution.agent_id == agent_id)
    if status:
        query = query.where(Execution.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_execution_stats(
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get execution statistics."""
    # Base query
    query = select(
        func.count(Execution.id).label("total"),
        func.sum(Execution.tokens_input).label("total_tokens_input"),
        func.sum(Execution.tokens_output).label("total_tokens_output"),
        func.sum(Execution.cost_cents).label("total_cost_cents"),
    )
    
    if agent_id:
        query = query.where(Execution.agent_id == agent_id)
    
    result = await db.execute(query)
    row = result.one()
    
    # Get success count
    success_query = select(func.count(Execution.id)).where(Execution.status == "success")
    if agent_id:
        success_query = success_query.where(Execution.agent_id == agent_id)
    success_result = await db.execute(success_query)
    successful = success_result.scalar() or 0
    
    # Get failed count
    failed_query = select(func.count(Execution.id)).where(Execution.status == "failed")
    if agent_id:
        failed_query = failed_query.where(Execution.agent_id == agent_id)
    failed_result = await db.execute(failed_query)
    failed = failed_result.scalar() or 0
    
    total = row.total or 0
    success_rate = (successful / total * 100) if total > 0 else 0.0
    
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": round(success_rate, 1),
        "total_tokens": (row.total_tokens_input or 0) + (row.total_tokens_output or 0),
        "total_cost_cents": row.total_cost_cents or 0,
    }


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an execution by ID with all steps."""
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )
    
    # Load steps
    steps_result = await db.execute(
        select(ExecutionStep)
        .where(ExecutionStep.execution_id == execution_id)
        .order_by(ExecutionStep.step_number)
    )
    steps = steps_result.scalars().all()
    
    response = ExecutionResponse.model_validate(execution)
    response.steps = [ExecutionStepResponse.model_validate(s) for s in steps]
    return response


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running execution."""
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )
    
    if execution.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel execution with status: {execution.status}",
        )
    
    execution.status = "cancelled"
    execution.completed_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Execution cancelled", "execution_id": execution_id}
