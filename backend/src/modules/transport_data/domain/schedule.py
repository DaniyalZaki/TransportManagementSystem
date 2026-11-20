"""Published schedule resolution and PKT current-departure calculation."""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo


PKT = ZoneInfo("Asia/Karachi")


@dataclass(frozen=True, slots=True)
class Route:
    route_code: str
    origin: str
    destination: str
    direction: str


@dataclass(frozen=True, slots=True)
class Assignment:
    route_code: str
    bus_identifier: str


@dataclass(frozen=True, slots=True)
class WeeklyDeparture:
    weekday: int
    departure_time: time
    route_code: str
    bus_identifier: str


class OverrideOperation(StrEnum):
    ADD = "add"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class DepartureOverride:
    service_date: date
    is_full_day_no_service: bool = False
    operation: OverrideOperation | None = None
    route_code: str | None = None
    bus_identifier: str | None = None
    departure_time: time | None = None

    @classmethod
    def full_day_no_service(cls, service_date: date) -> "DepartureOverride":
        return cls(service_date=service_date, is_full_day_no_service=True)

    @classmethod
    def add(
        cls,
        service_date: date,
        route_code: str,
        bus_identifier: str,
        departure_time: time,
    ) -> "DepartureOverride":
        return cls(
            service_date=service_date,
            operation=OverrideOperation.ADD,
            route_code=route_code,
            bus_identifier=bus_identifier,
            departure_time=departure_time,
        )

    @classmethod
    def remove(
        cls,
        service_date: date,
        route_code: str,
        bus_identifier: str,
        departure_time: time,
    ) -> "DepartureOverride":
        return cls(
            service_date=service_date,
            operation=OverrideOperation.REMOVE,
            route_code=route_code,
            bus_identifier=bus_identifier,
            departure_time=departure_time,
        )


@dataclass(frozen=True, slots=True)
class PublishedTransportSnapshot:
    published_at: datetime
    routes: tuple[Route, ...]
    assignments: tuple[Assignment, ...]
    weekly_departures: tuple[WeeklyDeparture, ...]
    overrides: tuple[DepartureOverride, ...]


@dataclass(frozen=True, slots=True)
class ScheduledDeparture:
    route: Route
    bus_identifier: str
    scheduled_departure_at: datetime


@dataclass(frozen=True, slots=True)
class CurrentDeparture:
    route: Route
    bus_identifier: str
    status: str
    scheduled_departure_at: datetime | None


def pkt_service_date(instant: datetime) -> date:
    """Return the service date for an instant, always in Pakistan Standard Time."""
    if instant.tzinfo is None:
        raise ValueError("A timezone-aware instant is required")
    return instant.astimezone(PKT).date()


def daily_schedule(
    snapshot: PublishedTransportSnapshot,
    service_date: date,
) -> tuple[ScheduledDeparture, ...]:
    """Resolve weekly service plus full-day and partial date overrides."""
    relevant_overrides = tuple(
        override for override in snapshot.overrides if override.service_date == service_date
    )
    if any(override.is_full_day_no_service for override in relevant_overrides):
        return ()

    entries = {
        (departure.route_code, departure.bus_identifier, departure.departure_time)
        for departure in snapshot.weekly_departures
        if departure.weekday == service_date.weekday()
    }
    for override in relevant_overrides:
        if override.operation is None:
            continue
        key = _override_key(override)
        if override.operation is OverrideOperation.REMOVE:
            entries.discard(key)
        elif override.operation is OverrideOperation.ADD:
            entries.add(key)

    routes = {route.route_code: route for route in snapshot.routes}
    return tuple(
        ScheduledDeparture(
            route=routes[route_code],
            bus_identifier=bus_identifier,
            scheduled_departure_at=datetime.combine(service_date, departure_time, PKT),
        )
        for route_code, bus_identifier, departure_time in sorted(
            entries, key=lambda entry: (entry[2], entry[0], entry[1])
        )
        if route_code in routes
    )


def current_departures(
    snapshot: PublishedTransportSnapshot,
    service_date: date,
    now: datetime,
) -> tuple[CurrentDeparture, ...]:
    """Find one next upcoming departure, or an exhausted state, per assignment."""
    if now.tzinfo is None:
        raise ValueError("A timezone-aware instant is required")
    now_pkt = now.astimezone(PKT)
    scheduled = daily_schedule(snapshot, service_date)
    routes = {route.route_code: route for route in snapshot.routes}
    results: list[CurrentDeparture] = []
    for assignment in sorted(
        snapshot.assignments, key=lambda item: (item.route_code, item.bus_identifier)
    ):
        route = routes.get(assignment.route_code)
        if route is None:
            continue
        next_entry = next(
            (
                entry
                for entry in scheduled
                if entry.route.route_code == assignment.route_code
                and entry.bus_identifier == assignment.bus_identifier
                and entry.scheduled_departure_at >= now_pkt
            ),
            None,
        )
        results.append(
            CurrentDeparture(
                route=route,
                bus_identifier=assignment.bus_identifier,
                status="scheduled" if next_entry else "no_further_departures_today",
                scheduled_departure_at=(
                    next_entry.scheduled_departure_at if next_entry else None
                ),
            )
        )
    return tuple(results)


def _override_key(override: DepartureOverride) -> tuple[str, str, time]:
    if not (
        override.route_code
        and override.bus_identifier
        and override.departure_time is not None
    ):
        raise ValueError("Partial overrides require route, bus, and departure time")
    return override.route_code, override.bus_identifier, override.departure_time
