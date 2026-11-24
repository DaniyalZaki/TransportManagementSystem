import asyncio
from datetime import UTC, datetime

from src.application.authorization.roles import Principal, Role
from src.application.main import create_app
from src.modules.announcement.application.services import AnnouncementService
from src.modules.announcement.presentation.router import PublishAnnouncementRequest


class MemoryAnnouncements:
    def __init__(self): self.announcements = {}; self.banners = {}
    async def publish(self, item): self.announcements[item.id] = item; return item
    async def update(self, item): self.announcements[item.id] = item; return item
    async def get(self, identifier): return self.announcements.get(identifier)
    async def public_announcements(self, now): return tuple(item for item in self.announcements.values() if item.is_visible_at(now))
    async def current_announcements(self, now): return await self.public_announcements(now)
    async def public_banners(self): return tuple(item for item in self.banners.values() if item.is_visible)
    async def add_banner(self, item): self.banners[item.id] = item; return item
    async def get_banner(self, identifier): return self.banners.get(identifier)
    async def update_banner(self, item): self.banners[item.id] = item; return item
    async def delete_expired_or_removed(self, cutoff): return 0


class Cache:
    def invalidate_announcements(self): pass


def _endpoint(app, path, method):
    return next(route.endpoint for route in app.routes if route.path == path and method in route.methods)


def test_announcement_routes_document_public_reads_and_privileged_lifecycle():
    paths = create_app().openapi()["paths"]
    assert "/api/v1/public/announcements" in paths
    assert "/api/v1/public/urgent-banners" in paths
    assert "security" not in paths["/api/v1/public/announcements"]["get"]
    assert "/api/v1/admin/announcements" in paths
    assert "/api/v1/admin/announcements/current" in paths
    assert "/api/v1/admin/announcements/{announcement_id}" in paths
    assert "/api/v1/admin/announcements/{announcement_id}/remove" in paths
    assert "/api/v1/admin/urgent-banners/{banner_id}/remove" in paths
    assert "/api/v1/admin/urgent-banners/{banner_id}/resolve" in paths
    properties = paths["/api/v1/admin/announcements"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert properties["$ref"] == "#/components/schemas/PublishAnnouncementRequest"
    schema = create_app().openapi()["components"]["schemas"]["PublishAnnouncementRequest"]
    assert "operational" not in schema["properties"]
    assert "confirmed_at" not in schema["properties"]


def test_announcement_request_allows_an_omitted_message():
    request = PublishAnnouncementRequest(title="Title only")

    assert request.content == ""


def test_public_announcement_response_never_exposes_removed_or_expired_records():
    app = create_app()
    repository = MemoryAnnouncements()
    app.state.announcement_service = AnnouncementService(repository, Cache(), clock=lambda: datetime(2026, 11, 22, 9, tzinfo=UTC))
    publish = _endpoint(app, "/api/v1/admin/announcements", "POST")
    public = _endpoint(app, "/api/v1/public/announcements", "GET")
    principal = Principal("admin", Role.DESIGNATED_ADMINISTRATOR, True)

    asyncio.run(publish(PublishAnnouncementRequest(title="Expired", content="Old", expires_at="2026-11-22T10:00:00Z"), app, principal))
    item = next(iter(repository.announcements.values()))
    repository.announcements[item.id] = item.edit(item.title, item.content, datetime(2026, 11, 22, 8, tzinfo=UTC), item.updated_at)
    response = asyncio.run(public(app))

    assert response["announcements"] == []
