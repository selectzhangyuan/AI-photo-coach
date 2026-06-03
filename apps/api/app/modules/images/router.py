import hashlib
import logging
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user_id
from app.models.image_asset import ImageAsset
from app.schemas.image import ImageUploadResponse
from app.services.storage.s3_storage import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ImageUploadResponse:
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        image = Image.open(BytesIO(content))
        width, height = image.size
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc


    extension = Path(file.filename or "").suffix.lower()
    if not extension:
        extension = ".jpg"

    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    object_key = f"{user_id}/{date_part}/{uuid.uuid4().hex}{extension}"
    sha256 = hashlib.sha256(content).hexdigest()

    storage = get_storage_service()
    storage.upload_bytes(object_key=object_key, content=content, content_type=file.content_type)

    image_asset = ImageAsset(
        user_id=user_id,
        parent_image_id=None,
        asset_type="original",
        storage_provider="minio",
        bucket=storage.bucket,
        object_key=object_key,
        mime_type=file.content_type,
        size_bytes=len(content),
        width=width,
        height=height,
        sha256=sha256,
        exif_json=None,
    )
    db.add(image_asset)
    db.commit()
    db.refresh(image_asset)

    logger.info(
        "Image uploaded",
        extra={
            "image_id": str(image_asset.id),
            "user_id": str(user_id),
            "size_bytes": image_asset.size_bytes,
            "mime_type": image_asset.mime_type,
            "width": image_asset.width,
            "height": image_asset.height,
        },
    )

    return ImageUploadResponse(
        image_id=image_asset.id,
        mime_type=image_asset.mime_type,
        size_bytes=image_asset.size_bytes,
        width=image_asset.width,
        height=image_asset.height,
        object_key=image_asset.object_key,
    )
