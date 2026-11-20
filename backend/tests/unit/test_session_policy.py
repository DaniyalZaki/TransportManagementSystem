from datetime import UTC, datetime, timedelta

import pytest

from src.modules.authentication.application.session_policy import (
    AccountDeactivatedForNewLogin,
    SessionPolicy,
)
from src.modules.authentication.domain.role_mapping import RoleMapping
from src.application.authorization.roles import Role


def test_active_mapping_allows_new_login() -> None:
    mapping = RoleMapping("user-1", Role.TRANSPORT_MANAGEMENT, True)

    assert SessionPolicy().allow_new_login(mapping) is None


def test_deactivation_rejects_a_new_login() -> None:
    mapping = RoleMapping("user-1", Role.TRANSPORT_MANAGEMENT, False)

    with pytest.raises(AccountDeactivatedForNewLogin):
        SessionPolicy().allow_new_login(mapping)


def test_token_issued_before_deactivation_remains_usable_until_expiry() -> None:
    deactivated_at = datetime(2026, 11, 20, 10, tzinfo=UTC)
    mapping = RoleMapping(
        "user-1", Role.TRANSPORT_MANAGEMENT, False, deactivated_at=deactivated_at
    )

    assert SessionPolicy().allow_existing_session(
        mapping, deactivated_at - timedelta(seconds=1)
    ) is None


def test_token_issued_after_deactivation_is_rejected() -> None:
    deactivated_at = datetime(2026, 11, 20, 10, tzinfo=UTC)
    mapping = RoleMapping(
        "user-1", Role.TRANSPORT_MANAGEMENT, False, deactivated_at=deactivated_at
    )

    with pytest.raises(AccountDeactivatedForNewLogin):
        SessionPolicy().allow_existing_session(mapping, deactivated_at + timedelta(seconds=1))
