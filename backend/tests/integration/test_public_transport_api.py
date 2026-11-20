import asyncio
from datetime import UTC, date, datetime, time

from src.application.main import create_app
from src.modules.transport_data.domain.schedule import (
    Assignment,
    PublishedTransportSnapshot,
    Route,
    WeeklyDeparture,
)


class PublishedSnapshotRepository:
    async def get_current(self) -> PublishedTransportSnapshot:
        return PublishedTransportSnapshot(
            published_at=datetime(2026, 11, 20, 8, tzinfo=UTC),
            routes=(Route("R-01", "Lahore", "Campus", "Inbound"),),
            assignments=(Assignment("R-01", "C-12"),),
            weekly_departures=(
                WeeklyDeparture(2, time(14), "R-01", "C-12"),
            ),
            overrides=(),
        )


def _endpoint(app, path: str):
    return next(route.endpoint for route in app.routes if route.path == path)


def test_public_transport_endpoints_are_documented_without_authentication() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v1/public/transport/current-departures" in paths
    assert "/api/v1/public/transport/schedule" in paths
    assert "security" not in paths["/api/v1/public/transport/current-departures"]["get"]
    assert "security" not in paths["/api/v1/public/transport/schedule"]["get"]


def test_public_schedule_and_current_departures_use_only_the_injected_published_snapshot() -> None:
    app = create_app()
    app.state.transport_snapshot_repository = PublishedSnapshotRepository()
    app.state.transport_clock = lambda: datetime(2026, 11, 18, 8, tzinfo=UTC)
    current = _endpoint(app, "/api/v1/public/transport/current-departures")
    schedule = _endpoint(app, "/api/v1/public/transport/schedule")

    current_response = asyncio.run(current(service_date=date(2026, 11, 18), request=app))
    schedule_response = asyncio.run(schedule(service_date=date(2026, 11, 18), request=app))

    assert current_response["departures"] == [
        {
            "route_id": "R-01",
            "bus_identifier": "C-12",
            "status": "scheduled",
            "scheduled_departure_at": "2026-11-18T14:00:00+05:00",
        }
    ]
    assert schedule_response["service_status"] == "operating"
    assert schedule_response["entries"][0]["origin"] == "Lahore"
    assert schedule_response["entries"][0]["bus_identifier"] == "C-12"
