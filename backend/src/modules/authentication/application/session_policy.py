from datetime import datetime

from src.modules.authentication.domain.role_mapping import RoleMapping


class AccountDeactivatedForNewLogin(PermissionError):
    """Raised when an account may not start a new privileged session."""


class SessionPolicy:
    """Keeps token-expiry semantics intact when an account is deactivated."""

    def allow_new_login(self, mapping: RoleMapping) -> None:
        if not mapping.active:
            raise AccountDeactivatedForNewLogin(
                "The account is deactivated and cannot start a new session"
            )

    def allow_existing_session(
        self, mapping: RoleMapping, issued_at: datetime
    ) -> None:
        if mapping.active or mapping.deactivated_at is None:
            return
        if issued_at > mapping.deactivated_at:
            raise AccountDeactivatedForNewLogin(
                "The account is deactivated and cannot start a new session"
            )
