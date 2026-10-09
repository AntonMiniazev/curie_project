"""Financial report queries against the monthly Gold contract."""

from data.cache_reader import table_path
from data.query_utils import MonthSelection, filter_sql, query
from shared.report_scope import ReportScope

PERFORMANCE = "curie_financial_performance_monthly_store"
PRODUCT = "curie_financial_product_margin_monthly_store"


def monthly_performance(store_id: int | None, scope: ReportScope):
    where, params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        WITH monthly AS (
          SELECT month, sum(revenue_amount) AS revenue_amount,
            sum(budget_revenue_amount) AS budget_revenue_amount,
            sum(product_cost_amount) AS product_cost_amount,
            sum(delivery_cost_amount) AS delivery_cost_amount,
            sum(gross_profit_amount) AS gross_profit_amount
          FROM CURIE_TABLE(?) {where} GROUP BY month
        )
        SELECT month, revenue_amount, budget_revenue_amount,
          revenue_amount - budget_revenue_amount AS revenue_variance_amount,
          revenue_amount / nullif(budget_revenue_amount, 0) - 1 AS revenue_variance_pct,
          product_cost_amount, delivery_cost_amount, gross_profit_amount,
          gross_profit_amount / nullif(revenue_amount, 0) AS gross_margin_pct,
          gross_profit_amount - delivery_cost_amount AS operational_profit_amount
        FROM monthly ORDER BY month
        """,
        [table_path(PERFORMANCE), *params],
        scope,
    )


def store_monthly_performance(store_id: int | None, scope: ReportScope):
    where, params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        WITH monthly AS (
          SELECT month, store_id, any_value(store_name) AS store_name,
            any_value(city) AS city, sum(revenue_amount) AS revenue_amount,
            sum(product_cost_amount) AS product_cost_amount,
            sum(delivery_cost_amount) AS delivery_cost_amount,
            sum(gross_profit_amount) AS gross_profit_amount
          FROM CURIE_TABLE(?) {where} GROUP BY month, store_id
        )
        SELECT month, store_id, store_name, city, revenue_amount,
          product_cost_amount, delivery_cost_amount, gross_profit_amount,
          gross_profit_amount / nullif(revenue_amount, 0) AS gross_margin_pct,
          gross_profit_amount - delivery_cost_amount AS operational_profit_amount
        FROM monthly ORDER BY month, store_name
        """,
        [table_path(PERFORMANCE), *params],
        scope,
    )


def product_margin(
    months: MonthSelection,
    store_id: int | None,
    limit: int,
    direction: str,
    scope: ReportScope,
):
    if direction not in {"top", "bottom"}:
        raise ValueError("direction must be either 'top' or 'bottom'.")
    where, params = filter_sql(
        month_column="month", months=months, store_column="store_id", store_id=store_id
    )
    order = "DESC" if direction == "top" else "ASC"
    return query(
        f"""
        WITH products AS (
          SELECT product_id, any_value(product_name) AS product_name,
            any_value(category_name) AS category_name,
            sum(revenue_amount) AS revenue_amount,
            sum(product_cost_amount) AS product_cost_amount
          FROM CURIE_TABLE(?) {where} GROUP BY product_id
        )
        SELECT product_name, category_name, revenue_amount, product_cost_amount,
          revenue_amount - product_cost_amount AS gross_profit_amount,
          (revenue_amount - product_cost_amount) / nullif(revenue_amount, 0) AS gross_margin_pct
        FROM products WHERE revenue_amount <> 0
        ORDER BY gross_margin_pct {order}, gross_profit_amount {order} LIMIT ?
        """,
        [table_path(PRODUCT), *params, limit],
        scope,
    )
