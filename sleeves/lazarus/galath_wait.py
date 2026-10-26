"""galath_wait: the producer jobs of the six Lazarus WAIT lanes (lz_wait_q14, _flow, _chase, _olx_books, _r2_dcyan, _intraweek).

The source never fed these lanes. sleeve_feed 1.0.4 kept them as WAIT placeholders, and Research Lab froze their intended rules in
galath-research DESK_INTEGRATION/sleeve_specs/<lane>/README.md (vendored byte-exact). This module runs them on this desk's research
root (<root>/inputs/lazarus, galath_producers.Paths) as background jobs. The rules, divergences and output are documented in
galath_wait_feed.py, the composer.

galath_wait_feed (trading days, 21:30 ET: after tracker_close 16:45, altdata 18:47, lab_live_daily 19:20 with its 5,400 s limit,
sleeve_feed_pm 20:05), in this order:
  1. the OLX lab pass (s_wait_olx_books): the live lab producer DESK_INTEGRATION/lab_live/run/scripts/tensor/lab_live.mjs, run as
     run_lab_live.sh runs each job (cwd = the lab run tree, memguard.sh run -- node --max-old-space-size=4500, MEMGUARD_CAP_MB 6000,
     10,800 s, the box's 08:00 ET day-stop, the lab_live lock), with the OLX ids instead of rules43.ids and --no-books (frozen rules
     only, the CoS parity method of the README), into DESK_INTEGRATION/lab_live/out/olx/<lane>-<signal>-<universe>.json. The 9 jobs
     are the README's producer jobs of the 29 live-loadable rules. A 1D job reruns when its output is older than the panel's last day.
     A 1W job reruns when its output is older than the last complete week, so it runs on Fridays and catches up, like run_lab_live.sh.
     A failed job keeps its previous output.
  2. the partial-week detector (s_wait_intraweek): galath_intraweek.mjs on the tracker's 1wk payloads and closed daily bars.
  3. the composer (the research venv runs galath_wait_feed.py) -> shadow/paper_sleeve/live/wait_fires_v1.json.
galath_wait_compose (trading days, 08:50 ET): the composer alone. It refreshes the file before the open, so a fire stays readable after
a long weekend. The lanes read the file under Lazarus' 80 h freshness rule.
While galath_producers.OFF holds altdata_nightly (its finra_flow plug-in is this desk's reader of FINRA's CDN files, not cleared for
it), both jobs pass the composer --no-finra-fetch with that reason (finra_off): it requests no FINRA file (FEED-04a).

The OLX ids are olx_r12_other.ids when the pinned file is present (INPUTS.json, pending the fetch). Until then they are the rows
the vendored README's rule table flags as live-loadable."""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

from ... import calendar as cal
from ...util import ET
from . import galath_producers as G
from . import galath_wait_feed as F

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSER = os.path.join(HERE, "galath_wait_feed.py")
DETECTOR = os.path.join(HERE, "galath_intraweek.mjs")
LAB = "DESK_INTEGRATION/lab_live"
OLX_README = os.path.join(G.GR, F.SPEC_REL, "s_wait_olx_books", "README.md")
OLX_IDS_REL = f"{F.SPEC_REL}/s_wait_olx_books/olx_r12_other.ids"
OLX_JOBS = (("1D", "green", "full"), ("1D", "green", "covered"), ("1D", "swing", "full"), ("1D", "swing", "covered"),
            ("1W", "cyan", "covered"), ("1W", "green", "full"), ("1W", "green", "covered"), ("1W", "swing", "full"),
            ("1W", "swing", "covered"))
LAB_JOB_TIMEOUT_S = 10800
COMPOSE_TIMEOUT_S = 1800
DETECT_TIMEOUT_S = 1800
LOCK_WAIT_S = 3 * 3600


def olx_ids(paths):
    """(ids, source): the pinned olx_r12_other.ids when present, else the README table's live-loadable rows."""
    p = os.path.join(paths.inputs, OLX_IDS_REL)
    if os.path.exists(p):
        return open(p).read().split(), OLX_IDS_REL
    return F.olx_ids_from_readme(open(OLX_README).read()), "README rule table (olx_r12_other.ids pending the fetch)"


def _sessions(lo, hi):
    d, out = lo, []
    while d <= hi:
        if cal.is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def lab_dates(meta):
    """run_lab_live.sh: (last, from, wk_asof, wk_from) from the live panel meta (last real day; 5 sessions; the last complete week)."""
    last = datetime.strptime(meta.get("last_real_day") or meta["days"][-2], "%Y-%m-%d").date()
    s = _sessions(last - timedelta(days=14), last)
    days = _sessions(last - timedelta(days=21), last + timedelta(days=7))
    wk = lambda x: x.isocalendar()[:2]
    done = [x for x in days if x <= last and x == max(y for y in days if wk(y) == wk(x))]
    a = done[-1]
    return str(last), str(s[-5]), str(a), str(min(y for y in days if wk(y) == wk(a)))


def _lock(path, wait_s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fh = open(path, "w")
    t0 = time.time()
    while True:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fh
        except BlockingIOError:
            if time.time() - t0 > wait_s:
                fh.close()
                return None
            time.sleep(15)


def olx_pass(paths, now_et, runner, lf, env):
    """step 1: the OLX lab jobs -> {job: rc / 'fresh' / 'stopped'}."""
    lab = os.path.join(paths.inputs, LAB)
    run_dir = os.path.join(lab, "run")
    meta_p = os.path.join(run_dir, "data", "canon", "flat", "meta.json")
    if not os.path.exists(meta_p):
        return {"skipped": f"no live lab panel ({LAB}/run/data/canon/flat/meta.json; lab_live_daily builds it)"}
    last, frm, wk_asof, wk_from = lab_dates(json.load(open(meta_p)))
    ids, src = olx_ids(paths)
    ids_file = os.path.join(paths.cache, "wait", "olx_r12_other.ids")
    os.makedirs(os.path.dirname(ids_file), exist_ok=True)
    with open(ids_file, "w") as fh:
        fh.write("\n".join(ids) + "\n")
    out_dir = os.path.join(lab, "out", "olx")
    os.makedirs(os.path.join(lab, "out", "olx_archive"), exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    res = {"ids": len(ids), "ids_source": src, "asof": last, "wk_asof": wk_asof}
    hm = now_et.hour * 100 + now_et.minute
    if now_et.weekday() < 5 and 1615 <= hm <= 1915 and not env.get("LL_FORCE"):
        res["skipped"] = "REFUSE: inside 16:15-19:15 ET (run_lab_live.sh)"
        return res
    lock = _lock(os.path.join(paths.scratch, "lab_live.lock"), LOCK_WAIT_S)
    if lock is None:
        res["skipped"] = "the lab_live lock stayed busy"
        return res
    try:
        mg = os.path.join(paths.inputs, "REBUILD", "box", "backup_tooling", "memguard.sh")
        for lane, sig, uni in OLX_JOBS:
            name = f"{lane}-{sig}-{uni}"
            ja, jf = (wk_asof, wk_from) if lane == "1W" else (last, frm)
            out = os.path.join(out_dir, f"{name}.json")
            try:
                cur = json.load(open(out)).get("asof") or ""
            except (OSError, ValueError):
                cur = ""
            if cur >= ja:
                res[name] = "fresh"
                continue
            t = datetime.now(tz=ET)
            if t.weekday() < 5 and 800 <= t.hour * 100 + t.minute < 1915 and not env.get("LL_NO_DAYSTOP"):
                res[name] = "stopped: past 08:00 ET (run_lab_live.sh day-stop; the desk pre-open is 09:20)"
                break
            tmp = out + ".tmp"
            cmd = ["bash", mg, "run", "--", "node", "--max-old-space-size=4500", "scripts/tensor/lab_live.mjs", lane, sig, uni,
                   "--asof", ja, "--score-from", jf, "--frozen-ids", ids_file, "--no-books", "--out", tmp]
            t0 = time.time()
            lf.write(f"-- olx {name} asof {ja} from {jf}\n")
            lf.flush()
            try:
                rc = runner(cmd, cwd=run_dir, env=dict(env, MEMGUARD_CAP_MB="6000"), stdout=lf, stderr=subprocess.STDOUT,
                            timeout=LAB_JOB_TIMEOUT_S).returncode
            except subprocess.TimeoutExpired:
                rc = 124
            if rc == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                os.replace(tmp, out)
                shutil.copyfile(out, os.path.join(lab, "out", "olx_archive", f"{name}_{ja}.json"))
                res[name] = {"rc": 0, "secs": round(time.time() - t0)}
            else:
                if os.path.exists(tmp):
                    os.remove(tmp)
                res[name] = {"rc": rc, "secs": round(time.time() - t0), "note": "previous output kept"}
    finally:
        lock.close()
    return res


def detect(paths, now, runner, lf, env):
    """step 2: the partial-week detector -> (output path | None, info)."""
    wk = os.path.join(paths.scratch, "shadow", "work", "data", "1wk")
    d1 = os.path.join(paths.scratch, "shadow", "engine", "1d")
    if not (os.path.isdir(wk) and os.path.isdir(d1)):
        return None, {"skipped": "no tracker 1wk payloads / engine 1d store yet"}
    day = datetime.fromtimestamp(now, tz=ET).strftime("%Y-%m-%d")
    out = os.path.join(paths.cache, "wait", f"intraweek_{day}.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["node", "--max-old-space-size=1500", DETECTOR, os.path.join(paths.inputs, "real_engine", "lib", "anna-replica.mjs"), wk, d1, out]
    t0 = time.time()
    try:
        r = runner(cmd, cwd=paths.cache, env=env, capture_output=True, text=True, timeout=DETECT_TIMEOUT_S)
        rc, so = r.returncode, (r.stdout or "").strip().splitlines()
    except subprocess.TimeoutExpired:
        rc, so = 124, []
    lf.write(f"-- intraweek detector rc {rc}: {so[-1] if so else ''}\n")
    info = {"rc": rc, "secs": round(time.time() - t0)}
    try:
        info.update(json.loads(so[-1]))
    except (IndexError, ValueError):
        pass
    for old in sorted(f for f in os.listdir(os.path.dirname(out)) if f.startswith("intraweek_2"))[:-10]:
        os.remove(os.path.join(os.path.dirname(out), old))
    return (out if rc == 0 else None), info


FINRA_OFF = "altdata_nightly"          # the producer whose finra_flow plug-in reads FINRA's CDN files (galath_producers.OFF)


def finra_off():
    """why the composer may request no FINRA CDN file: the owner's OFF switch on the alt-data producer (None: not off)."""
    why = G.OFF.get(FINRA_OFF)
    return f"galath_producers.OFF {FINRA_OFF}: {why}" if why else None


def compose(paths, now, runner, lf, env, detector_out=None):
    """step 3: the composer in the research venv -> its summary dict (raises on failure)."""
    py = os.path.join(paths.inputs, ".venv", "bin", "python")
    off = finra_off()
    cmd = [py, COMPOSER, "--research", paths.inputs, "--scratch", paths.scratch, "--cache", os.path.join(paths.cache, "wait"),
           "--now", str(int(now))] + (["--intraweek", detector_out] if detector_out else []) + \
        (["--no-finra-fetch", off] if off else [])
    r = runner(cmd, cwd=paths.cache, env=env, capture_output=True, text=True, timeout=COMPOSE_TIMEOUT_S)
    lf.write((r.stdout or "")[-2000:] + (r.stderr or "")[-2000:])
    if r.returncode != 0:
        raise RuntimeError(f"wait_feed composer rc {r.returncode}: {(r.stderr or r.stdout or '')[-300:]}")
    try:
        return json.loads((r.stdout or "").strip().splitlines()[-1])
    except (IndexError, ValueError):
        return {"stdout": (r.stdout or "")[-300:]}


def run_job(name, root, now, cfg=None, runner=subprocess.run, venv=True, extra_env=None):
    """galath_wait_feed (OLX lab pass, intraweek detector, composer) | galath_wait_compose (composer) on the research root."""
    now_et = datetime.fromtimestamp(now, tz=ET)
    if not cal.is_trading_day(now_et.date()):
        return {"skipped": "not a trading day"}
    paths = G.Paths(root, cfg)
    mat = G.materialize(paths)
    if venv:
        G.ensure_venv(paths, runner)
    env = G.env_of(paths, extra_env)
    os.makedirs(paths.logs, exist_ok=True)
    info = {"materialized": len(mat["files"])}
    with open(os.path.join(paths.logs, f"{name}.log"), "a") as lf:
        lf.write(f"\n== {now_et.isoformat()} {name}\n")
        lf.flush()
        det = None
        if name == "galath_wait_feed":
            info["olx"] = olx_pass(paths, now_et, runner, lf, env)
            det, info["intraweek"] = detect(paths, now, runner, lf, env)
        info["compose"] = compose(paths, now, runner, lf, env, det)
    return info


def _job(name):
    def run(engine):
        return run_job(name, engine.root, engine.clock(), getattr(engine, "cfg", None))
    run.__name__ = name
    return run


JOBS = {"galath_wait_feed": ("weekday:12345&et:21:30-23:59", 72000, _job("galath_wait_feed")),
        "galath_wait_compose": ("weekday:12345&et:08:50-09:19", 72000, _job("galath_wait_compose"))}


def sleeves():
    return []


if __name__ == "__main__":                            # manual run: python -m desk.sleeves.families.galath_wait <job> <root>
    print(json.dumps(run_job(sys.argv[1], sys.argv[2], time.time()), default=str))
