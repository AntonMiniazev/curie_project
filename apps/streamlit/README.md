# Curie Streamlit

Streamlit report application embedded by the protected SvelteKit report pages.

## Responsibilities

- Render Marketing, Finance, and Delivery dashboards.
- Read only the local DuckDB serving cache during user interaction.
- Apply the signed user's store scope in DuckDB views before aggregation; use Polars only for bounded query results.
- Share report theme tokens with the SvelteKit host through `curie_theme` iframe query params.

## Run Locally

From the repository root:

```bash
uv run streamlit run apps/streamlit/app.py
```

The app expects a current DuckDB release at `CURIE_SERVING_CACHE_CURRENT`. Docker Compose mounts the serving cache read only.

The app opens `CURIE_SERVING_CACHE_CURRENT` read only. It never contacts Flight SQL during a report request. Marketing, Financial, and Delivery query only their own domain tables. Cached query results include the active release and scope in their keys.

In dev Compose, the release lives in the `curie-dev-serving-cache` Docker volume. After the API reports a successful Flight SQL refresh, rebuild/start the Streamlit profile to try all three dashboards locally.

A direct visit to `http://localhost:8501/` without a Curie login displays an access message because report queries require a signed user scope. For local browser testing, run the SvelteKit dev server, sign in at `http://localhost:5173/curie/login`, and open a report from the Curie workspace. The local web configuration points its iframe to port 8501. An active DuckDB release is required.

## Docker Compose

```bash
docker compose --env-file infra/env/curie-dev.env -f infra/compose.dev.yml --profile streamlit up -d streamlit
```

## Styling

Shared Streamlit styles live in `apps/streamlit/styles/reporting.css`. Owned classes follow BEM naming, for example `reporting-kpis` and `reporting-kpis__card`. Streamlit-generated `data-testid` selectors are documented exceptions because Streamlit controls that markup.
