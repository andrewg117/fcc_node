import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import MediaModel

# Postgres's error code for "user_id points at a user that doesn't exist".
FOREIGN_KEY_VIOLATION = "23503"


class DuplicateMediaError(Exception):
    pass


class MissingUserError(Exception):
    pass


@dataclass(frozen=True)
class MediaRecord:
    id: str
    user_id: str
    title: str
    description: str
    image_path: str
    song_path: str
    created_at: datetime


class MediaUpdate(BaseModel):
    """The fields `update` may change. None means "keep the current value"."""

    title: str | None = None
    description: str | None = None
    image_path: str | None = None
    song_path: str | None = None


def _to_record(model: MediaModel) -> MediaRecord:
    return MediaRecord(
        id=str(model.id),
        user_id=str(model.user_id),
        title=model.title,
        description=model.description,
        image_path=model.image_path,
        song_path=model.song_path,
        created_at=model.created_at,
    )


def _parse_id(value: str) -> uuid.UUID | None:
    """The id as a UUID, or None if it isn't one. A malformed id can't match any row."""
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


class MediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: str,
        title: str,
        description: str,
        image_path: str,
        song_path: str,
    ) -> MediaRecord:
        """Raises MissingUserError if the user doesn't exist."""
        user_uuid = _parse_id(user_id)
        if user_uuid is None:
            raise MissingUserError
        model = MediaModel(
            user_id=user_uuid,
            title=title,
            description=description,
            image_path=image_path,
            song_path=song_path,
        )
        self._session.add(model)
        await self._commit()
        return _to_record(model)

    async def list_for_user(self, user_id: str) -> list[MediaRecord]:
        """An empty list if the user doesn't exist."""
        user_uuid = _parse_id(user_id)
        if user_uuid is None:
            return []
        result = await self._session.execute(
            select(MediaModel)
            .where(MediaModel.user_id == user_uuid)
            .order_by(MediaModel.created_at.desc())
        )
        return [_to_record(model) for model in result.scalars()]

    async def get_by_id(self, media_id: str) -> MediaRecord | None:
        """None if the row doesn't exist."""
        model = await self._get_model(media_id)
        return _to_record(model) if model else None

    async def update(self, media_id: str, changes: MediaUpdate) -> MediaRecord | None:
        """Change only the fields that aren't None. None if the row doesn't exist."""
        model = await self._get_model(media_id)
        if model is None:
            return None
        for field, value in changes.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        await self._commit()
        return _to_record(model)

    async def delete_by_id(self, media_id: str) -> bool:
        """False if the row doesn't exist."""
        media_uuid = _parse_id(media_id)
        if media_uuid is None:
            return False
        result = await self._session.execute(
            delete(MediaModel).where(MediaModel.id == media_uuid).returning(MediaModel.id)
        )
        deleted_id = result.scalar_one_or_none()
        await self._session.commit()
        return deleted_id is not None

    async def _get_model(self, media_id: str) -> MediaModel | None:
        media_uuid = _parse_id(media_id)
        if media_uuid is None:
            return None
        return await self._session.get(MediaModel, media_uuid)

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            # Postgres's error code says which rule the row broke.
            if getattr(error.orig, "sqlstate", None) == FOREIGN_KEY_VIOLATION:
                raise MissingUserError from None
            # Otherwise image_path or song_path is already used by another row.
            raise DuplicateMediaError from None
