#!/bin/sh
# Match the configured container listener without exposing configuration values.
set -eu
cd "${ASTER_PROJECT_ROOT:-/app}"
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi
case "${ASTER_HOST:-0.0.0.0}" in
    ::|::1) health_host='[::1]' ;;
    *) health_host=127.0.0.1 ;;
esac
exec python scripts/monitor.py --url "http://${health_host}:${ASTER_PORT:-8787}" --maximum-age 180
