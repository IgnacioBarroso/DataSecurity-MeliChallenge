from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch


def test_rag_debug_success():
    client = TestClient(app)

    async def fake_debug(question: str):
        return [
            {"score": 0.9, "selected": True, "text_preview": "doc1"},
            {"score": 0.7, "selected": False, "text_preview": "doc2"},
        ]

    with patch("api.routers.rag.debug_rag_service", side_effect=fake_debug):
        resp = client.post("/api/rag/debug", json={"question": "Hola?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "Hola?"
    assert isinstance(data.get("docs"), list) and len(data["docs"]) == 2
