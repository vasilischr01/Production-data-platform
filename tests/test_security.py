from datetime import timedelta

import jwt
import pytest

from src.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(
        password,
        hashed,
    )


def test_wrong_password_is_rejected():
    hashed = hash_password(
        "CorrectPassword123!"
    )

    assert not verify_password(
        "WrongPassword123!",
        hashed,
    )


def test_access_token_round_trip():
    token = create_access_token(
        subject="user@example.com"
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user@example.com"
    assert "exp" in payload
    assert "iat" in payload


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject="user@example.com",
        expires_delta=timedelta(
            seconds=-1
        ),
    )

    with pytest.raises(
        jwt.ExpiredSignatureError
    ):
        decode_access_token(token)