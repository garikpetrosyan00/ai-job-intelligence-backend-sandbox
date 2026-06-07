from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.application import ApplicationStatus
from app.services.application import ApplicationService


class FakeDb:
    def __init__(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.refreshed_objects = []

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def refresh(self, obj) -> None:
        self.refreshed_objects.append(obj)


class FakeJobRepository:
    def __init__(self, *, job_exists: bool = True) -> None:
        self.job_exists = job_exists
        self.requested_job_ids = []

    def get_job_by_id(self, db, job_id: int):
        self.requested_job_ids.append(job_id)

        if not self.job_exists:
            return None

        return SimpleNamespace(id=job_id)


class FakeApplicationRepository:
    def __init__(
        self,
        *,
        existing_application=None,
        existing_results=None,
        owned_application=None,
        create_error: Exception | None = None,
    ) -> None:
        self.existing_application = existing_application
        self.existing_results = (
            list(existing_results)
            if existing_results is not None
            else None
        )
        self.owned_application = owned_application
        self.create_error = create_error

        self.get_by_user_and_job_calls = []
        self.get_by_id_for_user_calls = []
        self.create_calls = []
        self.list_calls = []
        self.update_calls = []

    def get_by_user_and_job(
        self,
        db,
        *,
        user_id: int,
        job_id: int,
    ):
        self.get_by_user_and_job_calls.append(
            {
                "user_id": user_id,
                "job_id": job_id,
            }
        )

        if self.existing_results is not None:
            return self.existing_results.pop(0)

        return self.existing_application

    def get_by_id_for_user(
        self,
        db,
        *,
        application_id: int,
        user_id: int,
    ):
        self.get_by_id_for_user_calls.append(
            {
                "application_id": application_id,
                "user_id": user_id,
            }
        )

        return self.owned_application

    def list_for_user(
        self,
        db,
        *,
        user_id: int,
    ):
        self.list_calls.append(
            {
                "user_id": user_id,
            }
        )

        return [
            SimpleNamespace(
                id=1,
                user_id=user_id,
                job_id=12,
                status="planned",
            )
        ]

    def create(
        self,
        db,
        *,
        user_id: int,
        job_id: int,
        status: str,
        notes: str | None,
        applied_at: datetime | None,
    ):
        self.create_calls.append(
            {
                "user_id": user_id,
                "job_id": job_id,
                "status": status,
                "notes": notes,
                "applied_at": applied_at,
            }
        )

        if self.create_error is not None:
            raise self.create_error

        return SimpleNamespace(
            id=1,
            user_id=user_id,
            job_id=job_id,
            status=status,
            notes=notes,
            applied_at=applied_at,
        )

    def update_status(
        self,
        db,
        *,
        application,
        status: str,
        applied_at: datetime | None,
    ):
        self.update_calls.append(
            {
                "application": application,
                "status": status,
                "applied_at": applied_at,
            }
        )

        application.status = status
        application.applied_at = applied_at

        return application


def make_application(
    *,
    application_id: int = 25,
    user_id: int = 7,
    job_id: int = 12,
    status: str = "planned",
    applied_at: datetime | None = None,
):
    return SimpleNamespace(
        id=application_id,
        user_id=user_id,
        job_id=job_id,
        status=status,
        notes=None,
        applied_at=applied_at,
    )


def test_create_planned_application() -> None:
    db = FakeDb()
    repository = FakeApplicationRepository()

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    application = service.create_application(
        db=db,
        user_id=7,
        job_id=12,
        application_status=ApplicationStatus.PLANNED,
        notes="Update CV first",
    )

    assert application.user_id == 7
    assert application.job_id == 12
    assert application.status == "planned"
    assert application.notes == "Update CV first"
    assert application.applied_at is None

    assert repository.create_calls == [
        {
            "user_id": 7,
            "job_id": 12,
            "status": "planned",
            "notes": "Update CV first",
            "applied_at": None,
        }
    ]

    assert db.commit_calls == 1
    assert db.rollback_calls == 0
    assert db.refreshed_objects == [application]


def test_create_applied_application_sets_applied_at() -> None:
    db = FakeDb()
    repository = FakeApplicationRepository()

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    application = service.create_application(
        db=db,
        user_id=7,
        job_id=12,
        application_status=ApplicationStatus.APPLIED,
        notes=None,
    )

    assert application.status == "applied"
    assert application.applied_at is not None
    assert application.applied_at.tzinfo is not None


def test_create_application_for_unknown_job_returns_404() -> None:
    service = ApplicationService(
        repository=FakeApplicationRepository(),
        job_repository=FakeJobRepository(
            job_exists=False,
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_application(
            db=FakeDb(),
            user_id=7,
            job_id=999999,
            application_status=ApplicationStatus.PLANNED,
            notes=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Job not found"


def test_create_duplicate_application_returns_409() -> None:
    db = FakeDb()

    repository = FakeApplicationRepository(
        existing_application=make_application(),
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_application(
            db=db,
            user_id=7,
            job_id=12,
            application_status=ApplicationStatus.PLANNED,
            notes=None,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Application already exists"

    assert repository.create_calls == []
    assert db.commit_calls == 0
    assert db.rollback_calls == 0


def test_create_application_maps_integrity_error_to_409() -> None:
    db = FakeDb()

    repository = FakeApplicationRepository(
        existing_results=[
            None,
            make_application(),
        ],
        create_error=IntegrityError(
            "INSERT INTO applications",
            {},
            Exception("duplicate key"),
        ),
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_application(
            db=db,
            user_id=7,
            job_id=12,
            application_status=ApplicationStatus.PLANNED,
            notes=None,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Application already exists"

    assert db.commit_calls == 0
    assert db.rollback_calls == 1


def test_create_application_reraises_unexpected_integrity_error() -> None:
    db = FakeDb()

    repository = FakeApplicationRepository(
        existing_results=[
            None,
            None,
        ],
        create_error=IntegrityError(
            "INSERT INTO applications",
            {},
            Exception("unexpected constraint error"),
        ),
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    with pytest.raises(IntegrityError):
        service.create_application(
            db=db,
            user_id=7,
            job_id=12,
            application_status=ApplicationStatus.PLANNED,
            notes=None,
        )

    assert db.commit_calls == 0
    assert db.rollback_calls == 1


def test_list_applications_uses_user_id_filter() -> None:
    repository = FakeApplicationRepository()

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    applications = service.list_applications(
        db=FakeDb(),
        user_id=9,
    )

    assert len(applications) == 1
    assert applications[0].user_id == 9
    assert repository.list_calls == [
        {
            "user_id": 9,
        }
    ]


def test_update_application_returns_404_when_not_owned_by_user() -> None:
    repository = FakeApplicationRepository(
        owned_application=None,
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.update_application_status(
            db=FakeDb(),
            application_id=25,
            user_id=9,
            new_status=ApplicationStatus.INTERVIEW,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Application not found"

    assert repository.get_by_id_for_user_calls == [
        {
            "application_id": 25,
            "user_id": 9,
        }
    ]

    assert repository.update_calls == []


def test_update_planned_application_to_applied() -> None:
    db = FakeDb()

    application = make_application(
        status="planned",
        applied_at=None,
    )

    repository = FakeApplicationRepository(
        owned_application=application,
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    updated_application = service.update_application_status(
        db=db,
        application_id=25,
        user_id=7,
        new_status=ApplicationStatus.APPLIED,
    )

    assert updated_application.status == "applied"
    assert updated_application.applied_at is not None
    assert updated_application.applied_at.tzinfo is not None

    assert repository.update_calls[0]["status"] == "applied"
    assert db.commit_calls == 1
    assert db.refreshed_objects == [application]


def test_update_applied_application_to_interview_preserves_applied_at() -> None:
    db = FakeDb()

    original_applied_at = datetime(
        2026,
        6,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    application = make_application(
        status="applied",
        applied_at=original_applied_at,
    )

    repository = FakeApplicationRepository(
        owned_application=application,
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    updated_application = service.update_application_status(
        db=db,
        application_id=25,
        user_id=7,
        new_status=ApplicationStatus.INTERVIEW,
    )

    assert updated_application.status == "interview"
    assert updated_application.applied_at == original_applied_at

    assert repository.update_calls[0]["applied_at"] == original_applied_at
    assert db.commit_calls == 1


def test_update_application_rejects_invalid_transition() -> None:
    db = FakeDb()

    application = make_application(
        status="planned",
    )

    repository = FakeApplicationRepository(
        owned_application=application,
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.update_application_status(
            db=db,
            application_id=25,
            user_id=7,
            new_status=ApplicationStatus.OFFER,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Invalid application status transition"

    assert application.status == "planned"
    assert repository.update_calls == []
    assert db.commit_calls == 0


def test_update_application_to_same_status_is_no_op() -> None:
    db = FakeDb()

    application = make_application(
        status="applied",
    )

    repository = FakeApplicationRepository(
        owned_application=application,
    )

    service = ApplicationService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    updated_application = service.update_application_status(
        db=db,
        application_id=25,
        user_id=7,
        new_status=ApplicationStatus.APPLIED,
    )

    assert updated_application is application
    assert repository.update_calls == []
    assert db.commit_calls == 0
    assert db.refreshed_objects == []
