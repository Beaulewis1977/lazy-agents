"""
MCP server management API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encrypt_secret, verify_api_key
from app.mcp import MCPServerLifecycleError, MCPServerManager, MCPServerNotFoundError
from app.models.mcp_server import MCPServer

router = APIRouter(prefix="/api/mcp", dependencies=[Depends(verify_api_key)])


def _encrypt_env(env: Dict[str, str]) -> Dict[str, str]:
    """Encrypt environment variable values before database persistence."""
    return {key: encrypt_secret(value) for key, value in env.items()}


def _mask_env(env: Dict[str, str]) -> Dict[str, str]:
    """Expose only masked environment values in API responses."""
    return {key: "********" for key in env.keys()}


def _to_response(server: MCPServer) -> "MCPServerResponse":
    return MCPServerResponse(
        id=server.id,
        name=server.name,
        description=server.description,
        command=server.command,
        args=server.args,
        env=_mask_env(server.env or {}),
        enabled=server.enabled,
        status=server.status,
        tools_detected=server.tools_detected or [],
        last_error=server.last_error,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


def _get_manager(request: Request) -> MCPServerManager:
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP lifecycle manager is unavailable",
        )
    return manager


class MCPServerBase(BaseModel):
    """Shared request payload fields for MCP server writes."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    command: str = Field(..., min_length=1, max_length=500)
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True

    @field_validator("name", "command")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be blank")
        return trimmed

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("args")
    @classmethod
    def validate_args(cls, value: List[str]) -> List[str]:
        for index, item in enumerate(value):
            if not isinstance(item, str):
                raise ValueError(f"args[{index}] must be a string")
            if not item.strip():
                raise ValueError(f"args[{index}] must not be blank")
        return value

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: Dict[str, str]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, item in value.items():
            normalized_key = key.strip()
            if not normalized_key:
                raise ValueError("env keys must not be blank")
            if not isinstance(item, str):
                raise ValueError(f"env.{normalized_key} must be a string")
            normalized[normalized_key] = item
        return normalized


class MCPServerCreate(MCPServerBase):
    """Schema for creating MCP servers."""


class MCPServerUpdate(BaseModel):
    """Schema for partial MCP server updates."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    command: Optional[str] = Field(default=None, min_length=1, max_length=500)
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None

    @field_validator("name", "command")
    @classmethod
    def validate_non_blank_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be blank")
        return trimmed

    @field_validator("description")
    @classmethod
    def normalize_description_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("args")
    @classmethod
    def validate_args_optional(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        for index, item in enumerate(value):
            if not isinstance(item, str):
                raise ValueError(f"args[{index}] must be a string")
            if not item.strip():
                raise ValueError(f"args[{index}] must not be blank")
        return value

    @field_validator("env")
    @classmethod
    def validate_env_optional(cls, value: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        if value is None:
            return None
        normalized: Dict[str, str] = {}
        for key, item in value.items():
            normalized_key = key.strip()
            if not normalized_key:
                raise ValueError("env keys must not be blank")
            if not isinstance(item, str):
                raise ValueError(f"env.{normalized_key} must be a string")
            normalized[normalized_key] = item
        return normalized


class MCPServerResponse(BaseModel):
    """MCP server response schema with masked environment values."""

    id: str
    name: str
    description: Optional[str]
    command: str
    args: List[str]
    env: Dict[str, str]
    enabled: bool
    status: str
    tools_detected: List[Dict[str, object]]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(db: AsyncSession = Depends(get_db)):
    """List configured MCP servers."""
    result = await db.execute(select(MCPServer))
    servers = result.scalars().all()
    return [_to_response(server) for server in servers]


@router.post("/servers", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_data: MCPServerCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new MCP server configuration."""
    server = MCPServer(
        name=server_data.name,
        description=server_data.description,
        command=server_data.command,
        args=server_data.args,
        env=_encrypt_env(server_data.env),
        enabled=server_data.enabled,
        status="stopped",
        tools_detected=[],
        last_error=None,
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return _to_response(server)


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an MCP server by ID."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )
    return _to_response(server)


@router.put("/servers/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: str,
    server_data: MCPServerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an MCP server configuration."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )

    updates = server_data.model_dump(exclude_unset=True)
    if "env" in updates:
        updates["env"] = _encrypt_env(updates["env"] or {})

    for field_name, value in updates.items():
        setattr(server, field_name, value)

    await db.commit()
    await db.refresh(server)
    return _to_response(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an MCP server configuration."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )

    await db.delete(server)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/servers/{server_id}/restart", response_model=MCPServerResponse)
async def restart_mcp_server(
    server_id: str,
    request: Request,
):
    """Restart an MCP runtime and return the persisted lifecycle state."""

    manager = _get_manager(request)
    try:
        server = await manager.restart_server(server_id)
        return _to_response(server)
    except MCPServerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except MCPServerLifecycleError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/servers/{server_id}/sync", response_model=MCPServerResponse)
async def sync_mcp_server(
    server_id: str,
    request: Request,
):
    """Sync tool discovery for an MCP runtime and return updated state."""

    manager = _get_manager(request)
    try:
        server = await manager.sync_server(server_id)
        return _to_response(server)
    except MCPServerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except MCPServerLifecycleError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
