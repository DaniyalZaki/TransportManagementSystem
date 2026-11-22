import asyncio

from src.application.main import create_app


def _endpoint(app, path, method):
    return next(route.endpoint for route in app.routes if route.path == path and method in route.methods)


def test_feedback_route_is_public_and_documents_the_form_contract():
    paths = create_app().openapi()["paths"]

    assert "/api/v1/public/feedback" in paths
    operation = paths["/api/v1/public/feedback"]["post"]
    assert "security" not in operation
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("FeedbackRequest")


def test_feedback_route_returns_receipt_delivery_error_and_neutral_pending_duplicate():
    from src.modules.feedback.application.services import FeedbackResult

    class Service:
        def __init__(self, outcome): self.outcome = outcome
        async def submit(self, **_): return FeedbackResult(self.outcome, None)

    app = create_app()
    endpoint = _endpoint(app, "/api/v1/public/feedback", "POST")
    request_type = endpoint.__annotations__["payload"]
    payload = request_type(content="Feedback", honeypot="")

    for outcome, expected_status, expected_message in [
        ("received", 201, "received"),
        ("delivery_failed", 503, "could not be delivered"),
        ("already_received", 202, "already received"),
    ]:
        app.state.feedback_service = Service(outcome)
        response = asyncio.run(endpoint(payload, app))
        assert response.status_code == expected_status
        assert expected_message in response.body.decode().lower()
