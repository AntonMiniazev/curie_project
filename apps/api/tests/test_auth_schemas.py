import pytest
from pydantic import ValidationError

from apps.api.schemas.auth import TokenResponse, UserCreateRequest


def test_user_create_request_accepts_role_field() -> None:
    request = UserCreateRequest(
        email="demo@example.com",
        password="ChangeMe123!",
        role="store_fontaine",
    )

    assert request.role == "store_fontaine"


def test_user_create_request_accepts_selected_role_alias() -> None:
    request = UserCreateRequest(
        email="demo@example.com",
        password="ChangeMe123!",
        selected_role="store_honeybee",
    )

    assert request.role == "store_honeybee"


def test_user_create_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreateRequest(
            email="not-an-email",
            password="ChangeMe123!",
            role="store_fontaine",
        )


def test_token_response_contains_session_tokens() -> None:
    response = TokenResponse(
        access_token="access",
        refresh_token="refresh",
        expires_in_seconds=3600,
    )

    assert response.access_token == "access"
    assert response.refresh_token == "refresh"
    assert response.expires_in_seconds == 3600
