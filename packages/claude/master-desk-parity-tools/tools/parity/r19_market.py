"""A deterministic synthetic US-equity market behind a fake Alpaca client — the four GET endpoints the R19 collector
reads (paper /v2/assets, data /v2/stocks/bars daily SIP + intraday IEX, /v1/corporate-actions,
/v2/stocks/quotes/latest), on the XNYS sessions of desk.feedlib.r19_source.DeskXNYS. Ten-minute regular-session
bars are the base series (an intraday drift / mean-reversion walk with planted afternoon runs and hourly trends);
30-minute and daily bars aggregate them exactly; older daily history is a plain walk ending at the first intraday
session's open. Quotes are the last completed ten-minute close +- half a cent-grid spread, stamped one second
before the clock. Used by the r19_timing parity harness and engine tests (both sides read the same client)."""
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta, timezone

from desk.feedlib.r19_source import DeskXNYS, is_session

UTC = timezone.utc
CAL = DeskXNYS()


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def sessions_between(a, b):
    d, out = a, []
    while d <= b:
        if is_session(d):
            out.append(d)
        d += timedelta(days=1)
    return out


class Market:
    def __init__(self, seed, symbols, intraday_from, intraday_to, clock):
        self.seed, self.symbols, self.clock = seed, list(symbols), clock
        self.intraday = sessions_between(intraday_from, intraday_to)
        self.first = self.intraday[0]
        self._ten, self._day = {}, {}
        rnd = random.Random(seed)
        self.base = {s: round(rnd.uniform(8, 120), 2) for s in self.symbols}
        self.vol = {s: rnd.uniform(0.0015, 0.004) for s in self.symbols}
        self.quote_size = {s: rnd.choice((100, 300, 800, 2000, 5000)) for s in self.symbols}
        self.ids = {s: hashlib.sha1(f"asset:{s}".encode()).hexdigest()[:8] + "-0000-4000-8000-" +
                    hashlib.sha1(f"id:{s}".encode()).hexdigest()[:12] for s in self.symbols}

    # -- series ------------------------------------------------------------------------------------------
    def _rnd(self, *k):
        return random.Random(hashlib.sha256(json.dumps([self.seed, *k]).encode()).hexdigest())

    def ten(self, sym, d):
        """ten-minute bars of session d (list of dicts t/o/h/l/c/v), deterministic, chained by close."""
        key = (sym, d)
        if key in self._ten:
            return self._ten[key]
        i = self.intraday.index(d)
        prev = self.ten(sym, self.intraday[i - 1])[-1]["c"] if i else self.base[sym]
        rnd = self._rnd("ten", sym, d.isoformat())
        opened, closed = CAL.session_open(d).timestamp(), CAL.session_close(d).timestamp()
        n = int((closed - opened) // 600)
        px = round(prev * (1 + rnd.gauss(0, 0.006)), 2)
        trend = rnd.choice((-1, 0, 0, 1, 1)) * self.vol[sym] * 0.35
        run = rnd.random() < 0.25                         # an afternoon run (13:00-15:00 strength)
        out = []
        for k in range(n):
            t = opened + 600 * k
            drift = trend + (self.vol[sym] * 0.9 if run and 21 <= k < 33 else 0.0)
            o = px
            c = max(0.5, round(o * (1 + drift + rnd.gauss(0, self.vol[sym])), 2))
            h = round(max(o, c) * (1 + abs(rnd.gauss(0, self.vol[sym] / 2))), 2)
            l = round(min(o, c) * (1 - abs(rnd.gauss(0, self.vol[sym] / 2))), 2)
            out.append({"t": t, "o": o, "h": max(h, o, c), "l": min(l, o, c), "c": c,
                        "v": float(int(rnd.uniform(2e3, 4e4)))})
            px = c
        self._ten[key] = out
        return out

    def agg(self, bars, minutes, opened):
        out = {}
        for b in bars:
            k = opened + ((b["t"] - opened) // (minutes * 60)) * minutes * 60
            a = out.get(k)
            if a is None:
                out[k] = dict(b, t=k)
            else:
                a.update(h=max(a["h"], b["h"]), l=min(a["l"], b["l"]), c=b["c"], v=a["v"] + b["v"])
        return [out[k] for k in sorted(out)]

    def daily(self, sym, d):
        if d >= self.first:
            if d not in self.intraday:
                return None
            tb = self.ten(sym, d)
            return {"t": _midnight(d), "o": tb[0]["o"],
                    "h": max(b["h"] for b in tb), "l": min(b["l"] for b in tb), "c": tb[-1]["c"],
                    "v": sum(b["v"] for b in tb)}
        key = (sym, "old")
        if key not in self._day:
            rnd = self._rnd("daily", sym)
            days = sessions_between(self.first - timedelta(days=2600), self.first - timedelta(days=1))
            px, rows = self.ten(sym, self.first)[0]["o"], {}
            for dd in reversed(days):                      # walk backwards from the first intraday open
                c = px
                o = max(0.5, round(c / (1 + rnd.gauss(0, 0.02)), 2))
                rows[dd] = {"t": _midnight(dd), "o": o,
                            "h": round(max(o, c) * 1.01, 2), "l": round(min(o, c) * 0.99, 2), "c": c,
                            "v": float(int(rnd.uniform(3e5, 5e6)))}
                px = o
            self._day[key] = rows
        return self._day[key].get(d)

    # -- the fake client -----------------------------------------------------------------------------------
    def client(self):
        return FakeAlpaca(self)


class FakeAlpaca:
    host = "https://paper-api.alpaca.markets"

    def __init__(self, market):
        self.m = market
        self.calls = []

    def _get(self, path, params=None, host=None):
        p = dict(params or {})
        self.calls.append(path)
        if path == "/v2/assets":
            if p.get("status") == "inactive":
                return []
            return [{"id": self.m.ids[s], "class": "us_equity", "exchange": "NASDAQ", "symbol": s, "name": s,
                     "status": "active", "tradable": True, "marginable": True, "shortable": True,
                     "easy_to_borrow": True, "fractionable": True} for s in self.m.symbols]
        if path == "/v1/corporate-actions":
            return {"corporate_actions": {}, "next_page_token": None}
        if path == "/v2/stocks/quotes/latest":
            now = self.m.clock()
            out = {}
            for s in p["symbols"].split(","):
                if s not in self.m.ids:
                    continue
                last = self._last_close(s, now)
                if last is None:
                    continue
                sz = self.m.quote_size[s]
                out[s] = {"bp": round(last - 0.01, 2), "ap": round(last + 0.01, 2), "bs": sz, "as": sz,
                          "t": _iso(now - 1), "bx": "V", "ax": "V", "c": ["R"], "z": "C"}
            return {"quotes": out}
        if path == "/v2/stocks/bars":
            return self._bars(p)
        raise AssertionError(path)

    def _last_close(self, s, now):
        for d in reversed(self.m.intraday):
            if CAL.session_open(d).timestamp() > now:
                continue
            done = [b for b in self.m.ten(s, d) if b["t"] + 600 <= now]
            if done:
                return done[-1]["c"]
        if hasattr(self.m, "last_daily_close"):              # a daily-tape market: the last completed close
            return self.m.last_daily_close(s, now)
        return None

    def _bars(self, p):
        syms = [s for s in p["symbols"].split(",") if s in self.m.ids]
        start, end = _parse(p["start"]), _parse(p["end"])
        tf = p["timeframe"]
        now = self.m.clock()
        out = {}
        for s in syms:
            rows = []
            if tf == "1Day":
                d0 = datetime.fromtimestamp(start, tz=UTC).date()
                d1 = datetime.fromtimestamp(min(end, now), tz=UTC).date()
                for d in sessions_between(d0 - timedelta(days=1), d1):
                    b = self.m.daily(s, d)
                    if b and start <= b["t"] < end and CAL.session_close(d).timestamp() <= now:
                        rows.append(b)
            else:
                minutes = {"30Min": 30, "10Min": 10}[tf]
                for d in self.m.intraday:
                    opened = CAL.session_open(d).timestamp()
                    if opened > min(end, now) or CAL.session_close(d).timestamp() < start:
                        continue
                    for b in self.m.agg(self.m.ten(s, d), minutes, opened) if minutes == 30 else self.m.ten(s, d):
                        if start <= b["t"] < end and b["t"] <= now:      # the forming bar is served too
                            rows.append(b)
            if rows:
                out[s] = [{"t": _iso(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"],
                           "n": 100, "vw": round((b["h"] + b["l"] + b["c"]) / 3, 4)} for b in rows]
        return {"bars": out, "next_page_token": None}


TAPE_START, TAPE_SPAN_END = date(2021, 6, 1), date(2026, 10, 9)


def tensor_tape(seed, end):
    """a deterministic daily tape on the XNYS sessions from 2021-06-01: a steady stretch, a 120-220 session
    crash in the last 300-420 sessions before 2026-10-09, a volatile base after it, then a mild walk to `end`.
    Seeds 172 and 24 carry a Author v615 buy-green G4 qualifier on the week ending 2026-10-02 as
    qualify_snapshot builds it on 2026-10-05 (the last 1,100 sessions)."""
    import math
    span = sessions_between(TAPE_START, TAPE_SPAN_END)
    rnd = random.Random(seed)
    px = rnd.uniform(15, 60)
    n = len(span)
    crash_a = rnd.randint(n - 420, n - 300)
    crash_b = crash_a + rnd.randint(120, 220)
    rows = {}
    for i, d in enumerate(span):
        drift = 0.0005
        if crash_a <= i < crash_b:
            drift = -rnd.uniform(0.004, 0.012)
        elif i >= crash_b:
            drift = rnd.choice((0.0, 0.002, 0.004, -0.002))
        vol = 0.045 if i >= crash_a else 0.025
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.3, px * math.exp(drift + rnd.gauss(0, vol)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = float(int(rnd.uniform(1.5e6, 6e6) * (2 if i >= crash_a else 1)))
        rows[d] = {"o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4), "v": v}
        px = c
    more = random.Random(seed + 10 ** 6)
    for d in sessions_between(TAPE_SPAN_END + timedelta(days=1), end):
        o = px * (1 + more.gauss(0, 0.01))
        c = max(0.3, px * math.exp(more.gauss(0.0003, 0.03)))
        h, l = max(o, c) * (1 + abs(more.gauss(0, 0.01))), min(o, c) * (1 - abs(more.gauss(0, 0.01)))
        rows[d] = {"o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4),
                   "v": float(int(more.uniform(1.5e6, 6e6)))}
        px = c
    return rows


class TapeMarket:
    """explicit daily tapes ({symbol: {session date: o/h/l/c/v}}) behind the same fake client: daily SIP bars,
    the asset census of these symbols, quotes at the last completed session close +- 1 cent (stamped one
    second before the clock), no intraday bars."""

    def __init__(self, tapes, clock, quote_size=5000):
        self.tapes, self.clock = tapes, clock
        self.symbols = sorted(tapes)
        self.intraday = []
        self.quote_size = {s: quote_size for s in self.symbols}
        self.ids = {s: hashlib.sha1(f"asset:{s}".encode()).hexdigest()[:8] + "-0000-4000-8000-" +
                    hashlib.sha1(f"id:{s}".encode()).hexdigest()[:12] for s in self.symbols}

    def ten(self, sym, d):
        return []

    def daily(self, sym, d):
        b = self.tapes[sym].get(d)
        return dict(b, t=_midnight(d)) if b else None

    def last_daily_close(self, sym, now):
        best = None
        for d, b in self.tapes[sym].items():
            if CAL.session_close(d).timestamp() <= now and (best is None or d > best[0]):
                best = (d, b["c"])
        return best[1] if best else None

    def client(self):
        return FakeAlpaca(self)


def _midnight(d):
    """Alpaca stamps a daily bar at 00:00 America/New_York of its session."""
    from desk.util import ET
    return datetime(d.year, d.month, d.day, tzinfo=ET).timestamp()
