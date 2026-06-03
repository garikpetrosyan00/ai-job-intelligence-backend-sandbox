from sqlalchemy.orm import Session

from app.integrations.job_sources.base import (
    JobSourceAdapter,
    JobSourceError,
)
from app.integrations.job_sources.registry import JobSourceAdapterRegistry
from app.models.job_source import JobSource
from app.models.sync_run import SyncRun
from app.repositories.job_source import JobSourceRepository
from app.repositories.sync_run import SyncRunRepository
from app.services.job_sync import JobSyncService


class JobSourceNotFoundError(Exception):
    """Raised when the requested job source does not exist."""


class JobSourceSyncError(Exception):
    """Raised when a job source sync attempt fails."""


class AdminSyncService:
    def __init__(
        self,
        *,
        source_repository: JobSourceRepository | None = None,
        sync_run_repository: SyncRunRepository | None = None,
        job_sync_service: JobSyncService | None = None,
        adapter_registry: JobSourceAdapterRegistry | None = None,
    ) -> None:
        self.source_repository = source_repository or JobSourceRepository()
        self.sync_run_repository = sync_run_repository or SyncRunRepository()
        self.job_sync_service = job_sync_service or JobSyncService()
        self.adapter_registry = adapter_registry or JobSourceAdapterRegistry()

    def sync_source(
        self,
        db: Session,
        *,
        source_id: int,
        limit: int,
        adapter: JobSourceAdapter | None = None,
    ) -> SyncRun:
        source = self.source_repository.get_by_id(
            db=db,
            source_id=source_id,
        )

        if source is None:
            raise JobSourceNotFoundError(
                f"Job source {source_id} was not found"
            )

        sync_run = self.sync_run_repository.create_running(
            db=db,
            source_id=source.id,
        )

        db.commit()
        db.refresh(sync_run)

        sync_run_id = sync_run.id

        try:
            summary = self._sync_jobs(
                db=db,
                source=source,
                adapter=adapter,
                limit=limit,
            )

            self.sync_run_repository.mark_succeeded(
                db=db,
                sync_run=sync_run,
                jobs_fetched=summary.fetched_count,
                jobs_created=summary.created_count,
                jobs_updated=summary.updated_count,
            )

            db.commit()
            db.refresh(sync_run)

            return sync_run

        except Exception as exc:
            db.rollback()

            failed_sync_run = self.sync_run_repository.get_by_id(
                db=db,
                sync_run_id=sync_run_id,
            )

            if failed_sync_run is not None:
                self.sync_run_repository.mark_failed(
                    db=db,
                    sync_run=failed_sync_run,
                    error_message=self._safe_error_message(exc),
                )

                db.commit()

            raise JobSourceSyncError(
                "Job source sync failed"
            ) from exc

    def list_runs(
        self,
        db: Session,
        *,
        limit: int,
        offset: int,
    ) -> list[SyncRun]:
        return self.sync_run_repository.list_runs(
            db=db,
            limit=limit,
            offset=offset,
        )

    def _sync_jobs(
        self,
        db: Session,
        *,
        source: JobSource,
        adapter: JobSourceAdapter | None,
        limit: int,
    ):
        if adapter is not None:
            return self.job_sync_service.sync_jobs(
                db=db,
                source_id=source.id,
                adapter=adapter,
                limit=limit,
            )

        with self.adapter_registry.open_adapter(source) as resolved_adapter:
            return self.job_sync_service.sync_jobs(
                db=db,
                source_id=source.id,
                adapter=resolved_adapter,
                limit=limit,
            )

    @staticmethod
    def _safe_error_message(exc: Exception) -> str:
        if isinstance(exc, JobSourceError):
            return str(exc)[:1000]

        return "Unexpected error while syncing job source"
