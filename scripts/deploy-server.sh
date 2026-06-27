#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/data/sales-ai/app"

cd "$APP_DIR"
docker compose up -d --build
docker compose ps
