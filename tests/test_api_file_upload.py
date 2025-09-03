import io
from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


def test_analyze_upload_with_file(monkeypatch):
    async def fake_run(text):
        assert isinstance(text, str) and len(text) > 0
        return {"report_json": "{\"ok\": true}", "session_id": "sess-file-1"}

    monkeypatch.setattr("api.routers.analysis.crew_service.run_analysis_crew", fake_run)

    content = b"hello from file"
    files = {"file": ("sample.txt", io.BytesIO(content), "text/plain")}
    resp = client.post("/api/analyze-upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-file-1"
    assert data["report_json"] == "{\"ok\": true}"


def test_analyze_upload_with_form_text(monkeypatch):
    async def fake_run(text):
        assert text == "form text"
        return {"report_json": "{\"ok\": true}", "session_id": "sess-form-1"}

    monkeypatch.setattr("api.routers.analysis.crew_service.run_analysis_crew", fake_run)

    resp = client.post("/api/analyze-upload", data={"user_input": "form text"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-form-1"
    assert data["report_json"] == "{\"ok\": true}"

