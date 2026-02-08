"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

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

    readiness = "ready" if checks["database"] == "ok" else "not_ready"
    http_status = (
        status.HTTP_200_OK if readiness == "ready" else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "status": readiness,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        },
    )
