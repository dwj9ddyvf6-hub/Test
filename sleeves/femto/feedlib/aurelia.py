"""The Aurelia signal (aurelia-gc-band20-v1), computed as the source desk computed it.

Source: Agentic-Trading-Desk aurelia-paper-desk @1720157f768e — desk/paper.py _aurelia (the traded exposures and
the record-only APEX read), desk/brain/perceive.py tape (the posture's inputs). The math is the source's own text
(desk/vendor/aurelia/features.py whole; desk/vendor/aurelia/prism.py verbatim excerpts); this module supplies its
data: the daily frames the source's yahoo.get_daily returned — the same chart call (period1 1900-01-01, events
div,split, adjusted closes) and the same parse (bar time + the exchange gmtoffset, normalized to a date;
duplicated dates keep the last; rows without a positive close dropped), cached per symbol and refetched once a
newer completed session can exist (a failed fetch serves the cache, as the source's get_daily did).

exposures(frames, through): the Nasdaq-100 total return (QQQ adjusted closes spliced onto ^NDX before 1999-03-10)
sliced to the last finished session, gold front-month futures (GC=F closes) aligned to it, PRISM trend x
volatility targets on that session: ndx = min(NDX, 3), gold = GOLD. Recorded with it: the APEX read (trend score,
HAR vol, apex_3x = trend x min(3, 0.50 / vol)) and the tape on that session (the ^VIX close, the ^NDX day).

feed(): {"signal_id", "as_of", "through", "aurelia_ndx", "aurelia_gold", "apex_3x", "trend", "vol", "vix",
"ndx_day", "requirements" (initial margin fractions: Reg T, or Alpaca's maintenance rate when higher), "status"}
or {"error": ...} (the sleeve fails closed)."""
import json
import math
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..util import write_json_atomic

SIGNAL_ID = "aurelia-gc-band20-v1"
SYMBOLS = ("^NDX", "QQQ", "GC=F", "^VIX")
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
EARLIEST = -2_208_988_800
HEADERS = {"User-Agent": "Mozilla/5.0"}
RETRY_S = 900
FALLBACK_REQ = {"QQQ": 0.50, "TQQQ": 0.75, "GLD": 0.50, "BIL": 0.50}
_LOCK = threading.Lock()
_REQ = {}


def _fetch(symbol, now):
    from ..data.http import get
    return get(URL.format(symbol=symbol), {"period1": EARLIEST, "period2": int(now) + 86_400, "interval": "1d",
                                           "events": "div,split", "includeAdjustedClose": "true"}, headers=HEADERS)


def parse(payload, symbol):
    """the source's _download parse -> {"dates": [...], "open", "high", "low", "close", "volume", "adj_close"}
    (columns as lists; NaN as None)."""
    import numpy as np
    import pandas as pd
    payload = (payload or {}).get("chart") or {}
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    res = (payload.get("result") or [None])[0]
    if not res:
        raise RuntimeError(f"Yahoo returned no result for {symbol}")
    ts = res.get("timestamp") or []
    if not ts:
        raise RuntimeError(f"Yahoo returned no bars for {symbol}")
    offset = res["meta"].get("gmtoffset", 0)
    idx = pd.to_datetime(np.asarray(ts, dtype="int64") + offset, unit="s").normalize()
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({"open": q.get("open"), "high": q.get("high"), "low": q.get("low"), "close": q.get("close"),
                       "volume": q.get("volume")}, index=idx)
    adj = res["indicators"].get("adjclose")
    df["adj_close"] = adj[0]["adjclose"] if adj else df["close"]
    df.index.name = "date"
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["close"])
    df = df[df["close"] > 0]
    df = df.astype("float64")
    out = {"dates": [d.date().isoformat() for d in df.index]}
    for c in ("open", "high", "low", "close", "volume", "adj_close"):
        out[c] = [None if (v != v) else float(v) for v in df[c].tolist()]
    return out


def frame(rec):
    """a cached record -> the source's daily DataFrame (DatetimeIndex 'date', float64 columns)."""
    import pandas as pd
    idx = pd.DatetimeIndex(pd.to_datetime(rec["dates"]), name="date")
    cols = {c: [float("nan") if v is None else v for v in rec[c]] for c in ("open", "high", "low", "close", "volume",
                                                                         "adj_close")}
    return pd.DataFrame(cols, index=idx).astype("float64")


def last_done_session(now):
    """the newest session whose daily bar is final (15 minutes after its close)."""
    d = cal._as_date(now)
    for _ in range(15):
        if cal.is_trading_day(d) and float(now) >= cal.session_close(d) + 900:
            return d
        d = d - timedelta(days=1)
    return d


def completed_through(now):
    """session.completed_through: the session's date once its close has passed, else the day before."""
    d = cal._as_date(now)
    if cal.is_trading_day(d) and float(now) >= cal.session_close(d):
        return d
    return d - timedelta(days=1)


class History:
    """per-symbol full daily history at <root>/<SYM>.json; refetched when a session finished after the fetch."""

    def __init__(self, root, getter=None):
        self.root, self.getter = root, getter or _fetch
        self.status = {}

    def _path(self, sym):
        return os.path.join(self.root, sym.replace("^", "IDX_").replace("=", "_").replace("/", "_") + ".json")

    def load(self, sym, now):
        p = self._path(sym)
        rec = None
        if os.path.exists(p):
            try:
                rec = json.load(open(p))
            except (OSError, ValueError):
                rec = None
        due = cal.session_close(last_done_session(now)) + 900
        fresh = rec is not None and float(rec.get("fetched_at") or 0) >= due
        tried = rec is not None and float(now) - float(rec.get("tried_at") or 0) < RETRY_S
        if fresh or (tried and rec.get("dates")):
            self.status[sym] = "cache"
            return rec if rec.get("dates") else None
        try:
            got = parse(self.getter(sym, now), sym)
            got.update(fetched_at=float(now), tried_at=float(now), symbol=sym)
            os.makedirs(self.root, exist_ok=True)
            write_json_atomic(p, got)
            self.status[sym] = "fetch"
            return got
        except Exception as e:
            self.status[sym] = "stale_cache: %s" % str(e)[:120] if rec and rec.get("dates") else "error: %s" % str(e)[:120]
            if rec is not None:
                rec["tried_at"] = float(now)
                try:
                    write_json_atomic(p, rec)
                except OSError:
                    pass
            return rec if rec and rec.get("dates") else None


class _Yahoo:
    """the `yahoo` module the source excerpts call: get_daily(symbol) -> that symbol's cached frame."""

    def __init__(self, frames):
        self.frames = frames

    def get_daily(self, symbol, refresh=False, **_kw):
        if symbol not in self.frames:
            raise RuntimeError(f"no daily history for {symbol}")
        return self.frames[symbol]


def exposures(frames, through):
    """paper._aurelia(through) on these frames (+ the tape the posture reads)."""
    import numpy as np
    import pandas as pd
    from ..vendor.aurelia import features as F
    from ..vendor.aurelia import prism as P
    with _LOCK:
        P.yahoo = _Yahoo(frames)
        try:
            cut = pd.Timestamp(through)
            r = P.ndx_total_return()
            r = r[r.index.normalize() <= cut]
            if r.empty:
                raise RuntimeError(f"No finished session on or before {through}")
            level = (1.0 + r).cumprod()
            trend = F.trend_score(level)
            vol = F.har_vol_forecast(r)
            apex = (trend * np.minimum(3.0, (0.50 / vol) ** 1.0)).iloc[-1]
            gc = P.aligned_returns("GC=F", r.index, field="close")
            targets, _ = P.prism_targets({"NDX": r, "GOLD": gc}, r.index)
        finally:
            P.yahoo = None
    row = targets.dropna(how="all").iloc[-1]
    ndx = min(float(row["NDX"]), 3.0)
    gold = float(row["GOLD"])
    if not math.isfinite(ndx) or not math.isfinite(gold):
        raise RuntimeError(f"Aurelia signal is not finite (ndx={ndx}, gold={gold})")

    def last2(sym):
        c = frames[sym]["close"].dropna()
        c = c[c.index.normalize() <= cut]
        return (float(c.iloc[-1]) if len(c) else None), (float(c.iloc[-2]) if len(c) > 1 else None)

    vix = last2("^VIX")[0] if "^VIX" in frames else None
    n1, n0 = last2("^NDX")
    return {"signal_id": SIGNAL_ID, "as_of": str(r.index[-1].date()), "data_through": str(through),
            "aurelia_ndx": ndx, "aurelia_gold": gold, "apex_3x": float(apex) if math.isfinite(apex) else None,
            "trend": float(trend.iloc[-1]), "vol": float(vol.iloc[-1]), "vix": vix,
            "ndx_day": (n1 / n0 - 1.0) if (n1 and n0) else None}


def requirements(hub, day):
    """initial margin fraction per name: at least Reg T and at least Alpaca's maintenance rate (paper.py
    _margin_requirements; a lookup miss keeps the stricter fallback). Read once per day."""
    if _REQ.get("day") == day:
        return dict(_REQ["req"])
    out = dict(FALLBACK_REQ)
    client = getattr(getattr(hub, "alpaca", None), "c", None)
    for sym in FALLBACK_REQ:
        try:
            info = client.asset(sym) if client is not None else None
            maint = float((info or {}).get("maintenance_margin_requirement") or 0.0) / 100.0
        except Exception:
            continue
        out[sym] = max(FALLBACK_REQ[sym], maint, 0.50)
    _REQ.update(day=day, req=dict(out))
    return out


def feed(feeds, sleeve, now, arg=None):
    root = os.path.join(os.path.dirname(feeds.hub.cache.root), "aurelia")
    hist = History(root)
    recs = {s: hist.load(s, now) for s in SYMBOLS}
    missing = [s for s in ("^NDX", "QQQ", "GC=F") if not recs.get(s)]
    if missing:
        return {"error": "no daily history for %s" % ", ".join(missing), "status": dict(hist.status)}
    through = completed_through(now)
    key = "%s|%s|%s" % (SIGNAL_ID, through.isoformat(), "|".join("%s:%s" % (s, (recs[s] or {}).get("dates", [""])[-1])
                                                                 for s in SYMBOLS if recs.get(s)))
    cpath = os.path.join(root, "exposure_cache.json")
    exp = None
    try:
        c = json.load(open(cpath))
        if c.get("key") == key:
            exp = c.get("exp")
    except (OSError, ValueError):
        pass
    if exp is None:
        try:
            frames = {s: frame(recs[s]) for s in SYMBOLS if recs.get(s)}
            exp = exposures(frames, through)
        except Exception as e:
            return {"error": "%s: %s" % (type(e).__name__, str(e)[:200]), "status": dict(hist.status)}
        write_json_atomic(cpath, {"key": key, "exp": exp, "computed_at": float(now)})
    out = dict(exp)
    out["status"] = dict(hist.status)
    out["requirements"] = requirements(feeds.hub, cal._as_date(now).isoformat())
    return out
