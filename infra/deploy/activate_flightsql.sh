#!/usr/bin/env bash
set -euo pipefail

cd /opt/curie
compose=(docker compose --env-file env/curie-prod.env -f compose.yml)

"${compose[@]}" pull web api streamlit
"${compose[@]}" run --rm --no-deps api sh -c 'cd apps/api && uv run alembic upgrade head'
"${compose[@]}" up -d --no-deps --force-recreate api

api_ready=false
for _ in $(seq 1 30); do
  if curl --fail --silent --output /dev/null http://127.0.0.1:8000/api/health; then
    api_ready=true
    break
  fi
  sleep 2
done
if [ "$api_ready" != true ]; then
  echo "API did not become healthy; old Streamlit remains running." >&2
  exit 1
fi

# A failed refresh leaves the old Streamlit container untouched. The new
# Streamlit image is activated only after this synchronous job succeeds.
"${compose[@]}" --profile flightsql-cache run --rm --no-deps flightsql-cache-refresh
python3 /opt/curie/deploy/check_flightsql_status.py
"${compose[@]}" up -d --no-deps --force-recreate web streamlit
"${compose[@]}" ps web api streamlit
