from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sync_run import SyncRun


class SyncRunRepository:
    def get_by_id(
        self,
        db: Session,
        sync_run_id: int,
    ) -> SyncRun | None:
        statement = select(SyncRun).where(SyncRun.id == sync_run_id)

        return db.scalars(statement).first()

    def create_running(
        self,
        db: Session,
        *,
        source_id: int,
    ) -> SyncRun:
        sync_run = SyncRun(
            source_id=source_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        db.add(sync_run)
        db.flush()

        return sync_run

    def mark_succeeded(
        self,
        db: Session,
        *,
        sync_run: SyncRun,
        jobs_fetched: int,
        jobs_created: int,
        jobs_updated: int,
    ) -> SyncRun:
        sync_run.status = "succeeded"
        sync_run.finished_at = datetime.now(timezone.utc)
        sync_run.jobs_fetched = jobs_fetched
        sync_run.jobs_created = jobs_created
        sync_run.jobs_updated = jobs_updated
        sync_run.error_message = None

        db.flush()

        return sync_run

    def mark_failed(
        self,
        db: Session,
        *,
        sync_run: SyncRun,
        error_message: str,
    ) -> SyncRun:
        sync_run.status = "failed"
        sync_run.finished_at = datetime.now(timezone.utc)
        sync_run.error_message = error_message

        db.flush()

        return sync_run

    def list_runs(
        self,
        db: Session,
        *,
        limit: int,
        offset: int,
    ) -> list[SyncRun]:
        statement = (
            select(SyncRun)
            .order_by(SyncRun.started_at.desc(), SyncRun.id.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(db.scalars(statement).all())
