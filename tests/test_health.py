from fastapi.testclient import TestClient
from api.main import app


def test_health_endpoint_basic():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("api") == "ok"
    assert "vector_db" in data
    assert "redis" in data
    assert "mcp" in data

