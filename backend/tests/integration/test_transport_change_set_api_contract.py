import pytest
from pydantic import ValidationError

from src.application.main import create_app
from src.modules.transport_data.presentation.admin_router import (
    RouteInput,
    WeeklyDepartureInput,
)


def test_change_set_routes_are_privileged_and_document_publish_confirmation() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v1/admin/transport/change-sets" in paths
    assert "/api/v1/admin/transport/change-sets/{change_set_id}/validate" in paths
    assert "/api/v1/admin/transport/change-sets/{change_set_id}/publish" in paths
    assert "/api/v1/admin/transport/change-sets/{change_set_id}" in paths
    assert "/api/v1/admin/transport/publications" in paths
    assert "/api/v1/admin/transport/publications/{change_set_id}/recover" in paths
    assert "authorization" in {
        parameter["name"]
        for parameter in paths["/api/v1/admin/transport/change-sets"]["post"]["parameters"]
    }
    publish_schema = create_app().openapi()["components"]["schemas"]["PublishChangeSetRequest"]
    assert "publish_anyway" in publish_schema["properties"]
    update_schema = create_app().openapi()["components"]["schemas"]["UpdateChangeSetRequest"]
    assert "expected_version" in update_schema["properties"]


def test_schedule_contract_uses_weekdays_one_through_seven_and_fixed_directions() -> None:
    assert WeeklyDepartureInput(weekday=1, route_code="R-01", departure_time="08:30").weekday == 1
    assert WeeklyDepartureInput(weekday=7, route_code="R-01", departure_time="08:30").weekday == 7
    route = RouteInput(
        route_code="R-01", origin="A", destination="B", direction="RETURN"
    )
    assert route.direction == "RETURN"
    with pytest.raises(ValidationError):
        WeeklyDepartureInput(weekday=0, route_code="R-01", departure_time="08:30")
    with pytest.raises(ValidationError):
        RouteInput(route_code="R-01", origin="A", destination="B", direction="Outbound")
