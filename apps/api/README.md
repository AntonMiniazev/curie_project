# Curie API

FastAPI service for Curie authentication, report metadata, cache status, and cache refresh triggers.

## Responsibilities

- User registration, login, logout, JWT cookies, and refresh-token storage.
- Public role metadata for account creation.
- Authenticated report metadata returned to the SvelteKit app.
- Admin-protected cache refresh endpoint used by Ampere Airflow.
- Cache status endpoint and local cache manifest inspection.
- Alembic migrations for PostgreSQL schema and seed data.

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
