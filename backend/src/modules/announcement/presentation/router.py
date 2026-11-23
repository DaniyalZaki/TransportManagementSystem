from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.application.authorization.roles import Principal
from src.infrastructure.cache.read_cache import InMemoryReadCache
from src.infrastructure.configuration.settings import Settings
from src.modules.announcement.application.services import AnnouncementService, InvalidAnnouncement
from src.modules.announcement.infrastructure.repository import PostgresAnnouncementRepository
from src.modules.authentication.presentation.router import _principal

public_router = APIRouter(prefix="/api/v1/public", tags=["public announcements"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["announcement administration"])


class PublishAnnouncementRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    content: str = Field(min_length=1, max_length=4000)
    expires_at: datetime | None = None
    urgent: bool = False
    operational: bool = False
    confirmed_at: datetime | None = None


class EditAnnouncementRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    content: str = Field(min_length=1, max_length=4000)
    expires_at: datetime | None = None


class _AnnouncementCache:
    def __init__(self, cache: InMemoryReadCache): self._cache = cache
    def invalidate_announcements(self) -> None:
        self._cache.invalidate("public_announcements")
        self._cache.invalidate("public_urgent_banners")


def _service(request: Request) -> AnnouncementService:
    application = getattr(request, "app", request)
    injected = getattr(application.state, "announcement_service", None)
    if injected is not None: return injected
    cache = getattr(application.state, "read_cache", None)
    if cache is None:
        cache = InMemoryReadCache(); application.state.read_cache = cache
    return AnnouncementService(PostgresAnnouncementRepository(Settings().database_url), _AnnouncementCache(cache))


def _announcement(item) -> dict[str, object]:
    return {"id": str(item.id), "title": item.title, "content": item.content, "published_at": item.published_at.isoformat(), "expires_at": item.expires_at.isoformat() if item.expires_at else None}


def _banner(item) -> dict[str, object]:
    return {"id": str(item.id), "announcement_id": str(item.announcement_id), "title": item.title, "content": item.content, "created_at": item.created_at.isoformat()}


@public_router.get("/announcements")
async def announcements(request: Request) -> dict[str, object]:
    return {"announcements": [_announcement(item) for item in await _service(request).public_announcements()]}


@public_router.get("/urgent-banners")
async def urgent_banners(request: Request) -> dict[str, object]:
    return {"banners": [_banner(item) for item in await _service(request).public_banners()]}


@admin_router.get("/announcements/current")
async def current_announcements(request: Request, principal: Annotated[Principal, Depends(_principal)]) -> dict[str, object]:
    try:
        announcements, banners = await _service(request).current_items(principal)
        return {
            "announcements": [_announcement(item) for item in announcements],
            "banners": [_banner(item) for item in banners],
        }
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@admin_router.post("/announcements", status_code=status.HTTP_201_CREATED)
async def publish_announcement(payload: PublishAnnouncementRequest, request: Request, principal: Annotated[Principal, Depends(_principal)]) -> dict[str, object]:
    try:
        result = await _service(request).publish(payload.title, payload.content, payload.expires_at, payload.urgent, payload.operational, payload.confirmed_at, principal)
        return {"announcement": _announcement(result.announcement), "banner": _banner(result.banner) if result.banner else None}
    except InvalidAnnouncement as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@admin_router.patch("/announcements/{announcement_id}")
async def edit_announcement(announcement_id: UUID, payload: EditAnnouncementRequest, request: Request, principal: Annotated[Principal, Depends(_principal)]) -> dict[str, object]:
    try: return {"announcement": _announcement(await _service(request).edit(announcement_id, payload.title, payload.content, payload.expires_at, principal))}
    except InvalidAnnouncement as error: raise HTTPException(status_code=422, detail=str(error)) from error
    except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error


@admin_router.post("/announcements/{announcement_id}/remove")
async def remove_announcement(announcement_id: UUID, request: Request, principal: Annotated[Principal, Depends(_principal)]) -> dict[str, object]:
    try: return {"announcement": _announcement(await _service(request).remove_announcement(announcement_id, principal))}
    except InvalidAnnouncement as error: raise HTTPException(status_code=422, detail=str(error)) from error
    except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error


@admin_router.post("/urgent-banners/{banner_id}/remove")
async def remove_banner(banner_id: UUID, request: Request, principal: Annotated[Principal, Depends(_principal)]) -> dict[str, object]:
    try: return {"banner": _banner(await _service(request).remove_banner(banner_id, principal))}
    except InvalidAnnouncement as error: raise HTTPException(status_code=422, detail=str(error)) from error
    except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error


@admin_router.post("/urgent-banners/{banner_id}/resolve")
async def resolve_banner(banner_id: UUID, request: Request, principal: Annotated[Principal, Depends(_principal)]) -> dict[str, object]:
    try: return {"banner": _banner(await _service(request).resolve_banner(banner_id, principal))}
    except InvalidAnnouncement as error: raise HTTPException(status_code=422, detail=str(error)) from error
    except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
