#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/beifen/sales-ai-backups/mysql"
APP_DIR="/data/sales-ai/app"
DATE="$(date +%F_%H%M%S)"

mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

MYSQL_PASSWORD="$(grep '^MYSQL_PASSWORD=' .env | cut -d= -f2-)"
MYSQL_DB="$(grep '^MYSQL_DB=' .env | cut -d= -f2-)"

docker compose exec -T mysql mysqldump -uroot -p"$MYSQL_PASSWORD" "$MYSQL_DB" | gzip > "$BACKUP_DIR/${MYSQL_DB}_${DATE}.sql.gz"
find "$BACKUP_DIR" -type f -name '*.sql.gz' -mtime +14 -delete
