from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from src.application.authorization.roles import Role
from src.modules.authentication.domain.role_mapping import RoleMapping


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    supabase_user_id: str
    access_token: str
    refresh_token: str | None


class EmailPasswordIdentityProvider(Protocol):
    async def sign_in(self, email: str, password: str) -> AuthenticatedSession: ...


class RoleMappingRepository(Protocol):
    async def get(self, supabase_user_id: str) -> RoleMapping | None: ...

    async def create(self, supabase_user_id: str, role: Role) -> RoleMapping: ...

    async def deactivate(self, supabase_user_id: str) -> None: ...


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Mapping[str, object]: ...
