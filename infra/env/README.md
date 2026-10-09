# Environment Files

Runtime environment files live in this folder.

## Layout

```text
infra/env/curie-dev.env          local dev runtime env, ignored
infra/env/curie-dev.example.env  safe dev template, committed
infra/env/curie-prod.env         plaintext prod env, ignored
infra/env/curie-prod.example.env safe prod template, committed
infra/env/curie-prod.sops.env    encrypted prod env, committed
```

## Local Development

Create the local dev env from the template:

```bash
cp infra/env/curie-dev.example.env infra/env/curie-dev.env
```

Then edit `infra/env/curie-dev.env` with local passwords, JWT secret, password pepper, admin API key, and the Flight SQL token for cache refresh.

Run dev Docker Compose with:

```bash
docker compose --env-file infra/env/curie-dev.env -f infra/compose.dev.yml up -d postgres
```

## Production

Production real values should be stored encrypted in:

```text
infra/env/curie-prod.sops.env
```

Do not commit plaintext `infra/env/curie-prod.env`.

GitHub Actions decrypts `infra/env/curie-prod.sops.env` during deployment and copies it to:

```text
/opt/curie/env/curie-prod.env
```

Manual server env copying should only be used for emergency debugging.

During deployment, GitHub Actions reads `ampere-flight-sql-token` from `az-ampere-kv` and adds it to the temporary server env file. The deployment identity needs secret-read permission on that secret. The temporary file is removed from the runner after it is copied to the server.
