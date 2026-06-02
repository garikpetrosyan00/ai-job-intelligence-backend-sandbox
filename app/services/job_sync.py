from sqlalchemy.orm import Session

from app.integrations.job_sources.base import JobSourceAdapter
from app.services.job_import import JobImportService, JobImportSummary


class JobSyncService:
    def __init__(
        self,
        *,
        import_service: JobImportService | None = None,
    ) -> None:
        self.import_service = import_service or JobImportService()

    def sync_jobs(
        self,
        db: Session,
        *,
        source_id: int,
        adapter: JobSourceAdapter,
        limit: int,
    ) -> JobImportSummary:
        jobs = adapter.fetch_jobs(limit=limit)

        return self.import_service.import_jobs(
            db=db,
            source_id=source_id,
            jobs=jobs,
        )
