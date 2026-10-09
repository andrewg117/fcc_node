"""Runs the real UserRepository against a real Postgres database.

Skipped unless DATABASE_TEST_URL is set, e.g.
    DATABASE_TEST_URL=postgresql+asyncpg://... uv run pytest
Every table is redirected from the fcc_node schema to fcc_node_test, which
is created before the test, and its tables are dropped afterwards. So
DATABASE_TEST_URL may point at the same database as DATABASE_URL without
touching the real fcc_node.users table.
"""

import asyncio
import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.db.models import Base
from backend.repositories.user_repository import DuplicateEmailError, UserRepository

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_TEST_URL"), reason="DATABASE_TEST_URL is not set"
)

TEST_SCHEMA = "fcc_node_test"


def test_repository_round_trip_against_postgres():
    async def scenario() -> None:
        engine = create_async_engine(
            os.environ["DATABASE_TEST_URL"],
            # Every "fcc_node" table becomes "fcc_node_test", for DDL and queries alike.
            # Without this, drop_all below would delete the real fcc_node.users table.
            execution_options={"schema_translate_map": {"fcc_node": TEST_SCHEMA}},
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with engine.begin() as conn:
                # create_all won't make the schema, and raw text() isn't translated.
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
                await conn.run_sync(Base.metadata.create_all)

            async with session_factory() as session:
                users = UserRepository(session)
                created = await users.create("Andrew", "andrew@example.com", "hash")
                assert (await users.get_by_email("andrew@example.com")) == created
                assert (await users.get_by_id(created.id)) == created
                assert await users.get_by_email("nobody@example.com") is None
                assert await users.get_by_id("not-a-uuid") is None

            async with session_factory() as session:
                users = UserRepository(session)
                with pytest.raises(DuplicateEmailError):
                    await users.create("Other", "andrew@example.com", "hash")

            async with session_factory() as session:
                users = UserRepository(session)
                await users.delete_by_id(created.id)

            async with session_factory() as session:
                users = UserRepository(session)
                assert await users.get_by_id(created.id) is None
                assert await users.get_by_email("andrew@example.com") is None
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()

    asyncio.run(scenario())
