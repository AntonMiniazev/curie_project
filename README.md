# Curie Project

Curie is a full-stack reporting portal built as a practical data-application lab. It brings together a public project hub, authenticated report workspace, embedded Streamlit dashboards, and a FastAPI backend that serves users, roles, report metadata, and cache-refresh operations.

The application is designed around a compact production shape: SvelteKit renders the website, FastAPI protects the API surface, PostgreSQL stores application metadata, and Streamlit delivers interactive dashboards. Task 16 adds an isolated Flight SQL refresh job that builds durable local DuckDB releases. The existing Iceberg-derived Parquet cache remains available during parity validation; production Streamlit stays on it until the DuckDB release passes the live gates.

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
