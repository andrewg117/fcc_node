from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_home_route():
    res = client.get("/server/")
    assert res.status_code == 200
    assert res.text == "Server home\n"

def test_valid_numeric_user_id():
    res = client.get("/server/user/42")
    assert res.status_code == 200
    assert res.text == "User ID: 42"

def test_non_numeric_user_id_returns_404():
    res = client.get("/server/user/abc")
    assert res.status_code == 404
    body = res.json()
    assert body["message"] == "Id given is not a number"

def test_unmatched_route_404s():
    res = client.get("/server/does-not-exist")
    assert res.status_code == 404