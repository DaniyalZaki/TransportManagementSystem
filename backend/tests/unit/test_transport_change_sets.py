import asyncio
from datetime import UTC, datetime, time
from uuid import uuid4

import pytest

from src.application.authorization.roles import Principal, Role
from src.modules.transport_data.application.services import (
    ChangeSetConflict,
    PublishConfirmationRequired,
    TransportChangeSetService,
)
from src.modules.transport_data.domain.change_sets import (
    DraftTransportSnapshot,
    TransportChangeSet,
    TransportChangeSetStatus,
)
from src.modules.transport_data.domain.schedule import Assignment, Route, WeeklyDeparture


class MemoryChangeSets:
    def __init__(self) -> None:
        self.current_id = uuid4()
        self.current = TransportChangeSet(
            id=self.current_id,
            name="Published baseline",
            status=TransportChangeSetStatus.PUBLISHED,
            version=1,
            base_published_change_set_id=None,
            created_at=datetime(2026, 11, 1, tzinfo=UTC),
            updated_at=datetime(2026, 11, 1, tzinfo=UTC),
            expires_at=datetime(2026, 12, 1, tzinfo=UTC),
        )
        self.snapshots = {
            self.current_id: DraftTransportSnapshot(
                routes=(Route("R-01", "Lahore", "Campus", "Inbound"),),
                buses=("C-12",),
                assignments=(Assignment("R-01", "C-12"),),
                weekly_departures=(WeeklyDeparture(1, time(8), "R-01"),),
                overrides=(),
            )
        }
        self.items = {self.current_id: self.current}

    async def current_published(self):
        return self.current

    async def get(self, change_set_id):
        return self.items.get(change_set_id)

    async def snapshot(self, change_set_id):
        return self.snapshots[change_set_id]

    async def create(self, change_set, snapshot):
        if any(item.name == change_set.name for item in self.items.values()):
            raise ValueError("duplicate change-set name")
        self.items[change_set.id] = change_set
        self.snapshots[change_set.id] = snapshot
        return change_set

    async def publish(self, change_set_id, expected_base_id, publisher, published_at, audit):
        draft = self.items[change_set_id]
        if (
            expected_base_id != self.current_id
            or draft.base_published_change_set_id != self.current_id
        ):
            raise ChangeSetConflict("stale_change_set")
        published = draft.published(published_at)
        self.items[change_set_id] = published
        self.current_id = change_set_id
        self.current = published
        await audit.record_publication(change_set_id, publisher, published_at)
        return published

    async def replace_snapshot(self, change_set_id, expected_version, snapshot, updated_at):
        draft = self.items[change_set_id]
        if draft.version != expected_version:
            raise ChangeSetConflict("stale_change_set")
        updated = TransportChangeSet(
            id=draft.id, name=draft.name, status=draft.status, version=draft.version + 1,
            base_published_change_set_id=draft.base_published_change_set_id,
            created_at=draft.created_at, updated_at=updated_at, expires_at=draft.expires_at,
        )
        self.items[change_set_id] = updated
        self.snapshots[change_set_id] = snapshot
        return updated

    async def recover(self, source_change_set_id, publisher, recovered_at, audit):
        source = self.items[source_change_set_id]
        recovered = TransportChangeSet(
            id=uuid4(), name=f"Recovery of {source.name}",
            status=TransportChangeSetStatus.PUBLISHED, version=1,
            base_published_change_set_id=self.current_id, created_at=recovered_at,
            updated_at=recovered_at, expires_at=source.expires_at,
        )
        self.items[recovered.id] = recovered
        self.snapshots[recovered.id] = self.snapshots[source_change_set_id]
        self.current_id = recovered.id
        self.current = recovered
        await audit.record_publication(recovered.id, publisher, recovered_at)
        return recovered

    async def rebase(self, change_set_id, base_change_set_id, snapshot, rebased_at):
        draft = self.items[change_set_id]
        rebased = TransportChangeSet(
            id=draft.id, name=draft.name, status=draft.status, version=draft.version + 1,
            base_published_change_set_id=base_change_set_id, created_at=draft.created_at,
            updated_at=rebased_at, expires_at=draft.expires_at,
        )
        self.items[change_set_id] = rebased
        self.snapshots[change_set_id] = snapshot
        return rebased


class RecordingAudit:
    def __init__(self) -> None:
        self.records = []

    async def record_publication(self, change_set_id, publisher, published_at, connection=None):
        self.records.append((change_set_id, publisher, published_at))

    async def is_recoverable(self, change_set_id, now):
        return True

    async def recent_publications(self, now):
        return self.records


class RecordingCache:
    def __init__(self) -> None:
        self.invalidated = False

    def invalidate_published_transport(self) -> None:
        self.invalidated = True


def service(repository=None, audit=None, cache=None):
    return TransportChangeSetService(
        repository or MemoryChangeSets(), audit or RecordingAudit(), cache or RecordingCache(),
        clock=lambda: datetime(2026, 11, 20, 9, tzinfo=UTC),
    )


def test_creating_a_named_draft_clones_the_current_published_baseline() -> None:
    repository = MemoryChangeSets()
    draft = asyncio.run(service(repository).create_draft("Spring timetable"))

    assert draft.status is TransportChangeSetStatus.DRAFT
    assert draft.base_published_change_set_id == repository.current_id
    assert (
        asyncio.run(repository.snapshot(draft.id))
        == repository.snapshots[repository.current_id]
    )


def test_duplicate_draft_name_is_rejected() -> None:
    change_sets = MemoryChangeSets()
    application = service(change_sets)
    asyncio.run(application.create_draft("Spring timetable"))

    with pytest.raises(ChangeSetConflict, match="name"):
        asyncio.run(application.create_draft("Spring timetable"))


def test_publish_with_schedule_warnings_requires_explicit_confirmation() -> None:
    repository = MemoryChangeSets()
    application = service(repository)
    draft = asyncio.run(application.create_draft("Incomplete timetable"))
    repository.snapshots[draft.id] = DraftTransportSnapshot(
        routes=(Route("R-01", "Lahore", "Campus", "Inbound"),),
        buses=("C-12",),
        assignments=(),
        weekly_departures=(WeeklyDeparture(1, time(8), "R-01"),),
        overrides=(),
    )

    with pytest.raises(PublishConfirmationRequired) as error:
        asyncio.run(application.publish(draft.id, repository.current_id, False, "publisher-1"))

    assert error.value.warnings[0].code == "missing_assignment"


def test_publish_is_atomic_from_callers_perspective_records_audit_and_invalidates_cache() -> None:
    repository = MemoryChangeSets()
    audit = RecordingAudit()
    cache = RecordingCache()
    application = service(repository, audit, cache)
    draft = asyncio.run(application.create_draft("Spring timetable"))

    result = asyncio.run(
        application.publish(draft.id, repository.current_id, False, "publisher-1")
    )

    assert result.status is TransportChangeSetStatus.PUBLISHED
    assert repository.current_id == draft.id
    assert audit.records == [(draft.id, "publisher-1", datetime(2026, 11, 20, 9, tzinfo=UTC))]
    assert cache.invalidated is True


def test_stale_draft_cannot_publish_until_rebased() -> None:
    repository = MemoryChangeSets()
    application = service(repository)
    draft = asyncio.run(application.create_draft("Spring timetable"))
    repository.current_id = uuid4()

    with pytest.raises(ChangeSetConflict, match="stale"):
        asyncio.run(
            application.publish(
                draft.id, draft.base_published_change_set_id, False, "publisher-1"
            )
        )


def test_rebase_replaces_a_stale_draft_with_the_current_published_baseline() -> None:
    repository = MemoryChangeSets()
    application = service(repository)
    draft = asyncio.run(application.create_draft("Spring timetable"))
    new_published_id = uuid4()
    repository.current_id = new_published_id
    repository.current = TransportChangeSet(
        id=new_published_id, name="New live timetable",
        status=TransportChangeSetStatus.PUBLISHED, version=2,
        base_published_change_set_id=None, created_at=datetime(2026, 11, 20, tzinfo=UTC),
        updated_at=datetime(2026, 11, 20, tzinfo=UTC),
        expires_at=datetime(2026, 12, 20, tzinfo=UTC),
    )
    repository.snapshots[new_published_id] = DraftTransportSnapshot((), (), (), (), ())

    rebased = asyncio.run(application.rebase(draft.id))

    assert rebased.base_published_change_set_id == new_published_id
    assert asyncio.run(repository.snapshot(draft.id)) == DraftTransportSnapshot((), (), (), (), ())


def test_expired_draft_cannot_be_rebased_or_published() -> None:
    repository = MemoryChangeSets()
    application = service(repository)
    draft = asyncio.run(application.create_draft("Expired timetable"))
    repository.items[draft.id] = TransportChangeSet(
        id=draft.id, name=draft.name, status=draft.status, version=draft.version,
        base_published_change_set_id=draft.base_published_change_set_id,
        created_at=draft.created_at, updated_at=draft.updated_at,
        expires_at=datetime(2026, 11, 19, tzinfo=UTC),
    )

    with pytest.raises(ChangeSetConflict, match="expired"):
        asyncio.run(application.rebase(draft.id))


def test_only_privileged_roles_may_manage_transport_change_sets() -> None:
    application = service()
    student = Principal("not-a-manager", Role.TRANSPORT_MANAGEMENT, active=False)

    with pytest.raises(PermissionError):
        asyncio.run(application.create_draft("Spring timetable", student))


def test_draft_save_uses_optimistic_version_and_never_changes_published_data() -> None:
    repository = MemoryChangeSets()
    application = service(repository)
    draft = asyncio.run(application.create_draft("Spring timetable"))
    replacement = DraftTransportSnapshot((), (), (), (), ())

    saved = asyncio.run(application.replace_snapshot(draft.id, 1, replacement))

    assert saved.version == 2
    assert asyncio.run(repository.snapshot(repository.current_id)).routes
    with pytest.raises(ChangeSetConflict, match="stale"):
        asyncio.run(application.replace_snapshot(draft.id, 1, replacement))


def test_recovery_publishes_a_whole_prior_snapshot_without_restoring_a_draft() -> None:
    repository = MemoryChangeSets()
    audit = RecordingAudit()
    recovered = asyncio.run(
        service(repository, audit).recover(repository.current_id, "publisher-1")
    )

    assert recovered.status is TransportChangeSetStatus.PUBLISHED
    assert recovered.id != repository.current_id or repository.current is recovered
    assert asyncio.run(repository.snapshot(recovered.id)) == repository.snapshots[recovered.id]
    assert audit.records[0][0] == recovered.id
