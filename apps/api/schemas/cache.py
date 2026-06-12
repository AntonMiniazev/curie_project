# apps/api/schemas/cache.py

from pydantic import BaseModel


class CacheTableStatus(BaseModel):
    name: str
    source_table: str
    path: str
    schema_path: str
    row_count: int
    checksum: str


class CacheStatusResponse(BaseModel):
    configured: bool
    active_release_id: str | None
    tables: list[CacheTableStatus]


class CacheRefreshAcceptedResponse(BaseModel):
    status: str
    message: str
