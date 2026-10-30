#!/usr/bin/env bash
# Supervisor skeleton: keep ONE desk loop alive. Run it from cron / a scheduler / an agent wake-up.
# Idempotent: running it twice never starts two loops.
#
# Lessons encoded here:
#  * single-instance lock (flock) so two supervisors cannot both start a loop;
#  * the loop is launched with setsid + closed fds so it does NOT belong to the shell/tool session
#    that started it (a loop owned by a tool session dies when the session is reaped);
#  * restart sequence is TERM, wait, then KILL (a hung loop ignores TERM);
#  * heartbeat ages are judged AFTER a VM-pause check: if the wall clock jumped but the monotonic
#    clock did not, grant a grace period instead of killing a healthy loop;
#  * "alive" means the heartbeat is fresh (progress-gated by the loop), not merely that a pid exists.
set -u
ROOT="${DESK_ROOT:-$PWD}"
STATE="$ROOT/state"; mkdir -p "$STATE/log"
HB="$STATE/heartbeat.json"
LOOP_CMD=(python3 -m deskkit_loop)             # replace with your loop entry point
STALE_S="${STALE_S:-900}"                       # heartbeat considered stale after this
GRACE_S="${GRACE_S:-150}"                       # extra grace after a detected VM resume
exec 9>"$STATE/ensure.lock"; flock -n 9 || exit 0

now_wall=$(date +%s); now_mono=$(cut -d. -f1 /proc/uptime)
prev="$STATE/clock_prev"; jump=0
if [ -f "$prev" ]; then
  read -r pw pm < "$prev"
  jump=$(( (now_wall - pw) - (now_mono - pm) ))
fi
echo "$now_wall $now_mono" > "$prev"
[ "$jump" -gt 180 ] && { echo "$(date -Is) VM pause detected (+${jump}s); granting grace" >> "$STATE/log/ensure.log"; sleep "$GRACE_S"; }

hb_age=999999
[ -f "$HB" ] && hb_age=$(( now_wall - $(date -r "$HB" +%s) ))
pid=$(cat "$STATE/loop.pid" 2>/dev/null || true)
alive=0; [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null && alive=1

if [ "$alive" = 1 ] && [ "$hb_age" -lt "$STALE_S" ]; then exit 0; fi

if [ "$alive" = 1 ]; then                       # alive but stale: stop it properly
  echo "$(date -Is) stale heartbeat ${hb_age}s: TERM" >> "$STATE/log/ensure.log"
  kill -TERM "$pid"; for _ in $(seq 15); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  kill -0 "$pid" 2>/dev/null && { echo "$(date -Is) KILL" >> "$STATE/log/ensure.log"; kill -KILL "$pid"; }
fi
# record WHY we are starting (death forensics): uptime, heartbeat age, kernel OOM kills
oom=$(dmesg 2>/dev/null | grep -ci 'out of memory\|oom-kill' || true)
echo "$(date -Is) start loop (alive=$alive hb_age=${hb_age}s oom_kills=$oom)" >> "$STATE/log/ensure.log"
( cd "$ROOT" && setsid -f nohup "${LOOP_CMD[@]}" >> "$STATE/log/loop.out" 2>&1 < /dev/null 9>&- )
sleep 1; pgrep -fn "${LOOP_CMD[*]}" > "$STATE/loop.pid" || true
