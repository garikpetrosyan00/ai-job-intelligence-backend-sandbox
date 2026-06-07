from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.repositories.application import ApplicationRepository
from app.repositories.job import JobRepository
from app.schemas.application import ApplicationStatus


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    ApplicationStatus.PLANNED.value: {
        ApplicationStatus.APPLIED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.APPLIED.value: {
        ApplicationStatus.INTERVIEW.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.INTERVIEW.value: {
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.OFFER.value: set(),
    ApplicationStatus.REJECTED.value: set(),
    ApplicationStatus.WITHDRAWN.value: set(),
}


class ApplicationService:
    def __init__(
        self,
        repository: ApplicationRepository | None = None,
        job_repository: JobRepository | None = None,
    ) -> None:
        self.repository = repository or ApplicationRepository()
        self.job_repository = job_repository or JobRepository()

    def create_application(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
        application_status: ApplicationStatus,
        notes: str | None,
    ) -> Application:
        job = self.job_repository.get_job_by_id(
            db=db,
            job_id=job_id,
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        existing_application = self.repository.get_by_user_and_job(
            db=db,
            user_id=user_id,
            job_id=job_id,
        )

        if existing_application is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists",
            )

        application_status_value = application_status.value

        applied_at = None
        if application_status_value == ApplicationStatus.APPLIED.value:
            applied_at = datetime.now(timezone.utc)

        try:
            application = self.repository.create(
                db=db,
                user_id=user_id,
                job_id=job_id,
                status=application_status_value,
                notes=notes,
                applied_at=applied_at,
            )

            db.commit()
            db.refresh(application)

            return application
        except IntegrityError as exc:
            db.rollback()

            existing_application = self.repository.get_by_user_and_job(
                db=db,
                user_id=user_id,
                job_id=job_id,
            )

            if existing_application is None:
                raise

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists",
            ) from exc

    def list_applications(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> list[Application]:
        return self.repository.list_for_user(
            db=db,
            user_id=user_id,
        )

    def update_application_status(
        self,
        db: Session,
        *,
        application_id: int,
        user_id: int,
        new_status: ApplicationStatus,
    ) -> Application:
        application = self.repository.get_by_id_for_user(
            db=db,
            application_id=application_id,
            user_id=user_id,
        )

        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        new_status_value = new_status.value

        if application.status == new_status_value:
            return application

        allowed_statuses = ALLOWED_TRANSITIONS.get(
            application.status,
            set(),
        )

        if new_status_value not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid application status transition",
            )

        applied_at = application.applied_at

        if (
            new_status_value == ApplicationStatus.APPLIED.value
            and applied_at is None
        ):
            applied_at = datetime.now(timezone.utc)

        application = self.repository.update_status(
            db=db,
            application=application,
            status=new_status_value,
            applied_at=applied_at,
        )

        db.commit()
        db.refresh(application)

        return application
