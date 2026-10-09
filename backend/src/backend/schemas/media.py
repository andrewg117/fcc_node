from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from backend.core.media_types import MediaKind

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class UploadRequest(BaseModel):
    kind: MediaKind
    content_type: str
    size: int = Field(gt=0)


class UploadResponse(BaseModel):
    path: str
    upload_url: str


class CreateMediaRequest(BaseModel):
    title: Title
    description: Description = ""
    image_path: str
    song_path: str


class UpdateMediaRequest(BaseModel):
    # None (or left out) means "keep the current value".
    title: Title | None = None
    description: Description | None = None
    image_path: str | None = None
    song_path: str | None = None


class MediaPublic(BaseModel):
    id: str
    title: str
    description: str
    image_url: str
    song_url: str
    created_at: datetime
