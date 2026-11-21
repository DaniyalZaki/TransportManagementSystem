"""Raw PostgreSQL persistence for Transport Data's named change sets."""
# flake8: noqa: E501

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.infrastructure.database.connection import open_connection
from src.modules.transport_data.application.services import ChangeSetConflict
from src.modules.transport_data.domain.change_sets import (
    DraftTransportSnapshot,
    TransportChangeSet,
    TransportChangeSetStatus,
)
from src.modules.transport_data.domain.schedule import (
    Assignment, DepartureOverride, OverrideOperation, Route, WeeklyDeparture,
)


class PostgresChangeSetRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    async def current_published(self) -> TransportChangeSet | None:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow(
                """SELECT cs.* FROM published_change_sets pointer
                JOIN transport_change_sets cs ON cs.id = pointer.change_set_id
                WHERE pointer.is_current = TRUE"""
            )
        return self._to_change_set(row) if row else None

    async def get(self, change_set_id: UUID) -> TransportChangeSet | None:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow(
                "SELECT * FROM transport_change_sets WHERE id = $1", change_set_id
            )
        return self._to_change_set(row) if row else None

    async def expire_drafts(self, now: datetime) -> int:
        """Lifecycle job entry point; expired drafts are never publishable."""
        async with open_connection(self._database_url) as connection:
            result = await connection.execute(
                """UPDATE transport_change_sets
                SET status = 'expired', updated_at = $1
                WHERE status = 'draft' AND expires_at <= $1""",
                now,
            )
        return int(result.rsplit(" ", 1)[-1])

    async def delete_retired(self, now: datetime) -> int:
        """Physically remove retired published snapshots only after 30 days."""
        async with open_connection(self._database_url) as connection:
            async with connection.transaction():
                retired = await connection.fetch(
                    """SELECT id FROM transport_change_sets
                    WHERE status = 'retired' AND retired_at <= $1 - interval '30 days'
                    FOR UPDATE""", now,
                )
                ids = [row["id"] for row in retired]
                if not ids:
                    return 0
                await connection.execute(
                    "DELETE FROM published_change_sets WHERE change_set_id = ANY($1::uuid[])", ids
                )
                for change_set_id in ids:
                    await self._delete_snapshot(connection, change_set_id)
                result = await connection.execute(
                    "DELETE FROM transport_change_sets WHERE id = ANY($1::uuid[])", ids
                )
        return int(result.rsplit(" ", 1)[-1])

    async def snapshot(self, change_set_id: UUID) -> DraftTransportSnapshot:
        async with open_connection(self._database_url) as connection:
            routes = await connection.fetch("SELECT route_code, origin, destination, direction FROM transport_routes WHERE change_set_id = $1", change_set_id)
            buses = await connection.fetch("SELECT bus_identifier FROM transport_buses WHERE change_set_id = $1", change_set_id)
            assignments = await connection.fetch("SELECT route_code, bus_identifier FROM transport_assignments WHERE change_set_id = $1", change_set_id)
            departures = await connection.fetch("SELECT weekday, local_departure_time, route_code, bus_identifier FROM transport_weekly_departures WHERE change_set_id = $1", change_set_id)
            overrides = await connection.fetch("SELECT service_date, is_full_day_no_service, operation, route_code, bus_identifier, local_departure_time FROM transport_date_overrides WHERE change_set_id = $1", change_set_id)
        return DraftTransportSnapshot(
            routes=tuple(Route(row["route_code"], row["origin"], row["destination"], row["direction"]) for row in routes),
            buses=tuple(row["bus_identifier"] for row in buses),
            assignments=tuple(Assignment(row["route_code"], row["bus_identifier"]) for row in assignments),
            weekly_departures=tuple(WeeklyDeparture(row["weekday"], row["local_departure_time"], row["route_code"], row["bus_identifier"]) for row in departures),
            overrides=tuple(DepartureOverride(row["service_date"], row["is_full_day_no_service"], OverrideOperation(row["operation"]) if row["operation"] else None, row["route_code"], row["bus_identifier"], row["local_departure_time"]) for row in overrides),
        )

    async def create(self, change_set: TransportChangeSet, snapshot: DraftTransportSnapshot) -> TransportChangeSet:
        async with open_connection(self._database_url) as connection:
            try:
                async with connection.transaction():
                    await connection.execute(
                        """INSERT INTO transport_change_sets
                        (id, name, status, version, base_published_change_set_id, created_at, updated_at, expires_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                        change_set.id, change_set.name, change_set.status.value, change_set.version,
                        change_set.base_published_change_set_id, change_set.created_at,
                        change_set.updated_at, change_set.expires_at,
                    )
                    await self._insert_snapshot(connection, change_set.id, snapshot, "draft", 1)
            except Exception as error:
                if getattr(error, "sqlstate", None) == "23505":
                    raise ValueError("duplicate change-set name") from error
                raise
        return change_set

    async def publish(self, change_set_id: UUID, expected_base_id: UUID | None, publisher: str, published_at: datetime, audit) -> TransportChangeSet:
        async with open_connection(self._database_url) as connection:
            async with connection.transaction():
                draft_row = await connection.fetchrow("SELECT * FROM transport_change_sets WHERE id = $1 FOR UPDATE", change_set_id)
                if draft_row is None:
                    raise ChangeSetConflict("Change set does not exist")
                pointer = await connection.fetchrow("SELECT change_set_id FROM published_change_sets WHERE is_current = TRUE FOR UPDATE")
                current_id = pointer["change_set_id"] if pointer else None
                if draft_row["base_published_change_set_id"] != current_id or expected_base_id != current_id:
                    raise ChangeSetConflict("stale_change_set: rebase before publishing")
                if pointer:
                    await connection.execute("UPDATE published_change_sets SET is_current = FALSE WHERE is_current = TRUE")
                    await connection.execute("UPDATE transport_change_sets SET status = 'retired', retired_at = $1 WHERE id = $2", published_at, current_id)
                await connection.execute("UPDATE transport_change_sets SET status = 'published', version = version + 1, updated_at = $1 WHERE id = $2", published_at, change_set_id)
                for table in ("transport_routes", "transport_buses", "transport_assignments", "transport_weekly_departures", "transport_date_overrides"):
                    await connection.execute(f"UPDATE {table} SET status = 'published', version = version + 1 WHERE change_set_id = $1", change_set_id)
                await connection.execute("INSERT INTO published_change_sets (change_set_id, published_at, is_current) VALUES ($1, $2, TRUE) ON CONFLICT (change_set_id) DO UPDATE SET published_at = EXCLUDED.published_at, is_current = TRUE", change_set_id, published_at)
                await audit.record_publication(change_set_id, publisher, published_at, connection)
                row = await connection.fetchrow("SELECT * FROM transport_change_sets WHERE id = $1", change_set_id)
        return self._to_change_set(row)

    async def replace_snapshot(self, change_set_id: UUID, expected_version: int, snapshot: DraftTransportSnapshot, updated_at: datetime) -> TransportChangeSet:
        async with open_connection(self._database_url) as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    "SELECT * FROM transport_change_sets WHERE id = $1 FOR UPDATE", change_set_id
                )
                if row is None or row["status"] != "draft":
                    raise ChangeSetConflict("Only an active draft can be updated")
                if row["version"] != expected_version:
                    raise ChangeSetConflict("stale_change_set: reload before saving")
                await self._delete_snapshot(connection, change_set_id)
                await self._insert_snapshot(connection, change_set_id, snapshot, "draft", 1)
                row = await connection.fetchrow(
                    """UPDATE transport_change_sets SET version = version + 1, updated_at = $1
                    WHERE id = $2 RETURNING *""", updated_at, change_set_id
                )
        return self._to_change_set(row)

    async def recover(self, source_change_set_id: UUID, publisher: str, recovered_at: datetime, audit) -> TransportChangeSet:
        async with open_connection(self._database_url) as connection:
            async with connection.transaction():
                source = await connection.fetchrow(
                    "SELECT * FROM transport_change_sets WHERE id = $1 FOR UPDATE", source_change_set_id
                )
                if source is None or source["status"] not in {"published", "retired"}:
                    raise ChangeSetConflict("Only a previously published change set can recover")
                snapshot = await self._snapshot_with_connection(connection, source_change_set_id)
                pointer = await connection.fetchrow(
                    "SELECT change_set_id FROM published_change_sets WHERE is_current = TRUE FOR UPDATE"
                )
                if pointer:
                    await connection.execute("UPDATE published_change_sets SET is_current = FALSE WHERE is_current = TRUE")
                    await connection.execute("UPDATE transport_change_sets SET status = 'retired', retired_at = $1 WHERE id = $2", recovered_at, pointer["change_set_id"])
                recovered_id = uuid4()
                row = await connection.fetchrow(
                    """INSERT INTO transport_change_sets
                    (id, name, status, version, base_published_change_set_id, created_at, updated_at, expires_at)
                    VALUES ($1, $2, 'published', 1, $3, $4, $4, $5) RETURNING *""",
                    recovered_id, f"Recovery of {source['name']} ({recovered_at.isoformat()})",
                    pointer["change_set_id"] if pointer else None, recovered_at,
                    recovered_at + timedelta(days=30),
                )
                await self._insert_snapshot(connection, recovered_id, snapshot, "published", 1)
                await connection.execute("INSERT INTO published_change_sets (change_set_id, published_at, is_current) VALUES ($1, $2, TRUE)", recovered_id, recovered_at)
                await audit.record_publication(recovered_id, publisher, recovered_at, connection)
        return self._to_change_set(row)

    async def rebase(
        self, change_set_id: UUID, base_change_set_id: UUID | None,
        snapshot: DraftTransportSnapshot, rebased_at: datetime,
    ) -> TransportChangeSet:
        async with open_connection(self._database_url) as connection:
            async with connection.transaction():
                await self._delete_snapshot(connection, change_set_id)
                await self._insert_snapshot(connection, change_set_id, snapshot, "draft", 1)
                row = await connection.fetchrow(
                    """UPDATE transport_change_sets
                    SET base_published_change_set_id = $1, version = version + 1,
                        updated_at = $2
                    WHERE id = $3 AND status = 'draft'
                    RETURNING *""",
                    base_change_set_id, rebased_at, change_set_id,
                )
        if row is None:
            raise ChangeSetConflict("Only an active draft can be rebased")
        return self._to_change_set(row)

    @staticmethod
    async def _insert_snapshot(connection, change_set_id: UUID, snapshot: DraftTransportSnapshot, status: str, version: int) -> None:
        for route in snapshot.routes:
            await connection.execute("INSERT INTO transport_routes (id, change_set_id, route_code, origin, destination, direction, status, version) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)", change_set_id, route.route_code, route.origin, route.destination, route.direction, status, version)
        for bus in snapshot.buses:
            await connection.execute("INSERT INTO transport_buses (id, change_set_id, bus_identifier, status, version) VALUES (gen_random_uuid(), $1, $2, $3, $4)", change_set_id, bus, status, version)
        for assignment in snapshot.assignments:
            await connection.execute("INSERT INTO transport_assignments (id, change_set_id, route_code, bus_identifier, status, version) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)", change_set_id, assignment.route_code, assignment.bus_identifier, status, version)
        for departure in snapshot.weekly_departures:
            await connection.execute("INSERT INTO transport_weekly_departures (id, change_set_id, weekday, local_departure_time, route_code, bus_identifier, status, version) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)", change_set_id, departure.weekday, departure.departure_time, departure.route_code, departure.bus_identifier, status, version)
        for override in snapshot.overrides:
            await connection.execute("INSERT INTO transport_date_overrides (id, change_set_id, service_date, is_full_day_no_service, operation, route_code, bus_identifier, local_departure_time, status, version) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9)", change_set_id, override.service_date, override.is_full_day_no_service, override.operation.value if override.operation else None, override.route_code, override.bus_identifier, override.departure_time, status, version)

    @staticmethod
    async def _delete_snapshot(connection, change_set_id: UUID) -> None:
        for table in ("transport_date_overrides", "transport_weekly_departures", "transport_assignments", "transport_buses", "transport_routes"):
            await connection.execute(f"DELETE FROM {table} WHERE change_set_id = $1", change_set_id)

    @staticmethod
    async def _snapshot_with_connection(connection, change_set_id: UUID) -> DraftTransportSnapshot:
        routes = await connection.fetch("SELECT route_code, origin, destination, direction FROM transport_routes WHERE change_set_id = $1", change_set_id)
        buses = await connection.fetch("SELECT bus_identifier FROM transport_buses WHERE change_set_id = $1", change_set_id)
        assignments = await connection.fetch("SELECT route_code, bus_identifier FROM transport_assignments WHERE change_set_id = $1", change_set_id)
        departures = await connection.fetch("SELECT weekday, local_departure_time, route_code, bus_identifier FROM transport_weekly_departures WHERE change_set_id = $1", change_set_id)
        overrides = await connection.fetch("SELECT service_date, is_full_day_no_service, operation, route_code, bus_identifier, local_departure_time FROM transport_date_overrides WHERE change_set_id = $1", change_set_id)
        return DraftTransportSnapshot(
            routes=tuple(Route(row["route_code"], row["origin"], row["destination"], row["direction"]) for row in routes), buses=tuple(row["bus_identifier"] for row in buses), assignments=tuple(Assignment(row["route_code"], row["bus_identifier"]) for row in assignments), weekly_departures=tuple(WeeklyDeparture(row["weekday"], row["local_departure_time"], row["route_code"], row["bus_identifier"]) for row in departures), overrides=tuple(DepartureOverride(row["service_date"], row["is_full_day_no_service"], OverrideOperation(row["operation"]) if row["operation"] else None, row["route_code"], row["bus_identifier"], row["local_departure_time"]) for row in overrides),
        )

    @staticmethod
    def _to_change_set(row) -> TransportChangeSet:
        return TransportChangeSet(UUID(str(row["id"])), row["name"], TransportChangeSetStatus(row["status"]), row["version"], row["base_published_change_set_id"], row["created_at"], row["updated_at"], row["expires_at"])
