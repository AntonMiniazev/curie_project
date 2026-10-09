from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from apps.api.cache import job_trigger


class CompletedProcessStub:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        cache_refresh_enabled=True,
        serving_refresh_container_prefix="curie-flightsql-cache-refresh",
        serving_host_cache_dir="/var/lib/curie/serving-cache",
        cache_refresh_network="curie-prod_default",
        cache_refresh_image="curie-api:latest",
        flightsql_uri="flightsql://example.invalid:8815?transport=tcp",
        flightsql_auth_token=SecretStr("test-token"),
        flightsql_timeout_seconds=30,
        flightsql_fetch_timeout_seconds=300,
        serving_cache_keep_previous=3,
    )


def test_trigger_cache_refresh_job_returns_running_job_without_starting_new_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> CompletedProcessStub:
        calls.append(command)
        return CompletedProcessStub(stdout="curie-flightsql-cache-refresh-20260816045438\n")

    monkeypatch.setattr(job_trigger, "get_settings", _settings)
    monkeypatch.setattr(job_trigger.subprocess, "run", fake_run)

    job_id = job_trigger.trigger_cache_refresh_job()

    assert job_id == "curie-flightsql-cache-refresh-20260816045438"
    assert len(calls) == 1
    assert calls[0][:2] == ["docker", "ps"]


def test_trigger_cache_refresh_job_starts_new_container_when_no_job_is_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> CompletedProcessStub:
        calls.append(command)
        return CompletedProcessStub()

    monkeypatch.setattr(job_trigger, "get_settings", _settings)
    monkeypatch.setattr(job_trigger.subprocess, "run", fake_run)

    job_id = job_trigger.trigger_cache_refresh_job()

    assert job_id.startswith("curie-flightsql-cache-refresh-")
    assert len(calls) == 2
    assert calls[0][:2] == ["docker", "ps"]
    assert calls[1][:3] == ["docker", "run", "-d"]
    assert "--volumes-from" not in calls[1]
    assert "/var/lib/curie/serving-cache:/app/data/serving-cache" in calls[1]
    assert "curie-api:latest" in calls[1]


def test_trigger_cache_refresh_job_raises_when_guard_cannot_query_docker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **_: object) -> CompletedProcessStub:
        assert command[:2] == ["docker", "ps"]
        return CompletedProcessStub(returncode=1, stderr="docker unavailable")

    monkeypatch.setattr(job_trigger, "get_settings", _settings)
    monkeypatch.setattr(job_trigger.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Cache refresh guard failed"):
        job_trigger.trigger_cache_refresh_job()
