"""Watchdog / supervisor (HARDEN always-on, H21/H22; research adopts
R-ADOPT-1 restart-intensity cap + R-ADOPT-2 verified-work heartbeat).

The desk's runner (desk3.run_live) is a detached process; the agent
layer that launched it restarts often and must not be in the trading
path. This watchdog is the desk's OWN supervision: a second detached
process that verifies the runner by EFFECTS — the heartbeat the runner
writes itself (state/runner.json: pid + cycle + ts, rewritten only
after a completed cycle) plus the pid's live /proc cmdline — never by
a pattern the checker's own command line could match.

Posture:
- Healthy = pid alive with a desk3.run_live cmdline AND heartbeat age
  <= GRACE_S (3x the 60 s cycle). A heartbeat is trusted only as
  evidence of a VERIFIED completed cycle (run_live writes it after
  run_cycle returns), never as a liveness ping alone.
- Unhealthy (dead pid, stale heartbeat, missing heartbeat) -> relaunch
  the runner detached (setsid), in desired_mode() — its last
  recorded mode before FLIP_AT, dispatch from FLIP_AT onward (A9).
  Every restart is journaled to state/watchdog.jsonl with old/new
  pid + reason.
- Restart intensity (R-ADOPT-1): at most MAX_RESTARTS relaunches in
  WINDOW_S; beyond the cap the watchdog stops relaunching, writes the
  named DEGRADED state to state/watchdog.json, and journals it —
  a crash-looping runner is surfaced, not respawned forever.
- Launch hold (LAUNCH-KILL-LOOP cure, 2026-11-04): a launched runner
  past LAUNCH_GRACE_S with no heartbeat yet is held, not terminated,
  while sleeve journals or the warm product show activity inside
  HOLD_WINDOW_S. First cycles under load legitimately outrun the
  launch grace; killing them made each next first cycle slower and
  produced the 2026-11-03 300.5-minute cycle hole (32 terminations).
  A silent launch (no activity in the window) is still terminated
  and relaunched exactly as before.
- Single instance: an flock on state/watchdog.lock; a second watchdog
  (or a --once check while the loop runs) reports 'supervised' and
  changes nothing. If the recorded runner pid is alive, no second
  runner is ever launched (duplicate-order guard at the source; the
  dispatcher's seen-index + broker client-order-id dedup are the
  second and third lines).
- A9 Monday flip (A9-FLIP-20261025): mode used to be decided ONLY by
  the `--dispatch` argv flag at runner launch, and this watchdog
  preserved the recorded mode forever — so Monday's live session
  depended on a human remembering OPERATIONS.md's manual relaunch.
  The watchdog now owns the flip: desired_mode() returns "dispatch"
  from FLIP_AT (Mon 2026-10-26 09:25 ET, five minutes before the
  open) onward. A healthy evaluate-only runner past FLIP_AT is
  terminated (verified dead, A-01) and relaunched in dispatch mode,
  journaled as `mode_flip`; any relaunch past FLIP_AT launches
  dispatch regardless of the recorded mode. After the flip, the
  first post-flip `fill` event in state/dispatcher.jsonl is read
  back at the broker (PaperDoor.get_order_by_client_id +
  get_positions) and the proof written to state/a9_first_fill.json
  exactly once — A9 closes on that broker read-back, not on the
  dispatcher's own journal.
- Internal only: no external dead-man service (owner retired it
  2026-10-23).

Run:  python3 -m desk3.watchdog --loop   (detached, forever)
      python3 -m desk3.watchdog --once   (single check; exit 0 ok /
      supervised, 3 degraded, 4 restarted-this-check is still exit 0 —
      see status file; the journal is the record)
      python3 -m desk3.watchdog --status (print state/watchdog.json)
"""
from __future__ import annotations
import fcntl, json, os, subprocess, sys, time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYCLE_S = 60
GRACE_S = 600          # AUDIT-CURE 2026-10-25 (A-01/A-02): the 180 s
                       # grace was shorter than the REAL cycle period
                       # (measured ~275 s: ~215 s evaluation + 60 s
                       # sleep, 312-sleeve roster), so slow-but-live
                       # cycles were misjudged stale and relaunched
                       # BESIDE the live runner (33 restarts on
                       # 2026-10-25, duplicate runners 970 + 2520).
                       # 600 s ~= 2x the measured worst period.
WEDGED_S = 1800        # a LIVE pid whose heartbeat is older than this
                       # is treated as wedged: it is terminated FIRST
                       # (verified dead) and only then relaunched —
                       # never duplicated (A-01).
LAUNCH_GRACE_S = 900   # a fresh runner's first cycle runs the full
                       # producer warm (measured up to ~440 s cold);
                       # the heartbeat still names the PREVIOUS pid
                       # until that cycle lands, so a launched pid is
                       # judged by its launch age, not the stale file
HOLD_WINDOW_S = 1800   # LAUNCH-KILL-LOOP cure 2026-11-04: past launch
                       # grace, a launched runner is HELD (not killed)
                       # while desk activity (sleeve journal writes or
                       # the warm product landing) is newer than this
                       # window — on 2026-11-03 first cycles under load
                       # outran the 900 s grace and 32 healthy launches
                       # were terminated mid-cycle, a self-exciting
                       # loop that produced a 300.5-minute cycle hole.
                       # No activity inside the window keeps the old
                       # launched_no_heartbeat behaviour exactly.
CHECK_S = 30
MAX_RESTARTS = 3       # R-ADOPT-1 restart-intensity cap
WINDOW_S = 600
FLIP_AT = datetime(2026, 10, 26, 13, 25, tzinfo=timezone.utc)
# A9: Mon 2026-10-26 09:25 ET (EDT = UTC-4) — five minutes before
# the 09:30 RTH open. Before this instant the recorded mode is
# preserved exactly as before; from it onward the desk's desired
# mode is dispatch (paper door only — PaperDoor refuses live).


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _sd_notify(msg):
    """SUPERVISION-HARDEN-20261114: systemd keep-alive. Sends one
    sd_notify datagram when running under systemd (NOTIFY_SOCKET
    set); a no-op everywhere else, so --once checks, tests and
    detached runs are byte-identical to before. The loop sends
    READY=1 after its first completed check pass and WATCHDOG=1
    after every completed pass: the keep-alive is tied to real
    supervision work (a full check_once), never to a timer alone,
    so a wedged loop stops pinging and systemd's WatchdogSec
    restarts the watchdog instead of admiring a live-but-stuck
    process."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    try:
        import socket as _socket
        if addr.startswith("@"):
            addr = "\0" + addr[1:]
        sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_DGRAM)
        try:
            sock.sendto(msg.encode(), addr)
        finally:
            sock.close()
    except Exception:
        pass


def read_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return None


def pid_alive_desk(pid):
    """Effects check: the pid exists AND its own cmdline is the runner.
    Never a pgrep-style pattern over other processes."""
    if not pid:
        return False
    try:
        with open(f"/proc/{int(pid)}/cmdline", "rb") as fh:
            cmd = fh.read().replace(b"\0", b" ").decode(errors="replace")
    except Exception:
        return False
    return "desk3.run_live" in cmd


def live_runner_pids():
    """Every pid whose OWN /proc cmdline is desk3.run_live (A-01).
    Enumerates /proc directly — never a pgrep pattern that the
    checker's own command line could match."""
    out = set()
    try:
        entries = os.listdir("/proc")
    except OSError:
        return out
    for name in entries:
        if not name.isdigit():
            continue
        pid = int(name)
        if pid == os.getpid():
            continue
        if pid_alive_desk(pid):
            out.add(pid)
    return out


def _terminate(pid):
    """SIGTERM a wedged runner and verify it died. Returns True only
    when the pid is confirmed no longer a live runner."""
    import signal
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError:
        return not pid_alive_desk(pid)
    for _ in range(50):
        if not pid_alive_desk(pid):
            return True
        time.sleep(0.1)
    return False


def runner_health(state_dir, now=None):
    now = now or _now()
    hb = read_json(os.path.join(state_dir, "runner.json"))
    if not hb:
        return {"healthy": False, "reason": "no_heartbeat", "pid": None,
                "cycle": None, "age_s": None, "mode": None}
    pid = hb.get("pid")
    alive = pid_alive_desk(pid)
    age = None
    try:
        ts = datetime.fromisoformat(str(hb.get("ts")))
        age = (now - ts).total_seconds()
    except Exception:
        age = None
    if not alive:
        reason = "pid_dead"
    elif age is None:
        reason = "heartbeat_unparsable"
    elif age > GRACE_S:
        reason = f"heartbeat_stale:{age:.0f}s>{GRACE_S}s"
    else:
        reason = "ok"
    return {"healthy": reason == "ok", "reason": reason, "pid": pid,
            "cycle": hb.get("cycle"), "age_s": age,
            "mode": hb.get("mode")}


def _journal(state_dir, row):
    path = os.path.join(state_dir, "watchdog.jsonl")
    with open(path, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


_BOOT_ID = False


def _boot_id():
    """PID-DEAD-BOOT-CLASS-20261108: the host's current boot id
    (/proc/sys/kernel/random/boot_id), read once per watchdog
    process. Restart and termination rows carry it so a runner
    death can be classified after the fact: a row whose boot_id
    differs from the previous row's died WITH the host (the
    2026-11-08 evidence: full OS boots at ~2h cadence, journal
    'Journal started' at each, watchdog service and runner both
    new at the same minute, and the incoming watchdog recording
    pid_dead for a runner the reboot killed). A death inside one
    boot keeps the old meaning. Unreadable -> None, never fatal."""
    global _BOOT_ID
    if _BOOT_ID is False:
        try:
            with open("/proc/sys/kernel/random/boot_id") as fh:
                _BOOT_ID = fh.read().strip() or None
        except OSError:
            _BOOT_ID = None
    return _BOOT_ID


def _prior_boot_id(state_dir):
    """The boot_id on the most recent watchdog journal row that
    carries one (restart and wedged_terminated rows do), or None
    when the journal has no boot evidence yet."""
    path = os.path.join(state_dir, "watchdog.jsonl")
    if not os.path.exists(path):
        return None
    prior = None
    for line in open(path).read().splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("boot_id"):
            prior = r["boot_id"]
    return prior


def _death_class(state_dir, boot_id):
    """RUNNER-DEATH-CLASS-20261116: classify a runner death from
    the journal's own boot evidence. Sunday 2026-11-15 produced 16
    restart rows, all journaled as the same unexplained pid_dead;
    counted afterward, 13 carried a boot_id different from the
    previous restart row (the runner died WITH the host at the
    platform's roughly hourly boot cadence, and the incoming
    watchdog's relaunch was recorded as a runner death) and 3 were
    same-boot deaths by SIGTERM during the night's landing
    activity. The classes keep those populations separate forever:
    host_boot_recovery (the boot changed since the last journaled
    boot evidence; the death is the platform's, the recovery is
    the watchdog's), same_boot_death (the boot did not change; a
    genuine in-boot runner death, carrying its exit evidence), and
    unclassified_no_prior_boot (no prior boot evidence exists to
    judge against). Returns (death_class, prior_boot_id)."""
    prior = _prior_boot_id(state_dir)
    if prior is None or boot_id is None:
        return "unclassified_no_prior_boot", prior
    if prior != boot_id:
        return "host_boot_recovery", prior
    return "same_boot_death", prior


def restarts_in_window(state_dir, now=None):
    now = now or _now()
    path = os.path.join(state_dir, "watchdog.jsonl")
    n = 0
    if os.path.exists(path):
        for line in open(path).read().splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") != "restart":
                continue
            try:
                t = datetime.fromisoformat(str(r.get("ts")))
            except Exception:
                continue
            if 0 <= (now - t).total_seconds() <= WINDOW_S:
                n += 1
    return n


# DSK-9 death-evidence (NO-PARTIALS DRIVE 2026-11-11): the watchdog
# used to discard the Popen handle at launch, so a launched runner's
# exit status (code or killing signal) was unrecoverable and death
# rows carried no signal, code, or memory evidence at all. Handles
# launched by THIS watchdog process are retained here so the death
# row can reap them; runners adopted from another watchdog life are
# not children and cannot be waited, so for those the last VmHWM
# sample (below) is the only memory evidence the platform offers.
_CHILDREN = {}


def note_launched_child(pid, proc):
    """Retain a launched child's handle for death evidence (DSK-9)."""
    if pid is not None and proc is not None:
        _CHILDREN[int(pid)] = proc


def _death_evidence(pid):
    """Reap a retained child and return its exit evidence, or {}.

    exit_code is set for a normal exit, exit_signal for a death by
    signal (Popen returncode is negative the signal number).
    child_peak_rss_kb is RUSAGE_CHILDREN's ru_maxrss after the reap:
    the peak RSS of the largest reaped child of this process, named
    as the aggregate it is."""
    if pid is None:
        return {}
    proc = _CHILDREN.pop(int(pid), None)
    if proc is None:
        return {}
    try:
        rc = proc.poll()
        if rc is None:
            rc = proc.wait(timeout=5)
    except Exception:
        return {}
    out = {}
    if rc is not None:
        if rc < 0:
            out["exit_signal"] = -rc
        else:
            out["exit_code"] = rc
    try:
        import resource
        out["child_peak_rss_kb"] = int(
            resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    except Exception:
        pass
    return out


def _pid_vmhwm_kb(pid):
    """Peak RSS (VmHWM) of a live pid from /proc, or None (DSK-9)."""
    try:
        with open(f"/proc/{int(pid)}/status") as fh:
            for line in fh:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except Exception:
        return None
    return None


def _record_mem_sample(state_dir, pid):
    kb = _pid_vmhwm_kb(pid)
    if kb is None or not pid:
        return
    try:
        path = os.path.join(state_dir, "watchdog_mem.json")
        data = read_json(path) or {}
        data[str(pid)] = {"vmhwm_kb": kb, "ts": _iso(_now())}
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(data, fh, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        pass


def _last_mem_sample(state_dir, pid):
    if not pid:
        return {}
    data = read_json(os.path.join(state_dir, "watchdog_mem.json")) or {}
    row = data.get(str(pid)) or {}
    if "vmhwm_kb" in row:
        return {"last_vmhwm_kb": row["vmhwm_kb"],
                "last_vmhwm_ts": row.get("ts")}
    return {}


def default_launcher(root, mode):
    """Relaunch the runner detached (setsid) exactly as OPERATIONS.md
    documents; returns the new pid. The caller passes desired_mode():
    the recorded mode before FLIP_AT, dispatch from FLIP_AT (A9)."""
    state = os.path.join(root, "state")
    log_name = ("runner_dispatch.log" if mode == "dispatch"
                else "runner_eval.log")
    log = open(os.path.join(state, log_name), "ab")
    args = [sys.executable, "-u", "-m", "desk3.run_live"]
    if mode == "dispatch":
        args.append("--dispatch")
    proc = subprocess.Popen(args, cwd=root, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    note_launched_child(proc.pid, proc)  # DSK-9: keep the handle
    return proc.pid


def desired_mode(now, recorded_mode):
    """A9 mode predicate. Before FLIP_AT: the recorded mode, exactly
    the pre-A9 preservation behavior. At/after FLIP_AT: "dispatch" —
    Monday's session must not depend on a human relaunch."""
    if now >= FLIP_AT:
        return "dispatch"
    return recorded_mode or "evaluate-only"


def _flip_ts(state_dir):
    """Ts of the journaled mode_flip event, or None."""
    path = os.path.join(state_dir, "watchdog.jsonl")
    if not os.path.exists(path):
        return None
    for line in open(path).read().splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("event") == "mode_flip":
            try:
                return datetime.fromisoformat(str(r.get("ts")))
            except Exception:
                return None
    return None


def a9_readback(state_dir, now=None, door=None):
    """A9 first-fill broker read-back. Finds the first dispatcher
    `fill` event at/after the flip boundary (FLIP_AT, or the
    journaled mode_flip ts when later), reads that order back at
    the broker, and writes state/a9_first_fill.json exactly once.
    Returns the proof dict, the existing proof, or None when no
    post-flip fill exists yet. A submit ACK is not a fill: the
    verdict is FILLED_READ_BACK only when the BROKER's own record
    says filled with filled_qty > 0."""
    now = now or _now()
    path = os.path.join(state_dir, "a9_first_fill.json")
    existing = read_json(path)
    if existing:
        return existing
    boundary = FLIP_AT
    ft = _flip_ts(state_dir)
    if ft is not None and ft > boundary:
        boundary = ft
    dpath = os.path.join(state_dir, "dispatcher.jsonl")
    fill = None
    if os.path.exists(dpath):
        for line in open(dpath).read().splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") != "fill":
                continue
            try:
                ts = datetime.fromisoformat(str(r.get("ts")))
            except Exception:
                continue
            if ts >= boundary:
                fill = r
                break
    if fill is None:
        return None
    if door is None:
        from desk3.broker import PaperDoor
        from desk3.run_live import credential_env
        door = PaperDoor(env=credential_env())
    coid = fill.get("client_order_id")
    order = door.get_order_by_client_id(coid)
    positions = door.get_positions()
    filled_qty = float(order.get("filled_qty") or 0)
    proof = {
        "event": "a9_first_fill",
        "ts": _iso(now),
        "client_order_id": coid,
        "intent_id": fill.get("intent_id"),
        "sleeve": fill.get("sleeve"),
        "symbol": fill.get("symbol"),
        "side": fill.get("side"),
        "journal_qty": fill.get("qty"),
        "journal_price": fill.get("price"),
        "journal_ts": fill.get("ts"),
        "broker_status": order.get("status"),
        "broker_filled_qty": filled_qty,
        "broker_filled_avg_price": order.get("filled_avg_price"),
        "broker_position_qty": positions.get(fill.get("symbol")),
        "verdict": ("FILLED_READ_BACK"
                    if order.get("status") == "filled" and filled_qty > 0
                    else "SUBMITTED_NOT_FILLED"),
    }
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(proof, fh, sort_keys=True)
    os.replace(tmp, path)
    _journal(state_dir, {"event": "a9_first_fill_readback",
                         "ts": _iso(now), "client_order_id": coid,
                         "verdict": proof["verdict"]})
    return proof


def write_status(state_dir, row):
    path = os.path.join(state_dir, "watchdog.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(row, fh, sort_keys=True)
    os.replace(tmp, path)


def _launched_path(state_dir):
    return os.path.join(state_dir, "watchdog_launched.json")


def _read_launched(state_dir):
    return read_json(_launched_path(state_dir))


def _write_launched(state_dir, pid, mode, now):
    path = _launched_path(state_dir)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump({"pid": pid, "mode": mode or "evaluate-only",
                   "ts": _iso(now)}, fh, sort_keys=True)
    os.replace(tmp, path)


def _clear_launched(state_dir):
    try:
        os.remove(_launched_path(state_dir))
    except OSError:
        pass


def _recent_desk_activity(state_dir, now):
    """True when the desk shows work landing inside HOLD_WINDOW_S:
    the newest sleeve journal write (state/<sleeve>/journal.jsonl)
    or the warm product (state/warm_bars.json). A launched runner
    mid-first-cycle writes both long before its first heartbeat; a
    truly wedged launch writes neither. Bounded stat scan, no reads.
    """
    cutoff = now.timestamp() - HOLD_WINDOW_S
    newest = None

    def _see(path):
        nonlocal newest
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return
        if newest is None or mtime > newest:
            newest = mtime

    try:
        names = os.listdir(state_dir)
    except OSError:
        return False
    for name in names:
        if name == "warm_bars.json":
            _see(os.path.join(state_dir, name))
        else:
            _see(os.path.join(state_dir, name, "journal.jsonl"))
    return newest is not None and newest >= cutoff


def _pid_cpu_jiffies(pid):
    """utime+stime from /proc/<pid>/stat, or None when unreadable.
    The comm field may contain spaces/parens; fields after the last
    ')' are field 3 onward, so utime (14) sits at index 11 and
    stime (15) at index 12 of the post-comm list."""
    try:
        with open(f"/proc/{int(pid)}/stat", "rb") as fh:
            data = fh.read().decode("utf-8", "replace")
        parts = data[data.rindex(")") + 2:].split()
        return int(parts[11]) + int(parts[12])
    except Exception:
        return None


def _record_launched_cpu(state_dir, launched, jiffies):
    """Persist the launched record with its latest CPU sample,
    preserving pid/mode/ts exactly (the launch age is judged from
    the original ts)."""
    path = _launched_path(state_dir)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump({"pid": launched.get("pid"),
                   "mode": launched.get("mode") or "evaluate-only",
                   "ts": launched.get("ts"),
                   "cpu_jiffies": jiffies}, fh, sort_keys=True)
    os.replace(tmp, path)


def check_once(root=ROOT, launcher=None, now=None, live_pids=None,
               killer=None):
    """One supervision pass. Returns a status dict; relaunches at most
    once, and only when the runner is proven unhealthy by effects AND
    no desk3.run_live pid is alive anywhere (A-01: a live runner is
    NEVER duplicated — a stale-but-alive runner is named, and a wedged
    one is terminated and verified dead before any relaunch)."""
    now = now or _now()
    state_dir = os.path.join(root, "state")
    os.makedirs(state_dir, exist_ok=True)
    health = runner_health(state_dir, now=now)
    if live_pids is None:
        live_pids = live_runner_pids()
    else:
        live_pids = set(live_pids)
    # DSK-9: while the heartbeat pid is alive, keep a fresh VmHWM
    # sample so its death row can carry the last peak memory even
    # when this watchdog did not launch it (adopted runners cannot
    # be waited; the sample is the only memory evidence available).
    if health.get("pid") is not None and health["pid"] in live_pids:
        _record_mem_sample(state_dir, health["pid"])
    base = {"ts": _iso(now), "watchdog_pid": os.getpid(),
            "runner_pid": health["pid"], "runner_cycle": health["cycle"],
            "heartbeat_age_s": (None if health["age_s"] is None
                                else round(health["age_s"], 1)),
            "reason": health["reason"]}
    if health["healthy"]:
        want = desired_mode(now, health["mode"])
        if want != (health["mode"] or "evaluate-only"):
            # A9 flip: healthy runner, wrong mode, past FLIP_AT.
            # A-01 still governs: never flip beside a stranger pid,
            # and relaunch only on a verified death.
            strangers = {p for p in live_pids if p != health["pid"]}
            if strangers:
                row = {**base, "status": "flip_blocked_duplicate",
                       "live_runner_pids": sorted(live_pids),
                       "detail": ("mode flip due but a desk3.run_live "
                                  "pid exists that the heartbeat does "
                                  "not name; refusing to flip (A-01)")}
                write_status(state_dir, row)
                return {**row, "action": "none"}
            killer = killer or _terminate
            if not killer(health["pid"]):
                row = {**base, "status": "degraded",
                       "detail": ("mode flip due but the evaluate-only "
                                  "runner could not be terminated; left "
                                  "in place by name, no duplicate "
                                  "launched (A-01)")}
                write_status(state_dir, row)
                return {**row, "action": "degraded"}
            launcher = launcher or default_launcher
            new_pid = launcher(root, want)
            _write_launched(state_dir, new_pid, want, now)
            _journal(state_dir, {"event": "mode_flip", "ts": _iso(now),
                                 "old_pid": health["pid"],
                                 "new_pid": new_pid,
                                 "from_mode": health["mode"],
                                 "to_mode": want,
                                 "reason": "a9_monday_flip"})
            row = {**base, "status": "flipped", "new_pid": new_pid,
                   "mode": want}
            write_status(state_dir, row)
            return {**row, "action": "flip"}
        _clear_launched(state_dir)
        if want == "dispatch":
            try:
                a9_readback(state_dir, now=now)
            except Exception:
                pass  # read-back retries next pass; supervision first
        write_status(state_dir, {**base, "status": "ok"})
        return {**base, "status": "ok", "action": "none"}
    # A-01 duplicate guard, ahead of every relaunch path: any live
    # runner that is not the heartbeat pid (and not a tracked launch
    # still in its first cycle, handled below) means a runner EXISTS.
    # Launching another one races the same state/snapshot/dispatcher
    # files — name the state, launch nothing.
    launched_pre = _read_launched(state_dir)
    launched_pid = launched_pre.get("pid") if launched_pre else None
    strangers = {p for p in live_pids
                 if p != health["pid"] and p != launched_pid}
    if strangers:
        row = {**base, "status": "duplicate_alive",
               "live_runner_pids": sorted(live_pids),
               "detail": ("a desk3.run_live pid is alive that the "
                          "heartbeat does not name; refusing to "
                          "launch another runner (A-01)")}
        write_status(state_dir, row)
        return {**row, "action": "none"}
    # Stale heartbeat but the heartbeat pid itself is ALIVE: a slow or
    # wedged cycle, not a dead runner. Below WEDGED_S it is named and
    # left alone; beyond it, terminate FIRST and relaunch only on a
    # verified death.
    if (health["pid"] is not None and health["pid"] in live_pids
            and str(health["reason"]).startswith("heartbeat_stale")):
        age = health["age_s"] or 0
        if age <= WEDGED_S:
            row = {**base, "status": "stale_but_alive",
                   "detail": ("runner pid alive with heartbeat age "
                              f"{age:.0f}s > grace {GRACE_S}s but "
                              f"<= wedged {WEDGED_S}s; named, not "
                              "duplicated (A-01/A-02)")}
            write_status(state_dir, row)
            return {**row, "action": "none"}
        killer = killer or _terminate
        if not killer(health["pid"]):
            row = {**base, "status": "degraded",
                   "detail": ("wedged runner pid could not be "
                              "terminated; left in place by name, "
                              "no duplicate launched (A-01)")}
            write_status(state_dir, row)
            return {**row, "action": "degraded"}
        _journal(state_dir, {"event": "wedged_terminated",
                             "ts": _iso(now), "pid": health["pid"],
                             "reason": health["reason"],
                             "boot_id": _boot_id(),
                             **_death_evidence(health["pid"]),
                             **_last_mem_sample(state_dir,
                                                 health["pid"])})
        live_pids.discard(health["pid"])
    # A runner WE launched may still be in its first cycle: the
    # heartbeat file legitimately still names the previous (dead) pid
    # until that cycle lands. Judging that window by the stale file
    # relaunched a second and third runner live on 2026-10-25
    # (BUGLOG HARDEN-WD1) — judge the launched pid by its launch age.
    launched = _read_launched(state_dir)
    if launched and launched.get("pid") != health["pid"]:
        if pid_alive_desk(launched.get("pid")):
            try:
                launch_age = (now - datetime.fromisoformat(
                    str(launched.get("ts")))).total_seconds()
            except Exception:
                launch_age = None
            # CPU-progress sample (LAUNCH-HOLD-CPU-20261104): the
            # warm/startup phase writes no journals, so journal
            # activity alone cannot see a launched runner that is
            # working but has not reached evaluation yet. Jiffies
            # advancing between checks IS progress; a wedged launch
            # burns none. The sample rides the launched record.
            jiffies = _pid_cpu_jiffies(launched.get("pid"))
            prev_jiffies = launched.get("cpu_jiffies")
            if jiffies is not None and jiffies != prev_jiffies:
                try:
                    _record_launched_cpu(state_dir, launched, jiffies)
                except OSError:
                    pass
            if launch_age is not None and launch_age <= LAUNCH_GRACE_S:
                row = {**base, "status": "starting",
                       "launched_pid": launched.get("pid"),
                       "launch_age_s": round(launch_age, 1)}
                write_status(state_dir, row)
                return {**row, "action": "none"}
            if (jiffies is not None and prev_jiffies is not None
                    and jiffies > prev_jiffies):
                row = {**base, "status": "launch_hold",
                       "launched_pid": launched.get("pid"),
                       "detail": ("launched runner past launch grace "
                                  "with no heartbeat yet, but its CPU "
                                  f"time advanced ({prev_jiffies} -> "
                                  f"{jiffies} jiffies) between checks; "
                                  "held, not terminated "
                                  "(LAUNCH-HOLD-CPU-20261104)")}
                write_status(state_dir, row)
                return {**row, "action": "none"}
            health = {**health, "reason": "launched_no_heartbeat"}
            base["reason"] = health["reason"]
        else:
            _clear_launched(state_dir)
    elif launched and launched.get("pid") == health["pid"]:
        _clear_launched(state_dir)  # heartbeat caught up, then died
    # LAUNCH-KILL-LOOP cure 2026-11-04: the launched runner is past its
    # grace and the heartbeat still names the dead pid, but the desk's
    # own journals prove work is landing — the runner is mid-first-
    # cycle, not wedged. Hold: name it, kill nothing, launch nothing.
    # Silence inside HOLD_WINDOW_S falls through to the old path.
    if (health.get("reason") == "launched_no_heartbeat"
            and _recent_desk_activity(state_dir, now)):
        row = {**base, "status": "launch_hold",
               "launched_pid": launched.get("pid"),
               "detail": ("launched runner past launch grace with no "
                          "heartbeat yet, but sleeve journals / warm "
                          "product show activity inside "
                          f"{HOLD_WINDOW_S}s; held, not terminated "
                          "(LAUNCH-KILL-LOOP cure 2026-11-04)")}
        write_status(state_dir, row)
        return {**row, "action": "none"}
    prior = restarts_in_window(state_dir, now=now)
    if prior >= MAX_RESTARTS:
        row = {**base, "status": "degraded",
               "detail": (f"restart cap {MAX_RESTARTS}/{WINDOW_S}s hit; "
                          "runner left down by name, not respawned")}
        prev = read_json(os.path.join(state_dir, "watchdog.json")) or {}
        write_status(state_dir, row)
        if prev.get("status") != "degraded":  # journal the transition once
            _journal(state_dir, {"event": "degraded", "ts": _iso(now),
                                 "reason": health["reason"],
                                 "restarts_in_window": prior})
        return {**row, "action": "degraded"}
    # Final A-01 guard immediately before any launch: no live runner
    # pid may exist. A tracked launch past its grace that is still
    # alive is terminated and verified dead first, like a wedged
    # heartbeat pid; anything else still alive blocks the launch.
    if live_pids:
        killer = killer or _terminate
        for pid in sorted(live_pids):
            if killer(pid):
                _journal(state_dir, {"event": "wedged_terminated",
                                     "ts": _iso(now), "pid": pid,
                                     "reason": health["reason"],
                                     "boot_id": _boot_id(),
                                     **_death_evidence(pid),
                                     **_last_mem_sample(state_dir, pid)})
                live_pids.discard(pid)
        if live_pids:
            row = {**base, "status": "degraded",
                   "live_runner_pids": sorted(live_pids),
                   "detail": ("live runner pid(s) could not be "
                              "terminated; no duplicate launched "
                              "(A-01)")}
            write_status(state_dir, row)
            return {**row, "action": "degraded"}
    launcher = launcher or default_launcher
    want = desired_mode(now, health["mode"])
    new_pid = launcher(root, want)
    _write_launched(state_dir, new_pid, want, now)
    _dclass, _prior_boot = _death_class(state_dir, _boot_id())
    _journal(state_dir, {"event": "restart", "ts": _iso(now),
                         "reason": health["reason"],
                         "death_class": _dclass,
                         "prev_boot_id": _prior_boot,
                         "old_pid": health["pid"], "new_pid": new_pid,
                         "mode": want, "boot_id": _boot_id(),
                         **_death_evidence(health["pid"]),
                         **_last_mem_sample(state_dir, health["pid"])})
    row = {**base, "status": "restarted", "new_pid": new_pid,
           "death_class": _dclass,
           "restarts_in_window": prior + 1}
    write_status(state_dir, row)
    return {**row, "action": "restart"}


def acquire_lock(state_dir):
    path = os.path.join(state_dir, "watchdog.lock")
    fh = open(path, "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    fh.seek(0); fh.truncate(); fh.write(str(os.getpid())); fh.flush()
    return fh


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    state_dir = os.path.join(ROOT, "state")
    os.makedirs(state_dir, exist_ok=True)
    if "--status" in argv:
        print(json.dumps(read_json(os.path.join(state_dir,
                                                "watchdog.json")), indent=2))
        return 0
    lock = acquire_lock(state_dir)
    if lock is None:
        print("supervised: another watchdog holds the lock")
        return 0
    if "--once" in argv:
        row = check_once(ROOT)
        print(json.dumps(row, sort_keys=True))
        return 3 if row["status"] == "degraded" else 0
    # --loop (default for the detached supervisor)
    _ready_sent = False
    while True:
        try:
            check_once(ROOT)
        except Exception as e:  # supervisor must outlive its own errors
            try:
                write_status(state_dir,
                             {"ts": _iso(_now()), "status": "error",
                              "detail": f"{type(e).__name__}:{e}",
                              "watchdog_pid": os.getpid()})
            except Exception:
                pass
        # SUPERVISION-HARDEN-20261114: a pass completed (check_once
        # ran, or its failure was journaled above -- either way the
        # loop is alive and working): ping systemd. A pass that
        # never returns sends nothing, by design.
        if not _ready_sent:
            _sd_notify("READY=1")
            _ready_sent = True
        _sd_notify("WATCHDOG=1")
        time.sleep(CHECK_S)


if __name__ == "__main__":
    sys.exit(main())
