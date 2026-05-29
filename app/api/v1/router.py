"""Central API router.

Day 3 adds read-only jobs and job sources endpoints using
route -> service -> repository layering.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, job_sources, jobs


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(job_sources.router)
