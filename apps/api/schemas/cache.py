# apps/api/schemas/cache.py

from pydantic import BaseModel, Field


class CacheRefreshAcceptedResponse(BaseModel):
    status: str
    message: str
    job_id: str | None = None


class FlightDatasetStatus(BaseModel):
    name: str
    row_count: int
    date_min: str | None = None
    date_max: str | None = None
    checksum: str | None = None  # Legacy Airflow logs this field.


class FlightCacheStatusResponse(BaseModel):
    configured: bool
    running: bool
    job_id: str | None = None
    state: str | None = None
    last_failure: str | None = None
    active_release_id: str | None = None
    active_release_timestamp: str | None = None
    tables: list[FlightDatasetStatus] = Field(default_factory=list)
