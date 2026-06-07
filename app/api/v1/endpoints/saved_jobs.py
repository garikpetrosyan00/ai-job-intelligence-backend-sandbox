from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.saved_job import SavedJobRead
from app.services.saved_job import SavedJobService


router = APIRouter(tags=["saved-jobs"])
saved_job_service = SavedJobService()


@router.post(
    "/jobs/{job_id}/save",
    response_model=SavedJobRead,
    status_code=status.HTTP_201_CREATED,
)
def save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return saved_job_service.save_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id,
    )


@router.get(
    "/me/saved-jobs",
    response_model=list[SavedJobRead],
)
def list_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return saved_job_service.list_saved_jobs(
        db=db,
        user_id=current_user.id,
    )
