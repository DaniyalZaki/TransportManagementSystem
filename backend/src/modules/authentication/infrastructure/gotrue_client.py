import httpx

from src.modules.authentication.application.ports import AuthenticatedSession


class GoTrueEmailPasswordIdentity:
    """Narrow adapter for self-hosted Supabase Auth's password grant."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def sign_in(self, email: str, password: str) -> AuthenticatedSession:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self._base_url}/token",
                params={"grant_type": "password"},
                json={"email": email, "password": password},
            )
        if response.status_code in {400, 401, 422}:
            raise PermissionError("Invalid email address or password")
        response.raise_for_status()
        payload = response.json()
        user_id = payload.get("user", {}).get("id")
        access_token = payload.get("access_token")
        if not isinstance(user_id, str) or not isinstance(access_token, str):
            raise RuntimeError("Supabase Auth returned an invalid password-grant response")
        refresh_token = payload.get("refresh_token")
        return AuthenticatedSession(
            supabase_user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token if isinstance(refresh_token, str) else None,
        )
