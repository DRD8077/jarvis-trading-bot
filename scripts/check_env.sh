#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(dirname "$0")/..
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo ".env file not found. Copy .env.example to .env and fill values." >&2
  exit 2
fi

echo "Checking required env vars in .env..."
REQUIRED=(TELEGRAM_BOT_TOKEN WEBHOOK_URL)
MISSING=()
for v in "${REQUIRED[@]}"; do
  if ! grep -q "^$v=" .env; then
    MISSING+=($v)
  fi
done
if [ ${#MISSING[@]} -ne 0 ]; then
  echo "Missing vars in .env: ${MISSING[*]}" >&2
  exit 3
fi

echo "Validating docker-compose..."
if ! docker compose config >/dev/null 2>&1; then
  echo "docker compose config failed" >&2
  exit 4
fi

echo "Starting containers (detached)..."
docker compose up -d --build

echo "Waiting for health endpoint..."
for i in {1..12}; do
  if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "Health OK"
    exit 0
  fi
  sleep 5
done

echo "Health endpoint did not respond" >&2
docker compose logs --no-color --tail=100
exit 5
