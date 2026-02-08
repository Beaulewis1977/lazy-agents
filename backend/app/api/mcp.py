"""
MCP server management API endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encrypt_secret, verify_api_key
from app.mcp import MCPServerLifecycleError, MCPServerManager, MCPServerNotFoundError
from app.models.mcp_server import MCPServer

router = APIRouter(prefix="/api/mcp", dependencies=[Depends(verify_api_key)])


def _encrypt_env(env: dict[str, str]) -> dict[str, str]:
    """Encrypt environment variable values before database persistence."""
    return {key: encrypt_secret(value) for key, value in env.items()}


def _mask_env(env: dict[str, str]) -> dict[str, str]:
    """Expose only masked environment values in API responses."""
    return dict.fromkeys(env, "********")


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
    description: str | None = None
    command: str = Field(..., min_length=1, max_length=500)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
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
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("args")
    @classmethod
    def validate_args(cls, value: list[str]) -> list[str]:
        for index, item in enumerate(value):
            if not isinstance(item, str):
                raise ValueError(f"args[{index}] must be a string")
            if not item.strip():
                raise ValueError(f"args[{index}] must not be blank")
        return value

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
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

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    command: str | None = Field(default=None, min_length=1, max_length=500)
    args: list[str] | None = None
    env: dict[str, str] | None = None
    merge_env: bool | None = None
    enabled: bool | None = None

    @field_validator("name", "command")
    @classmethod
    def validate_non_blank_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be blank")
        return trimmed

    @field_validator("description")
    @classmethod
    def normalize_description_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("args")
    @classmethod
    def validate_args_optional(cls, value: list[str] | None) -> list[str] | None:
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
    def validate_env_optional(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        normalized: dict[str, str] = {}
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
    description: str | None
    command: str
    args: list[str]
    env: dict[str, str]
    enabled: bool
    status: str
    tools_detected: list[dict[str, object]]
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/servers", response_model=list[MCPServerResponse])
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
    merge_env = bool(updates.pop("merge_env", False))
    if "env" in updates:
        encrypted_env = _encrypt_env(updates["env"] or {})
        if merge_env:
            merged_env = dict(server.env or {})
            merged_env.update(encrypted_env)
            updates["env"] = merged_env
        else:
            updates["env"] = encrypted_env

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
