from fastapi.testclient import TestClient

from backend.main import app

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

def test_create_user():
    payload = {
        "name": "andrew",
        "email": "email"
    }
    res = client.post("/server/user/", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert "data" in body
    assert body["data"]["name"] == "andrew" and body["data"]["email"] == "email"
    assert body["message"] == "User created successfully"

def test_invalid_create_user():
    payload = {
    }
    res = client.post("/server/user/", json=payload)
    assert res.status_code == 422

def test_create_user_with_empty_fields():
    payload = {"name": "andrew", "email": ""}
    res = client.post("/server/user/", json=payload)
    assert res.status_code == 422
    body = res.json()
    assert body["message"] == "Fields missing. User not created"