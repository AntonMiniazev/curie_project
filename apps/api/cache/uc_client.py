# ask Unity Catalog for table metadata and source location

import time
from typing import Any

import requests

from ..core.config import get_settings


def uc_client_get_table_metadata(full_table_name: str) -> dict[str, Any]:
    settings = get_settings()

    url = f"{settings.uc_base_url}/api/2.1/unity-catalog/tables/{full_table_name}"
    attempts = max(1, settings.uc_retry_attempts)
    backoff_seconds = max(0, settings.uc_retry_backoff_seconds)
    retryable_status_codes = {429, 500, 502, 503, 504}

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                timeout=settings.uc_timeout_seconds,
            )
            if response.status_code in retryable_status_codes and attempt < attempts:
                time.sleep(backoff_seconds * attempt)
                continue

            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt >= attempts:
                raise
            time.sleep(backoff_seconds * attempt)

    raise RuntimeError(f"Unity Catalog request failed without response: {url}")


def normalize_uc_table_metadata(raw_table: dict[str, Any]) -> dict[str, Any]:
    columns = []

    for column in raw_table.get("columns", []):
        columns.append(
            {
                "name": column["name"],
                "type": column.get("type_text"),
                "nullable": column.get("nullable", True),
                "comment": column.get("comment"),
            }
        )

    return {
        "table": raw_table["name"],
        "source_table": raw_table["catalog_name"]
        + "."
        + raw_table["schema_name"]
        + "."
        + raw_table["name"],
        "source_format": raw_table.get("data_source_format"),
        "source_location": raw_table.get("storage_location"),
        "columns": columns,
    }
