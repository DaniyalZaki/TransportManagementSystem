from datetime import date, datetime

from src.modules.transport_data.application.ports import PublishedSnapshotRepository
from src.modules.transport_data.domain.schedule import (
    CurrentDeparture,
    ScheduledDeparture,
    current_departures,
    daily_schedule,
)


class PublicTransportService:
    """Public transport reads; only a published snapshot can enter this service."""

    def __init__(self, snapshots: PublishedSnapshotRepository) -> None:
        self._snapshots = snapshots

    async def current_departures(
        self, service_date: date, now: datetime
    ) -> tuple[datetime, tuple[CurrentDeparture, ...]] | None:
        snapshot = await self._snapshots.get_current()
        if snapshot is None:
            return None
        return snapshot.published_at, current_departures(snapshot, service_date, now)

    async def schedule(
        self, service_date: date
    ) -> tuple[datetime, tuple[ScheduledDeparture, ...]] | None:
        snapshot = await self._snapshots.get_current()
        if snapshot is None:
            return None
        return snapshot.published_at, daily_schedule(snapshot, service_date)
