"""Delivery report queries against the monthly Gold contract."""

from data.cache_reader import table_path
from data.query_utils import MonthSelection, filter_sql, query
from shared.report_scope import ReportScope

COURIER = "delivery_courier_performance_monthly_store"
CourierTypeSelection = tuple[str, ...] | None


def _where(
    months: MonthSelection, store_id: int | None, courier_types: CourierTypeSelection
):
    where, params = filter_sql(
        month_column="month", months=months, store_column="store_id", store_id=store_id
    )
    if courier_types is not None:
        clause = "AND" if where else "WHERE"
        if not courier_types:
            where += f" {clause} 1 = 0"
        else:
            where += (
                f" {clause} courier_type IN ({', '.join('?' for _ in courier_types)})"
            )
            params.extend(courier_types)
    return where, params


def courier_types(store_id: int | None, scope: ReportScope):
    where, params = _where(None, store_id, None)
    return query(
        f"SELECT DISTINCT courier_type FROM CURIE_TABLE(?) {where} ORDER BY 1",
        [table_path(COURIER), *params],
        scope,
    )


def monthly_courier_orders(
    store_id: int | None, courier_types: CourierTypeSelection, scope: ReportScope
):
    where, params = _where(None, store_id, courier_types)
    return query(
        f"""
        WITH monthly AS (
          SELECT month, sum(delivered_order_count) AS delivered_order_count,
            count(DISTINCT courier_id) AS active_courier_count,
            sum(delivery_cost_amount) AS delivery_cost_amount
          FROM CURIE_TABLE(?) {where} GROUP BY month
        )
        SELECT month, delivered_order_count, active_courier_count,
          delivered_order_count::DOUBLE / nullif(active_courier_count, 0) AS avg_orders_per_courier,
          delivery_cost_amount,
          delivery_cost_amount::DOUBLE / nullif(delivered_order_count, 0) AS avg_delivery_cost_per_order
        FROM monthly ORDER BY month
        """,
        [table_path(COURIER), *params],
        scope,
    )


def courier_type_tariff(
    months: MonthSelection,
    store_id: int | None,
    courier_types: CourierTypeSelection,
    scope: ReportScope,
):
    where, params = _where(months, store_id, courier_types)
    return query(
        f"""
        WITH tariff AS (
          SELECT courier_type, sum(delivery_cost_amount) AS total_delivery_cost,
            sum(delivered_order_count) AS delivered_order_count,
            count(DISTINCT courier_id) AS active_courier_count
          FROM CURIE_TABLE(?) {where} GROUP BY courier_type
        )
        SELECT courier_type, total_delivery_cost, delivered_order_count,
          active_courier_count,
          total_delivery_cost::DOUBLE / nullif(delivered_order_count, 0) AS avg_delivery_cost_per_order
        FROM tariff ORDER BY total_delivery_cost DESC NULLS LAST
        """,
        [table_path(COURIER), *params],
        scope,
    )


def courier_workload(
    months: MonthSelection,
    store_id: int | None,
    courier_types: CourierTypeSelection,
    scope: ReportScope,
):
    where, params = _where(months, store_id, courier_types)
    return query(
        f"""SELECT any_value(fullname) AS fullname, courier_type,
          sum(delivered_order_count) AS delivered_order_count
          FROM CURIE_TABLE(?) {where} GROUP BY courier_id, courier_type
          ORDER BY delivered_order_count DESC""",
        [table_path(COURIER), *params],
        scope,
    )
