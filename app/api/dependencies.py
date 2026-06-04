from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
user_repository = UserRepository()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        subject = decode_access_token(token)
        user_id = int(subject)
    except (InvalidTokenError, ValueError) as exc:
        raise credentials_error from exc

    user = user_repository.get_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None or not user.is_active:
        raise credentials_error

    return user
