from src.infrastructure.configuration.settings import Settings


def test_settings_accepts_local_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_environment == "local"
    assert settings.database_url.startswith("postgresql://")
    assert settings.supabase_jwt_issuer.startswith("http://")


def test_settings_rejects_non_postgres_database_url() -> None:
    try:
        Settings(database_url="sqlite:///not-allowed.db")
    except ValueError as error:
        assert "PostgreSQL" in str(error)
    else:
        raise AssertionError("SQLite must not be accepted as the system of record")


def test_settings_accepts_the_local_jwt_verification_configuration() -> None:
    settings = Settings(
        supabase_auth_url="http://localhost:9999",
        supabase_jwt_signing_key="local-development-signing-key",
    )

    assert settings.supabase_auth_url == "http://localhost:9999"
    assert settings.supabase_jwt_signing_key == "local-development-signing-key"
