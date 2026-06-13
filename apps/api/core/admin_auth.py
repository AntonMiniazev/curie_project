import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from .config import get_settings


def require_admin_api_key(
    x_curie_admin_key: Annotated[
        str | None,
        Header(alias="X-Curie-Admin-Key"),
    ] = None,
) -> None:
    """Require a valid admin API key for operational endpoints."""
    if x_curie_admin_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key is required.",
        )

    admin_api_keys = get_settings().admin_api_keys
    if not admin_api_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured.",
        )

    if not any(secrets.compare_digest(x_curie_admin_key, key) for key in admin_api_keys):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API key is invalid.",
        )
