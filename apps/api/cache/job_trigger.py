import os
import subprocess
from datetime import UTC, datetime

from ..core.config import get_settings


def _find_running_refresh_job_id() -> str | None:
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter",
            "label=curie.job=cache-refresh",
            "--filter",
            "status=running",
            "--format",
            "{{.Names}}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Cache refresh guard failed: {detail}")

    running_jobs = [
        line.strip() for line in result.stdout.splitlines() if line.strip()
    ]
    return running_jobs[0] if running_jobs else None


def trigger_cache_refresh_job() -> str:
    settings = get_settings()

    if not settings.cache_refresh_enabled:
        raise RuntimeError("Cache refresh job trigger is not enabled.")

    if running_job_id := _find_running_refresh_job_id():
        return running_job_id

    job_id = f"{settings.cache_refresh_container_prefix}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    command = [
        "docker",
        "run",
        "-d",
        "--name",
        job_id,
        "--label",
        "app=curie",
        "--label",
        "curie.job=cache-refresh",
        "-e",
        "CURIE_CACHE_ROOT=/app/data/cache",
        "-e",
        "CURIE_CACHE_CURRENT=/app/data/cache/current",
    ]

    if settings.cache_refresh_volumes_from:
        command.extend(["--volumes-from", settings.cache_refresh_volumes_from])
    else:
        command.extend(
            [
                "-v",
                f"{settings.cache_refresh_host_cache_dir}:/app/data/cache",
            ]
        )

    if settings.cache_refresh_network:
        command.extend(["--network", settings.cache_refresh_network])

    for host_mapping in settings.cache_refresh_extra_hosts:
        command.extend(["--add-host", host_mapping])

    for key, value in os.environ.items():
        if key == "APP_ENV" or key.startswith("CURIE_"):
            command.extend(["-e", key])

    command.extend(
        [
            settings.cache_refresh_image,
            "uv",
            "run",
            "python",
            "-m",
            "apps.api.cache.refresh",
        ]
    )

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Cache refresh job trigger failed: {detail}")

    return job_id
