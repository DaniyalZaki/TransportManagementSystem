from datetime import datetime
from uuid import UUID

from src.infrastructure.database.connection import open_connection
from src.modules.announcement.domain.models import Announcement, UrgentBanner


class PostgresAnnouncementRepository:
    def __init__(self, database_url: str) -> None: self._database_url = database_url

    async def publish(self, item: Announcement) -> Announcement:
        async with open_connection(self._database_url) as connection:
            await connection.execute("""INSERT INTO announcements (id, title, content, published_at, expires_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6)""", item.id, item.title, item.content, item.published_at, item.expires_at, item.updated_at)
        return item

    async def update(self, item: Announcement) -> Announcement:
        async with open_connection(self._database_url) as connection:
            await connection.execute("""UPDATE announcements SET title=$2, content=$3, expires_at=$4, removed_at=$5, updated_at=$6 WHERE id=$1""", item.id, item.title, item.content, item.expires_at, item.removed_at, item.updated_at)
        return item

    async def get(self, identifier: UUID) -> Announcement | None:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow("SELECT * FROM announcements WHERE id=$1", identifier)
        return _announcement(row) if row else None

    async def public_announcements(self, now: datetime) -> tuple[Announcement, ...]:
        async with open_connection(self._database_url) as connection:
            rows = await connection.fetch("""SELECT * FROM announcements WHERE removed_at IS NULL AND (expires_at IS NULL OR expires_at > $1) ORDER BY published_at DESC""", now)
        return tuple(_announcement(row) for row in rows)

    async def current_announcements(self, now: datetime) -> tuple[Announcement, ...]:
        return await self.public_announcements(now)

    async def add_banner(self, item: UrgentBanner) -> UrgentBanner:
        async with open_connection(self._database_url) as connection:
            await connection.execute("INSERT INTO urgent_banners (id, announcement_id, title, content, created_at) VALUES ($1,$2,$3,$4,$5)", item.id, item.announcement_id, item.title, item.content, item.created_at)
        return item

    async def public_banners(self) -> tuple[UrgentBanner, ...]:
        async with open_connection(self._database_url) as connection:
            rows = await connection.fetch("SELECT * FROM urgent_banners WHERE removed_at IS NULL AND resolved_at IS NULL ORDER BY created_at DESC")
        return tuple(_banner(row) for row in rows)

    async def get_banner(self, identifier: UUID) -> UrgentBanner | None:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow("SELECT * FROM urgent_banners WHERE id=$1", identifier)
        return _banner(row) if row else None

    async def update_banner(self, item: UrgentBanner) -> UrgentBanner:
        async with open_connection(self._database_url) as connection:
            await connection.execute("UPDATE urgent_banners SET removed_at=$2, resolved_at=$3 WHERE id=$1", item.id, item.removed_at, item.resolved_at)
        return item

    async def delete_expired_or_removed(self, cutoff: datetime) -> int:
        async with open_connection(self._database_url) as connection:
            result = await connection.execute("""DELETE FROM announcements a WHERE (a.removed_at < $1 OR a.expires_at < $1)
                AND NOT EXISTS (SELECT 1 FROM urgent_banners b WHERE b.announcement_id=a.id AND b.removed_at IS NULL AND b.resolved_at IS NULL)""", cutoff)
        return int(result.rsplit(" ", 1)[-1])


def _announcement(row) -> Announcement:
    return Announcement(row["id"], row["title"], row["content"], row["published_at"], row["expires_at"], row["removed_at"], row["updated_at"])


def _banner(row) -> UrgentBanner:
    return UrgentBanner(row["id"], row["announcement_id"], row["title"], row["content"], row["created_at"], row["removed_at"], row["resolved_at"])
