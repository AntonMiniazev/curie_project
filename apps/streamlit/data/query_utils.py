"""Shared DuckDB query helpers for cache-backed reporting modules."""

from __future__ import annotations

from datetime import date
from typing import Sequence

import polars as pl

from data.cache_reader import connect, table_path


MonthSelection = str | date | Sequence[str | date] | None


def query(sql: str, params: list[object]) -> pl.DataFrame:
    """Execute parameterized DuckDB SQL and convert the reduced result to Polars."""
    with connect() as con:
        return pl.from_arrow(con.execute(sql, params).fetch_arrow_table())


def normalize_months(months: MonthSelection) -> list[str | date]:
    """Normalize one or many month values into a parameter list."""
    if months is None:
        return []
    if isinstance(months, str | date):
        return [months]
    return list(months)


def filter_sql(
    *,
    month_column: str | None = None,
    months: MonthSelection = None,
    store_column: str | None = None,
    store_id: int | None = None,
) -> tuple[str, list[object]]:
    """Build shared month/store WHERE clauses for cache facts."""
    conditions: list[str] = []
    params: list[object] = []
    month_values = normalize_months(months)

    if month_column and month_values:
        placeholders = ", ".join(["date_trunc('month', ?::DATE)"] * len(month_values))
        conditions.append(f"date_trunc('month', {month_column}) IN ({placeholders})")
        params.extend(month_values)

    if store_column and store_id is not None:
        conditions.append(f"{store_column} = ?")
        params.append(store_id)

    if not conditions:
        return "", []

    return "WHERE " + " AND ".join(conditions), params


def store_dimension() -> pl.DataFrame:
    """Return one label row per store from the cached store dimension."""
    stores_path = str(table_path("dim_stores"))
    return query(
        """
        SELECT
          store_id,
          any_value(store_name) AS store_name,
          any_value(city) AS city
        FROM read_parquet(?)
        GROUP BY 1
        ORDER BY store_name
        """,
        [stores_path],
    )
