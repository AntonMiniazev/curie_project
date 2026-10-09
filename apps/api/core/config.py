"""Curie API runtime settings for auth and the Flight SQL serving cache."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / "infra" / "env" / "curie-dev.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    database_url: str = Field(alias="CURIE_DATABASE_URL")
    database_connect_timeout_seconds: int = Field(
        default=2, alias="CURIE_DATABASE_CONNECT_TIMEOUT_SECONDS"
    )
    database_statement_timeout_ms: int = Field(
        default=15000, alias="CURIE_DATABASE_STATEMENT_TIMEOUT_MS"
    )
    database_pool_timeout_seconds: int = Field(
        default=2, alias="CURIE_DATABASE_POOL_TIMEOUT_SECONDS"
    )
    curie_password_pepper: SecretStr = Field(alias="CURIE_PASSWORD_PEPPER")
    jwt_secret_key: SecretStr = Field(alias="CURIE_JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="CURIE_JWT_ALGORITHM")
    access_token_minutes: int = Field(default=60, alias="CURIE_ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=14, alias="CURIE_REFRESH_TOKEN_DAYS")
    auth_access_cookie_name: str = Field(
        default="curie_access_token", alias="CURIE_AUTH_ACCESS_COOKIE_NAME"
    )
    auth_refresh_cookie_name: str = Field(
        default="curie_refresh_token", alias="CURIE_AUTH_REFRESH_COOKIE_NAME"
    )
    auth_cookie_secure: bool = Field(default=False, alias="CURIE_AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="CURIE_AUTH_COOKIE_SAMESITE")
    admin_api_keys_csv: SecretStr | None = Field(
        default=None, alias="CURIE_ADMIN_API_KEYS"
    )
    cors_origins_csv: str = Field(default="", alias="CURIE_CORS_ORIGINS")

    flightsql_uri: str | None = Field(default=None, alias="CURIE_FLIGHTSQL_URI")
    flightsql_auth_token: SecretStr | None = Field(
        default=None, alias="CURIE_FLIGHTSQL_AUTH_TOKEN"
    )
    flightsql_timeout_seconds: int = Field(
        default=30, ge=1, alias="CURIE_FLIGHTSQL_TIMEOUT_SECONDS"
    )
    flightsql_fetch_timeout_seconds: int = Field(
        default=300, ge=1, alias="CURIE_FLIGHTSQL_FETCH_TIMEOUT_SECONDS"
    )
    serving_cache_root: Path = Field(
        default=REPO_ROOT / "data" / "dev-serving-cache",
        alias="CURIE_SERVING_CACHE_ROOT",
    )
    serving_cache_current: Path = Field(
        default=REPO_ROOT / "data" / "dev-serving-cache" / "current",
        alias="CURIE_SERVING_CACHE_CURRENT",
    )
    serving_cache_keep_previous: int = Field(
        default=3, ge=0, alias="CURIE_SERVING_CACHE_KEEP_PREVIOUS"
    )
    serving_refresh_container_prefix: str = Field(
        default="curie-flightsql-cache-refresh",
        alias="CURIE_SERVING_REFRESH_CONTAINER_PREFIX",
    )
    serving_host_cache_dir: str = Field(
        default="/var/lib/curie/serving-cache",
        alias="CURIE_SERVING_HOST_CACHE_DIR",
    )
    cache_refresh_enabled: bool = Field(
        default=False, alias="CURIE_CACHE_REFRESH_ENABLED"
    )
    cache_refresh_image: str = Field(
        default="ghcr.io/antonminiazev/curie-api:latest",
        alias="CURIE_CACHE_REFRESH_IMAGE",
    )
    cache_refresh_network: str | None = Field(
        default=None, alias="CURIE_CACHE_REFRESH_NETWORK"
    )

    @property
    def admin_api_keys(self) -> list[str]:
        if self.admin_api_keys_csv is None:
            return []
        return [
            item.strip()
            for item in self.admin_api_keys_csv.get_secret_value().split(",")
            if item.strip()
        ]

    @property
    def cors_origins(self) -> list[str]:
        return [
            item.strip() for item in self.cors_origins_csv.split(",") if item.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
