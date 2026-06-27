#!/usr/bin/env sh
set -eu

attempt=1
until python -m app.core.init_db; do
  if [ "$attempt" -ge 60 ]; then
    echo "database initialization failed after $attempt attempts"
    exit 1
  fi
  echo "waiting for database... attempt $attempt"
  attempt=$((attempt + 1))
  sleep 2
done
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
