"""Reusable Altair chart builders for Curie reporting dashboards.

This module owns chart presentation details that should stay consistent across
Marketing, Finance, and Delivery: Curie colors, transparent backgrounds,
legend placement, and axis padding.
"""

from __future__ import annotations

import altair as alt
import polars as pl

from shared.reporting_ui import current_report_colors as curie_colors


def sales_and_average_bill_chart(
    monthly_sales: pl.DataFrame,
    average_bill: pl.DataFrame,
    sales_vs_budget: pl.DataFrame,
) -> alt.LayerChart:
    """Render monthly sales/budget performance with average bill as a line."""
    colors = curie_colors()
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
                        colors["blue_l3"],
                        colors["red_l1"],
                        colors["green_l1"],
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
            color=colors["muted"],
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
    colors = curie_colors()
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
                    range=[colors["blue_l3"], colors["blue_l4"]],
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
    colors = curie_colors()
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
                        colors["blue_l3"],
                        colors["blue_l4"],
                        colors["red_l1"],
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
                        colors["blue_l3"],
                        colors["blue_l4"],
                        colors["red_l1"],
                    ],
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            tooltip=[alt.Tooltip("churn_pct:Q", title="Churn %", format=",.1f")],
        )
    )
    return _style_chart(alt.layer(bars, churn_line).resolve_scale(y="independent"))


def finance_performance_chart(monthly_finance: pl.DataFrame) -> alt.LayerChart:
    """Render revenue/budget bars with gross margin percent as a line."""
    colors = curie_colors()
    measure_data = (
        monthly_finance.pipe(
            _money_k_columns,
            ["revenue_amount", "budget_revenue_amount", "gross_profit_amount"],
        )
        .pipe(_float_columns, ["gross_margin_pct"])
        .with_columns(pl.col("month").dt.strftime("%b %Y").alias("month_label"))
        .with_columns(pl.col("month").dt.strftime("%Y-%m-%d").alias("month_date"))
    )
    bars_data = (
        measure_data.select(
            [
                "month_date",
                "month_label",
                "revenue_amount_k",
                "budget_revenue_amount_k",
                "gross_profit_amount_k",
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
                    "revenue_amount_k": "Revenue",
                    "budget_revenue_amount_k": "Budget revenue",
                    "gross_profit_amount_k": "Gross profit",
                }
            )
            .alias("metric")
        )
        .to_dicts()
    )
    margin_data = measure_data.select(
        ["month_date", "month_label", "gross_margin_pct"]
    ).to_dicts()
    month_order = _month_order([*bars_data, *margin_data])

    bars = (
        alt.Chart(alt.Data(values=bars_data))
        .mark_bar()
        .encode(
            x=_month_axis(month_order),
            y=alt.Y("amount_k:Q", title="$K"),
            xOffset=alt.XOffset("metric:N"),
            color=_metric_color(
                ["Revenue", "Budget revenue", "Gross profit"],
                [colors["blue_l3"], colors["blue_l4"], colors["green_l1"]],
            ),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("amount_k:Q", title="$K", format=",.0f"),
            ],
        )
    )
    margin_line = (
        alt.Chart(alt.Data(values=margin_data))
        .transform_calculate(metric="'Gross margin %'")
        .mark_line(
            color=colors["red_l1"],
            point=alt.OverlayMarkDef(filled=False, fill="white"),
            interpolate="monotone",
        )
        .encode(
            x=_month_axis(month_order),
            y=alt.Y(
                "gross_margin_pct:Q",
                title="Gross margin %",
                axis=alt.Axis(format=".1%"),
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip("gross_margin_pct:Q", title="Gross margin %", format=".1%"),
            ],
        )
    )
    return _style_chart(alt.layer(bars, margin_line).resolve_scale(y="independent"))


def delivery_workload_chart(monthly_delivery: pl.DataFrame) -> alt.LayerChart:
    """Render delivered orders with average orders per courier as a line."""
    colors = curie_colors()
    chart_data = (
        monthly_delivery.pipe(_float_columns, ["avg_orders_per_courier"])
        .with_columns(pl.col("month").dt.strftime("%b %Y").alias("month_label"))
        .with_columns(pl.col("month").dt.strftime("%Y-%m-%d").alias("month_date"))
    )
    bar_data = chart_data.select(
        ["month_date", "month_label", "delivered_order_count", "active_courier_count"]
    ).to_dicts()
    line_data = chart_data.select(
        ["month_date", "month_label", "avg_orders_per_courier"]
    ).to_dicts()
    month_order = _month_order([*bar_data, *line_data])

    bars = (
        alt.Chart(alt.Data(values=bar_data))
        .mark_bar(color=colors["blue_l3"])
        .encode(
            x=_month_axis(month_order),
            y=alt.Y("delivered_order_count:Q", title="Delivered orders"),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip(
                    "delivered_order_count:Q",
                    title="Delivered orders",
                    format=",.0f",
                ),
                alt.Tooltip(
                    "active_courier_count:Q", title="Active couriers", format=",.0f"
                ),
            ],
        )
    )
    line = (
        alt.Chart(alt.Data(values=line_data))
        .mark_line(
            color=colors["red_l1"],
            point=alt.OverlayMarkDef(filled=False, fill="white"),
            interpolate="monotone",
        )
        .encode(
            x=_month_axis(month_order),
            y=alt.Y(
                "avg_orders_per_courier:Q",
                title="Orders per courier",
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                alt.Tooltip("month_label:N", title="Month"),
                alt.Tooltip(
                    "avg_orders_per_courier:Q",
                    title="Orders per courier",
                    format=",.1f",
                ),
            ],
        )
    )
    return _style_chart(alt.layer(bars, line).resolve_scale(y="independent"))


def delivery_tariff_donut_chart(tariff_by_type: pl.DataFrame) -> alt.Chart:
    """Render delivery cost split by courier type as a donut chart."""
    colors = curie_colors()
    prepared_data = tariff_by_type.pipe(
        _float_columns,
        ["total_delivery_cost", "avg_delivery_cost_per_order"],
    ).sort("total_delivery_cost", descending=True)
    chart_data = prepared_data.to_dicts()
    courier_types = prepared_data.get_column("courier_type").to_list()
    segment_colors = [
        colors["blue_l3"],
        colors["green_l1"],
        colors["red_l1"],
        colors["blue_l4"],
        colors["blue_l1"],
    ][: len(courier_types)]
    base = (
        alt.Chart(alt.Data(values=chart_data))
        .encode(
            theta=alt.Theta("total_delivery_cost:Q", title="Delivery cost"),
            color=alt.Color(
                "courier_type:N",
                title=None,
                scale=alt.Scale(domain=courier_types, range=segment_colors),
                legend=alt.Legend(orient="right"),
            ),
            order=alt.Order("total_delivery_cost:Q", sort="descending"),
        )
    )
    arc = (
        base
        .mark_arc(innerRadius=72, outerRadius=132)
        .encode(
            tooltip=[
                alt.Tooltip("courier_type:N", title="Courier type"),
                alt.Tooltip(
                    "total_delivery_cost:Q",
                    title="Delivery cost",
                    format="$,.0f",
                ),
                alt.Tooltip(
                    "avg_delivery_cost_per_order:Q",
                    title="Avg tariff / order",
                    format="$,.2f",
                ),
                alt.Tooltip(
                    "delivered_order_count:Q",
                    title="Delivered orders",
                    format=",.0f",
                ),
                alt.Tooltip(
                    "active_courier_count:Q",
                    title="Active couriers",
                    format=",.0f",
                ),
            ],
        )
    )
    labels = (
        alt.Chart(alt.Data(values=chart_data))
        .mark_text(radius=156, color=colors["text"], size=12)
        .encode(
            theta=alt.Theta("total_delivery_cost:Q", stack=True),
            order=alt.Order("total_delivery_cost:Q", sort="descending"),
            text=alt.Text("total_delivery_cost:Q", format="$,.0f"),
        )
    )
    return _style_chart(alt.layer(arc, labels))


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
    colors = curie_colors()
    return (
        chart.properties(padding={"left": 12, "right": 18, "top": 12, "bottom": 12})
        .configure(background="transparent")
        .configure_axis(
            labelColor=colors["text"],
            labelPadding=6,
            titleColor=colors["text"],
            titlePadding=14,
            gridColor=colors["border"],
        )
        .configure_legend(
            labelColor=colors["text"],
            orient="top",
            direction="horizontal",
            title=None,
        )
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
