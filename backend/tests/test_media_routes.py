import pytest
from fastapi.testclient import TestClient

from backend.core.exceptions import HttpError
from backend.core.media_types import MB
from backend.repositories.media_repository import (
    MediaRecord,
    MediaUpdate,
    MissingUserError,
)
from backend.services.media_storage import StoredObject

IMAGE = {"kind": "image", "content_type": "image/png", "size": MB}
SONG = {"kind": "audio", "content_type": "audio/mpeg", "size": 9 * MB}


def sign_in(client: TestClient, email: str = "andrew@example.com") -> dict[str, str]:
    """Register and log in a user. Returns the Authorization header for them."""
    password = "correct-horse-battery"
    client.post("/auth/register", json={"name": "Andrew", "email": email, "password": password})
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def upload_file(client: TestClient, fake_storage, headers: dict[str, str], file: dict) -> str:
    """Upload steps 1 and 2 for one file. The fake storage stands in for the browser's PUT."""
    path = client.post("/media/uploads", json=file, headers=headers).json()["path"]
    fake_storage.objects[path] = StoredObject(content_type=file["content_type"], size=file["size"])
    return path


def create(client: TestClient, fake_storage, headers: dict[str, str], **fields):
    """All three upload steps for one image and one song."""
    body = {
        "title": "My Song",
        "description": "Recorded at home",
        "image_path": upload_file(client, fake_storage, headers, IMAGE),
        "song_path": upload_file(client, fake_storage, headers, SONG),
        **fields,
    }
    return client.post("/media", json=body, headers=headers)


def path_of(url: str) -> str:
    return url.removeprefix("https://storage.test/public/")


# --- POST /media/uploads ----------------------------------------------------


@pytest.mark.parametrize(("file", "extension"), [(IMAGE, ".png"), (SONG, ".mp3")])
def test_start_upload_returns_path_and_upload_url(client, fake_users, file, extension):
    res = client.post("/media/uploads", json=file, headers=sign_in(client))
    assert res.status_code == 200
    body = res.json()
    user_id = next(iter(fake_users.users))
    assert body["path"].startswith(f"{user_id}/")
    assert body["path"].endswith(extension)
    assert body["upload_url"] == f"https://storage.test/upload/{body['path']}?token=test"


def test_start_upload_gives_a_new_path_each_time(client):
    headers = sign_in(client)
    first = client.post("/media/uploads", json=SONG, headers=headers).json()["path"]
    second = client.post("/media/uploads", json=SONG, headers=headers).json()["path"]
    assert first != second


@pytest.mark.parametrize(
    ("kind", "content_type", "message"),
    [
        ("image", "audio/mpeg", "Image must be a JPEG, PNG, WebP or GIF file"),
        ("image", "image/svg+xml", "Image must be a JPEG, PNG, WebP or GIF file"),
        ("audio", "image/png", "Song must be an MP3, M4A, AAC or OGG file"),
        ("audio", "audio/wav", "Song must be an MP3, M4A, AAC or OGG file"),
        ("audio", "", "Song must be an MP3, M4A, AAC or OGG file"),
    ],
)
def test_start_upload_rejects_the_wrong_type(client, kind, content_type, message):
    res = client.post(
        "/media/uploads", json={"kind": kind, "content_type": content_type, "size": MB}, headers=sign_in(client)
    )
    assert res.status_code == 400
    assert res.json()["message"] == message


@pytest.mark.parametrize(
    ("file", "message"),
    [
        ({**IMAGE, "size": 10 * MB + 1}, "Image must be 10 MB or smaller"),
        ({**SONG, "size": 30 * MB + 1}, "Song must be 30 MB or smaller"),
    ],
)
def test_start_upload_rejects_large_files(client, file, message):
    res = client.post("/media/uploads", json=file, headers=sign_in(client))
    assert res.status_code == 400
    assert res.json()["message"] == message


@pytest.mark.parametrize("file", [{**SONG, "size": 0}, {**SONG, "kind": "video"}])
def test_start_upload_rejects_invalid_requests(client, file):
    assert client.post("/media/uploads", json=file, headers=sign_in(client)).status_code == 422


def test_media_routes_need_a_token(client):
    assert client.get("/media").status_code == 401
    assert client.post("/media/uploads", json=SONG).status_code == 401
    assert client.post("/media", json={"title": "x", "image_path": "x", "song_path": "x"}).status_code == 401
    assert client.patch("/media/1", json={"title": "x"}).status_code == 401
    assert client.delete("/media/1").status_code == 401


# --- POST /media -------------------------------------------------------------


def test_create_media(client, fake_storage):
    res = create(client, fake_storage, sign_in(client))
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "My Song"
    assert body["description"] == "Recorded at home"
    assert body["image_url"].startswith("https://storage.test/public/")
    assert body["image_url"].endswith(".png")
    assert body["song_url"].endswith(".mp3")


def test_create_media_description_is_optional(client, fake_storage):
    headers = sign_in(client)
    body = {
        "title": "My Song",
        "image_path": upload_file(client, fake_storage, headers, IMAGE),
        "song_path": upload_file(client, fake_storage, headers, SONG),
    }
    res = client.post("/media", json=body, headers=headers)
    assert res.status_code == 201
    assert res.json()["description"] == ""


@pytest.mark.parametrize("title", ["", "   ", "x" * 101])
def test_create_media_needs_a_title(client, fake_storage, title):
    assert create(client, fake_storage, sign_in(client), title=title).status_code == 422


def test_create_media_without_upload_returns_400(client, fake_storage):
    headers = sign_in(client)
    # Upload step 1 ran for the image, but the file was never sent.
    image_path = client.post("/media/uploads", json=IMAGE, headers=headers).json()["path"]
    res = create(client, fake_storage, headers, image_path=image_path)
    assert res.status_code == 400
    assert res.json()["message"] == "Upload not found"


def test_create_media_rejects_a_song_path_as_the_image(client, fake_storage):
    headers = sign_in(client)
    song_path = upload_file(client, fake_storage, headers, SONG)
    res = create(client, fake_storage, headers, image_path=song_path)
    assert res.status_code == 400
    assert res.json()["message"] == "Invalid upload path"
    # A valid file in the wrong slot is left alone.
    assert song_path in fake_storage.objects


def test_create_media_rejects_another_users_path(client, fake_storage):
    owner = sign_in(client)
    image_path = upload_file(client, fake_storage, owner, IMAGE)
    other = sign_in(client, email="other@example.com")
    res = create(client, fake_storage, other, image_path=image_path)
    assert res.status_code == 400
    assert res.json()["message"] == "Invalid upload path"


def test_create_media_checks_the_real_file_and_deletes_bad_ones(client, fake_storage, fake_media):
    headers = sign_in(client)
    song_path = upload_file(client, fake_storage, headers, SONG)
    # The browser said 9 MB of MP3, but a 40 MB file arrived.
    fake_storage.objects[song_path] = StoredObject(content_type="audio/mpeg", size=40 * MB)
    res = create(client, fake_storage, headers, song_path=song_path)
    assert res.status_code == 400
    assert res.json()["message"] == "Song must be 30 MB or smaller"
    assert fake_storage.deleted == [song_path]
    assert fake_media.items == {}


def test_create_media_twice_with_the_same_files_returns_409(client, fake_storage):
    headers = sign_in(client)
    first = create(client, fake_storage, headers).json()
    res = create(client, fake_storage, headers, image_path=path_of(first["image_url"]))
    assert res.status_code == 409
    assert res.json()["message"] == "Upload already saved"


def test_create_media_for_a_deleted_account_returns_401_and_deletes_the_files(
    client, fake_storage, fake_media, monkeypatch
):
    headers = sign_in(client)

    async def user_deleted_meanwhile(*args: str) -> MediaRecord:
        # What the real create raises if Delete Account ran during this request.
        raise MissingUserError

    monkeypatch.setattr(fake_media, "create", user_deleted_meanwhile)
    res = create(client, fake_storage, headers)
    assert res.status_code == 401
    assert res.json()["message"] == "Not authenticated"
    # Both uploaded files were deleted, so none are left.
    assert len(fake_storage.deleted) == 2
    assert fake_storage.objects == {}


# --- GET /media ----------------------------------------------------------------


def test_list_media_shows_only_your_own_newest_first(client, fake_storage):
    andrew = sign_in(client)
    other = sign_in(client, email="other@example.com")
    create(client, fake_storage, andrew, title="First")
    create(client, fake_storage, other, title="Not mine")
    create(client, fake_storage, andrew, title="Second")

    res = client.get("/media", headers=andrew)
    assert res.status_code == 200
    assert [item["title"] for item in res.json()] == ["Second", "First"]


# --- PATCH /media/{id} ------------------------------------------------------------


def test_update_title_and_description_keeps_the_files(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    res = client.patch(f"/media/{item['id']}", json={"title": "New title", "description": ""}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "New title"
    assert body["description"] == ""
    assert body["image_url"] == item["image_url"]
    assert body["song_url"] == item["song_url"]
    assert fake_storage.deleted == []


def test_update_with_an_empty_body_changes_nothing(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    res = client.patch(f"/media/{item['id']}", json={}, headers=headers)
    assert res.status_code == 200
    assert res.json() == item


def test_update_rejects_a_blank_title(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    assert client.patch(f"/media/{item['id']}", json={"title": " "}, headers=headers).status_code == 422


@pytest.mark.parametrize(("field", "file"), [("image", IMAGE), ("song", SONG)])
def test_update_replaces_one_file_and_deletes_the_old_one(client, fake_storage, field, file):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    new_path = upload_file(client, fake_storage, headers, file)

    res = client.patch(f"/media/{item['id']}", json={f"{field}_path": new_path}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert path_of(body[f"{field}_url"]) == new_path
    assert fake_storage.deleted == [path_of(item[f"{field}_url"])]
    # The other file is untouched.
    other = "song" if field == "image" else "image"
    assert body[f"{other}_url"] == item[f"{other}_url"]


def test_update_everything_at_once(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    changes = {
        "title": "New title",
        "description": "New description",
        "image_path": upload_file(client, fake_storage, headers, IMAGE),
        "song_path": upload_file(client, fake_storage, headers, SONG),
    }
    res = client.patch(f"/media/{item['id']}", json=changes, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert (body["title"], body["description"]) == ("New title", "New description")
    assert path_of(body["image_url"]) == changes["image_path"]
    assert path_of(body["song_url"]) == changes["song_path"]
    assert sorted(fake_storage.deleted) == sorted([path_of(item["image_url"]), path_of(item["song_url"])])


def test_update_with_the_current_path_deletes_nothing(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    res = client.patch(f"/media/{item['id']}", json={"image_path": path_of(item["image_url"])}, headers=headers)
    assert res.status_code == 200
    assert fake_storage.deleted == []


def test_update_with_another_items_file_returns_409(client, fake_storage):
    headers = sign_in(client)
    first = create(client, fake_storage, headers).json()
    second = create(client, fake_storage, headers).json()
    res = client.patch(f"/media/{second['id']}", json={"image_path": path_of(first["image_url"])}, headers=headers)
    assert res.status_code == 409
    assert fake_storage.deleted == []


def test_update_without_upload_returns_400_and_keeps_the_item(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    image_path = client.post("/media/uploads", json=IMAGE, headers=headers).json()["path"]
    res = client.patch(f"/media/{item['id']}", json={"title": "New", "image_path": image_path}, headers=headers)
    assert res.status_code == 400
    assert client.get("/media", headers=headers).json() == [item]


def test_update_another_users_media_returns_404(client, fake_storage):
    item = create(client, fake_storage, sign_in(client)).json()
    other = sign_in(client, email="other@example.com")
    assert client.patch(f"/media/{item['id']}", json={"title": "Mine now"}, headers=other).status_code == 404


def test_update_succeeds_even_if_the_old_file_cant_be_deleted(client, fake_storage, monkeypatch):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    new_path = upload_file(client, fake_storage, headers, IMAGE)

    async def broken_delete(paths: list[str]) -> None:
        raise HttpError("File storage is unavailable", 502)

    monkeypatch.setattr(fake_storage, "delete", broken_delete)
    res = client.patch(f"/media/{item['id']}", json={"image_path": new_path}, headers=headers)
    assert res.status_code == 200
    assert path_of(res.json()["image_url"]) == new_path


def test_update_of_media_deleted_meanwhile_returns_404(client, fake_storage, fake_media, monkeypatch):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    new_path = upload_file(client, fake_storage, headers, IMAGE)
    real_update = fake_media.update

    async def update_after_delete(media_id: str, changes: MediaUpdate) -> MediaRecord | None:
        # Another request deletes the row after get_own_item found it.
        await fake_media.delete_by_id(media_id)
        return await real_update(media_id, changes)

    monkeypatch.setattr(fake_media, "update", update_after_delete)
    res = client.patch(f"/media/{item['id']}", json={"image_path": new_path}, headers=headers)
    assert res.status_code == 404
    assert res.json()["message"] == "Media not found"
    # No file is deleted: the new one might belong to another upload.
    assert fake_storage.deleted == []


# --- DELETE /media/{id} ---------------------------------------------------------


def test_delete_media_removes_both_files_and_the_record(client, fake_storage):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    res = client.delete(f"/media/{item['id']}", headers=headers)
    assert res.status_code == 204
    assert fake_storage.objects == {}
    assert client.get("/media", headers=headers).json() == []


def test_delete_media_of_another_user_returns_404(client, fake_storage):
    owner = sign_in(client)
    item = create(client, fake_storage, owner).json()
    other = sign_in(client, email="other@example.com")
    assert client.delete(f"/media/{item['id']}", headers=other).status_code == 404
    assert len(client.get("/media", headers=owner).json()) == 1


def test_delete_unknown_media_returns_404(client):
    assert client.delete("/media/999", headers=sign_in(client)).status_code == 404


def test_delete_storage_failure_returns_502_and_keeps_the_record(client, fake_storage, monkeypatch):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()

    async def broken_delete(paths: list[str]) -> None:
        raise HttpError("File storage is unavailable", 502)

    monkeypatch.setattr(fake_storage, "delete", broken_delete)
    res = client.delete(f"/media/{item['id']}", headers=headers)
    assert res.status_code == 502
    assert res.json()["message"] == "File storage is unavailable"
    assert len(client.get("/media", headers=headers).json()) == 1


def test_delete_of_media_deleted_meanwhile_returns_404(client, fake_storage, fake_media, monkeypatch):
    headers = sign_in(client)
    item = create(client, fake_storage, headers).json()
    real_delete_by_id = fake_media.delete_by_id

    async def delete_after_another_delete(media_id: str) -> bool:
        # Another request deletes the row after get_own_item found it.
        await real_delete_by_id(media_id)
        return await real_delete_by_id(media_id)

    monkeypatch.setattr(fake_media, "delete_by_id", delete_after_another_delete)
    res = client.delete(f"/media/{item['id']}", headers=headers)
    assert res.status_code == 404
    assert client.get("/media", headers=headers).json() == []


# --- DELETE /auth/deregister ---------------------------------------------------


def test_deregister_deletes_all_your_files(client, fake_storage):
    headers = sign_in(client)
    first = create(client, fake_storage, headers).json()
    second = create(client, fake_storage, headers).json()
    other = sign_in(client, email="other@example.com")
    create(client, fake_storage, other)

    assert client.delete("/auth/deregister", headers=headers).status_code == 204
    assert sorted(fake_storage.deleted) == sorted(
        path_of(item[key]) for item in (first, second) for key in ("image_url", "song_url")
    )
    # Only the other user's image and song are left.
    assert len(fake_storage.objects) == 2
