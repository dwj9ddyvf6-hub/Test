"""Qullamaggie proposal scan runner (HARDEN-B4).

The Qullamaggie reconstruction engine is an upstream core product
(sleeves/qullamaggie_paper.py: "The engine stays a core Data/research
product upstream; its accepted proposals arrive as proposals") — the
same posture as Best Setups generation (desk3/setups_generate.py runs
the original tree's generator read-only, output into v3 state).

This runner executes muse-desk-v2's runtime/qulla_warm.run()
READ-ONLY (PYTHONDONTWRITEBYTECODE=1, the v2 tree is never written)
with root=<this desk>, so the engine's proposals land in this desk's
cache layout (cache/qulla/proposals.json, cache/bars/...), where
desk3.producers_g4.QullaFileProducer serves them for the persisted
session only. The v2 warmer fetches any missing daily/1min bars
through v2's Alpaca door using this desk's paper credential route.

Run: python3 -m desk3.qulla_scan [YYYY-MM-DD]
Exit 0 + a {"session", "proposals"} summary on success; nonzero with
the failure named on stderr otherwise (no file is refreshed on
failure, so a stale session simply stays UNFED).
"""
from __future__ import annotations
import json, os, subprocess, sys

V2_ROOT = os.path.expanduser("~/workspace/muse-desk-v2")

_SNIPPET = """
import json, os, sys
root, session = sys.argv[1], (sys.argv[2] or None)
sys.path.insert(0, os.getcwd())
# CURE2-QULLA-WARM-TIMEOUT-20261102: LEAN warm. qulla_warm.run with
# its warm flag on delegates to runtime.cache_warm.warm(), whose
# defaults run the ENTIRE desk warm (the 40-symbol bb_rsi 1Hour
# expansion plus quotes, the options chain warm, kraken, earnings,
# account read-back) once per timeframe; that is what burned the
# 1800s scan timeout in cure round 1. Measured cure: fetching
# exactly the missing (symbol, timeframe) pairs below takes 45s
# and the produce step 9s. The engine and its cache contract are
# untouched; only the fetch loses sections that were never this
# producer's to run. The v2 tree is still never written (the
# cache written here is this desk's, the designed output).
from datetime import datetime
from zoneinfo import ZoneInfo
from runtime.alpaca_door import AlpacaDoor
from runtime.cache import BarCache
from runtime.qulla_warm import SYMBOLS, _epoch, _has_session, run
_ET = ZoneInfo("America/New_York")

def _has_rth_1min(cache, sym, session):
    # QULLA-RTH-GATE-20261111: _has_session's 1Min test is the
    # bar's UTC date, which the prior evening's after-hours bars
    # (19:00-19:59 ET = 00:00-00:59Z) satisfy for the NEXT
    # session, so the session's real 1Min fetch was skipped on
    # every attempt after the first pre-market one and the
    # engine's intraday frame — RTH window in ET only
    # (core.qulla_feeds.intraday_frame) — stayed empty: every
    # scan failed "qulla frames incomplete" (live artifact
    # 2026-11-11: intraday_rows 0 with 11k cached 1Min rows).
    # Gate the 1Min fetch on the engine's own presence rule.
    for b in cache.read_bars(sym, "1Min", 0):
        et = datetime.fromtimestamp(_epoch(b.t), tz=_ET)
        if et.date().isoformat() != session:
            continue
        if 570 <= et.hour * 60 + et.minute <= 959:
            return True
    return False

cache = BarCache(os.path.join(os.path.abspath(root), "cache"))
door = AlpacaDoor()
for tf, limit in (("1Day", 500), ("1Min", 3000)):
    for sym in SYMBOLS:
        if tf == "1Min":
            missing = not _has_rth_1min(cache, sym, session)
        else:
            missing = not _has_session(cache, sym, tf, session)
        if missing:
            cache.write_bars(sym, tf, door.get_bars(
                sym, timeframe=tf, limit=limit, feed="sip"))
payload = run(root, session=session, warm_first=False)
print(json.dumps({"session": payload["session"],
                  "proposals": payload["proposals"],
                  "evidence": payload.get("evidence")}))
"""


SCAN_EARLIEST_ET = (9, 47)


def scan_deferred(session, now_et):
    """QULLA-PREOPEN-DEFERRAL-20261113: True when a scan for
    `session` cannot succeed yet because the engine's intraday
    frame cannot exist. The engine (core.qulla_feeds.intraday_frame)
    builds its intraday frame ONLY from `session`'s own RTH 1Min
    bars (09:30-16:00 ET); the first RTH bar completes at 09:31 ET
    and the door's SIP bars carry a measured 15-minute serve lag
    (2026-11-13: fetched at 14:39:29Z, newest bar served was
    14:24:00Z), so no RTH bar for the session is servable before
    ~09:46 ET. Before 09:47 ET on the session's own trading day
    that frame is necessarily empty and every scan writes an
    errored proposals
    file ("RuntimeError: qulla frames incomplete", intraday_rows
    0) which QullaFileProducer then fail-closes on for the whole
    retry window. That is the clear-then-recur pattern: the prior
    session's scan goes clean once its RTH bars exist (the Thu
    night final roll), the session date rolls at midnight, and
    the first pre-open launch of the new session re-poisons the
    file (live artifact 2026-11-13: file written 14:00:02Z =
    09:00 ET, 30 minutes before the open, daily_rows 10794,
    intraday_rows 0). Deferral applies only when the session IS
    today ET and today is a trading day: a rolled-back session
    (weekend/holiday) names a completed session whose RTH bars
    all exist, and scans for it are never deferred."""
    if session != now_et.date().isoformat():
        return False
    from core.data import is_trading_day
    if not is_trading_day(now_et.date()):
        return False
    return (now_et.hour, now_et.minute) < SCAN_EARLIEST_ET


def default_session():
    """The session the producer serves: today's ET date on a
    trading day, else the most recent trading day. The session
    names the DECISION date (desk3.producers_g4.QullaFileProducer
    serves the file only when session == today ET); the engine's
    features are fenced to completed sessions before it, so a
    pre-open scan for today is the designed shape."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from core.data import is_trading_day
    d = datetime.now(ZoneInfo("America/New_York")).date()
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d.isoformat()


def run_scan(root, session=None, timeout_s=1800, now_et=None):
    session = session or default_session()
    from datetime import datetime
    from zoneinfo import ZoneInfo
    if now_et is None:
        now_et = datetime.now(ZoneInfo("America/New_York"))
    # QULLA-PREOPEN-DEFERRAL-20261113: refuse before the engine is
    # invoked, so no caller (warmer, cron, operator) can write an
    # errored proposals file for a session whose intraday frame
    # cannot exist yet. See scan_deferred.
    if scan_deferred(session, now_et):
        raise RuntimeError(
            f"qulla scan deferred: session {session} intraday frame "
            f"cannot exist before 09:47 ET (first completed RTH "
            f"1Min bar plus the door's 15-minute SIP serve lag); "
            f"refusing to run the engine pre-open")
    if not os.path.isdir(V2_ROOT):
        raise RuntimeError(f"v2 engine tree absent: {V2_ROOT}")
    today = now_et.date().isoformat()
    if session > today:
        raise RuntimeError(
            f"session {session} is in the future (today ET is "
            f"{today}); no bars can exist for it, refusing to warm")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [sys.executable, "-c", _SNIPPET, os.path.abspath(root), session or ""],
        cwd=V2_ROOT, env=env, capture_output=True, text=True,
        timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(
            f"qulla engine run failed rc={proc.returncode}: "
            f"{(proc.stderr or '').strip()[-500:]}")
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return json.loads(lines[-1])


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session = argv[0] if argv else None
    try:
        out = run_scan(root, session=session)
    except Exception as e:
        print(f"qulla scan FAILED: {type(e).__name__}:{e}", file=sys.stderr)
        return 1
    print(json.dumps({"session": out["session"],
                      "n_proposals": len(out["proposals"]),
                      "proposals": out["proposals"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
