"""Shared formatting helpers for Curie Streamlit reporting.

Marketing, Finance, and Delivery dashboards should use this module for common
table column aliases, numeric formatting, year filters, KPI text, and small
theme adjustments. Keep it domain-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import polars as pl
import streamlit as st


CURIE_COLORS = {
    "bg": "#f5f7fb",
    "surface": "#ffffff",
    "text": "#1d3557",
    "muted": "#455874",
    "border": "#d8e0eb",
    "blue_l1": "#1d3557",
    "blue_l2": "#455874",
    "blue_l3": "#457b9d",
    "blue_l4": "#70beef",
    "red_l1": "#e63946",
    "green_l1": "#2a9d8f",
}


@dataclass(frozen=True)
class ColumnSpec:
    """Declarative mapping from a source dataframe column to a report column."""

    source: str
    label: str
    kind: str = "text"


def apply_reporting_theme() -> None:
    """Apply light-touch Streamlit styling shared by all reporting dashboards."""
    st.markdown(
        f"""
        <style>
          :root {{
            --curie-bg: {CURIE_COLORS["bg"]};
            --curie-surface: {CURIE_COLORS["surface"]};
            --curie-text: {CURIE_COLORS["text"]};
            --curie-text-muted: {CURIE_COLORS["muted"]};
            --curie-border: {CURIE_COLORS["border"]};
            --curie-blue-l1: {CURIE_COLORS["blue_l1"]};
            --curie-blue-l3: {CURIE_COLORS["blue_l3"]};
            --curie-red-l1: {CURIE_COLORS["red_l1"]};
          }}
          [data-testid="stVegaLiteChart"] {{
            border: 1px solid var(--curie-border);
            border-radius: 8px;
            padding: 0.5rem;
          }}
          [data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def data_freshness(created_at_utc: str) -> str:
    """Format cache creation time for the report caption."""
    created_at = datetime.fromisoformat(created_at_utc)
    offset = created_at.strftime("%z")
    offset_label = f"UTC{offset[:3]}" if offset else "UTC"
    return f"Data freshness: {created_at:%d/%m/%Y %H:%M} ({offset_label})"


def filter_years(
    df: pl.DataFrame, years: Iterable[str], date_column: str = "month"
) -> pl.DataFrame:
    """Filter a dataframe by selected calendar years using a date/datetime column."""
    selected = [int(year) for year in years]
    if not selected or date_column not in df.columns or df.is_empty():
        return df

    return df.filter(pl.col(date_column).dt.year().is_in(selected))


def filter_month_range(
    df: pl.DataFrame,
    start_month: date | None,
    end_month: date | None,
    date_column: str = "month",
) -> pl.DataFrame:
    """Filter a dataframe to an inclusive month range."""
    if (
        start_month is None
        or end_month is None
        or date_column not in df.columns
        or df.is_empty()
    ):
        return df

    month_expr = pl.col(date_column).dt.date()
    return df.filter((month_expr >= start_month) & (month_expr <= end_month))


def available_years(*frames: pl.DataFrame, date_column: str = "month") -> list[str]:
    """Collect available years across report dataframes for a global year filter."""
    years: set[int] = set()
    for frame in frames:
        if date_column not in frame.columns or frame.is_empty():
            continue
        years.update(
            frame.select(pl.col(date_column).dt.year())
            .drop_nulls()
            .get_column(date_column)
            .to_list()
        )
    return [str(year) for year in sorted(years, reverse=True)]


def available_months(*frames: pl.DataFrame, date_column: str = "month") -> list[date]:
    """Collect available months across report dataframes in ascending order."""
    months: set[date] = set()
    for frame in frames:
        if date_column not in frame.columns or frame.is_empty():
            continue
        months.update(
            frame.select(pl.col(date_column).dt.date())
            .drop_nulls()
            .get_column(date_column)
            .to_list()
        )
    return sorted(months)


def default_timeframe(
    months: list[date], today: date | None = None
) -> tuple[date, date]:
    """Choose the default timeframe from first month to current/latest month."""
    if not months:
        raise ValueError("Cannot build a default timeframe without available months.")

    current_month = (today or date.today()).replace(day=1)
    available_until_now = [month for month in months if month <= current_month]
    end_month = available_until_now[-1] if available_until_now else months[-1]
    return months[0], end_month


def latest_row(df: pl.DataFrame, required_columns: list[str]) -> dict | None:
    """Return the latest month with all required KPI fields populated."""
    if df.is_empty():
        return None

    filtered = df.drop_nulls(required_columns)
    if filtered.is_empty():
        return None

    return filtered.sort("month").tail(1).to_dicts()[0]


def format_money_k(value: object | None) -> str:
    """Format a KPI money value in thousands."""
    if value is None:
        return "-"
    return f"${float(value) / 1_000:,.0f}K"


def format_money(value: object | None) -> str:
    """Format a KPI money value with cents."""
    if value is None:
        return "-"
    return f"${float(value):,.2f}"


def format_number(value: object | None) -> str:
    """Format a KPI count value."""
    if value is None:
        return "-"
    return f"{float(value):,.0f}"


def format_percent(value: object | None, *, already_percent: bool = False) -> str:
    """Format KPI percentage values from either ratio or already-percent inputs."""
    if value is None:
        return "-"

    numeric = float(value)
    if not already_percent:
        numeric *= 100
    return _format_percent_number(numeric)


def display_table(
    df: pl.DataFrame, columns: list[ColumnSpec]
) -> tuple[pl.DataFrame, dict[str, object]]:
    """Build a typed, aliased dataframe and Streamlit column config for display.

    Values stay as dates/numbers so Streamlit table sorting works correctly.
    Formatting is applied through `st.column_config`, not by converting values
    to strings.
    """
    select_expressions: list[pl.Expr] = []
    column_config: dict[str, object] = {}

    for column in columns:
        if column.source not in df.columns:
            continue

        expression = pl.col(column.source).alias(column.label)
        if column.kind == "month":
            expression = pl.col(column.source).dt.date().alias(column.label)
            column_config[column.label] = st.column_config.DateColumn(
                column.label,
                format="MMM YYYY",
            )
        elif column.kind in {"money", "money_2", "money_k", "number"}:
            expression = pl.col(column.source).cast(pl.Float64).alias(column.label)
            column_config[column.label] = st.column_config.NumberColumn(
                column.label,
                format=_number_format(column.kind),
            )
        elif column.kind in {"percent_ratio", "percent"}:
            expression = (
                _percent_expression(column.source, column.kind)
                .cast(pl.Float64)
                .alias(column.label)
            )
            column_config[column.label] = st.column_config.NumberColumn(
                column.label,
                format="percent",
            )

        select_expressions.append(expression)

    return df.select(select_expressions), column_config


def _format_cell(value: object | None, kind: str) -> str:
    if value is None:
        return "-"
    if kind == "month":
        return _format_month(value)
    if kind == "money":
        return f"${float(value):,.0f}"
    if kind == "money_2":
        return format_money(value)
    if kind == "money_k":
        return format_money_k(value)
    if kind == "number":
        return format_number(value)
    if kind == "percent_ratio":
        return format_percent(value)
    if kind == "percent":
        return format_percent(value, already_percent=True)
    return str(value)


def _number_format(kind: str) -> str:
    if kind == "money":
        return "dollar"
    if kind == "money_2":
        return "$%.2f"
    if kind == "money_k":
        return "compact"
    return "localized"


def _percent_expression(source: str, kind: str) -> pl.Expr:
    expression = pl.col(source)
    if kind == "percent":
        return expression / 100
    return expression


def _format_month(value: object) -> str:
    if isinstance(value, datetime | date):
        return value.strftime("%b %Y")
    return str(value)


def _format_percent_number(value: float) -> str:
    formatted = f"{value:,.2f}".rstrip("0").rstrip(".")
    if "." not in formatted:
        formatted = f"{formatted}.0"
    return f"{formatted}%"
