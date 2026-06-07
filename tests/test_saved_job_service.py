from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.services.saved_job import SavedJobService


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


class FakeSavedJobRepository:
    def __init__(
        self,
        *,
        existing_results=None,
        create_error: Exception | None = None,
    ) -> None:
        self.existing_results = list(existing_results or [])
        self.create_error = create_error

        self.get_calls = []
        self.create_calls = []
        self.list_calls = []

    def get_by_user_and_job(
        self,
        db,
        *,
        user_id: int,
        job_id: int,
    ):
        self.get_calls.append(
            {
                "user_id": user_id,
                "job_id": job_id,
            }
        )

        if self.existing_results:
            return self.existing_results.pop(0)

        return None

    def create(
        self,
        db,
        *,
        user_id: int,
        job_id: int,
    ):
        self.create_calls.append(
            {
                "user_id": user_id,
                "job_id": job_id,
            }
        )

        if self.create_error is not None:
            raise self.create_error

        return SimpleNamespace(
            id=1,
            user_id=user_id,
            job_id=job_id,
        )

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
            )
        ]


def test_save_job_creates_saved_job_when_missing() -> None:
    db = FakeDb()
    repository = FakeSavedJobRepository()
    job_repository = FakeJobRepository()

    service = SavedJobService(
        repository=repository,
        job_repository=job_repository,
    )

    saved_job = service.save_job(
        db=db,
        user_id=7,
        job_id=12,
    )

    assert saved_job.user_id == 7
    assert saved_job.job_id == 12

    assert repository.create_calls == [
        {
            "user_id": 7,
            "job_id": 12,
        }
    ]

    assert db.commit_calls == 1
    assert db.rollback_calls == 0
    assert db.refreshed_objects == [saved_job]


def test_save_job_returns_existing_record_without_duplicate() -> None:
    db = FakeDb()

    existing_saved_job = SimpleNamespace(
        id=5,
        user_id=7,
        job_id=12,
    )

    repository = FakeSavedJobRepository(
        existing_results=[existing_saved_job],
    )

    service = SavedJobService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    saved_job = service.save_job(
        db=db,
        user_id=7,
        job_id=12,
    )

    assert saved_job is existing_saved_job
    assert repository.create_calls == []
    assert db.commit_calls == 0
    assert db.rollback_calls == 0


def test_save_unknown_job_returns_404() -> None:
    service = SavedJobService(
        repository=FakeSavedJobRepository(),
        job_repository=FakeJobRepository(
            job_exists=False,
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.save_job(
            db=FakeDb(),
            user_id=7,
            job_id=999999,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Job not found"


def test_save_job_recovers_from_unique_constraint_race() -> None:
    db = FakeDb()

    saved_by_competing_request = SimpleNamespace(
        id=8,
        user_id=7,
        job_id=12,
    )

    repository = FakeSavedJobRepository(
        existing_results=[
            None,
            saved_by_competing_request,
        ],
        create_error=IntegrityError(
            "INSERT INTO saved_jobs",
            {},
            Exception("duplicate key"),
        ),
    )

    service = SavedJobService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    saved_job = service.save_job(
        db=db,
        user_id=7,
        job_id=12,
    )

    assert saved_job is saved_by_competing_request
    assert len(repository.create_calls) == 1
    assert db.commit_calls == 0
    assert db.rollback_calls == 1


def test_save_job_reraises_unexpected_integrity_error() -> None:
    db = FakeDb()

    repository = FakeSavedJobRepository(
        existing_results=[
            None,
            None,
        ],
        create_error=IntegrityError(
            "INSERT INTO saved_jobs",
            {},
            Exception("unexpected constraint error"),
        ),
    )

    service = SavedJobService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    with pytest.raises(IntegrityError):
        service.save_job(
            db=db,
            user_id=7,
            job_id=12,
        )

    assert db.rollback_calls == 1


def test_list_saved_jobs_uses_user_id_filter() -> None:
    repository = FakeSavedJobRepository()

    service = SavedJobService(
        repository=repository,
        job_repository=FakeJobRepository(),
    )

    saved_jobs = service.list_saved_jobs(
        db=FakeDb(),
        user_id=9,
    )

    assert len(saved_jobs) == 1
    assert saved_jobs[0].user_id == 9
    assert repository.list_calls == [
        {
            "user_id": 9,
        }
    ]
