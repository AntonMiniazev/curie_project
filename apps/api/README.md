# Curie API

FastAPI service for Curie authentication, report metadata, cache status, and cache refresh triggers.

## Responsibilities

- User registration, login, logout, JWT cookies, and refresh-token storage.
- Public role metadata for account creation.
- Authenticated report metadata returned to the SvelteKit app.
- Admin-protected cache refresh endpoint used by Ampere Airflow.
- Cache status endpoint and local cache manifest inspection.
- Alembic migrations for PostgreSQL schema and seed data.

## Authentication And Authorization

Curie uses JWT-backed RBAC for user-facing access.

- Users authenticate with email and password.
- Passwords are hashed with Argon2 plus an application pepper before storage.
- Successful login or registration issues a short-lived JWT access token and a long-lived opaque refresh token.
- Refresh tokens are stored server-side only as SHA-256 hashes, so the raw token is not persisted.
- Users are assigned roles through `curie.user_roles`; available roles are stored in `curie.roles`.
- JWT access tokens include a `roles` claim.
- Reports declare a `required_role`; report and Streamlit access are scoped from the authenticated user's roles.

Browser sessions use HTTP-only cookies because the SvelteKit frontend and API share the same production origin. The browser sends these cookies automatically on same-origin requests, while JavaScript cannot read HTTP-only cookie values. This reduces accidental token exposure through frontend code or cross-site scripting bugs.

Operational endpoints use a separate admin API key model

## Run Locally

Commands are run from the repository root because the root `pyproject.toml` owns Python dependencies and pytest import paths.

```bash
docker compose --env-file infra/env/curie-dev.env -f infra/compose.dev.yml up -d postgres
uv run alembic -c apps/api/alembic.ini upgrade head
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```bash
uv run pytest apps/api/tests
```

## Contract Generation

FastAPI is the source of truth for frontend API types:

```bash
bash scripts/export-openapi.sh
bash scripts/generate-api-client.sh
```

Use `bash scripts/check-openapi-diff.sh` before push when API routes or schemas change.

## Migrations

Migration files live in `apps/api/db/migrations/versions`. Production deploy runs Alembic before starting the updated services.
