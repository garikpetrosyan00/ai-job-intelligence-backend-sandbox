from datetime import datetime
from typing import Any

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

    def get_by_source_and_external_id(
        self,
        db: Session,
        *,
        source_id: int,
        external_id: str,
    ) -> Job | None:
        statement = select(Job).where(
            Job.source_id == source_id,
            Job.external_id == external_id,
        )

        return db.scalars(statement).first()

    def create(
        self,
        db: Session,
        *,
        source_id: int,
        company_id: int | None,
        external_id: str,
        title: str,
        description: str | None,
        location: str | None,
        apply_url: str | None,
        published_at: datetime | None,
        raw_payload: dict[str, Any],
    ) -> Job:
        job = Job(
            source_id=source_id,
            company_id=company_id,
            external_id=external_id,
            title=title,
            description=description,
            location=location,
            apply_url=apply_url,
            published_at=published_at,
            raw_payload=raw_payload,
        )

        db.add(job)
        db.flush()

        return job

    def update_from_external(
        self,
        db: Session,
        *,
        job: Job,
        company_id: int | None,
        title: str,
        description: str | None,
        location: str | None,
        apply_url: str | None,
        published_at: datetime | None,
        raw_payload: dict[str, Any],
    ) -> Job:
        job.company_id = company_id
        job.title = title
        job.description = description
        job.location = location
        job.apply_url = apply_url
        job.published_at = published_at
        job.raw_payload = raw_payload

        db.flush()

        return job
