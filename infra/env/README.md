# Environment Files

Use committed `*.example` files as templates.

Local development:

```bash
cp .env.dev.example .env.dev
```

Production:

```bash
cp .env.prod.example .env.prod
```

Do not commit real `.env.dev` or `.env.prod` files. Production secrets should be encrypted with SOPS before they are committed.

The production Docker image should not contain secrets or cache files. Pass secrets through the environment, and mount the cache directory from the host:

```bash
docker compose --env-file .env.prod -f infra/compose.prod.example.yml up -d api
docker compose --env-file .env.prod -f infra/compose.prod.example.yml --profile cache run --rm cache-refresh
```
