"""Desk fear composite — the old desk's desk/sentiment.py (User 2026-10-10), ported verbatim in its arithmetic.

0 = extreme greed, 100 = extreme fear; the average of whichever components are available:
  vix_pct       percentile of the latest ^VIX close vs the prior year's closes
  spy_drawdown  SPY distance below its 50-day MA: -10% -> 100
  vrp           VIX minus SPY 20-day realized vol (annualised %): +20 -> 100
Series: Yahoo daily chart range=1y (the last point is today's in-progress bar during the session, as the old
_yahoo_daily read it). Snapshot per ET day; an unavailable build is retried after 45 minutes.
fear_gate_ok: score >= 55 (FEAR+); unavailable -> True (fail-open: an overlay, not a safety gate)."""
import math
from datetime import datetime, timezone

from ..data.http import get
from ..util import ET

FEAR_GATE_MIN = 55.0


def _yahoo_daily(symbol, rng="1y"):
    try:
        d = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", {"interval": "1d", "range": rng})
        r = d["chart"]["result"][0]
        closes = r["indicators"]["quote"][0]["close"]
        pts = [(datetime.fromtimestamp(t, tz=timezone.utc).astimezone(ET).date().isoformat(), c)
               for t, c in zip(r["timestamp"], closes) if c]
        pts.sort()
        return pts or None
    except Exception:
        return None


def _percentile(val, hist):
    return sum(1 for h in hist if h <= val) / len(hist) * 100.0 if hist else None


def _sma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None


def _realized_vol_20(closes):
    if len(closes) < 22:
        return None
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(-21, 0) if closes[i - 1] > 0]
    if len(rets) < 20:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252) * 100.0


def label_for(score):
    if score is None:
        return "UNKNOWN"
    return ("EXTREME_FEAR" if score >= 75 else "FEAR" if score >= 55 else "NEUTRAL" if score >= 45
            else "GREED" if score >= 25 else "EXTREME_GREED")


def build_snapshot(now, vix_pts=None, spy_pts=None):
    comps = {}
    vix_pts = vix_pts if vix_pts is not None else _yahoo_daily("%5EVIX")
    spy_pts = spy_pts if spy_pts is not None else _yahoo_daily("SPY")
    if vix_pts and len(vix_pts) >= 60:
        pct = _percentile(vix_pts[-1][1], [c for _, c in vix_pts[:-1]])
        if pct is not None:
            comps["vix_pct"] = round(pct, 1)
    if spy_pts and len(spy_pts) >= 60:
        sc = [c for _, c in spy_pts]
        ma50 = _sma(sc, 50)
        if ma50:
            dd = (sc[-1] / ma50 - 1) * 100.0
            comps["spy_drawdown"] = round(max(0.0, min(100.0, -dd * 10.0)), 1)
        rv20 = _realized_vol_20(sc)
        if rv20 is not None and vix_pts:
            comps["vrp"] = round(max(0.0, min(100.0, (vix_pts[-1][1] - rv20 + 5.0) * 4.0)), 1)
    vals = list(comps.values())
    score = round(sum(vals) / len(vals), 1) if vals else None
    return {"date": datetime.fromtimestamp(now, tz=ET).date().isoformat(), "built_at": now, "score": score,
            "label": label_for(score), "components": comps, "data_status": "ok" if vals else "unavailable"}


class Fear:
    def __init__(self):
        self.snap = None

    def snapshot(self, now):
        today = datetime.fromtimestamp(now, tz=ET).date().isoformat()
        s = self.snap
        if s and s["date"] == today and (s["data_status"] == "ok" or now - s["built_at"] < 2700):
            return s
        self.snap = build_snapshot(now)
        return self.snap

    def gate_ok(self, now):
        s = self.snapshot(now)
        if s.get("score") is None:
            return True                      # fail-open, as the old fear_gate_ok
        return s["score"] >= FEAR_GATE_MIN
