"""Delivery Operations dashboard backed by Curie's local cache."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

import polars as pl
import streamlit as st

import shared.reporting_charts as reporting_charts
from shared.access_control import current_report_access
from data.cache_reader import load_manifest
from data.delivery_queries import (
    delivery_courier_types,
    delivery_courier_type_tariff,
    delivery_courier_workload,
    delivery_monthly_courier_orders,
)
from shared.reporting_charts import delivery_tariff_donut_chart, delivery_workload_chart
from shared.reporting_controls import (
    chart_key,
    dataframe_with_download,
    reset_layout_control,
    selected_months,
    selected_store_id,
    sum_column,
)
from shared.reporting_format import (
    available_months,
    available_years,
    data_freshness,
    filter_month_range,
    filter_years,
    format_table_column,
    format_value,
)
from shared.reporting_ui import kpi_grid, apply_shared_css


st.set_page_config(
    page_title="Delivery Operations",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_shared_css()


@st.cache_data(show_spinner=False)
def _monthly_courier_orders(
    store_id: int | None,
    courier_types: tuple[str, ...] | None,
    cache_key: str,
) -> pl.DataFrame:
    """Cached monthly courier workload query."""
    return delivery_monthly_courier_orders(
        store_id=store_id,
        courier_types=courier_types,
    )


@st.cache_data(show_spinner=False)
def _courier_types(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached list of courier types available to Delivery filters."""
    return delivery_courier_types(store_id=store_id)


@st.cache_data(show_spinner=False)
def _courier_type_tariff(
    months: tuple[date, ...],
    store_id: int | None,
    courier_types: tuple[str, ...] | None,
    cache_key: str,
) -> pl.DataFrame:
    """Cached tariff-by-courier-type query."""
    return delivery_courier_type_tariff(
        months=list(months) or None,
        store_id=store_id,
        courier_types=courier_types,
    )


@st.cache_data(show_spinner=False)
def _courier_workload(
    months: tuple[date, ...],
    store_id: int | None,
    courier_types: tuple[str, ...] | None,
    cache_key: str,
) -> pl.DataFrame:
    """Cached courier workload table query."""
    return delivery_courier_workload(
        months=list(months) or None,
        store_id=store_id,
        courier_types=courier_types,
    )


def _period_day_count(start_month: date | None, end_month: date | None) -> int | None:
    """Return the inclusive day count covered by the selected month range."""
    if start_month is None or end_month is None:
        return None

    end_day = monthrange(end_month.year, end_month.month)[1]
    end_date = end_month.replace(day=end_day)
    return (end_date - start_month).days + 1


def _filter_couriers_by_name(
    courier_workload: pl.DataFrame,
    search_text: str,
) -> pl.DataFrame:
    """Apply the courier-name search box to the workload table."""
    query_text = search_text.strip().lower()
    if not query_text or courier_workload.is_empty():
        return courier_workload

    return courier_workload.filter(
        pl.col("fullname").fill_null("").str.to_lowercase().str.contains(
            query_text,
            literal=True,
        )
    )


MONTHLY_DELIVERY_COLUMNS = [
    format_table_column(
        source="month",
        label="Month",
        kind="month",
    ),
    format_table_column(
        source="delivered_order_count",
        label="Delivered Orders",
        kind="integer",
    ),
    format_table_column(
        source="active_courier_count",
        label="Active Couriers",
        kind="integer",
    ),
    format_table_column(
        source="avg_orders_per_courier",
        label="Avg Orders / Courier",
        kind="number",
        decimals=2,
    ),
    format_table_column(
        source="delivery_cost_amount",
        label="Delivery Cost",
        kind="money",
        decimals=2,
    ),
    format_table_column(
        source="avg_delivery_cost_per_order",
        label="Avg Delivery Cost",
        kind="money",
        decimals=2,
    ),
]

COURIER_WORKLOAD_COLUMNS = [
    format_table_column(
        source="fullname",
        label="Courier",
    ),
    format_table_column(
        source="courier_type",
        label="Courier Type",
    ),
    format_table_column(
        source="delivered_order_count",
        label="Delivered Orders",
        kind="integer",
    ),
]

TARIFF_COLUMNS = [
    format_table_column(
        source="courier_type",
        label="Courier Type",
    ),
    format_table_column(
        source="total_delivery_cost",
        label="Total Delivery Cost",
        kind="money",
        decimals=2,
    ),
    format_table_column(
        source="avg_delivery_cost_per_order",
        label="Avg Tariff / Order",
        kind="money",
        decimals=2,
    ),
    format_table_column(
        source="delivered_order_count",
        label="Delivered Orders",
        kind="integer",
    ),
    format_table_column(
        source="active_courier_count",
        label="Active Couriers",
        kind="integer",
    ),
]


manifest = load_manifest()
cache_key = manifest.get("release_id") or manifest["created_at_utc"]
access = current_report_access()

st.title("Delivery Operations")
st.caption(data_freshness(manifest["created_at_utc"]))

if not access.is_allowed:
    st.error(
        access.error or "Your Curie role does not allow access to this report data."
    )
    st.stop()

st.caption(f"Data access: {access.label}")
reset_layout_control()

store_id = selected_store_id(access, key="delivery_store")
courier_type_df = _courier_types(store_id, cache_key)
courier_type_options = courier_type_df.get_column("courier_type").to_list()
selected_courier_types = st.sidebar.multiselect(
    "Courier type",
    options=courier_type_options,
    default=courier_type_options,
    key="delivery_courier_type",
)
courier_types = (
    None
    if set(selected_courier_types) == set(courier_type_options)
    else tuple(selected_courier_types)
)

monthly_all = _monthly_courier_orders(store_id, courier_types, cache_key)

year_options = available_years(monthly_all)
selected_years = st.sidebar.multiselect(
    "Years",
    options=year_options,
    default=["2026"] if "2026" in year_options else year_options,
)

monthly = filter_years(monthly_all, selected_years)
months = selected_months(
    available_months(monthly),
    key=f"delivery_timeframe_{'_'.join(selected_years)}",
)
timeframe_start = months[0] if months else None
timeframe_end = months[-1] if months else None
monthly = filter_month_range(monthly, timeframe_start, timeframe_end)

tariff_by_type = (
    _courier_type_tariff(months, store_id, courier_types, cache_key)
    if months
    else pl.DataFrame()
)
courier_workload = (
    _courier_workload(months, store_id, courier_types, cache_key)
    if months
    else pl.DataFrame()
)

delivered_orders = sum_column(monthly, "delivered_order_count")
active_couriers = courier_workload.height if not courier_workload.is_empty() else None
period_days = _period_day_count(timeframe_start, timeframe_end)
avg_orders_per_courier_per_day = (
    delivered_orders / (active_couriers * period_days)
    if delivered_orders is not None and active_couriers and period_days
    else None
)
total_delivery_cost = sum_column(tariff_by_type, "total_delivery_cost")
avg_tariff_per_order = (
    total_delivery_cost / delivered_orders
    if total_delivery_cost is not None and delivered_orders
    else None
)

kpi_grid(
    [
        ("Delivered orders", format_value(delivered_orders, "number", decimals=0)),
        ("Active couriers", format_value(active_couriers, "number", decimals=0)),
        (
            "Avg orders / courier / day",
            format_value(avg_orders_per_courier_per_day, "decimal", decimals=2),
        ),
        ("Avg tariff / order", format_value(avg_tariff_per_order, "money", decimals=2)),
    ]
)

overview_tab, courier_tab = st.tabs(["Overview", "Couriers"])

with overview_tab:
    st.subheader("Courier Workload")
    st.altair_chart(
        delivery_workload_chart(monthly),
        width="stretch",
        key=chart_key("delivery_workload", reporting_charts.__file__),
    )

    st.subheader("Delivery Cost by Courier Type")
    st.altair_chart(
        delivery_tariff_donut_chart(tariff_by_type),
        width="stretch",
        key=chart_key("delivery_tariff", reporting_charts.__file__),
    )

    dataframe_with_download(
        name="tariff_by_courier_type",
        title="",
        df=tariff_by_type,
        columns=TARIFF_COLUMNS,
    )

with courier_tab:
    courier_search = st.text_input(
        "Search courier",
        key="delivery_courier_search",
        placeholder="Courier name",
    )
    courier_workload_table = _filter_couriers_by_name(courier_workload, courier_search)
    dataframe_with_download(
        name="courier_workload",
        title="Courier Workload Table",
        df=courier_workload_table,
        columns=COURIER_WORKLOAD_COLUMNS,
    )

    dataframe_with_download(
        name="monthly_delivery_metrics",
        title="Monthly Delivery Metrics",
        df=monthly,
        columns=MONTHLY_DELIVERY_COLUMNS,
    )
