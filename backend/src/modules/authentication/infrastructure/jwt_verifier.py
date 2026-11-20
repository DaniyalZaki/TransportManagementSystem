from collections.abc import Mapping

import jwt


class JwtVerifier:
    """Validates a Supabase-issued token locally; it never creates sessions."""

    def __init__(self, issuer: str, audience: str, signing_key: str) -> None:
        self._issuer = issuer
        self._audience = audience
        self._signing_key = signing_key

    def verify(self, token: str) -> Mapping[str, object]:
        return jwt.decode(
            token,
            self._signing_key,
            algorithms=["HS256"],
            audience=self._audience,
            issuer=self._issuer,
            options={"require": ["sub", "exp", "aud", "iss"]},
        )
