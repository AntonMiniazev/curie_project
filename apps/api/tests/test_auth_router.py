from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import SQLAlchemyError

from apps.api.db.models import RefreshToken, Role, User
from apps.api.routers.auth import (
    get_available_roles,
    get_current_user,
    login_user,
    logout_user,
    nginx_streamlit_auth,
    refresh_access_token,
    register_user,
)
from apps.api.schemas.auth import LogoutRequest, RefreshTokenRequest, UserCreateRequest, UserLoginRequest
from apps.api.core.config import get_settings
from apps.api.core.security import decode_access_token


@dataclass
class FakeSession:
    users: list[User] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    refresh_tokens: list[RefreshToken] = field(default_factory=list)
    commits: int = 0
    rollbacks: int = 0

    def query(self, model: type[Any]) -> FakeQuery:
        return FakeQuery(self, model)

    def add(self, item: Any) -> None:
        if isinstance(item, User):
            if item.id is None:
                item.id = uuid4()
            if item.is_active is None:
                item.is_active = True
            if item.is_verified is None:
                item.is_verified = False
            if item not in self.users:
                self.users.append(item)
            return

        if isinstance(item, RefreshToken):
            if item.id is None:
                item.id = uuid4()
            user = self.get_user_by_id(item.user_id)
            if user is not None:
                item.user = user
            if item not in self.refresh_tokens:
                self.refresh_tokens.append(item)
            return

        raise TypeError(f"Unsupported fake session item: {type(item)!r}")

    def flush(self) -> None:
        for user in self.users:
            if user.id is None:
                user.id = uuid4()

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def get_user_by_id(self, user_id: UUID) -> User | None:
        for user in self.users:
            if user.id == user_id:
                return user
        return None


class FakeQuery:
    def __init__(self, session: FakeSession, model: type[Any]) -> None:
        self.session = session
        self.model = model
        self.filters: list[tuple[str, Any]] = []
        self.order_key: str | None = None

    def filter(self, expression: Any) -> FakeQuery:
        left = getattr(expression, "left")
        right = getattr(expression, "right")
        self.filters.append((left.key, right.value))
        return self

    def order_by(self, expression: Any) -> FakeQuery:
        self.order_key = expression.key
        return self

    def all(self) -> list[Any]:
        items = self._items()
        if self.order_key is not None:
            items = sorted(items, key=lambda item: getattr(item, self.order_key))
        return items

    def one_or_none(self) -> Any | None:
        items = self._items()
        if len(items) > 1:
            raise AssertionError("Fake query expected at most one result.")
        return items[0] if items else None

    def count(self) -> int:
        return len(self._items())

    def _items(self) -> list[Any]:
        if self.model is User:
            items: list[Any] = list(self.session.users)
        elif self.model is Role:
            items = list(self.session.roles)
        elif self.model is RefreshToken:
            items = list(self.session.refresh_tokens)
        else:
            raise TypeError(f"Unsupported fake query model: {self.model!r}")

        for key, value in self.filters:
            items = [item for item in items if getattr(item, key) == value]
        return items


class BrokenSession:
    def query(self, model: type[Any]) -> Any:
        raise SQLAlchemyError("database unavailable")


def role(name: str, description: str) -> Role:
    return Role(id=uuid4(), name=name, description=description)


def session_with_roles() -> FakeSession:
    return FakeSession(
        roles=[
            role("store_honeybee", "Store - Honeybee: can see Honeybee store data."),
            role("store_fontaine", "Store - Fontaine: can see Fontaine store data."),
        ]
    )


def make_response() -> Response:
    return Response()


def make_request(cookies: dict[str, str] | None = None) -> Request:
    cookie_header = ""
    if cookies:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())

    headers = []
    if cookie_header:
        headers.append((b"cookie", cookie_header.encode()))

    return Request({"type": "http", "headers": headers})


def test_get_available_roles_returns_seeded_roles() -> None:
    response = get_available_roles(session_with_roles())

    assert response.count == 2
    assert [item.name for item in response.items] == ["store_fontaine", "store_honeybee"]
    assert response.items[0].label == "Store - Fontaine"


def test_get_available_roles_returns_503_when_database_is_unavailable() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_available_roles(BrokenSession())  # type: ignore[arg-type]

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_register_login_me_refresh_and_logout_flow() -> None:
    db = session_with_roles()

    registered = register_user(
        UserCreateRequest(
            email="Demo@Example.com",
            password="ChangeMe123!",
            role="store_fontaine",
            display_name="Demo User",
        ),
        db,  # type: ignore[arg-type]
        make_response(),
    )

    assert registered.token_type == "bearer"
    assert registered.access_token
    assert registered.refresh_token
    assert len(db.users) == 1
    assert db.users[0].email == "demo@example.com"
    assert db.users[0].password_hash != "ChangeMe123!"
    assert [role.name for role in db.users[0].roles] == ["store_fontaine"]
    assert len(db.refresh_tokens) == 1

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=registered.access_token,
    )
    current_user = get_current_user(credentials, db, make_request())  # type: ignore[arg-type]

    assert current_user.email == "demo@example.com"
    assert current_user.roles == ["store_fontaine"]

    logged_in = login_user(
        UserLoginRequest(email="demo@example.com", password="ChangeMe123!"),
        db,  # type: ignore[arg-type]
        make_response(),
    )

    assert logged_in.access_token
    assert logged_in.refresh_token
    assert len(db.refresh_tokens) == 2

    refreshed = refresh_access_token(
        make_response(),
        make_request(),
        RefreshTokenRequest(refresh_token=logged_in.refresh_token),
        db,  # type: ignore[arg-type]
    )

    assert refreshed.refresh_token != logged_in.refresh_token
    assert len(db.refresh_tokens) == 3

    with pytest.raises(HTTPException) as reused_token_error:
        refresh_access_token(
            make_response(),
            make_request(),
            RefreshTokenRequest(refresh_token=logged_in.refresh_token),
            db,  # type: ignore[arg-type]
        )

    assert reused_token_error.value.status_code == status.HTTP_401_UNAUTHORIZED

    logout_user(
        make_response(),
        make_request(),
        LogoutRequest(refresh_token=refreshed.refresh_token),
        db,  # type: ignore[arg-type]
    )

    with pytest.raises(HTTPException) as revoked_token_error:
        refresh_access_token(
            make_response(),
            make_request(),
            RefreshTokenRequest(refresh_token=refreshed.refresh_token),
            db,  # type: ignore[arg-type]
        )

    assert revoked_token_error.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_nginx_streamlit_auth_returns_signed_scope_header_from_cookie() -> None:
    db = session_with_roles()
    registered = register_user(
        UserCreateRequest(
            email="demo@example.com",
            password="ChangeMe123!",
            role="store_fontaine",
        ),
        db,  # type: ignore[arg-type]
        make_response(),
    )
    settings = get_settings()

    response = nginx_streamlit_auth(
        make_response(),
        None,
        db,  # type: ignore[arg-type]
        make_request({settings.auth_access_cookie_name: registered.access_token}),
    )

    token = response.headers["X-Curie-Streamlit-Scope"]
    claims = decode_access_token(token)
    assert claims["email"] == "demo@example.com"
    assert claims["roles"] == ["store_fontaine"]
    assert claims["type"] == "streamlit_scope"


def test_nginx_streamlit_auth_rejects_missing_session_cookie() -> None:
    with pytest.raises(HTTPException) as exc_info:
        nginx_streamlit_auth(
            make_response(),
            None,
            session_with_roles(),  # type: ignore[arg-type]
            make_request(),
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_rejects_duplicate_email() -> None:
    db = session_with_roles()
    request = UserCreateRequest(
        email="demo@example.com",
        password="ChangeMe123!",
        role="store_fontaine",
    )
    register_user(request, db, make_response())  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        register_user(request, db, make_response())  # type: ignore[arg-type]

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


def test_register_rejects_unknown_role() -> None:
    db = session_with_roles()

    with pytest.raises(HTTPException) as exc_info:
        register_user(
            UserCreateRequest(
                email="demo@example.com",
                password="ChangeMe123!",
                role="missing_role",
            ),
            db,  # type: ignore[arg-type]
            make_response(),
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_login_rejects_wrong_password() -> None:
    db = session_with_roles()
    register_user(
        UserCreateRequest(
            email="demo@example.com",
            password="ChangeMe123!",
            role="store_fontaine",
        ),
        db,  # type: ignore[arg-type]
        make_response(),
    )

    with pytest.raises(HTTPException) as exc_info:
        login_user(
            UserLoginRequest(email="demo@example.com", password="wrong-password"),
            db,  # type: ignore[arg-type]
            make_response(),
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_rejects_expired_token() -> None:
    db = session_with_roles()
    registered = register_user(
        UserCreateRequest(
            email="demo@example.com",
            password="ChangeMe123!",
            role="store_fontaine",
        ),
        db,  # type: ignore[arg-type]
        make_response(),
    )
    db.refresh_tokens[0].expires_at = datetime.now(timezone.utc)

    with pytest.raises(HTTPException) as exc_info:
        refresh_access_token(
            make_response(),
            make_request(),
            RefreshTokenRequest(refresh_token=registered.refresh_token),
            db,  # type: ignore[arg-type]
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
