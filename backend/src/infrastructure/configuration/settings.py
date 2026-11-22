from dataclasses import dataclass
from os import getenv

DEFAULT_ENVIRONMENT = "local"
DEFAULT_DATABASE_URL = (
    "postgresql://uzair_transport:local-development-only@localhost:5432/uzair_transport"
)
DEFAULT_SUPABASE_ISSUER = "http://localhost:9999"
DEFAULT_SUPABASE_AUDIENCE = "authenticated"
DEFAULT_SUPABASE_AUTH_URL = "http://localhost:9999"


@dataclass(frozen=True, slots=True)
class Settings:
    """Environment-backed settings; no credentials are committed to the repository."""

    app_environment: str = DEFAULT_ENVIRONMENT
    database_url: str = DEFAULT_DATABASE_URL
    supabase_jwt_issuer: str = DEFAULT_SUPABASE_ISSUER
    supabase_jwt_audience: str = DEFAULT_SUPABASE_AUDIENCE
    supabase_auth_url: str = DEFAULT_SUPABASE_AUTH_URL
    supabase_jwt_signing_key: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender: str | None = None
    feedback_recipient: str | None = None

    def __init__(
        self,
        app_environment: str | None = None,
        database_url: str | None = None,
        supabase_jwt_issuer: str | None = None,
        supabase_jwt_audience: str | None = None,
        supabase_auth_url: str | None = None,
        supabase_jwt_signing_key: str | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        smtp_sender: str | None = None,
        feedback_recipient: str | None = None,
        **_: object,
    ) -> None:
        resolved_database_url = database_url or getenv("UTS_DATABASE_URL", DEFAULT_DATABASE_URL)
        if not resolved_database_url.startswith(("postgresql://", "postgres://")):
            raise ValueError("PostgreSQL is required as the system of record")
        object.__setattr__(
            self,
            "app_environment",
            app_environment or getenv("UTS_APP_ENVIRONMENT", DEFAULT_ENVIRONMENT),
        )
        object.__setattr__(self, "database_url", resolved_database_url)
        object.__setattr__(
            self,
            "supabase_jwt_issuer",
            supabase_jwt_issuer
            or getenv("UTS_SUPABASE_JWT_ISSUER", DEFAULT_SUPABASE_ISSUER),
        )
        object.__setattr__(
            self,
            "supabase_jwt_audience",
            supabase_jwt_audience
            or getenv("UTS_SUPABASE_JWT_AUDIENCE", DEFAULT_SUPABASE_AUDIENCE),
        )
        object.__setattr__(
            self,
            "supabase_auth_url",
            supabase_auth_url or getenv("UTS_SUPABASE_AUTH_URL", DEFAULT_SUPABASE_AUTH_URL),
        )
        object.__setattr__(
            self,
            "supabase_jwt_signing_key",
            supabase_jwt_signing_key or getenv("UTS_SUPABASE_JWT_SIGNING_KEY"),
        )
        object.__setattr__(self, "smtp_host", smtp_host or getenv("UTS_SMTP_HOST"))
        object.__setattr__(self, "smtp_port", smtp_port or int(getenv("UTS_SMTP_PORT", "587")))
        object.__setattr__(self, "smtp_username", smtp_username or getenv("UTS_SMTP_USERNAME"))
        object.__setattr__(self, "smtp_password", smtp_password or getenv("UTS_SMTP_PASSWORD"))
        object.__setattr__(self, "smtp_sender", smtp_sender or getenv("UTS_SMTP_SENDER"))
        object.__setattr__(self, "feedback_recipient", feedback_recipient or getenv("UTS_FEEDBACK_RECIPIENT"))
