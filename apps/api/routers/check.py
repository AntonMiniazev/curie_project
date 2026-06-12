from pathlib import Path
import json
from ..core.config import get_settings

settings = get_settings()
manifest_path = Path(settings.cache_current) / "manifest.json"

if not manifest_path.exists():
    print(
        f"Warning: Cache manifest not found at {manifest_path}. Cache status will indicate not configured."
    )
else:
    print(
        f"Cache manifest found at {manifest_path}. Cache status will indicate configured."
    )

    with open(manifest_path) as f:
        manifest_data = json.load(f)
        release_id = manifest_data.get("release_id")
        tables = manifest_data.get("tables", [])

    print(type(tables))