"""Checks the requests MediaStorage sends to Supabase, using a fake transport."""

import asyncio
import json

import httpx2
import pytest

from backend.core.exceptions import HttpError
from backend.services.media_storage import MediaStorage, StoredObject


def make_storage(handler) -> tuple[MediaStorage, list[httpx2.Request]]:
    sent: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        sent.append(request)
        return handler(request)

    storage = MediaStorage("https://project.supabase.co", "secret", "media", transport=httpx2.MockTransport(record))
    return storage, sent


def test_public_url():
    storage, _ = make_storage(lambda request: httpx2.Response(200))
    assert storage.public_url("1/abc.mp3") == "https://project.supabase.co/storage/v1/object/public/media/1/abc.mp3"


def test_create_upload_url():
    storage, sent = make_storage(
        lambda request: httpx2.Response(200, json={"url": "/object/upload/sign/media/1/abc.mp3?token=xyz"})
    )
    url = asyncio.run(storage.create_upload_url("1/abc.mp3"))
    assert url == "https://project.supabase.co/storage/v1/object/upload/sign/media/1/abc.mp3?token=xyz"
    assert sent[0].method == "POST"
    assert str(sent[0].url) == "https://project.supabase.co/storage/v1/object/upload/sign/media/1/abc.mp3"
    assert sent[0].headers["apikey"] == "secret"
    assert sent[0].headers["authorization"] == "Bearer secret"


def test_get_file_info_reads_type_and_size():
    storage, sent = make_storage(
        lambda request: httpx2.Response(200, headers={"content-type": "audio/mpeg", "content-length": "1234"})
    )
    assert asyncio.run(storage.get_file_info("1/abc.mp3")) == StoredObject(content_type="audio/mpeg", size=1234)
    assert sent[0].method == "HEAD"


@pytest.mark.parametrize("status_code", [400, 404])
def test_get_file_info_returns_none_when_missing(status_code):
    storage, _ = make_storage(lambda request: httpx2.Response(status_code))
    assert asyncio.run(storage.get_file_info("1/abc.mp3")) is None


def test_delete_sends_paths_as_prefixes():
    storage, sent = make_storage(lambda request: httpx2.Response(200, json=[]))
    asyncio.run(storage.delete(["1/a.mp3", "1/b.png"]))
    assert sent[0].method == "DELETE"
    assert str(sent[0].url) == "https://project.supabase.co/storage/v1/object/media"
    assert json.loads(sent[0].content) == {"prefixes": ["1/a.mp3", "1/b.png"]}


def test_delete_nothing_sends_no_request():
    storage, sent = make_storage(lambda request: httpx2.Response(200, json=[]))
    asyncio.run(storage.delete([]))
    assert sent == []


def test_supabase_error_becomes_502():
    storage, _ = make_storage(lambda request: httpx2.Response(500))
    with pytest.raises(HttpError) as exc_info:
        asyncio.run(storage.create_upload_url("1/abc.mp3"))
    assert exc_info.value.status_code == 502


def test_network_error_becomes_502():
    def fail(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no network", request=request)

    storage, _ = make_storage(fail)
    with pytest.raises(HttpError) as exc_info:
        asyncio.run(storage.delete(["1/a.mp3"]))
    assert exc_info.value.status_code == 502
