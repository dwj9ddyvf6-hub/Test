#!/bin/sh
# Prepared container entrypoint; not activated by writing this file.
# An external container orchestrator must restart the container after PID 1 exits.
set -eu
ASTER_ENTRYPOINT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ASTER_ENTRYPOINT_ROOT"
# Compose passes .env as environment. A deliberately mounted POSIX .env is
# also inherited by the supervisor/coordinator rather than only one child.
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
ASTER_ENTRYPOINT_DATA=$(dirname -- "${ASTER_DB_PATH:-/data/aster.sqlite}")
ASTER_ENTRYPOINT_PROBE=127.0.0.1
if [ "${ASTER_HOST:-0.0.0.0}" = '::1' ] || [ "${ASTER_HOST:-0.0.0.0}" = '::' ]; then
  ASTER_ENTRYPOINT_PROBE='[::1]'
fi
exec python3 "$ASTER_ENTRYPOINT_ROOT/scripts/aster_supervisor.py" --project-root "$ASTER_ENTRYPOINT_ROOT" \
  --health-url "http://$ASTER_ENTRYPOINT_PROBE:${ASTER_PORT:-8787}/api/health" \
  --output-dir "${ASTER_SUPERVISOR_OUTPUT_DIR:-$ASTER_ENTRYPOINT_DATA/aster-supervisor}" "$@"
