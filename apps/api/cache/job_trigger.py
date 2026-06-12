import os
import subprocess
from datetime import UTC, datetime

from ..core.config import get_settings


def trigger_cache_refresh_job() -> str:
    settings = get_settings()

    if not settings.cache_refresh_enabled:
        raise RuntimeError("Cache refresh job trigger is not enabled.")

    job_id = f"{settings.cache_refresh_container_prefix}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    command = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        job_id,
        "-v",
        f"{settings.cache_refresh_host_cache_dir}:/app/data/cache",
        "-e",
        "CURIE_CACHE_ROOT=/app/data/cache",
        "-e",
        "CURIE_CACHE_CURRENT=/app/data/cache/current",
    ]

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
