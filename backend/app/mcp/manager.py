"""Lifecycle manager for MCP server runtimes and persisted state transitions."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decrypt_secret
from app.mcp import client
from app.models.mcp_server import MCPServer

logger = structlog.get_logger(__name__)


class MCPServerNotFoundError(ValueError):
    """Raised when an MCP server ID does not exist in persistence."""


class MCPServerLifecycleError(RuntimeError):
    """Raised when runtime lifecycle operations fail."""


@dataclass
class RuntimeEntry:
    """In-memory registry entry for a running MCP server process/session."""

    handle: client.MCPRuntimeHandle


class MCPServerManager:
    """Controls MCP runtime processes and keeps DB state synchronized."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession] | None = None,
        mcp_client_module: Any = client,
    ) -> None:
        self._session_factory = session_factory or async_session
        self._client = mcp_client_module
        self._runtimes: dict[str, RuntimeEntry] = {}
        self._lock = asyncio.Lock()

    async def start_enabled_servers(self) -> None:
        """Start all enabled MCP servers and persist failures per server."""

        async with self._session_factory() as db:
            result = await db.execute(select(MCPServer.id).where(MCPServer.enabled.is_(True)))
            server_ids = [row[0] for row in result.all()]

        for server_id in server_ids:
            try:
                await self.start_server(server_id)
            except Exception as exc:
                # Failure details are already persisted by start_server.
                logger.warning(
                    "Failed to auto-start MCP server during bootstrap",
                    server_id=server_id,
                    error=str(exc),
                )
                continue

    async def start_server(self, server_id: str) -> MCPServer:
        """Transition to starting, initialize runtime, then persist running/error."""

        try:
            config = await self._mark_starting(server_id)
            async with self._lock:
                old_runtime = self._runtimes.pop(server_id, None)
                if old_runtime:
                    await self._safe_close(server_id, old_runtime)

                runtime_handle, tools = await self._client.start_runtime_session(
                    command=config["command"],
                    args=config["args"],
                    env=config["env"],
                )
                self._runtimes[server_id] = RuntimeEntry(handle=runtime_handle)

            return await self._persist_state(
                server_id,
                status="running",
                last_error=None,
                tools_detected=tools,
            )
        except Exception as exc:
            error_text = self._format_error("startup", exc)
            await self._persist_state(server_id, status="error", last_error=error_text)
            raise MCPServerLifecycleError(error_text) from exc

    async def stop_server(self, server_id: str) -> MCPServer:
        """Stop a running MCP runtime and persist stopped state."""

        async with self._lock:
            runtime = self._runtimes.pop(server_id, None)
            if runtime:
                await self._safe_close(server_id, runtime)

            return await self._persist_state(
                server_id,
                status="stopped",
                last_error=None,
            )

    async def restart_server(self, server_id: str) -> MCPServer:
        """Restart MCP runtime by stop then start."""

        await self.stop_server(server_id)
        return await self.start_server(server_id)

    async def sync_server(self, server_id: str) -> MCPServer:
        """Refresh discovered tools and persist current lifecycle state."""

        if server_id not in self._runtimes:
            await self.start_server(server_id)

        async with self._lock:
            runtime = self._runtimes.get(server_id)
            if runtime is None:
                raise MCPServerLifecycleError(
                    f"Server {server_id} has no active runtime after startup"
                )

            try:
                tools = await self._client.list_tools(runtime.handle.session)
                return await self._persist_state(
                    server_id,
                    status="running",
                    last_error=None,
                    tools_detected=tools,
                )
            except Exception as exc:
                error_text = self._format_error("sync", exc)
                await self._safe_close(server_id, runtime)
                self._runtimes.pop(server_id, None)
                return await self._persist_state(
                    server_id,
                    status="error",
                    last_error=error_text,
                )

    async def shutdown_all(self) -> None:
        """Stop all tracked MCP runtimes during app shutdown."""

        async with self._lock:
            runtime_items = list(self._runtimes.items())
            self._runtimes.clear()

        for server_id, runtime in runtime_items:
            try:
                await self._safe_close(server_id, runtime)
                await self._persist_state(server_id, status="stopped", last_error=None)
            except Exception as exc:
                await self._persist_state(
                    server_id,
                    status="error",
                    last_error=self._format_error("shutdown", exc),
                )

    async def get_server(self, server_id: str) -> MCPServer:
        """Fetch current server row for API response serialization."""

        async with self._session_factory() as db:
            server = await self._load_server(db, server_id)
            await db.refresh(server)
            return server

    async def _mark_starting(self, server_id: str) -> dict[str, Any]:
        """Persist `starting` state and return runtime launch configuration."""

        async with self._session_factory() as db:
            server = await self._load_server(db, server_id)
            server.status = "starting"
            server.last_error = None
            await db.commit()
            await db.refresh(server)

            return {
                "command": server.command,
                "args": list(server.args or []),
                "env": self._decrypt_env(server.env or {}),
            }

    async def _persist_state(
        self,
        server_id: str,
        *,
        status: str,
        last_error: str | None,
        tools_detected: list[dict[str, Any]] | None = None,
    ) -> MCPServer:
        """Persist status boundary changes used by lifecycle operations."""

        async with self._session_factory() as db:
            server = await self._load_server(db, server_id)
            server.status = status
            server.last_error = last_error
            if tools_detected is not None:
                server.tools_detected = tools_detected
            await db.commit()
            await db.refresh(server)
            return server

    async def _load_server(self, db: AsyncSession, server_id: str) -> MCPServer:
        """Load an MCP server row or raise a typed not-found error."""

        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if server is None:
            raise MCPServerNotFoundError(f"MCP server {server_id} not found")
        return server

    def _decrypt_env(self, env: dict[str, str]) -> dict[str, str]:
        """Decrypt persisted env payload before runtime startup."""

        decrypted: dict[str, str] = {}
        for key, value in env.items():
            try:
                decrypted[key] = decrypt_secret(value)
            except Exception as exc:
                raise MCPServerLifecycleError(f"Unable to decrypt env var '{key}': {exc}") from exc
        return decrypted

    async def _safe_close(self, server_id: str, runtime: RuntimeEntry) -> None:
        """Close runtime resources and normalize close-time errors."""

        try:
            await self._client.close_runtime_session(runtime.handle)
        except Exception as exc:
            raise MCPServerLifecycleError(
                self._format_error(f"closing runtime for {server_id}", exc)
            ) from exc

    @staticmethod
    def _format_error(action: str, exc: Exception) -> str:
        """Build deterministic error text for operator-facing last_error fields."""

        return f"MCP {action} failed: {exc.__class__.__name__}: {exc}"
