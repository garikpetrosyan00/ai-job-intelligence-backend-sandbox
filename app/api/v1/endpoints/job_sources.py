from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job_source import JobSourceRead
from app.services.job_source import JobSourceService


router = APIRouter(prefix="/job-sources", tags=["job-sources"])
job_source_service = JobSourceService()


@router.get("", response_model=list[JobSourceRead])
def list_job_sources(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return job_source_service.list_sources(db=db, limit=limit, offset=offset)
