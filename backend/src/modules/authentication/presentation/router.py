from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, validator

from src.application.authorization.roles import Principal, Role
from src.infrastructure.configuration.settings import Settings
from src.modules.authentication.application.services import (
    AccountManagementService,
    AuthenticationService,
    UnknownPrivilegedAccount,
)
from src.modules.authentication.application.session_policy import (
    AccountDeactivatedForNewLogin,
)
from src.modules.authentication.infrastructure.gotrue_client import (
    GoTrueEmailPasswordIdentity,
)
from src.modules.authentication.infrastructure.jwt_verifier import JwtVerifier
from src.modules.authentication.infrastructure.role_mapping_repository import (
    PostgresRoleMappingRepository,
)

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str

    @validator("email")
    def email_must_have_a_domain(cls, value: str) -> str:
        if "@" not in value or value.endswith("@"):
            raise ValueError("A valid email address is required")
        return value


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None
    token_type: str = "bearer"


class AccountMappingRequest(BaseModel):
    supabase_user_id: str
    role: Role


class AccountMappingResponse(BaseModel):
    supabase_user_id: str
    role: Role
    active: bool


def _services() -> tuple[AuthenticationService, AccountManagementService]:
    settings = Settings()
    if not settings.supabase_jwt_signing_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication signing-key configuration is unavailable",
        )
    role_mappings = PostgresRoleMappingRepository(settings.database_url)
    authentication = AuthenticationService(
        GoTrueEmailPasswordIdentity(settings.supabase_auth_url),
        role_mappings,
        JwtVerifier(
            settings.supabase_jwt_issuer,
            settings.supabase_jwt_audience,
            settings.supabase_jwt_signing_key,
        ),
    )
    return authentication, AccountManagementService(role_mappings)


async def _principal(
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required"
        )
    authentication, _ = _services()
    try:
        return await authentication.authenticate(authorization.removeprefix("Bearer "))
    except (PermissionError, UnknownPrivilegedAccount) as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    authentication, _ = _services()
    try:
        session = await authentication.login(payload.email, payload.password)
    except (PermissionError, UnknownPrivilegedAccount, AccountDeactivatedForNewLogin) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    return LoginResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )


@router.get("/auth/session", response_model=AccountMappingResponse)
async def current_session(
    principal: Annotated[Principal, Depends(_principal)],
) -> AccountMappingResponse:
    return AccountMappingResponse(
        supabase_user_id=principal.subject, role=principal.role, active=principal.active
    )


@router.post(
    "/admin/accounts",
    response_model=AccountMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account_mapping(
    payload: AccountMappingRequest,
    principal: Annotated[Principal, Depends(_principal)],
) -> AccountMappingResponse:
    _, accounts = _services()
    try:
        mapping = await accounts.create_mapping(
            principal, payload.supabase_user_id, payload.role
        )
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    return AccountMappingResponse(
        supabase_user_id=mapping.supabase_user_id,
        role=mapping.role,
        active=mapping.active,
    )


@router.post(
    "/admin/accounts/{supabase_user_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_account(
    supabase_user_id: str,
    principal: Annotated[Principal, Depends(_principal)],
) -> None:
    _, accounts = _services()
    try:
        await accounts.deactivate(principal, supabase_user_id)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
