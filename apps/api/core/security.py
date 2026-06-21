from pwdlib import PasswordHash
from .config import get_settings
import hashlib
import jwt
import secrets
from datetime import datetime, timedelta, timezone

password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """Return a secure one-way hash for a raw user password before storing it."""
    settings = get_settings()
    password_with_pepper = password + settings.curie_password_pepper.get_secret_value()

    # Hash the password (Argon2 automatically adds a unique salt)
    return password_hasher.hash(password_with_pepper)

def verify_password(password: str, password_hash: str) -> bool:
    """Return True when a raw login password matches the stored password hash."""
    settings = get_settings()
    password_with_pepper = password + settings.curie_password_pepper.get_secret_value()
    return password_hasher.verify(password_with_pepper, password_hash)

def create_access_token(user_id: str, email: str, roles: list[str]) -> str:
    """Create a signed short-lived JWT access token for an authenticated user."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_streamlit_embed_token(user_id: str, email: str, roles: list[str]) -> str:
    """Create a signed short-lived JWT that Streamlit can use for report scoping."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "type": "streamlit_embed",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Validate a JWT access token and return its decoded claims."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )


def hash_token(token: str) -> str:
    """Return a stable hash of a refresh token so the raw token is never stored."""
    token_bytes = token.encode("utf-8")
    return f"sha256:{hashlib.sha256(token_bytes).hexdigest()}"


def create_random_token() -> str:
    """Create a cryptographically random token suitable for refresh-token use."""
    return secrets.token_urlsafe(48)
