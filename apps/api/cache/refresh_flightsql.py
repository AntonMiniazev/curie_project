"""Stream fixed Flight SQL Gold queries into an isolated local DuckDB release."""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import duckdb
from adbc_driver_flightsql import ConnectionOptions, DatabaseOptions
from adbc_driver_flightsql.dbapi import connect as flight_connect
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .flightsql_sources import SOURCES


class FlightRefreshSettings(BaseSettings):
    """Only the credentials and limits required by the isolated refresh job."""

    model_config = SettingsConfigDict(extra="ignore")
    flightsql_uri: str = Field(alias="CURIE_FLIGHTSQL_URI")
    flightsql_auth_token: SecretStr = Field(alias="CURIE_FLIGHTSQL_AUTH_TOKEN")
    flightsql_timeout_seconds: int = Field(
        default=30, ge=1, alias="CURIE_FLIGHTSQL_TIMEOUT_SECONDS"
    )
    flightsql_fetch_timeout_seconds: int = Field(
        default=300, ge=1, alias="CURIE_FLIGHTSQL_FETCH_TIMEOUT_SECONDS"
    )
    serving_cache_root: Path = Field(alias="CURIE_SERVING_CACHE_ROOT")
    serving_cache_current: Path = Field(alias="CURIE_SERVING_CACHE_CURRENT")
    serving_cache_keep_previous: int = Field(
        default=3, ge=0, alias="CURIE_SERVING_CACHE_KEEP_PREVIOUS"
    )


def _identifier(value: str) -> str:
    """Quote a trusted manifest identifier for DuckDB SQL."""
    return '"' + value.replace('"', '""') + '"'


@contextmanager
def _close_preserving_failure(resource):
    """Keep a query failure visible if cleanup also fails after a server restart."""
    try:
        yield resource
    except BaseException:
        try:
            resource.close()
        except Exception:
            pass
        raise
    else:
        resource.close()


def write_state(root: Path, state: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    target = root / "status.json"
    temporary = root / f".status-{uuid.uuid4().hex}.tmp"
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)


@contextmanager
def _refresh_lock(root: Path) -> Iterator[None]:
    """Serialize refreshes, including manual Compose invocations."""
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".refresh.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _cleanup_abandoned_temporary(root: Path) -> None:
    cutoff = time.time() - 24 * 60 * 60
    for path in (root / "refresh").glob("*.tmp.duckdb*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()


def _cleanup_releases(root: Path, current: Path, keep_previous: int) -> None:
    releases = sorted(
        (root / "releases").glob("*.duckdb"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    active = next((path for path in releases if os.path.samefile(path, current)), None)
    if active is None:
        raise RuntimeError("Active release is missing from releases directory")
    keep = {active, *[path for path in releases if path != active][:keep_previous]}
    for release in releases:
        if release not in keep:
            release.unlink()


def _activate_release(
    root: Path, release: Path, current: Path, release_id: str
) -> None:
    next_link = root / f".current-{release_id}"
    if os.name == "nt":
        # Windows development may lack symlink privilege; a same-volume hardlink
        # still makes the single-file switch atomic for local parity checks.
        os.link(release, next_link)
    else:
        next_link.symlink_to(Path("releases") / release.name)
    os.replace(next_link, current)


def _validate_and_record(con: duckdb.DuckDBPyConnection, dataset) -> dict:
    table = f"cache.{_identifier(dataset.name)}"
    column_types = {
        row[1].lower(): row[2].upper()
        for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()
    }
    columns = set(column_types)
    missing = set(dataset.required_columns) - columns
    if missing:
        raise RuntimeError(
            f"{dataset.name}: missing required columns {sorted(missing)}"
        )
    for column, expected_type in dataset.expected_types:
        if column_types[column] != expected_type:
            raise RuntimeError(
                f"{dataset.name}.{column}: expected {expected_type}, got {column_types[column]}"
            )
    scope_count = (
        f"count(*) FILTER (WHERE {_identifier(dataset.rls_key)} IS NULL)"
        if dataset.rls_key
        else "0"
    )
    date_min_sql = (
        f"min({_identifier(dataset.date_column)})" if dataset.date_column else "NULL"
    )
    date_max_sql = (
        f"max({_identifier(dataset.date_column)})" if dataset.date_column else "NULL"
    )
    row_count, missing_scope, date_min, date_max = con.execute(
        f"SELECT count(*), {scope_count}, {date_min_sql}, {date_max_sql} FROM {table}"
    ).fetchone()
    if row_count < 1:
        raise RuntimeError(f"{dataset.name}: source returned no rows")
    if missing_scope:
        raise RuntimeError(f"{dataset.name}: {missing_scope} rows lack the RLS key")
    if dataset.grain:
        keys = ", ".join(_identifier(key) for key in dataset.grain)
        duplicate = con.execute(
            f"SELECT 1 FROM {table} GROUP BY {keys} HAVING count(*) > 1 LIMIT 1"
        ).fetchone()
        if duplicate:
            raise RuntimeError(
                f"{dataset.name}: duplicate rows at grain {dataset.grain}"
            )
    con.execute(
        "INSERT INTO curie_datasets VALUES (?, ?, ?, ?, ?)",
        [dataset.name, dataset.source_query, row_count, date_min, date_max],
    )
    return {
        "name": dataset.name,
        "row_count": row_count,
        "date_min": str(date_min) if date_min is not None else None,
        "date_max": str(date_max) if date_max is not None else None,
    }


def _load_query(
    con: duckdb.DuckDBPyConnection, source, dataset, query: str, *, append: bool
) -> None:
    """Consume one Flight stream while its ADBC cursor remains open."""
    with _close_preserving_failure(source.cursor()) as cursor:
        cursor.execute(query)
        reader = cursor.fetch_record_batch()
        incoming_columns = {name.lower() for name in reader.schema.names}
        missing = set(dataset.required_columns) - incoming_columns
        if missing:
            raise RuntimeError(f"{dataset.name}: source is missing {sorted(missing)}")
        con.register("_curie_incoming", reader)
        try:
            verb = "INSERT INTO" if append else "CREATE TABLE"
            table = f"cache.{_identifier(dataset.name)}"
            statement = (
                f"{verb} {table} SELECT * FROM _curie_incoming"
                if append
                else f"{verb} {table} AS SELECT * FROM _curie_incoming"
            )
            con.execute(statement)
        finally:
            con.unregister("_curie_incoming")


def _load_dataset(con: duckdb.DuckDBPyConnection, source, dataset) -> int | None:
    """Use stable order-ID ranges for Gold relations too large for one result."""
    size = dataset.order_id_chunk_size
    if size is None:
        _load_query(con, source, dataset, dataset.source_query, append=False)
        return None

    relation = f"iceberg_gold.gold.{dataset.name}"
    with _close_preserving_failure(source.cursor()) as cursor:
        cursor.execute(
            "SELECT min(order_id), max(order_id), count(*), "
            f"count(*) FILTER (WHERE order_id IS NULL) FROM {relation}"
        )
        first, last, expected, missing_ids = cursor.fetchone()
    if not expected or missing_ids:
        raise RuntimeError(
            f"{dataset.name}: expected nonempty source with non-null order_id; "
            f"rows={expected}, missing_ids={missing_ids}"
        )
    created = False
    for start in range(first, last + 1, size):
        end = min(start + size, last + 1)
        query = f"{dataset.source_query} WHERE order_id >= {start} AND order_id < {end}"
        _load_query(con, source, dataset, query, append=created)
        created = True
        print(f"loaded {dataset.name}: order_id [{start}, {end})", flush=True)
    loaded = con.execute(
        f"SELECT count(*) FROM cache.{_identifier(dataset.name)}"
    ).fetchone()[0]
    if loaded != expected:
        raise RuntimeError(
            f"{dataset.name}: source changed during refresh or rows were lost; "
            f"expected={expected}, loaded={loaded}"
        )
    return expected


def _build_database(
    path: Path, settings: FlightRefreshSettings, release_id: str
) -> list[dict]:
    token = settings.flightsql_auth_token.get_secret_value()
    created_at = datetime.now(UTC).isoformat()
    inventory: list[dict] = []
    with duckdb.connect(str(path)) as con:
        con.execute("SET threads=1")
        con.execute("SET memory_limit='768MB'")
        con.execute("SET preserve_insertion_order=false")
        con.execute("CREATE SCHEMA cache")
        con.execute(
            "CREATE TABLE curie_release (release_id VARCHAR, created_at_utc VARCHAR, "
            "source_uri VARCHAR)"
        )
        con.execute(
            "CREATE TABLE curie_datasets (name VARCHAR, source_query VARCHAR, "
            "row_count BIGINT, date_min TIMESTAMP, date_max TIMESTAMP)"
        )
        with _close_preserving_failure(
            flight_connect(
                settings.flightsql_uri,
                db_kwargs={
                    DatabaseOptions.AUTHORIZATION_HEADER.value: f"Bearer {token}",
                    "adbc.flight.sql.rpc.timeout_seconds.connect": str(
                        settings.flightsql_timeout_seconds
                    ),
                },
                conn_kwargs={
                    ConnectionOptions.TIMEOUT_QUERY.value: str(
                        settings.flightsql_fetch_timeout_seconds
                    ),
                    ConnectionOptions.TIMEOUT_FETCH.value: str(
                        settings.flightsql_fetch_timeout_seconds
                    ),
                },
            )
        ) as source:
            for dataset in SOURCES:
                _load_dataset(con, source, dataset)
                entry = _validate_and_record(con, dataset)
                inventory.append(entry)
                print(f"loaded {dataset.name}: {entry['row_count']} rows", flush=True)
        con.execute(
            "INSERT INTO curie_release VALUES (?, ?, ?)",
            [release_id, created_at, settings.flightsql_uri],
        )
        con.execute("CHECKPOINT")
    return inventory


def refresh() -> dict:
    settings = FlightRefreshSettings()
    if (
        not settings.flightsql_uri
        or not settings.flightsql_auth_token.get_secret_value()
    ):
        raise RuntimeError("Flight SQL URI and protected token are required")
    root = settings.serving_cache_root
    current = settings.serving_cache_current
    if current.parent != root:
        raise RuntimeError("Serving current symlink must live under serving cache root")
    release_id = datetime.now(UTC).strftime("flightsql-release-%Y%m%d-%H%M%S")
    release_id += "-" + uuid.uuid4().hex[:8]
    temporary = root / "refresh" / f"{release_id}.tmp.duckdb"
    release = root / "releases" / f"{release_id}.duckdb"
    with _refresh_lock(root):
        (root / "refresh").mkdir(exist_ok=True)
        (root / "releases").mkdir(exist_ok=True)
        _cleanup_abandoned_temporary(root)
        write_state(
            root,
            {
                "state": "running",
                "release_id": release_id,
                "started_at_utc": datetime.now(UTC).isoformat(),
            },
        )
        try:
            if shutil.disk_usage(root).free < 3 * 1024**3:
                raise RuntimeError(
                    "Serving cache needs at least 3 GiB free before refresh"
                )
            inventory = _build_database(temporary, settings, release_id)
            os.replace(temporary, release)
            _activate_release(root, release, current, release_id)
            state = {
                "state": "succeeded",
                "release_id": release_id,
                "finished_at_utc": datetime.now(UTC).isoformat(),
                "tables": inventory,
            }
            try:
                _cleanup_releases(root, current, settings.serving_cache_keep_previous)
            except OSError as cleanup_error:
                state["cleanup_warning"] = (
                    f"{type(cleanup_error).__name__}: {cleanup_error}"
                )
            write_state(root, state)
            return {"release_id": release_id, "tables": inventory}
        except Exception as exc:
            for path in (temporary, Path(f"{temporary}.wal")):
                path.unlink(missing_ok=True)
            detail = str(exc).replace(
                settings.flightsql_auth_token.get_secret_value(), "[REDACTED]"
            )
            write_state(
                root,
                {
                    "state": "failed",
                    "release_id": release_id,
                    "finished_at_utc": datetime.now(UTC).isoformat(),
                    "last_failure": f"{type(exc).__name__}: {detail}",
                },
            )
            raise


if __name__ == "__main__":
    print(json.dumps(refresh()))
