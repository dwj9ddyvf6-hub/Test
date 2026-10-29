"""md2 entrypoint.  python3 -m mdesk.main pass|loop|catalog|status [--force-open] [--ledger PATH] [--no-muse]"""
import sys, os, time, json, argparse, fcntl, signal
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from mdesk import registry, desk as D
from mdesk.engines import muse
ROOT = "/workspace/desk2"

def _bk():
    sys.path.insert(0, f"{ROOT}/tools"); import backup; return backup

PHASE_S = 20   # bar-settle margin after the 5-min boundary
JOBS = (("09:20", "pre-open"), ("21:30", "night"))   # ET, weekdays: full bar + options/kraken/earnings warm via the vendored warmers
def _jobs(last):
    import subprocess, datetime as _d
    now = _d.datetime.now(); done = []
    for hm, tag in JOBS:
        key = f"{now:%F} {hm}"
        if now.weekday() < 5 and now.strftime("%H:%M") >= hm and last.get("job:" + key) is None:
            last["job:" + key] = time.time()
            for t in ("warm_muse.py", "warm_feeds.py"):
                subprocess.Popen(["nice", "-n", "10", sys.executable, f"{ROOT}/tools/{t}"], stdout=open(f"{ROOT}/state/log/job_{t}.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)
            done.append(key)
    return dict(readback_match=None, jobs=done)

def _bg_funding():
    """shadow funding recorder (feeds no book), run on a daemon thread so the pass loop never waits on the network."""
    import threading
    from mdesk import funding_shadow as F
    threading.Thread(target=lambda: (_safe(F.record, f"{ROOT}/state/funding_shadow/coingecko_binance.jsonl"),
                                      _safe(F.record_coinalyze, f"{ROOT}/state/funding_shadow/coinalyze_binance.jsonl")), daemon=True).start(); return {}

def _safe(fn, *a):
    try: fn(*a)
    except Exception as e: open(f"{ROOT}/state/log/funding_shadow.err", "a").write(f"{time.strftime('%F %T %Z')} {type(e).__name__}: {str(e)[:120]}\n")

class PassTimeout(Exception): pass
PASS_DEADLINE_S = 600   # stuck-desk fix 2026-10-28 (Trader t220u): a pass (cache read, warm, network) that hangs is aborted and the loop moves on (a pass is normally < 90 s)
SIDE_DEADLINE_S = 240   # each side job (publish / backups / warm kick-off)
def guard(seconds, fn, *a):
    """run fn under a SIGALRM wall-clock deadline (main thread; interrupts blocking syscalls such as a stuck read or socket wait)."""
    def _h(*_): raise PassTimeout(f"deadline {seconds}s exceeded")
    old = signal.signal(signal.SIGALRM, _h); signal.alarm(int(seconds))
    try: return fn(*a)
    finally: signal.alarm(0); signal.signal(signal.SIGALRM, old)

def build(a):
    native, m, _ = registry.load_all()
    mc = None if a.no_muse else muse.MemoCache(f"{ROOT}/state/muse_cache")
    return D.Desk(native, ledger_path=a.ledger, muse=[] if a.no_muse else [s for s in m if s.status == "installed"], muse_cache=mc,
                  snapshot=a.snapshot, force_open=a.force_open, use_bs=False)  # Best Setups disconnected (t202u)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--force-open", action="store_true"); ap.add_argument("--no-muse", action="store_true")
    ap.add_argument("--no-bs", action="store_true"); ap.add_argument("--ledger", default=f"{ROOT}/state/ledger.sqlite"); ap.add_argument("--snapshot", default=f"{ROOT}/terminal/state.json")
    ap.add_argument("--interval", type=int, default=300); a = ap.parse_args()
    if a.cmd == "catalog": print(json.dumps(registry.catalog()["summary"], indent=1)); return
    if a.cmd == "pass": d = build(a); print(json.dumps(d.run_pass(), default=str)); return
    if a.cmd == "loop":
        lk = open(f"{ROOT}/state/loop.lock", "w")
        try: fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError: print("md2 loop already running"); return
        d = build(a); stop = []; last = {}
        signal.signal(signal.SIGTERM, lambda *_: stop.append(1))
        while not stop:
            t = time.time()
            try:
                m = guard(PASS_DEADLINE_S, d.run_pass); line = dict(at=time.strftime("%F %T %Z"), **{k: m[k] for k in ("pass_wall_s", "pass_cpu_s", "ledger_writes", "exits", "entries", "muse_intents")})
            except Exception as e: line = dict(at=time.strftime("%F %T %Z"), error=f"{type(e).__name__}: {e}"[:300])   # alert only; loop never halts
            for name, every, fn in (("publish", 0, lambda: __import__("mdesk.publish").publish.push(a.snapshot)), ("store_backup", 0, lambda: _bk().to_store(a.ledger)),
                                    ("github_backup", 3600, lambda: _bk().to_github(a.ledger)), ("funding_shadow", 300, lambda: _bg_funding()), ("feed_warm", 0, lambda: _jobs(last))):
                if time.time() - last.get(name, 0) < every: continue
                try:
                    r = guard(SIDE_DEADLINE_S, fn) or {}; last[name] = time.time()   # (bug fixed: the call used to sit in an unevaluated conditional branch)
                    line[name] = r.get("readback_match") if name == "publish" else (r.get("remote_matches", True) and "ok")
                except Exception as e: line[name] = f"ALERT {type(e).__name__}"   # alert only, never halts
            open(f"{ROOT}/state/heartbeat", "w").write(str(time.time())); print(json.dumps(line), flush=True)
            iv = max(5, a.interval); end = (time.time() // iv + 1) * iv + PHASE_S   # E12: wall-clock aligned (:00:20, :05:20, ...) - the pass lands
            # PHASE_S after each 5-min bar close (signal->order latency <= ~PHASE_S + pass, was up to 300 s + drift) and a pass always
            # falls inside the 15:55-16:00 flatten window (E10); a late wake runs the next pass immediately at the next boundary.
            while not stop and time.time() < end: time.sleep(1)   # SIGTERM is honoured within 1 s
        return
    if a.cmd == "status": print(open(a.snapshot).read()[:3000]); return

if __name__ == "__main__": main()
