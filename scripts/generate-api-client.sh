#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/web"
npx openapi-typescript ../../packages/contracts/openapi.json \
  -o ../../packages/api-client/src/schema.ts
