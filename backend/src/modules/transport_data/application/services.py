from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from src.application.authorization.roles import Principal, Role
from src.modules.transport_data.application.change_set_ports import (
    ChangeSetRepository,
    PublicationAudit,
    PublishedTransportCache,
)
from src.modules.transport_data.application.ports import PublishedSnapshotRepository
from src.modules.transport_data.domain.change_sets import (
    DraftTransportSnapshot,
    TransportChangeSet,
    TransportChangeSetStatus,
    TransportWarning,
)
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


class ChangeSetConflict(ValueError):
    """A draft cannot be saved or published against its current baseline."""


class PublishConfirmationRequired(ValueError):
    def __init__(self, warnings: tuple[TransportWarning, ...]) -> None:
        super().__init__("publish_anyway confirmation is required for schedule warnings")
        self.warnings = warnings


class TransportChangeSetService:
    """Transport Data's draft, validation, and publish workflow.

    The persistence adapter is responsible for the database transaction which
    moves the pointer. The service deliberately invalidates cache only after a
    successful transaction and only after Audit has recorded publication.
    """

    def __init__(
        self,
        change_sets: ChangeSetRepository,
        audit: PublicationAudit,
        cache: PublishedTransportCache,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._change_sets = change_sets
        self._audit = audit
        self._cache = cache
        self._clock = clock

    async def create_draft(
        self, name: str, principal: Principal | None = None
    ) -> TransportChangeSet:
        self._require_privileged(principal)
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("A change-set name is required")
        current = await self._change_sets.current_published()
        if current is None:
            snapshot = DraftTransportSnapshot((), (), (), (), ())
            base_id = None
        else:
            snapshot = await self._change_sets.snapshot(current.id)
            base_id = current.id
        now = self._clock()
        draft = TransportChangeSet(
            id=uuid4(), name=normalized_name, status=TransportChangeSetStatus.DRAFT,
            version=1, base_published_change_set_id=base_id, created_at=now,
            updated_at=now, expires_at=now + timedelta(days=30),
        )
        try:
            return await self._change_sets.create(draft, snapshot)
        except Exception as error:
            if "unique" in str(error).lower() or "duplicate" in str(error).lower():
                raise ChangeSetConflict("A change set with this name already exists") from error
            raise

    async def expire_drafts(self) -> int:
        """Called by the single-worker lifecycle job before privileged operations."""
        return await self._change_sets.expire_drafts(self._clock())

    async def delete_retired(self) -> int:
        return await self._change_sets.delete_retired(self._clock())

    async def validate(self, change_set_id) -> tuple[TransportWarning, ...]:
        change_set = await self._required_draft(change_set_id)
        snapshot = await self._change_sets.snapshot(change_set.id)
        assignments = {(item.route_code, item.bus_identifier) for item in snapshot.assignments}
        warnings: list[TransportWarning] = []
        for departure in snapshot.weekly_departures:
            if (departure.route_code, departure.bus_identifier) not in assignments:
                warnings.append(TransportWarning(
                    "missing_assignment",
                    f"{departure.route_code} / {departure.bus_identifier} at "
                    f"{departure.departure_time.isoformat()} has no assignment",
                ))
        grouped: dict[tuple[int, str, object], set[str]] = {}
        for departure in snapshot.weekly_departures:
            grouped.setdefault(
                (departure.weekday, departure.route_code, departure.departure_time), set()
            ).add(departure.bus_identifier)
        for (weekday, route, departure_time), buses in grouped.items():
            if len(buses) > 1:
                warnings.append(TransportWarning(
                    "conflicting_assignment",
                    f"{route} has conflicting buses at weekday {weekday}, "
                    f"{departure_time.isoformat()}",
                ))
        return tuple(warnings)

    async def publish(
        self, change_set_id, expected_base_id, publish_anyway: bool, publisher: str,
        principal: Principal | None = None,
    ) -> TransportChangeSet:
        self._require_privileged(principal)
        draft = await self._required_draft(change_set_id)
        current = await self._change_sets.current_published()
        current_id = current.id if current else None
        if draft.base_published_change_set_id != current_id or expected_base_id != current_id:
            raise ChangeSetConflict("stale_change_set: rebase before publishing")
        warnings = await self.validate(change_set_id)
        if warnings and not publish_anyway:
            raise PublishConfirmationRequired(warnings)
        published_at = self._clock()
        published = await self._change_sets.publish(
            change_set_id, expected_base_id, publisher, published_at, self._audit
        )
        self._cache.invalidate_published_transport()
        return published

    async def replace_snapshot(
        self, change_set_id, expected_version: int, snapshot: DraftTransportSnapshot,
        principal: Principal | None = None,
    ) -> TransportChangeSet:
        self._require_privileged(principal)
        await self._required_draft(change_set_id)
        return await self._change_sets.replace_snapshot(
            change_set_id, expected_version, snapshot, self._clock()
        )

    async def get_draft(
        self, change_set_id, principal: Principal | None = None,
    ) -> tuple[TransportChangeSet, DraftTransportSnapshot]:
        self._require_privileged(principal)
        change_set = await self._required_draft(change_set_id)
        return change_set, await self._change_sets.snapshot(change_set_id)

    async def recover(
        self, source_change_set_id, publisher: str,
        principal: Principal | None = None,
    ) -> TransportChangeSet:
        """Restore an eligible published snapshot directly, never as a draft."""
        self._require_privileged(principal)
        if not await self._audit.is_recoverable(source_change_set_id, self._clock()):
            raise ChangeSetConflict(
                "Only a published change set retained within 30 days can recover"
            )
        recovered = await self._change_sets.recover(
            source_change_set_id, publisher, self._clock(), self._audit
        )
        self._cache.invalidate_published_transport()
        return recovered

    async def publication_history(
        self, principal: Principal | None = None,
    ) -> list[tuple[object, str, datetime]]:
        self._require_privileged(principal)
        return await self._audit.recent_publications(self._clock())

    async def rebase(
        self, change_set_id, principal: Principal | None = None
    ) -> TransportChangeSet:
        """Discard stale draft edits and start again from the current published set."""
        self._require_privileged(principal)
        draft = await self._required_draft(change_set_id)
        current = await self._change_sets.current_published()
        if current is None:
            raise ChangeSetConflict("No published transport baseline is available")
        snapshot = await self._change_sets.snapshot(current.id)
        return await self._change_sets.rebase(
            draft.id, current.id, snapshot, self._clock()
        )

    async def _required_draft(self, change_set_id) -> TransportChangeSet:
        change_set = await self._change_sets.get(change_set_id)
        if change_set is None:
            raise ChangeSetConflict("Change set does not exist")
        if change_set.status is not TransportChangeSetStatus.DRAFT:
            raise ChangeSetConflict("Only an active draft can be changed or published")
        if change_set.expires_at <= self._clock():
            raise ChangeSetConflict("Draft has expired")
        return change_set

    @staticmethod
    def _require_privileged(principal: Principal | None) -> None:
        if principal is None:
            return
        if not principal.active or principal.role not in {
            Role.TRANSPORT_MANAGEMENT, Role.DESIGNATED_ADMINISTRATOR,
        }:
            raise PermissionError("A privileged transport role is required")
