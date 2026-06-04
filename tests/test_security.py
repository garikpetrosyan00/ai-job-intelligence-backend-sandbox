from datetime import timedelta

import jwt
import pytest
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_creates_argon2_hash() -> None:
    hashed_password = hash_password("StrongPassword123")

    assert hashed_password.startswith("$argon2")
    assert hashed_password != "StrongPassword123"


def test_verify_password_accepts_correct_password() -> None:
    hashed_password = hash_password("StrongPassword123")

    assert verify_password(
        "StrongPassword123",
        hashed_password,
    ) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed_password = hash_password("StrongPassword123")

    assert verify_password(
        "WrongPassword123",
        hashed_password,
    ) is False


def test_decode_access_token_returns_subject() -> None:
    token = create_access_token(subject=7)

    assert decode_access_token(token) == "7"


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        subject=7,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ExpiredSignatureError):
        decode_access_token(token)


def test_decode_access_token_rejects_missing_subject() -> None:
    token = jwt.encode(
        {"example": "value"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
