import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from typing import ClassVar
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

    def __init__(self, message: str, operation_order: int | None = None) -> None:
        super().__init__(message)
        self.operation_order = operation_order


class PublishConfirmationRequired(ValueError):
    def __init__(self, warnings: tuple[TransportWarning, ...]) -> None:
        super().__init__("publish_anyway confirmation is required for schedule warnings")
        self.warnings = warnings


@dataclass(frozen=True, slots=True)
class PublicationResult:
    draft: TransportChangeSet
    published_change_set_id: object
    published_at: datetime


@dataclass(frozen=True, slots=True)
class SerializedDraftResult:
    draft: TransportChangeSet


class TransportChangeSetService:
    """Transport Data's draft, validation, and publish workflow.

    The persistence adapter is responsible for the database transaction which
    moves the pointer. The service deliberately invalidates cache only after a
    successful transaction and only after Audit has recorded publication.
    """

    _mutation_lock: ClassVar[asyncio.Lock | None] = None
    _next_operation_order: ClassVar[int] = 1

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

    async def open_draft(self, principal: Principal | None = None) -> TransportChangeSet:
        self._require_privileged(principal)
        existing = await self._change_sets.working_draft()
        if existing is not None:
            return existing
        current = await self._change_sets.current_published()
        if current is None:
            snapshot = DraftTransportSnapshot((), (), (), (), ())
            base_id = None
        else:
            snapshot = await self._change_sets.snapshot(current.id)
            base_id = current.id
        now = self._clock()
        draft = TransportChangeSet(
            id=uuid4(), name="Working draft", status=TransportChangeSetStatus.DRAFT,
            version=1, base_published_change_set_id=base_id, created_at=now,
            updated_at=now, expires_at=datetime.max.replace(tzinfo=UTC),
        )
        try:
            return await self._change_sets.create(draft, snapshot)
        except Exception as error:
            if "unique" in str(error).lower() or "duplicate" in str(error).lower():
                # A concurrent Open Draft won the race; return that one.
                existing = await self._change_sets.working_draft()
                if existing is not None:
                    return existing
                raise ChangeSetConflict("Unable to initialize the working draft") from error
            raise

    async def expire_drafts(self) -> int:
        """The permanent working draft is deliberately exempt from expiry."""
        return 0

    async def delete_retired(self) -> int:
        return await self._change_sets.delete_retired(self._clock())

    async def validate(self, change_set_id) -> tuple[TransportWarning, ...]:
        change_set = await self._required_draft(change_set_id)
        snapshot = await self._change_sets.snapshot(change_set.id)
        scheduled_routes = {item.route_code for item in snapshot.weekly_departures}
        warnings: list[TransportWarning] = []
        for route in snapshot.routes:
            if route.route_code not in scheduled_routes:
                warnings.append(TransportWarning(
                    "missing_schedule",
                    f"{route.route_code} has no recurring schedule entry",
                ))
        return tuple(warnings)

    async def publish(
        self, change_set_id, publish_anyway: bool, publisher: str,
        principal: Principal | None = None,
    ) -> PublicationResult:
        self._require_privileged(principal)
        async with self._mutation_gate() as operation_order:
            try:
                await self._required_draft(change_set_id)
                warnings = await self.validate(change_set_id)
                if warnings and not publish_anyway:
                    raise PublishConfirmationRequired(warnings)
                published_at = self._clock()
                updated_draft, published_id = await self._change_sets.publish(
                    change_set_id, publisher, published_at, self._audit
                )
                self._cache.invalidate_published_transport()
                return PublicationResult(
                    replace(updated_draft, operation_order=operation_order),
                    published_id,
                    published_at,
                )
            except ChangeSetConflict as error:
                raise ChangeSetConflict(str(error), operation_order) from error

    async def replace_snapshot(
        self, change_set_id, expected_version: int, snapshot: DraftTransportSnapshot,
        principal: Principal | None = None,
    ) -> SerializedDraftResult:
        self._require_privileged(principal)
        async with self._mutation_gate() as operation_order:
            try:
                await self._required_draft(change_set_id)
                draft = await self._change_sets.replace_snapshot(
                    change_set_id, expected_version, snapshot, self._clock()
                )
                return SerializedDraftResult(
                    replace(draft, operation_order=operation_order)
                )
            except ChangeSetConflict as error:
                raise ChangeSetConflict(str(error), operation_order) from error

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
        return change_set

    @classmethod
    def _mutation_gate(cls):
        """Serialize save/publish operations in this approved single worker.

        The counter is intentionally process-local and only identifies the
        temporary order in which the working-draft mutation executed.
        """
        if cls._mutation_lock is None:
            cls._mutation_lock = asyncio.Lock()

        class _Gate:
            async def __aenter__(self_inner):
                await cls._mutation_lock.acquire()
                order = cls._next_operation_order
                cls._next_operation_order += 1
                return order

            async def __aexit__(self_inner, *_):
                cls._mutation_lock.release()

        return _Gate()

    @staticmethod
    def _require_privileged(principal: Principal | None) -> None:
        if principal is None:
            return
        if not principal.active or principal.role not in {
            Role.TRANSPORT_MANAGEMENT, Role.DESIGNATED_ADMINISTRATOR,
        }:
            raise PermissionError("A privileged transport role is required")
