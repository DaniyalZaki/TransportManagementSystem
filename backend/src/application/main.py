import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.authentication.presentation.router import router as authentication_router
from src.modules.transport_data.presentation.router import router as transport_router
from src.modules.transport_data.presentation.admin_router import router as transport_admin_router
from src.infrastructure.configuration.settings import Settings
from src.modules.transport_data.infrastructure.change_set_repository import (
    PostgresChangeSetRepository,
)
from src.modules.audit.application.publication_audit import PostgresPublicationAudit
from src.modules.announcement.application.services import AnnouncementService
from src.modules.announcement.infrastructure.repository import PostgresAnnouncementRepository
from src.modules.announcement.presentation.router import (
    admin_router as announcement_admin_router,
    public_router as announcement_public_router,
)
from src.modules.feedback.application.services import FeedbackService
from src.modules.feedback.infrastructure.repository import PostgresFeedbackRepository
from src.modules.feedback.infrastructure.smtp_mailer import SmtpFeedbackMailer
from src.modules.feedback.presentation.router import router as feedback_router


@asynccontextmanager
async def _lifespan(_: FastAPI):
    """Run the approved draft/retired-record retention work in this one worker."""
    async def retain() -> None:
        repository = PostgresChangeSetRepository(Settings().database_url)
        audit = PostgresPublicationAudit(Settings().database_url)
        announcement_service = AnnouncementService(
            PostgresAnnouncementRepository(Settings().database_url),
            _AnnouncementCacheForCleanup(),
        )
        feedback_service = FeedbackService(
            PostgresFeedbackRepository(Settings().database_url), SmtpFeedbackMailer(Settings())
        )
        last_hourly_cleanup: datetime | None = None
        while True:
            try:
                now = datetime.now(UTC)
                await feedback_service.retry_due()
                if last_hourly_cleanup is None or now - last_hourly_cleanup >= timedelta(hours=1):
                    await audit.delete_expired(now)
                    await repository.delete_retired(now)
                    await announcement_service.cleanup()
                    await feedback_service.cleanup()
                    last_hourly_cleanup = now
            except Exception:
                # The next run retries; serving public reads must not stop on cleanup failure.
                pass
            await asyncio.sleep(60)

    task = asyncio.create_task(retain())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    """Compose the single-worker modular-monolith HTTP application."""
    app = FastAPI(title="Uzair Transport Service API", version="0.1.0", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(authentication_router)
    app.include_router(transport_router)
    app.include_router(transport_admin_router)
    app.include_router(announcement_public_router)
    app.include_router(announcement_admin_router)
    app.include_router(feedback_router)

    @app.get("/health", tags=["platform"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


class _AnnouncementCacheForCleanup:
    def invalidate_announcements(self) -> None:
        # Retention cleanup does not affect active public content.
        pass
