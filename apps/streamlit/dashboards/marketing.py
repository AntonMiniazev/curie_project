"""Marketing Reporting dashboard backed by Curie's local cache.

The page is intentionally thin: it orchestrates filters, KPIs, tabs, exports,
and cached calls into `shared.marketing_queries`. Query definitions, table
formatting, and chart styling live in reusable `shared` modules.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl
import streamlit as st

import shared.reporting_charts as reporting_charts
from shared.access_control import current_report_access, restrict_store_options
from shared.cache_reader import load_manifest
from shared.marketing_queries import (
    marketing_active_clients,
    marketing_average_bill_by_month,
    marketing_client_churn_by_month,
    marketing_monthly_clients,
    marketing_monthly_sales,
    marketing_monthly_sales_vs_budget,
    marketing_new_clients_by_month,
    marketing_store_monthly_sales_vs_budget,
    marketing_top_categories,
    marketing_top_products,
)
from shared.reporting_charts import (
    clients_chart,
    sales_and_average_bill_chart,
)
from shared.reporting_format import (
    ColumnSpec,
    apply_reporting_theme,
    available_months,
    available_years,
    data_freshness,
    display_table,
    default_timeframe,
    filter_month_range,
    filter_years,
    format_money,
    format_money_k,
    format_number,
    format_percent,
)
from shared.reporting_ui import kpi_grid


st.set_page_config(page_title="Marketing Reporting", layout="wide")
apply_reporting_theme()


def _manifest() -> dict:
    return load_manifest()


@st.cache_data(show_spinner=False)
def _monthly_sales(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached monthly sales query; `cache_key` invalidates on cache release."""
    return marketing_monthly_sales(store_id=store_id)


@st.cache_data(show_spinner=False)
def _average_bill_by_month(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached average bill query for the Sales Dynamics block."""
    return marketing_average_bill_by_month(store_id=store_id)


@st.cache_data(show_spinner=False)
def _monthly_clients(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached active-client query for the Client Base block."""
    return marketing_monthly_clients(store_id=store_id)


@st.cache_data(show_spinner=False)
def _active_clients(
    months: tuple[date, ...], store_id: int | None, cache_key: str
) -> pl.DataFrame:
    """Cached distinct active-client KPI query for the selected timeframe."""
    return marketing_active_clients(months=list(months) or None, store_id=store_id)


@st.cache_data(show_spinner=False)
def _client_churn_by_month(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached churn query for the Client Base block."""
    return marketing_client_churn_by_month(store_id=store_id)


@st.cache_data(show_spinner=False)
def _monthly_sales_vs_budget(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached actual-vs-budget query for total monthly Sales reporting."""
    return marketing_monthly_sales_vs_budget(store_id=store_id)


@st.cache_data(show_spinner=False)
def _store_monthly_sales_vs_budget(
    store_id: int | None, cache_key: str
) -> pl.DataFrame:
    """Cached actual-vs-budget query for the store-level Sales table."""
    return marketing_store_monthly_sales_vs_budget(store_id=store_id)


@st.cache_data(show_spinner=False)
def _top_products(
    months: tuple[date, ...],
    metric: str,
    limit: int,
    store_id: int | None,
    cache_key: str,
) -> pl.DataFrame:
    """Cached top-product query for the Products tab ranking block."""
    return marketing_top_products(
        months=list(months) or None,
        metric=metric,
        limit=limit,
        store_id=store_id,
    )


@st.cache_data(show_spinner=False)
def _top_categories(
    months: tuple[date, ...],
    metric: str,
    limit: int,
    store_id: int | None,
    cache_key: str,
) -> pl.DataFrame:
    """Cached top-category query for the Products tab ranking block."""
    return marketing_top_categories(
        months=list(months) or None,
        metric=metric,
        limit=limit,
        store_id=store_id,
    )


@st.cache_data(show_spinner=False)
def _new_clients_by_month(store_id: int | None, cache_key: str) -> pl.DataFrame:
    """Cached new-client query for the Client Base block."""
    return marketing_new_clients_by_month(store_id=store_id)


def _month_options(
    months: list[date],
) -> list[tuple[str, date]]:
    """Build month labels and values for the global timeframe slicer."""
    return [(month.strftime("%b %Y"), month) for month in months]


def _store_options(store_sales_vs_budget: pl.DataFrame) -> list[tuple[str, int | None]]:
    """Build sidebar store choices from store-level reporting data."""
    stores = (
        store_sales_vs_budget.select(["store_id", "store_name", "city"])
        .drop_nulls("store_id")
        .unique()
        .sort("store_name")
    )
    options: list[tuple[str, int | None]] = [("All stores", None)]
    for row in stores.iter_rows(named=True):
        options.append((f"{row['store_name']} ({row['city']})", int(row["store_id"])))
    return options


def _table_key(name: str) -> str:
    """Return a remountable key so users can reset manual table layout changes."""
    return f"{name}_{st.session_state.get('report_layout_version', 0)}"


def _chart_key(name: str) -> str:
    """Return a remountable key so chart frontend state can be reset."""
    charts_version = Path(reporting_charts.__file__).stat().st_mtime_ns
    return f"{name}_{st.session_state.get('report_layout_version', 0)}_{charts_version}"


def _dataframe(name: str, df: pl.DataFrame, columns: list[ColumnSpec]) -> None:
    """Render one report table with typed formatting and a CSV export button."""
    display_df, column_config = display_table(df, columns)
    _, download_column = st.columns([0.96, 0.04])
    download_column.download_button(
        "",
        data=display_df.write_csv().encode("utf-8"),
        file_name=f"{name}.csv",
        mime="text/csv",
        key=f"{_table_key(name)}_download",
        help="Download CSV",
        icon=":material/download:",
        on_click="ignore",
        width="content",
    )
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config=column_config,
        key=_table_key(name),
    )


def _empty_frame_like(df: pl.DataFrame) -> pl.DataFrame:
    """Return an empty dataframe with the same schema as a query result."""
    return df.head(0)


def _sum_column(df: pl.DataFrame, column: str) -> float | None:
    """Return a numeric column sum for the selected reporting timeframe."""
    if df.is_empty() or column not in df.columns:
        return None

    value = df.select(pl.col(column).sum()).item()
    return None if value is None else float(value)


def _period_average_bill(monthly_sales: pl.DataFrame) -> float | None:
    """Return average bill across the selected timeframe."""
    sales_amount = _sum_column(monthly_sales, "sales_amount")
    order_count = _sum_column(monthly_sales, "order_count")
    if sales_amount is None or not order_count:
        return None
    return sales_amount / order_count


def _period_variance_pct(sales_vs_budget: pl.DataFrame) -> float | None:
    """Return actual-vs-budget percent for the selected timeframe."""
    actual_sales = _sum_column(sales_vs_budget, "actual_sales_amount")
    budget_sales = _sum_column(sales_vs_budget, "budget_sales_amount")
    if actual_sales is None or not budget_sales:
        return None
    return actual_sales / budget_sales - 1


def _period_churn_pct(client_churn: pl.DataFrame) -> float | None:
    """Return weighted churn percent across selected months."""
    churned_clients = _sum_column(client_churn, "churned_clients")
    client_base = _sum_column(client_churn, "client_base_start")
    if churned_clients is None or not client_base:
        return None
    return churned_clients / client_base * 100


# Table column contracts stay near the dashboard because they are report-specific
# labels, while `display_table` remains reusable across future dashboard blocks.
STORE_SALES_VS_BUDGET_COLUMNS = [
    ColumnSpec("month", "Month", "month"),
    ColumnSpec("store_name", "Store"),
    ColumnSpec("city", "City"),
    ColumnSpec("actual_sales_amount", "Actual Sales", "money"),
    ColumnSpec("budget_sales_amount", "Budget Sales", "money"),
    ColumnSpec("sales_variance_amount", "Variance", "money"),
    ColumnSpec("sales_variance_pct", "Variance %", "percent_ratio"),
    ColumnSpec("actual_order_count", "Actual Orders", "number"),
    ColumnSpec("budget_order_count", "Budget Orders", "number"),
]

TOP_PRODUCT_COLUMNS = [
    ColumnSpec("product_name", "Product"),
    ColumnSpec("category_name", "Category"),
    ColumnSpec("sales_amount", "Sales", "money"),
    ColumnSpec("order_count", "Orders", "number"),
]

TOP_CATEGORY_COLUMNS = [
    ColumnSpec("category_name", "Category"),
    ColumnSpec("sales_amount", "Sales", "money"),
    ColumnSpec("order_count", "Orders", "number"),
]


manifest = _manifest()
cache_key = manifest.get("release_id") or manifest["created_at_utc"]
all_store_sales_vs_budget = _store_monthly_sales_vs_budget(None, cache_key)
access = current_report_access()
store_options = restrict_store_options(
    _store_options(all_store_sales_vs_budget), access
)

st.title("Marketing Reporting")
st.caption(data_freshness(manifest["created_at_utc"]))

if not access.is_allowed or not store_options:
    st.error(
        access.error or "Your Curie role does not allow access to this report data."
    )
    st.stop()

st.caption(f"Data access: {access.label}")

if "report_layout_version" not in st.session_state:
    st.session_state.report_layout_version = 0

# Streamlit does not expose a native "reset resized columns" control. Incrementing
# the component keys remounts tables/charts without a full browser refresh.
if st.sidebar.button("Reset table and chart layout"):
    st.session_state.report_layout_version += 1
    st.rerun()

selected_store_label = st.sidebar.selectbox(
    "Store",
    options=[label for label, _ in store_options],
    disabled=not access.can_view_all_stores and len(store_options) == 1,
)
selected_store_id = dict(store_options)[selected_store_label]

monthly_sales_all = _monthly_sales(selected_store_id, cache_key)
average_bill_all = _average_bill_by_month(selected_store_id, cache_key)
monthly_clients_all = _monthly_clients(selected_store_id, cache_key)
client_churn_all = _client_churn_by_month(selected_store_id, cache_key)
sales_vs_budget_all = _monthly_sales_vs_budget(selected_store_id, cache_key)
store_sales_vs_budget_all = (
    all_store_sales_vs_budget
    if selected_store_id is None
    else _store_monthly_sales_vs_budget(selected_store_id, cache_key)
)
new_clients_all = _new_clients_by_month(selected_store_id, cache_key)

year_options = available_years(
    monthly_sales_all,
    average_bill_all,
    monthly_clients_all,
    client_churn_all,
    sales_vs_budget_all,
    new_clients_all,
)
default_years = [
    year for year in ["2026", "2025"] if year in year_options
] or year_options
selected_years = st.sidebar.multiselect(
    "Years",
    options=year_options,
    default=["2026"],
)

monthly_sales = filter_years(monthly_sales_all, selected_years)
average_bill = filter_years(average_bill_all, selected_years)
monthly_clients = filter_years(monthly_clients_all, selected_years)
client_churn = filter_years(client_churn_all, selected_years)
sales_vs_budget = filter_years(sales_vs_budget_all, selected_years)
store_sales_vs_budget = filter_years(store_sales_vs_budget_all, selected_years)
new_clients = filter_years(new_clients_all, selected_years)

timeframe_months = available_months(
    monthly_sales,
    average_bill,
    monthly_clients,
    client_churn,
    sales_vs_budget,
    store_sales_vs_budget,
    new_clients,
)

if timeframe_months:
    month_options = _month_options(timeframe_months)
    month_labels = [label for label, _ in month_options]
    default_start, default_end = default_timeframe(timeframe_months)
    default_start_label = default_start.strftime("%b %Y")
    default_end_label = default_end.strftime("%b %Y")

    if len(month_labels) > 1:
        selected_start_label, selected_end_label = st.sidebar.select_slider(
            "Timeframe",
            options=month_labels,
            value=(default_start_label, default_end_label),
            key=f"timeframe_{'_'.join(selected_years)}",
        )
        start_index = month_labels.index(selected_start_label)
        end_index = month_labels.index(selected_end_label)
        selected_months = tuple(
            month for _, month in month_options[start_index : end_index + 1]
        )
    else:
        st.sidebar.selectbox(
            "Timeframe",
            options=month_labels,
            disabled=True,
            key=f"timeframe_{'_'.join(selected_years)}",
        )
        selected_months = tuple(timeframe_months)

    timeframe_start = selected_months[0]
    timeframe_end = selected_months[-1]
else:
    st.sidebar.caption("No months available for the selected years.")
    selected_months = ()
    timeframe_start = None
    timeframe_end = None

monthly_sales = filter_month_range(monthly_sales, timeframe_start, timeframe_end)
average_bill = filter_month_range(average_bill, timeframe_start, timeframe_end)
monthly_clients = filter_month_range(monthly_clients, timeframe_start, timeframe_end)
client_churn = filter_month_range(client_churn, timeframe_start, timeframe_end)
sales_vs_budget = filter_month_range(sales_vs_budget, timeframe_start, timeframe_end)
store_sales_vs_budget = filter_month_range(
    store_sales_vs_budget,
    timeframe_start,
    timeframe_end,
)
new_clients = filter_month_range(new_clients, timeframe_start, timeframe_end)

period_sales_amount = _sum_column(monthly_sales, "sales_amount")
period_order_count = _sum_column(monthly_sales, "order_count")
period_average_bill = _period_average_bill(monthly_sales)
period_active_clients = (
    _active_clients(selected_months, selected_store_id, cache_key)
    .select("active_client_count")
    .item()
    if selected_months
    else None
)
period_budget_variance = _sum_column(sales_vs_budget, "sales_variance_amount")
period_variance_pct = _period_variance_pct(sales_vs_budget)
period_churn_pct = _period_churn_pct(client_churn)

kpi_grid(
    [
        ("Sales", format_money_k(period_sales_amount)),
        ("Orders", format_number(period_order_count)),
        ("Average bill", format_money(period_average_bill)),
        ("Active clients", format_number(period_active_clients)),
        ("Budget variance", format_money_k(period_budget_variance)),
        ("Variance %", format_percent(period_variance_pct)),
        ("Churn %", format_percent(period_churn_pct, already_percent=True)),
    ]
)

sales_tab, clients_tab, products_tab = st.tabs(["Sales", "Clients", "Products"])

with sales_tab:
    # Sales block: monthly sales dynamics, average bill, and actual-vs-budget.
    st.subheader("Sales Dynamics")
    st.altair_chart(
        sales_and_average_bill_chart(monthly_sales, average_bill, sales_vs_budget),
        width="stretch",
        key=_chart_key("sales_average_bill"),
    )

    st.subheader("Store Sales vs Budget")
    _dataframe(
        "store_sales_vs_budget",
        store_sales_vs_budget,
        STORE_SALES_VS_BUDGET_COLUMNS,
    )

with clients_tab:
    # Clients block: active/new clients and churn based on dim_clients events.
    st.subheader("Client Base")
    st.altair_chart(
        clients_chart(monthly_clients, new_clients, client_churn),
        width="stretch",
        key=_chart_key("clients"),
    )
    st.caption(
        "Churn % = clients churned during month / client base at start of month * 100."
    )

with products_tab:
    # Products block: ranking metric is local; timeframe comes from global filters.
    ranking_metric_label = st.segmented_control(
        "Ranking metric",
        options=["By sales $", "By orders"],
        default="By sales $",
    )

    ranking_metric = "sales" if ranking_metric_label == "By sales $" else "orders"
    if selected_months:
        top_products = _top_products(
            selected_months,
            ranking_metric,
            10,
            selected_store_id,
            cache_key,
        )
        top_categories = _top_categories(
            selected_months,
            ranking_metric,
            10,
            selected_store_id,
            cache_key,
        )
    else:
        top_products = _empty_frame_like(
            _top_products((), ranking_metric, 1, selected_store_id, cache_key)
        )
        top_categories = _empty_frame_like(
            _top_categories((), ranking_metric, 1, selected_store_id, cache_key)
        )

    st.subheader("Top Products")
    _dataframe("top_products", top_products, TOP_PRODUCT_COLUMNS)

    st.subheader("Top Categories")
    _dataframe("top_categories", top_categories, TOP_CATEGORY_COLUMNS)
