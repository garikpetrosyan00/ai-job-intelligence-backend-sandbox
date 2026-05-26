"""Central API router.

For Day 1 we expose only /health.
Later days will add jobs, auth, admin sync, applications, and AI routes here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router)
