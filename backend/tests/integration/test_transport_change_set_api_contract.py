from src.application.main import create_app


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
