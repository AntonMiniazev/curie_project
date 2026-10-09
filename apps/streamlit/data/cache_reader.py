"""Read the active local DuckDB serving-cache release."""

import duckdb

from shared.settings import get_settings


def connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(get_settings().serving_cache_current), read_only=True)


def load_manifest() -> dict:
    with connect() as con:
        release = con.execute(
            "SELECT release_id, created_at_utc, source_uri FROM curie_release"
        ).fetchone()
        if release is None:
            raise RuntimeError("Active DuckDB cache has no release metadata")
        rows = con.execute(
            "SELECT name, row_count FROM curie_datasets ORDER BY name"
        ).fetchall()
    return {
        "release_id": release[0],
        "created_at_utc": release[1],
        "source": release[2],
        "tables": [{"name": name, "row_count": count} for name, count in rows],
    }


def aggregate_cache_active() -> bool:
    """Require the complete Gold aggregate release before running reports."""
    required = {
        "curie_marketing_sales_budget_monthly_store",
        "curie_marketing_product_sales_monthly_store",
        "curie_marketing_category_sales_monthly_store",
        "curie_marketing_client_metrics_monthly_store",
        "curie_marketing_active_client_month",
        "curie_financial_performance_monthly_store",
        "curie_financial_product_margin_monthly_store",
        "curie_delivery_courier_performance_monthly_store",
    }
    return required <= {row["name"] for row in load_manifest()["tables"]}


def table_entry(table_name: str) -> dict:
    table = next(
        (row for row in load_manifest()["tables"] if row["name"] == table_name),
        None,
    )
    if table is None:
        raise KeyError(f"Table {table_name!r} was not found in cache manifest")
    return table


def table_path(table_name: str) -> str:
    """Return a fixed logical table reference for the scoped query layer."""
    table_entry(table_name)
    return f"curie-table://{table_name}"


def all_store_rows() -> list[dict]:
    """Map signed store names to IDs before applying report RLS."""
    with connect() as con:
        rows = con.execute(
            "SELECT DISTINCT store_id, store_name "
            "FROM cache.curie_marketing_sales_budget_monthly_store"
        ).fetchall()
    return [{"store_id": row[0], "store_name": row[1]} for row in rows]
