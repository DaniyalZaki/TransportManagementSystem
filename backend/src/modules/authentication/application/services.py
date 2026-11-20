from datetime import UTC, datetime

from src.application.authorization.roles import Principal, Role, require_role
from src.modules.authentication.application.ports import (
    AuthenticatedSession,
    EmailPasswordIdentityProvider,
    RoleMappingRepository,
    TokenVerifier,
)
from src.modules.authentication.application.session_policy import SessionPolicy
from src.modules.authentication.domain.role_mapping import RoleMapping


class UnknownPrivilegedAccount(PermissionError):
    """A Supabase identity without a backend-owned role mapping."""


class AuthenticationService:
    def __init__(
        self,
        identity_provider: EmailPasswordIdentityProvider,
        role_mappings: RoleMappingRepository,
        token_verifier: TokenVerifier,
        session_policy: SessionPolicy | None = None,
    ) -> None:
        self._identity_provider = identity_provider
        self._role_mappings = role_mappings
        self._token_verifier = token_verifier
        self._session_policy = session_policy or SessionPolicy()

    async def login(self, email: str, password: str) -> AuthenticatedSession:
        session = await self._identity_provider.sign_in(email, password)
        mapping = await self._required_mapping(session.supabase_user_id)
        self._session_policy.allow_new_login(mapping)
        return session

    async def authenticate(self, access_token: str) -> Principal:
        claims = self._token_verifier.verify(access_token)
        subject = claims.get("sub")
        issued_at = claims.get("iat")
        if not isinstance(subject, str) or not isinstance(issued_at, (int, float)):
            raise PermissionError("The access token has invalid required claims")
        mapping = await self._required_mapping(subject)
        self._session_policy.allow_existing_session(
            mapping, datetime.fromtimestamp(issued_at, tz=UTC)
        )
        return Principal(subject=subject, role=mapping.role, active=True)

    async def _required_mapping(self, supabase_user_id: str) -> RoleMapping:
        mapping = await self._role_mappings.get(supabase_user_id)
        if mapping is None:
            raise UnknownPrivilegedAccount("No privileged role is assigned to this account")
        return mapping


class AccountManagementService:
    def __init__(self, role_mappings: RoleMappingRepository) -> None:
        self._role_mappings = role_mappings

    async def create_mapping(
        self, actor: Principal, supabase_user_id: str, role: Role
    ) -> RoleMapping:
        require_role(actor, Role.TRANSPORT_MANAGEMENT)
        return await self._role_mappings.create(supabase_user_id, role)

    async def deactivate(self, actor: Principal, supabase_user_id: str) -> None:
        require_role(actor, Role.TRANSPORT_MANAGEMENT)
        await self._role_mappings.deactivate(supabase_user_id)
