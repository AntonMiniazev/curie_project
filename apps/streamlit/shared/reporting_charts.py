"""Reusable Altair chart builders for Curie reporting dashboards.

This module owns chart presentation details that should stay consistent across
Marketing, Finance, and Delivery: Curie colors, transparent backgrounds,
legend placement, and axis padding.
"""

from __future__ import annotations

import altair as alt
import polars as pl

from shared.reporting_format import CURIE_COLORS


def sales_and_average_bill_chart(
    monthly_sales: pl.DataFrame,
    average_bill: pl.DataFrame,
    sales_vs_budget: pl.DataFrame,
) -> alt.LayerChart:
    """Render monthly sales/budget performance with average bill as a line."""
    measure_data = (
        monthly_sales.join(
            average_bill.select(["month", "average_bill_amount"]),
            on="month",
            how="left",
        )
        .join(
            sales_vs_budget.select(
                ["month", "actual_sales_amount", "budget_sales_amount"]
            ),
            on="month",
            how="left",
        )
        .pipe(
            _float_columns,
            ["sales_amount", "actual_sales_amount", "budget_sales_amount"],
        )
        .pipe(_float_columns, ["average_bill_amount"])
        .with_columns(
            pl.coalesce(["actual_sales_amount", "sales_amount", pl.lit(0.0)]).alias(
                "actual_sales_amount"
            ),
            pl.coalesce(["budget_sales_amount", pl.lit(0.0)]).alias(
                "budget_sales_amount"
            ),
        )
        .with_columns(
            pl.min_horizontal("actual_sales_amount", "budget_sales_amount").alias(
                "base_sales_amount"
            ),
            (pl.col("budget_sales_amount") - pl.col("actual_sales_amount"))
            .clip(lower_bound=0)
            .alias("gap_to_budget_amount"),
            (pl.col("actual_sales_amount") - pl.col("budget_sales_amount"))
            .clip(lower_bound=0)
            .alias("over_budget_amount"),
            pl.max_horizontal("actual_sales_amount", "budget_sales_amount").alias(
                "bar_total_amount"
            ),
            pl.col("month").dt.strftime("%b %Y").alias("month_label"),
            pl.col("month").dt.strftime("%Y-%m-%d").alias("month_date"),
        )
        .pipe(
            _money_k_columns,
            [
                "base_sales_amount",
                "gap_to_budget_amount",
                "over_budget_amount",
                "actual_sales_amount",
                "budget_sales_amount",
                "bar_total_amount",
            ],
        )
    )
    bar_data = (
        measure_data.select(
            [
                "month_date",
                "month_label",
                "actual_sales_amount_k",
                "budget_sales_amount_k",
                "base_sales_amount_k",
                "gap_to_budget_amount_k",
                "over_budget_amount_k",
            ]
        )
        .unpivot(
            index=[
                "month_date",
                "month_label",
                "actual_sales_amount_k",
                "budget_sales_amount_k",
            ],
            variable_name="segment",
            value_name="amount_k",
        )
        .filter(pl.col("amount_k") > 0)
        .with_columns(
            pl.col("segment")
            .replace(
                {
                    "base_sales_amount_k": "Sales covered",
                    "gap_to_budget_amount_k": "Gap to budget",
                    "over_budget_amount_k": "Over budget",
                }
            )
            .alias("segment"),
            pl.col("segment")
            .replace(
                {
                    "base_sales_amount_k": 0,
                    "gap_to_budget_amount_k": 1,
                    "over_budget_amount_k": 1,
                }
            )
            .alias("segment_order"),
        )
        .to_dicts()
    )
    line_data = measure_data.select(
        [
            "month_date",
            "month_label",
            "average_bill_amount",
        ]
    ).to_dicts()
    month_order = _month_order([*bar_data, *line_data])
    sales_bar = (
        alt.Chart(alt.Data(values=bar_data))
        .mark_bar()
        .encode(
            x=_month_axis(month_order),
            y=alt.Y("amount_k:Q", title="Sales $K", stack="zero"),
            color=alt.Color(
                "segment:N",
                title=None,
                scale=alt.Scale(
                    domain=["Sales covered", "Gap to budget", "Over budget"],
                    range=[
                        CURIE_COLORS["blue_l3"],
                        CURIE_COLORS["red_l1"],
                        CURIE_COLORS["green_l1"],
                    ],
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            order=alt.Order("segment_order:Q"),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("amount_k:Q", title="Segment $K", format=",.0f"),
                alt.Tooltip(
                    "actual_sales_amount_k:Q", title="Actual $K", format=",.0f"
                ),
                alt.Tooltip(
                    "budget_sales_amount_k:Q", title="Budget $K", format=",.0f"
                ),
            ],
        )
    )
    average_line = (
        alt.Chart(alt.Data(values=line_data))
        .transform_calculate(metric="'Average bill $'")
        .mark_line(
            point=alt.OverlayMarkDef(filled=False, fill="white"),
            color=CURIE_COLORS["muted"],
            interpolate="monotone",
        )
        .encode(
            x=_month_axis(month_order),
            y=alt.Y(
                "average_bill_amount:Q",
                title="Average bill $",
                axis=alt.Axis(
                    orient="right",
                ),
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                alt.Tooltip(
                    "average_bill_amount:Q", title="Average bill $", format=",.2f"
                )
            ],
        )
    )
    return _style_chart(
        alt.layer(
            sales_bar,
            average_line,
        ).resolve_scale(y="independent")
    )


def sales_vs_budget_chart(sales_vs_budget: pl.DataFrame) -> alt.Chart:
    """Render actual sales and budget sales as monthly comparison lines."""
    chart_data = (
        sales_vs_budget.pipe(
            _money_k_columns,
            ["actual_sales_amount", "budget_sales_amount"],
        )
        .with_columns(pl.col("month").dt.strftime("%b %Y").alias("month_label"))
        .with_columns(pl.col("month").dt.strftime("%Y-%m-%d").alias("month_date"))
        .select(
            [
                "month_date",
                "month_label",
                "actual_sales_amount_k",
                "budget_sales_amount_k",
            ]
        )
        .unpivot(
            index=["month_date", "month_label"],
            variable_name="metric",
            value_name="amount_k",
        )
        .with_columns(
            pl.col("metric")
            .replace(
                {
                    "actual_sales_amount_k": "Actual sales",
                    "budget_sales_amount_k": "Budget sales",
                }
            )
            .alias("metric")
        )
        .to_dicts()
    )
    month_order = _month_order(chart_data)
    return _style_chart(
        alt.Chart(alt.Data(values=chart_data))
        .mark_line(point=True)
        .encode(
            x=_month_axis(month_order),
            y=alt.Y("amount_k:Q", title="Sales $K"),
            color=alt.Color(
                "metric:N",
                title=None,
                scale=alt.Scale(
                    domain=["Actual sales", "Budget sales"],
                    range=[CURIE_COLORS["blue_l3"], CURIE_COLORS["blue_l4"]],
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("amount_k:Q", title="Sales $K", format=",.0f"),
            ],
        )
    )


def clients_chart(
    monthly_clients: pl.DataFrame,
    new_clients: pl.DataFrame,
    client_churn: pl.DataFrame,
) -> alt.LayerChart:
    """Render active/new client bars with churn percentage as a line."""
    client_bars = (
        monthly_clients.join(new_clients, on="month", how="full", coalesce=True)
        .fill_null(0)
        .with_columns(pl.col("month").dt.strftime("%b %Y").alias("month_label"))
        .with_columns(pl.col("month").dt.strftime("%Y-%m-%d").alias("month_date"))
        .select(
            ["month_date", "month_label", "active_client_count", "new_client_count"]
        )
        .unpivot(
            index=["month_date", "month_label"],
            variable_name="metric",
            value_name="client_count",
        )
        .with_columns(
            pl.col("metric")
            .replace(
                {
                    "active_client_count": "Active clients",
                    "new_client_count": "New clients",
                }
            )
            .alias("metric")
        )
        .with_columns(
            pl.col("metric")
            .replace({"Active clients": 0, "New clients": 1})
            .alias("metric_order")
        )
        .to_dicts()
    )
    churn_line_data = (
        _float_columns(client_churn, ["churn_pct"])
        .with_columns(pl.col("month").dt.strftime("%b %Y").alias("month_label"))
        .with_columns(pl.col("month").dt.strftime("%Y-%m-%d").alias("month_date"))
        .select(["month_date", "month_label", "churn_pct"])
        .to_dicts()
    )
    month_order = _month_order([*client_bars, *churn_line_data])

    bars = (
        alt.Chart(alt.Data(values=client_bars))
        .mark_bar()
        .encode(
            x=_month_axis(month_order),
            y=alt.Y("client_count:Q", title="Clients"),
            color=alt.Color(
                "metric:N",
                title=None,
                scale=alt.Scale(
                    domain=["Active clients", "New clients", "Churn %"],
                    range=[
                        CURIE_COLORS["blue_l3"],
                        CURIE_COLORS["blue_l4"],
                        CURIE_COLORS["red_l1"],
                    ],
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            order=alt.Order("metric_order:Q"),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("client_count:Q", title="Clients", format=",.0f"),
            ],
        )
    )
    churn_line = (
        alt.Chart(alt.Data(values=churn_line_data))
        .transform_calculate(metric="'Churn %'")
        .mark_line(
            point=alt.OverlayMarkDef(filled=False, fill="white"), interpolate="monotone"
        )
        .encode(
            x=_month_axis(month_order),
            y=alt.Y("churn_pct:Q", title="Churn %", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "metric:N",
                title=None,
                scale=alt.Scale(
                    domain=["Active clients", "New clients", "Churn %"],
                    range=[
                        CURIE_COLORS["blue_l3"],
                        CURIE_COLORS["blue_l4"],
                        CURIE_COLORS["red_l1"],
                    ],
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            tooltip=[alt.Tooltip("churn_pct:Q", title="Churn %", format=",.1f")],
        )
    )
    return _style_chart(alt.layer(bars, churn_line).resolve_scale(y="independent"))


def _float_columns(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Cast chart measure columns to float so Altair receives JSON-safe values."""
    expressions = [
        pl.col(column).cast(pl.Float64) for column in columns if column in df.columns
    ]
    return df.with_columns(expressions) if expressions else df


def _money_k_columns(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Add `$K` measure columns for readable chart axes."""
    expressions = [
        (pl.col(column).cast(pl.Float64) / 1_000).alias(f"{column}_k")
        for column in columns
        if column in df.columns
    ]
    return df.with_columns(expressions) if expressions else df


def _style_chart(chart: alt.Chart | alt.LayerChart) -> alt.Chart | alt.LayerChart:
    """Apply shared chart padding/theme without forcing light-mode backgrounds."""
    return (
        chart.properties(padding={"left": 12, "right": 18, "top": 12, "bottom": 12})
        .configure(background="transparent")
        .configure_axis(labelPadding=6, titlePadding=14)
        .configure_legend(orient="top", direction="horizontal", title=None)
        .configure_view(
            fill="transparent",
            stroke=None,
        )
    )


def _metric_color(domain: list[str], colors: list[str]) -> alt.Color:
    """Build a stable legend/color mapping for layered chart series."""
    return alt.Color(
        "metric:N",
        title=None,
        scale=alt.Scale(domain=domain, range=colors),
        legend=alt.Legend(orient="top", direction="horizontal"),
    )


def _month_axis(month_order: list[str]) -> alt.X:
    """Use month labels as categories with an explicit chronological order."""
    return alt.X(
        "month_label:N",
        title="Month",
        sort=month_order,
        axis=alt.Axis(labelAngle=0, labelExpr="replace(datum.label, ' ', '\\n')"),
    )


def _month_order(rows: list[dict[str, object]]) -> list[str]:
    """Return unique month labels ordered by the hidden ISO month date."""
    ordered: dict[str, str] = {}
    for row in sorted(rows, key=lambda item: str(item["month_date"])):
        ordered[str(row["month_label"])] = str(row["month_date"])
    return list(ordered)
