from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.job import Job
from app.models.saved_job import SavedJob


class SavedJobRepository:
    def get_by_user_and_job(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
    ) -> SavedJob | None:
        statement = (
            select(SavedJob)
            .options(
                selectinload(SavedJob.job).selectinload(Job.company),
                selectinload(SavedJob.job).selectinload(Job.source),
            )
            .where(
                SavedJob.user_id == user_id,
                SavedJob.job_id == job_id,
            )
        )

        return db.scalars(statement).first()

    def list_for_user(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> list[SavedJob]:
        statement = (
            select(SavedJob)
            .options(
                selectinload(SavedJob.job).selectinload(Job.company),
                selectinload(SavedJob.job).selectinload(Job.source),
            )
            .where(SavedJob.user_id == user_id)
            .order_by(SavedJob.created_at.desc(), SavedJob.id.desc())
        )

        return list(db.scalars(statement).all())

    def create(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
    ) -> SavedJob:
        saved_job = SavedJob(
            user_id=user_id,
            job_id=job_id,
        )

        db.add(saved_job)
        db.flush()

        return saved_job
