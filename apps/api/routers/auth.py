from typing import Annotated
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import (
    create_access_token,
    create_random_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)
from ..db.models import RefreshToken, Role, User
from ..db.session import get_db_session
from ..schemas.auth import (
    AvailableRoleResponse,
    AvailableRolesResponse,
    CurrentUserResponse,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreateRequest,
    UserLoginRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

db_dependency = Annotated[Session, Depends(get_db_session)]
bearer_scheme = HTTPBearer(auto_error=False)
bearer_dependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def unauthorized(detail: str = "Invalid authentication credentials.") -> HTTPException:
    """Create a Bearer-compatible 401 error for auth failures."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_refresh_token_for_user(user: User, db: Session) -> str:
    """Create a raw refresh token and store only its hash for the user."""
    settings = get_settings()
    refresh_token = create_random_token()
    refresh_token_model = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
    )
    db.add(refresh_token_model)
    return refresh_token


def user_roles(user: User) -> list[str]:
    """Return role names attached to a user."""
    return [role.name for role in user.roles]


def token_response_for_user(user: User, refresh_token: str) -> TokenResponse:
    """Build the standard token response for a user and refresh token."""
    settings = get_settings()
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        roles=user_roles(user),
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=settings.access_token_minutes * 60,
    )


def resolve_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    """Resolve and validate the current user from a Bearer access token."""
    if credentials is None:
        raise unauthorized()

    try:
        claims = decode_access_token(credentials.credentials)
    except PyJWTError as exc:
        raise unauthorized() from exc

    if claims.get("type") != "access":
        raise unauthorized()

    user_id = claims.get("sub")
    if not user_id:
        raise unauthorized()
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise unauthorized() from exc

    try:
        user = db.query(User).filter(User.id == user_uuid).one_or_none()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable.",
        ) from exc

    if user is None or not user.is_active:
        raise unauthorized()

    return user


@router.get(
    "/roles",
    response_model=AvailableRolesResponse,
    status_code=status.HTTP_200_OK,
)
def get_available_roles(db: db_dependency) -> AvailableRolesResponse:
    """Return public roles that a new user can select during registration."""
    try:
        roles = db.query(Role).order_by(Role.name).all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable.",
        ) from exc

    role_items = (
        AvailableRoleResponse(
            name=role.name,
            label=(role.description or role.name).split(":", 1)[0],
            description=role.description,
        )
        for role in roles
    )
    items = list(role_items)
    return AvailableRolesResponse(items=items, count=len(items))


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: UserCreateRequest,
    db: db_dependency,
) -> TokenResponse:
    """Create a user, assign the selected role, and return access/refresh tokens."""
    try:
        user_email = str(request.email).lower()
        existing_user = db.query(User).filter(User.email == user_email).one_or_none()
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            )

        role = db.query(Role).filter(Role.name == request.role).one_or_none()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected role is not available.",
            )
        role_name = role.name

        user = User(
            email=user_email,
            password_hash=hash_password(request.password),
            display_name=request.display_name,
        )
        user.roles.append(role)
        db.add(user)
        db.flush()
        user_id = str(user.id)

        settings = get_settings()
        refresh_token = create_random_token()
        refresh_token_model = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_days),
        )
        db.add(refresh_token_model)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable.",
        ) from exc

    access_token = create_access_token(
        user_id=user_id,
        email=user_email,
        roles=[role_name],
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=settings.access_token_minutes * 60,
    )



@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login_user(
    request: UserLoginRequest,
    db: db_dependency,
) -> TokenResponse:
    """Verify user credentials and return access/refresh tokens."""
    try:
        user_email = str(request.email).lower()
        user = db.query(User).filter(User.email == user_email).one_or_none()
        if user is None or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        settings = get_settings()
        refresh_token = create_random_token()
        refresh_token_model = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_days),
        )
        db.add(refresh_token_model)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable.",
        ) from exc

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        roles=[role.name for role in user.roles],
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=settings.access_token_minutes * 60,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_user(
    credentials: bearer_dependency,
    db: db_dependency,
) -> CurrentUserResponse:
    """Return the current user represented by a valid Bearer access token."""
    user = resolve_current_user(credentials, db)
    return CurrentUserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        roles=user_roles(user),
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_access_token(
    request: RefreshTokenRequest,
    db: db_dependency,
) -> TokenResponse:
    """Use a valid refresh token to issue a new access token."""
    token_hash = hash_token(request.refresh_token)
    now = datetime.now(timezone.utc)

    try:
        stored_token = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .one_or_none()
        )
        if (
            stored_token is None
            or stored_token.revoked_at is not None
            or stored_token.expires_at <= now
            or not stored_token.user.is_active
        ):
            raise unauthorized("Invalid or expired refresh token.")

        stored_token.revoked_at = now
        new_refresh_token = create_refresh_token_for_user(stored_token.user, db)
        response = token_response_for_user(stored_token.user, new_refresh_token)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable.",
        ) from exc

    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_user(
    request: LogoutRequest,
    db: db_dependency,
) -> None:
    """Revoke a refresh token so it cannot be used again."""
    token_hash = hash_token(request.refresh_token)

    try:
        stored_token = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .one_or_none()
        )
        if stored_token is not None and stored_token.revoked_at is None:
            stored_token.revoked_at = datetime.now(timezone.utc)
            db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable.",
        ) from exc

    return None
