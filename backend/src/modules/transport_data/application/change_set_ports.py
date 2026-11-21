from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.modules.transport_data.domain.change_sets import (
    DraftTransportSnapshot,
    TransportChangeSet,
)


class PublicationRecord(Protocol):
    change_set_id: UUID
    publisher: str
    published_at: datetime


class ChangeSetRepository(Protocol):
    async def expire_drafts(self, now: datetime) -> int:
        ...

    async def delete_retired(self, now: datetime) -> int:
        ...

    async def current_published(self) -> TransportChangeSet | None:
        ...

    async def get(self, change_set_id: UUID) -> TransportChangeSet | None:
        ...

    async def search_drafts(self, query: str) -> list[TransportChangeSet]:
        ...

    async def snapshot(self, change_set_id: UUID) -> DraftTransportSnapshot:
        ...

    async def create(
        self, change_set: TransportChangeSet, snapshot: DraftTransportSnapshot
    ) -> TransportChangeSet:
        ...

    async def publish(
        self, change_set_id: UUID, expected_base_id: UUID | None,
        publisher: str, published_at: datetime, audit: "PublicationAudit",
    ) -> TransportChangeSet:
        ...

    async def replace_snapshot(
        self, change_set_id: UUID, expected_version: int,
        snapshot: DraftTransportSnapshot, updated_at: datetime,
    ) -> TransportChangeSet:
        ...

    async def recover(
        self, source_change_set_id: UUID, publisher: str, recovered_at: datetime,
        audit: "PublicationAudit",
    ) -> TransportChangeSet:
        ...

    async def rebase(
        self, change_set_id: UUID, base_change_set_id: UUID | None,
        snapshot: DraftTransportSnapshot, rebased_at: datetime,
    ) -> TransportChangeSet:
        ...


class PublicationAudit(Protocol):
    async def record_publication(
        self, change_set_id: UUID, publisher: str, published_at: datetime,
        connection: object | None = None,
    ) -> None:
        ...

    async def is_recoverable(self, change_set_id: UUID, now: datetime) -> bool:
        ...

    async def recent_publications(self, now: datetime) -> list[tuple[UUID, str, datetime]]:
        ...


class PublishedTransportCache(Protocol):
    def invalidate_published_transport(self) -> None:
        ...
