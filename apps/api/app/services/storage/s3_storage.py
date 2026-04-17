from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from app.core.config import settings


class S3StorageService:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(connect_timeout=3, read_timeout=8, retries={"max_attempts": 1}),
        )
        self.bucket = settings.s3_bucket

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except (ClientError, BotoCoreError) as exc:
                raise HTTPException(status_code=503, detail="Image storage is unavailable") from exc
        except BotoCoreError as exc:
            raise HTTPException(status_code=503, detail="Image storage is unavailable") from exc

    def upload_bytes(self, object_key: str, content: bytes, content_type: str) -> None:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=content,
                ContentType=content_type,
            )
        except (ClientError, BotoCoreError) as exc:
            raise HTTPException(status_code=503, detail="Image storage is unavailable") from exc

    def download_bytes(self, object_key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response["Body"].read()
        except (ClientError, BotoCoreError) as exc:
            raise HTTPException(status_code=503, detail="Image storage is unavailable") from exc


@lru_cache(maxsize=1)
def get_storage_service() -> S3StorageService:
    service = S3StorageService()
    service.ensure_bucket()
    return service

