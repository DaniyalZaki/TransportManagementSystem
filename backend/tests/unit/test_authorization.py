import pytest

from src.application.authorization.roles import Principal, Role, require_role


def test_transport_management_is_authorized_for_account_management() -> None:
    principal = Principal(subject="user-1", role=Role.TRANSPORT_MANAGEMENT, active=True)

    require_role(principal, Role.TRANSPORT_MANAGEMENT)


def test_designated_administrator_cannot_manage_accounts() -> None:
    principal = Principal(subject="user-2", role=Role.DESIGNATED_ADMINISTRATOR, active=True)

    with pytest.raises(PermissionError, match="Transport Management"):
        require_role(principal, Role.TRANSPORT_MANAGEMENT)


def test_deactivated_account_is_rejected_for_newly_validated_token() -> None:
    principal = Principal(subject="user-3", role=Role.TRANSPORT_MANAGEMENT, active=False)

    with pytest.raises(PermissionError, match="deactivated"):
        require_role(principal, Role.TRANSPORT_MANAGEMENT)
