"""Fail deployment unless the eight-table Flight SQL release is active."""

import json
from urllib.request import urlopen

EXPECTED = {
    "marketing_sales_budget_monthly_store",
    "marketing_product_sales_monthly_store",
    "marketing_category_sales_monthly_store",
    "marketing_client_metrics_monthly_store",
    "marketing_active_client_month",
    "financial_performance_monthly_store",
    "financial_product_margin_monthly_store",
    "delivery_courier_performance_monthly_store",
}

with urlopen("http://127.0.0.1:8000/api/cache/status_flightsql", timeout=15) as response:
    status = json.load(response)

actual = {row["name"] for row in status["tables"]}
if (
    status.get("state") != "succeeded"
    or status.get("running")
    or not status.get("active_release_id")
    or actual != EXPECTED
    or any(row["row_count"] < 1 for row in status["tables"])
):
    raise SystemExit(
        "Flight SQL release is not ready: "
        f"state={status.get('state')}, release={status.get('active_release_id')}, "
        f"missing={sorted(EXPECTED - actual)}, unexpected={sorted(actual - EXPECTED)}"
    )

print(f"Flight SQL release ready: {status['active_release_id']} ({len(actual)} tables)")
