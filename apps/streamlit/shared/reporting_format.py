"""Shared formatting helpers for Curie Streamlit reporting.

Marketing, Finance, and Delivery dashboards should use this module for common
table column aliases, numeric formatting, year filters, and KPI values. Keep it
domain-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Literal

import polars as pl
import streamlit as st


FormatKind = Literal[
    "text",
    "number",
    "decimal",
    "integer",
    "money",
    "money_k",
    "money_accounting",
    "percent",
    "month",
]


@dataclass(frozen=True)
class ValueFormat:
    """Shared scalar and table formatting defaults for one semantic value type."""

    kind: FormatKind
    decimals: int = 0
    divisor: float = 1
    prefix: str = ""
    suffix: str = ""
    empty: str = "-"
    table_format: str | None = None
    date_format: str | None = None


@dataclass(frozen=True)
class TableColumn:
    """Prepared Polars expression and Streamlit configuration for one column."""

    source: str
    label: str
    expression: pl.Expr
    config: Any | None = None


DEFAULT_FORMATS: dict[FormatKind, ValueFormat] = {
    "text": ValueFormat(
        kind="text",
    ),
    "number": ValueFormat(
        kind="number",
        decimals=0,
        table_format="%,.0f",
    ),
    "decimal": ValueFormat(
        kind="decimal",
        decimals=2,
        table_format="%,.2f",
    ),
    "integer": ValueFormat(
        kind="integer",
        decimals=0,
        table_format="%,d",
    ),
    "money": ValueFormat(
        kind="money",
        decimals=2,
        prefix="$",
        table_format="$%,.2f",
    ),
    "money_k": ValueFormat(
        kind="money_k",
        decimals=0,
        divisor=1_000,
        prefix="$",
        suffix="K",
        table_format="$%,.0fK",
    ),
    "money_accounting": ValueFormat(
        kind="money_accounting",
        decimals=2,
        prefix="$",
        table_format="accounting",
    ),
    "percent": ValueFormat(
        kind="percent",
        decimals=2,
        suffix="%",
        table_format="percent",
    ),
    "month": ValueFormat(
        kind="month",
        date_format="MMM YY",
    ),
}


def data_freshness(created_at_utc: str) -> str:
    """Format cache creation time for the report caption."""
    created_at = datetime.fromisoformat(created_at_utc)
    offset = created_at.strftime("%z")
    offset_label = f"UTC{offset[:3]}" if offset else "UTC"
    return f"Data freshness: {created_at:%d/%m/%Y %H:%M} ({offset_label})"


def filter_years(
    df: pl.DataFrame,
    years: Iterable[str],
    date_column: str = "month",
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
    months: list[date],
    today: date | None = None,
) -> tuple[date, date]:
    """Choose the default timeframe from first month to current/latest month."""
    if not months:
        raise ValueError("Cannot build a default timeframe without available months.")

    current_month = (today or date.today()).replace(day=1)
    available_until_now = [month for month in months if month <= current_month]
    end_month = available_until_now[-1] if available_until_now else months[-1]
    return months[0], end_month


def prepare_table(
    df: pl.DataFrame,
    columns: list[TableColumn],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Prepare a typed dataframe and its Streamlit column configuration."""
    available_columns = [column for column in columns if column.source in df.columns]

    display_df = df.select([column.expression for column in available_columns])

    column_config = {
        column.label: column.config
        for column in available_columns
        if column.config is not None
    }

    return display_df, column_config


def format_table_column(
    source: str,
    label: str,
    kind: FormatKind = "text",
    *,
    width: str | int | None = None,
    decimals: int | None = None,
    date_format: str | None = None,
) -> TableColumn:
    """Build a table column using defaults shared with scalar value formatting."""
    spec = DEFAULT_FORMATS[kind]
    expression = pl.col(source)

    if kind == "text":
        config = st.column_config.TextColumn(label, width=width)

    elif kind == "month":
        expression = expression.dt.date()
        config = st.column_config.DateColumn(
            label,
            format=date_format or spec.date_format or "MMM YY",
            width=width,
        )

    elif kind == "integer":
        expression = expression.cast(pl.Int64)
        config = st.column_config.NumberColumn(
            label,
            format=spec.table_format,
            width=width,
        )

    elif kind in {"number", "decimal", "money", "money_k"}:
        expression = expression.cast(pl.Float64)
        if spec.divisor != 1:
            expression = expression / spec.divisor

        precision = spec.decimals if decimals is None else decimals
        table_format = _numeric_table_format(spec, precision)

        config = st.column_config.NumberColumn(
            label,
            format=table_format,
            width=width,
        )

    elif kind == "money_accounting":
        expression = expression.cast(pl.Float64)
        config = st.column_config.NumberColumn(
            label,
            format=spec.table_format,
            width=width,
        )

    elif kind == "percent":
        # Input is always a ratio: 0.1 is displayed as 10%.
        expression = expression.cast(pl.Float64)
        config = st.column_config.NumberColumn(
            label,
            format=spec.table_format,
            width=width,
        )

    else:
        raise ValueError(f"Unsupported column kind: {kind!r}")

    return TableColumn(
        source=source,
        label=label,
        expression=expression.alias(label),
        config=config,
    )


def format_value(
    value: object | None,
    kind: FormatKind,
    *,
    decimals: int | None = None,
    empty: str | None = None,
) -> str:
    """Format a scalar value using shared predefined display defaults."""
    spec = DEFAULT_FORMATS[kind]

    if value is None:
        return empty if empty is not None else spec.empty

    if kind == "text":
        return str(value)

    if kind == "month":
        if isinstance(value, datetime | date):
            return value.strftime("%b %y")
        return str(value)

    numeric = float(value)

    if kind == "percent":
        numeric *= 100

    numeric /= spec.divisor
    precision = spec.decimals if decimals is None else decimals

    if kind == "money_accounting" and numeric < 0:
        return f"({spec.prefix}{abs(numeric):,.{precision}f})"

    return f"{spec.prefix}{numeric:,.{precision}f}{spec.suffix}"


def _numeric_table_format(spec: ValueFormat, precision: int) -> str:
    """Build a Streamlit printf-style format from a shared value specification."""
    return f"{spec.prefix}%,.{precision}f{spec.suffix}"
