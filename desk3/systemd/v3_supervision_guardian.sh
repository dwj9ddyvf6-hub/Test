#!/usr/bin/env bash
# v3 supervision guardian (EGRESS-2 cure, route B).
#
# Why this exists: the platform rebuilds /etc/systemd/system at VM
# boot/replacement, wiping the installed watchdog unit. Only the
# home directory persists. This script lives in the repo at
# desk3/systemd/v3_supervision_guardian.sh and is installed
# byte-identically under ~/hooks/scripts/ as a Muse hook
# (id: v3-supervision-guardian, poll 60 s). Hook definitions are
# runtime-managed saved work and are restored after replacement.
#
# Behaviour: silent when healthy; on absence it reinstalls the
# canonical unit, daemon-reloads, enables, starts, and verifies by
# effects. It wakes an agent only when its own heal fails.
set -uo pipefail
source "$HATCH_HOOK_RUNTIME"

REPO="/home/hatch/workspace/muse-desk-v3"
CANON="/home/hatch/workspace/muse-desk-v3/desk3/systemd/muse-desk-v3-watchdog.service"
INSTALLED="/etc/systemd/system/muse-desk-v3-watchdog.service"
SVC="muse-desk-v3-watchdog.service"
WD_JSON="$REPO/state/watchdog.json"
HEALTH_JSON="$REPO/state/health.json"
LOCK="$REPO/state/guardian.lock"

fresh_enough() {
  # $1=file $2=json ts field $3=max age seconds
  python3 - "$1" "$2" "$3" <<'PYEOF'
import json, sys
from datetime import datetime, timezone
try:
    d = json.load(open(sys.argv[1]))
    ts = datetime.fromisoformat(str(d[sys.argv[2]]))
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    sys.exit(0 if age <= float(sys.argv[3]) else 1)
except Exception:
    sys.exit(1)
PYEOF
}

runner_count() {
  # AUDIT-CURE 2026-10-25 (A-04): the guardian was blind to duplicate
  # runners — A-01 (two desk3.run_live processes racing the same
  # state) passed every healthy poll. Count runners by their OWN
  # /proc cmdlines (never a pgrep pattern this script's own command
  # line could match: this script's cmdline names the guardian, and
  # the python probe below reads /proc entries directly).
  python3 - <<'PYEOF'
import os, sys
n = 0
for name in os.listdir("/proc"):
    if not name.isdigit():
        continue
    try:
        with open(f"/proc/{name}/cmdline", "rb") as fh:
            cmd = fh.read().replace(b"\0", b" ").decode(errors="replace")
    except Exception:
        continue
    if "desk3.run_live" in cmd and "python" in cmd:
        n += 1
print(n)
PYEOF
}

reason="healthy"
healthy() {
  if [ ! -f "$INSTALLED" ]; then reason="unit_missing"; return 1; fi
  if ! cmp -s "$INSTALLED" "$CANON"; then reason="unit_differs"; return 1; fi
  if ! systemctl is-active --quiet "$SVC"; then reason="service_inactive"; return 1; fi
  if ! fresh_enough "$WD_JSON" ts 240; then reason="watchdog_stale"; return 1; fi
  if ! fresh_enough "$HEALTH_JSON" generated_at 900; then reason="health_stale"; return 1; fi
  if [ "$(runner_count)" -gt 1 ]; then reason="duplicate_runner"; return 1; fi
  reason="healthy"; return 0
}

healed_enough() {
  [ -f "$INSTALLED" ] && cmp -s "$INSTALLED" "$CANON" \
    && systemctl is-active --quiet "$SVC" \
    && fresh_enough "$WD_JSON" ts 240 \
    && [ "$(runner_count)" -le 1 ]
}

if healthy; then
  silent "v3 supervision healthy" '{"status":"ok"}'
  exit 0
fi
absent_reason="$reason"

if [ "${HATCH_HOOK_DRY_RUN:-0}" = "1" ]; then
  wake "v3 supervision absent (dry run, no heal attempted): $absent_reason" "{\"reason\":\"$absent_reason\",\"dry_run\":true}"
  exit 0
fi

# Single healer: never two concurrent reinstalls.
exec 9>"$LOCK"
if ! flock -n 9; then
  silent "v3 supervision heal already in progress" "{\"reason\":\"$absent_reason\"}"
  exit 0
fi

log "supervision absent; healing" "{\"reason\":\"$absent_reason\"}"
if [ ! -f "$INSTALLED" ] || ! cmp -s "$INSTALLED" "$CANON"; then
  cp "$CANON" "$INSTALLED" 2>/dev/null || true
  chmod 644 "$INSTALLED" 2>/dev/null || true
fi
systemctl daemon-reload 2>/dev/null || true
systemctl enable "$SVC" 2>/dev/null || true
if ! systemctl is-active --quiet "$SVC"; then
  systemctl start "$SVC" 2>/dev/null || systemctl restart "$SVC" 2>/dev/null || true
fi

ok=0
for _ in $(seq 1 24); do
  if healed_enough; then ok=1; break; fi
  sleep 5
done

if [ "$ok" = "1" ]; then
  log "supervision healed" "{\"reason\":\"$absent_reason\"}"
  silent "v3 supervision healed hands-free after absence: $absent_reason" "{\"healed\":true,\"reason\":\"$absent_reason\"}"
  exit 0
fi

wake "v3 supervision heal failed; agent intervention required: $absent_reason" "{\"healed\":false,\"reason\":\"$absent_reason\"}"
exit 0
