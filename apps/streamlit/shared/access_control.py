"""Role-based data scoping for embedded Curie Streamlit reports."""

from __future__ import annotations

from dataclasses import dataclass

import jwt
import streamlit as st
from jwt import PyJWTError

from shared.settings import get_settings


REGION_ROLE = "region_directory"
SCOPE_HEADER = "X-Curie-Streamlit-Scope"
STORE_ROLE_TO_STORE_NAME = {
    "store_fontaine": "Fontaine",
    "store_honeybee": "Honeybee",
    "store_tomcats": "Tomcats",
    "store_rosemary": "Rosemary",
    "store_suburban": "Suburban",
}


@dataclass(frozen=True)
class ReportAccess:
    """Authenticated report scope decoded from a signed Curie embed token."""

    email: str | None
    roles: tuple[str, ...]
    can_view_all_stores: bool
    allowed_store_names: tuple[str, ...]
    error: str | None = None

    @property
    def is_allowed(self) -> bool:
        return self.can_view_all_stores or bool(self.allowed_store_names)

    @property
    def label(self) -> str:
        if self.can_view_all_stores:
            return "Region directory: all stores"
        if self.allowed_store_names:
            return f"Store scope: {', '.join(self.allowed_store_names)}"
        return "No store access"


def current_report_access() -> ReportAccess:
    """Resolve signed report scope from Nginx headers, with a local-dev cookie fallback."""
    cached_claims = st.session_state.get("curie_embed_claims")
    claims = cached_claims if isinstance(cached_claims, dict) else None

    if claims is None:
        settings = get_settings()
        token = _scope_header()
        expected_type = "streamlit_scope"
        if token is None and settings.app_env == "dev":
            token = _access_cookie(settings.auth_access_cookie_name)
            expected_type = "access"

        if token is None:
            return _denied(
                "Open this report from the Curie website so Streamlit receives an authenticated report scope."
            )

        try:
            claims = jwt.decode(
                token,
                settings.jwt_secret_key.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
        except PyJWTError:
            return _denied("The Streamlit report scope is invalid or expired.")

        if claims.get("type") != expected_type:
            return _denied("The Streamlit report scope has an unexpected token type.")

        st.session_state.curie_embed_claims = claims

    roles = tuple(str(role) for role in claims.get("roles", []) if role)
    allowed_store_names = tuple(
        store_name
        for role, store_name in STORE_ROLE_TO_STORE_NAME.items()
        if role in roles
    )
    return ReportAccess(
        email=claims.get("email"),
        roles=roles,
        can_view_all_stores=REGION_ROLE in roles,
        allowed_store_names=allowed_store_names,
    )


def restrict_store_options(
    store_options: list[tuple[str, int | None]],
    access: ReportAccess,
) -> list[tuple[str, int | None]]:
    """Return store selector options allowed by the current user's role."""
    if access.can_view_all_stores:
        return store_options

    allowed_names = {store_name.lower() for store_name in access.allowed_store_names}
    return [
        (label, store_id)
        for label, store_id in store_options
        if store_id is not None and _store_name_from_label(label).lower() in allowed_names
    ]


def _scope_header() -> str | None:
    headers = st.context.headers
    token = headers.get(SCOPE_HEADER) or headers.get(SCOPE_HEADER.lower())
    return token or None


def _access_cookie(cookie_name: str) -> str | None:
    token = st.context.cookies.get(cookie_name)
    if isinstance(token, list):
        return token[0] if token else None
    return token or None


def _store_name_from_label(label: str) -> str:
    return label.split(" (", 1)[0]


def _denied(message: str) -> ReportAccess:
    return ReportAccess(
        email=None,
        roles=(),
        can_view_all_stores=False,
        allowed_store_names=(),
        error=message,
    )
