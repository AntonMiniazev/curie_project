import json
from json import JSONDecodeError
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from ..cache.job_trigger import trigger_cache_refresh_job
from ..core.config import get_settings
from ..schemas.cache import CacheRefreshAcceptedResponse, CacheStatusResponse

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get(
    "/status", response_model=CacheStatusResponse, status_code=status.HTTP_200_OK
)
def get_cache_status() -> CacheStatusResponse:
    settings = get_settings()
    manifest_path = Path(settings.cache_current) / "manifest.json"

    if not manifest_path.exists():
        return CacheStatusResponse(
            configured=False,
            active_release_id=None,
            tables=[],
        )

    try:
        with manifest_path.open(encoding="utf-8") as file:
            manifest_data = json.load(file)
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache manifest is not valid JSON.",
        ) from exc

    return CacheStatusResponse(
        configured=True,
        active_release_id=manifest_data.get("release_id"),
        tables=manifest_data.get("tables", []),
    )


@router.post(
    "/refresh",
    response_model=CacheRefreshAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def refresh_cache_endpoint(
) -> CacheRefreshAcceptedResponse:
    try:
        job_id = trigger_cache_refresh_job()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return CacheRefreshAcceptedResponse(
        status="accepted",
        message=f"Cache refresh job started: {job_id}",
        job_id=job_id,
    )
