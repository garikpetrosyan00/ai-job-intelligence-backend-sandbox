from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobRead
from app.services.job import JobService


router = APIRouter(prefix="/jobs", tags=["jobs"])
job_service = JobService()


@router.get("", response_model=list[JobRead])
def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return job_service.list_jobs(db=db, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    return job_service.get_job_by_id(db=db, job_id=job_id)
