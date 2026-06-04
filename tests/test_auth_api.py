from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.v1.endpoints import auth as auth_endpoint
from app.main import app
from app.services.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)


client = TestClient(app)


class FakeAuthService:
    def __init__(self) -> None:
        self.user = SimpleNamespace(
            id=1,
            email="garik@example.com",
            full_name="Garik Petrosyan",
            is_active=True,
        )

    def register(
        self,
        db,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ):
        if email == "existing@example.com":
            raise UserAlreadyExistsError(
                "A user with this email already exists"
            )

        return SimpleNamespace(
            id=1,
            email=email,
            full_name=full_name,
            is_active=True,
        )

    def authenticate(
        self,
        db,
        *,
        email: str,
        password: str,
    ):
        if (
            email != self.user.email
            or password != "StrongPassword123"
        ):
            raise InvalidCredentialsError(
                "Invalid email or password"
            )

        return self.user

    def create_token_for_user(self, user) -> str:
        return "header.payload.signature"


def test_register_user_returns_created_user(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_endpoint,
        "auth_service",
        FakeAuthService(),
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "StrongPassword123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "email": "new-user@example.com",
        "full_name": "New User",
        "is_active": True,
    }


def test_register_duplicate_email_returns_409(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_endpoint,
        "auth_service",
        FakeAuthService(),
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A user with this email already exists",
    }


def test_register_invalid_payload_returns_422() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_returns_access_token(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_endpoint,
        "auth_service",
        FakeAuthService(),
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "garik@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "header.payload.signature",
        "token_type": "bearer",
    }


def test_login_wrong_password_returns_401(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_endpoint,
        "auth_service",
        FakeAuthService(),
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "garik@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_users_me_returns_authenticated_user() -> None:
    current_user = SimpleNamespace(
        id=7,
        email="garik@example.com",
        full_name="Garik Petrosyan",
        is_active=True,
    )

    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.get("/users/me")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "email": "garik@example.com",
        "full_name": "Garik Petrosyan",
        "is_active": True,
    }


def test_users_me_without_token_returns_401() -> None:
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated",
    }


def test_users_me_with_invalid_token_returns_401() -> None:
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalid.token.value",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }
