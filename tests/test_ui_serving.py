from fastapi.testclient import TestClient
from api.main import app


def test_serves_index_html():
    client = TestClient(app)
    r = client.get("/ui")
    assert r.status_code == 200
    assert "Meli Challenge" in r.text


def test_serves_assets():
    client = TestClient(app)
    r_css = client.get("/ui/assets/css/styles.css")
    assert r_css.status_code == 200
    r_js = client.get("/ui/assets/js/app.js")
    assert r_js.status_code == 200

