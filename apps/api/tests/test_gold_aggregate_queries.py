"""Contract query smoke checks with store RLS and distinct counts."""

from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from apps.api.cache import refresh_flightsql
from apps.api.cache.flightsql_sources import SourceDataset
from data import cache_reader, query_utils
from data import delivery_aggregate_queries as delivery
from data import finance_aggregate_queries as finance
from data import marketing_aggregate_queries as marketing
from shared.report_scope import ReportScope


def test_aggregate_reports_keep_scope_and_visual_shapes(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "current.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("CREATE SCHEMA cache")
        con.execute(
            "CREATE TABLE curie_release AS SELECT 'r' AS release_id, 'now' AS created_at_utc, 'flight' AS source_uri"
        )
        con.execute("CREATE TABLE curie_datasets (name VARCHAR, row_count BIGINT)")
        schemas = {
            marketing.SALES: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, sales_amount DECIMAL(14,4), order_count BIGINT, budget_sales_amount DECIMAL(14,4), budget_order_count DECIMAL(14,4)",
            marketing.PRODUCT: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, product_id INTEGER, product_name VARCHAR, category_name VARCHAR, sales_amount DECIMAL(14,4), order_count BIGINT",
            marketing.CATEGORY: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, category_name VARCHAR, sales_amount DECIMAL(14,4), order_count BIGINT",
            marketing.CLIENTS: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, active_client_count BIGINT, new_client_count BIGINT, client_base_start BIGINT, churned_clients BIGINT",
            marketing.ACTIVITY: "month DATE, store_id INTEGER, client_id INTEGER",
            finance.PERFORMANCE: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, revenue_amount DECIMAL(14,4), product_cost_amount DECIMAL(14,4), delivery_cost_amount DECIMAL(14,4), gross_profit_amount DECIMAL(14,4), budget_revenue_amount DECIMAL(14,4)",
            finance.PRODUCT: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, product_id INTEGER, product_name VARCHAR, category_name VARCHAR, revenue_amount DECIMAL(14,4), product_cost_amount DECIMAL(14,4)",
            delivery.COURIER: "month DATE, store_id INTEGER, store_name VARCHAR, city VARCHAR, courier_id INTEGER, fullname VARCHAR, courier_type VARCHAR, delivered_order_count BIGINT, delivery_cost_amount DECIMAL(14,4)",
        }
        for name, schema in schemas.items():
            con.execute(f"CREATE TABLE cache.{name} ({schema})")
            con.execute("INSERT INTO curie_datasets VALUES (?, 1)", [name])
        con.execute(
            f"INSERT INTO cache.{marketing.SALES} VALUES ('2026-01-01',1,'One','A',100,2,80,2), ('2026-01-01',2,'Two','B',200,4,100,3)"
        )
        con.execute(
            f"INSERT INTO cache.{marketing.ACTIVITY} VALUES ('2026-01-01',1,7), ('2026-01-01',2,7), ('2026-02-01',1,7)"
        )
        con.execute(
            f"INSERT INTO cache.{marketing.PRODUCT} VALUES ('2026-01-01',1,'One','A',10,'P','C',100,2)"
        )
        con.execute(
            f"INSERT INTO cache.{marketing.CATEGORY} VALUES ('2026-01-01',1,'One','A','C',100,1)"
        )
        con.execute(
            f"INSERT INTO cache.{marketing.CLIENTS} VALUES ('2026-01-01',1,'One','A',1,2,10,1)"
        )
        con.execute(
            f"INSERT INTO cache.{finance.PERFORMANCE} VALUES ('2026-01-01',1,'One','A',100,50,10,40,80), ('2026-01-01',2,'Two','B',200,70,20,110,100)"
        )
        con.execute(
            f"INSERT INTO cache.{finance.PRODUCT} VALUES ('2026-01-01',1,'One','A',10,'P','C',100,50)"
        )
        con.execute(
            f"INSERT INTO cache.{delivery.COURIER} VALUES ('2026-01-01',1,'One','A',9,'Courier','Bike',2,10), ('2026-01-01',2,'Two','B',8,'Other','Car',3,15)"
        )
    settings = SimpleNamespace(serving_cache_current=path)
    monkeypatch.setattr(cache_reader, "get_settings", lambda: settings)
    scoped = ReportScope("one@example.com", False, (1,), "one")
    region = ReportScope("region@example.com", True, (), "region")

    assert cache_reader.aggregate_cache_active()
    assert marketing.monthly_sales(None, scoped)["sales_amount"].item() == 100
    assert marketing.monthly_sales(None, region)["sales_amount"].item() == 300
    assert marketing.monthly_clients(None, region)["active_client_count"][0] == 1
    assert (
        marketing.active_clients(None, None, region)["active_client_count"].item() == 1
    )
    assert (
        marketing.top_categories(None, "orders", 5, None, scoped)["order_count"].item()
        == 1
    )
    assert (
        finance.monthly_performance(None, scoped)["operational_profit_amount"].item()
        == 30
    )
    assert (
        finance.product_margin(None, None, 5, "top", scoped)[
            "gross_profit_amount"
        ].item()
        == 50
    )
    assert (
        delivery.monthly_courier_orders(None, None, scoped)[
            "delivered_order_count"
        ].item()
        == 2
    )
    assert (
        delivery.courier_type_tariff(None, None, None, scoped)[
            "total_delivery_cost"
        ].item()
        == 10
    )
    assert query_utils.store_dimension(scoped, "Financial")["store_id"].to_list() == [1]


def test_refresh_rejects_duplicate_aggregate_grain() -> None:
    source = SourceDataset(
        name="sample",
        source_query="SELECT * FROM iceberg_gold.gold.sample",
        required_columns=("month", "store_id", "value"),
        rls_key="store_id",
        date_column="month",
        grain=("month", "store_id"),
    )
    with duckdb.connect(":memory:") as con:
        con.execute("CREATE SCHEMA cache")
        con.execute(
            "CREATE TABLE cache.sample (month DATE, store_id INTEGER, value INTEGER)"
        )
        con.execute(
            "INSERT INTO cache.sample VALUES ('2026-01-01', 1, 10), ('2026-01-01', 1, 20)"
        )
        with pytest.raises(RuntimeError, match="duplicate rows at grain"):
            refresh_flightsql._validate_and_record(con, source)
