# build/read/write manifest.json
import datetime
from typing import Any


def build_manifest_tables(
    normalized_table: dict[str, Any], path, schema_path, row_count, checksum
) -> dict[str, Any]:
    return {
        "name": normalized_table["table"],
        "source_table": normalized_table["source_table"],
        "path": path,
        "schema_path": schema_path,
        "row_count": row_count,
        "checksum": checksum,
    }


def build_manifest(
    raw_table: dict[str, Any], tables: list[dict[str, Any]]
) -> dict[str, Any]:
    # build manifest.json with table metadata and source location
    manifest_table = {
        "release_id": "dev-empty",
        "source": raw_table.get("catalog_name") + "." + raw_table.get("schema_name"),
        "source_catalog": raw_table.get("catalog_name"),
        "source_schema": raw_table.get("schema_name"),
        "created_at_utc": datetime.datetime.now().isoformat() + "Z",
        "tables": tables,
    }

    return manifest_table
