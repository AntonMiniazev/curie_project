"""DuckDB query layer for Finance reporting over Curie's local cache."""

from __future__ import annotations

from data.cache_reader import table_path
from data.query_utils import MonthSelection, filter_sql, query


def finance_monthly_performance(store_id: int | None = None):
    """Return monthly revenue, costs, margin, profit, and revenue budget."""
    margin_path = str(table_path("fct_order_margin"))
    budget_path = str(table_path("budget_orders_sales"))
    actual_where, actual_params = filter_sql(store_column="store_id", store_id=store_id)
    budget_where, budget_params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        WITH actual AS (
          SELECT
            date_trunc('month', order_date) AS month,
            sum(total_amount) AS revenue_amount,
            sum(product_cost_amount) AS product_cost_amount,
            sum(delivery_cost_amount) AS delivery_cost_amount,
            sum(gross_profit_amount) AS gross_profit_amount,
            sum(gross_profit_amount - delivery_cost_amount) AS operational_profit_amount
          FROM read_parquet(?)
          {actual_where}
          GROUP BY 1
        ),
        budget AS (
          SELECT
            date_trunc('month', budget_date) AS month,
            sum(sales_amount_daily) AS budget_revenue_amount
          FROM read_parquet(?)
          {budget_where}
          GROUP BY 1
        )
        SELECT
          coalesce(actual.month, budget.month) AS month,
          coalesce(actual.revenue_amount, 0) AS revenue_amount,
          budget.budget_revenue_amount,
          coalesce(actual.revenue_amount, 0) - budget.budget_revenue_amount AS revenue_variance_amount,
          CASE
            WHEN budget.budget_revenue_amount = 0 THEN NULL
            ELSE coalesce(actual.revenue_amount, 0) / budget.budget_revenue_amount - 1
          END AS revenue_variance_pct,
          coalesce(actual.product_cost_amount, 0) AS product_cost_amount,
          coalesce(actual.delivery_cost_amount, 0) AS delivery_cost_amount,
          coalesce(actual.gross_profit_amount, 0) AS gross_profit_amount,
          CASE
            WHEN actual.revenue_amount = 0 THEN NULL
            ELSE actual.gross_profit_amount / actual.revenue_amount
          END AS gross_margin_pct,
          coalesce(actual.operational_profit_amount, 0) AS operational_profit_amount
        FROM actual
        FULL OUTER JOIN budget USING (month)
        ORDER BY 1
        """,
        [margin_path, *actual_params, budget_path, *budget_params],
    )


def finance_store_monthly_performance(store_id: int | None = None):
    """Return monthly finance performance split by store."""
    margin_path = str(table_path("fct_order_margin"))
    stores_path = str(table_path("dim_stores"))
    where_sql, where_params = filter_sql(store_column="m.store_id", store_id=store_id)
    return query(
        f"""
        WITH store_labels AS (
          SELECT
            store_id,
            any_value(store_name) AS store_name,
            any_value(city) AS city
          FROM read_parquet(?)
          GROUP BY 1
        )
        SELECT
          date_trunc('month', m.order_date) AS month,
          m.store_id,
          s.store_name,
          s.city,
          sum(m.total_amount) AS revenue_amount,
          sum(m.product_cost_amount) AS product_cost_amount,
          sum(m.delivery_cost_amount) AS delivery_cost_amount,
          sum(m.gross_profit_amount) AS gross_profit_amount,
          CASE
            WHEN sum(m.total_amount) = 0 THEN NULL
            ELSE sum(m.gross_profit_amount) / sum(m.total_amount)
          END AS gross_margin_pct,
          sum(m.gross_profit_amount - m.delivery_cost_amount) AS operational_profit_amount
        FROM read_parquet(?) m
        LEFT JOIN store_labels s USING (store_id)
        {where_sql}
        GROUP BY 1, 2, 3, 4
        ORDER BY 1, 3
        """,
        [stores_path, margin_path, *where_params],
    )


def finance_product_margin(
    months: MonthSelection = None,
    store_id: int | None = None,
    limit: int = 5,
    direction: str = "top",
):
    """Return top or bottom products by gross margin percentage."""
    if direction not in {"top", "bottom"}:
        raise ValueError("direction must be either 'top' or 'bottom'.")

    order_product_path = str(table_path("fct_order_product"))
    costing_path = str(table_path("dim_costing"))
    products_path = str(table_path("dim_products"))
    where_sql, where_params = filter_sql(
        month_column="op.order_date",
        months=months,
        store_column="op.store_id",
        store_id=store_id,
    )
    order_direction = "DESC" if direction == "top" else "ASC"
    return query(
        f"""
        SELECT
          p.product_name,
          p.category_name,
          sum(op.line_sales_amount) AS revenue_amount,
          sum(c.total_cost) AS product_cost_amount,
          sum(op.line_sales_amount) - sum(c.total_cost) AS gross_profit_amount,
          CASE
            WHEN sum(op.line_sales_amount) = 0 THEN NULL
            ELSE (sum(op.line_sales_amount) - sum(c.total_cost)) / sum(op.line_sales_amount)
          END AS gross_margin_pct
        FROM read_parquet(?) op
        LEFT JOIN read_parquet(?) c
          ON op.order_id = c.order_id
         AND op.product_id = c.product_id
         AND op.store_id = c.store_id
        LEFT JOIN read_parquet(?) p
          ON p.product_id = op.product_id
        {where_sql}
        GROUP BY 1, 2
        HAVING gross_margin_pct IS NOT NULL
        ORDER BY gross_margin_pct {order_direction}, gross_profit_amount {order_direction}
        LIMIT ?
        """,
        [order_product_path, costing_path, products_path, *where_params, limit],
    )
