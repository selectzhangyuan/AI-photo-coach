from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Photo Coach API"
    env: str = "dev"
    api_prefix: str = "/api/v1"

    db_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/photo_coach"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "photo-images"
    s3_region: str = "us-east-1"

    model_name: str = "mock-vision-v1"
    prompt_version: str = "v1"

    cors_origins: str = (
        "http://localhost:5151,http://127.0.0.1:5151,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )
    default_user_id: str = "00000000-0000-0000-0000-000000000001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
