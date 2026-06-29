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
        default=2,
        alias="CURIE_DATABASE_CONNECT_TIMEOUT_SECONDS",
    )
    database_statement_timeout_ms: int = Field(
        default=15000,
        alias="CURIE_DATABASE_STATEMENT_TIMEOUT_MS",
    )
    database_pool_timeout_seconds: int = Field(
        default=2,
        alias="CURIE_DATABASE_POOL_TIMEOUT_SECONDS",
    )
    curie_password_pepper: SecretStr = Field(alias="CURIE_PASSWORD_PEPPER")
    jwt_secret_key: SecretStr = Field(alias="CURIE_JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="CURIE_JWT_ALGORITHM")
    access_token_minutes: int = Field(default=60, alias="CURIE_ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=14, alias="CURIE_REFRESH_TOKEN_DAYS")
    auth_access_cookie_name: str = Field(
        default="curie_access_token",
        alias="CURIE_AUTH_ACCESS_COOKIE_NAME",
    )
    auth_refresh_cookie_name: str = Field(
        default="curie_refresh_token",
        alias="CURIE_AUTH_REFRESH_COOKIE_NAME",
    )
    auth_cookie_secure: bool = Field(default=False, alias="CURIE_AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="CURIE_AUTH_COOKIE_SAMESITE")
    admin_api_keys_csv: SecretStr | None = Field(
        default=None,
        alias="CURIE_ADMIN_API_KEYS",
    )
    cors_origins_csv: str = Field(default="", alias="CURIE_CORS_ORIGINS")

    uc_base_url: str = Field(default="http://ucatalog.local", alias="CURIE_UC_BASE_URL")
    uc_timeout_seconds: int = Field(default=10, alias="CURIE_UC_TIMEOUT_SECONDS")
    uc_retry_attempts: int = Field(default=5, alias="CURIE_UC_RETRY_ATTEMPTS")
    uc_retry_backoff_seconds: int = Field(
        default=5,
        alias="CURIE_UC_RETRY_BACKOFF_SECONDS",
    )

    source_catalog: str = Field(default="ampere", alias="CURIE_SOURCE_CATALOG")
    source_schema: str = Field(default="gold", alias="CURIE_SOURCE_SCHEMA")
    source_tables_csv: str = Field(
        default=(
            "dim_clients,"
            "dim_costing,"
            "dim_delivery_cost,"
            "dim_products,"
            "dim_resource,"
            "dim_stores,"
            "fct_deliveries,"
            "fct_order_margin,"
            "fct_orders_sales,"
            "budget_orders_sales,"
            "fct_order_product"
        ),
        alias="CURIE_SOURCE_TABLES",
    )

    minio_endpoint: str = Field(
        default="https://s3.minio.local", alias="CURIE_MINIO_ENDPOINT"
    )
    minio_region: str = Field(default="us-east-1", alias="CURIE_MINIO_REGION")
    minio_access_key: SecretStr | None = Field(
        default=None, alias="CURIE_MINIO_ACCESS_KEY"
    )
    minio_secret_key: SecretStr | None = Field(
        default=None, alias="CURIE_MINIO_SECRET_KEY"
    )
    minio_allow_invalid_certificates: bool = Field(
        default=True,
        alias="CURIE_MINIO_ALLOW_INVALID_CERTIFICATES",
    )

    cache_root: Path = Field(
        default=REPO_ROOT / "data" / "dev-cache", alias="CURIE_CACHE_ROOT"
    )
    cache_current: Path = Field(
        default=REPO_ROOT / "data" / "dev-cache" / "current",
        alias="CURIE_CACHE_CURRENT",
    )
    cache_refresh_enabled: bool = Field(
        default=False, alias="CURIE_CACHE_REFRESH_ENABLED"
    )
    cache_refresh_image: str = Field(
        default="ghcr.io/antonminiazev/curie-api:latest",
        alias="CURIE_CACHE_REFRESH_IMAGE",
    )
    cache_refresh_host_cache_dir: str = Field(
        default=str(REPO_ROOT / "data" / "dev-cache"),
        alias="CURIE_CACHE_REFRESH_HOST_CACHE_DIR",
    )
    cache_refresh_volumes_from: str | None = Field(
        default=None, alias="CURIE_CACHE_REFRESH_VOLUMES_FROM"
    )
    cache_refresh_container_prefix: str = Field(
        default="curie-cache-refresh",
        alias="CURIE_CACHE_REFRESH_CONTAINER_PREFIX",
    )
    cache_refresh_network: str | None = Field(
        default=None, alias="CURIE_CACHE_REFRESH_NETWORK"
    )
    upstream_host_ip: str | None = Field(default=None, alias="CURIE_UPSTREAM_HOST_IP")
    cache_refresh_extra_hosts_csv: str = Field(
        default="", alias="CURIE_CACHE_REFRESH_EXTRA_HOSTS"
    )

    @property
    def source_tables(self) -> list[str]:
        return [
            item.strip() for item in self.source_tables_csv.split(",") if item.strip()
        ]

    @property
    def cache_refresh_extra_hosts(self) -> list[str]:
        explicit_hosts = [
            item.strip()
            for item in self.cache_refresh_extra_hosts_csv.split(",")
            if item.strip()
        ]
        if explicit_hosts:
            return explicit_hosts
        if self.upstream_host_ip:
            return [
                f"ucatalog.local:{self.upstream_host_ip}",
                f"s3.minio.local:{self.upstream_host_ip}",
                f"minio.local:{self.upstream_host_ip}",
            ]
        return []

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

    @property
    def has_minio_credentials(self) -> bool:
        return bool(self.minio_access_key and self.minio_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
