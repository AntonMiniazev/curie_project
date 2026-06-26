"""Finance Performance dashboard backed by Curie's local cache."""

from __future__ import annotations

from datetime import date

import polars as pl
import streamlit as st

import shared.reporting_charts as reporting_charts
from shared.access_control import current_report_access
from data.cache_reader import load_manifest
from data.finance_queries import (
    finance_monthly_performance,
    finance_product_margin,
    finance_store_monthly_performance,
)
from shared.reporting_charts import finance_performance_chart
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
    page_title="Finance Performance",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_shared_css()


@st.cache_data(show_spinner=False)
def _monthly_performance(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached monthly Finance performance query."""
    return finance_monthly_performance(store_id=store_id)


@st.cache_data(show_spinner=False)
def _store_monthly_performance(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached store-level Finance performance query."""
    return finance_store_monthly_performance(store_id=store_id)


@st.cache_data(show_spinner=False)
def _product_margin(
    months: tuple[date, ...],
    direction: str,
    store_id: int | None,
    cache_key: str,
) -> pl.DataFrame:
    """Cached product margin ranking query."""
    return finance_product_margin(
        months=list(months) or None,
        store_id=store_id,
        limit=5,
        direction=direction,
    )


OPERATIONAL_PL_COLUMNS = [
    format_table_column(
        source="Metric",
        label="Metric",
    ),
    format_table_column(
        source="FY up to date",
        label="FY up to date",
    ),
    format_table_column(
        source="Current month",
        label="Current month",
    ),
    format_table_column(
        source="Vs prev. month",
        label="Vs prev. month",
    ),
]

MONTHLY_FINANCE_COLUMNS = [
    format_table_column(
        source="month",
        label="Month",
        kind="month",
    ),
    format_table_column(
        source="revenue_amount",
        label="Revenue",
        kind="money_accounting",
    ),
    format_table_column(
        source="budget_revenue_amount",
        label="Budget Revenue",
        kind="money_accounting",
    ),
    format_table_column(
        source="revenue_variance_amount",
        label="Variance",
        kind="money_accounting",
    ),
    format_table_column(
        source="revenue_variance_pct",
        label="Variance %",
        kind="percent",
    ),
    format_table_column(
        source="gross_profit_amount",
        label="Gross Profit",
        kind="money_accounting",
    ),
    format_table_column(
        source="gross_margin_pct",
        label="Gross Margin %",
        kind="percent",
    ),
    format_table_column(
        source="operational_profit_amount",
        label="Operational Profit",
        kind="money_accounting",
    ),
]

PRODUCT_MARGIN_COLUMNS = [
    format_table_column(
        source="product_name",
        label="Product",
    ),
    format_table_column(
        source="category_name",
        label="Category",
    ),
    format_table_column(
        source="revenue_amount",
        label="Revenue",
        kind="money_accounting",
    ),
    format_table_column(
        source="product_cost_amount",
        label="Product Cost",
        kind="money_accounting",
    ),
    format_table_column(
        source="gross_profit_amount",
        label="Gross Profit",
        kind="money_accounting",
    ),
    format_table_column(
        source="gross_margin_pct",
        label="Gross Margin %",
        kind="percent",
    ),
]


def _period_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or not denominator:
        return None
    return numerator / denominator


def _pl_row(
    label: str, current: float | None, previous: float | None, ytd: float | None
) -> dict:
    return {
        "Metric": label,
        "FY up to date": format_value(ytd, "number"),
        "Current month": format_value(current, "number"),
        "Vs prev. month": format_value(
            None if current is None or previous is None else current - previous,
            "number",
        ),
    }


def _operational_pl(monthly: pl.DataFrame) -> pl.DataFrame:
    """Build the compact operational P&L table from monthly Finance data."""
    if monthly.is_empty():
        return pl.DataFrame(
            {
                "Metric": [],
                "FY up to date": [],
                "Current month": [],
                "Vs prev. month": [],
            }
        )

    ordered = monthly.sort("month")
    current = ordered.tail(1).to_dicts()[0]
    previous = ordered.tail(2).head(1).to_dicts()[0] if ordered.height > 1 else {}

    revenue_ytd = sum_column(ordered, "revenue_amount")
    gross_profit_ytd = sum_column(ordered, "gross_profit_amount")
    margin_ytd = _period_ratio(gross_profit_ytd, revenue_ytd)
    current_margin = _period_ratio(
        current.get("gross_profit_amount"),
        current.get("revenue_amount"),
    )
    previous_margin = _period_ratio(
        previous.get("gross_profit_amount"),
        previous.get("revenue_amount"),
    )

    rows = [
        _pl_row(
            "Revenue",
            current.get("revenue_amount"),
            previous.get("revenue_amount"),
            revenue_ytd,
        ),
        _pl_row(
            "Product cost",
            current.get("product_cost_amount"),
            previous.get("product_cost_amount"),
            sum_column(ordered, "product_cost_amount"),
        ),
        _pl_row(
            "Gross profit",
            current.get("gross_profit_amount"),
            previous.get("gross_profit_amount"),
            gross_profit_ytd,
        ),
        _pl_row(
            "Delivery cost",
            current.get("delivery_cost_amount"),
            previous.get("delivery_cost_amount"),
            sum_column(ordered, "delivery_cost_amount"),
        ),
        _pl_row(
            "Operational profit",
            current.get("operational_profit_amount"),
            previous.get("operational_profit_amount"),
            sum_column(ordered, "operational_profit_amount"),
        ),
        {
            "Metric": "Gross margin %",
            "FY up to date": format_value(margin_ytd, "percent"),
            "Current month": format_value(current_margin, "percent"),
            "Vs prev. month": format_value(
                None
                if current_margin is None or previous_margin is None
                else current_margin - previous_margin,
                "percent",
            ),
        },
    ]
    return pl.DataFrame(rows)


manifest = load_manifest()
cache_key = manifest.get("release_id") or manifest["created_at_utc"]
access = current_report_access()

st.title("Finance Performance")
st.caption(data_freshness(manifest["created_at_utc"]))

if not access.is_allowed:
    st.error(
        access.error or "Your Curie role does not allow access to this report data."
    )
    st.stop()

st.caption(f"Data access: {access.label}")
reset_layout_control()

store_id = selected_store_id(access, key="finance_store")
monthly_all = _monthly_performance(store_id, cache_key)
store_monthly_all = _store_monthly_performance(store_id, cache_key)

year_options = available_years(monthly_all)
selected_years = st.sidebar.multiselect(
    "Years",
    options=year_options,
    default=["2026"] if "2026" in year_options else year_options,
)

monthly = filter_years(monthly_all, selected_years)
store_monthly = filter_years(store_monthly_all, selected_years)
months = selected_months(
    available_months(monthly, store_monthly),
    key=f"finance_timeframe_{'_'.join(selected_years)}",
)
timeframe_start = months[0] if months else None
timeframe_end = months[-1] if months else None
monthly = filter_month_range(monthly, timeframe_start, timeframe_end)
store_monthly = filter_month_range(store_monthly, timeframe_start, timeframe_end)

revenue = sum_column(monthly, "revenue_amount")
gross_profit = sum_column(monthly, "gross_profit_amount")
operational_profit = sum_column(monthly, "operational_profit_amount")
variance = sum_column(monthly, "revenue_variance_amount")
gross_margin = _period_ratio(gross_profit, revenue)
variance_pct = _period_ratio(variance, sum_column(monthly, "budget_revenue_amount"))

kpi_grid(
    [
        ("Revenue", format_value(revenue, "money", decimals=0)),
        ("Gross profit", format_value(gross_profit, "money", decimals=0)),
        ("Gross margin", format_value(gross_margin, "percent")),
        ("Operational profit", format_value(operational_profit, "money", decimals=0)),
        ("Revenue variance", format_value(variance, "money", decimals=0)),
        ("Variance %", format_value(variance_pct, "percent")),
    ]
)

overview_tab, products_tab, stores_tab = st.tabs(["Overview", "Products", "Stores"])

with overview_tab:
    st.subheader("Revenue and Margin Dynamics")
    st.altair_chart(
        finance_performance_chart(monthly),
        width="stretch",
        key=chart_key("finance_performance", reporting_charts.__file__),
    )

    dataframe_with_download(
        name="finance_operational_pl",
        title="Operational P&L",
        df=_operational_pl(monthly),
        columns=OPERATIONAL_PL_COLUMNS,
    )

with products_tab:
    if months:
        top_margin = _product_margin(months, "top", store_id, cache_key)
        bottom_margin = _product_margin(months, "bottom", store_id, cache_key)
    else:
        top_margin = pl.DataFrame()
        bottom_margin = pl.DataFrame()

    dataframe_with_download(
        name="top_margin_products",
        title="Top 5 Margin Products",
        df=top_margin,
        columns=PRODUCT_MARGIN_COLUMNS,
    )

    dataframe_with_download(
        name="bottom_margin_products",
        title="Bottom 5 Margin Products",
        df=bottom_margin,
        columns=PRODUCT_MARGIN_COLUMNS,
    )

with stores_tab:
    dataframe_with_download(
        name="store_finance_performance",
        title="Store Finance Performance",
        df=store_monthly,
        columns=MONTHLY_FINANCE_COLUMNS,
    )
