from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Request, status

from src.infrastructure.configuration.settings import Settings
from src.modules.transport_data.application.services import PublicTransportService
from src.modules.transport_data.domain.schedule import PKT, pkt_service_date
from src.modules.transport_data.infrastructure.published_snapshot_repository import (
    PostgresPublishedSnapshotRepository,
)


router = APIRouter(prefix="/api/v1/public/transport", tags=["public transport"])


def _service(request: Request) -> PublicTransportService:
    application = getattr(request, "app", request)
    repository = getattr(application.state, "transport_snapshot_repository", None)
    if repository is None:
        repository = PostgresPublishedSnapshotRepository(Settings().database_url)
    return PublicTransportService(repository)


@router.get("/current-departures")
async def get_current_departures(
    request: Request,
    service_date: date | None = None,
) -> dict[str, object]:
    application = getattr(request, "app", request)
    clock = getattr(application.state, "transport_clock", lambda: datetime.now(PKT))
    current_time = clock()
    requested_date = service_date or pkt_service_date(current_time)
    result = await _service(request).current_departures(requested_date, current_time)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Published transport information is unavailable",
        )
    published_at, departures = result
    return {
        "service_date": requested_date.isoformat(),
        "published_at": published_at.isoformat(),
        "departures": [
            {
                "route_id": departure.route.route_code,
                "bus_identifier": departure.bus_identifier,
                "status": departure.status,
                "scheduled_departure_at": (
                    departure.scheduled_departure_at.isoformat()
                    if departure.scheduled_departure_at
                    else None
                ),
            }
            for departure in departures
        ],
    }


@router.get("/schedule")
async def get_schedule(
    request: Request,
    service_date: date | None = None,
) -> dict[str, object]:
    requested_date = service_date or pkt_service_date(datetime.now(PKT))
    result = await _service(request).schedule(requested_date)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Published transport information is unavailable",
        )
    published_at, entries = result
    return {
        "service_date": requested_date.isoformat(),
        "service_status": "operating" if entries else "no_service",
        "published_at": published_at.isoformat(),
        "entries": [
            {
                "route_id": entry.route.route_code,
                "origin": entry.route.origin,
                "destination": entry.route.destination,
                "direction": entry.route.direction,
                "bus_identifiers": list(entry.bus_identifiers),
                "scheduled_departure_at": entry.scheduled_departure_at.isoformat(),
            }
            for entry in entries
        ],
    }
