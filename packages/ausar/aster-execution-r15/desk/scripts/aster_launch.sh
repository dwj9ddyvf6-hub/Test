#!/usr/bin/env bash
# Preserve the existing trusted .env startup contract in the parent and children.
# This command never installs or funds a paper/research component.
set -euo pipefail
ASTER_LAUNCH_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ASTER_LAUNCH_ROOT"
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
ASTER_LAUNCH_PYTHON="$ASTER_LAUNCH_ROOT/.venv/bin/python"
if [ ! -x "$ASTER_LAUNCH_PYTHON" ]; then
  printf '%s\n' 'Prepare the project runtime with run.sh before supervised launch.' >&2
  exit 78
fi
ASTER_LAUNCH_PROBE_HOST=127.0.0.1
if [ "${ASTER_HOST:-127.0.0.1}" = '::1' ] || [ "${ASTER_HOST:-127.0.0.1}" = '::' ]; then
  ASTER_LAUNCH_PROBE_HOST='[::1]'
fi
ASTER_LAUNCH_STATE_DIR="$(dirname -- "${ASTER_DB_PATH:-$ASTER_LAUNCH_ROOT/data/aster.sqlite}")"
exec "$ASTER_LAUNCH_PYTHON" "$ASTER_LAUNCH_ROOT/scripts/aster_supervisor.py" \
  --project-root "$ASTER_LAUNCH_ROOT" \
  --health-url "http://$ASTER_LAUNCH_PROBE_HOST:${ASTER_PORT:-8787}/api/health" \
  --output-dir "${ASTER_SUPERVISOR_OUTPUT_DIR:-$ASTER_LAUNCH_STATE_DIR/aster-supervisor}" \
  "$@" -- "$ASTER_LAUNCH_PYTHON" "$ASTER_LAUNCH_ROOT/scripts/aster_services.py"
