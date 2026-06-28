# Curie Streamlit

Streamlit report application embedded by the protected SvelteKit report pages.

## Responsibilities

- Render Marketing, Finance, and Delivery dashboards.
- Read only the local Curie serving cache, not upstream Ampere Delta tables during user interaction.
- Query Parquet files with DuckDB and shape bounded display data with Polars/Pandas where needed.
- Share report theme tokens with the SvelteKit host through `curie_theme` iframe query params.

## Run Locally

From the repository root:

```bash
uv run streamlit run apps/streamlit/app.py
```

The app expects a current cache under the path configured by `CURIE_CACHE_CURRENT`. For Docker Compose development this is mounted from `data/dev-cache/current`.

## Docker Compose

```bash
docker compose --env-file infra/env/curie-dev.env -f infra/compose.dev.yml --profile streamlit up -d streamlit
```

## Styling

Shared Streamlit styles live in `apps/streamlit/styles/reporting.css`. Owned classes follow BEM naming, for example `reporting-kpis` and `reporting-kpis__card`. Streamlit-generated `data-testid` selectors are documented exceptions because Streamlit controls that markup.
