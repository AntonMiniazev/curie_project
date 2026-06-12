import json
from json import JSONDecodeError
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from ..cache.refresh import refresh_all_tables
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
    background_tasks: BackgroundTasks,
) -> CacheRefreshAcceptedResponse:
    background_tasks.add_task(refresh_all_tables)

    return CacheRefreshAcceptedResponse(
        status="accepted",
        message="Cache refresh started in the API background task runner.",
    )
