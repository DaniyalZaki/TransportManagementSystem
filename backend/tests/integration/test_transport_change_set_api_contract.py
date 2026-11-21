# flake8: noqa
import pytest
from pydantic import ValidationError
from src.application.main import create_app
from src.modules.transport_data.presentation.admin_router import RouteInput, WeeklyDepartureInput

def test_single_draft_routes_are_documented():
    paths = create_app().openapi()["paths"]
    assert "/api/v1/admin/transport/draft" in paths and "/api/v1/admin/transport/draft/publish" in paths
    assert "/api/v1/admin/transport/change-sets" not in paths
    publish_schema = create_app().openapi()["components"]["schemas"]["PublishChangeSetRequest"]
    assert "expected_base_published_change_set_id" not in publish_schema["properties"]

def test_schedule_contract_uses_weekdays_one_through_seven_and_fixed_directions():
    assert WeeklyDepartureInput(weekday=7, route_code="R-01", departure_time="08:30").weekday == 7
    assert RouteInput(route_code="R-01", origin="A", destination="B", direction="RETURN").direction == "RETURN"
    with pytest.raises(ValidationError): WeeklyDepartureInput(weekday=0, route_code="R-01", departure_time="08:30")
