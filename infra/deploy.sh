#!/usr/bin/env bash

set -eu

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/infra/.env.prod"
COMPOSE_FILE="${REPO_ROOT}/infra/docker-compose.prod.yml"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  echo "Create it from infra/.env.prod.example before deploying." >&2
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

require_command docker

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is not available on this machine." >&2
  exit 1
fi

required_vars='SERVER_IP POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET'

for key in $required_vars; do
  if ! grep -Eq "^${key}=.+" "$ENV_FILE"; then
    echo "Missing required setting in $(basename "$ENV_FILE"): $key" >&2
    exit 1
  fi
done

cd "$REPO_ROOT"

echo "Deploying production stack from: $REPO_ROOT"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up --build -d

echo
echo "Deployment command completed. Current service status:"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

server_ip="$(awk -F= '$1=="SERVER_IP"{print $2}' "$ENV_FILE" | tail -n 1)"

echo
echo "Useful follow-up commands:"
echo "  docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml logs api --tail 100"
echo "  docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml logs web --tail 100"
echo
echo "Expected URLs:"
echo "  http://${server_ip}"
echo "  http://${server_ip}/healthz"
