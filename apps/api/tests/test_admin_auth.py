from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status

from apps.api.core import admin_auth


def test_require_admin_api_key_rejects_missing_key() -> None:
    with pytest.raises(HTTPException) as exc_info:
        admin_auth.require_admin_api_key()

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_require_admin_api_key_rejects_wrong_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        admin_auth,
        "get_settings",
        lambda: SimpleNamespace(admin_api_keys=["expected-key"]),
    )

    with pytest.raises(HTTPException) as exc_info:
        admin_auth.require_admin_api_key("wrong-key")

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_admin_api_key_rejects_unconfigured_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        admin_auth,
        "get_settings",
        lambda: SimpleNamespace(admin_api_keys=[]),
    )

    with pytest.raises(HTTPException) as exc_info:
        admin_auth.require_admin_api_key("any-key")

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_require_admin_api_key_accepts_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        admin_auth,
        "get_settings",
        lambda: SimpleNamespace(admin_api_keys=["expected-key"]),
    )

    assert admin_auth.require_admin_api_key("expected-key") is None
