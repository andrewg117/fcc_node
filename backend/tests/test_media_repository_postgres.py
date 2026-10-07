"""Runs the real MediaRepository against a real Postgres database.

Skipped unless DATABASE_TEST_URL is set. Like test_user_repository_postgres.py,
every table is redirected from the fcc_node schema to fcc_node_test, so the
real fcc_node tables are never touched.
"""

import asyncio
import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.db.models import Base
from backend.repositories.media_repository import (
    DuplicateMediaError,
    MediaRepository,
    MediaUpdate,
    MissingUserError,
)
from backend.repositories.user_repository import UserRepository

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_TEST_URL"), reason="DATABASE_TEST_URL is not set"
)

TEST_SCHEMA = "fcc_node_test"


def test_media_repository_round_trip_against_postgres():
    async def scenario() -> None:
        engine = create_async_engine(
            os.environ["DATABASE_TEST_URL"],
            # Every "fcc_node" table becomes "fcc_node_test", for DDL and queries alike.
            # Without this, drop_all below would delete the real fcc_node tables.
            execution_options={"schema_translate_map": {"fcc_node": TEST_SCHEMA}},
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
                await conn.run_sync(Base.metadata.create_all)

            async with session_factory() as session:
                user = await UserRepository(session).create("Andrew", "andrew@example.com", "hash")
                media = MediaRepository(session)
                first = await media.create(user.id, "First", "", f"{user.id}/a.png", f"{user.id}/a.mp3")
                second = await media.create(user.id, "Second", "Notes", f"{user.id}/b.png", f"{user.id}/b.mp3")
                assert await media.list_for_user(user.id) == [second, first]
                assert await media.get_by_id(first.id) == first

            # Missing rows: every method handles an unknown id and a malformed one.
            async with session_factory() as session:
                media = MediaRepository(session)
                for missing in (str(uuid.uuid4()), "not-a-uuid"):
                    assert await media.list_for_user(missing) == []
                    assert await media.get_by_id(missing) is None
                    assert await media.update(missing, MediaUpdate(title="Nobody")) is None
                    assert await media.delete_by_id(missing) is False
                    # For create, the missing row is the user (the user_id foreign key).
                    with pytest.raises(MissingUserError):
                        await media.create(missing, "Orphan", "", f"{missing}/o.png", f"{missing}/o.mp3")

            # A file can only belong to one row.
            async with session_factory() as session:
                with pytest.raises(DuplicateMediaError):
                    await MediaRepository(session).create(
                        user.id, "Copy", "", f"{user.id}/a.png", f"{user.id}/c.mp3"
                    )

            # update changes only the fields that are passed.
            async with session_factory() as session:
                media = MediaRepository(session)
                updated = await media.update(
                    first.id, MediaUpdate(title="Renamed", image_path=f"{user.id}/c.png")
                )
                assert updated is not None
                assert (updated.title, updated.description) == ("Renamed", "")
                assert (updated.image_path, updated.song_path) == (f"{user.id}/c.png", f"{user.id}/a.mp3")
                assert await media.get_by_id(first.id) == updated

            async with session_factory() as session:
                with pytest.raises(DuplicateMediaError):
                    await MediaRepository(session).update(first.id, MediaUpdate(song_path=f"{user.id}/b.mp3"))

            async with session_factory() as session:
                media = MediaRepository(session)
                assert await media.delete_by_id(first.id) is True
                assert await media.list_for_user(user.id) == [second]
                # Deleting it again finds nothing.
                assert await media.delete_by_id(first.id) is False

            # Deleting the user deletes their remaining media rows (ON DELETE CASCADE).
            async with session_factory() as session:
                await UserRepository(session).delete_by_id(user.id)
                assert await MediaRepository(session).get_by_id(second.id) is None
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()

    asyncio.run(scenario())
