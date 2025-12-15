from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    PRODUCTION = "production"
    DEV = "development"
    TESTING = "testing"


class Config(BaseSettings):
    """
    Base configuration.
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    API_V1_STR: str = "/api/v1"

    APP_VERSION: str = "0.0.1"
    ENV: AppEnvironment = AppEnvironment.PRODUCTION

    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000

    BACKEND_CORS_ORIGINS: str = ""
    PROJECT_NAME: str = "FastAPI app template"

    SENTRY_ENABLED: bool | None = False
    SENTRY_DSN: str | None = ""
    SENTRY_ENV: str | None = "dev"

    DATABASE_USER: str = "app"
    DATABASE_PASSWORD: str = "password"
    DATABASE_URL: str = "127.0.0.1"
    DATABASE_NAME: str = "app"
    DATABASE_PORT: int = 5432
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    LOGGING_LEVEL: str = "INFO"
    SQL_VERBOSE_LOGGING: bool = False

    # Redis 配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # Email 配置
    EMAIL_MOCK_MODE: bool = True  # 开发模式下使用 Mock

    # 测试配置
    TEST_DATABASE_NAME: str = "tabapi_test"

    @property
    def REDIS_URL(self) -> str:
        """构建 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def is_dev(self) -> bool:
        return self.ENV == AppEnvironment.DEV

    def is_prod(self) -> bool:
        return self.ENV == AppEnvironment.PRODUCTION


settings = Config()
