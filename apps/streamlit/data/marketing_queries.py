"""DuckDB query layer for the Marketing reporting dashboard.

Functions in this module return small Polars dataframes that are already
aggregated for Streamlit visuals. Keep raw Parquet scans here so dashboards do
not materialize large fact tables or know cache file paths.
"""

from __future__ import annotations

import polars as pl

from data.cache_reader import table_path
from data.query_utils import MonthSelection, filter_sql, query


def marketing_monthly_sales(store_id: int | None = None) -> pl.DataFrame:
    """Return monthly sales amount and order count from `fct_orders_sales`."""
    orders_path = str(table_path("fct_orders_sales"))
    where_sql, where_params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        SELECT
          date_trunc('month', order_date) AS month,
          sum(total_amount) AS sales_amount,
          count(DISTINCT order_id) AS order_count
        FROM read_parquet(?)
        {where_sql}
        GROUP BY 1
        ORDER BY 1
        """,
        [orders_path, *where_params],
    )


def marketing_average_bill_by_month(store_id: int | None = None) -> pl.DataFrame:
    """Return monthly average bill as sales divided by distinct order count."""
    orders_path = str(table_path("fct_orders_sales"))
    where_sql, where_params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        SELECT
          date_trunc('month', order_date) AS month,
          sum(total_amount) AS sales_amount,
          count(DISTINCT order_id) AS order_count,
          sum(total_amount) / nullif(count(DISTINCT order_id), 0) AS average_bill_amount
        FROM read_parquet(?)
        {where_sql}
        GROUP BY 1
        ORDER BY 1
        """,
        [orders_path, *where_params],
    )


def marketing_monthly_clients(store_id: int | None = None) -> pl.DataFrame:
    """Return active clients by month based on clients with at least one order."""
    orders_path = str(table_path("fct_orders_sales"))
    where_sql, where_params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        SELECT
          date_trunc('month', order_date) AS month,
          count(DISTINCT client_id) AS active_client_count
        FROM read_parquet(?)
        {where_sql}
        {"AND" if where_sql else "WHERE"} client_id IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """,
        [orders_path, *where_params],
    )


def marketing_active_clients(
    months: MonthSelection = None, store_id: int | None = None
) -> pl.DataFrame:
    """Return distinct active clients across the selected reporting period."""
    orders_path = str(table_path("fct_orders_sales"))
    where_sql, where_params = filter_sql(
        month_column="order_date",
        months=months,
        store_column="store_id",
        store_id=store_id,
    )
    client_condition = f"{'AND' if where_sql else 'WHERE'} client_id IS NOT NULL"
    return query(
        f"""
        SELECT
          count(DISTINCT client_id) AS active_client_count
        FROM read_parquet(?)
        {where_sql}
        {client_condition}
        """,
        [orders_path, *where_params],
    )


def marketing_client_churn_by_month(store_id: int | None = None) -> pl.DataFrame:
    """Return churn numerator, starting client base, and churn percent by month."""
    orders_path = str(table_path("fct_orders_sales"))
    clients_path = str(table_path("dim_clients"))
    client_store_filter = "AND c.preferred_store_id = ?" if store_id is not None else ""
    churn_store_filter = "AND preferred_store_id = ?" if store_id is not None else ""
    params: list[object] = [orders_path, clients_path, clients_path]
    if store_id is not None:
        params.append(store_id)
    params.append(clients_path)
    if store_id is not None:
        params.append(store_id)

    # Churn is defined as churn events during the month divided by the client
    # base at the start of the month. `updated_at` is the churn event timestamp.
    return query(
        f"""
        WITH months AS (
          SELECT DISTINCT date_trunc('month', order_date) AS month_start
          FROM read_parquet(?)
          UNION
          SELECT DISTINCT date_trunc('month', updated_at) AS month_start
          FROM read_parquet(?)
          WHERE churned = true
            AND updated_at IS NOT NULL
        ),
        client_base AS (
          SELECT
            m.month_start,
            count(DISTINCT c.client_id) AS client_base_start
          FROM months m
          CROSS JOIN read_parquet(?) c
          WHERE c.registration_date < m.month_start
            AND (c.churned IS DISTINCT FROM true OR c.updated_at >= m.month_start)
            {client_store_filter}
          GROUP BY 1
        ),
        monthly_churn AS (
          SELECT
            date_trunc('month', updated_at) AS month_start,
            count(DISTINCT client_id) AS churned_clients
          FROM read_parquet(?)
          WHERE churned = true
            AND updated_at IS NOT NULL
            {churn_store_filter}
          GROUP BY 1
        )
        SELECT
          b.month_start AS month,
          b.client_base_start,
          coalesce(c.churned_clients, 0) AS churned_clients,
          CASE
            WHEN b.client_base_start = 0 THEN NULL
            ELSE coalesce(c.churned_clients, 0)::DOUBLE / b.client_base_start * 100
          END AS churn_pct
        FROM client_base b
        LEFT JOIN monthly_churn c USING (month_start)
        ORDER BY 1
        """,
        params,
    )


def marketing_monthly_budget(store_id: int | None = None) -> pl.DataFrame:
    """Return daily budget rows rolled up to monthly sales and order budgets."""
    budget_path = str(table_path("budget_orders_sales"))
    where_sql, where_params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        SELECT
          date_trunc('month', budget_date) AS month,
          sum(sales_amount_daily) AS budget_sales_amount,
          sum(orders_budget_daily) AS budget_order_count
        FROM read_parquet(?)
        {where_sql}
        GROUP BY 1
        ORDER BY 1
        """,
        [budget_path, *where_params],
    )


def marketing_monthly_sales_vs_budget(store_id: int | None = None) -> pl.DataFrame:
    """Return total monthly actuals, budgets, variance amount, and variance pct."""
    orders_path = str(table_path("fct_orders_sales"))
    budget_path = str(table_path("budget_orders_sales"))
    actual_where, actual_params = filter_sql(store_column="store_id", store_id=store_id)
    budget_where, budget_params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        WITH actual AS (
          SELECT
            date_trunc('month', order_date) AS month,
            sum(total_amount) AS actual_sales_amount,
            count(DISTINCT order_id) AS actual_order_count
          FROM read_parquet(?)
          {actual_where}
          GROUP BY 1
        ),
        budget AS (
          SELECT
            date_trunc('month', budget_date) AS month,
            sum(sales_amount_daily) AS budget_sales_amount,
            sum(orders_budget_daily) AS budget_order_count
          FROM read_parquet(?)
          {budget_where}
          GROUP BY 1
        )
        SELECT
          coalesce(actual.month, budget.month) AS month,
          coalesce(actual.actual_sales_amount, 0) AS actual_sales_amount,
          budget.budget_sales_amount,
          coalesce(actual.actual_sales_amount, 0) - budget.budget_sales_amount AS sales_variance_amount,
          CASE
            WHEN budget.budget_sales_amount = 0 THEN NULL
            ELSE coalesce(actual.actual_sales_amount, 0) / budget.budget_sales_amount - 1
          END AS sales_variance_pct,
          coalesce(actual.actual_order_count, 0) AS actual_order_count,
          budget.budget_order_count
        FROM actual
        FULL OUTER JOIN budget USING (month)
        ORDER BY 1
        """,
        [orders_path, *actual_params, budget_path, *budget_params],
    )


def marketing_store_monthly_sales_vs_budget(
    store_id: int | None = None,
) -> pl.DataFrame:
    """Return monthly actual-vs-budget metrics split by store."""
    orders_path = str(table_path("fct_orders_sales"))
    budget_path = str(table_path("budget_orders_sales"))
    stores_path = str(table_path("dim_stores"))
    store_filter = "WHERE store_id = ?" if store_id is not None else ""
    params: list[object] = [orders_path]
    if store_id is not None:
        params.append(store_id)
    params.append(budget_path)
    if store_id is not None:
        params.append(store_id)
    params.append(stores_path)

    # `dim_stores` can contain repeated rows per store in the cache, so labels
    # are deduped before joining to store-level actual-vs-budget metrics.
    return query(
        f"""
        WITH actual AS (
          SELECT
            date_trunc('month', order_date) AS month,
            store_id,
            sum(total_amount) AS actual_sales_amount,
            count(DISTINCT order_id) AS actual_order_count
          FROM read_parquet(?)
          {store_filter}
          GROUP BY 1, 2
        ),
        budget AS (
          SELECT
            date_trunc('month', budget_date) AS month,
            store_id,
            sum(sales_amount_daily) AS budget_sales_amount,
            sum(orders_budget_daily) AS budget_order_count
          FROM read_parquet(?)
          {store_filter}
          GROUP BY 1, 2
        ),
        store_labels AS (
          SELECT
            store_id,
            any_value(store_name) AS store_name,
            any_value(city) AS city
          FROM read_parquet(?)
          GROUP BY 1
        ),
        sales_vs_budget AS (
          SELECT
            coalesce(actual.month, budget.month) AS month,
            coalesce(actual.store_id, budget.store_id) AS store_id,
            coalesce(actual.actual_sales_amount, 0) AS actual_sales_amount,
            budget.budget_sales_amount,
            coalesce(actual.actual_sales_amount, 0) - budget.budget_sales_amount AS sales_variance_amount,
            CASE
              WHEN budget.budget_sales_amount = 0 THEN NULL
              ELSE coalesce(actual.actual_sales_amount, 0) / budget.budget_sales_amount - 1
            END AS sales_variance_pct,
            coalesce(actual.actual_order_count, 0) AS actual_order_count,
            budget.budget_order_count
          FROM actual
          FULL OUTER JOIN budget USING (month, store_id)
        )
        SELECT
          sales_vs_budget.month,
          sales_vs_budget.store_id,
          store_labels.store_name,
          store_labels.city,
          sales_vs_budget.actual_sales_amount,
          sales_vs_budget.budget_sales_amount,
          sales_vs_budget.sales_variance_amount,
          sales_vs_budget.sales_variance_pct,
          sales_vs_budget.actual_order_count,
          sales_vs_budget.budget_order_count
        FROM sales_vs_budget
        LEFT JOIN store_labels USING (store_id)
        ORDER BY sales_vs_budget.month, store_labels.store_name
        """,
        params,
    )


def marketing_top_products(
    months: MonthSelection = None,
    metric: str = "sales",
    limit: int = 10,
    store_id: int | None = None,
) -> pl.DataFrame:
    """Return top products for the selected month range, store, and ranking metric."""
    if metric not in {"sales", "orders"}:
        raise ValueError("metric must be either 'sales' or 'orders'.")

    order_column = "sales_amount" if metric == "sales" else "order_count"
    order_product_path = str(table_path("fct_order_product"))
    products_path = str(table_path("dim_products"))
    where_sql, where_params = filter_sql(
        month_column="op.order_date",
        months=months,
        store_column="op.store_id",
        store_id=store_id,
    )

    return query(
        f"""
        SELECT
          p.product_name,
          p.category_name,
          sum(op.line_sales_amount) AS sales_amount,
          count(DISTINCT op.order_id) AS order_count
        FROM read_parquet(?) op
        LEFT JOIN read_parquet(?) p USING (product_id)
        {where_sql}
        GROUP BY 1, 2
        ORDER BY {order_column} DESC NULLS LAST
        LIMIT ?
        """,
        [order_product_path, products_path, *where_params, limit],
    )


def marketing_top_categories(
    months: MonthSelection = None,
    metric: str = "sales",
    limit: int = 10,
    store_id: int | None = None,
) -> pl.DataFrame:
    """Return top categories for the selected month range, store, and metric."""
    if metric not in {"sales", "orders"}:
        raise ValueError("metric must be either 'sales' or 'orders'.")

    order_column = "sales_amount" if metric == "sales" else "order_count"
    order_product_path = str(table_path("fct_order_product"))
    products_path = str(table_path("dim_products"))
    where_sql, where_params = filter_sql(
        month_column="op.order_date",
        months=months,
        store_column="op.store_id",
        store_id=store_id,
    )

    return query(
        f"""
        SELECT
          p.category_name,
          sum(op.line_sales_amount) AS sales_amount,
          count(DISTINCT op.order_id) AS order_count
        FROM read_parquet(?) op
        LEFT JOIN read_parquet(?) p USING (product_id)
        {where_sql}
        GROUP BY 1
        ORDER BY {order_column} DESC NULLS LAST
        LIMIT ?
        """,
        [order_product_path, products_path, *where_params, limit],
    )


def marketing_new_clients_by_month(store_id: int | None = None) -> pl.DataFrame:
    """Return new clients grouped by registration month."""
    clients_path = str(table_path("dim_clients"))
    where_sql, where_params = filter_sql(
        store_column="preferred_store_id",
        store_id=store_id,
    )
    return query(
        f"""
        SELECT
          date_trunc('month', registration_date) AS month,
          count(DISTINCT client_id) AS new_client_count
        FROM read_parquet(?)
        {where_sql}
        {"AND" if where_sql else "WHERE"} registration_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """,
        [clients_path, *where_params],
    )
