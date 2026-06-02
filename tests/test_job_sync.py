from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.integrations.job_sources.base import ExternalJobDTO
from app.models.job import Job
from app.models.job_source import JobSource
from app.services.job_sync import JobSyncService


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


class FakeJobSourceAdapter:
    def __init__(self) -> None:
        self.received_limits: list[int] = []

    def fetch_jobs(self, limit: int) -> list[ExternalJobDTO]:
        self.received_limits.append(limit)

        return [
            ExternalJobDTO(
                external_id="remoteok-1",
                title="  Python   Backend Developer ",
                company_name=" Example LLC ",
                location=" Remote, ",
                apply_url=" HTTPS://Example.com/jobs/remoteok-1/#apply ",
                raw_payload={
                    "id": "remoteok-1",
                    "position": "  Python   Backend Developer ",
                },
            )
        ][:limit]


def test_sync_jobs_fetches_from_adapter_and_imports_idempotently(
    db: Session,
) -> None:
    source = JobSource(
        name="Remote OK",
        base_url="https://remoteok.com",
        is_active=True,
    )

    db.add(source)
    db.flush()

    adapter = FakeJobSourceAdapter()
    service = JobSyncService()

    first_summary = service.sync_jobs(
        db=db,
        source_id=source.id,
        adapter=adapter,
        limit=5,
    )
    db.commit()

    second_summary = service.sync_jobs(
        db=db,
        source_id=source.id,
        adapter=adapter,
        limit=5,
    )
    db.commit()

    assert adapter.received_limits == [5, 5]

    assert first_summary.fetched_count == 1
    assert first_summary.created_count == 1
    assert first_summary.updated_count == 0
    assert first_summary.skipped_count == 0

    assert second_summary.fetched_count == 1
    assert second_summary.created_count == 0
    assert second_summary.updated_count == 0
    assert second_summary.skipped_count == 1

    jobs_count = db.scalar(
        select(func.count()).select_from(Job)
    )

    assert jobs_count == 1

    job = db.scalars(select(Job)).one()

    assert job.external_id == "remoteok-1"
    assert job.title == "Python Backend Developer"
    assert job.location == "Remote"
    assert job.apply_url == "https://example.com/jobs/remoteok-1"
    assert job.company is not None
    assert job.company.name == "Example LLC"
    assert job.company.normalized_name == "example llc"
