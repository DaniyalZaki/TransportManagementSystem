"""Domain records for the privileged transport draft/publish lifecycle."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from src.modules.transport_data.domain.schedule import (
    Assignment,
    DepartureOverride,
    Route,
    WeeklyDeparture,
)


class TransportChangeSetStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class DraftTransportSnapshot:
    routes: tuple[Route, ...]
    buses: tuple[str, ...]
    assignments: tuple[Assignment, ...]
    weekly_departures: tuple[WeeklyDeparture, ...]
    overrides: tuple[DepartureOverride, ...]


@dataclass(frozen=True, slots=True)
class TransportChangeSet:
    id: UUID
    name: str
    status: TransportChangeSetStatus
    version: int
    base_published_change_set_id: UUID | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    operation_order: int | None = None

    def published(self, at: datetime) -> "TransportChangeSet":
        return TransportChangeSet(
            id=self.id,
            name=self.name,
            status=TransportChangeSetStatus.PUBLISHED,
            version=self.version + 1,
            base_published_change_set_id=self.base_published_change_set_id,
            created_at=self.created_at,
            updated_at=at,
            expires_at=self.expires_at,
        )


@dataclass(frozen=True, slots=True)
class TransportWarning:
    code: str
    message: str
