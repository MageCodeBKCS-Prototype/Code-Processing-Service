from typing import Any

from pydantic import RedisDsn, MariaDBDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.constants import Environment


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    DATABASE_URL: MariaDBDsn
    REDIS_URL: RedisDsn
    RAILS_API_LOGIN_URL: str
    RAILS_API_EMAIL: str
    RAILS_API_PASSWORD: str
    COLLECT_CODEQL_RESULT_URL: str

    SITE_DOMAIN: str = "magecode.com"

    ENVIRONMENT: Environment = Environment.PRODUCTION

    SENTRY_DSN: str | None = None

    CORS_ORIGINS: list[str]
    CORS_ORIGINS_REGEX: str | None = None
    CORS_HEADERS: list[str]

    APP_VERSION: str = "1"

    MODEL_NAME: str
    MODEL_PATH: str


settings = Config()

app_configs: dict[str, Any] = {"title": "MageCode Code Processing API"}
if settings.ENVIRONMENT.is_deployed:
    app_configs["root_path"] = f"/api/v{settings.APP_VERSION}"

if not settings.ENVIRONMENT.is_debug:
    # hide docs
    app_configs["openapi_url"] = None
