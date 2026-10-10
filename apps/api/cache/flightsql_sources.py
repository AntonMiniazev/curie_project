"""Fixed Flight SQL source contract for Curie's aggregate serving cache."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDataset:
    name: str
    source_query: str
    required_columns: tuple[str, ...]
    rls_key: str | None = None
    date_column: str | None = None
    order_id_chunk_size: int | None = None
    grain: tuple[str, ...] = ()
    expected_types: tuple[tuple[str, str], ...] = ()


def _aggregate(name: str, columns: str, grain: str) -> SourceDataset:
    required = tuple(columns.split())
    ids = {"store_id", "product_id", "courier_id", "client_id"}
    expected_types = tuple(
        (
            column,
            "DATE"
            if column == "month"
            else "INTEGER"
            if column in ids
            else "DECIMAL(14,4)"
            if column.endswith("_amount") or column == "budget_order_count"
            else "BIGINT"
            if column.endswith("_count")
            or column in {"client_base_start", "churned_clients"}
            else "VARCHAR",
        )
        for column in required
    )
    return SourceDataset(
        name=name,
        source_query=f"SELECT {', '.join(required)} FROM iceberg_gold.gold.{name}",
        required_columns=required,
        rls_key="store_id",
        date_column="month",
        grain=tuple(grain.split()),
        expected_types=expected_types,
    )


# Names and columns match .local/ampere_gold/gold_data_contract.json.
# The client-month bridge is the only relation with an identity grain.
SOURCES: tuple[SourceDataset, ...] = (
    _aggregate(
        "marketing_sales_budget_monthly_store",
        "month store_id store_name city sales_amount order_count budget_sales_amount budget_order_count",
        "month store_id",
    ),
    _aggregate(
        "marketing_product_sales_monthly_store",
        "month store_id store_name city product_id product_name category_name sales_amount order_count",
        "month store_id product_id",
    ),
    _aggregate(
        "marketing_category_sales_monthly_store",
        "month store_id store_name city category_name sales_amount order_count",
        "month store_id category_name",
    ),
    _aggregate(
        "marketing_client_metrics_monthly_store",
        "month store_id store_name city active_client_count new_client_count client_base_start churned_clients",
        "month store_id",
    ),
    _aggregate(
        "marketing_active_client_month",
        "month store_id client_id",
        "month store_id client_id",
    ),
    _aggregate(
        "financial_performance_monthly_store",
        "month store_id store_name city revenue_amount product_cost_amount delivery_cost_amount gross_profit_amount budget_revenue_amount",
        "month store_id",
    ),
    _aggregate(
        "financial_product_margin_monthly_store",
        "month store_id store_name city product_id product_name category_name revenue_amount product_cost_amount",
        "month store_id product_id",
    ),
    _aggregate(
        "delivery_courier_performance_monthly_store",
        "month store_id store_name city courier_id fullname courier_type delivered_order_count delivery_cost_amount",
        "month store_id courier_id",
    ),
)
