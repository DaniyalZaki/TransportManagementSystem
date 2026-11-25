from src.application.main import create_app


def test_health_endpoint_reports_ready() -> None:
    app = create_app()
    route = next(route for route in app.routes if route.path == "/health")

    assert route.methods == {"GET"}
    assert route.endpoint() == {"status": "ok"}


def test_openapi_describes_the_api() -> None:
    document = create_app().openapi()

    assert document["info"]["title"] == "Transport Service API"
    assert "/health" in document["paths"]
