"""Marketing report queries over the Gold aggregate release."""

from data.marketing_aggregate_queries import (
    active_clients as marketing_active_clients,
    average_bill_by_month as marketing_average_bill_by_month,
    client_churn_by_month as marketing_client_churn_by_month,
    monthly_budget as marketing_monthly_budget,
    monthly_clients as marketing_monthly_clients,
    monthly_sales as marketing_monthly_sales,
    monthly_sales_vs_budget as marketing_monthly_sales_vs_budget,
    new_clients_by_month as marketing_new_clients_by_month,
    store_monthly_sales_vs_budget as marketing_store_monthly_sales_vs_budget,
    top_categories as marketing_top_categories,
    top_products as marketing_top_products,
)
