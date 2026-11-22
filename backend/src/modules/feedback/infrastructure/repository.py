from datetime import datetime

from src.infrastructure.database.connection import open_connection
from src.modules.feedback.domain.models import FeedbackSubmission


class PostgresFeedbackRepository:
    def __init__(self, database_url: str) -> None: self._database_url = database_url

    async def find_recent_by_normalized_content(self, normalized_content: str, since: datetime) -> FeedbackSubmission | None:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow("""SELECT * FROM feedback_submissions
                WHERE normalized_content=$1 AND received_at > $2 ORDER BY received_at DESC LIMIT 1""", normalized_content, since)
        return _submission(row) if row else None

    async def save(self, item: FeedbackSubmission) -> FeedbackSubmission:
        async with open_connection(self._database_url) as connection:
            await connection.execute("""INSERT INTO feedback_submissions
                (id, content, normalized_content, name, contact, received_at, delivered_at, retry_count, next_retry_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""", item.id, item.content, item.normalized_content, item.name, item.contact, item.received_at, item.delivered_at, item.retry_count, item.next_retry_at)
        return item

    async def update_delivery(self, item: FeedbackSubmission) -> FeedbackSubmission:
        async with open_connection(self._database_url) as connection:
            await connection.execute("""UPDATE feedback_submissions SET delivered_at=$2, retry_count=$3, next_retry_at=$4 WHERE id=$1""", item.id, item.delivered_at, item.retry_count, item.next_retry_at)
        return item

    async def due_retries(self, now: datetime) -> tuple[FeedbackSubmission, ...]:
        async with open_connection(self._database_url) as connection:
            rows = await connection.fetch("SELECT * FROM feedback_submissions WHERE delivered_at IS NULL AND next_retry_at IS NOT NULL AND next_retry_at <= $1 ORDER BY next_retry_at", now)
        return tuple(_submission(row) for row in rows)

    async def delete_before(self, cutoff: datetime) -> int:
        async with open_connection(self._database_url) as connection:
            result = await connection.execute("DELETE FROM feedback_submissions WHERE received_at < $1", cutoff)
        return int(result.rsplit(" ", 1)[-1])


def _submission(row) -> FeedbackSubmission:
    return FeedbackSubmission(row["id"], row["content"], row["normalized_content"], row["name"], row["contact"], row["received_at"], row["delivered_at"], row["retry_count"], row["next_retry_at"])
