from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository


class UserAlreadyExistsError(Exception):
    """Raised when registration uses an existing email."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


class AuthService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    def register(
        self,
        db: Session,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        normalized_email = self._normalize_email(email)

        existing_user = self.repository.get_by_email(
            db=db,
            email=normalized_email,
        )

        if existing_user is not None:
            raise UserAlreadyExistsError(
                "A user with this email already exists"
            )

        try:
            user = self.repository.create(
                db=db,
                email=normalized_email,
                hashed_password=hash_password(password),
                full_name=self._normalize_full_name(full_name),
            )

            db.commit()

        except IntegrityError as exc:
            db.rollback()

            raise UserAlreadyExistsError(
                "A user with this email already exists"
            ) from exc

        db.refresh(user)

        return user

    def authenticate(
        self,
        db: Session,
        *,
        email: str,
        password: str,
    ) -> User:
        normalized_email = self._normalize_email(email)

        user = self.repository.get_by_email(
            db=db,
            email=normalized_email,
        )

        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.hashed_password)
        ):
            raise InvalidCredentialsError(
                "Invalid email or password"
            )

        return user

    def create_token_for_user(self, user: User) -> str:
        return create_access_token(subject=user.id)

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _normalize_full_name(full_name: str | None) -> str | None:
        if full_name is None:
            return None

        normalized_name = full_name.strip()

        return normalized_name or None
