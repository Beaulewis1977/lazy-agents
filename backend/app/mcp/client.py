"""MCP client/session helpers built on the official MCP Python SDK."""

from __future__ import annotations

from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any


class MCPClientError(RuntimeError):
    """Raised when MCP SDK operations fail."""


@dataclass
class MCPRuntimeHandle:
    """Holds active MCP session resources for a running server."""

    session: Any
    exit_stack: AsyncExitStack


async def start_runtime_session(
    command: str,
    args: list[str],
    env: dict[str, str],
) -> tuple[MCPRuntimeHandle, list[dict[str, Any]]]:
    """Start an MCP stdio client/session and return discovered tools."""

    StdioServerParameters, stdio_client, ClientSession = _load_mcp_sdk()
    exit_stack = AsyncExitStack()

    try:
        parameters = StdioServerParameters(
            command=command,
            args=args,
            env=env or None,
        )

        read_stream, write_stream = await exit_stack.enter_async_context(stdio_client(parameters))
        session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()

        tools = await list_tools(session)
        return MCPRuntimeHandle(session=session, exit_stack=exit_stack), tools
    except Exception as exc:  # pragma: no cover - exercised via manager tests
        await exit_stack.aclose()
        raise MCPClientError(f"Failed to start MCP runtime session: {exc}") from exc


async def list_tools(session: Any) -> list[dict[str, Any]]:
    """Return normalized tool payloads from ClientSession.list_tools."""

    try:
        response = await session.list_tools()
        raw_tools = getattr(response, "tools", response)
    except Exception as exc:  # pragma: no cover - exercised via manager tests
        raise MCPClientError(f"Failed to list MCP tools: {exc}") from exc

    normalized: list[dict[str, Any]] = []
    for tool in raw_tools or []:
        if hasattr(tool, "model_dump"):
            normalized.append(tool.model_dump())
            continue
        if isinstance(tool, dict):
            normalized.append(tool)
            continue

        normalized.append(
            {
                "name": getattr(tool, "name", "unknown"),
                "description": getattr(tool, "description", ""),
                "inputSchema": getattr(tool, "inputSchema", None),
            }
        )

    return normalized


async def call_tool(session: Any, tool_name: str, arguments: dict[str, Any]) -> Any:
    """Call a single tool on an initialized MCP session."""

    try:
        return await session.call_tool(tool_name, arguments)
    except Exception as exc:  # pragma: no cover - used in later phases
        raise MCPClientError(f"Failed to call MCP tool '{tool_name}': {exc}") from exc


async def close_runtime_session(handle: MCPRuntimeHandle) -> None:
    """Close all session resources for a runtime handle."""

    await handle.exit_stack.aclose()


def _load_mcp_sdk() -> tuple[Any, Any, Any]:
    """Import MCP SDK objects lazily so tests can run without mcp installed."""

    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        return StdioServerParameters, stdio_client, ClientSession
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise MCPClientError(
            "MCP Python SDK is not installed. Add 'mcp' to backend dependencies."
        ) from exc
