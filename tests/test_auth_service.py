from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.auth import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)


class FakeDb:
    def __init__(self) -> None:
        self.commit_called = False
        self.rollback_called = False
        self.refresh_called = False

    def commit(self) -> None:
        self.commit_called = True

    def rollback(self) -> None:
        self.rollback_called = True

    def refresh(self, user) -> None:
        self.refresh_called = True


class FakeUserRepository:
    def __init__(self) -> None:
        self.user = None

    def get_by_email(self, db, email: str):
        if self.user is not None and self.user.email == email:
            return self.user

        return None

    def create(
        self,
        db,
        *,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ):
        self.user = SimpleNamespace(
            id=1,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
        )

        return self.user


class IntegrityErrorRepository(FakeUserRepository):
    def create(
        self,
        db,
        *,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ):
        raise IntegrityError(
            "INSERT INTO users ...",
            {},
            Exception("duplicate key"),
        )


def test_register_normalizes_email_and_full_name() -> None:
    db = FakeDb()
    service = AuthService(repository=FakeUserRepository())

    user = service.register(
        db=db,
        email="  GARIK@EXAMPLE.COM  ",
        password="StrongPassword123",
        full_name="  Garik Petrosyan  ",
    )

    assert user.email == "garik@example.com"
    assert user.full_name == "Garik Petrosyan"
    assert user.hashed_password != "StrongPassword123"
    assert db.commit_called is True
    assert db.refresh_called is True


def test_register_rejects_existing_email() -> None:
    db = FakeDb()
    repository = FakeUserRepository()
    repository.user = SimpleNamespace(
        id=1,
        email="garik@example.com",
        hashed_password="example",
        full_name=None,
        is_active=True,
    )

    service = AuthService(repository=repository)

    with pytest.raises(UserAlreadyExistsError):
        service.register(
            db=db,
            email="GARIK@example.com",
            password="StrongPassword123",
        )


def test_register_rolls_back_on_integrity_error() -> None:
    db = FakeDb()
    service = AuthService(repository=IntegrityErrorRepository())

    with pytest.raises(UserAlreadyExistsError):
        service.register(
            db=db,
            email="garik@example.com",
            password="StrongPassword123",
        )

    assert db.rollback_called is True


def test_authenticate_returns_user_for_valid_credentials() -> None:
    db = FakeDb()
    repository = FakeUserRepository()
    service = AuthService(repository=repository)

    registered_user = service.register(
        db=db,
        email="garik@example.com",
        password="StrongPassword123",
    )

    authenticated_user = service.authenticate(
        db=db,
        email=" GARIK@example.com ",
        password="StrongPassword123",
    )

    assert authenticated_user.id == registered_user.id


def test_authenticate_rejects_wrong_password() -> None:
    db = FakeDb()
    repository = FakeUserRepository()
    service = AuthService(repository=repository)

    service.register(
        db=db,
        email="garik@example.com",
        password="StrongPassword123",
    )

    with pytest.raises(InvalidCredentialsError):
        service.authenticate(
            db=db,
            email="garik@example.com",
            password="WrongPassword123",
        )


def test_authenticate_rejects_inactive_user() -> None:
    db = FakeDb()
    repository = FakeUserRepository()
    service = AuthService(repository=repository)

    user = service.register(
        db=db,
        email="garik@example.com",
        password="StrongPassword123",
    )

    user.is_active = False

    with pytest.raises(InvalidCredentialsError):
        service.authenticate(
            db=db,
            email="garik@example.com",
            password="StrongPassword123",
        )
