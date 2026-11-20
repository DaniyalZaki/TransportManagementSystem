from src.application.main import create_app


def test_openapi_exposes_login_session_and_transport_management_account_routes() -> None:
    paths = create_app().openapi()["paths"]

    assert "/auth/login" in paths
    assert "/auth/session" in paths
    assert "/admin/accounts" in paths
    assert "/admin/accounts/{supabase_user_id}/deactivate" in paths

    account_parameters = paths["/admin/accounts"]["post"]["parameters"]
    assert any(
        parameter["name"] == "authorization" and parameter["in"] == "header"
        for parameter in account_parameters
    )
