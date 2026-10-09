# Curie Project

Curie is a full-stack reporting portal built as a practical data-application lab. It brings together a public project hub, authenticated report workspace, embedded Streamlit dashboards, and a FastAPI backend that serves users, roles, report metadata, and cache-refresh operations.

The application runs as a compact production stack: SvelteKit renders the website, FastAPI protects the API, PostgreSQL stores application metadata, and Streamlit delivers interactive dashboards. An isolated Flight SQL refresh job reads Ampere Gold aggregates and builds local DuckDB releases that Streamlit queries read only.

Curie is also the public-facing companion to the wider Ampere/Bohr learning environment:

- Ampere provides the data-platform side: source data, lakehouse layers, catalog metadata, and downstream reporting contracts.
- Bohr provides the infrastructure and home-lab architecture context.
- Curie turns those foundations into a user-facing reporting product with authentication, deployment, documentation, and performance baselines.

## What Curie Shows

- A SvelteKit project hub documenting Ampere, Bohr, and Curie as connected portfolio projects.
- A protected reporting workspace with role-aware access patterns.
- Marketing, Finance, and Delivery report dashboards embedded from Streamlit.
- A FastAPI backend with generated OpenAPI contracts and a TypeScript client.
- Docker Compose and Nginx production deployment for a small Hetzner-hosted runtime.
- Architecture documentation rendered from PlantUML/C4-style diagrams.

## Repository Layout

```text
apps/
  api/        FastAPI application, auth, report metadata, cache refresh endpoints, Alembic migrations
  streamlit/  Streamlit dashboards and scoped DuckDB reporting queries
  web/        SvelteKit frontend, project hub, auth screens, report iframe shell
docs/         Architecture diagrams and frontend styling notes
infra/        Docker Compose, Nginx, bootstrap, and environment templates
packages/     Generated OpenAPI contract and TypeScript API client
scripts/      OpenAPI export, client generation, and contract drift checks
```

## Documentation

Architecture diagrams and styling conventions are documented in [`docs/README.md`](docs/README.md).
