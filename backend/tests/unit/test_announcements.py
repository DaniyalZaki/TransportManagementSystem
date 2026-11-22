import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from src.application.authorization.roles import Principal, Role
from src.modules.announcement.application.services import (
    AnnouncementService,
    InvalidAnnouncement,
)
from src.modules.announcement.domain.models import Announcement


class MemoryAnnouncements:
    def __init__(self):
        self.announcements = {}
        self.banners = {}

    async def publish(self, announcement):
        self.announcements[announcement.id] = announcement
        return announcement

    async def update(self, announcement):
        self.announcements[announcement.id] = announcement
        return announcement

    async def get(self, identifier): return self.announcements.get(identifier)
    async def public_announcements(self, now):
        return tuple(sorted((item for item in self.announcements.values() if item.is_visible_at(now)), key=lambda item: item.published_at, reverse=True))
    async def public_banners(self):
        return tuple(sorted((item for item in self.banners.values() if item.is_visible), key=lambda item: item.created_at, reverse=True))
    async def add_banner(self, banner): self.banners[banner.id] = banner; return banner
    async def get_banner(self, identifier): return self.banners.get(identifier)
    async def update_banner(self, banner): self.banners[banner.id] = banner; return banner
    async def delete_expired_or_removed(self, cutoff):
        return 0


class Cache:
    def __init__(self): self.invalidated = False
    def invalidate_announcements(self): self.invalidated = True


def manager():
    return Principal("manager", Role.TRANSPORT_MANAGEMENT, True)


def service(repository, cache=None):
    return AnnouncementService(
        repository, cache or Cache(), clock=lambda: datetime(2026, 11, 22, 9, tzinfo=UTC)
    )


def test_routine_announcements_publish_directly_and_are_newest_first():
    repository = MemoryAnnouncements()
    app = service(repository)
    first = asyncio.run(app.publish("First", "Routine notice", None, False, False, None, manager())).announcement
    repository.announcements[first.id] = Announcement(
        first.id, first.title, first.content, first.published_at - timedelta(minutes=1), first.expires_at,
        first.is_operational, first.confirmed_at, first.removed_at, first.updated_at,
    )
    second = asyncio.run(app.publish("Second", "Newer notice", None, False, False, None, manager())).announcement

    assert [item.id for item in asyncio.run(app.public_announcements())] == [second.id, first.id]


def test_operational_notice_requires_confirmation_and_urgent_creates_a_separate_banner():
    repository = MemoryAnnouncements()
    app = service(repository)
    with pytest.raises(InvalidAnnouncement, match="confirmed"):
        asyncio.run(app.publish("Diversion", "Route moved", None, False, True, None, manager()))

    outcome = asyncio.run(app.publish("Diversion", "Route moved", None, True, True, datetime(2026, 11, 22, 8, 59, tzinfo=UTC), manager()))

    assert outcome.banner is not None
    assert outcome.banner.announcement_id == outcome.announcement.id
    assert len(asyncio.run(app.public_banners())) == 1


def test_expiry_hides_announcement_but_does_not_hide_its_banner():
    repository = MemoryAnnouncements()
    app = service(repository)
    outcome = asyncio.run(app.publish("Closure", "Use gate B", datetime(2026, 11, 22, 10, tzinfo=UTC), True, True, datetime(2026, 11, 22, 7, tzinfo=UTC), manager()))
    repository.announcements[outcome.announcement.id] = Announcement(
        outcome.announcement.id, outcome.announcement.title, outcome.announcement.content,
        outcome.announcement.published_at, datetime(2026, 11, 22, 8, tzinfo=UTC),
        outcome.announcement.is_operational, outcome.announcement.confirmed_at,
        outcome.announcement.removed_at, outcome.announcement.updated_at,
    )

    assert asyncio.run(app.public_announcements()) == ()
    assert [banner.id for banner in asyncio.run(app.public_banners())] == [outcome.banner.id]


def test_remove_only_hides_banner_while_resolve_records_resolution():
    repository = MemoryAnnouncements()
    app = service(repository)
    outcome = asyncio.run(app.publish("Closure", "Use gate B", None, True, True, datetime(2026, 11, 22, 8, tzinfo=UTC), manager()))

    removed = asyncio.run(app.remove_banner(outcome.banner.id, manager()))
    assert removed.removed_at is not None and removed.resolved_at is None
    resolved = asyncio.run(app.resolve_banner(outcome.banner.id, manager()))
    assert resolved.resolved_at is not None
    assert asyncio.run(app.public_banners()) == ()


def test_announcement_edit_replaces_content_without_creating_a_version():
    repository = MemoryAnnouncements()
    app = service(repository)
    created = asyncio.run(app.publish("Title", "Original", None, False, False, None, manager())).announcement
    edited = asyncio.run(app.edit(created.id, "Updated", "Replacement", None, manager()))

    assert edited.id == created.id
    assert len(repository.announcements) == 1
    assert asyncio.run(app.public_announcements())[0].content == "Replacement"


def test_manual_removal_hides_an_announcement_without_touching_its_banner():
    repository = MemoryAnnouncements()
    app = service(repository)
    outcome = asyncio.run(app.publish("Closure", "Use gate B", None, True, True, datetime(2026, 11, 22, 8, tzinfo=UTC), manager()))

    asyncio.run(app.remove_announcement(outcome.announcement.id, manager()))

    assert asyncio.run(app.public_announcements()) == ()
    assert [banner.id for banner in asyncio.run(app.public_banners())] == [outcome.banner.id]


def test_naive_expiry_is_interpreted_as_pakistan_standard_time():
    repository = MemoryAnnouncements()
    app = service(repository)

    announcement = asyncio.run(app.publish("Notice", "PKT expiry", datetime(2026, 11, 22, 16), False, False, None, manager())).announcement

    assert announcement.expires_at is not None
    assert announcement.expires_at.utcoffset().total_seconds() == 18_000


def test_operational_confirmation_cannot_be_in_the_future():
    with pytest.raises(InvalidAnnouncement, match="future"):
        asyncio.run(service(MemoryAnnouncements()).publish(
            "Diversion", "Route moved", None, False, True,
            datetime(2026, 11, 22, 10, tzinfo=UTC), manager(),
        ))
