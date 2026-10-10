"""Parameterized DuckDB report queries with mandatory store scope."""

from __future__ import annotations

import re
from datetime import date
from typing import Sequence

import duckdb
import polars as pl

from data.cache_reader import connect, table_path
from shared.report_scope import ReportScope

MonthSelection = str | date | Sequence[str | date] | None
_PARAMETER = re.compile(r"CURIE_TABLE\(\?\)|\?")
_VIEW_ORDER = (
    "marketing_sales_budget_monthly_store",
    "marketing_product_sales_monthly_store",
    "marketing_category_sales_monthly_store",
    "marketing_client_metrics_monthly_store",
    "marketing_active_client_month",
    "financial_performance_monthly_store",
    "financial_product_margin_monthly_store",
    "delivery_courier_performance_monthly_store",
)


def _compile(sql: str, params: list[object]) -> tuple[str, list[object], set[str]]:
    """Expand fixed table references and retain ordinary bind parameters."""
    values = iter(params)
    binds: list[object] = []
    referenced: set[str] = set()

    def replace(match: re.Match) -> str:
        try:
            value = next(values)
        except StopIteration as exc:
            raise ValueError("Not enough report SQL parameters") from exc
        if match.group() == "?":
            binds.append(value)
            return "?"
        prefix = "curie-table://"
        if not isinstance(value, str) or not value.startswith(prefix):
            raise ValueError("Expected a fixed Curie cache table reference")
        name = value[len(prefix):]
        if name not in _VIEW_ORDER:
            raise ValueError(f"Unexpected Curie cache table: {name}")
        referenced.add(name)
        return '"' + name + '"'

    compiled = _PARAMETER.sub(replace, sql)
    try:
        next(values)
    except StopIteration:
        return compiled, binds, referenced
    raise ValueError("Too many report SQL parameters")


def _install_views(
    con: duckdb.DuckDBPyConnection, scope: ReportScope, referenced: set[str]
) -> None:
    restricted = not scope.can_view_all_stores
    if restricted:
        if not scope.allowed_store_ids:
            raise PermissionError("This report scope has no allowed stores")
        con.execute("CREATE TEMP TABLE _curie_allowed_stores (store_id INTEGER)")
        con.executemany(
            "INSERT INTO _curie_allowed_stores VALUES (?)",
            [(store_id,) for store_id in scope.allowed_store_ids],
        )
    for name in _VIEW_ORDER:
        if name not in referenced:
            continue
        predicate = (
            " WHERE store_id IN (SELECT store_id FROM _curie_allowed_stores)"
            if restricted else ""
        )
        con.execute(f'CREATE TEMP VIEW "{name}" AS SELECT * FROM cache."{name}"{predicate}')


def query(sql: str, params: list[object], scope: ReportScope) -> pl.DataFrame:
    if not isinstance(scope, ReportScope) or not scope.is_allowed:
        raise PermissionError("An authorized ReportScope is required")
    compiled, binds, referenced = _compile(sql, params)
    with connect() as con:
        _install_views(con, scope, referenced)
        return pl.from_arrow(con.execute(compiled, binds).to_arrow_table())


def normalize_months(months: MonthSelection) -> list[str | date]:
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
    """Build month/UI-store WHERE clauses; scoped views enforce RLS first."""
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


def store_dimension(scope: ReportScope, domain: str) -> pl.DataFrame:
    """Return the stores present in one domain within the signed scope."""
    tables = {
        "Marketing": "marketing_sales_budget_monthly_store",
        "Financial": "financial_performance_monthly_store",
        "Delivery": "delivery_courier_performance_monthly_store",
    }
    return query(
        """SELECT store_id, any_value(store_name) AS store_name,
           any_value(city) AS city FROM CURIE_TABLE(?)
           GROUP BY store_id ORDER BY store_name""",
        [table_path(tables[domain])], scope,
    )
