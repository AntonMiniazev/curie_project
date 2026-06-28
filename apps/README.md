# Curie Apps

This folder contains the three runtime applications that make up Curie.

## Applications

- `api/`: FastAPI service for authentication, report metadata, cache status, and cache refresh orchestration.
- `web/`: SvelteKit website for the project hub, auth pages, report workspace navigation, and Streamlit iframe hosting.
- `streamlit/`: Streamlit dashboards for Marketing, Finance, and Delivery reporting over the local Parquet cache.

## Runtime Shape

In development, PostgreSQL usually runs through `infra/compose.dev.yml`, while API and web can be run directly for faster iteration. Streamlit can run directly with `uv run streamlit run apps/streamlit/app.py` or through the Docker Compose `streamlit` profile.

In production, GitHub Actions builds and deploys Docker images for API, web, and Streamlit. Nginx serves the public HTTPS routes and proxies `/api/*` and `/streamlit/*` to the internal services.

## Shared Contracts

The FastAPI OpenAPI schema is exported into `packages/contracts/openapi.json`. The SvelteKit app consumes generated TypeScript types from `packages/api-client`.
