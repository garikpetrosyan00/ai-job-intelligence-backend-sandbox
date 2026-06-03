from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sync_run import SyncRunRead
from app.services.admin_sync import (
    AdminSyncService,
    JobSourceNotFoundError,
    JobSourceSyncError,
)


router = APIRouter(prefix="/admin", tags=["admin-sync"])
admin_sync_service = AdminSyncService()


@router.post(
    "/sources/{source_id}/sync",
    response_model=SyncRunRead,
)
def sync_source(
    source_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return admin_sync_service.sync_source(
            db=db,
            source_id=source_id,
            limit=limit,
        )

    except JobSourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job source not found",
        ) from exc

    except JobSourceSyncError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Job source sync failed",
        ) from exc


@router.get("/sync-runs", response_model=list[SyncRunRead])
def list_sync_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return admin_sync_service.list_runs(
        db=db,
        limit=limit,
        offset=offset,
    )
