"""Marketing report queries against the monthly Gold contract."""

from data.cache_reader import table_path
from data.query_utils import MonthSelection, filter_sql, query
from shared.report_scope import ReportScope

SALES = "curie_marketing_sales_budget_monthly_store"
PRODUCT = "curie_marketing_product_sales_monthly_store"
CATEGORY = "curie_marketing_category_sales_monthly_store"
CLIENTS = "curie_marketing_client_metrics_monthly_store"
ACTIVITY = "curie_marketing_active_client_month"


def _monthly(table: str, fields: str, store_id: int | None, scope: ReportScope):
    where, params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"SELECT month, {fields} FROM CURIE_TABLE(?) {where} GROUP BY month ORDER BY month",
        [table_path(table), *params],
        scope,
    )


def monthly_sales(store_id: int | None, scope: ReportScope):
    return _monthly(
        SALES,
        "sum(sales_amount) AS sales_amount, sum(order_count) AS order_count",
        store_id,
        scope,
    )


def average_bill_by_month(store_id: int | None, scope: ReportScope):
    return _monthly(
        SALES,
        "sum(sales_amount) AS sales_amount, sum(order_count) AS order_count, "
        "sum(sales_amount) / nullif(sum(order_count), 0) AS average_bill_amount",
        store_id,
        scope,
    )


def monthly_clients(store_id: int | None, scope: ReportScope):
    where, params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""SELECT month, count(DISTINCT client_id) AS active_client_count
        FROM CURIE_TABLE(?) {where} GROUP BY month ORDER BY month""",
        [table_path(ACTIVITY), *params],
        scope,
    )


def active_clients(months: MonthSelection, store_id: int | None, scope: ReportScope):
    where, params = filter_sql(
        month_column="month", months=months, store_column="store_id", store_id=store_id
    )
    return query(
        f"SELECT count(DISTINCT client_id) AS active_client_count FROM CURIE_TABLE(?) {where}",
        [table_path(ACTIVITY), *params],
        scope,
    )


def client_churn_by_month(store_id: int | None, scope: ReportScope):
    return _monthly(
        CLIENTS,
        "sum(client_base_start) AS client_base_start, sum(churned_clients) AS churned_clients, "
        "100.0 * sum(churned_clients) / nullif(sum(client_base_start), 0) AS churn_pct",
        store_id,
        scope,
    )


def monthly_budget(store_id: int | None, scope: ReportScope):
    return _monthly(
        SALES,
        "sum(budget_sales_amount) AS budget_sales_amount, "
        "sum(budget_order_count) AS budget_order_count",
        store_id,
        scope,
    )


def monthly_sales_vs_budget(store_id: int | None, scope: ReportScope):
    where, params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        WITH monthly AS (
          SELECT month, sum(sales_amount) AS actual_sales_amount,
            sum(order_count) AS actual_order_count,
            sum(budget_sales_amount) AS budget_sales_amount,
            sum(budget_order_count) AS budget_order_count
          FROM CURIE_TABLE(?) {where} GROUP BY month
        )
        SELECT month, actual_sales_amount, budget_sales_amount,
          actual_sales_amount - budget_sales_amount AS sales_variance_amount,
          actual_sales_amount / nullif(budget_sales_amount, 0) - 1 AS sales_variance_pct,
          actual_order_count, budget_order_count
        FROM monthly ORDER BY month
        """,
        [table_path(SALES), *params],
        scope,
    )


def store_monthly_sales_vs_budget(store_id: int | None, scope: ReportScope):
    where, params = filter_sql(store_column="store_id", store_id=store_id)
    return query(
        f"""
        WITH monthly AS (
          SELECT month, store_id, any_value(store_name) AS store_name,
            any_value(city) AS city, sum(sales_amount) AS actual_sales_amount,
            sum(order_count) AS actual_order_count,
            sum(budget_sales_amount) AS budget_sales_amount,
            sum(budget_order_count) AS budget_order_count
          FROM CURIE_TABLE(?) {where} GROUP BY month, store_id
        )
        SELECT month, store_id, store_name, city, actual_sales_amount,
          budget_sales_amount,
          actual_sales_amount - budget_sales_amount AS sales_variance_amount,
          actual_sales_amount / nullif(budget_sales_amount, 0) - 1 AS sales_variance_pct,
          actual_order_count, budget_order_count
        FROM monthly ORDER BY month, store_name
        """,
        [table_path(SALES), *params],
        scope,
    )


def _top(
    table: str,
    label: str,
    months: MonthSelection,
    metric: str,
    limit: int,
    store_id: int | None,
    scope: ReportScope,
):
    if metric not in {"sales", "orders"}:
        raise ValueError("metric must be either 'sales' or 'orders'.")
    ranking = "sales_amount" if metric == "sales" else "order_count"
    where, params = filter_sql(
        month_column="month", months=months, store_column="store_id", store_id=store_id
    )
    labels = "product_name, category_name" if label == "product" else "category_name"
    return query(
        f"""SELECT {labels}, sum(sales_amount) AS sales_amount,
          sum(order_count) AS order_count FROM CURIE_TABLE(?) {where}
          GROUP BY {labels} ORDER BY {ranking} DESC NULLS LAST LIMIT ?""",
        [table_path(table), *params, limit],
        scope,
    )


def top_products(
    months: MonthSelection,
    metric: str,
    limit: int,
    store_id: int | None,
    scope: ReportScope,
):
    return _top(PRODUCT, "product", months, metric, limit, store_id, scope)


def top_categories(
    months: MonthSelection,
    metric: str,
    limit: int,
    store_id: int | None,
    scope: ReportScope,
):
    return _top(CATEGORY, "category", months, metric, limit, store_id, scope)


def new_clients_by_month(store_id: int | None, scope: ReportScope):
    return _monthly(
        CLIENTS, "sum(new_client_count) AS new_client_count", store_id, scope
    )
