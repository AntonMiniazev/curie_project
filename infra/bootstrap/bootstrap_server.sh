#!/usr/bin/env bash
set -euo pipefail

# Prepare a fresh Ubuntu server so the Curie GitHub Actions deploy workflow can run.
#
# Scope:
#   - install server prerequisites used by the deploy workflow
#   - join Tailscale when an auth key is provided
#   - open only SSH/HTTP/HTTPS in UFW
#   - create the deployment/cache directories expected by compose
#   - optionally authorize the GitHub Actions deploy SSH public key
#   - optionally pre-login Docker to GHCR on the server
#
# Deliberately out of scope:
#   - copying compose, Nginx, postgres init, or env files
#   - writing Nginx site configuration
#   - issuing certificates
#   - pulling images, running migrations, or starting containers
#
# Expected usage on the fresh server:
#   curl -fsSL https://raw.githubusercontent.com/AntonMiniazev/curie_project/main/infra/bootstrap/bootstrap_server.sh -o /root/bootstrap_server.sh
#   chmod +x /root/bootstrap_server.sh
#   TAILSCALE_AUTH_KEY=tskey-auth-... /root/bootstrap_server.sh
#
# Optional environment variables:
#   CURIE_DEPLOY_DIR=/opt/curie
#   CURIE_HOST_CACHE_DIR=/var/lib/curie/cache
#   CURIE_TAILSCALE_HOSTNAME=curie-server
#   TAILSCALE_AUTH_KEY=tskey-auth-...
#   CURIE_DEPLOY_PUBLIC_KEY='ssh-ed25519 ...'
#   GHCR_USERNAME=AntonMiniazev
#   GHCR_TOKEN=...

CURIE_DEPLOY_DIR="${CURIE_DEPLOY_DIR:-/opt/curie}"
CURIE_HOST_CACHE_DIR="${CURIE_HOST_CACHE_DIR:-/var/lib/curie/cache}"
CURIE_TAILSCALE_HOSTNAME="${CURIE_TAILSCALE_HOSTNAME:-curie-server}"

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root." >&2
    exit 1
  fi
}

log() {
  printf '\n==> %s\n' "$*"
}

install_base_packages() {
  log "Installing base packages"
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    certbot \
    curl \
    gnupg \
    lsb-release \
    nginx \
    python3-certbot-nginx \
    ufw
}

install_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    log "Docker already installed"
    docker --version
    docker compose version
    return
  fi

  log "Installing Docker Engine from official Docker apt repository"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    containerd.io \
    docker-buildx-plugin \
    docker-ce \
    docker-ce-cli \
    docker-compose-plugin

  systemctl enable --now docker
  docker --version
  docker compose version
}

install_tailscale() {
  if command -v tailscale >/dev/null 2>&1; then
    log "Tailscale already installed"
  else
    log "Installing Tailscale"
    curl -fsSL https://tailscale.com/install.sh | sh
  fi

  systemctl enable --now tailscaled

  if [ -n "${TAILSCALE_AUTH_KEY:-}" ]; then
    log "Joining Tailscale as ${CURIE_TAILSCALE_HOSTNAME}"
    tailscale up \
      --authkey="${TAILSCALE_AUTH_KEY}" \
      --hostname="${CURIE_TAILSCALE_HOSTNAME}" \
      --ssh \
      --accept-dns=false
  else
    log "TAILSCALE_AUTH_KEY is not set; leaving Tailscale installed but not authenticated"
  fi

  tailscale ip -4 2>/dev/null || true
}

configure_firewall() {
  log "Configuring UFW"
  ufw allow OpenSSH
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
  ufw status verbose
}

create_directories() {
  log "Creating Curie deployment directories"
  install -d -m 0700 "${CURIE_DEPLOY_DIR}"
  install -d -m 0700 "${CURIE_DEPLOY_DIR}/env"
  install -d -m 0755 "${CURIE_DEPLOY_DIR}/nginx"
  install -d -m 0755 "${CURIE_DEPLOY_DIR}/postgres/initdb"
  install -d -m 0755 "${CURIE_HOST_CACHE_DIR}/current"
  install -d -m 0755 "${CURIE_HOST_CACHE_DIR}/releases"
}

authorize_deploy_key_if_configured() {
  if [ -z "${CURIE_DEPLOY_PUBLIC_KEY:-}" ]; then
    log "CURIE_DEPLOY_PUBLIC_KEY is not set; skipping SSH deploy key installation"
    return
  fi

  log "Authorizing GitHub Actions deploy public key for root"
  install -d -m 0700 /root/.ssh
  touch /root/.ssh/authorized_keys
  chmod 0600 /root/.ssh/authorized_keys

  if ! grep -qxF "${CURIE_DEPLOY_PUBLIC_KEY}" /root/.ssh/authorized_keys; then
    printf '%s\n' "${CURIE_DEPLOY_PUBLIC_KEY}" >> /root/.ssh/authorized_keys
  fi
}

login_to_ghcr_if_configured() {
  if [ -n "${GHCR_USERNAME:-}" ] && [ -n "${GHCR_TOKEN:-}" ]; then
    log "Logging Docker into GHCR"
    printf '%s' "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
  else
    log "GHCR_USERNAME/GHCR_TOKEN not set; skipping docker login"
  fi
}

enable_services() {
  log "Enabling base services"
  systemctl enable --now nginx
  systemctl enable --now docker
}

print_readiness() {
  local tailscale_ip
  tailscale_ip="$(tailscale ip -4 2>/dev/null | head -n 1 || true)"

  cat <<EOF

Bootstrap complete. This server is prepared for the GitHub Actions deploy workflow.

Server readiness state:
- Docker and docker compose are installed.
- Nginx and Certbot are installed, but no Curie Nginx site was written by bootstrap.
- UFW allows SSH, HTTP, and HTTPS.
- Deployment directory exists: ${CURIE_DEPLOY_DIR}
- Cache directory exists: ${CURIE_HOST_CACHE_DIR}
- Tailscale IPv4: ${tailscale_ip:-not joined}

Before the first GitHub Actions deploy:
1. Ensure GitHub Actions can SSH as root to this host.
   If you did not pass CURIE_DEPLOY_PUBLIC_KEY, add the public half of CURIE_DEPLOY_SSH_KEY to /root/.ssh/authorized_keys manually.
2. Update .github/workflows/deploy-api.yml CURIE_DEPLOY_HOST if the public IPv4 changed.
3. Update infra/env/curie-prod.sops.env Tailnet bindings when the Tailscale IP changed:
   CURIE_API_PORT=<new-tailscale-ip>:8000
   CURIE_STREAMLIT_PORT=<new-tailscale-ip>:8501
   CURIE_POSTGRES_PORT=<new-tailscale-ip>:5432
4. Ensure certificates exist before applying the current HTTPS Nginx config.
   The current infra/nginx/curie.conf references /etc/letsencrypt/live/ampere-data.work/.
5. Restore or refresh production data after deploy.
   Deleting the old server deletes its Docker postgres volume and ${CURIE_HOST_CACHE_DIR} unless backed up separately.
EOF
}

main() {
  require_root
  install_base_packages
  install_docker
  install_tailscale
  configure_firewall
  create_directories
  authorize_deploy_key_if_configured
  login_to_ghcr_if_configured
  enable_services
  print_readiness
}

main "$@"
