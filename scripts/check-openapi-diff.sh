#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

before="$(mktemp)"
trap 'rm -f "$before"' EXIT

if [[ -f packages/contracts/openapi.json ]]; then
  cp packages/contracts/openapi.json "$before"
else
  : > "$before"
fi

scripts/export-openapi.sh

if ! cmp -s "$before" packages/contracts/openapi.json; then
  echo "OpenAPI contract changed. Run scripts/export-openapi.sh and commit packages/contracts/openapi.json." >&2
  exit 1
fi
