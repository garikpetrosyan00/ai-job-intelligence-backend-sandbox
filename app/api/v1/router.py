"""Central API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_sync,
    applications,
    auth,
    health,
    job_sources,
    jobs,
    saved_jobs,
    users,
)


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(job_sources.router)
api_router.include_router(admin_sync.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(saved_jobs.router)
api_router.include_router(applications.router)
