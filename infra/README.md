# Server Setup

## 1. Create A Fresh Ubuntu Server

Create a new Ubuntu 22.04 or 24.04 server with public IPv4 access.

Record:

```text
Public IPv4: <server-public-ip>
Root user: root
```

## 2. Prepare The Deploy SSH Key

Create or reuse the SSH key used by GitHub Actions to connect to the server.

Keep the private key in the GitHub secret:

```text
CURIE_DEPLOY_SSH_KEY
```

Use the public key during bootstrap:

```text
CURIE_DEPLOY_PUBLIC_KEY='ssh-ed25519 ...'
```

## 3. Prepare A Tailscale Auth Key

Create an ephemeral reusable auth key in the Tailscale admin console.

Use it during bootstrap:

```text
TAILSCALE_AUTH_KEY=tskey-auth-...
```

The expected server hostname is:

```text
curie-server
```

## 4. Prepare GHCR Access

Create a GitHub token that can pull images from GitHub Container Registry.

Use these values during bootstrap if the images are private:

```text
GHCR_USERNAME=username
GHCR_TOKEN=<github-token-with-package-read-access>
```

## 5. Run Bootstrap On The Server

Connect to the new server as root:

```bash
ssh root@<server-public-ip>
```

Download and run the bootstrap script:

```bash
curl -fsSL https://raw.githubusercontent.com/AntonMiniazev/curie_project/main/infra/bootstrap/bootstrap_server.sh -o /root/bootstrap_server.sh
chmod +x /root/bootstrap_server.sh

TAILSCALE_AUTH_KEY='tskey-auth-...' \
CURIE_DEPLOY_PUBLIC_KEY='ssh-ed25519 ...' \
GHCR_USERNAME='username' \
GHCR_TOKEN='<github-token-with-package-read-access>' \
/root/bootstrap_server.sh
```

For public GHCR images, omit `GHCR_USERNAME` and `GHCR_TOKEN`.

## 6. Record The Tailscale IP

After bootstrap completes, record the server Tailnet IPv4:

```bash
tailscale ip -4
```

Expected format:

```text
100.x.x.x
```

## 7. Update GitHub Actions Deploy Host

Update the deploy workflow host when the public IPv4 changes:

```yaml
CURIE_DEPLOY_HOST: <server-public-ip>
```

The workflow is:

```text
.github/workflows/deploy-api.yml
```

## 8. Update Production Tailnet Bindings

Update the encrypted production environment with the new Tailscale IP:

```dotenv
CURIE_API_PORT=<new-tailscale-ip>:8000
CURIE_STREAMLIT_PORT=<new-tailscale-ip>:8501
CURIE_POSTGRES_PORT=<new-tailscale-ip>:5432
```

The encrypted file is:

```text
infra/env/curie-prod.sops.env
```

Keep `CURIE_UPSTREAM_HOST_IP` unchanged unless the upstream data host also changed.

## 9. Update DNS

Point both records to the new public IPv4:

```text
ampere-data.work      A    <server-public-ip>
www.ampere-data.work  A    <server-public-ip>
```

Use DNS only mode until HTTPS is verified.

## 10. Prepare HTTPS Certificates

The production Nginx config expects Let’s Encrypt files under:

```text
/etc/letsencrypt/live/ampere-data.work/
```

Issue the certificate before applying the HTTPS Nginx config:

```bash
certbot certonly --nginx \
  -d ampere-data.work \
  -d www.ampere-data.work
```

## 11. Run GitHub Actions Deploy

Run the deploy workflow manually or push a commit that triggers the image and deploy pipeline.

The deploy workflow copies:

```text
infra/compose.prod.yml -> /opt/curie/compose.yml
infra/nginx/curie.conf -> /opt/curie/nginx/curie.conf
infra/postgres/initdb/* -> /opt/curie/postgres/initdb/
infra/env/curie-prod.sops.env -> /opt/curie/env/curie-prod.env
```

The workflow then pulls images, runs migrations, starts containers, applies Nginx config, and verifies public routes.

## 12. Validate The Server

Check containers:

```bash
ssh root@<server-public-ip> "cd /opt/curie && docker compose --env-file env/curie-prod.env -f compose.yml ps"
```

Check public routes:

```bash
curl -I https://ampere-data.work/
curl https://ampere-data.work/api/health
curl -I https://ampere-data.work/streamlit/
```

Check direct public service ports stay closed:

```bash
curl --connect-timeout 5 http://<server-public-ip>:8000/api/health
curl --connect-timeout 5 http://<server-public-ip>:8501/
```

These direct port checks should fail.

## 13. Restore Or Refresh Data

Restore PostgreSQL and cache data if a backup exists.

If no backup exists, recreate application users and trigger a cache refresh.

Cache path:

```text
/var/lib/curie/cache/current
```

PostgreSQL data is stored in the Docker volume:

```text
curie-postgres-prod-data
```
