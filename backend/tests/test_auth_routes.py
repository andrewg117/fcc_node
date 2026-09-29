from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_settings
from backend.core.security import create_access_token, decode_access_token

VALID_USER = {"name": "Andrew", "email": "andrew@example.com", "password": "correct-horse-battery"}


def register(client: TestClient, **overrides):
    return client.post("/auth/register", json={**VALID_USER, **overrides})


def login(client: TestClient, email: str = VALID_USER["email"], password: str = VALID_USER["password"]):
    return client.post("/auth/login", json={"email": email, "password": password})


# --- register ---------------------------------------------------------------


def test_register_creates_user(client, fake_users):
    res = register(client)
    assert res.status_code == 201
    assert res.json() == {
        "message": "User created successfully",
        "data": {"name": "Andrew", "email": "andrew@example.com"},
    }
    stored = fake_users.users["1"]
    assert stored.password_hash != VALID_USER["password"]
    assert stored.password_hash.startswith("$argon2")


def test_register_ignores_password_confirm_field(client):
    # The client's Register form sends passwordConfirm too.
    assert register(client, passwordConfirm="correct-horse-battery").status_code == 201


def test_register_normalizes_email_and_name(client):
    res = register(client, name="  Andrew  ", email="Andrew@Example.COM")
    assert res.status_code == 201
    assert res.json()["data"] == {"name": "Andrew", "email": "andrew@example.com"}


def test_register_duplicate_email_returns_409(client):
    assert register(client).status_code == 201
    res = register(client, email="ANDREW@example.com")
    assert res.status_code == 409
    assert res.json() == {"code": 409, "type": "HttpError", "message": "Email already registered"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"password": "short"},
        {"password": "x" * 129},
        {"name": "   "},
    ],
)
def test_register_rejects_invalid_input(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_register_rejects_missing_fields(client):
    assert client.post("/auth/register", json={}).status_code == 422


# --- login ------------------------------------------------------------------


def test_login_returns_token_and_user(client, fake_users):
    register(client)
    res = login(client)
    assert res.status_code == 200
    body = res.json()
    assert body["message"] == "Login successful"
    assert body["data"] == {"name": "Andrew", "email": "andrew@example.com"}
    assert decode_access_token(body["token"]) == fake_users.users["1"].id


def test_login_email_is_case_and_whitespace_insensitive(client):
    register(client)
    assert login(client, email="  ANDREW@example.com ").status_code == 200


def test_login_wrong_password_returns_401(client):
    register(client)
    res = login(client, password="wrong-password")
    assert res.status_code == 401
    assert res.json() == {"code": 401, "type": "HttpError", "message": "Invalid email or password"}


def test_login_unknown_email_gets_same_error_as_wrong_password(client):
    register(client)
    wrong_password = login(client, password="wrong-password")
    unknown_email = login(client, email="nobody@example.com")
    assert unknown_email.status_code == 401
    assert unknown_email.json() == wrong_password.json()


# --- /auth/me and token handling --------------------------------------------


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_returns_current_user(client):
    register(client)
    token = login(client).json()["token"]
    res = client.get("/auth/me", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json() == {"name": "Andrew", "email": "andrew@example.com"}


def test_me_without_token_returns_401_in_error_shape(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
    assert res.json() == {"code": 401, "type": "HttpError", "message": "Not authenticated"}


def test_me_with_garbage_token_returns_401(client):
    res = client.get("/auth/me", headers=auth_header("not-a-jwt"))
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid or expired token"


def test_me_with_expired_token_returns_401(client):
    register(client)
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    res = client.get("/auth/me", headers=auth_header(expired))
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid or expired token"


def test_me_with_token_signed_by_another_secret_returns_401(client):
    register(client)
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "some-other-secret-that-is-also-32-characters-long",
        algorithm="HS256",
    )
    assert client.get("/auth/me", headers=auth_header(forged)).status_code == 401


def test_me_for_deleted_user_returns_401(client, fake_users):
    register(client)
    token = login(client).json()["token"]
    fake_users.users.clear()
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_token_for_unknown_user_id_is_rejected(client):
    token = create_access_token("does-not-exist")
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


# --- /auth/deregister -------------------------------------------------------


def test_deregister_deletes_current_user(client, fake_users):
    register(client)
    token = login(client).json()["token"]
    res = client.delete("/auth/deregister", headers=auth_header(token))
    assert res.status_code == 204
    assert res.content == b""
    assert fake_users.users == {}


def test_deregister_invalidates_token_and_login(client):
    register(client)
    token = login(client).json()["token"]
    client.delete("/auth/deregister", headers=auth_header(token))
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401
    assert login(client).status_code == 401


def test_deregister_only_deletes_own_account(client, fake_users):
    register(client)
    register(client, email="other@example.com")
    token = login(client, email="other@example.com").json()["token"]
    assert client.delete("/auth/deregister", headers=auth_header(token)).status_code == 204
    assert [user.email for user in fake_users.users.values()] == ["andrew@example.com"]


def test_deregister_without_token_returns_401(client, fake_users):
    register(client)
    res = client.delete("/auth/deregister")
    assert res.status_code == 401
    assert res.json() == {"code": 401, "type": "HttpError", "message": "Not authenticated"}
    assert len(fake_users.users) == 1


def test_email_can_register_again_after_deregister(client):
    register(client)
    token = login(client).json()["token"]
    client.delete("/auth/deregister", headers=auth_header(token))
    assert register(client).status_code == 201
