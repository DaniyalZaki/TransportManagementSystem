import asyncio
from datetime import UTC, date, datetime, time
from time import perf_counter

from src.modules.transport_data.application.services import PublicTransportService
from src.modules.transport_data.domain.schedule import (
    Assignment,
    PublishedTransportSnapshot,
    Route,
    WeeklyDeparture,
)


class SnapshotRepository:
    def __init__(self, snapshot: PublishedTransportSnapshot) -> None:
        self.snapshot = snapshot

    async def get_current(self) -> PublishedTransportSnapshot:
        return self.snapshot


def _baseline_snapshot() -> PublishedTransportSnapshot:
    routes = tuple(
        Route(f"R-{route:02d}", "Campus", f"Stop {route}", "RETURN")
        for route in range(2_000)
    )
    assignments = tuple(
        Assignment(f"R-{route:02d}", f"B-{route:02d}")
        for route in range(2_000)
    )
    # One row per route yields the required 2,000 scheduled departure instances.
    weekly_departures = tuple(
        WeeklyDeparture(3, time(8, route % 60), f"R-{route:02d}")
        for route in range(2_000)
    )
    return PublishedTransportSnapshot(
        published_at=datetime(2026, 11, 24, 8, tzinfo=UTC),
        routes=routes,
        assignments=assignments,
        weekly_departures=weekly_departures,
        overrides=(),
    )


def test_baseline_read_workload_resolves_2000_departures_for_500_readers_within_target() -> None:
    """Fast deterministic guard; live publish-to-visible evidence is recorded separately."""
    service = PublicTransportService(SnapshotRepository(_baseline_snapshot()))
    service_date = date(2026, 11, 18)  # Wednesday: ISO weekday 3.
    now = datetime(2026, 11, 18, 7, 30, tzinfo=UTC)

    async def read() -> int:
        _, departures = await service.current_departures(service_date, now)
        return len(departures)

    async def batch() -> list[int]:
        return await asyncio.gather(*(read() for _ in range(500)))

    started = perf_counter()
    counts = asyncio.run(batch())
    elapsed = perf_counter() - started

    assert counts == [2_000] * 500
    assert elapsed < 5.0
