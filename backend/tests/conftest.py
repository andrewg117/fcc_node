import pytest
from fastapi.testclient import TestClient

from backend.api.deps import get_user_repository
from backend.core.config import get_settings
from backend.main import app
from backend.repositories.user_repository import DuplicateEmailError, UserRecord


class FakeUserRepository:
    """In-memory stand-in for UserRepository, so route tests never touch Postgres."""

    def __init__(self) -> None:
        self.users: dict[str, UserRecord] = {}

    async def create(self, name: str, email: str, password_hash: str) -> UserRecord:
        if any(user.email == email for user in self.users.values()):
            raise DuplicateEmailError(email)
        user = UserRecord(
            id=str(len(self.users) + 1),
            name=name,
            email=email,
            password_hash=password_hash,
        )
        self.users[user.id] = user
        return user

    async def get_by_email(self, email: str) -> UserRecord | None:
        return next((user for user in self.users.values() if user.email == email), None)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self.users.get(user_id)


@pytest.fixture(autouse=True)
def test_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_users():
    return FakeUserRepository()


@pytest.fixture
def client(fake_users: FakeUserRepository):
    # TestClient(app) without a `with` block does not run the lifespan, so no
    # Postgres connection is opened; the dependency override does the rest.
    app.dependency_overrides[get_user_repository] = lambda: fake_users
    yield TestClient(app)
    app.dependency_overrides.clear()
