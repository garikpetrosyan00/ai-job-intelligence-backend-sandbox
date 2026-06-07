from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.saved_job import SavedJob
from app.repositories.job import JobRepository
from app.repositories.saved_job import SavedJobRepository


class SavedJobService:
    def __init__(
        self,
        repository: SavedJobRepository | None = None,
        job_repository: JobRepository | None = None,
    ) -> None:
        self.repository = repository or SavedJobRepository()
        self.job_repository = job_repository or JobRepository()

    def save_job(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
    ) -> SavedJob:
        job = self.job_repository.get_job_by_id(
            db=db,
            job_id=job_id,
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        existing_saved_job = self.repository.get_by_user_and_job(
            db=db,
            user_id=user_id,
            job_id=job_id,
        )

        if existing_saved_job is not None:
            return existing_saved_job

        try:
            saved_job = self.repository.create(
                db=db,
                user_id=user_id,
                job_id=job_id,
            )
            db.commit()
            db.refresh(saved_job)

            return saved_job
        except IntegrityError:
            db.rollback()

            existing_saved_job = self.repository.get_by_user_and_job(
                db=db,
                user_id=user_id,
                job_id=job_id,
            )

            if existing_saved_job is None:
                raise

            return existing_saved_job

    def list_saved_jobs(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> list[SavedJob]:
        return self.repository.list_for_user(
            db=db,
            user_id=user_id,
        )
