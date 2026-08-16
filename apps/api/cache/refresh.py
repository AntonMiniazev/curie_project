# apps/api/cache/refresh.py

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from ..core.config import get_settings
from .uc_client import normalize_uc_table_metadata, uc_client_get_table_metadata


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return f"sha256:{digest.hexdigest()}"


def build_storage_options() -> dict[str, str]:
    settings = get_settings()

    storage_options = {
        "AWS_ENDPOINT_URL": settings.minio_endpoint,
        "AWS_REGION": settings.minio_region,
        "AWS_S3_FORCE_PATH_STYLE": "true",
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
        "AWS_ALLOW_INVALID_CERTIFICATES": str(
            settings.minio_allow_invalid_certificates
        ).lower(),
    }

    if settings.minio_endpoint.startswith("http://"):
        storage_options["AWS_ALLOW_HTTP"] = "true"

    if settings.minio_access_key and settings.minio_secret_key:
        storage_options["AWS_ACCESS_KEY_ID"] = (
            settings.minio_access_key.get_secret_value()
        )
        storage_options["AWS_SECRET_ACCESS_KEY"] = (
            settings.minio_secret_key.get_secret_value()
        )

    return storage_options


def refresh_one_table(
    full_table_name: str,
    release_dir: Path,
    storage_options: dict[str, str],
) -> dict[str, Any]:
    raw_table = uc_client_get_table_metadata(full_table_name)
    normalized_table = normalize_uc_table_metadata(raw_table)

    table_name = normalized_table["table"]

    data_dir = release_dir / "data"
    schema_dir = release_dir / "schemas"
    data_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = data_dir / f"{table_name}.parquet"
    schema_path = schema_dir / f"{table_name}.schema.json"

    table_scan = pl.scan_delta(
        normalized_table["source_location"],
        storage_options=storage_options,
    )

    table_scan.sink_parquet(parquet_path)
    row_count = table_scan.select(pl.len()).collect().item()

    with schema_path.open("w", encoding="utf-8") as file:
        json.dump(normalized_table, file, indent=2)

    return {
        "name": table_name,
        "source_table": normalized_table["source_table"],
        "path": f"data/{table_name}.parquet",
        "schema_path": f"schemas/{table_name}.schema.json",
        "row_count": row_count,
        "checksum": sha256_file(parquet_path),
    }


def refresh_all_tables() -> dict[str, Any]:
    settings = get_settings()

    release_id = datetime.now(UTC).strftime("release-%Y%m%d-%H%M%S")
    release_dir = settings.cache_root / "releases" / release_id
    release_dir.mkdir(parents=True, exist_ok=False)

    storage_options = build_storage_options()

    table_entries = []

    for table_name in settings.source_tables:
        full_table_name = (
            f"{settings.source_catalog}.{settings.source_schema}.{table_name}"
        )

        table_entry = refresh_one_table(
            full_table_name=full_table_name,
            release_dir=release_dir,
            storage_options=storage_options,
        )
        table_entries.append(table_entry)

    manifest = {
        "release_id": release_id,
        "source": f"{settings.source_catalog}.{settings.source_schema}",
        "source_catalog": settings.source_catalog,
        "source_schema": settings.source_schema,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "tables": table_entries,
    }

    manifest_path = release_dir / "manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    promote_release_to_current(release_dir=release_dir, current_dir=settings.cache_current)
    cleanup_release_directories(cache_root=settings.cache_root)

    return manifest


def promote_release_to_current(release_dir: Path, current_dir: Path) -> None:
    temp_current_dir = current_dir.with_name(f"{current_dir.name}.tmp")

    if temp_current_dir.exists():
        shutil.rmtree(temp_current_dir)

    shutil.copytree(release_dir, temp_current_dir)

    if current_dir.exists():
        shutil.rmtree(current_dir)

    temp_current_dir.replace(current_dir)


def cleanup_release_directories(cache_root: Path) -> None:
    releases_dir = cache_root / "releases"
    releases_dir.mkdir(parents=True, exist_ok=True)

    for path in releases_dir.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def main() -> None:
    manifest = refresh_all_tables()
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
