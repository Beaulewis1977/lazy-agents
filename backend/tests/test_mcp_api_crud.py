import sys
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Ensure local backend package imports resolve under direct pytest invocation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load_app_modules():
    from app.api.mcp import router as mcp_router
    from app.core.database import Base, get_db
    from app.models.mcp_server import MCPServer

    return mcp_router, Base, get_db, MCPServer


@pytest.fixture
def app_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/mcp-crud-env.db")
    monkeypatch.setenv("APP_DEBUG", "true")
    return _load_app_modules()


@pytest_asyncio.fixture
async def db_session_factory(app_modules, tmp_path):
    _, Base, _, _ = app_modules
    db_url = f"sqlite+aiosqlite:///{tmp_path}/mcp-crud-test.db"
    engine = create_async_engine(db_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield session_factory

    await engine.dispose()


@pytest_asyncio.fixture
async def test_client(app_modules, db_session_factory):
    from app.core.security import verify_api_key

    mcp_router, _, get_db, _ = app_modules
    app = FastAPI()
    app.include_router(mcp_router)

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

    def override_verify_api_key():
        """Allow all requests in test mode."""
        return True

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_mcp_server_crud_lifecycle(test_client):
    create_payload = {
        "name": "Filesystem MCP",
        "description": "Serves filesystem tools",
        "command": "npx",
        "args": ["@modelcontextprotocol/server-filesystem", "."],
        "env": {"API_TOKEN": "super-secret-token"},
        "enabled": True,
    }

    create_response = await test_client.post("/api/mcp/servers", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    server_id = created["id"]

    assert created["name"] == create_payload["name"]
    assert created["status"] == "stopped"
    assert created["tools_detected"] == []
    assert created["last_error"] is None
    assert created["env"] == {"API_TOKEN": "********"}

    list_response = await test_client.get("/api/mcp/servers")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == server_id

    get_response = await test_client.get(f"/api/mcp/servers/{server_id}")
    assert get_response.status_code == 200
    assert get_response.json()["env"] == {"API_TOKEN": "********"}

    update_payload = {
        "name": "Filesystem MCP Updated",
        "args": ["node", "mcp-server.js"],
        "env": {"API_TOKEN": "rotated-secret"},
        "enabled": False,
    }
    update_response = await test_client.put(
        f"/api/mcp/servers/{server_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == update_payload["name"]
    assert updated["args"] == update_payload["args"]
    assert updated["enabled"] is False
    assert updated["env"] == {"API_TOKEN": "********"}

    delete_response = await test_client.delete(f"/api/mcp/servers/{server_id}")
    assert delete_response.status_code == 204
    assert delete_response.text == ""

    get_deleted_response = await test_client.get(f"/api/mcp/servers/{server_id}")
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_mcp_server_validation_errors_are_actionable(test_client):
    missing_required = {
        "name": "Invalid",
        "args": [],
        "env": {},
        "enabled": True,
    }
    missing_required_response = await test_client.post(
        "/api/mcp/servers",
        json=missing_required,
    )
    assert missing_required_response.status_code == 422
    assert "command" in str(missing_required_response.json()["detail"])

    invalid_args_type = {
        "name": "Invalid Args",
        "command": "npx",
        "args": "not-a-list",
        "env": {},
        "enabled": True,
    }
    invalid_args_response = await test_client.post(
        "/api/mcp/servers",
        json=invalid_args_type,
    )
    assert invalid_args_response.status_code == 422
    assert "args" in str(invalid_args_response.json()["detail"])

    invalid_env_shape = {
        "name": "Invalid Env",
        "command": "npx",
        "args": [],
        "env": ["NOT", "AN", "OBJECT"],
        "enabled": True,
    }
    invalid_env_response = await test_client.post(
        "/api/mcp/servers",
        json=invalid_env_shape,
    )
    assert invalid_env_response.status_code == 422
    assert "env" in str(invalid_env_response.json()["detail"])


@pytest.mark.asyncio
async def test_mcp_server_env_values_are_encrypted_at_rest(
    test_client, db_session_factory, app_modules
):
    _, _, _, MCPServer = app_modules
    plain_env_value = "sample-env-value"
    payload = {
        "name": "Encrypted MCP",
        "description": "Checks encrypted storage",
        "command": "python",
        "args": ["server.py"],
        "env": {"TOKEN": plain_env_value},
        "enabled": True,
    }

    create_response = await test_client.post("/api/mcp/servers", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["env"] == {"TOKEN": "********"}

    async with db_session_factory() as session:
        result = await session.execute(select(MCPServer).where(MCPServer.id == created["id"]))
        persisted = result.scalar_one()

    assert persisted.env["TOKEN"] != plain_env_value
    assert isinstance(persisted.env["TOKEN"], str)
    assert len(persisted.env["TOKEN"]) > 20


@pytest.mark.asyncio
async def test_mcp_server_update_can_merge_env_without_overwriting_existing_keys(test_client):
    create_payload = {
        "name": "Merge Env MCP",
        "description": "Checks env merge behavior",
        "command": "python",
        "args": ["server.py"],
        "env": {
            "API_TOKEN": "original-token",
            "ORG_ID": "org-123",
        },
        "enabled": True,
    }

    create_response = await test_client.post("/api/mcp/servers", json=create_payload)
    assert create_response.status_code == 201
    server_id = create_response.json()["id"]

    update_payload = {
        "env": {"API_TOKEN": "rotated-token", "REGION": "us-east-1"},
        "merge_env": True,
    }
    update_response = await test_client.put(
        f"/api/mcp/servers/{server_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200

    get_response = await test_client.get(f"/api/mcp/servers/{server_id}")
    assert get_response.status_code == 200
    assert get_response.json()["env"] == {
        "API_TOKEN": "********",
        "ORG_ID": "********",
        "REGION": "********",
    }
