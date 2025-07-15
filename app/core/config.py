import os
from typing import Literal

from loguru import logger
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    # Application
    APP_NAME: str = "QRApp Backend"
    APP_VERSION: str = "0.0.0"
    PAGE_SIZE: int = 10
    # Secret
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 60
    ACCESS_KEY: str
    REFRESH_KEY: str
    # FrontEnd
    FRONTEND_HOST: str = "http://localhost:5173"
    # Database
    MONGO_URL: str | None = None
    MONGO_DATABASE: str = "QRApp"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    # Session
    REDIS_URL: str | None = None
    # ADMIN ACOUNT
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    # Logging
    LOG_FILE: str = "./logs/app.log"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"

    @model_validator(mode="after")
    def config_logging(self) -> Self:
        logger.remove()
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        logger.add(
            self.LOG_FILE,
            format="{message}",
            level=self.LOG_LEVEL,
            enqueue=True,
            encoding="utf-8",
            rotation="50 MB",
            retention="7 days",
            compression="zip",
            filter=lambda record: "/ws" not in record["message"] and "WebSocket" not in record["message"],
        )
        return self


settings = Settings()
