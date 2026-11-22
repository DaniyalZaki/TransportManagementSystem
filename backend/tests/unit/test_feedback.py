import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.feedback.application.services import FeedbackService, FeedbackSubmissionError


class MemoryFeedback:
    def __init__(self):
        self.items = []

    async def find_recent_by_normalized_content(self, normalized_content, since):
        return next((item for item in self.items if item.normalized_content == normalized_content and item.received_at > since), None)

    async def save(self, item):
        self.items.append(item)
        return item

    async def update_delivery(self, item):
        self.items[self.items.index(next(existing for existing in self.items if existing.id == item.id))] = item
        return item

    async def due_retries(self, now):
        return tuple(item for item in self.items if item.next_retry_at and item.next_retry_at <= now)

    async def delete_before(self, cutoff):
        before = len(self.items)
        self.items = [item for item in self.items if item.received_at >= cutoff]
        return before - len(self.items)


class Mailer:
    def __init__(self, outcomes): self.outcomes = iter(outcomes); self.delivered = []
    async def send(self, item):
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception): raise outcome
        self.delivered.append(item)


def service(repository, mailer, now=datetime(2026, 11, 22, 9, tzinfo=UTC)):
    return FeedbackService(repository, mailer, clock=lambda: now)


def test_anonymous_feedback_is_delivered_and_returns_a_receipt():
    app = service(MemoryFeedback(), Mailer([None]))

    result = asyncio.run(app.submit("Service was helpful", None, None, ""))

    assert result.outcome == "received"
    assert result.submission.name is None
    assert result.submission.contact is None
    assert result.submission.delivered_at is not None


def test_normalization_collapses_case_outer_and_internal_whitespace_for_duplicate_checking():
    repository = MemoryFeedback()
    app = service(repository, Mailer([None]))
    asyncio.run(app.submit("  Bus   was LATE  ", None, None, ""))

    with pytest.raises(FeedbackSubmissionError, match="already received"):
        asyncio.run(app.submit("bus was late", "Name", "contact@example.edu", ""))


def test_duplicate_at_exactly_ten_minutes_is_not_rejected():
    repository = MemoryFeedback()
    first = service(repository, Mailer([None]), datetime(2026, 11, 22, 9, tzinfo=UTC))
    asyncio.run(first.submit("Same feedback", None, None, ""))
    second = service(repository, Mailer([None]), datetime(2026, 11, 22, 9, 10, tzinfo=UTC))

    assert asyncio.run(second.submit("same feedback", None, None, "")).outcome == "received"


def test_populated_honeypot_is_rejected_without_persistence_or_delivery():
    repository = MemoryFeedback()
    with pytest.raises(FeedbackSubmissionError, match="invalid"):
        asyncio.run(service(repository, Mailer([None])).submit("Help", None, None, "bot value"))

    assert repository.items == []


def test_initial_smtp_failure_is_retained_and_schedules_first_retry():
    repository = MemoryFeedback()
    app = service(repository, Mailer([OSError("mail unavailable")]))

    result = asyncio.run(app.submit("Driver was late", None, None, ""))

    assert result.outcome == "delivery_failed"
    assert result.submission.delivered_at is None
    assert result.submission.retry_count == 0
    assert result.submission.next_retry_at == datetime(2026, 11, 22, 9, 1, tzinfo=UTC)


def test_pending_duplicate_gets_neutral_already_received_response_without_a_second_send():
    repository = MemoryFeedback()
    app = service(repository, Mailer([OSError("mail unavailable")]))
    asyncio.run(app.submit("Driver was late", None, None, ""))

    result = asyncio.run(app.submit(" DRIVER  was  late ", None, None, ""))

    assert result.outcome == "already_received"
    assert len(repository.items) == 1


def test_failed_delivery_retries_at_one_five_and_thirty_minutes_then_stops():
    repository = MemoryFeedback()
    mailer = Mailer([OSError("initial"), OSError("one"), OSError("five"), OSError("thirty")])
    app = service(repository, mailer)
    asyncio.run(app.submit("Missed stop", None, None, ""))

    for instant, expected in [
        (datetime(2026, 11, 22, 9, 1, tzinfo=UTC), datetime(2026, 11, 22, 9, 6, tzinfo=UTC)),
        (datetime(2026, 11, 22, 9, 6, tzinfo=UTC), datetime(2026, 11, 22, 9, 36, tzinfo=UTC)),
        (datetime(2026, 11, 22, 9, 36, tzinfo=UTC), None),
    ]:
        app = service(repository, mailer, instant)
        assert asyncio.run(app.retry_due()) == 1
        assert repository.items[0].next_retry_at == expected

    assert repository.items[0].retry_count == 3


def test_successful_retry_marks_delivered_without_a_user_notification_channel():
    repository = MemoryFeedback()
    app = service(repository, Mailer([OSError("initial"), None]))
    asyncio.run(app.submit("Late departure", None, None, ""))
    retry = service(repository, app._mailer, datetime(2026, 11, 22, 9, 1, tzinfo=UTC))

    assert asyncio.run(retry.retry_due()) == 1
    assert repository.items[0].delivered_at == datetime(2026, 11, 22, 9, 1, tzinfo=UTC)
    assert repository.items[0].next_retry_at is None


def test_retention_removes_feedback_after_thirty_days():
    repository = MemoryFeedback()
    app = service(repository, Mailer([None]))
    asyncio.run(app.submit("Old feedback", None, None, ""))
    repository.items[0] = repository.items[0].__class__(**{**repository.items[0].__dict__, "received_at": datetime(2026, 10, 22, 8, 59, tzinfo=UTC)})

    assert asyncio.run(app.cleanup()) == 1
    assert repository.items == []
