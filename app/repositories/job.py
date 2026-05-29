from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.job import Job


class JobRepository:
    def list_jobs(self, db: Session, limit: int, offset: int) -> list[Job]:
        statement = (
            select(Job)
            .options(
                selectinload(Job.company),
                selectinload(Job.source),
            )
            .order_by(Job.created_at.desc(), Job.id.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(db.scalars(statement).all())

    def get_job_by_id(self, db: Session, job_id: int) -> Job | None:
        statement = (
            select(Job)
            .options(
                selectinload(Job.company),
                selectinload(Job.source),
            )
            .where(Job.id == job_id)
        )

        return db.scalars(statement).first()
