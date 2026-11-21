"""Privileged HTTP contract for Transport Data change-set publication."""

from datetime import date, time
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.application.authorization.roles import Principal
from src.infrastructure.cache.read_cache import InMemoryReadCache
from src.infrastructure.configuration.settings import Settings
from src.modules.audit.application.publication_audit import PostgresPublicationAudit
from src.modules.authentication.presentation.router import _principal
from src.modules.transport_data.application.services import (
    ChangeSetConflict, PublishConfirmationRequired, TransportChangeSetService,
)
from src.modules.transport_data.domain.change_sets import DraftTransportSnapshot
from src.modules.transport_data.domain.schedule import (
    Assignment, DepartureOverride, Route, WeeklyDeparture,
)
from src.modules.transport_data.infrastructure.change_set_repository import (
    PostgresChangeSetRepository,
)

router = APIRouter(prefix="/api/v1/admin/transport", tags=["transport administration"])


class PublishChangeSetRequest(BaseModel):
    publish_anyway: bool = False


class RouteInput(BaseModel):
    route_code: str = Field(min_length=1, max_length=80)
    origin: str = Field(min_length=1, max_length=160)
    destination: str = Field(min_length=1, max_length=160)
    direction: Literal["RETURN", "PICK-UP"]


class AssignmentInput(BaseModel):
    route_code: str = Field(min_length=1, max_length=80)
    bus_identifier: str = Field(min_length=1, max_length=80)


class WeeklyDepartureInput(BaseModel):
    weekday: int = Field(ge=1, le=7)
    route_code: str = Field(min_length=1, max_length=80)
    departure_time: time


class OverrideInput(BaseModel):
    service_date: date
    is_full_day_no_service: bool = False
    operation: Literal["add", "remove"] | None = None
    route_code: str | None = None
    bus_identifier: str | None = None
    departure_time: time | None = None


class UpdateChangeSetRequest(BaseModel):
    expected_version: int = Field(gt=0)
    routes: list[RouteInput] = []
    buses: list[str] = []
    assignments: list[AssignmentInput] = []
    weekly_departures: list[WeeklyDepartureInput] = []
    overrides: list[OverrideInput] = []


def _service(request: Request) -> TransportChangeSetService:
    application = getattr(request, "app", request)
    injected = getattr(application.state, "transport_change_set_service", None)
    if injected is not None:
        return injected
    cache = getattr(application.state, "read_cache", None)
    if cache is None:
        cache = InMemoryReadCache()
        application.state.read_cache = cache
    return TransportChangeSetService(
        PostgresChangeSetRepository(Settings().database_url),
        PostgresPublicationAudit(Settings().database_url),
        _TransportCacheInvalidator(cache),
    )


class _TransportCacheInvalidator:
    def __init__(self, cache: InMemoryReadCache) -> None:
        self._cache = cache

    def invalidate_published_transport(self) -> None:
        self._cache.clear()


def _response(change_set) -> dict[str, object]:
    return {
        "id": str(change_set.id), "name": change_set.name,
        "status": change_set.status.value, "version": change_set.version,
        "base_published_change_set_id": (
            str(change_set.base_published_change_set_id)
            if change_set.base_published_change_set_id else None
        ),
        "operation_order": change_set.operation_order,
    }


def _snapshot_response(snapshot: DraftTransportSnapshot) -> dict[str, object]:
    return {
        "routes": [
            {"route_code": x.route_code, "origin": x.origin,
             "destination": x.destination, "direction": x.direction}
            for x in snapshot.routes
        ],
        "buses": list(snapshot.buses),
        "assignments": [
            {"route_code": x.route_code, "bus_identifier": x.bus_identifier}
            for x in snapshot.assignments
        ],
        "weekly_departures": [
            {"weekday": x.weekday, "departure_time": x.departure_time.isoformat(),
             "route_code": x.route_code}
            for x in snapshot.weekly_departures
        ],
        "overrides": [
            {"service_date": x.service_date.isoformat(),
             "is_full_day_no_service": x.is_full_day_no_service,
             "operation": x.operation.value if x.operation else None,
             "route_code": x.route_code, "bus_identifier": x.bus_identifier,
             "departure_time": x.departure_time.isoformat() if x.departure_time else None}
            for x in snapshot.overrides
        ],
    }


def _snapshot(payload: UpdateChangeSetRequest) -> DraftTransportSnapshot:
    overrides = []
    for item in payload.overrides:
        if item.is_full_day_no_service:
            if any((item.operation, item.route_code, item.bus_identifier, item.departure_time)):
                raise ValueError("Full-day no-service overrides cannot include a partial override")
            overrides.append(DepartureOverride.full_day_no_service(item.service_date))
        elif (
            item.operation and item.route_code and item.bus_identifier
            and item.departure_time is not None
        ):
            factory = DepartureOverride.add if item.operation == "add" else DepartureOverride.remove
            overrides.append(
                factory(item.service_date, item.route_code,
                        item.bus_identifier, item.departure_time)
            )
        else:
            raise ValueError("Partial overrides require operation, route, bus, and departure time")
    return DraftTransportSnapshot(
        routes=tuple(
            Route(x.route_code, x.origin, x.destination, x.direction)
            for x in payload.routes
        ),
        buses=tuple(x.strip() for x in payload.buses if x.strip()),
        assignments=tuple(Assignment(x.route_code, x.bus_identifier) for x in payload.assignments),
        weekly_departures=tuple(
            WeeklyDeparture(x.weekday, x.departure_time, x.route_code)
            for x in payload.weekly_departures
        ),
        overrides=tuple(overrides),
    )


@router.get("/draft")
async def open_draft(
    request: Request,
    principal: Annotated[Principal, Depends(_principal)],
) -> dict[str, object]:
    try:
        service = _service(request)
        draft = await service.open_draft(principal)
        _, snapshot = await service.get_draft(draft.id, principal)
        return {**_response(draft), "snapshot": _snapshot_response(snapshot)}
    except (ValueError, PermissionError, ChangeSetConflict) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.patch("/draft")
async def update_change_set(
    payload: UpdateChangeSetRequest, request: Request,
    principal: Annotated[Principal, Depends(_principal)],
) -> dict[str, object]:
    try:
        service = _service(request)
        draft = await service.open_draft(principal)
        updated = await service.replace_snapshot(
            draft.id, payload.expected_version, _snapshot(payload), principal
        )
        return _response(updated.draft)
    except ChangeSetConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_change_set",
                "message": str(error),
                "operation_order": error.operation_order,
            },
        ) from error
    except (ValueError, PermissionError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.post("/draft/publish")
async def publish_change_set(
    payload: PublishChangeSetRequest, request: Request,
    principal: Annotated[Principal, Depends(_principal)],
) -> dict[str, object]:
    try:
        service = _service(request)
        draft = await service.open_draft(principal)
        published = await service.publish(
            draft.id, payload.publish_anyway, principal.subject, principal,
        )
        return {
            **_response(published.draft),
            "published_change_set_id": str(published.published_change_set_id),
            "published_at": published.published_at.isoformat(),
        }
    except PublishConfirmationRequired as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "publish_confirmation_required", "warnings": [
                {"code": item.code, "message": item.message} for item in error.warnings
            ]},
        ) from error
    except ChangeSetConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_change_set",
                "message": str(error),
                "operation_order": error.operation_order,
            },
        ) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.post("/publications/{change_set_id}/recover")
async def recover_published_change_set(
    change_set_id: UUID, request: Request,
    principal: Annotated[Principal, Depends(_principal)],
) -> dict[str, object]:
    try:
        return _response(
            await _service(request).recover(change_set_id, principal.subject, principal)
        )
    except ChangeSetConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.get("/publications")
async def publication_history(
    request: Request, principal: Annotated[Principal, Depends(_principal)],
) -> dict[str, object]:
    try:
        records = await _service(request).publication_history(principal)
        return {"publications": [
            {"change_set_id": str(change_set_id), "publisher": publisher,
             "published_at": published_at.isoformat()}
            for change_set_id, publisher, published_at in records
        ]}
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
