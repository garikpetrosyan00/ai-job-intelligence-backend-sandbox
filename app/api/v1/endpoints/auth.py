from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import TokenRead, UserRegister
from app.schemas.user import UserRead
from app.services.auth import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)


router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        return auth_service.register(
            db=db,
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
        )

    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from exc


@router.post("/login", response_model=TokenRead)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        user = auth_service.authenticate(
            db=db,
            email=form_data.username,
            password=form_data.password,
        )

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenRead(
        access_token=auth_service.create_token_for_user(user),
    )
