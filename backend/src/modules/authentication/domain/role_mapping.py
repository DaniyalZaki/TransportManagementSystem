from dataclasses import dataclass
from datetime import datetime

from src.application.authorization.roles import Role


@dataclass(frozen=True, slots=True)
class RoleMapping:
    supabase_user_id: str
    role: Role
    active: bool
    deactivated_at: datetime | None = None
