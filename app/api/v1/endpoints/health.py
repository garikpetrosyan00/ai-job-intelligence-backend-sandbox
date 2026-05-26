"""Health endpoint used for local smoke checks and deployment readiness."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a small health response proving the API process is running."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }
