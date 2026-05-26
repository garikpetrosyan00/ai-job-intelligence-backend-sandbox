"""FastAPI application entry point for the AI Job Intelligence Backend sandbox."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )

    # Day 1 keeps /health at root level for a simple smoke check.
    # Later API resources can be mounted under /api/v1.
    app.include_router(api_router)

    return app


app = create_app()
