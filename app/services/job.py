from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.job import JobRepository


class JobService:
    def __init__(self, repository: JobRepository | None = None) -> None:
        self.repository = repository or JobRepository()

    def list_jobs(self, db: Session, limit: int, offset: int) -> list[Job]:
        return self.repository.list_jobs(db=db, limit=limit, offset=offset)

    def get_job_by_id(self, db: Session, job_id: int) -> Job:
        job = self.repository.get_job_by_id(db=db, job_id=job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        return job
