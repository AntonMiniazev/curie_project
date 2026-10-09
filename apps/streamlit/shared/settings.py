"""Runtime settings for the DuckDB-backed Streamlit reports."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class StreamlitSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / "infra" / "env" / "curie-dev.env",
        env_file_encoding="utf-8", extra="ignore",
    )

    serving_cache_current: Path = Field(
        default=REPO_ROOT / "data" / "dev-serving-cache" / "current",
        validation_alias="CURIE_SERVING_CACHE_CURRENT",
    )
    app_env: str = Field(default="prod", validation_alias="APP_ENV")
    jwt_secret_key: SecretStr = Field(validation_alias="CURIE_JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="CURIE_JWT_ALGORITHM")
    auth_access_cookie_name: str = Field(
        default="curie_access_token",
        validation_alias="CURIE_AUTH_ACCESS_COOKIE_NAME",
    )


@lru_cache
def get_settings() -> StreamlitSettings:
    return StreamlitSettings()
