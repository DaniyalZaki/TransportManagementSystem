from datetime import UTC, datetime, timedelta

import jwt
import pytest

from src.modules.authentication.infrastructure.jwt_verifier import JwtVerifier

SIGNING_KEY = "test-signing-key-with-at-least-32-bytes"


def test_verifier_accepts_a_locally_signed_supabase_token() -> None:
    token = jwt.encode(
        {
            "sub": "user-1",
            "iss": "http://localhost:9999",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SIGNING_KEY,
        algorithm="HS256",
    )

    claims = JwtVerifier(
        "http://localhost:9999", "authenticated", SIGNING_KEY
    ).verify(token)

    assert claims["sub"] == "user-1"


def test_verifier_rejects_a_token_for_another_audience() -> None:
    token = jwt.encode(
        {
            "sub": "user-1",
            "iss": "http://localhost:9999",
            "aud": "other-service",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SIGNING_KEY,
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidAudienceError):
        JwtVerifier("http://localhost:9999", "authenticated", SIGNING_KEY).verify(
            token
        )
