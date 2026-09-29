"""Runs the real UserRepository against a real Postgres database.

Skipped unless DATABASE_TEST_URL is set, e.g.
    DATABASE_TEST_URL=postgresql+asyncpg://... uv run pytest
Creates the users table before the test and drops it afterwards, so
DATABASE_TEST_URL must point at a throwaway database, never a real one.
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


def test_repository_round_trip_against_postgres():
    async def scenario() -> None:
        engine = create_async_engine(os.environ["DATABASE_TEST_URL"])
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with engine.begin() as conn:
                # A fresh database has no fcc_node schema, and create_all won't make one.
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS fcc_node"))
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
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()

    asyncio.run(scenario())
