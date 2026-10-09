from typing import Literal

from backend.core.exceptions import HttpError

MediaKind = Literal["image", "audio"]

MB = 1024 * 1024

# For each kind: content type -> file extension used in the storage path.
ALLOWED_TYPES: dict[MediaKind, dict[str, str]] = {
    "image": {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    },
    "audio": {
        "audio/mpeg": "mp3",
        # Some browsers report MP3 files as audio/mp3 instead of audio/mpeg.
        "audio/mp3": "mp3",
        "audio/mp4": "m4a",
        "audio/x-m4a": "m4a",
        "audio/aac": "aac",
        "audio/ogg": "ogg",
    },
}

MAX_BYTES: dict[MediaKind, int] = {"image": 10 * MB, "audio": 30 * MB}

# What the user calls each kind, for error messages.
LABELS: dict[MediaKind, str] = {"image": "Image", "audio": "Song"}

TYPE_NAMES: dict[MediaKind, str] = {"image": "a JPEG, PNG, WebP or GIF", "audio": "an MP3, M4A, AAC or OGG"}


def extensions(kind: MediaKind) -> set[str]:
    return set(ALLOWED_TYPES[kind].values())


def check_file(kind: MediaKind, content_type: str, size: int) -> str:
    """Return the file extension for an allowed file of this kind, or raise a 400 HttpError."""
    extension = ALLOWED_TYPES[kind].get(content_type)
    if extension is None:
        raise HttpError(f"{LABELS[kind]} must be {TYPE_NAMES[kind]} file", 400)
    if size <= 0:
        raise HttpError(f"{LABELS[kind]} file is empty", 400)
    if size > MAX_BYTES[kind]:
        raise HttpError(f"{LABELS[kind]} must be {MAX_BYTES[kind] // MB} MB or smaller", 400)
    return extension
