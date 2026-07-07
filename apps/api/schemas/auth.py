from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Request body for registering a new user with email, password, display name, and selected role."""

    role: str = Field(
        min_length=1,
        max_length=80,
        validation_alias=AliasChoices("role", "selected_role"),
    )
    email: EmailStr
    password: str = Field(min_length=5, max_length=256)
    display_name: str | None = Field(default=None, max_length=120)


class UserLoginRequest(BaseModel):
    """Request body for logging in an existing user with email and password."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    """Response body returned after register, login, or token refresh with session token details."""

    access_token: str
    refresh_token: str
    expires_in_seconds: int


class CurrentUserResponse(BaseModel):
    """Response body describing the authenticated user resolved from a valid access token."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str | None
    created_at: str
    roles: list[str]
    role_descriptions: list[str]
    role_short_descriptions: list[str]
    is_active: bool
    is_verified: bool


class AvailableRoleResponse(BaseModel):
    """Single public role option that the frontend can show during registration."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    label: str
    description: str | None
    short_description: str | None


class AvailableRolesResponse(BaseModel):
    """List response containing all roles that a new user is allowed to select."""

    items: list[AvailableRoleResponse]
    count: int


class RefreshTokenRequest(BaseModel):
    """Request body for getting a new access token using a valid refresh token."""

    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    """Request body for revoking a refresh token during logout."""

    refresh_token: str = Field(min_length=1)
