"""Start one isolated Flight SQL serving-cache refresh container."""

import os
import subprocess
from datetime import UTC, datetime

from ..core.config import get_settings


def _find_running_refresh_job_id(job_kind: str = "flightsql") -> str | None:
    if job_kind != "flightsql":
        raise ValueError(f"Unsupported cache refresh kind: {job_kind}")
    result = subprocess.run(
        [
            "docker", "ps", "--filter", "label=curie.job=flightsql-cache-refresh",
            "--filter", "status=running", "--format", "{{.Names}}",
        ],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Cache refresh guard failed: {detail}")
    return next((line.strip() for line in result.stdout.splitlines() if line.strip()), None)


def trigger_cache_refresh_job(job_kind: str = "flightsql") -> str:
    if job_kind != "flightsql":
        raise ValueError(f"Unsupported cache refresh kind: {job_kind}")
    settings = get_settings()
    if not settings.cache_refresh_enabled:
        raise RuntimeError("Cache refresh job trigger is not enabled.")
    if (
        not settings.flightsql_uri
        or not settings.flightsql_auth_token
        or not settings.flightsql_auth_token.get_secret_value()
    ):
        raise RuntimeError("Flight SQL URI and protected token are not configured")
    if running := _find_running_refresh_job_id():
        return running

    job_id = f"{settings.serving_refresh_container_prefix}-{datetime.now(UTC):%Y%m%d%H%M%S}"
    command = [
        "docker", "run", "-d", "--rm", "--name", job_id,
        "--label", "app=curie", "--label", "curie.job=flightsql-cache-refresh",
        "--memory=2g", "--cpus=1.5",
        "-e", "CURIE_SERVING_CACHE_ROOT=/app/data/serving-cache",
        "-e", "CURIE_SERVING_CACHE_CURRENT=/app/data/serving-cache/current",
        "-v", f"{settings.serving_host_cache_dir}:/app/data/serving-cache",
    ]
    if settings.cache_refresh_network:
        command.extend(["--network", settings.cache_refresh_network])

    environment = os.environ.copy()
    environment.update(
        CURIE_FLIGHTSQL_URI=settings.flightsql_uri,
        CURIE_FLIGHTSQL_AUTH_TOKEN=settings.flightsql_auth_token.get_secret_value(),
        CURIE_FLIGHTSQL_TIMEOUT_SECONDS=str(settings.flightsql_timeout_seconds),
        CURIE_FLIGHTSQL_FETCH_TIMEOUT_SECONDS=str(settings.flightsql_fetch_timeout_seconds),
        CURIE_SERVING_CACHE_KEEP_PREVIOUS=str(settings.serving_cache_keep_previous),
    )
    for key in environment:
        if key == "APP_ENV" or key.startswith("CURIE_FLIGHTSQL_") or key.startswith("CURIE_SERVING_"):
            if key not in {"CURIE_SERVING_CACHE_ROOT", "CURIE_SERVING_CACHE_CURRENT"}:
                command.extend(["-e", key])

    command.extend([
        settings.cache_refresh_image, "uv", "run", "python", "-m",
        "apps.api.cache.refresh_flightsql",
    ])
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, env=environment
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Cache refresh job trigger failed: {detail}")
    return job_id
