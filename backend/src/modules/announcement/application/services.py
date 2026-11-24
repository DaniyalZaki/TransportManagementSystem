from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo
from uuid import UUID, uuid4

from src.application.authorization.roles import Principal, Role
from src.modules.announcement.application.ports import AnnouncementCache, AnnouncementRepository
from src.modules.announcement.domain.models import Announcement, UrgentBanner


class InvalidAnnouncement(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PublishedAnnouncement:
    announcement: Announcement
    banner: UrgentBanner | None


class AnnouncementService:
    """Direct announcement publication and independent urgent-banner lifecycle."""

    def __init__(self, repository: AnnouncementRepository, cache: AnnouncementCache, clock=lambda: datetime.now(UTC)) -> None:
        self._repository, self._cache, self._clock = repository, cache, clock

    async def publish(self, title: str, content: str, expires_at: datetime | None, urgent: bool, principal: Principal | None = None) -> PublishedAnnouncement:
        self._require_privileged(principal)
        now = self._clock()
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Karachi"))
        title, content = self._valid_text(title, content)
        if expires_at is not None and expires_at <= now:
            # Past expiries are allowed for lifecycle correctness only in tests/imports; direct publications must be live.
            raise InvalidAnnouncement("Announcement expiry must be in the future")
        announcement = await self._repository.publish(Announcement(uuid4(), title, content, now, expires_at, None, now))
        banner = None
        if urgent:
            banner = await self._repository.add_banner(UrgentBanner(uuid4(), announcement.id, title, content, now))
        self._cache.invalidate_announcements()
        return PublishedAnnouncement(announcement, banner)

    async def edit(self, identifier: UUID, title: str, content: str, expires_at: datetime | None, principal: Principal | None = None) -> Announcement:
        self._require_privileged(principal)
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Karachi"))
        announcement = await self._required(identifier)
        title, content = self._valid_text(title, content)
        updated = await self._repository.update(announcement.edit(title, content, expires_at, self._clock()))
        self._cache.invalidate_announcements()
        return updated

    async def public_announcements(self) -> tuple[Announcement, ...]:
        return await self._repository.public_announcements(self._clock())

    async def current_items(
        self, principal: Principal | None = None,
    ) -> tuple[tuple[Announcement, ...], tuple[UrgentBanner, ...]]:
        self._require_privileged(principal)
        return (
            await self._repository.current_announcements(self._clock()),
            await self._repository.public_banners(),
        )

    async def remove_announcement(self, identifier: UUID, principal: Principal | None = None) -> Announcement:
        self._require_privileged(principal)
        updated = await self._repository.update((await self._required(identifier)).remove(self._clock()))
        self._cache.invalidate_announcements()
        return updated

    async def public_banners(self) -> tuple[UrgentBanner, ...]:
        return await self._repository.public_banners()

    async def remove_banner(self, identifier: UUID, principal: Principal | None = None) -> UrgentBanner:
        self._require_privileged(principal)
        banner = await self._required_banner(identifier)
        updated = await self._repository.update_banner(banner.remove(self._clock()))
        self._cache.invalidate_announcements()
        return updated

    async def resolve_banner(self, identifier: UUID, principal: Principal | None = None) -> UrgentBanner:
        self._require_privileged(principal)
        banner = await self._required_banner(identifier)
        updated = await self._repository.update_banner(banner.resolve(self._clock()))
        self._cache.invalidate_announcements()
        return updated

    async def cleanup(self) -> int:
        from datetime import timedelta
        return await self._repository.delete_expired_or_removed(self._clock() - timedelta(days=30))

    async def _required(self, identifier: UUID) -> Announcement:
        item = await self._repository.get(identifier)
        if item is None: raise InvalidAnnouncement("Announcement does not exist")
        return item

    async def _required_banner(self, identifier: UUID) -> UrgentBanner:
        item = await self._repository.get_banner(identifier)
        if item is None: raise InvalidAnnouncement("Urgent banner does not exist")
        return item

    @staticmethod
    def _valid_text(title: str, content: str) -> tuple[str, str]:
        if not title.strip():
            raise InvalidAnnouncement("Title is required")
        return title.strip(), content.strip()

    @staticmethod
    def _require_privileged(principal: Principal | None) -> None:
        if principal is None: return
        if not principal.active or principal.role not in {Role.TRANSPORT_MANAGEMENT, Role.DESIGNATED_ADMINISTRATOR}:
            raise PermissionError("A privileged announcement role is required")
