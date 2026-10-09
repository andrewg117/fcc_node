import re
import uuid

from fastapi import APIRouter, status

from backend.api.deps import CurrentUser, MediaRepo, Storage
from backend.core.exceptions import HttpError
from backend.core.media_types import MediaKind, check_file, extensions
from backend.repositories.media_repository import (
    DuplicateMediaError,
    MediaRecord,
    MediaRepository,
    MediaUpdate,
    MissingUserError,
)
from backend.schemas.media import (
    CreateMediaRequest,
    MediaPublic,
    UpdateMediaRequest,
    UploadRequest,
    UploadResponse,
)
from backend.services.media_storage import MediaStorage

router = APIRouter(prefix="/media")


def to_public(item: MediaRecord, storage: MediaStorage) -> MediaPublic:
    return MediaPublic(
        id=item.id,
        title=item.title,
        description=item.description,
        image_url=storage.public_url(item.image_path),
        song_url=storage.public_url(item.song_path),
        created_at=item.created_at,
    )


async def delete_quietly(storage: MediaStorage, paths: list[str]) -> None:
    """Delete files nothing uses any more. If it fails, a file is left behind, which only wastes space."""
    try:
        await storage.delete(paths)
    except HttpError:
        pass


async def check_upload(path: str, kind: MediaKind, user_id: str, storage: MediaStorage) -> None:
    """Make sure `path` is a finished upload of the right kind that start_upload made for this user."""
    # <user id>/<32 hex characters>.<an extension of this kind>, exactly as start_upload builds it.
    # The extension check means an image path can't be sent as a song, or a song path as an image.
    allowed_extensions = "|".join(sorted(extensions(kind)))
    if not re.fullmatch(rf"{re.escape(user_id)}/[0-9a-f]{{32}}\.({allowed_extensions})", path):
        raise HttpError("Invalid upload path", 400)

    stored = await storage.get_file_info(path)
    if stored is None:
        raise HttpError("Upload not found", 400)
    try:
        check_file(kind, stored.content_type, stored.size)
    except HttpError:
        # The file that arrived isn't what the browser promised. Remove it so it doesn't use up storage.
        await storage.delete([path])
        raise


async def get_own_item(media_id: str, user_id: str, media: MediaRepository) -> MediaRecord:
    item = await media.get_by_id(media_id)
    # Same 404 for "doesn't exist" and "someone else's", so ids can't be probed.
    if item is None or item.user_id != user_id:
        raise HttpError("Media not found", 404)
    return item


# "" rather than "/", so the URL is /media. With "/", a request to /media
# would get a redirect to /media/, and a redirected request loses its Authorization header.
@router.get("")
async def list_media(user: CurrentUser, media: MediaRepo, storage: Storage) -> list[MediaPublic]:
    return [to_public(item, storage) for item in await media.list_for_user(user.id)]


@router.post("/uploads")
async def start_upload(body: UploadRequest, user: CurrentUser, storage: Storage) -> UploadResponse:
    # Checks what the browser says about the file. The real file is checked again in check_upload.
    extension = check_file(body.kind, body.content_type, body.size)
    # A random name, so two uploads never collide and nobody can guess another file's URL.
    path = f"{user.id}/{uuid.uuid4().hex}.{extension}"
    return UploadResponse(path=path, upload_url=await storage.create_upload_url(path))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_media(body: CreateMediaRequest, user: CurrentUser, media: MediaRepo, storage: Storage) -> MediaPublic:
    await check_upload(body.image_path, "image", user.id, storage)
    await check_upload(body.song_path, "audio", user.id, storage)
    try:
        item = await media.create(user.id, body.title, body.description, body.image_path, body.song_path)
    except DuplicateMediaError:
        raise HttpError("Upload already saved", 409) from None
    except MissingUserError:
        # The account was deleted while this request ran. Nothing will ever use these files now.
        await delete_quietly(storage, [body.image_path, body.song_path])
        raise HttpError("Not authenticated", 401) from None
    return to_public(item, storage)


@router.patch("/{media_id}")
async def update_media(
    media_id: str, body: UpdateMediaRequest, user: CurrentUser, media: MediaRepo, storage: Storage
) -> MediaPublic:
    item = await get_own_item(media_id, user.id, media)
    new_image = body.image_path if body.image_path not in (None, item.image_path) else None
    new_song = body.song_path if body.song_path not in (None, item.song_path) else None
    if new_image:
        await check_upload(new_image, "image", user.id, storage)
    if new_song:
        await check_upload(new_song, "audio", user.id, storage)

    try:
        updated = await media.update(
            item.id,
            MediaUpdate(title=body.title, description=body.description, image_path=new_image, song_path=new_song),
        )
    except DuplicateMediaError:
        raise HttpError("Upload already saved", 409) from None
    if updated is None:
        # Another request deleted the upload after get_own_item found it.
        # The new files are left alone: one could be a file another upload uses.
        raise HttpError("Media not found", 404)

    # Delete the replaced files only now that the row points at the new ones.
    # The update is already saved, so a failed delete isn't reported.
    replaced = [old for old, new in ((item.image_path, new_image), (item.song_path, new_song)) if new]
    await delete_quietly(storage, replaced)
    return to_public(updated, storage)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: str, user: CurrentUser, media: MediaRepo, storage: Storage) -> None:
    item = await get_own_item(media_id, user.id, media)
    # Files first: if storage fails, nothing has changed and the user can retry.
    await storage.delete([item.image_path, item.song_path])
    if not await media.delete_by_id(item.id):
        # Another request deleted the row after get_own_item found it.
        raise HttpError("Media not found", 404)
