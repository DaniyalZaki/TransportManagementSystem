"""Raw PostgreSQL reader for the current published transport snapshot."""

from datetime import datetime

from src.infrastructure.database.connection import open_connection
from src.modules.transport_data.domain.schedule import (
    Assignment,
    DepartureOverride,
    OverrideOperation,
    PublishedTransportSnapshot,
    Route,
    WeeklyDeparture,
)


class PostgresPublishedSnapshotRepository:
    """Read published Transport Data rows only; drafts are never queried here."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    async def get_current(self) -> PublishedTransportSnapshot | None:
        async with open_connection(self._database_url) as connection:
            pointer = await connection.fetchrow(
                """
                SELECT change_set_id, published_at
                FROM published_change_sets
                WHERE is_current = TRUE
                """
            )
            if pointer is None:
                return None
            change_set_id = pointer["change_set_id"]
            routes = await connection.fetch(
                """
                SELECT route_code, origin, destination, direction
                FROM transport_routes
                WHERE change_set_id = $1 AND status = 'published'
                """,
                change_set_id,
            )
            assignments = await connection.fetch(
                """
                SELECT route_code, bus_identifier
                FROM transport_assignments
                WHERE change_set_id = $1 AND status = 'published'
                """,
                change_set_id,
            )
            departures = await connection.fetch(
                """
                SELECT DISTINCT weekday, local_departure_time, route_code
                FROM transport_weekly_departures
                WHERE change_set_id = $1 AND status = 'published'
                """,
                change_set_id,
            )
            overrides = await connection.fetch(
                """
                SELECT service_date, is_full_day_no_service, operation,
                       route_code, bus_identifier, local_departure_time
                FROM transport_date_overrides
                WHERE change_set_id = $1 AND status = 'published'
                """,
                change_set_id,
            )
        return PublishedTransportSnapshot(
            published_at=_as_datetime(pointer["published_at"]),
            routes=tuple(
                Route(row["route_code"], row["origin"], row["destination"], row["direction"])
                for row in routes
            ),
            assignments=tuple(
                Assignment(row["route_code"], row["bus_identifier"])
                for row in assignments
            ),
            weekly_departures=tuple(
                WeeklyDeparture(
                    weekday=row["weekday"],
                    departure_time=row["local_departure_time"],
                    route_code=row["route_code"],
                )
                for row in departures
            ),
            overrides=tuple(
                DepartureOverride(
                    service_date=row["service_date"],
                    is_full_day_no_service=row["is_full_day_no_service"],
                    operation=(
                        OverrideOperation(row["operation"])
                        if row["operation"] is not None
                        else None
                    ),
                    route_code=row["route_code"],
                    bus_identifier=row["bus_identifier"],
                    departure_time=row["local_departure_time"],
                )
                for row in overrides
            ),
        )


def _as_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("Database published_at must be a datetime")
    return value
