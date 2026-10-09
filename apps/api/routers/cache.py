"""Flight SQL serving-cache controls and temporary Airflow URL aliases."""

import json
from json import JSONDecodeError
from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, HTTPException, status

from ..cache.job_trigger import _find_running_refresh_job_id, trigger_cache_refresh_job
from ..core.admin_auth import require_admin_api_key
from ..core.config import get_settings
from ..schemas.cache import (
    CacheRefreshAcceptedResponse,
    FlightCacheStatusResponse,
    FlightDatasetStatus,
)

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/status_flightsql", response_model=FlightCacheStatusResponse)
@router.get("/status", response_model=FlightCacheStatusResponse, deprecated=True)
@router.get("/status_iceberg", response_model=FlightCacheStatusResponse, deprecated=True)
def get_flightsql_cache_status() -> FlightCacheStatusResponse:
    """Report the active DuckDB release, including for the older Airflow URLs."""
    settings = get_settings()
    state_path = settings.serving_cache_root / "status.json"
    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail="Flight SQL cache status is invalid") from exc
    try:
        job_id = _find_running_refresh_job_id() if settings.cache_refresh_enabled else None
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    release_id = release_time = None
    tables: list[FlightDatasetStatus] = []
    if settings.serving_cache_current.exists():
        try:
            with duckdb.connect(str(settings.serving_cache_current), read_only=True) as con:
                release_id, release_time = con.execute(
                    "SELECT release_id, created_at_utc FROM curie_release"
                ).fetchone()
                tables = [
                    FlightDatasetStatus(
                        name=row[0], row_count=row[1],
                        date_min=str(row[2]) if row[2] is not None else None,
                        date_max=str(row[3]) if row[3] is not None else None,
                    )
                    for row in con.execute(
                        "SELECT name, row_count, date_min, date_max "
                        "FROM curie_datasets ORDER BY name"
                    ).fetchall()
                ]
        except (duckdb.Error, OSError, TypeError) as exc:
            raise HTTPException(status_code=500, detail="Active Flight SQL cache is invalid") from exc

    reported_state = state.get("state")
    if reported_state == "running" and not job_id:
        reported_state = "interrupted"
    return FlightCacheStatusResponse(
        configured=bool(
            settings.flightsql_uri
            and settings.flightsql_auth_token
            and settings.flightsql_auth_token.get_secret_value()
        ),
        running=bool(job_id), job_id=job_id, state=reported_state,
        last_failure=state.get("last_failure"),
        active_release_id=release_id,
        active_release_timestamp=release_time,
        tables=tables,
    )


@router.post(
    "/refresh_flightsql", response_model=CacheRefreshAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@router.post(
    "/refresh", response_model=CacheRefreshAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED, deprecated=True,
)
@router.post(
    "/refresh_iceberg", response_model=CacheRefreshAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED, deprecated=True,
)
def refresh_flightsql_cache_endpoint(
    _: Annotated[None, Depends(require_admin_api_key)],
) -> CacheRefreshAcceptedResponse:
    """Start a Flight SQL refresh even when Airflow calls an older URL."""
    try:
        job_id = trigger_cache_refresh_job()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CacheRefreshAcceptedResponse(
        status="accepted",
        message=f"Flight SQL cache refresh job started: {job_id}",
        job_id=job_id,
    )
