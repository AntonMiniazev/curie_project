from fastapi import APIRouter, status
from ..schemas.meta import MetaResponse

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get(
    "/capabilities",
    response_model=MetaResponse,
    status_code=status.HTTP_200_OK,
)
def get_capabilities() -> MetaResponse:
    return MetaResponse(
        app="curie",
        environment="dev",
        features=["reports", "cache"],
    )
