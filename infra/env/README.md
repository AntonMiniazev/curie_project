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

Then edit `infra/env/curie-dev.env` with your local passwords, MinIO keys, JWT secret, password pepper, and admin API key.

For the Iceberg refresh, also set `CURIE_LAKEKEEPER_CLIENT_ID` and
`CURIE_LAKEKEEPER_CLIENT_SECRET` to the pilot Entra application values. Keep
the read-only `CURIE_MINIO_ACCESS_KEY` and `CURIE_MINIO_SECRET_KEY` scoped to
`ampere-iceberg-gold`. `CURIE_ICEBERG_SOURCE_TABLES` defaults to the 11 Gold
tables in the migration request and can be overridden for a smaller local pilot.

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

During deployment, GitHub Actions also reads the Iceberg Entra client ID,
client secret, and dedicated MinIO access/secret keys from `az-ampere-kv` and
adds them to the temporary server env file. The deployment identity therefore
needs secret-read permission only for `ampere-iceberg-curie-clientid`,
`ampere-iceberg-curie-secret`, `ampere-iceberg-minio-access-key`, and
`ampere-iceberg-minio-secret-key`. Prefer Azure RBAC assignments scoped to
those four individual secrets. The temporary file is removed from the runner
after it is copied to the server.
