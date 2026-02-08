"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check including dependencies."""
    checks = {
        "llm_providers": settings.available_providers,
    }

    # Check Database
    try:
        from sqlalchemy import text

        from app.core.database import async_session

        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e!s}"

    status_code = "ready" if checks["database"] == "ok" else "not_ready"

    return {"status": status_code, "timestamp": datetime.utcnow().isoformat(), "checks": checks}
