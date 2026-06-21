"""Environment-driven settings for Streamlit reporting apps.

The reporting process reads only Curie's local cache directory. Local
development uses `data/dev-cache/current`; Docker/production should override it
with `CURIE_CACHE_CURRENT`.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


def _default_cache_current() -> Path:
    """Return the repo-local cache path used by Windows/root-venv development."""
    return REPO_ROOT / "data" / "dev-cache" / "current"


class StreamlitSettings(BaseSettings):
    """Runtime paths for cache-backed Streamlit dashboards."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / "infra" / "env" / "curie-dev.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cache_current: Path = Field(
        default_factory=_default_cache_current,
        validation_alias="CURIE_CACHE_CURRENT",
    )
    jwt_secret_key: SecretStr = Field(validation_alias="CURIE_JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="CURIE_JWT_ALGORITHM")

    @computed_field
    @property
    def manifest_path(self) -> Path:
        return self.cache_current / "manifest.json"

    @computed_field
    @property
    def data_dir(self) -> Path:
        return self.cache_current / "data"

    @computed_field
    @property
    def schemas_dir(self) -> Path:
        return self.cache_current / "schemas"


@lru_cache
def get_settings() -> StreamlitSettings:
    """Return process-wide settings; env vars are read once per Streamlit process."""
    return StreamlitSettings()
