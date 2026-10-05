"""Export Lakekeeper managed Iceberg Gold tables into an isolated Parquet cache."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from ..core.config import get_settings
from .refresh import cleanup_release_directories, promote_release_to_current, sha256_file


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _require_credentials() -> tuple[str, str, str]:
    settings = get_settings()
    if not settings.iceberg_client_id or not settings.iceberg_client_secret:
        raise RuntimeError("Lakekeeper OAuth credentials are not configured.")
    if not settings.minio_access_key or not settings.minio_secret_key:
        raise RuntimeError("Iceberg MinIO credentials are not configured.")
    return (
        settings.iceberg_client_id.get_secret_value(),
        settings.iceberg_client_secret.get_secret_value(),
        settings.minio_secret_key.get_secret_value(),
    )


def _connect_catalog() -> duckdb.DuckDBPyConnection:
    settings = get_settings()
    client_id, client_secret, minio_secret = _require_credentials()
    connection = duckdb.connect(":memory:")
    connection.execute("INSTALL iceberg")
    connection.execute("LOAD iceberg")
    connection.execute("INSTALL httpfs")
    connection.execute("LOAD httpfs")
    connection.execute(
        "CREATE SECRET lakekeeper_oauth (TYPE iceberg, "
        f"CLIENT_ID {_literal(client_id)}, CLIENT_SECRET {_literal(client_secret)}, "
        f"OAUTH2_SCOPE {_literal(settings.iceberg_oauth_scope)}, "
        f"OAUTH2_SERVER_URI {_literal(settings.iceberg_oauth_token_url)})"
    )
    endpoint = (
        settings.minio_endpoint.removeprefix("https://").removeprefix("http://")
    )
    connection.execute(
        "CREATE SECRET iceberg_s3 (TYPE s3, PROVIDER config, "
        f"KEY_ID {_literal(settings.minio_access_key.get_secret_value())}, "
        f"SECRET {_literal(minio_secret)}, ENDPOINT {_literal(endpoint)}, "
        f"REGION {_literal(settings.minio_region)}, URL_STYLE 'path', "
        f"USE_SSL {str(settings.minio_endpoint.startswith('https://')).lower()}, "
        "VERIFY_SSL true)"
    )
    connection.execute(
        f"ATTACH {_literal(settings.iceberg_warehouse)} AS lakekeeper_catalog "
        f"(TYPE iceberg, ENDPOINT {_literal(settings.iceberg_catalog_endpoint)}, "
        "SECRET lakekeeper_oauth, ACCESS_DELEGATION_MODE 'none')"
    )
    return connection


def refresh_all_iceberg_tables() -> dict[str, Any]:
    settings = get_settings()
    release_id = datetime.now(UTC).strftime("iceberg-release-%Y%m%d-%H%M%S")
    release_dir = settings.iceberg_cache_root / "releases" / release_id
    release_dir.mkdir(parents=True, exist_ok=False)
    connection = _connect_catalog()
    entries: list[dict[str, Any]] = []
    try:
        for table_name in settings.iceberg_source_tables:
            table_ref = ".".join(
                _identifier(part)
                for part in (
                    "lakekeeper_catalog",
                    settings.iceberg_namespace,
                    table_name,
                )
            )
            data_dir = release_dir / "data"
            schema_dir = release_dir / "schemas"
            data_dir.mkdir(exist_ok=True)
            schema_dir.mkdir(exist_ok=True)
            parquet_path = data_dir / f"{table_name}.parquet"
            schema_path = schema_dir / f"{table_name}.schema.json"
            connection.execute(
                f"COPY (SELECT * FROM {table_ref}) "
                f"TO {_literal(str(parquet_path))} (FORMAT PARQUET)"
            )
            row_count = connection.execute(
                f"SELECT count(*) FROM {table_ref}"
            ).fetchone()[0]
            columns = connection.execute(
                f"DESCRIBE SELECT * FROM {table_ref}"
            ).fetchall()
            schema = {
                "table": table_name,
                "source_table": (
                    f"{settings.iceberg_warehouse}."
                    f"{settings.iceberg_namespace}.{table_name}"
                ),
                "source_format": "iceberg",
                "columns": [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] != "NO",
                    }
                    for row in columns
                ],
            }
            schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            entries.append(
                {
                    "name": table_name,
                    "source_table": schema["source_table"],
                    "path": f"data/{table_name}.parquet",
                    "schema_path": f"schemas/{table_name}.schema.json",
                    "row_count": row_count,
                    "checksum": sha256_file(parquet_path),
                }
            )
    finally:
        connection.close()

    manifest = {
        "release_id": release_id,
        "source": "lakekeeper.gold",
        "source_catalog": "lakekeeper",
        "source_schema": settings.iceberg_namespace,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "tables": entries,
    }
    (release_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    promote_release_to_current(release_dir, settings.iceberg_cache_current)
    cleanup_release_directories(settings.iceberg_cache_root)
    return manifest


def main() -> None:
    print(json.dumps(refresh_all_iceberg_tables(), indent=2))


if __name__ == "__main__":
    main()
