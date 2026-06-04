from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Photo Coach API"
    env: str = "dev"
    api_prefix: str = "/api/v1"

    db_url: str | None = None
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "photo_coach"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "photo-images"
    s3_region: str = "us-east-1"

    log_level: str = "INFO"
    # 服务层独立级别（开发时可设为 DEBUG 查看 AI 链路细节，不影响全局噪音）
    log_level_services: str = "INFO"

    model_name: str = "mock-vision-v1"
    prompt_version: str = "v1"

    cors_origins: str = (
        "http://localhost:5151,http://127.0.0.1:5151,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    # JWT 认证配置
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @model_validator(mode="after")
    def build_db_url(self) -> "Settings":
        if self.db_url:
            return self

        self.db_url = URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
