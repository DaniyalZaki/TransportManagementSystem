from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Announcement:
    id: UUID
    title: str
    content: str
    published_at: datetime
    expires_at: datetime | None
    removed_at: datetime | None
    updated_at: datetime

    def is_visible_at(self, now: datetime) -> bool:
        return self.removed_at is None and (self.expires_at is None or self.expires_at > now)

    def edit(self, title: str, content: str, expires_at: datetime | None, now: datetime) -> "Announcement":
        return replace(self, title=title, content=content, expires_at=expires_at, updated_at=now)

    def remove(self, now: datetime) -> "Announcement":
        return replace(self, removed_at=now, updated_at=now)


@dataclass(frozen=True, slots=True)
class UrgentBanner:
    id: UUID
    announcement_id: UUID
    title: str
    content: str
    created_at: datetime
    removed_at: datetime | None = None
    resolved_at: datetime | None = None

    @property
    def is_visible(self) -> bool:
        return self.removed_at is None and self.resolved_at is None

    def remove(self, now: datetime) -> "UrgentBanner":
        return replace(self, removed_at=now)

    def resolve(self, now: datetime) -> "UrgentBanner":
        return replace(self, resolved_at=now)
