from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)
from app.services.application import ApplicationService


router = APIRouter(prefix="/applications", tags=["applications"])
application_service = ApplicationService()


@router.post(
    "",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_service.create_application(
        db=db,
        user_id=current_user.id,
        job_id=payload.job_id,
        application_status=payload.status,
        notes=payload.notes,
    )


@router.get(
    "",
    response_model=list[ApplicationRead],
)
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_service.list_applications(
        db=db,
        user_id=current_user.id,
    )


@router.patch(
    "/{application_id}",
    response_model=ApplicationRead,
)
def update_application_status(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_service.update_application_status(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
        new_status=payload.status,
    )
