from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class FeedbackSubmission:
    """A Feedback-owned record; delivery state is never exposed publicly."""

    id: UUID
    content: str
    normalized_content: str
    name: str | None
    contact: str | None
    received_at: datetime
    delivered_at: datetime | None = None
    retry_count: int = 0
    next_retry_at: datetime | None = None

    def delivered(self, at: datetime) -> "FeedbackSubmission":
        return FeedbackSubmission(self.id, self.content, self.normalized_content, self.name, self.contact, self.received_at, at, self.retry_count, None)

    def retry_at(self, at: datetime, retry_count: int) -> "FeedbackSubmission":
        return FeedbackSubmission(self.id, self.content, self.normalized_content, self.name, self.contact, self.received_at, None, retry_count, at)
