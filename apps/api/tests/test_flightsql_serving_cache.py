"""Task 16 safety checks for local cache activation and SQL store scope."""

from pathlib import Path
from types import SimpleNamespace

import duckdb
import pyarrow as pa
import pytest
from pydantic import SecretStr

from apps.api.cache import refresh_flightsql
from apps.api.cache.flightsql_sources import SourceDataset
from shared.report_scope import ReportScope
from data import query_utils


def test_report_query_filters_before_aggregation(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "current.duckdb"
    with duckdb.connect(str(database)) as con:
        con.execute("CREATE SCHEMA cache")
        con.execute(
            "CREATE TABLE cache.curie_marketing_sales_budget_monthly_store "
            "(store_id INTEGER, sales_amount INTEGER)"
        )
        con.execute(
            "INSERT INTO cache.curie_marketing_sales_budget_monthly_store "
            "VALUES (1, 10), (2, 90)"
        )
        con.execute(
            "CREATE TABLE cache.curie_marketing_active_client_month "
            "(store_id INTEGER, client_id INTEGER)"
        )
        con.execute(
            "INSERT INTO cache.curie_marketing_active_client_month VALUES (1, 11), (2, 22)"
        )
    monkeypatch.setattr(
        query_utils, "connect", lambda: duckdb.connect(str(database), read_only=True)
    )
    scoped = ReportScope("one@example.com", False, (1,), "store-one")
    all_stores = ReportScope("region@example.com", True, (), "region")
    sql = "SELECT sum(sales_amount) AS total FROM CURIE_TABLE(?)"
    ref = ["curie-table://curie_marketing_sales_budget_monthly_store"]
    assert query_utils.query(sql, ref, scoped).item() == 10
    assert query_utils.query(sql, ref, all_stores).item() == 100
    assert (
        query_utils.query(
            "SELECT count(*) FROM CURIE_TABLE(?)",
            ["curie-table://curie_marketing_active_client_month"],
            scoped,
        ).item()
        == 1
    )


def test_report_query_rejects_missing_scope_and_untrusted_table(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        query_utils.query(
            "SELECT * FROM CURIE_TABLE(?)",
            ["curie-table://curie_marketing_sales_budget_monthly_store"], None
        )
    with pytest.raises(ValueError, match="Unexpected Curie cache table"):
        query_utils._compile("SELECT * FROM CURIE_TABLE(?)", ["curie-table://secrets"])


def test_failed_refresh_preserves_current_release(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "serving-cache"
    releases = root / "releases"
    releases.mkdir(parents=True)
    previous = releases / "previous.duckdb"
    previous.write_bytes(b"previous release")
    current = root / "current"
    if refresh_flightsql.os.name == "nt":
        refresh_flightsql.os.link(previous, current)
    else:
        current.symlink_to(Path("releases") / previous.name)
    settings = SimpleNamespace(
        flightsql_uri="flightsql://example.invalid:8815?transport=tcp",
        flightsql_auth_token=SecretStr("test-only-token"),
        serving_cache_root=root,
        serving_cache_current=current,
        serving_cache_keep_previous=2,
    )
    monkeypatch.setattr(refresh_flightsql, "FlightRefreshSettings", lambda: settings)

    def fail_after_partial_write(path, _settings, _release_id):
        path.write_bytes(b"partial release")
        raise RuntimeError("simulated source failure")

    monkeypatch.setattr(refresh_flightsql, "_build_database", fail_after_partial_write)
    with pytest.raises(RuntimeError, match="simulated source failure"):
        refresh_flightsql.refresh()
    assert current.read_bytes() == b"previous release"
    assert list((root / "refresh").glob("*.duckdb")) == []
    assert (root / "status.json").read_text(encoding="utf-8").find(
        '"state": "failed"'
    ) >= 0


def test_activation_and_retention_keep_active_release(tmp_path: Path) -> None:
    root = tmp_path / "serving-cache"
    releases = root / "releases"
    releases.mkdir(parents=True)
    previous = releases / "previous.duckdb"
    previous.write_bytes(b"old")
    current = root / "current"
    if refresh_flightsql.os.name == "nt":
        refresh_flightsql.os.link(previous, current)
    else:
        current.symlink_to(Path("releases") / previous.name)
    fresh = releases / "fresh.duckdb"
    fresh.write_bytes(b"new")
    refresh_flightsql._activate_release(root, fresh, current, "fresh")
    refresh_flightsql._cleanup_releases(root, current, keep_previous=1)
    assert current.read_bytes() == b"new"
    assert previous.exists()


def test_order_id_ranges_load_all_rows_once() -> None:
    rows = [(1, 10), (1, 20), (4, 40), (7, 70)]

    class Cursor:
        def execute(self, query):
            self.query = query

        def fetchone(self):
            return 1, 7, len(rows), 0

        def fetch_record_batch(self):
            import re

            start, end = map(
                int,
                re.search(
                    r"order_id >= (\d+) AND order_id < (\d+)", self.query
                ).groups(),
            )
            selected = [
                (order_id, value) for order_id, value in rows if start <= order_id < end
            ]
            table = pa.table(
                {
                    "order_id": pa.array([row[0] for row in selected], type=pa.int64()),
                    "value": pa.array([row[1] for row in selected], type=pa.int64()),
                }
            )
            return table.to_reader()

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    class Source:
        def cursor(self):
            return Cursor()

    dataset = SourceDataset(
        name="example",
        source_query="SELECT order_id, value FROM iceberg_gold.gold.example",
        required_columns=("order_id", "value"),
        order_id_chunk_size=2,
    )
    with duckdb.connect(":memory:") as con:
        con.execute("CREATE SCHEMA cache")
        assert refresh_flightsql._load_dataset(con, Source(), dataset) == len(rows)
        assert (
            con.execute(
                "SELECT order_id, value FROM cache.example ORDER BY value"
            ).fetchall()
            == rows
        )


def test_source_cleanup_does_not_hide_query_failure() -> None:
    class BrokenClose:
        def close(self):
            raise RuntimeError("cleanup failed")

    with pytest.raises(ValueError, match="stream failed"):
        with refresh_flightsql._close_preserving_failure(BrokenClose()):
            raise ValueError("stream failed")
