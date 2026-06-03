from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_source import JobSource


class JobSourceRepository:
    def get_by_id(self, db: Session, source_id: int) -> JobSource | None:
        statement = select(JobSource).where(JobSource.id == source_id)

        return db.scalars(statement).first()

    def list_sources(self, db: Session, limit: int, offset: int) -> list[JobSource]:
        statement = (
            select(JobSource)
            .order_by(JobSource.id.asc())
            .limit(limit)
            .offset(offset)
        )

        return list(db.scalars(statement).all())
