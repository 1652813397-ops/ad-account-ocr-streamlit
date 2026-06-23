#!/usr/bin/env bash
set -euo pipefail

if [ ! -f ".env.public" ]; then
  echo ".env.public not found."
  echo "Please copy .env.public.example to .env.public and fill in your real values first."
  exit 1
fi

docker compose --env-file .env.public -f docker-compose.public.yml up -d --build

echo
echo "Public deployment started."
echo "Make sure your domain, HTTPS certificate, and reverse proxy are configured."
