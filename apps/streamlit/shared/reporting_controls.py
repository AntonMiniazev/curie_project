"""Reusable Streamlit controls for Curie reporting dashboards."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import pandas as pd
import polars as pl
import streamlit as st
from shared.reporting_ui import current_report_colors
from shared.access_control import ReportAccess, restrict_store_options
from data.query_utils import store_dimension
from shared.reporting_format import (
    TableColumn,
    default_timeframe,
    prepare_table,
)


def store_options() -> list[tuple[str, int | None]]:
    """Return report store selector options from the cached store dimension."""
    options: list[tuple[str, int | None]] = [("All stores", None)]
    for row in store_dimension().iter_rows(named=True):
        options.append((f"{row['store_name']} ({row['city']})", int(row["store_id"])))
    return options


def selected_store_id(access: ReportAccess, key: str = "store") -> int | None:
    """Render a store selector scoped to the current user's report access."""
    options = restrict_store_options(store_options(), access)
    if not options:
        return None

    selected_label = st.sidebar.selectbox(
        "Store",
        options=[label for label, _ in options],
        disabled=not access.can_view_all_stores and len(options) == 1,
        key=key,
    )
    return dict(options)[selected_label]


def selected_months(months: list[date], key: str = "timeframe") -> tuple[date, ...]:
    """Render a global month-range slicer and return selected months."""
    if not months:
        st.sidebar.caption("No months available for the selected years.")
        return ()

    month_options = [(month.strftime("%b %Y"), month) for month in months]
    month_labels = [label for label, _ in month_options]
    default_start, default_end = default_timeframe(months)
    default_value = (default_start.strftime("%b %Y"), default_end.strftime("%b %Y"))

    if len(month_labels) == 1:
        st.sidebar.selectbox("Timeframe", options=month_labels, disabled=True, key=key)
        return tuple(months)

    selected_start_label, selected_end_label = st.sidebar.select_slider(
        "Timeframe",
        options=month_labels,
        value=default_value,
        key=key,
    )
    start_index = month_labels.index(selected_start_label)
    end_index = month_labels.index(selected_end_label)
    return tuple(month for _, month in month_options[start_index : end_index + 1])


def reset_layout_control() -> None:
    """Render a reset button that remounts stateful tables and charts."""
    if "report_layout_version" not in st.session_state:
        st.session_state.report_layout_version = 0

    if st.sidebar.button("Reset table and chart layout"):
        st.session_state.report_layout_version += 1
        st.rerun()


def table_key(name: str) -> str:
    """Return a key that changes when users reset manual table layout changes."""
    return f"{name}_{st.session_state.get('report_layout_version', 0)}"


def chart_key(name: str, source_path: str | Path) -> str:
    """Return a chart key that updates when shared chart code changes."""
    chart_version = Path(source_path).stat().st_mtime_ns
    return f"{name}_{st.session_state.get('report_layout_version', 0)}_{chart_version}"


def style_report_table(
    df: pl.DataFrame,
) -> pd.io.formats.style.Styler:
    """Apply Curie colors and alternating row backgrounds."""
    colors = current_report_colors()
    pandas_df = df.to_pandas()

    def row_background(row: pd.Series) -> list[str]:
        background = colors["surface"] if row.name % 2 == 0 else colors["surface_muted"]

        return [f"background-color: {background}; color: {colors['text']}" for _ in row]

    return pandas_df.style.apply(
        row_background,
        axis=1,
    )


def dataframe_with_download(
    *,
    name: str,
    title: str,
    df: pl.DataFrame,
    columns: list[TableColumn],
) -> None:
    """Render a themed dataframe with CSV download."""
    display_df, column_config = prepare_table(df, columns)
    styled_df = style_report_table(display_df)

    title_column, download_column = st.columns(
        [12, 1],
        vertical_alignment="center",
        gap="small",
    )

    with title_column:
        st.subheader(title)

    with download_column:
        st.download_button(
            "",
            data=display_df.write_csv().encode("utf-8"),
            file_name=f"{name}.csv",
            mime="text/csv",
            key=f"{table_key(name)}_download",
            help="Download CSV",
            icon=":material/download:",
            on_click="ignore",
            width="content",
        )

    st.dataframe(
        styled_df,
        column_config=column_config,
        width="stretch",
        hide_index=True,
        key=table_key(name),
    )


def plain_dataframe(name: str, df: pl.DataFrame) -> None:
    """Render a native Streamlit dataframe without column remapping."""
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        key=table_key(name),
    )


def sum_column(df: pl.DataFrame, column: str) -> float | None:
    """Return a numeric column sum for the selected reporting frame."""
    if df.is_empty() or column not in df.columns:
        return None

    value = df.select(pl.col(column).sum()).item()
    return None if value is None else float(value)
