import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import UserModel


class DuplicateEmailError(Exception):
    pass


@dataclass(frozen=True)
class UserRecord:
    id: str
    name: str
    email: str
    password_hash: str


def _to_record(model: UserModel) -> UserRecord:
    return UserRecord(id=str(model.id), name=model.name, email=model.email, password_hash=model.password_hash)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, email: str, password_hash: str) -> UserRecord:
        model = UserModel(name=name, email=email, password_hash=password_hash)
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise DuplicateEmailError(email) from None
        return _to_record(model)

    async def get_by_email(self, email: str) -> UserRecord | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return _to_record(model) if model else None

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        model = await self._session.get(UserModel, user_uuid)
        return _to_record(model) if model else None
