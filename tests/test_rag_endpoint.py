from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch


def test_rag_ask_success():
    client = TestClient(app)

    async def fake_ask(question: str):
        return {"answer": "ans", "context": "ctx"}

    with patch("api.routers.rag.ask_rag", side_effect=fake_ask):
        resp = client.post("/api/rag/ask", json={"question": "Hola?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "ans"
    assert "context_preview" in data


def test_rag_ask_validation_error():
    client = TestClient(app)
    resp = client.post("/api/rag/ask", json={"question": ""})
    assert resp.status_code == 422
