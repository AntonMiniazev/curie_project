"""DuckDB query layer for Delivery reporting over Curie's local cache."""

from __future__ import annotations

from data.cache_reader import table_path
from data.query_utils import MonthSelection, filter_sql, query

CourierTypeSelection = tuple[str, ...] | None


def _add_courier_type_filter(
    where_sql: str,
    where_params: list[object],
    courier_types: CourierTypeSelection,
) -> tuple[str, list[object]]:
    """Append a courier-type condition to an existing WHERE clause."""
    if courier_types is None:
        return where_sql, where_params

    clause = "AND" if where_sql else "WHERE"
    if not courier_types:
        return f"{where_sql} {clause} 1 = 0", where_params

    placeholders = ", ".join(["?"] * len(courier_types))
    return (
        f"{where_sql} {clause} coalesce(r.courier_type, 'Unknown') IN ({placeholders})",
        [*where_params, *courier_types],
    )


def delivery_courier_types(store_id: int | None = None):
    """Return courier types available in delivered orders for the selected store."""
    deliveries_path = str(table_path("fct_deliveries"))
    orders_path = str(table_path("fct_orders_sales"))
    resource_path = str(table_path("dim_resource"))
    where_sql, where_params = filter_sql(store_column="o.store_id", store_id=store_id)
    return query(
        f"""
        WITH order_couriers AS (
          SELECT DISTINCT
            order_id,
            courier_id
          FROM read_parquet(?)
          WHERE courier_id IS NOT NULL
        )
        SELECT DISTINCT
          coalesce(r.courier_type, 'Unknown') AS courier_type
        FROM order_couriers
        JOIN read_parquet(?) o USING (order_id)
        LEFT JOIN read_parquet(?) r USING (courier_id)
        {where_sql}
        ORDER BY 1
        """,
        [deliveries_path, orders_path, resource_path, *where_params],
    )


def delivery_monthly_courier_orders(
    store_id: int | None = None,
    courier_types: CourierTypeSelection = None,
):
    """Return monthly order workload and average orders per active courier."""
    deliveries_path = str(table_path("fct_deliveries"))
    orders_path = str(table_path("fct_orders_sales"))
    delivery_cost_path = str(table_path("dim_delivery_cost"))
    resource_path = str(table_path("dim_resource"))
    where_sql, where_params = filter_sql(store_column="o.store_id", store_id=store_id)
    where_sql, where_params = _add_courier_type_filter(
        where_sql,
        where_params,
        courier_types,
    )
    return query(
        f"""
        WITH delivered_orders AS (
          SELECT DISTINCT
            d.order_id,
            d.courier_id
          FROM read_parquet(?) d
          WHERE d.courier_id IS NOT NULL
        )
        SELECT
          date_trunc('month', o.order_date) AS month,
          count(DISTINCT delivered_orders.order_id) AS delivered_order_count,
          count(DISTINCT delivered_orders.courier_id) AS active_courier_count,
          count(DISTINCT delivered_orders.order_id)::DOUBLE
            / nullif(count(DISTINCT delivered_orders.courier_id), 0) AS avg_orders_per_courier,
          sum(coalesce(dc.tariff, 0)) AS delivery_cost_amount,
          sum(coalesce(dc.tariff, 0))::DOUBLE
            / nullif(count(DISTINCT delivered_orders.order_id), 0) AS avg_delivery_cost_per_order
        FROM delivered_orders
        JOIN read_parquet(?) o USING (order_id)
        LEFT JOIN read_parquet(?) dc USING (order_id)
        LEFT JOIN read_parquet(?) r USING (courier_id)
        {where_sql}
        GROUP BY 1
        ORDER BY 1
        """,
        [
            deliveries_path,
            orders_path,
            delivery_cost_path,
            resource_path,
            *where_params,
        ],
    )


def delivery_courier_type_tariff(
    months: MonthSelection = None,
    store_id: int | None = None,
    courier_types: CourierTypeSelection = None,
):
    """Return delivery tariff split by courier type for a selected period/store."""
    deliveries_path = str(table_path("fct_deliveries"))
    orders_path = str(table_path("fct_orders_sales"))
    delivery_cost_path = str(table_path("dim_delivery_cost"))
    resource_path = str(table_path("dim_resource"))
    where_sql, where_params = filter_sql(
        month_column="o.order_date",
        months=months,
        store_column="o.store_id",
        store_id=store_id,
    )
    where_sql, where_params = _add_courier_type_filter(
        where_sql,
        where_params,
        courier_types,
    )
    return query(
        f"""
        WITH order_couriers AS (
          SELECT DISTINCT
            order_id,
            courier_id
          FROM read_parquet(?)
          WHERE courier_id IS NOT NULL
        )
        SELECT
          coalesce(r.courier_type, 'Unknown') AS courier_type,
          sum(coalesce(dc.tariff, 0)) AS total_delivery_cost,
          count(DISTINCT order_couriers.order_id) AS delivered_order_count,
          count(DISTINCT order_couriers.courier_id) AS active_courier_count,
          sum(coalesce(dc.tariff, 0))::DOUBLE
            / nullif(count(DISTINCT order_couriers.order_id), 0) AS avg_delivery_cost_per_order
        FROM order_couriers
        JOIN read_parquet(?) o USING (order_id)
        LEFT JOIN read_parquet(?) dc USING (order_id)
        LEFT JOIN read_parquet(?) r USING (courier_id)
        {where_sql}
        GROUP BY 1
        ORDER BY total_delivery_cost DESC NULLS LAST
        """,
        [
            deliveries_path,
            orders_path,
            delivery_cost_path,
            resource_path,
            *where_params,
        ],
    )


def delivery_courier_workload(
    months: MonthSelection = None,
    store_id: int | None = None,
    courier_types: CourierTypeSelection = None,
):
    """Return courier-level delivered order counts for operational review."""
    deliveries_path = str(table_path("fct_deliveries"))
    orders_path = str(table_path("fct_orders_sales"))
    resource_path = str(table_path("dim_resource"))
    where_sql, where_params = filter_sql(
        month_column="o.order_date",
        months=months,
        store_column="o.store_id",
        store_id=store_id,
    )
    where_sql, where_params = _add_courier_type_filter(
        where_sql,
        where_params,
        courier_types,
    )
    return query(
        f"""
        WITH order_couriers AS (
          SELECT DISTINCT
            order_id,
            courier_id
          FROM read_parquet(?)
          WHERE courier_id IS NOT NULL
        )
        SELECT
          r.fullname,
          r.courier_type,
          count(DISTINCT order_couriers.order_id) AS delivered_order_count
        FROM order_couriers
        JOIN read_parquet(?) o USING (order_id)
        LEFT JOIN read_parquet(?) r USING (courier_id)
        {where_sql}
        GROUP BY 1, 2
        ORDER BY delivered_order_count DESC
        """,
        [deliveries_path, orders_path, resource_path, *where_params],
    )
