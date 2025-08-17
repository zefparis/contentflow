#!/usr/bin/env sh
set -e

PORT_RESOLVED="${PORT:-8000}"
echo "[boot] Using PORT=${PORT_RESOLVED}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_RESOLVED}"
