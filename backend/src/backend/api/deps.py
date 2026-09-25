from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import HttpError
from backend.core.security import decode_access_token
from backend.repositories.user_repository import UserRecord, UserRepository

# auto_error=False so a missing header reaches our code and produces the same
# {code, type, message} body as every other error, not FastAPI's default {"detail": ...}.
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_user_repository(session: DbSession) -> UserRepository:
    return UserRepository(session)


UserRepo = Annotated[UserRepository, Depends(get_user_repository)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    users: UserRepo,
) -> UserRecord:
    if credentials is None:
        raise HttpError("Not authenticated", 401)

    user = await users.get_by_id(decode_access_token(credentials.credentials))
    if user is None:
        raise HttpError("Not authenticated", 401)
    return user


CurrentUser = Annotated[UserRecord, Depends(get_current_user)]
