from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from src.modules.transport_data.domain.schedule import (
    Assignment,
    DepartureOverride,
    PublishedTransportSnapshot,
    Route,
    WeeklyDeparture,
    current_departures,
    daily_schedule,
    pkt_service_date,
)


ROUTE = Route("R-01", "Lahore", "Campus", "Inbound")
ASSIGNMENT = Assignment("R-01", "C-12")
PKT = ZoneInfo("Asia/Karachi")


def snapshot(*, overrides: tuple[DepartureOverride, ...] = ()) -> PublishedTransportSnapshot:
    return PublishedTransportSnapshot(
        published_at=datetime(2026, 11, 20, 8, tzinfo=UTC),
        routes=(ROUTE,),
        assignments=(ASSIGNMENT,),
        weekly_departures=(
            WeeklyDeparture(3, time(8), "R-01"),
            WeeklyDeparture(3, time(14), "R-01"),
        ),
        overrides=overrides,
    )


def test_pkt_service_date_uses_pakistan_timezone_not_server_timezone() -> None:
    assert pkt_service_date(datetime(2026, 11, 17, 19, 30, tzinfo=UTC)) == date(2026, 11, 18)


def test_daily_schedule_uses_weekly_departures_for_service_weekday() -> None:
    entries = daily_schedule(snapshot(), date(2026, 11, 18))

    assert [entry.scheduled_departure_at.isoformat() for entry in entries] == [
        "2026-11-18T08:00:00+05:00",
        "2026-11-18T14:00:00+05:00",
    ]
    assert entries[0].route == ROUTE
    assert entries[0].bus_identifiers == ("C-12",)


def test_route_schedule_expands_to_every_assigned_bus() -> None:
    many_buses = PublishedTransportSnapshot(
        published_at=datetime(2026, 11, 20, 8, tzinfo=UTC),
        routes=(ROUTE,),
        assignments=(ASSIGNMENT, Assignment("R-01", "C-13")),
        weekly_departures=(WeeklyDeparture(3, time(8), "R-01"),),
        overrides=(),
    )

    assert daily_schedule(many_buses, date(2026, 11, 18))[0].bus_identifiers == (
        "C-12", "C-13"
    )


def test_full_day_no_service_override_suppresses_weekly_schedule() -> None:
    entries = daily_schedule(
        snapshot(overrides=(DepartureOverride.full_day_no_service(date(2026, 11, 18)),)),
        date(2026, 11, 18),
    )

    assert entries == ()


def test_partial_overrides_remove_and_add_exact_route_bus_time_matches() -> None:
    entries = daily_schedule(
        snapshot(
            overrides=(
                DepartureOverride.remove(date(2026, 11, 18), "R-01", "C-12", time(8)),
                DepartureOverride.add(date(2026, 11, 18), "R-01", "C-12", time(9, 30)),
            )
        ),
        date(2026, 11, 18),
    )

    assert [entry.scheduled_departure_at.time() for entry in entries] == [time(9, 30), time(14)]


def test_current_departure_selects_equal_time_and_then_no_further_departures() -> None:
    service_date = date(2026, 11, 18)
    at_eight = current_departures(snapshot(), service_date, datetime(2026, 11, 18, 8, tzinfo=PKT))
    after_final = current_departures(
        snapshot(), service_date, datetime(2026, 11, 18, 15, tzinfo=PKT)
    )

    assert at_eight[0].scheduled_departure_at.time() == time(8)
    assert after_final[0].status == "no_further_departures_today"
    assert after_final[0].scheduled_departure_at is None


def test_current_departures_include_assignment_without_a_timetable_entry() -> None:
    empty_snapshot = PublishedTransportSnapshot(
        published_at=datetime(2026, 11, 20, 8, tzinfo=UTC),
        routes=(ROUTE,),
        assignments=(ASSIGNMENT,),
        weekly_departures=(),
        overrides=(),
    )

    result = current_departures(
        empty_snapshot,
        date(2026, 11, 18),
        datetime(2026, 11, 18, 8, tzinfo=PKT),
    )

    assert result[0].status == "no_further_departures_today"
