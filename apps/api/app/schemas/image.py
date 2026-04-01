from uuid import UUID

from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    image_id: UUID
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    object_key: str

