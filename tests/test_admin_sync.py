from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.integrations.job_sources.base import (
    ExternalJobDTO,
    JobSourceTimeoutError,
)
from app.models.company import Company
from app.models.job import Job
from app.models.job_source import JobSource
from app.models.sync_run import SyncRun
from app.services.admin_sync import (
    AdminSyncService,
    JobSourceNotFoundError,
    JobSourceSyncError,
)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


def create_source(db: Session) -> JobSource:
    source = JobSource(
        name="Remote OK",
        base_url="https://remoteok.com",
        is_active=True,
    )

    db.add(source)
    db.flush()

    return source


def count_rows(db: Session, model) -> int:
    statement = select(func.count()).select_from(model)

    return db.scalar(statement) or 0


class FakeSuccessfulAdapter:
    def fetch_jobs(self, limit: int) -> list[ExternalJobDTO]:
        return [
            ExternalJobDTO(
                external_id="remoteok-1",
                title=" Python Backend Developer ",
                company_name=" Example LLC ",
                location=" Remote, ",
                raw_payload={
                    "id": "remoteok-1",
                    "position": " Python Backend Developer ",
                },
            )
        ][:limit]


class FakeFailingAdapter:
    def fetch_jobs(self, limit: int) -> list[ExternalJobDTO]:
        raise JobSourceTimeoutError(
            "Remote OK API request timed out"
        )


class UnexpectedFailingJobSyncService:
    def sync_jobs(
        self,
        db: Session,
        *,
        source_id: int,
        adapter,
        limit: int,
    ):
        db.add(
            Company(
                name="Temporary LLC",
                normalized_name="temporary llc",
            )
        )
        db.flush()

        raise RuntimeError("internal implementation detail")


def test_sync_source_persists_successful_run_and_imported_job(
    db: Session,
) -> None:
    source = create_source(db)
    service = AdminSyncService()

    sync_run = service.sync_source(
        db=db,
        source_id=source.id,
        adapter=FakeSuccessfulAdapter(),
        limit=5,
    )

    assert sync_run.status == "succeeded"
    assert sync_run.finished_at is not None
    assert sync_run.jobs_fetched == 1
    assert sync_run.jobs_created == 1
    assert sync_run.jobs_updated == 0
    assert sync_run.error_message is None

    assert count_rows(db, SyncRun) == 1
    assert count_rows(db, Job) == 1

    job = db.scalars(select(Job)).one()

    assert job.external_id == "remoteok-1"
    assert job.title == "Python Backend Developer"
    assert job.location == "Remote"


def test_sync_source_persists_safe_adapter_failure(
    db: Session,
) -> None:
    source = create_source(db)
    service = AdminSyncService()

    with pytest.raises(JobSourceSyncError):
        service.sync_source(
            db=db,
            source_id=source.id,
            adapter=FakeFailingAdapter(),
            limit=5,
        )

    sync_run = db.scalars(select(SyncRun)).one()

    assert sync_run.status == "failed"
    assert sync_run.finished_at is not None
    assert sync_run.jobs_fetched == 0
    assert sync_run.jobs_created == 0
    assert sync_run.jobs_updated == 0
    assert sync_run.error_message == "Remote OK API request timed out"

    assert count_rows(db, Job) == 0


def test_sync_source_rolls_back_import_changes_and_hides_unexpected_error(
    db: Session,
) -> None:
    source = create_source(db)

    service = AdminSyncService(
        job_sync_service=UnexpectedFailingJobSyncService(),
    )

    with pytest.raises(JobSourceSyncError):
        service.sync_source(
            db=db,
            source_id=source.id,
            adapter=FakeSuccessfulAdapter(),
            limit=5,
        )

    sync_run = db.scalars(select(SyncRun)).one()

    assert sync_run.status == "failed"
    assert sync_run.finished_at is not None
    assert sync_run.error_message == "Unexpected error while syncing job source"

    assert count_rows(db, Company) == 0
    assert count_rows(db, Job) == 0


def test_sync_source_unknown_source_does_not_create_run(
    db: Session,
) -> None:
    service = AdminSyncService()

    with pytest.raises(JobSourceNotFoundError):
        service.sync_source(
            db=db,
            source_id=999999,
            adapter=FakeSuccessfulAdapter(),
            limit=5,
        )

    assert count_rows(db, SyncRun) == 0
