"""Restricted server-side acceptance probe for the standard Flight SQL endpoint.

Run only in the API image with its protected environment loaded. This command
reads three bounded SQL results and never changes the serving cache.
"""

from adbc_driver_flightsql import ConnectionOptions, DatabaseOptions
from adbc_driver_flightsql.dbapi import connect

from ..core.config import get_settings


QUERIES = (
    ("select_one", "SELECT 1"),
    ("gold_order_count", "SELECT COUNT(*) FROM iceberg_gold.gold.fct_orders_sales"),
    ("report_source", "SELECT * FROM iceberg_gold.gold.dim_stores LIMIT 1"),
)


def main() -> None:
    settings = get_settings()
    if not settings.flightsql_uri or not settings.flightsql_auth_token:
        raise SystemExit("Flight SQL URI and protected auth token must be configured")
    token = settings.flightsql_auth_token.get_secret_value()
    if not token:
        raise SystemExit("Flight SQL auth token is empty")

    print(f"Flight SQL acceptance endpoint: {settings.flightsql_uri}")
    try:
        with connect(
            settings.flightsql_uri,
            db_kwargs={
                DatabaseOptions.AUTHORIZATION_HEADER.value: f"Bearer {token}",
                "adbc.flight.sql.rpc.timeout_seconds.connect": str(
                    settings.flightsql_timeout_seconds
                ),
            },
            conn_kwargs={
                ConnectionOptions.TIMEOUT_QUERY.value: str(settings.flightsql_timeout_seconds),
                ConnectionOptions.TIMEOUT_FETCH.value: str(settings.flightsql_timeout_seconds),
            },
        ) as connection:
            with connection.cursor() as cursor:
                for name, sql in QUERIES:
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    if row is None:
                        raise RuntimeError(f"{name}: query returned no rows")
                    if name == "report_source":
                        print(f"{name}: received one row with {len(row)} columns")
                    else:
                        print(f"{name}: {row[0]}")
    except Exception as exc:
        # Driver error text can include request metadata. Never print a token.
        detail = str(exc).replace(token, "[REDACTED]")
        raise SystemExit(f"Flight SQL acceptance failed ({type(exc).__name__}): {detail}") from None


if __name__ == "__main__":
    main()
