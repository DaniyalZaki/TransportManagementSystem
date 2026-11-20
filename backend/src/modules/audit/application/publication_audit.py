"""Audit's public interface for publication-only records."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.infrastructure.database.connection import open_connection


class PostgresPublicationAudit:
    """Audit owns this append-only publication record; no edit history is stored."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    async def record_publication(
        self, change_set_id: UUID, publisher: str, published_at: datetime,
        connection: object | None = None,
    ) -> None:
        if connection is not None:
            await connection.execute(
                """
                INSERT INTO audit_transport_publications
                    (id, change_set_id, publisher_supabase_user_id, published_at, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid4(), change_set_id, publisher, published_at,
                published_at + timedelta(days=30),
            )
            return
        async with open_connection(self._database_url) as database_connection:
            await self.record_publication(
                change_set_id, publisher, published_at, database_connection
            )

    async def is_recoverable(self, change_set_id: UUID, now: datetime) -> bool:
        async with open_connection(self._database_url) as connection:
            return bool(await connection.fetchval(
                """SELECT EXISTS (
                    SELECT 1 FROM audit_transport_publications
                    WHERE change_set_id = $1 AND expires_at > $2
                )""",
                change_set_id, now,
            ))

    async def recent_publications(self, now: datetime) -> list[tuple[UUID, str, datetime]]:
        async with open_connection(self._database_url) as connection:
            rows = await connection.fetch(
                """SELECT change_set_id, publisher_supabase_user_id, published_at
                FROM audit_transport_publications WHERE expires_at > $1
                ORDER BY published_at DESC""", now,
            )
        return [
            (row["change_set_id"], row["publisher_supabase_user_id"], row["published_at"])
            for row in rows
        ]

    async def delete_expired(self, now: datetime) -> int:
        """Delete Audit-owned records before their retired snapshots are removed."""
        async with open_connection(self._database_url) as connection:
            result = await connection.execute(
                "DELETE FROM audit_transport_publications WHERE expires_at <= $1", now
            )
        return int(result.rsplit(" ", 1)[-1])
