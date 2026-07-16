from server.app.main import app


def test_investigation_routes_are_registered():
    route_paths = set(app.openapi()["paths"])

    assert {
        "/api/v1/investigations",
        "/api/v1/investigations/{investigation_id}/candidates",
        "/api/v1/investigations/{investigation_id}/timeline",
    } <= route_paths
