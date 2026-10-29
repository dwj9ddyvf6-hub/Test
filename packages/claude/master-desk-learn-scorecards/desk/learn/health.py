"""Self-awareness: is the desk alive, are its sleeves running when they should, are its inputs healthy, did
its jobs run, is its ledger intact, did its sleeves' decisions execute, is its clock right. Every check is OK / WARN /
CRIT with the evidence that decided it."""
import json
import os
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, time as dtime

from .. import calendar as cal
from .. import jobs as desk_jobs
from ..schedule import is_open
from ..util import ET, iso, read_json, write_json_atomic

LEVELS = {"OK": 0, "WARN": 1, "CRIT": 2}
EPS = 1e-9
DEFER_REPEAT = 3              # a parent deferred in this many passes of the window is deferred repeatedly
JOB_STEP_S = 240              # the job-window scan's step: shorter than every job's window (the funding relay's 270 s)
JOB_BACK_S = 4 * 86400        # how far back a window open at the horizon is followed to its start
CLOCK_MAX_OFFSET_S = 0.25     # the clock row warns past this offset from NTP time, or when not synchronized
CLOCK_TIMEOUT_S = 2.0         # the clock tools' whole budget
# a quote source the books' open positions are marked on is read every pass (Engine._mark): one the passes have not
# read for this long, while they ran, has gone stale (30 passes at the 30 s tick; the open's longest pass took 7.3 min)
QUOTE_STALE_S = 900.0


def _ledger_tail(path, max_bytes=8_000_000):
    if not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        f.seek(0, 2)
        n = f.tell()
        f.seek(max(0, n - max_bytes))
        lines = f.read().splitlines()
    out = []
    for ln in lines[1:] if n > max_bytes else lines:
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def _last_window_start(schedule, now, horizon=86400, step=300):
    """start of the most recent opening of the schedule within the horizon (None if it never opened)."""
    t = now
    seen_open = None
    while t >= now - horizon:
        o = is_open(schedule, t)
        if o:
            seen_open = t
        elif seen_open is not None:
            return seen_open
        t -= step
    return seen_open


def _session_start(now):
    """00:00 ET of the session the desk is in once it has opened, else of the most recent session: the execution
    outcomes and the job windows are judged over the current or most recent session and everything since (on a
    Sunday or before Monday's open: from Friday 00:00 ET)"""
    d = cal._as_date(now)
    if not cal.is_trading_day(d) or now < cal.session_open(d):
        d = cal.prev_trading_day(d)
    return datetime.combine(d, dtime(0, 0), ET).timestamp()


def _at(text):
    try:
        return datetime.fromisoformat(text).timestamp()
    except (TypeError, ValueError):
        return None


def _outcomes(tail, since, running=None):
    """The execution-outcome sentinel over the ledger tail's whole passes since `since` (a pass is its records from
    pass_start to pass_end; the one the tail's start cuts is skipped) -> [(check, "WARN", detail)], one row per
    reason, each naming its sleeves, never one row a sleeve:
      blocked:<reason>    every due evaluation of a running sleeve (`running`: ids, None for any) emitted a blocker,
                          a signal intent whose reason starts "blocker:". An evaluation's intents are its `signals`
                          record: a blocker's `observation` is written once per signal key in observation_dedupe_s
                          (6 h), so it cannot count evaluations. A sleeve is listed under its most frequent blocker.
      expired:entry_unfilled  an entry child (its `child` record's action "enter") expired with nothing filled
                          (`child_expired`, filled_v 0). An expiry whose child record is older than the tail is not
                          classified (counted as unclassified).
      deferred:<what>     a parent deferred in DEFER_REPEAT or more of the window's passes: the OMS's alert records
                          that defer one ("no reference price; parent deferred", the mleg and cross deferrals),
                          keyed by instrument or child; its sleeves are those with children on it in the tail."""
    action, by_inst, by_child = {}, defaultdict(set), {}     # from every record of the tail, the window's or older
    due, hit, why = Counter(), Counter(), defaultdict(Counter)
    expired, defer = [], defaultdict(lambda: defaultdict(set))   # what -> key -> the passes it was deferred in
    buf, whole, passes, cut, first = [], False, 0, 0, None
    for r in tail:
        k = r.get("kind")
        if k == "pass_start":
            buf, whole = [], True
            continue
        if k == "child" or k == "rule_exit":
            action[r.get("child")] = r.get("action") if k == "child" else "exit"
            by_inst[r.get("inst")].add(r.get("sleeve"))
            by_child[r.get("child")] = r.get("sleeve")
        if k != "pass_end":
            buf.append(r)
            continue
        s = r.get("summary") or {}
        at, mine, buf, ok, whole = _at(s.get("at")), buf, [], whole, False
        if not ok or at is None or at < since:
            continue
        passes, first = passes + 1, first or at
        listed = s.get("due") or []
        cut += int(s.get("n_due") or 0) > len(listed)        # the record lists 400 due sleeves at most
        seen = set(listed)
        for x in mine:
            kind = x.get("kind")
            if kind == "signals" and x.get("sleeve"):
                seen.add(x["sleeve"])
                b = {str(i.get("reason"))[8:].strip() for i in x.get("intents") or []
                     if str(i.get("reason") or "").startswith("blocker:")}
                if b:
                    hit[x["sleeve"]] += 1
                    why[x["sleeve"]].update(b)
            elif kind == "child_expired" and float(x.get("filled_v") or 0.0) <= EPS:
                expired.append(x)
            elif kind == "alert" and "deferred" in str(x.get("what")):
                defer[str(x["what"])][str(x.get("inst") or x.get("child"))].add(passes)
        due.update(seen)
    window = {"since": iso(since), "from": first and iso(first), "passes": passes}   # the tail may start after since
    if cut:
        window["due_lists_cut"] = cut
    out, rows = [], defaultdict(list)
    for sid, n in hit.items():
        if n == due[sid] and (running is None or sid in running):
            top = sorted(why[sid].items(), key=lambda kv: (-kv[1], kv[0]))
            rows[top[0][0]].append((sid, n, [k for k, _ in top[1:]]))
    for reason, got in sorted(rows.items()):
        got.sort()
        out.append(("blocked:" + reason, "WARN", dict(window, sleeves=[g[0] for g in got],
                                                      evaluations={g[0]: g[1] for g in got},
                                                      also={g[0]: g[2] for g in got if g[2]})))
    entries = [x for x in expired if action.get(x.get("child")) == "enter"]
    if entries:
        out.append(("expired:entry_unfilled", "WARN", dict(
            window, sleeves=sorted({str(x.get("sleeve")) for x in entries}),
            children=[{k: x.get(k) for k in ("child", "sleeve", "inst", "vqty")} for x in entries[-20:]],
            unclassified=sum(1 for x in expired if x.get("child") not in action))))
    for what, keys in sorted(defer.items()):
        many = {key: len(ps) for key, ps in sorted(keys.items()) if len(ps) >= DEFER_REPEAT}
        if many:
            owners = set().union(*(by_inst.get(key) or ({by_child[key]} if key in by_child else set()) for key in many))
            out.append(("deferred:" + what, "WARN", dict(window, deferred=many,
                                                         sleeves=sorted(str(s) for s in owners if s))))
    return out


def _flip(schedule, lo, hi):
    """lo and hi on either side of one of the schedule's edges (whole seconds): the edge to the second -> (the last
    second like lo, the first like hi)"""
    a = is_open(schedule, lo)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if is_open(schedule, mid) == a:
            lo = mid
        else:
            hi = mid
    return lo, hi


def _closed_window(schedule, now, since, after=float("-inf"), step=JOB_STEP_S, back=JOB_BACK_S):
    """(first, last) open second of the schedule's most recent window that has closed, when it closed at or after
    `since` and opened after `after` (a job's last start); else None. Probes every `step` seconds back from now
    (shorter than any job's window) and bisects each edge: at most (now - max(since, after)) / step + 20 schedule
    reads, and a window open for days is followed back `back` seconds at most."""
    t, floor = int(now), max(since, after)
    while is_open(schedule, t):                  # the window open now has not closed
        t -= step
        if t < floor:
            return None
    while not is_open(schedule, t):              # back across the gap to the last open second
        t -= step
        if t < floor:
            return None
    end = _flip(schedule, t, t + step)[0]
    s = t
    while s - step > t - back and is_open(schedule, s - step):
        s -= step
        if s < after:                            # the last start fell inside this window: it ran
            return None
    start = _flip(schedule, s - step, s)[1]
    return None if start <= after else (start, end)


def _missed_jobs(root, jobs, now, since, sched=None):
    """{job: {"window": [first, last second], "last_started"}} for each scheduled job whose most recent window closed
    since `since` without a run while it was due by its cadence. A job with no run on record is not judged (its
    window may predate its code), nor one always open, nor the chain probe once done, nor one whose previous run was
    still going when the window opened."""
    sched, by_state, out = sched or desk_jobs.schedules(), desk_jobs.cadences(), {}
    for name, (spec, cadence) in sorted(sched.items()):
        rec = jobs.get(name) or {}
        if rec.get("started") is None or all(a.strip() == "always" for a in (spec or "always").split(",")):
            continue
        last, fin = float(rec["started"]), rec.get("finished")
        w = _closed_window(spec, now, since, after=last)
        if w is None:                            # no window closed since `since`, or the last run is inside or after it
            continue
        start, end = w
        if name in by_state:
            cadence = by_state[name](rec, end)
        if last + float(cadence) > end or fin is None or float(fin) < last or float(fin) >= start:
            continue                             # not due in it, or the previous run still going when it opened
        if name == "chain_probe":                # done for good once its result is recorded (as jobs.due has it)
            from ..data import chain_probe
            if chain_probe.done(root):
                continue
        out[name] = {"window": [iso(start), iso(end)], "last_started": iso(last)}
    return out


_UNITS = {"ns": 1e-9, "us": 1e-6, "µs": 1e-6, "ms": 1e-3, "min": 60.0, "s": 1.0, "h": 3600.0}
_SPAN = r"(\d+(?:\.\d+)?)\s*(ns|us|µs|ms|min|s|h)\b"


def _tool(cmd, timeout):
    """a read-only command's output; None when it is missing, fails or outlasts its timeout"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def _span_s(text):
    """systemd's signed time span ("+215us", "-1.311ms", "+1min 2.5s") -> seconds; None when unreadable"""
    m = re.match(r"\s*([+-]?)\s*(\d.*)$", text or "")
    parts = re.findall(_SPAN, m.group(2)) if m else []
    if not parts:
        return None
    v = sum(float(n) * _UNITS[u] for n, u in parts)
    return -v if m.group(1) == "-" else v


def clock_status(run=None, which=None, timeout=CLOCK_TIMEOUT_S):
    """(level, detail) of the system clock, from read-only tools within `timeout` seconds in all: `chronyc tracking`
    when chrony is present (its "System time" offset, its leap status), else `timedatectl show -p NTPSynchronized`
    and `timedatectl timesync-status` (its Offset). WARN when not synchronized or the offset is past
    CLOCK_MAX_OFFSET_S; OK "unknown" when no tool answers (a container, CI)."""
    run, which = run or _tool, which or shutil.which
    end = time.monotonic() + timeout

    def left():
        return max(0.05, min(timeout, end - time.monotonic()))

    def verdict(source, synced, offset):
        d = {"source": source, "synchronized": synced, "offset_ms": None if offset is None else round(offset * 1000, 3),
             "max_offset_ms": int(CLOCK_MAX_OFFSET_S * 1000)}
        bad = not synced or (offset is not None and abs(offset) > CLOCK_MAX_OFFSET_S)
        return ("WARN" if bad else "OK"), d
    if which("chronyc"):
        out = run(["chronyc", "tracking"], left())
        f = {k.strip(): v.strip() for k, v in (ln.split(":", 1) for ln in (out or "").splitlines() if ":" in ln)}
        m = re.match(r"(\d+(?:\.\d+)?) seconds (slow|fast)", f.get("System time", ""))
        if m and f.get("Leap status"):
            off = float(m.group(1)) * (1 if m.group(2) == "fast" else -1)
            return verdict("chronyc", f["Leap status"] != "Not synchronised", off)
    if which("timedatectl"):
        sync = (run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], left()) or "").strip()
        if sync in ("yes", "no"):
            st = run(["timedatectl", "timesync-status"], left()) or ""
            m = re.search(r"^\s*Offset:\s*(.+)$", st, re.M)
            return verdict("timedatectl", sync == "yes", _span_s(m.group(1)) if m else None)
    return "OK", {"clock": "unknown"}


def _marked_on(root):
    """{quote source: open positions marked on it} from state/books.json (desk/router.py quote_source_for, as
    Engine._mark reads them every pass)"""
    from ..router import quote_source_for
    out = Counter()
    for b in (read_json(os.path.join(root, "state", "books.json"), {}) or {}).values():
        for inst in (b.get("positions") or {}) if isinstance(b, dict) else ():
            src = quote_source_for(None, inst)[0]
            if src:
                out[src] += 1
    return out


def check(root, now=None, sleeves=None, loop_tick_s=30):
    now = float(now or time.time())
    checks = []

    def add(name, level, detail):
        checks.append({"check": name, "level": level, "detail": detail})

    hb = read_json(os.path.join(root, "state", "heartbeat.json"), {}) or {}
    age = now - float(hb.get("at") or 0)
    add("heartbeat", "OK" if age < 6 * loop_tick_s else "WARN" if age < 900 else "CRIT",
        {"age_s": round(age, 1), "passes": hb.get("passes"), "mode": hb.get("mode"), "errors": hb.get("errors")})
    try:
        marked = _marked_on(root) if hb.get("data") else Counter()
    except Exception:                            # unreadable books: the sources' own ok decides, as before
        marked = Counter()
    for src, h in sorted((hb.get("data") or {}).items()):
        bad = isinstance(h, dict) and h.get("ok") is False
        if not bad and src.startswith("quotes:") and marked.get(src[7:]) and isinstance(h, dict) and h.get("at"):
            lag = float(hb.get("at") or 0) - float(h["at"])  # the last pass's start against this source's last read
            if lag > QUOTE_STALE_S:
                bad, h = True, dict(h, why="stale: the passes have not read it for %.0f s; %d open positions mark on "
                                           "it" % (lag, marked[src[7:]]))
        add("data:" + src, "WARN" if bad else "OK", h)
    desk = read_json(os.path.join(root, "state", "desk.json"), {}) or {}
    last_run = desk.get("last_run") or {}
    for s in sleeves or ():
        c = s.CONFIG
        if c.status == "parked":
            continue
        start = _last_window_start(c.schedule, now)
        lr = float(last_run.get(c.sleeve_id) or 0)
        if start is None:
            continue
        missed = lr < start - max(c.cadence_s, 600) and now - start > 900
        d = {"last_run_age_s": round(now - lr, 1) if lr else None, "window_start_age_s": round(now - start, 1)}
        blocked = (getattr(c, "params", None) or {}).get("blocked")
        if blocked:                    # its input is switched off (the missing piece): it runs, and cannot fire (FEED-02)
            d.update(ready=False, blocked=blocked)
        add("sleeve:" + c.sleeve_id, "WARN" if missed else "OK", d)
    tail = _ledger_tail(os.path.join(root, "state", "ledger.jsonl"))
    recs = [r for r in tail if r.get("kind") == "sleeve_error"]
    errs = {}
    for r in recs:
        errs.setdefault(r.get("sleeve"), []).append(r.get("error"))
    for sid, es in sorted(errs.items()):
        add("errors:" + str(sid), "WARN" if len(es) < 10 else "CRIT", {"n": len(es), "last": es[-1]})
    try:
        st = os.statvfs(root)
        free_mb = st.f_bavail * st.f_frsize / 1048576.0
        add("disk", "OK" if free_mb >= 2048 else "WARN" if free_mb >= 512 else "CRIT", {"free_mb": round(free_mb)})
    except OSError:
        pass
    jobs = read_json(os.path.join(root, "state", "jobs.json"), {}) or {}
    alive = set(desk_jobs.running(root))
    sched = desk_jobs.schedules()
    for name, j in sorted(jobs.items()):
        d = {k: j.get(k) for k in ("started", "finished", "ok", "info")}
        if name not in sched:          # retired (a deactivated row's producer, a removed job): its record is history
            add("job:" + name, "OK", dict(d, why="not scheduled"))
            continue
        level = "WARN" if j.get("ok") is False else "OK"         # its last run failed, or the one before was lost
        if j.get("ok") is False and not desk_jobs.unfinished(j):
            d["failed_in_a_row"] = int(j.get("retries") or 0) + 1   # retried RETRY_S later, RETRIES times at most
        if desk_jobs.unfinished(j):
            age = now - float(j["started"])
            if name not in alive:                                 # killed (a restart, the OOM killer) or crashed
                level, d["why"] = "WARN", "lost: started %.0f s ago, its process is gone, no finish recorded" % age
            elif age > desk_jobs.RESTART_WAIT_MAX_S:             # a hung job holds its slot until a restart
                level, d["why"] = "WARN", "running %.1f h" % (age / 3600.0)
        add("job:" + name, level, d)
    since = _session_start(now)
    running = None if sleeves is None else {s.CONFIG.sleeve_id for s in sleeves if s.CONFIG.status != "parked"}
    try:                                         # a check that cannot read the record is a row, never a lost report
        for name, level, d in _outcomes(tail, since, running):
            add(name, level, d)
    except Exception as e:
        add("outcomes", "WARN", {"error": f"{type(e).__name__}: {str(e)[:160]}"})
    try:
        # a job's windows are judged back JOB_BACK_S, past the session's start: a window missed in an earlier session
        # stays a row until the job runs again (a weekly job's Sunday window was forgotten at Monday's open, a daily
        # job's previous evening at the next session's start)
        horizon = min(since, now - JOB_BACK_S)
        missed = _missed_jobs(root, jobs, now, horizon, sched)
        if missed:
            add("jobs:window_missed", "WARN", {"since": iso(horizon), "jobs": missed})
    except Exception as e:
        add("jobs:window_missed", "WARN", {"error": f"{type(e).__name__}: {str(e)[:160]}"})
    try:
        add("clock", *clock_status())
    except Exception as e:
        add("clock", "OK", {"clock": "unknown", "error": f"{type(e).__name__}: {str(e)[:160]}"})
    level = max((c["level"] for c in checks), key=lambda x: LEVELS[x], default="OK")
    return {"level": level, "at": now, "checks": checks}


def summary(hl):
    """a report as the outside check reads it (the owner's watch session, docs/HANDOFF.md): its level, the CRIT
    checks by name and the WARN count, about 0.1 KB where health.json is about 38 KB"""
    checks = hl.get("checks") or []
    return {"level": hl["level"], "at": hl["at"], "crit": [c["check"] for c in checks if c["level"] == "CRIT"],
            "warn": sum(1 for c in checks if c["level"] == "WARN")}


def write(root, hl):
    """state/health.json and beside it its summary, state/health_level.json"""
    st = os.path.join(root, "state")
    write_json_atomic(os.path.join(st, "health.json"), hl)
    write_json_atomic(os.path.join(st, "health_level.json"), summary(hl))
