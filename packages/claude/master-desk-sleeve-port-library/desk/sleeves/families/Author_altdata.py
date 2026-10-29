"""Author_altdata: the alt-data producer of the Lazarus Q07 lanes, rebuilt as one lean job per source (act1, 2026-10-26).

It replaces altdata_nightly (ALTDATA_LIVE/nightly.sh, Author_producers.OFF), which ran every plug-in in one bash script. Its
2026-10-19 run did 15 minutes of work, then slept 3 h 45 min on another job's done marker (OPTIONS_IVSKEW's snapshot, whose
collector had failed at 18:45) until the desk's 4 h limit killed bash and left the plug-in polling as an orphan. Here each
source is its own background job, none waits on another job's marker, and each reads only what a live lane needs:

  job                       window (ET)            source            writes (research root <root>/inputs/lazarus)
  Author_altdata_wiki       every day 19:00-23:59  Wikimedia         WIKI_LIVE/data/wiki_pv_live.parquet, then the vendored
                                                                     features.py: WIKI_LIVE/out/wiki_features_{latest,history}
  Author_altdata_finra      weekdays 19:15-23:59   FINRA             ALTDATA_LIVE/data/finra/{shvol,ats}, then the vendored
                                                                     finra_flow build: out/finra_ats_events, finra_svr_history
  Author_altdata_sec        weekdays 19:30-23:59   SEC EDGAR         the vendored form4_insider: out/insider2_{latest,history}
  Author_altdata_options weekdays 19:40-23:59  SqueezeMetrics     ALTDATA_LIVE/out/options_market_{latest,history}.parquet from
                                                                     the host job squeezemetrics' series (no request of its own)
  Author_altdata_wswing     every day 20:30-23:59  none (offline)    the vendored w_swing_feed: w_swing_live/out (needs the
                                                                     wiki job's D+1 rows, so it runs after it, every day; no
                                                                     switch: it requests nothing, and its flags of a source that
                                                                     is off stay None, so the cells needing them fail closed)

Every day, weekends included: the Monday 09:00 sleeve feed needs Sunday's wiki rows (sleeve_wiki: the expected asof is
yesterday, the heartbeat at most 30 h old) and the week's swing book needs the Saturday wiki rows (w_swing_feed: wiki asof D+1).

Switches (config/altdata.json): a source runs only while its switch is on; a missing file, source or key is off, a barred
source never runs, and the SEC also needs a contact. The personal-email guard refuses any User-Agent with a personal address
(a consumer mail domain or Apple's private relay) or a browser string; the SEC switch with no contact, or with a refused one,
is off. Shipped (owner D33/D34, terms read 2026-10-26, SOURCES.md): wikimedia on; finra off (its terms forbid robots and
trade-prediction use of its files, and its API needs a credential); sec, finra and squeezemetrics on since 2026-10-27 (DAT-09/11/12).

The network is Author_altdata_run.py's (run by the research venv): at most one request a second per host across processes,
the honest User-Agent, a stop at the first 403 / 429 or challenge page, no retry after a proxy 403 / 407. A refused source
waits out its Retry-After, an hour at least, before its next run (REFUSAL_REST_S).
Each run is time-boxed well under the desk's 4 h limit (TIME_BOX_S) in its own process group, which is killed whole at the
box. Partial-safe: a source writes only its own outputs, each replaced atomically and only after a complete fetch; a failed
or cut run leaves its last good files and says so on its heartbeat (status fail, the last success kept)."""
import json
import os
import re
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CONFIG = os.path.join(ROOT, "config", "altdata.json")
RUNNER = os.path.join(HERE, "Author_altdata_run.py")
SOURCES = ("wikimedia", "finra", "sec", "squeezemetrics")
# job -> the source switch it needs (None: no source of its own, it runs offline), its desk schedule and time box (s); once a day
JOB_SOURCE = {"wiki": "wikimedia", "finra": "finra", "sec": "sec", "wswing": None, "options": "squeezemetrics"}
PRODUCER = {"wiki": "wiki", "finra": "altdata", "sec": "altdata", "wswing": "altdata", "options": "altdata"}    # Author_producers.missing_inputs
SCHEDULE = {"wiki": "et:19:00-23:59", "finra": "weekday:12345&et:19:15-23:59", "sec": "weekday:12345&et:19:30-23:59",
            "wswing": "et:20:30-23:59", "options": "weekday:12345&et:19:40-23:59"}
TIME_BOX_S = {"wiki": 45 * 60, "finra": 20 * 60, "sec": 45 * 60, "wswing": 30 * 60, "options": 10 * 60}
CADENCE_S = 20 * 3600
REFUSAL_REST_S = 3600
KILL_GRACE_S = 20

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
# consumer mailbox domains (and Apple's relay for them): an address there is a person's, never a desk's role contact
PERSONAL_DOMAINS = ("gmail.com", "googlemail.com", "yahoo.", "ymail.com", "rocketmail.com", "hotmail.", "outlook.", "live.",
                    "msn.com", "icloud.com", "me.com", "mac.com", "aol.com", "proton.me", "protonmail.", "pm.me",
                    "privaterelay.appleid.com", "gmx.", "mail.com", "yandex.", "zoho.com", "fastmail.", "hey.com",
                    "tutanota.", "tuta.io", "qq.com", "163.com", "126.com", "comcast.net", "verizon.net", "att.net",
                    "sbcglobal.net")
BROWSER = re.compile(r"\b(?:mozilla|applewebkit|chrome|chromium|safari|gecko|firefox|edg|edge|trident|opera|opr)/|\bmsie \d|"
                     r"like gecko", re.I)    # a browser's product tokens (name/version), never a word such as "Operations"


def guard_user_agent(ua):
    """the personal-email guard: the User-Agent unchanged, or ValueError when it is empty, names a browser, or holds a
    personal address."""
    if not ua or not str(ua).strip():
        raise ValueError("empty User-Agent")
    if BROWSER.search(ua):
        raise ValueError("browser User-Agent refused: a script never impersonates a browser")
    for m in EMAIL.finditer(ua):
        dom = m.group(1).lower()
        if any(dom == p or dom.startswith(p) or dom.endswith("." + p) for p in PERSONAL_DOMAINS):
            raise ValueError("personal email address refused in the User-Agent (the owner's rule)")
    return ua


def _read(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def switches(path=None):
    """{source: {on, why, ...}} from config/altdata.json: a source is on only when its switch says so, is not barred, and (the
    SEC) has a contact the guard accepts. Absent file / source / key: off."""
    cfg = _read(path or CONFIG) or {}
    src = cfg.get("sources") if isinstance(cfg.get("sources"), dict) else {}
    ua = cfg.get("user_agent")
    out = {}
    for name in SOURCES:
        s = src.get(name) if isinstance(src.get(name), dict) else {}
        on, why = s.get("on") is True, str(s.get("why") or "")
        if s.get("barred"):
            on, why = False, f"barred: {why}".strip()
        elif not on:
            why = f"switched off in config/altdata.json: {why}".strip() if s else "no switch in config/altdata.json (off by default)"
        row = {"on": on, "why": why}
        if on:
            try:
                row["user_agent"] = guard_user_agent(ua)
                if name == "sec":
                    contact = str(s.get("contact") or "").strip()
                    if not contact:
                        raise ValueError("the SEC switch is on but no contact is set (SEC fair access needs one)")
                    row["user_agent"] = guard_user_agent(f"{ua} {contact}")
            except ValueError as e:
                row = {"on": False, "why": f"refused: {e}"}
        out[name] = row
    return out


def off_reason(source, sw=None):
    """None while the source runs, else why it does not."""
    r = (sw or switches()).get(source) or {"on": False, "why": "unknown source"}
    return None if r["on"] else f"{source}: {r['why']}"


# --------------------------------------------------------------------------------------------- the run, time-boxed
def _rest_path(paths, job):
    return os.path.join(paths.cache, "altdata", f"{job}.json")


def resting(paths, job, now):
    """the refusal rest still running for a job (its record), else None."""
    r = _read(_rest_path(paths, job)) or {}
    return r if float(r.get("rest_until") or 0) > now else None


def run_group(cmd, cwd, env, timeout_s, log, popen=subprocess.Popen, clock=time.time):
    """run cmd in its own process group; at the time box the whole group is stopped (TERM, then KILL). -> (rc, stdout lines,
    timed_out). A plain subprocess timeout kills only the direct child: on 2026-10-19 the orphaned plug-in kept polling."""
    p = popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=log, text=True, start_new_session=True)
    try:
        out, _ = p.communicate(timeout=timeout_s)
        return p.returncode, (out or "").splitlines(), False
    except subprocess.TimeoutExpired:
        for sig, wait in ((signal.SIGTERM, KILL_GRACE_S), (signal.SIGKILL, 5)):
            try:
                os.killpg(p.pid, sig)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                out, _ = p.communicate(timeout=wait)
                break
            except subprocess.TimeoutExpired:
                out = ""
        return (p.returncode if p.returncode is not None else -9), (out or "").splitlines(), True


def run_job(job, root, now, cfg=None, runner=None, venv=True, sw=None, popen=subprocess.Popen):
    """one per-source run on the research root -> info dict; raises on a failed run (the job record says ok false)."""
    from . import Author_producers as G
    sw = sw or switches()
    why = off_reason(JOB_SOURCE[job], sw) if JOB_SOURCE[job] else None
    if why:
        return {"skipped": why}
    paths = G.Paths(root, cfg)
    rest = resting(paths, job, now)
    if rest:
        return {"skipped": f"resting after a refusal until {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(rest['rest_until']))}: "
                           f"{rest.get('why')}"}
    mat = G.materialize(paths)
    req, opt = G.missing_inputs(paths, PRODUCER[job])
    if req:
        raise RuntimeError(f"altdata: {len(req)} required pinned inputs missing: {', '.join(req[:8])}")
    if venv:
        G.ensure_venv(paths, runner or subprocess.run)
    py = os.path.join(paths.inputs, ".venv", "bin", "python") if venv else sys.executable
    os.makedirs(os.path.join(paths.cache, "altdata"), exist_ok=True)
    cmd = [py, RUNNER, job, "--research", paths.inputs, "--scratch", paths.scratch, "--state",
           os.path.join(paths.cache, "altdata"), "--now", str(int(now)), "--deadline", str(int(now + TIME_BOX_S[job] - 60))]
    env = G.env_of(paths, {"ALTDATA_USER_AGENT": (sw[JOB_SOURCE[job]].get("user_agent") if JOB_SOURCE[job] else "") or "",
                           "WSW_NO_NET": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    os.makedirs(paths.logs, exist_ok=True)
    t0 = time.time()
    with open(os.path.join(paths.logs, f"altdata_{job}.log"), "a") as lf:
        lf.write(f"\n== {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))} altdata {job}\n")
        lf.flush()
        rc, out, cut = run_group(cmd, paths.cache, env, TIME_BOX_S[job], lf, popen=popen)
    try:
        info = json.loads(out[-1]) if out else {}
    except ValueError:
        info = {"stdout": out[-1][-300:]}
    info.update(rc=rc, secs=round(time.time() - t0), materialized=len(mat["files"]), missing_optional_inputs=len(opt))
    if cut:
        info["time_box"] = f"stopped at its {TIME_BOX_S[job]} s box (process group killed)"
    if info.get("refused"):
        rest_s = max(REFUSAL_REST_S, float(info.get("retry_after_s") or 0))
        with open(_rest_path(paths, job) + ".tmp", "w") as f:
            json.dump({"rest_until": now + rest_s, "why": info["refused"], "at": now}, f)
        os.replace(_rest_path(paths, job) + ".tmp", _rest_path(paths, job))
    if rc != 0 or cut:
        raise RuntimeError(f"altdata {job} rc {rc}{' (time box)' if cut else ''}: {json.dumps(info, default=str)[:300]}")
    return info


def _job(job):
    def run(engine):
        return run_job(job, engine.root, engine.clock(), getattr(engine, "cfg", None))
    run.__name__ = f"Author_altdata_{job}"
    return run


JOBS = {f"Author_altdata_{job}": (SCHEDULE[job], CADENCE_S, _job(job)) for job in JOB_SOURCE}


def sleeves():
    return []
