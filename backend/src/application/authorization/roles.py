from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    TRANSPORT_MANAGEMENT = "transport_management"
    DESIGNATED_ADMINISTRATOR = "designated_administrator"


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    role: Role
    active: bool


def require_role(principal: Principal, required: Role) -> None:
    """Enforce backend RBAC independently from either frontend client."""
    if not principal.active:
        raise PermissionError("The account is deactivated and cannot start a new session")
    if principal.role is not required:
        raise PermissionError(f"{required.value.replace('_', ' ').title()} access is required")
