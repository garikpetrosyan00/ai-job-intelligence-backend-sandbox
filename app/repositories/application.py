from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.job import Job


class ApplicationRepository:
    def get_by_user_and_job(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
    ) -> Application | None:
        statement = (
            select(Application)
            .options(
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.job).selectinload(Job.source),
            )
            .where(
                Application.user_id == user_id,
                Application.job_id == job_id,
            )
        )

        return db.scalars(statement).first()

    def get_by_id_for_user(
        self,
        db: Session,
        *,
        application_id: int,
        user_id: int,
    ) -> Application | None:
        statement = (
            select(Application)
            .options(
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.job).selectinload(Job.source),
            )
            .where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )

        return db.scalars(statement).first()

    def list_for_user(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> list[Application]:
        statement = (
            select(Application)
            .options(
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.job).selectinload(Job.source),
            )
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc(), Application.id.desc())
        )

        return list(db.scalars(statement).all())

    def create(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
        status: str,
        notes: str | None,
        applied_at: datetime | None,
    ) -> Application:
        application = Application(
            user_id=user_id,
            job_id=job_id,
            status=status,
            notes=notes,
            applied_at=applied_at,
        )

        db.add(application)
        db.flush()

        return application

    def update_status(
        self,
        db: Session,
        *,
        application: Application,
        status: str,
        applied_at: datetime | None,
    ) -> Application:
        application.status = status
        application.applied_at = applied_at

        db.flush()

        return application
