from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_home_route():
    res = client.get("/server/")
    assert res.status_code == 200
    assert res.text == "Server home\n"

def test_unmatched_route_404s():
    res = client.get("/server/does-not-exist")
    assert res.status_code == 404