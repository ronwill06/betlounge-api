#!/usr/bin/env bash
set -euo pipefail

APP_NAME="betlounge-api-prod"
BASE_URL="https://${APP_NAME}.fly.dev"

log() {
  printf "\n==> %s\n" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd flyctl
require_cmd curl

log "Checking Fly authentication"
if ! flyctl auth whoami >/dev/null 2>&1; then
  echo "Not logged in to Fly. Run: fly auth login"
  exit 1
fi

log "Ensuring Fly app exists: ${APP_NAME}"
if ! flyctl apps show "${APP_NAME}" >/dev/null 2>&1; then
  flyctl apps create "${APP_NAME}"
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
  log "Syncing DATABASE_URL secret from local environment"
  flyctl secrets set DATABASE_URL="${DATABASE_URL}" -a "${APP_NAME}"
else
  log "DATABASE_URL not set locally; skipping secret update"
  echo "If needed, run: fly secrets set DATABASE_URL='...' -a ${APP_NAME}"
fi

log "Deploying ${APP_NAME}"
flyctl deploy -a "${APP_NAME}"

log "Running health checks"
curl --fail --silent --show-error "${BASE_URL}/healthz" >/dev/null
curl --fail --silent --show-error "${BASE_URL}/readyz" >/dev/null

echo
printf "Deployment successful: %s\n" "${BASE_URL}"
