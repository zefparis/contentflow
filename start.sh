#!/usr/bin/env sh
set -e

PORT_RESOLVED="${PORT:-8000}"
echo "[boot] IMAGE_BUILT_FROM_DOCKERFILE=${IMAGE_BUILT_FROM_DOCKERFILE}"
echo "[boot] Using PORT=${PORT_RESOLVED}"
echo "[boot] PWD=$(pwd)  LS=$(ls -la)"

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT_RESOLVED}" \
  --log-level info \
  --proxy-headers --forwarded-allow-ips="*"
