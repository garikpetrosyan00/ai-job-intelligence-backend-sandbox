from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.integrations.job_sources.base import ExternalJobDTO
from app.models.job import Job
from app.repositories.company import CompanyRepository
from app.repositories.job import JobRepository
from app.services.job_normalization import (
    NormalizedExternalJobDTO,
    normalize_external_job,
)


@dataclass(frozen=True)
class JobImportSummary:
    fetched_count: int
    created_count: int
    updated_count: int
    skipped_count: int


class JobImportService:
    def __init__(
        self,
        *,
        job_repository: JobRepository | None = None,
        company_repository: CompanyRepository | None = None,
    ) -> None:
        self.job_repository = job_repository or JobRepository()
        self.company_repository = company_repository or CompanyRepository()

    def import_jobs(
        self,
        db: Session,
        *,
        source_id: int,
        jobs: list[ExternalJobDTO],
    ) -> JobImportSummary:
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for external_job in jobs:
            try:
                normalized_job = normalize_external_job(external_job)

            except ValueError:
                skipped_count += 1
                continue

            company_id = self._get_or_create_company_id(
                db=db,
                job=normalized_job,
            )

            existing_job = self.job_repository.get_by_source_and_external_id(
                db=db,
                source_id=source_id,
                external_id=normalized_job.external_id,
            )

            if existing_job is None:
                self.job_repository.create(
                    db=db,
                    source_id=source_id,
                    company_id=company_id,
                    external_id=normalized_job.external_id,
                    title=normalized_job.title,
                    description=normalized_job.description,
                    location=normalized_job.location,
                    apply_url=normalized_job.apply_url,
                    published_at=normalized_job.published_at,
                    raw_payload=normalized_job.raw_payload,
                )

                created_count += 1
                continue

            if self._has_external_changes(
                job=existing_job,
                normalized_job=normalized_job,
                company_id=company_id,
            ):
                self.job_repository.update_from_external(
                    db=db,
                    job=existing_job,
                    company_id=company_id,
                    title=normalized_job.title,
                    description=normalized_job.description,
                    location=normalized_job.location,
                    apply_url=normalized_job.apply_url,
                    published_at=normalized_job.published_at,
                    raw_payload=normalized_job.raw_payload,
                )

                updated_count += 1
                continue

            skipped_count += 1

        return JobImportSummary(
            fetched_count=len(jobs),
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
        )

    def _get_or_create_company_id(
        self,
        db: Session,
        *,
        job: NormalizedExternalJobDTO,
    ) -> int | None:
        if (
            job.company_name is None
            or job.company_normalized_name is None
        ):
            return None

        company = self.company_repository.get_by_normalized_name(
            db=db,
            normalized_name=job.company_normalized_name,
        )

        if company is None:
            company = self.company_repository.create(
                db=db,
                name=job.company_name,
                normalized_name=job.company_normalized_name,
            )

        return company.id

    @staticmethod
    def _has_external_changes(
        *,
        job: Job,
        normalized_job: NormalizedExternalJobDTO,
        company_id: int | None,
    ) -> bool:
        return (
            job.company_id != company_id
            or job.title != normalized_job.title
            or job.description != normalized_job.description
            or job.location != normalized_job.location
            or job.apply_url != normalized_job.apply_url
            or job.published_at != normalized_job.published_at
            or job.raw_payload != normalized_job.raw_payload
        )
