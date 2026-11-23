# flake8: noqa
import asyncio
from datetime import UTC, datetime, time
from uuid import uuid4

import pytest

from src.modules.transport_data.application.services import ChangeSetConflict, PublishConfirmationRequired, TransportChangeSetService
from src.modules.transport_data.domain.change_sets import DraftTransportSnapshot, TransportChangeSet, TransportChangeSetStatus
from src.modules.transport_data.domain.schedule import Assignment, Route, WeeklyDeparture


class MemoryChangeSets:
    def __init__(self): self.current = None; self.items = {}; self.snapshots = {}
    async def working_draft(self): return next((x for x in self.items.values() if x.status is TransportChangeSetStatus.DRAFT), None)
    async def current_published(self): return self.current
    async def get(self, identifier): return self.items.get(identifier)
    async def snapshot(self, identifier): return self.snapshots[identifier]
    async def create(self, item, snapshot): self.items[item.id] = item; self.snapshots[item.id] = snapshot; return item
    async def expire_drafts(self, now): return 0
    async def delete_retired(self, now): return 0
    async def publish(self, identifier, publisher, published_at, audit):
        draft = self.items[identifier]; published = TransportChangeSet(uuid4(), "Published working draft", TransportChangeSetStatus.PUBLISHED, 1, draft.base_published_change_set_id, published_at, published_at, datetime.max.replace(tzinfo=UTC))
        self.items[published.id] = published; self.snapshots[published.id] = self.snapshots[identifier]; self.current = published
        updated = TransportChangeSet(draft.id, draft.name, draft.status, draft.version + 1, published.id, draft.created_at, published_at, draft.expires_at); self.items[identifier] = updated
        await audit.record_publication(published.id, publisher, published_at); return updated, published.id
    async def replace_snapshot(self, identifier, expected, snapshot, updated_at):
        draft = self.items[identifier]
        if draft.version != expected: raise ChangeSetConflict("stale_change_set")
        updated = TransportChangeSet(draft.id, draft.name, draft.status, draft.version + 1, draft.base_published_change_set_id, draft.created_at, updated_at, draft.expires_at); self.items[identifier] = updated; self.snapshots[identifier] = snapshot; return updated

class Audit:
    def __init__(self): self.records = []
    async def record_publication(self, *args, **kwargs): self.records.append(args)
    async def is_recoverable(self, *args): return True
    async def recent_publications(self, *args): return self.records
class Cache:
    def __init__(self): self.invalidated = False
    def invalidate_published_transport(self): self.invalidated = True
def make_service(repo, audit=None, cache=None): return TransportChangeSetService(repo, audit or Audit(), cache or Cache(), clock=lambda: datetime(2026, 11, 21, tzinfo=UTC))

def test_open_draft_creates_once_and_never_expires():
    repo = MemoryChangeSets(); app = make_service(repo); first = asyncio.run(app.open_draft()); second = asyncio.run(app.open_draft())
    assert first.id == second.id and first.expires_at.year == 9999

def test_save_persists_for_next_account_and_returns_execution_order():
    repo = MemoryChangeSets(); app = make_service(repo); draft = asyncio.run(app.open_draft())
    snapshot = DraftTransportSnapshot((Route("R-1", "A", "B", "RETURN"),), ("C-1",), (Assignment("R-1", "C-1"),), (), ())
    saved = asyncio.run(app.replace_snapshot(draft.id, draft.version, snapshot))
    assert saved.draft.operation_order is not None and asyncio.run(app.get_draft(draft.id))[1] == snapshot

def test_publish_warning_only_for_route_missing_schedule_and_preserves_draft():
    repo = MemoryChangeSets(); audit = Audit(); cache = Cache(); app = make_service(repo, audit, cache); draft = asyncio.run(app.open_draft())
    incomplete = DraftTransportSnapshot((Route("R-1", "A", "B", "RETURN"),), (), (), (), ())
    asyncio.run(app.replace_snapshot(draft.id, draft.version, incomplete))
    with pytest.raises(PublishConfirmationRequired): asyncio.run(app.publish(draft.id, False, "u"))
    outcome = asyncio.run(app.publish(draft.id, True, "u"))
    assert outcome.draft.status is TransportChangeSetStatus.DRAFT and repo.current.id == outcome.published_change_set_id and cache.invalidated


def test_publish_does_not_require_a_rebase_when_the_current_pointer_changes():
    repo = MemoryChangeSets()
    app = make_service(repo)
    draft = asyncio.run(app.open_draft())
    repo.current = TransportChangeSet(
        uuid4(), "Another publication", TransportChangeSetStatus.PUBLISHED, 1,
        None, datetime(2026, 11, 21, tzinfo=UTC), datetime(2026, 11, 21, tzinfo=UTC),
        datetime.max.replace(tzinfo=UTC),
    )

    outcome = asyncio.run(app.publish(draft.id, True, "u"))

    assert outcome.draft.status is TransportChangeSetStatus.DRAFT


def test_simultaneous_saves_are_processed_in_order_without_silent_overwrite():
    repo = MemoryChangeSets()
    app = make_service(repo)
    draft = asyncio.run(app.open_draft())

    async def save_empty_snapshot():
        return await app.replace_snapshot(
            draft.id, draft.version, DraftTransportSnapshot((), (), (), (), ())
        )

    async def save_together():
        return await asyncio.gather(
            save_empty_snapshot(), save_empty_snapshot(), return_exceptions=True
        )

    first, second = asyncio.run(save_together())

    assert first.draft.operation_order is not None
    assert isinstance(second, ChangeSetConflict)
    assert second.operation_order is not None
    assert second.operation_order > first.draft.operation_order


def test_draft_reports_changes_only_when_it_differs_from_current_publication():
    repo = MemoryChangeSets()
    app = make_service(repo)
    draft = asyncio.run(app.open_draft())
    published_snapshot = DraftTransportSnapshot(
        (Route("R-1", "A", "B", "RETURN"),),
        ("C-1",),
        (Assignment("R-1", "C-1"),),
        (WeeklyDeparture(1, time(8, 30), "R-1"),),
        (),
    )
    repo.snapshots[draft.id] = published_snapshot
    repo.current = TransportChangeSet(
        uuid4(), "Published", TransportChangeSetStatus.PUBLISHED, 1, None,
        datetime(2026, 11, 21, tzinfo=UTC), datetime(2026, 11, 21, tzinfo=UTC),
        datetime.max.replace(tzinfo=UTC),
    )
    repo.snapshots[repo.current.id] = published_snapshot

    assert asyncio.run(app.has_published_changes(draft.id)) is False

    changed = DraftTransportSnapshot(
        published_snapshot.routes, published_snapshot.buses, published_snapshot.assignments,
        (WeeklyDeparture(1, time(9), "R-1"),), (),
    )
    repo.snapshots[draft.id] = changed

    assert asyncio.run(app.has_published_changes(draft.id)) is True
