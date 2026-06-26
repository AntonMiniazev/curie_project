"""Generic Curie cache access helpers for Streamlit reports.

This module knows how to find files listed in `manifest.json` and open a
DuckDB connection. Domain-specific reporting SQL belongs in modules such as
`marketing_queries.py`.
"""

import duckdb
import json
from pathlib import Path

from shared.settings import get_settings


def load_manifest() -> dict:
    """Load the current cache manifest from `CURIE_CACHE_CURRENT`."""
    with get_settings().manifest_path.open(encoding="utf-8") as f:
        return json.load(f)


def table_entry(table_name: str) -> dict:
    """Return one table entry from the cache manifest by logical table name."""
    tables = load_manifest().get("tables", [])

    table = next((t for t in tables if t["name"] == table_name), None)
    if table is None:
        raise KeyError(f"Table {table_name!r} was not found in cache manifest.")

    return table


def table_path(table_name: str) -> Path:
    """Resolve a logical table name to its local Parquet path."""
    return get_settings().cache_current / table_entry(table_name)["path"]


def connect() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection used for bounded Parquet queries."""
    return duckdb.connect(database=":memory:", read_only=False)
