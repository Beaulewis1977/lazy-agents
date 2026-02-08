import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Ensure local backend package imports resolve under direct pytest invocation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load_app_modules():
    from app.api.mcp import router as mcp_router
    from app.core.database import Base, get_db
    from app.mcp.manager import MCPServerManager

    return mcp_router, Base, get_db, MCPServerManager


@pytest.fixture
def app_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/mcp-lifecycle-env.db")
    return _load_app_modules()


class FakeMCPClientModule:
    """In-memory MCP client double for lifecycle/state transition testing."""

    def __init__(self):
        self.fail_start: str | None = None
        self.fail_sync: str | None = None
        self.start_tools = [
            {
                "name": "filesystem_read",
                "description": "Read file content",
                "inputSchema": {"type": "object"},
            }
        ]
        self.sync_tools = [
            {
                "name": "filesystem_write",
                "description": "Write file content",
                "inputSchema": {"type": "object"},
            }
        ]
        self.closed_handles: list[SimpleNamespace] = []

    async def start_runtime_session(self, command, args, env):
        if self.fail_start:
            raise RuntimeError(self.fail_start)
        session = SimpleNamespace()
        handle = SimpleNamespace(session=session)
        return handle, list(self.start_tools)

    async def list_tools(self, session):
        if self.fail_sync:
            raise RuntimeError(self.fail_sync)
        return list(self.sync_tools)

    async def close_runtime_session(self, handle):
        self.closed_handles.append(handle)


@pytest_asyncio.fixture
async def db_session_factory(app_modules, tmp_path):
    _, Base, _, _ = app_modules
    db_url = f"sqlite+aiosqlite:///{tmp_path}/mcp-lifecycle-test.db"
    engine = create_async_engine(db_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield session_factory

    await engine.dispose()


@pytest_asyncio.fixture
async def test_app(app_modules, db_session_factory):
    mcp_router, _, get_db, MCPServerManager = app_modules
    app = FastAPI()
    app.include_router(mcp_router)

    fake_client = FakeMCPClientModule()
    app.state.mcp_manager = MCPServerManager(
        session_factory=db_session_factory,
        mcp_client_module=fake_client,
    )

    async def override_get_db():
        session = db_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest_asyncio.fixture
async def test_client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as client:
        yield client


async def _create_server(test_client: AsyncClient) -> str:
    payload = {
        "name": "Lifecycle MCP",
        "description": "Lifecycle tests",
        "command": "python",
        "args": ["server.py"],
        "env": {"TOKEN": "secret-token"},
        "enabled": True,
    }

    response = await test_client.post("/api/mcp/servers", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_restart_and_sync_endpoints_return_updated_status(test_client, test_app):
    server_id = await _create_server(test_client)

    restart_response = await test_client.post(f"/api/mcp/servers/{server_id}/restart")
    assert restart_response.status_code == 200
    restarted = restart_response.json()
    assert restarted["status"] == "running"
    assert restarted["last_error"] is None
    assert restarted["tools_detected"] == test_app.state.mcp_manager._client.start_tools

    sync_response = await test_client.post(f"/api/mcp/servers/{server_id}/sync")
    assert sync_response.status_code == 200
    synced = sync_response.json()
    assert synced["status"] == "running"
    assert synced["last_error"] is None
    assert synced["tools_detected"] == test_app.state.mcp_manager._client.sync_tools


@pytest.mark.asyncio
async def test_restart_failure_surfaces_actionable_last_error(test_client, test_app):
    server_id = await _create_server(test_client)
    test_app.state.mcp_manager._client.fail_start = "python executable not found"

    restart_response = await test_client.post(f"/api/mcp/servers/{server_id}/restart")
    assert restart_response.status_code == 500
    assert "python executable not found" in restart_response.json()["detail"]

    get_response = await test_client.get(f"/api/mcp/servers/{server_id}")
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["status"] == "error"
    assert "python executable not found" in (payload["last_error"] or "")


@pytest.mark.asyncio
async def test_running_to_error_transition_is_visible_after_sync_failure(test_client, test_app):
    server_id = await _create_server(test_client)

    restart_response = await test_client.post(f"/api/mcp/servers/{server_id}/restart")
    assert restart_response.status_code == 200
    assert restart_response.json()["status"] == "running"

    test_app.state.mcp_manager._client.fail_sync = "tool discovery timeout"
    sync_response = await test_client.post(f"/api/mcp/servers/{server_id}/sync")
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()
    assert sync_payload["status"] == "error"
    assert "tool discovery timeout" in (sync_payload["last_error"] or "")

    list_response = await test_client.get("/api/mcp/servers")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == server_id
    assert listed[0]["status"] == "error"
    assert "tool discovery timeout" in (listed[0]["last_error"] or "")
