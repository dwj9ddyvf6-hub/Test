"""The leader-1d event (R6 / T9 / R7): score >= 3 of 5 AND gate (buy-green or buy-cyan proxy) on a closed
daily bar, computed by the old desk's own research module — vendored byte-identical
(desk/vendor/old_desk_research/leader1d_long_fulluniverse_2026-10-02.py) and loaded the way the old sleeves
loaded it (importlib from its file). The genome job computes the latest-bar row for every name after the
close and writes cache/leader_events.json; the leader sleeves read it for their session only."""
import importlib.util
import os
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "old_desk_research",
                    "leader1d_long_fulluniverse_2026-10-02.py")
MIN_BARS = 252
_L1 = None


def l1():
    global _L1
    if _L1 is None:
        spec = importlib.util.spec_from_file_location("leader1d_long_fulluniverse", PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _L1 = mod
    return _L1


def bar_date(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat()


def rows(bars):
    """the old cache rows [date, o, h, l, c, v]."""
    return [[bar_date(b), float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0)]
            for b in bars or ()]


def latest(bars, min_bars=MIN_BARS):
    """(date, score, gate) of the last bar, or None (old latest_event_date's frame read)."""
    bl = rows(bars)
    if len(bl) < min_bars:
        return None
    try:
        df = l1().frame(bl)
    except Exception:
        return None
    if df is None or len(df) < 3:
        return None
    r = df.iloc[-1]
    try:
        return [bl[-1][0], int(r["score"]), bool(r["gate"])]
    except Exception:
        return None


def is_event(row):
    return bool(row and int(row[1]) >= 3 and bool(row[2]))


def run(hub, symbols, path, now, n=600, chunk=200):
    out = {}
    for i in range(0, len(symbols), chunk):
        got = hub.bars("equity_split", "1d", symbols[i:i + chunk], n, cache_only=True)
        for s, bl in got.items():
            r = latest(bl)
            if r:
                out[s] = r
    dates = sorted({r[0] for r in out.values()})
    doc = {"at": now, "date": dates[-1] if dates else None, "rows": out}
    write_json_atomic(path, doc)
    return doc


def load(path, session):
    """the rows computed on `session`'s close (None until the genome job has written them)."""
    doc = read_json(path, {}) or {}
    return doc.get("rows") if doc.get("date") == session else None


def load_last_close(path, now):
    """the rows computed on the last COMPLETED session's close (during a session: the previous one)."""
    from .. import calendar as cal
    d = cal._as_date(now)
    last = d if (cal.is_trading_day(d) and now >= cal.session_close(d)) else cal.prev_trading_day(d)
    doc = read_json(path, {}) or {}
    return doc.get("rows") if doc.get("date") == last.isoformat() else None
