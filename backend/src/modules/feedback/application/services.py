from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.modules.feedback.application.ports import FeedbackMailer, FeedbackRepository
from src.modules.feedback.domain.models import FeedbackSubmission


class FeedbackSubmissionError(ValueError):
    pass


@dataclass(frozen=True)
class FeedbackResult:
    outcome: str
    submission: FeedbackSubmission | None


class FeedbackService:
    """Owns feedback validation, database duplicate detection, SMTP delivery, and retry state."""

    _retry_delays = (timedelta(minutes=1), timedelta(minutes=5), timedelta(minutes=30))

    def __init__(self, repository: FeedbackRepository, mailer: FeedbackMailer, clock=lambda: datetime.now(UTC)) -> None:
        self._repository, self._mailer, self._clock = repository, mailer, clock

    async def submit(self, content: str, name: str | None, contact: str | None, honeypot: str) -> FeedbackResult:
        if honeypot.strip():
            raise FeedbackSubmissionError("invalid feedback submission")
        content = content.strip()
        if not content:
            raise FeedbackSubmissionError("Feedback content is required")
        now = self._clock()
        normalized = self.normalize(content)
        existing = await self._repository.find_recent_by_normalized_content(normalized, now - timedelta(minutes=10))
        if existing is not None:
            if existing.delivered_at is None and existing.next_retry_at is not None:
                return FeedbackResult("already_received", existing)
            raise FeedbackSubmissionError("Feedback was already received")
        item = FeedbackSubmission(uuid4(), content, normalized, self._optional(name), self._optional(contact), now)
        await self._repository.save(item)
        try:
            await self._mailer.send(item)
        except Exception:
            failed = item.retry_at(now + self._retry_delays[0], 0)
            await self._repository.update_delivery(failed)
            return FeedbackResult("delivery_failed", failed)
        delivered = item.delivered(now)
        await self._repository.update_delivery(delivered)
        return FeedbackResult("received", delivered)

    async def retry_due(self) -> int:
        now = self._clock()
        retried = 0
        for item in await self._repository.due_retries(now):
            try:
                await self._mailer.send(item)
            except Exception:
                next_count = item.retry_count + 1
                next_retry = now + self._retry_delays[next_count] if next_count < len(self._retry_delays) else None
                await self._repository.update_delivery(item.retry_at(next_retry, next_count) if next_retry else item.retry_at(None, next_count))
            else:
                await self._repository.update_delivery(item.delivered(now))
            retried += 1
        return retried

    async def cleanup(self) -> int:
        return await self._repository.delete_before(self._clock() - timedelta(days=30))

    @staticmethod
    def normalize(content: str) -> str:
        return " ".join(content.casefold().split())

    @staticmethod
    def _optional(value: str | None) -> str | None:
        return value.strip() or None if value is not None else None
