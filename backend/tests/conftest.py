import itertools
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from backend.api.deps import (
    get_media_repository,
    get_media_storage,
    get_user_repository,
)
from backend.core.config import get_settings
from backend.main import app
from backend.repositories.media_repository import (
    DuplicateMediaError,
    MediaRecord,
    MediaUpdate,
)
from backend.repositories.user_repository import DuplicateEmailError, UserRecord
from backend.services.media_storage import StoredObject


class FakeUserRepository:
    """In-memory stand-in for UserRepository, so route tests never touch Postgres."""

    def __init__(self) -> None:
        self.users: dict[str, UserRecord] = {}
        # A counter, not len(self.users) + 1, so ids never repeat after a delete.
        self._ids = itertools.count(1)

    async def create(self, name: str, email: str, password_hash: str) -> UserRecord:
        if any(user.email == email for user in self.users.values()):
            raise DuplicateEmailError(email)
        user = UserRecord(
            id=str(next(self._ids)),
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

    async def delete_by_id(self, user_id: str) -> None:
        self.users.pop(user_id, None)


class FakeMediaRepository:
    """In-memory stand-in for MediaRepository."""

    def __init__(self) -> None:
        self.items: dict[str, MediaRecord] = {}
        self._ids = itertools.count(1)

    def _check_paths_unused(self, media_id: str | None, *paths: str | None) -> None:
        # Like the unique constraints on image_path and song_path.
        for item in self.items.values():
            if item.id != media_id and {item.image_path, item.song_path} & set(paths):
                raise DuplicateMediaError

    async def create(
        self,
        user_id: str,
        title: str,
        description: str,
        image_path: str,
        song_path: str,
    ) -> MediaRecord:
        self._check_paths_unused(None, image_path, song_path)
        item = MediaRecord(
            id=str(next(self._ids)),
            user_id=user_id,
            title=title,
            description=description,
            image_path=image_path,
            song_path=song_path,
            created_at=datetime.now(UTC),
        )
        self.items[item.id] = item
        return item

    async def list_for_user(self, user_id: str) -> list[MediaRecord]:
        # Newest first, like the real repository. Ids only go up, so reversed insertion order works.
        return [
            item for item in reversed(self.items.values()) if item.user_id == user_id
        ]

    async def get_by_id(self, media_id: str) -> MediaRecord | None:
        return self.items.get(media_id)

    async def update(self, media_id: str, changes: MediaUpdate) -> MediaRecord | None:
        if media_id not in self.items:
            return None
        self._check_paths_unused(media_id, changes.image_path, changes.song_path)
        item = replace(self.items[media_id], **changes.model_dump(exclude_none=True))
        self.items[media_id] = item
        return item

    async def delete_by_id(self, media_id: str) -> bool:
        return self.items.pop(media_id, None) is not None


class FakeMediaStorage:
    """In-memory stand-in for MediaStorage. A test "uploads" a file by adding to `objects`."""

    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}
        self.deleted: list[str] = []

    def public_url(self, path: str) -> str:
        return f"https://storage.test/public/{path}"

    async def create_upload_url(self, path: str) -> str:
        return f"https://storage.test/upload/{path}?token=test"

    async def get_file_info(self, path: str) -> StoredObject | None:
        return self.objects.get(path)

    async def delete(self, paths: list[str]) -> None:
        for path in paths:
            self.objects.pop(path, None)
        self.deleted.extend(paths)


@pytest.fixture(autouse=True)
def test_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.test")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "test-secret-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_users():
    return FakeUserRepository()


@pytest.fixture
def fake_media():
    return FakeMediaRepository()


@pytest.fixture
def fake_storage():
    return FakeMediaStorage()


@pytest.fixture
def client(
    fake_users: FakeUserRepository,
    fake_media: FakeMediaRepository,
    fake_storage: FakeMediaStorage,
):
    # TestClient(app) without a `with` block does not run the lifespan, so no
    # Postgres connection is opened; the dependency overrides do the rest.
    app.dependency_overrides[get_user_repository] = lambda: fake_users
    app.dependency_overrides[get_media_repository] = lambda: fake_media
    app.dependency_overrides[get_media_storage] = lambda: fake_storage
    yield TestClient(app)
    app.dependency_overrides.clear()
