#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p packages/contracts

uv run python - <<'PY' > packages/contracts/openapi.json
import json

from apps.api.main import app

print(json.dumps(app.openapi(), indent=2))
PY
