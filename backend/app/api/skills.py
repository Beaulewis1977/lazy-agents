"""
Skills API endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.skill import Skill

router = APIRouter(dependencies=[Depends(verify_api_key)])


# =============================================================================
# Schemas
# =============================================================================

class SkillResponse(BaseModel):
    """Schema for skill response."""
    id: str
    name: str
    description: Optional[str]
    category: str
    parameters: Dict[str, Any]
    integration_required: Optional[str]
    is_builtin: bool

    class Config:
        from_attributes = True


class SkillCreate(BaseModel):
    """Schema for creating a custom skill."""
    id: str
    name: str
    description: Optional[str] = None
    category: str = "custom"
    parameters: Dict[str, Any] = {}
    integration_required: Optional[str] = None
    implementation: str


# =============================================================================
# Built-in Skills Registry
# =============================================================================

BUILTIN_SKILLS = [
    {
        "id": "github.list_issues",
        "name": "List GitHub Issues",
        "description": "List issues from a GitHub repository",
        "category": "github",
        "parameters": {
            "repo": {"type": "string", "description": "Repository in owner/repo format"},
            "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
            "limit": {"type": "integer", "default": 10},
        },
        "integration_required": "github",
        "is_builtin": True,
    },
    {
        "id": "github.create_issue",
        "name": "Create GitHub Issue",
        "description": "Create a new issue in a GitHub repository",
        "category": "github",
        "parameters": {
            "repo": {"type": "string", "description": "Repository in owner/repo format"},
            "title": {"type": "string", "description": "Issue title"},
            "body": {"type": "string", "description": "Issue body"},
        },
        "integration_required": "github",
        "is_builtin": True,
    },
    {
        "id": "discord.send_message",
        "name": "Send Discord Message",
        "description": "Send a message to a Discord channel",
        "category": "discord",
        "parameters": {
            "channel_id": {"type": "string", "description": "Discord channel ID"},
            "content": {"type": "string", "description": "Message content"},
        },
        "integration_required": "discord",
        "is_builtin": True,
    },
    {
        "id": "http.request",
        "name": "HTTP Request",
        "description": "Make an HTTP request to any URL",
        "category": "http",
        "parameters": {
            "url": {"type": "string", "description": "URL to request"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
            "headers": {"type": "object", "default": {}},
            "body": {"type": "object", "default": None},
        },
        "integration_required": None,
        "is_builtin": True,
    },
    {
        "id": "file.read",
        "name": "Read File",
        "description": "Read contents of a local file",
        "category": "file",
        "parameters": {
            "path": {"type": "string", "description": "File path"},
        },
        "integration_required": None,
        "is_builtin": True,
    },
    {
        "id": "file.write",
        "name": "Write File",
        "description": "Write contents to a local file",
        "category": "file",
        "parameters": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "File content"},
        },
        "integration_required": None,
        "is_builtin": True,
    },
]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("", response_model=List[SkillResponse])
async def list_skills(
    category: Optional[str] = None,
    include_builtin: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all available skills."""
    skills = []

    # Add built-in skills
    if include_builtin:
        for skill_data in BUILTIN_SKILLS:
            if category is None or skill_data["category"] == category:
                skills.append(SkillResponse(**skill_data))

    # Add custom skills from database
    query = select(Skill).where(Skill.is_builtin == False)  # noqa: E712
    if category:
        query = query.where(Skill.category == category)

    result = await db.execute(query)
    for skill in result.scalars().all():
        skills.append(SkillResponse.model_validate(skill))

    return skills


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a skill by ID."""
    # Check built-in skills first
    for skill_data in BUILTIN_SKILLS:
        if skill_data["id"] == skill_id:
            return SkillResponse(**skill_data)

    # Check database
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )

    return skill


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a custom skill."""
    # Check if ID already exists
    result = await db.execute(select(Skill).where(Skill.id == skill_data.id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Skill {skill_data.id} already exists",
        )

    skill = Skill(
        **skill_data.model_dump(),
        is_builtin=False,
        implementation_type="custom",
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Update a custom skill."""
    # Cannot update built-in skills
    for skill_data in BUILTIN_SKILLS:
        if skill_data["id"] == skill_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update built-in skills",
            )

    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )

    # Update fields
    allowed_fields = ["name", "description", "category", "parameters", "implementation"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom skill."""
    # Cannot delete built-in skills
    for skill_data in BUILTIN_SKILLS:
        if skill_data["id"] == skill_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete built-in skills",
            )

    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )

    await db.delete(skill)
    await db.commit()


@router.get("/{skill_id}/config")
async def get_skill_config(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get complete skill configuration including implementation details."""
    # Check built-in skills first
    for skill_data in BUILTIN_SKILLS:
        if skill_data["id"] == skill_id:
            return {
                **skill_data,
                "implementation_type": "native",
                "implementation": None,
                "source_path": None,
                "templates": {},
                "references": [],
            }

    # Check database
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )

    # Parse implementation if it's JSON
    import json
    implementation_data = {}
    if skill.implementation:
        try:
            implementation_data = json.loads(skill.implementation)
        except json.JSONDecodeError:
            implementation_data = {"instructions": skill.implementation}

    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "parameters": skill.parameters,
        "integration_required": skill.integration_required,
        "is_builtin": skill.is_builtin,
        "implementation_type": skill.implementation_type,
        "implementation": implementation_data.get("instructions"),
        "templates": implementation_data.get("templates", {}),
        "references": implementation_data.get("references", []),
        "source_path": skill.source_path if hasattr(skill, 'source_path') else None,
    }


@router.post("/load-from-path")
async def load_skill_from_path(
    path: str,
    db: AsyncSession = Depends(get_db),
):
    """Load a skill from a filesystem path (MD file or folder with SKILL.md)."""
    from app.runtime.skill_loader import SkillLoader

    loader = SkillLoader()
    loaded_skill = loader.load_skill_from_path(path)

    if not loaded_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not load skill from path: {path}",
        )

    # Check if skill already exists
    result = await db.execute(select(Skill).where(Skill.id == loaded_skill.id))
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing skill
        skill_data = loader.to_db_format(loaded_skill)
        for field, value in skill_data.items():
            if field != "id":
                setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return {
            "message": f"Skill '{loaded_skill.id}' updated from {path}",
            "skill": SkillResponse.model_validate(existing),
        }

    # Create new skill
    skill_data = loader.to_db_format(loaded_skill)
    skill = Skill(**skill_data)
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    return {
        "message": f"Skill '{loaded_skill.id}' loaded from {path}",
        "skill": SkillResponse.model_validate(skill),
    }


@router.post("/scan-directory")
async def scan_directory_for_skills(
    directory: str,
    db: AsyncSession = Depends(get_db),
):
    """Scan a directory for skill files and load them all."""
    from app.runtime.skill_loader import SkillLoader

    loader = SkillLoader(skill_dirs=[directory])
    loaded_skills = loader.load_all_skills()

    results = []
    for loaded_skill in loaded_skills:
        try:
            # Check if skill already exists
            result = await db.execute(select(Skill).where(Skill.id == loaded_skill.id))
            existing = result.scalar_one_or_none()

            skill_data = loader.to_db_format(loaded_skill)

            if existing:
                for field, value in skill_data.items():
                    if field != "id":
                        setattr(existing, field, value)
                await db.commit()
                results.append({"id": loaded_skill.id, "status": "updated"})
            else:
                skill = Skill(**skill_data)
                db.add(skill)
                await db.commit()
                results.append({"id": loaded_skill.id, "status": "created"})
        except Exception as e:
            results.append({"id": loaded_skill.id, "status": "error", "error": str(e)})

    return {
        "directory": directory,
        "skills_found": len(loaded_skills),
        "results": results,
    }


@router.get("/categories/list")
async def list_skill_categories(
    db: AsyncSession = Depends(get_db),
):
    """List all available skill categories."""
    categories = set()

    # From built-in skills
    for skill in BUILTIN_SKILLS:
        categories.add(skill["category"])

    # From database
    result = await db.execute(select(Skill.category).distinct())
    for row in result.scalars().all():
        if row:
            categories.add(row)

    return sorted(list(categories))
