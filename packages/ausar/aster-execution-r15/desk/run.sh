#!/usr/bin/env bash
set -euo pipefail
ASTER_PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ASTER_PROJECT_ROOT"
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
if [ ! -x .venv/bin/python ]; then
  python -m venv .venv
fi
ASTER_REQUIREMENTS_FILE=requirements-lock.txt
if [ ! -f "$ASTER_REQUIREMENTS_FILE" ]; then ASTER_REQUIREMENTS_FILE=requirements.txt; fi
ASTER_REQUIREMENTS_HASH="$(sha256sum "$ASTER_REQUIREMENTS_FILE" | cut -d ' ' -f 1)"
if [ ! -f .venv/.aster-requirements ] || [ "$(cat .venv/.aster-requirements)" != "$ASTER_REQUIREMENTS_HASH" ]; then
  .venv/bin/python -m pip install --quiet -r "$ASTER_REQUIREMENTS_FILE"
  echo "$ASTER_REQUIREMENTS_HASH" > .venv/.aster-requirements
fi
ASTER_FRONTEND_LOCK_HASH="$(sha256sum frontend/package-lock.json | cut -d ' ' -f 1)"
if [ ! -d frontend/node_modules ] || [ ! -f frontend/node_modules/.aster-package-lock ] || [ "$(cat frontend/node_modules/.aster-package-lock)" != "$ASTER_FRONTEND_LOCK_HASH" ]; then
  (cd frontend && npm ci --no-audit --no-fund)
  echo "$ASTER_FRONTEND_LOCK_HASH" > frontend/node_modules/.aster-package-lock
fi
(cd frontend && npm run build)
printf '\nAster Desk: http://%s:%s\n' "${ASTER_HOST:-127.0.0.1}" "${ASTER_PORT:-8787}"
exec .venv/bin/python -m uvicorn backend.app:app --host "${ASTER_HOST:-127.0.0.1}" --port "${ASTER_PORT:-8787}"

