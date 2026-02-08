"""
Integrations API endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key, encrypt_secret

router = APIRouter(dependencies=[Depends(verify_api_key)])


# =============================================================================
# Schemas
# =============================================================================

class IntegrationCreate(BaseModel):
    """Schema for creating an integration."""
    type: str
    name: str
    credentials: Dict[str, str] = {}
    permissions: List[str] = []
    config: Dict[str, Any] = {}


class IntegrationResponse(BaseModel):
    """Schema for integration response (no secrets exposed)."""
    id: str
    type: str
    name: str
    status: str
    permissions: List[str]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class IntegrationTypeInfo(BaseModel):
    """Information about a supported integration type."""
    type: str
    name: str
    description: str
    required_credentials: List[str]
    available_permissions: List[str]


# =============================================================================
# Supported Integration Types
# =============================================================================

INTEGRATION_TYPES = {
    "github": IntegrationTypeInfo(
        type="github",
        name="GitHub",
        description="Connect to GitHub repositories",
        required_credentials=["token"],
        available_permissions=["read:repos", "write:issues", "read:issues", "write:prs"],
    ),
    "discord": IntegrationTypeInfo(
        type="discord",
        name="Discord",
        description="Connect to Discord servers",
        required_credentials=["bot_token"],
        available_permissions=["send_messages", "read_messages", "manage_channels"],
    ),
    "slack": IntegrationTypeInfo(
        type="slack",
        name="Slack",
        description="Connect to Slack workspaces",
        required_credentials=["bot_token", "signing_secret"],
        available_permissions=["chat:write", "channels:read", "files:read"],
    ),
    "notion": IntegrationTypeInfo(
        type="notion",
        name="Notion",
        description="Connect to Notion workspaces",
        required_credentials=["api_key"],
        available_permissions=["read_content", "write_content", "read_databases"],
    ),
    "webhook": IntegrationTypeInfo(
        type="webhook",
        name="Webhook",
        description="Generic webhook integration",
        required_credentials=[],
        available_permissions=["send", "receive"],
    ),
    "openai": IntegrationTypeInfo(
        type="openai",
        name="OpenAI",
        description="OpenAI API for GPT models",
        required_credentials=["api_key"],
        available_permissions=["chat"],
    ),
    "anthropic": IntegrationTypeInfo(
        type="anthropic",
        name="Anthropic",
        description="Anthropic API for Claude models",
        required_credentials=["api_key"],
        available_permissions=["chat"],
    ),
    "google": IntegrationTypeInfo(
        type="google",
        name="Google Gemini",
        description="Google AI for Gemini models",
        required_credentials=["api_key"],
        available_permissions=["generate_content"],
    ),
}


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/types", response_model=List[IntegrationTypeInfo])
async def list_integration_types():
    """List all supported integration types."""
    return list(INTEGRATION_TYPES.values())


@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all configured integrations."""
    from app.models.integration import Integration

    query = select(Integration)
    if type:
        query = query.where(Integration.type == type)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_data: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new integration."""
    from app.models.integration import Integration
    import json

    # Validate integration type
    if integration_data.type not in INTEGRATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown integration type: {integration_data.type}",
        )

    # Validate required credentials
    type_info = INTEGRATION_TYPES[integration_data.type]
    for cred in type_info.required_credentials:
        if cred not in integration_data.credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required credential: {cred}",
            )

    # Encrypt credentials
    encrypted_creds = encrypt_secret(json.dumps(integration_data.credentials))

    integration = Integration(
        type=integration_data.type,
        name=integration_data.name,
        credentials_encrypted=encrypted_creds,
        permissions=integration_data.permissions,
        config=integration_data.config,
    )

    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return integration


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an integration by ID."""
    from app.models.integration import Integration

    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration {integration_id} not found",
        )

    return integration


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an integration."""
    from app.models.integration import Integration

    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration {integration_id} not found",
        )

    await db.delete(integration)
    await db.commit()


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Test an integration connection."""
    from app.models.integration import Integration

    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration {integration_id} not found",
        )

    # Decrypt credentials
    from app.core.security import decrypt_secret
    import json

    creds = {}
    if integration.credentials_encrypted:
        try:
            creds = json.loads(decrypt_secret(integration.credentials_encrypted))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt credentials",
            )

    try:
        # Test based on type
        if integration.type == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=creds.get("api_key"))
            client.models.list(limit=1)

        elif integration.type == "anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=creds.get("api_key"))
            # Just listing models is a good lightweight check
            # Note: client.models.list() might not be available in older SDKs,
            # but usually messages.create with max_tokens=1 works.
            # Using messages.create as definitive test
            client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}]
            )

        elif integration.type == "google":
            import google.generativeai as genai
            genai.configure(api_key=creds.get("api_key"))
            list(genai.list_models(page_size=1))

        elif integration.type == "github":
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {creds.get('token')}",
                        "Accept": "application/vnd.github.v3+json",
                    }
                )
                resp.raise_for_status()

        elif integration.type == "discord":
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://discord.com/api/v10/users/@me",
                    headers={
                        "Authorization": f"Bot {creds.get('bot_token')}",
                    }
                )
                resp.raise_for_status()

        elif integration.type == "slack":
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://slack.com/api/auth.test",
                    headers={
                        "Authorization": f"Bearer {creds.get('bot_token')}",
                    }
                )
                data = resp.json()
                if not data.get("ok"):
                    raise Exception(f"Slack auth failed: {data.get('error')}")

        # Add other types as needed

        return {
            "status": "ok",
            "message": f"Successfully connected to {integration.name}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
        }
