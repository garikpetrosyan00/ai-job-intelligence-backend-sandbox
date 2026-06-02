from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.integrations.job_sources.base import ExternalJobDTO
from app.models.company import Company
from app.models.job import Job
from app.models.job_source import JobSource
from app.services.job_import import JobImportService


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


def count_rows(db: Session, model: type[Job] | type[Company]) -> int:
    statement = select(func.count()).select_from(model)

    return db.scalar(statement) or 0


def test_import_jobs_creates_job_and_second_import_skips_duplicate(
    db: Session,
) -> None:
    source = create_source(db)
    service = JobImportService()

    jobs = [
        ExternalJobDTO(
            external_id=" 1132651 ",
            title="  Python   Backend Developer ",
            company_name=" Example LLC ",
            location=" Remote, ",
            description="  Backend role  ",
            apply_url=" HTTPS://Example.com/jobs/1132651/#apply ",
            raw_payload={
                "id": "1132651",
                "position": "  Python   Backend Developer ",
            },
        )
    ]

    first_summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=jobs,
    )
    db.commit()

    second_summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=jobs,
    )
    db.commit()

    assert first_summary.fetched_count == 1
    assert first_summary.created_count == 1
    assert first_summary.updated_count == 0
    assert first_summary.skipped_count == 0

    assert second_summary.fetched_count == 1
    assert second_summary.created_count == 0
    assert second_summary.updated_count == 0
    assert second_summary.skipped_count == 1

    assert count_rows(db, Job) == 1
    assert count_rows(db, Company) == 1

    job = db.scalars(select(Job)).one()

    assert job.external_id == "1132651"
    assert job.title == "Python Backend Developer"
    assert job.location == "Remote"
    assert job.description == "Backend role"
    assert job.apply_url == "https://example.com/jobs/1132651"
    assert job.raw_payload == {
        "id": "1132651",
        "position": "  Python   Backend Developer ",
    }


def test_import_jobs_updates_existing_job_without_creating_duplicate(
    db: Session,
) -> None:
    source = create_source(db)
    service = JobImportService()

    first_jobs = [
        ExternalJobDTO(
            external_id="job-1",
            title="Python Developer",
            company_name="Example LLC",
            location="Remote",
            raw_payload={"position": "Python Developer"},
        )
    ]

    second_jobs = [
        ExternalJobDTO(
            external_id="job-1",
            title="Senior Python Developer",
            company_name="Example LLC",
            location="Europe,",
            raw_payload={"position": "Senior Python Developer"},
        )
    ]

    first_summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=first_jobs,
    )
    db.commit()

    second_summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=second_jobs,
    )
    db.commit()

    assert first_summary.created_count == 1

    assert second_summary.created_count == 0
    assert second_summary.updated_count == 1
    assert second_summary.skipped_count == 0

    assert count_rows(db, Job) == 1

    job = db.scalars(select(Job)).one()

    assert job.title == "Senior Python Developer"
    assert job.location == "Europe"
    assert job.raw_payload == {
        "position": "Senior Python Developer",
    }


def test_import_jobs_reuses_company_by_normalized_name(
    db: Session,
) -> None:
    source = create_source(db)
    service = JobImportService()

    jobs = [
        ExternalJobDTO(
            external_id="job-1",
            title="Python Developer",
            company_name=" OpenAI ",
        ),
        ExternalJobDTO(
            external_id="job-2",
            title="Backend Engineer",
            company_name="OPENAI",
        ),
    ]

    summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=jobs,
    )
    db.commit()

    assert summary.created_count == 2
    assert count_rows(db, Company) == 1
    assert count_rows(db, Job) == 2

    company = db.scalars(select(Company)).one()
    imported_jobs = list(db.scalars(select(Job).order_by(Job.id.asc())).all())

    assert company.name == "OpenAI"
    assert company.normalized_name == "openai"
    assert imported_jobs[0].company_id == company.id
    assert imported_jobs[1].company_id == company.id


def test_import_jobs_skips_invalid_normalized_job(
    db: Session,
) -> None:
    source = create_source(db)
    service = JobImportService()

    jobs = [
        ExternalJobDTO(
            external_id="job-1",
            title="   ",
            company_name="Example LLC",
        )
    ]

    summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=jobs,
    )
    db.commit()

    assert summary.fetched_count == 1
    assert summary.created_count == 0
    assert summary.updated_count == 0
    assert summary.skipped_count == 1

    assert count_rows(db, Job) == 0
    assert count_rows(db, Company) == 0


def test_import_jobs_deduplicates_repeated_job_inside_same_batch(
    db: Session,
) -> None:
    source = create_source(db)
    service = JobImportService()

    jobs = [
        ExternalJobDTO(
            external_id="job-1",
            title="Python Developer",
            company_name="Example LLC",
        ),
        ExternalJobDTO(
            external_id="job-1",
            title="Python Developer",
            company_name="Example LLC",
        ),
    ]

    summary = service.import_jobs(
        db=db,
        source_id=source.id,
        jobs=jobs,
    )
    db.commit()

    assert summary.fetched_count == 2
    assert summary.created_count == 1
    assert summary.updated_count == 0
    assert summary.skipped_count == 1

    assert count_rows(db, Job) == 1
    assert count_rows(db, Company) == 1


def test_import_jobs_allows_same_external_id_for_different_sources(
    db: Session,
) -> None:
    first_source = create_source(db)

    second_source = JobSource(
        name="Another Source",
        base_url="https://example.com",
        is_active=True,
    )

    db.add(second_source)
    db.flush()

    service = JobImportService()

    jobs = [
        ExternalJobDTO(
            external_id="shared-id",
            title="Python Developer",
        )
    ]

    first_summary = service.import_jobs(
        db=db,
        source_id=first_source.id,
        jobs=jobs,
    )

    second_summary = service.import_jobs(
        db=db,
        source_id=second_source.id,
        jobs=jobs,
    )

    db.commit()

    assert first_summary.created_count == 1
    assert second_summary.created_count == 1

    assert count_rows(db, Job) == 2
