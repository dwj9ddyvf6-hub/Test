"""Blockers ASTER-CURE3 (verifier round 3): per-sleeve fixture census.

Verifier trace over all Aster blocker tests found ENTRY never returned
for 22 sleeves and EXIT never returned for 57 sleeves — the ASTER-B9-2
defect class repeated: representative variants driven, siblings
(B / touch / vol1pct / delay / reserve) config-only or refusal-only.
This file drives entry AND exit per named sleeve, parameterized per
family from the sibling-proven fixtures. The 6 buy-hold sleeves never
exit BY DESIGN (engine freq == BUY_HOLD; batch10/11 test_buy_hold_
never_exits) — they are proven never-exit here and recorded as the
by-design exemption instead of a fabricated exit drive.
Fail direction: pre-cure, this file does not exist (census = the
verifier counts above: entry_missing=22, exit_missing=57).
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")


def K(out):
    ks = []
    for o in out or []:
        k = o["kind"] if isinstance(o, dict) else getattr(o, "kind", None)
        ks.append({"enter": "entry"}.get(k, k))
    return ks


def ev3(sid, view, ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(view, ctx or {})


# ================= batch 2 (pead / core / recovery RSI2 long) =================
EPOCH2 = date(1970, 1, 1); START2 = date(2025, 1, 1)


def bars2(closes, vol=10000):
    return [{"t": float(((START2 + timedelta(days=i)) - EPOCH2).days * 86400),
             "o": c, "h": c * 1.001, "l": c * .999, "c": c, "v": vol}
            for i, c in enumerate(closes)]


def ctx2(sid, session="2025-10-06"):
    return {"sleeve_id": sid, "session": session,
            "now": session + "T09:37:00", "equity": 10000.0}


def rsi2_series2(n=210):
    return [100 + 0.5 * i for i in range(n - 3)] + [200.0, 190.0, 180.0]


def chain2(sym="SPY", spot=180.0, right="call", dte=17, delta=0.55,
           ask=0.4, bid=0.35):
    exp = (date(2025, 10, 6) + timedelta(days=dte)).isoformat()
    strike = spot
    out = [{"symbol": f"{sym}251023C00180000", "underlying": sym,
            "right": right, "expiry": exp, "strike": strike,
            "delta": delta if right == "call" else -delta,
            "bid": bid, "ask": ask, "bid_size": 50, "ask_size": 50}]
    ws = strike + 5 if right == "call" else strike - 5
    out.append({"symbol": f"{sym}WING", "underlying": sym, "right": right,
                "expiry": exp, "strike": ws,
                "delta": 0.3 if right == "call" else -0.3,
                "bid": 0.2, "ask": 0.25, "bid_size": 50, "ask_size": 50})
    return out


def opt_pos2(held=0, structure="long"):
    legs = [{"symbol": "SPY251023C00180000", "underlying": "SPY",
             "right": "call", "expiry": "2025-10-23", "strike": 180.0,
             "ratio": 1}]
    if structure == "vertical":
        legs.append({"symbol": "SPYWING", "underlying": "SPY",
                     "right": "call", "expiry": "2025-10-23",
                     "strike": 185.0, "ratio": -1})
    return [{"symbol": "SPY251023C00180000", "qty": 2, "avg_price": 2.0,
             "entry_spot": 180.0, "sessions_held": held, "legs": legs,
             "opened_at": "2025-10-06"}]


def pead_view2():
    evv = {"symbol": "ACME", "event_id": "E1", "surprise": -0.05,
           "threshold": -0.02, "spot_at_signal": 50.0,
           "mean20_dollar_volume": 5000000, "entry_session": "2025-10-06",
           "event_date": "2025-10-01"}
    return {"bars": {"ACME": bars2([50.0] * 30)},
            "options": chain2("ACME", spot=50.0, right="put", dte=28),
            "positions": [], "earnings_events": [evv]}


def rec_view2():
    return {"bars": {"SPY": bars2(rsi2_series2())}, "options": chain2(),
            "positions": []}


# ================= batch 5 (ADA absorption spot, aster_sleeves) =================
NOW5 = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)


def _iso5(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _mk4_5(specs):
    n = len(specs)
    return [{"t": _iso5(NOW5 - timedelta(hours=4 * (n - i))),
             "o": o, "h": h, "l": l, "c": c, "v": v}
            for i, (o, c, v, h, l) in enumerate(specs)]


def _absorption_bars5(entry_vol=1000.0):
    specs = [(1.0, 1.0, 1000.0, 1.001, 0.999)] * 300
    specs.append((1.0, 0.95, 3000.0, 1.001, 0.949))
    specs.append((0.95, 1.02, 1500.0, 1.021, 0.949))
    specs.append((1.02, 1.02, entry_vol, 1.021, 1.019))
    return _mk4_5(specs)


def _funding5(rate):
    settled = NOW5 - timedelta(hours=5)
    return {"ADAUSDT": [{"rate": rate, "settled_at": _iso5(settled),
                         "received_at": _iso5(settled + timedelta(minutes=30)),
                         "observed_public_endpoint": True}]}


def ev5(sid, bars4=None, funding=None):
    v = {"now": _iso5(NOW5), "bars": {}, "positions": [],
         "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    if bars4 is not None:
        v["bars"]["ADAUSDT|4Hour"] = bars4
    if funding is not None:
        v["funding"] = funding
    return importlib.import_module(f"aster_sleeves.{sid}").evaluate(
        v, {"sleeve_id": sid})


# ================= batch 6 / 7 / 12 crypto (adapters3, .kind objects) =================
NOW6 = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def bars6(n=25, breakout=True, vol=100000.0):
    out = []
    for i in range(n):
        t = NOW6 - timedelta(hours=4 * (n - i))
        c = 1.10 if (breakout and i == n - 1) else 1.0
        out.append({"t": t.isoformat(), "o": 1.0, "h": 1.05, "l": 0.95,
                    "c": c, "v": vol})
    return out


def drive6(sid, brs=None, funding=-0.01, positions=None, sym="ADAUSDT"):
    view = {"now": NOW6.isoformat(),
            "bars": {f"{sym}|4Hour": brs if brs is not None else bars6()},
            "funding": {sym: funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    return ev3(sid, view, {"sleeve_id": sid, "cycle_id": "fx",
                           "state_dir": tempfile.mkdtemp()})


def pos6(hours=20, qty=5000.0, sym="ADAUSDT"):
    return [{"symbol": sym, "qty": qty, "avg_price": 1.0,
             "opened_at": (NOW6 - timedelta(hours=hours)).isoformat(),
             "breakout_level": 1.05}]


def abs_bars7():
    out = []
    for i in range(302):
        t = NOW6 - timedelta(hours=4 * (302 - i))
        o = c = 2.0; h = 2.02; l = 1.98; v = 1000.0
        if i == 300: o, c, h, l, v = 2.0, 1.90, 2.0, 1.88, 5000.0
        if i == 301: o, c = 1.90, 1.96
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l, "c": c, "v": v})
    return out


def drive7(sid, brs=None, funding=-0.01, positions=None):
    view = {"now": NOW6.isoformat(),
            "bars": {"ENJUSDT|4Hour": brs if brs is not None else bars6()},
            "funding": {"ENJUSDT": funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    return ev3(sid, view, {"sleeve_id": sid, "cycle_id": "fx",
                           "state_dir": tempfile.mkdtemp()})


def pos7(hours=20, qty=5000.0):
    return [{"symbol": "ENJUSDT", "qty": qty, "avg_price": 1.0,
             "opened_at": (NOW6 - timedelta(hours=hours)).isoformat(),
             "breakout_level": 1.05}]


def bars12(n=25, breakout=True, vol=100000.0, last_close=None, shift_h=0):
    out = []
    for i in range(n):
        t = NOW6 - timedelta(hours=shift_h) - timedelta(hours=4 * (n - i))
        c = 22.0 if (breakout and i == n - 1) else 20.0
        out.append({"t": t.isoformat(), "o": 20.0, "h": 20.5, "l": 19.5,
                    "c": c, "v": vol})
    if last_close is not None:
        out[-1]["c"] = last_close
    return out


def drive12(sid, brs=None, funding=-0.01, positions=None):
    view = {"now": NOW6.isoformat(),
            "bars": {"LINKUSDT|4Hour": brs if brs is not None else bars12()},
            "funding": {"LINKUSDT": funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    return ev3(sid, view, {"sleeve_id": sid, "cycle_id": "fx",
                           "state_dir": tempfile.mkdtemp()})


def pos12(hours=20, qty=400.0):
    return [{"symbol": "LINKUSDT", "qty": qty, "avg_price": 20.0,
             "opened_at": (NOW6 - timedelta(hours=hours)).isoformat(),
             "breakout_level": 20.5}]


# ================= batch 9 ETF (interval entries) =================
UNIVERSE9 = ["QQQ", "SPY", "SMH", "XLB", "XLC", "XLE", "XLF", "XLI",
             "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]


def _series9(base, growth):
    return [base * (1 + growth * (i / 259.0)) for i in range(260)]


def make_bars9(winner="XLK"):
    m = {}
    for s in UNIVERSE9:
        g = 0.60 if s == winner else 0.05
        closes = _series9(100.0, g)
        rows = [{"t": "2025-06-02", "o": c, "h": c, "l": c, "c": c, "v": 1000}
                for c in closes]
        rows[-1] = dict(rows[-1], t="2026-10-15")
        m[f"{s}|1Day"] = rows
    return m


def view9(barsmap, positions=None, secondary=None):
    v = {"now": "2026-10-05T13:36:00+00:00", "bars": barsmap,
         "positions": positions or [],
         "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "extra": {}}
    if secondary is not None:
        v["bars_secondary"] = secondary
    return v


CTX9 = {"session": "2026-10-05", "now": "2026-10-05T13:36:00+00:00"}


# ================= ETF engine (batch 8 core25 / batch 10-11 fixed+monthly) =================
def flat_barsE(px, n=130):
    return [{"t": f"2026-01-{(i % 28) + 1:02d}", "o": px, "h": px, "l": px,
             "c": px, "v": 1000} for i in range(n)]


CTXE = {"session": "2026-10-01", "now": "2026-10-01T09:36:00",
        "slice": {"capital_usd": 10000.0}}


def viewE(barsmap, positions=None, now="2026-10-01T09:36:00"):
    return {"now": now, "bars": barsmap, "positions": positions or [],
            "quotes": {}, "extra": {}}


def basket8(leader="XLK"):
    syms = UNIVERSE9
    m = {s: flat_barsE(100.0) for s in syms}
    if leader:
        rows = flat_barsE(100.0)
        rows[3] = dict(rows[3], c=100.0)
        m[leader] = [{"t": r["t"], "o": r["o"], "h": r["h"], "l": r["l"],
                      "c": (100.0 if i < 3 else 120.0), "v": 1000}
                     for i, r in enumerate(rows)]
        # 126-session return uses close[-127]: set bar index 3 (=n-127) to 100, last 120
        m[leader] = flat_barsE(120.0)
        m[leader][3] = dict(m[leader][3], c=100.0)
    return m


# ================= batch 13 / 14 tensor =================
CTX13 = {"session": "2026-10-24", "now": "2026-10-24T15:00:00"}


def fire13(sid, sym="AAA", price=4.0, date="2026-10-23", **kw):
    f = {"sleeve_id": sid, "symbol": sym, "signal": "buy-cyan", "date": date,
         "price": price, "ret60": 40, "vol20": 0.1, "adv_usd": 3000000,
         "atr_ratio": 0.5}
    f.update(kw)
    return f


def tview13(sid, fires, positions=None, barsmap=None):
    return {"now": CTX13["now"], "tensor": {"fires": fires},
            "bars": barsmap or {}, "positions": positions or [], "extra": {}}


CTX14 = {"session": "2026-10-23", "now": "2026-10-23T15:00:00"}


def fire14(sym="ABC", price=8.0, **kw):
    f = {"symbol": sym, "signal": "buy-green", "price": price,
         "depth60": 80.0, "ret60": 5.0, "vol20": 0.12,
         "adv_usd": 3000000, "atr_ratio": 0.5, "date": "2026-10-22"}
    f.update(kw)
    return f


def view14(fires=None, positions=None, bars=None):
    return {"tensor": fires or [], "bars": bars or {},
            "positions": positions or []}


def bars14(px):
    return [{"t": "2026-10-23", "o": px, "h": px, "l": px, "c": px, "v": 1000}]


# ================= batch 15 (G4 red timeout / timing) =================
P15 = "aster_r19_"


def _weekdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


SESSIONS15 = _weekdays(date(2025, 1, 6), 640)
SESSION_STRS15 = [d.isoformat() for d in SESSIONS15]


def _at15(d, hh=9, mm=30):
    return datetime.combine(d, time(hh, mm), ET).astimezone(timezone.utc)


def drive15(sid, view, state_dir=None):
    view.setdefault("extra", {})["session_dates"] = SESSION_STRS15
    return ev3(sid, view, {"sleeve_id": sid, "cycle_id": "fx",
                           "state_dir": state_dir or tempfile.mkdtemp()})


def g4_view15(now, fires, positions=None, cash=10000.0, bars=None):
    return {"now": now.isoformat(), "tensor_fires": fires,
            "positions": positions or [],
            "bars": bars or {"AAA|1Day": [{"t": "2025-01-03", "o": 5.0,
                                           "h": 5.1, "l": 4.9, "c": 5.0,
                                           "v": 1e6}]},
            "slice": {"capital_usd": 10000.0, "cash_usd": cash},
            "quotes": {}, "extra": {}}


NOW_H15 = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)


def hour_bars15(n=61, close=100.0):
    out = []
    for i in range(n):
        t = NOW_H15 - timedelta(hours=n - i)
        out.append({"t": t.isoformat(),
                    "end": (t + timedelta(hours=1)).isoformat(),
                    "o": close, "h": close + 1, "l": close - 1,
                    "c": close, "v": 1000})
    return out


def swing15(**kw):
    s = {"confirmed": True, "score": 9, "invalidation": 99.0,
         "target": 110.0, "phenotype": "BULL", "usesFutureData": False,
         "bearishConflict": False}
    s.update(kw)
    return {"swing": s}


def hour_view15(sid_bars=61, sw=None, quotes=None, positions=None):
    return {"now": NOW_H15.isoformat(),
            "bars": {"MU|1Hour": hour_bars15(sid_bars)},
            "timing_signals": {"MU": sw if sw is not None else swing15()},
            "quotes": quotes or {"MU": {"bid": 99.9, "ask": 100.0}},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {}}


def cloud_fixture15():
    end = datetime(2026, 10, 23, 14, 50, tzinfo=timezone.utc)
    ten = []
    for i in range(30):
        c = 100 + 0.02 * i * i
        t = end - timedelta(minutes=10 * (30 - i))
        o, h, l = c, c + 0.2, c - 0.2
        if i == 29:
            l = 113.0
        ten.append({"t": t.isoformat(),
                    "end": (t + timedelta(minutes=10)).isoformat(),
                    "o": o, "h": h, "l": l, "c": c, "v": 1000})
    hour = []
    for i in range(60):
        c = 90 + 0.2 * i
        t = end - timedelta(hours=60 - i)
        hour.append({"t": t.isoformat(),
                     "end": (t + timedelta(hours=1)).isoformat(),
                     "o": c, "h": c + 0.3, "l": c - 0.3, "c": c, "v": 1000})
    daily = [{"t": "2026-10-22", "o": 100.0, "h": 130.0, "l": 99.0,
              "c": 105.0, "v": 1000}]
    return {"now": end.isoformat(),
            "bars": {"MU|10Min": ten, "MU|1Hour": hour, "MU|1Day": daily},
            "quotes": {"MU": {"bid": ten[-1]["c"] - 0.05,
                              "ask": ten[-1]["c"]}},
            "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {}}


# ================= batch 1 (abs_link / w1 recovery / open_gamma) =================
ABS_NOW1 = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def abs_bars1(n=302):
    out = []
    for i in range(n):
        t = ABS_NOW1 - timedelta(hours=4 * (n - i))
        o = c = 2.0; h, l, v = 2.02, 1.98, 1000.0
        if i == n - 2: o, c, h, l, v = 2.0, 1.90, 2.0, 1.88, 5000.0
        if i == n - 1: o, c, h, l = 1.90, 1.96, 1.97, 1.89
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l,
                    "c": c, "v": v})
    return out


def ctx1():
    return {"sleeve_id": "x", "state_dir": tempfile.mkdtemp(),
            "cycle_id": "fx"}


def trow1(idx, votes, frame="1h", **kw):
    bull = sum(1 for v in votes if v == 1)
    bear = sum(1 for v in votes if v == -1)
    d = {"bar_index": idx, "votes": votes, "bullish_votes": bull,
         "bearish_votes": bear, "total_votes": bull + bear,
         "balance": bull - bear, "close": 50.0, "atr14": 1.0,
         "dollar_volume20": 2000000, "volume": 100000,
         "obv_slope5": 500.0, "native_status": "ready", "frame": frame}
    d.update(kw)
    return d


# open gamma constants (from batch-1 fixture)
GSESS = "2026-10-23"; GPREV = "2026-10-22"
GOPENED = datetime(2026, 10, 23, 9, 30, tzinfo=ET)
GNOW = datetime(2026, 10, 23, 9, 37, tzinfo=ET)


def _iso1(d):
    return d.astimezone(timezone.utc).isoformat()


def gamma_event1(**kw):
    e = {"event_id": "E1", "symbol": "SPY", "session": GSESS,
         "prior_afternoon_session": GPREV,
         "first_5min_start_at": _iso1(GOPENED),
         "first_5min_end_at": _iso1(GOPENED + timedelta(minutes=5)),
         "first_5min_received_at": _iso1(GOPENED + timedelta(minutes=5, seconds=1)),
         "break_market_at": _iso1(GNOW - timedelta(seconds=2)),
         "break_received_at": _iso1(GNOW - timedelta(seconds=1)),
         "R5_signal_at": _iso1(datetime(2026, 10, 22, 15, 0, tzinfo=ET)),
         "R5_received_at": _iso1(datetime(2026, 10, 22, 15, 1, tzinfo=ET)),
         "first_5min_low": 99.5, "observed_break_price": 99.0,
         "first_5min_return": -0.008, "causal_R5_prior_afternoon": True,
         "first_5min_complete": True, "source_sha256": "a" * 64}
    e.update(kw)
    return e


def gamma_view1(positions=None, now=None):
    return {"now": _iso1(now or GNOW),
            "calendar": {"session": GSESS, "previous_session": GPREV,
                         "open": _iso1(GOPENED), "verified": True},
            "opening_events": [gamma_event1()] if positions is None else [],
            "options": [],
            "quotes": {"SPY": {"bid": 98.9, "ask": 99.1}},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "market_open": True}


# ================= batch 3 (recovery vertical/long + leaps exits) =================
SESSION3 = "2026-10-26"; PREV3 = "2026-10-23"
LONG_OCC3 = "SPY261113C00118000"; WING_OCC3 = "SPY261113C00123000"
EXPIRY3 = "2026-11-13"; LEAPS_OCC3 = "ACME280616C00004500"


def _future3(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


FUTURE3 = _future3(SESSION3, 320)


def chain3():
    mk = "2026-10-26T09:36:55-04:00"; rc = "2026-10-26T09:36:58-04:00"
    contracts = [
        {"symbol": LONG_OCC3, "underlying": "SPY", "right": "call",
         "expiry": EXPIRY3, "strike": 118.0, "delta": 0.55,
         "exercise_style": "american", "greeks_market_at": mk,
         "greeks_received_at": rc},
        {"symbol": WING_OCC3, "underlying": "SPY", "right": "call",
         "expiry": EXPIRY3, "strike": 123.0, "delta": 0.30,
         "exercise_style": "american", "greeks_market_at": mk,
         "greeks_received_at": rc}]
    quotes = {
        LONG_OCC3: {"symbol": LONG_OCC3, "feed": "opra", "bid": 2.90,
                    "ask": 3.00, "bid_size": 10, "ask_size": 10,
                    "market_at": "2026-10-26T09:36:56-04:00",
                    "received_at": rc},
        WING_OCC3: {"symbol": WING_OCC3, "feed": "opra", "bid": 1.10,
                    "ask": 1.20, "bid_size": 10, "ask_size": 10,
                    "market_at": "2026-10-26T09:36:56-04:00",
                    "received_at": rc}}
    return contracts, quotes


def calendar3():
    prev_map, closes = {}, {}
    for i, d in enumerate(FUTURE3):
        if i:
            prev_map[d] = FUTURE3[i - 1]
        closes[d] = f"{d}T16:00:00-04:00"
    return {"session": SESSION3, "previous_session": PREV3,
            "future_sessions": FUTURE3, "previous_session_by_date":
            {EXPIRY3: "2026-11-12", "2028-06-16": "2028-06-15"},
            "option_close_by_date": closes}


def held_position3(**meta_kw):
    contracts, _ = chain3()
    legs = [dict(contracts[0], ratio=1), dict(contracts[1], ratio=-1)]
    meta = {"legs": legs, "entry_spot": 118.0, "entry_session": SESSION3,
            "exit_session": "2026-10-30", "expiry_exit_session": "2026-11-12",
            "exit_rule": "fixed", "signal_id": "OPT_X:SPY:x",
            "rule_id": "OPT_X"}
    meta.update(meta_kw)
    return {"symbol": "PKG:TESTVERT", "qty": 1, "avg_price": 190.0,
            "opened_at": SESSION3, "metadata": meta}


def exit_view3(pos, now, session, und_bid=118.0):
    _, quotes = chain3()
    quotes[LONG_OCC3].update({"bid": 4.00, "ask": 4.10,
                              "market_at": now, "received_at": now})
    quotes[WING_OCC3].update({"bid": 0.50, "ask": 0.55,
                              "market_at": now, "received_at": now})
    cal = calendar3(); cal["session"] = session
    return {"now": now, "bars": {}, "options_chain": {},
            "quotes": {"SPY": {"symbol": "SPY", "feed": "sip",
                               "bid": und_bid, "ask": und_bid + 0.04,
                               "bid_size": 100, "ask_size": 100,
                               "market_at": now, "received_at": now}},
            "options_quotes": quotes, "positions": [pos],
            "calendar": cal,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {"market_open": True,
                      "option_fees": {"per_contract_per_fill": 0.65,
                                      "explicit_paper_assumption": True,
                                      "version": "aster-fixture-1"}},
            "params": {}}


def ev3b(sid, view, session, now):
    return ev3(sid, view, {"sleeve_id": sid, "session": session,
                           "now": now, "state_dir": "/tmp"})


# ================= batch 4 (vwap vertical + xsp) =================
EPOCH4 = date(1970, 1, 1); START4 = date(2025, 1, 1)


def ctx4(sid, session="2025-10-06", now=None):
    return {"sleeve_id": sid, "session": session,
            "now": now or (session + "T09:37:00"), "equity": 10000.0}


def vwap_bars4():
    out = []
    closes = [100 + (199 * i / 189) for i in range(190)] + [300.0] * 19
    for i, c in enumerate(closes):
        out.append({"t": float(((START4 + timedelta(days=i)) - EPOCH4).days * 86400),
                    "o": c, "h": c, "l": c, "c": c, "v": 10000.0})
    out.append({"t": float(((START4 + timedelta(days=209)) - EPOCH4).days * 86400),
                "o": 300.0, "h": 300.0, "l": 293.0, "c": 293.0, "v": 10000.0})
    return out


def vwap_chain4():
    exp = "2025-10-23"
    return [
        {"symbol": "SPY251023C00295000", "underlying": "SPY", "right": "call",
         "expiry": exp, "strike": 295.0, "delta": 0.55, "bid": 0.45,
         "ask": 0.50, "bid_size": 50, "ask_size": 50},
        {"symbol": "SPY251023C00300000", "underlying": "SPY", "right": "call",
         "expiry": exp, "strike": 300.0, "delta": 0.30, "bid": 0.25,
         "ask": 0.30, "bid_size": 50, "ask_size": 50}]


def vwap_pos4(held=0, entry_spot=293.0):
    legs = [{"symbol": "SPY251023C00295000", "underlying": "SPY",
             "right": "call", "expiry": "2025-10-23", "strike": 295.0,
             "ratio": 1},
            {"symbol": "SPY251023C00300000", "underlying": "SPY",
             "right": "call", "expiry": "2025-10-23", "strike": 300.0,
             "ratio": -1}]
    return [{"symbol": "SPY251023C00295000", "qty": 2, "avg_price": 0.25,
             "entry_spot": entry_spot, "sessions_held": held,
             "legs": legs, "opened_at": "2025-10-06"}]


def xsp_weekly4():
    fridays = [date(2025, 10, 3) - timedelta(days=7 * i) for i in range(20)][::-1]
    out = []
    for i, f in enumerate(fridays):
        c = 560.0 + 2 * i
        out.append({"week_end": f.isoformat(), "o": c - 1, "h": c + 5,
                    "l": c - 5, "c": c, "complete": True})
    return out


def xsp_chain4(short_bid=4.0, long_ask=1.5, adj_lo_mid=6.0, adj_hi_mid=7.0):
    out = []
    for k in range(560, 605, 5):
        bid, ask = 1.0, 1.2
        if k == 590: bid, ask = short_bid, short_bid + 0.2
        if k == 585: bid, ask = long_ask - 0.2, long_ask
        if k == 580: bid, ask = long_ask - 0.2, long_ask
        if k == 595: bid, ask = adj_lo_mid - 0.2, adj_lo_mid + 0.2
        if k == 600: bid, ask = adj_hi_mid - 0.2, adj_hi_mid + 0.2
        out.append({"symbol": f"XSP251010P{k}", "underlying": "XSP",
                    "right": "put", "expiry": "2025-10-10",
                    "strike": float(k), "bid": bid, "ask": ask,
                    "bid_size": 50, "ask_size": 50})
    return out


def xsp_view4(digital_hist=0.30, **kw):
    hist = [{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 1))).isoformat(),
             "value": digital_hist} for i in range(30)]
    return {"options": xsp_chain4(**kw), "positions": [],
            "calendar": {"first_session_of_week": True,
                         "session": "2025-10-06",
                         "previous_session": "2025-10-03",
                         "weekly_pm_expiry": "2025-10-10"},
            "xsp_state": {"weekly_bars": xsp_weekly4(),
                          "prior_digitals": hist,
                          "adjacent_put_symbols": ["XSP251010P595",
                                                   "XSP251010P600"]}}


def xsp_pos4():
    legs = [{"symbol": "XSP251010P585", "underlying": "XSP", "right": "put",
             "expiry": "2025-10-10", "strike": 585.0, "ratio": 1,
             "exercise_style": "european"},
            {"symbol": "XSP251010P590", "underlying": "XSP", "right": "put",
             "expiry": "2025-10-10", "strike": 590.0, "ratio": -1,
             "exercise_style": "european"}]
    return [{"symbol": "XSP251010P590", "qty": 1, "avg_price": 2.5,
             "entry_spot": 598.0, "legs": legs, "opened_at": "2025-10-06"}]


def xsp_graded_view4(cheap=False):
    v = xsp_view4()
    hist = ([{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 1))).isoformat(),
              "value": 0.25} for i in range(15)]
            + [{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 16))).isoformat(),
                "value": 0.45} for i in range(15)])
    v["xsp_state"]["prior_digitals"] = hist  # median .35, p75 .45
    v["options"] = xsp_chain4(adj_lo_mid=6.0, adj_hi_mid=8.0)  # digital .40
    for c in v["options"]:
        if c["strike"] == 585.0:
            c["bid"], c["ask"] = (4.6, 4.8) if cheap else (4.0, 4.2)
        if c["strike"] == 580.0:
            c["bid"], c["ask"] = (0.3, 0.4) if cheap else (1.3, 1.5)
    return v


# ================= drive tables =================
ADA = "aster_r19_adausdt_negative_funding_squeeze_"
ENJ = "aster_r19_enjusdt_"
LNK = "aster_r19_linkusdt_negative_funding_squeeze_"


def _normfail_bars6():
    b = bars6(breakout=False); b[-1]["c"] = 0.90; b[-1]["l"] = 0.90
    for bar in b:
        bar["t"] = (datetime.fromisoformat(bar["t"]) - timedelta(hours=8)).isoformat()
    return b


def _lost_bars6():
    b = bars6(breakout=False); b[-1]["c"] = 1.02
    return b


ENTRY_DRIVES = {
 # batch 5: vol1pct absorption variants (sibling fullcash drives proven)
 "aster_abs_neg_ada_vol1pct": lambda: ev5(
     "aster_abs_neg_ada_vol1pct", bars4=_absorption_bars5(entry_vol=50000.0),
     funding=_funding5(-0.0005)),
 "aster_abs_nonneg_ada_vol1pct": lambda: ev5(
     "aster_abs_nonneg_ada_vol1pct", bars4=_absorption_bars5(entry_vol=50000.0),
     funding=_funding5(0.0005)),
 # batch 9: INTERVAL M150 + INTERVAL_DRIFT1 C098 entries (secondary proven)
 "aster_etf_interval1_m150": lambda: ev3(
     "aster_etf_interval1_m150", view9(make_bars9("XLK"), secondary=make_bars9("XLK")), CTX9),
 "aster_etf_interval_drift1_c098": lambda: ev3(
     "aster_etf_interval_drift1_c098", view9(make_bars9("XLK"), secondary=make_bars9("XLK")), CTX9),
 # batch 2: pead B / vertical A entries + recovery touch A/B entries
 "aster_pead_long_b": lambda: ev3("aster_pead_long_b", pead_view2(), ctx2("aster_pead_long_b")),
 "aster_pead_vertical_a": lambda: ev3("aster_pead_vertical_a", pead_view2(), ctx2("aster_pead_vertical_a")),
 "aster_rec_rsi2_long_touch_a": lambda: ev3("aster_rec_rsi2_long_touch_a", rec_view2(), ctx2("aster_rec_rsi2_long_touch_a")),
 "aster_rec_rsi2_long_touch_b": lambda: ev3("aster_rec_rsi2_long_touch_b", rec_view2(), ctx2("aster_rec_rsi2_long_touch_b")),
 # batch 6: ADA NFS sibling arms enter on the proven breakout+funding fixture
 ADA + "fixed96_volume1pct": lambda: drive6(ADA + "fixed96_volume1pct"),
 ADA + "lost_breakout_fullcash": lambda: drive6(ADA + "lost_breakout_fullcash"),
 ADA + "lost_breakout_volume1pct": lambda: drive6(ADA + "lost_breakout_volume1pct"),
 ADA + "normalization_failure_fullcash": lambda: drive6(ADA + "normalization_failure_fullcash"),
 ADA + "normalization_failure_volume1pct": lambda: drive6(ADA + "normalization_failure_volume1pct"),
 ADA + "normalization_fullcash": lambda: drive6(ADA + "normalization_fullcash"),
 ADA + "normalization_volume1pct": lambda: drive6(ADA + "normalization_volume1pct"),
 # batch 7: ENJ absorption negative-funding vol1pct arm
 ENJ + "absorption_negative_funding_fixed16_volume1pct": lambda: drive7(
     ENJ + "absorption_negative_funding_fixed16_volume1pct", brs=abs_bars7()),
 # batch 15: hourly floor1+delay1 (62 bars, waited-bar geometry alive)
 "aster_r19_timing_hour_floor1_delay1": lambda: drive15(
     "aster_r19_timing_hour_floor1_delay1",
     hour_view15(sid_bars=62, sw=swing15(invalidation=98.0))),
 # batch 13: C1 delay cool/hot (prior-session fire, vol split)
 "aster_tensor_c1_delay_cool_25": lambda: ev3(
     "aster_tensor_c1_delay_cool_25",
     tview13("aster_tensor_c1_delay_cool_25",
             [fire13("aster_tensor_c1_delay_cool_25", atr_ratio=0.5)]), CTX13),
 "aster_tensor_c1_delay_hot_25": lambda: ev3(
     "aster_tensor_c1_delay_hot_25",
     tview13("aster_tensor_c1_delay_hot_25",
             [fire13("aster_tensor_c1_delay_hot_25", atr_ratio=1.5)]), CTX13),
 # batch 14: G4 delay cool + reserve cool entries
 "aster_tensor_g4_delay_cool_25": lambda: ev3(
     "aster_tensor_g4_delay_cool_25", view14([fire14(atr_ratio=0.5)]), CTX14),
 "aster_tensor_g4_reserve_cool_25": lambda: ev3(
     "aster_tensor_g4_reserve_cool_25",
     view14([fire14(atr_ratio=0.5)],
            positions=[{"symbol": "QQQ", "qty": 10, "avg_price": 100.0}],
            bars={"QQQ": bars14(100.0)}), CTX14),
 # batch 4: XSP graded B entry (graded band + cheap legs so the B book affords it)
 "aster_xsp_pcs_graded_b": lambda: ev3(
     "aster_xsp_pcs_graded_b", xsp_graded_view4(cheap=True),
     ctx4("aster_xsp_pcs_graded_b", session="2025-10-06", now="2025-10-06T10:02:00")),
}

EXIT_DRIVES = {
 # batch 1: LINK absorption 16h deadline (ENJ sibling proven)
 "aster_abs_link_4h": lambda: ev3(
     "aster_abs_link_4h",
     {"now": ABS_NOW1.isoformat(),
      "bars": {"LINKUSDT|4Hour": abs_bars1()}, "quotes": {},
      "positions": [{"symbol": "LINKUSDT", "qty": 1000.0, "avg_price": 1.96,
                     "opened_at": (ABS_NOW1 - timedelta(hours=20)).isoformat()}],
      "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}, ctx1()),
 # batch 1: weekly tensor recovery 20-native-bar hold exit
 "aster_tensor_w1_recovery": lambda: ev3(
     "aster_tensor_w1_recovery",
     {"now": "2026-10-23T14:00:00+00:00",
      "tensor": {"ACME": [trow1(240, [1, 1, 1, -1, 1, -1, -1], frame="1wk")]},
      "bars": {},
      "positions": [{"symbol": "ACME", "qty": 10, "avg_price": 50.0,
                     "entry_bar_index": 220}],
      "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}, ctx1()),
 # batch 1: opening gamma B same-day 10:00 flat exit
 "aster_open_gamma_b": lambda: ev3(
     "aster_open_gamma_b",
     gamma_view1(positions=[{"symbol": "SPY261031P00099000", "qty": 1,
                             "avg_price": 0.4, "entry_session": GSESS,
                             "legs": [{"symbol": "SPY261031P00099000",
                                       "underlying": "SPY", "right": "put",
                                       "expiry": "2026-10-31",
                                       "strike": 99.0, "ratio": 1}]}],
                 now=datetime(2026, 10, 23, 10, 0, tzinfo=ET)), ctx1()),
 # batch 2: options-package exits (planned hold / touch)
 "aster_core_rsi2_long": lambda: ev3(
     "aster_core_rsi2_long",
     {"bars": {"SPY": bars2([185.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=5)}, ctx2("aster_core_rsi2_long")),
 "aster_core_rsi2_vertical": lambda: ev3(
     "aster_core_rsi2_vertical",
     {"bars": {"SPY": bars2([185.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=5, structure="vertical")},
     ctx2("aster_core_rsi2_vertical")),
 "aster_pead_long_b": lambda: ev3(
     "aster_pead_long_b",
     {"bars": {"SPY": bars2([180.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=10)}, ctx2("aster_pead_long_b")),
 "aster_pead_vertical_a": lambda: ev3(
     "aster_pead_vertical_a",
     {"bars": {"SPY": bars2([180.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=10, structure="vertical")},
     ctx2("aster_pead_vertical_a")),
 "aster_pead_vertical_b": lambda: ev3(
     "aster_pead_vertical_b",
     {"bars": {"SPY": bars2([180.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=10, structure="vertical")},
     ctx2("aster_pead_vertical_b")),
 "aster_rec_rsi2_long_fixed_b": lambda: ev3(
     "aster_rec_rsi2_long_fixed_b",
     {"bars": {"SPY": bars2([185.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=5)}, ctx2("aster_rec_rsi2_long_fixed_b")),
 "aster_rec_rsi2_long_touch_b": lambda: ev3(
     "aster_rec_rsi2_long_touch_b",
     {"bars": {"SPY": bars2([185.0] * 10)}, "options": chain2(),
      "positions": opt_pos2(held=2)}, ctx2("aster_rec_rsi2_long_touch_b")),
 # batch 3: recovery vertical/long B exits + leaps B deadline exit
 "aster_rec_rsi2_vertical_fixed_b": lambda: ev3b(
     "aster_rec_rsi2_vertical_fixed_b",
     exit_view3(held_position3(), "2026-10-30T15:56:00-04:00", "2026-10-30"),
     "2026-10-30", "2026-10-30T15:56:00-04:00"),
 "aster_rec_vwap20_long_fixed_b": lambda: ev3b(
     "aster_rec_vwap20_long_fixed_b",
     exit_view3(held_position3(), "2026-10-30T15:56:00-04:00", "2026-10-30"),
     "2026-10-30", "2026-10-30T15:56:00-04:00"),
 "aster_rec_vwap20_long_touch_b": lambda: ev3b(
     "aster_rec_vwap20_long_touch_b",
     exit_view3(held_position3(exit_rule="touch"),
                "2026-10-28T10:15:00-04:00", "2026-10-28", und_bid=120.50),
     "2026-10-28", "2026-10-28T10:15:00-04:00"),
 "aster_tensor_leaps_b": lambda: _leaps_b_exit(),
 # batch 4: vwap vertical B exits + xsp settle exits
 "aster_rec_vwap20_vert_fixed_b": lambda: ev3(
     "aster_rec_vwap20_vert_fixed_b",
     {"bars": {"SPY": vwap_bars4()}, "options": vwap_chain4(),
      "positions": vwap_pos4(held=5)}, ctx4("aster_rec_vwap20_vert_fixed_b")),
 "aster_rec_vwap20_vert_touch_b": lambda: ev3(
     "aster_rec_vwap20_vert_touch_b",
     {"bars": {"SPY": _vwap_touch_bars4()}, "options": vwap_chain4(),
      "positions": vwap_pos4(held=2)}, ctx4("aster_rec_vwap20_vert_touch_b")),
 "aster_xsp_pcs_calm_b": lambda: _xsp_settle("aster_xsp_pcs_calm_b"),
 "aster_xsp_pcs_graded_a": lambda: _xsp_settle("aster_xsp_pcs_graded_a"),
 "aster_xsp_pcs_graded_b": lambda: _xsp_settle("aster_xsp_pcs_graded_b"),
 # batch 6: ADA NFS vol1pct structural/deadline exits
 ADA + "fixed96_volume1pct": lambda: drive6(ADA + "fixed96_volume1pct", positions=pos6(hours=97)),
 ADA + "lost_breakout_volume1pct": lambda: drive6(ADA + "lost_breakout_volume1pct", brs=_lost_bars6(), positions=pos6(hours=2)),
 ADA + "normalization_failure_volume1pct": lambda: drive6(ADA + "normalization_failure_volume1pct", brs=_normfail_bars6(), funding=0.002, positions=pos6(hours=20)),
 ADA + "normalization_volume1pct": lambda: drive6(ADA + "normalization_volume1pct", funding=0.0, positions=pos6(hours=2)),
 # batch 12: LINK NFS vol1pct exits (4h execution delay on structural arms)
 LNK + "fixed96_volume1pct": lambda: drive12(LNK + "fixed96_volume1pct", positions=pos12(hours=97)),
 LNK + "lost_breakout_volume1pct": lambda: drive12(LNK + "lost_breakout_volume1pct", brs=bars12(breakout=False, last_close=19.0, shift_h=8), positions=pos12(hours=20)),
 LNK + "normalization_failure_volume1pct": lambda: drive12(LNK + "normalization_failure_volume1pct", brs=_normfail_bars12(), funding=0.002, positions=pos12(hours=20)),
 # batch 7: ENJ fixed16 deadline exits for all six arms
 ENJ + "absorption_negative_funding_fixed16_fullcash": lambda: drive7(ENJ + "absorption_negative_funding_fixed16_fullcash", positions=pos7(hours=17)),
 ENJ + "absorption_negative_funding_fixed16_volume1pct": lambda: drive7(ENJ + "absorption_negative_funding_fixed16_volume1pct", positions=pos7(hours=17)),
 ENJ + "absorption_nonnegative_funding_fixed16_fullcash": lambda: drive7(ENJ + "absorption_nonnegative_funding_fixed16_fullcash", positions=pos7(hours=17)),
 ENJ + "absorption_nonnegative_funding_fixed16_volume1pct": lambda: drive7(ENJ + "absorption_nonnegative_funding_fixed16_volume1pct", positions=pos7(hours=17)),
 ENJ + "breakout_base_fixed16_fullcash": lambda: drive7(ENJ + "breakout_base_fixed16_fullcash", positions=pos7(hours=17)),
 ENJ + "breakout_base_fixed16_volume1pct": lambda: drive7(ENJ + "breakout_base_fixed16_volume1pct", positions=pos7(hours=17)),
 # ETF: core25 M150 rotation exit (non-target XLK sold in full)
 "aster_etf_core25_m150": lambda: ev3(
     "aster_etf_core25_m150",
     viewE(basket8(leader="XLE"),
           positions=[{"symbol": "QQQ", "qty": 73, "avg_price": 100.0, "entry_date": "2026-09-02"},
                      {"symbol": "XLK", "qty": 20, "avg_price": 120.0, "entry_date": "2026-09-02"}]),
     CTXE),
 # ETF monthly: non-target holding sold in full (kind=exit) at new month
 "aster_etf_qld_monthly": lambda: _monthly_exit("aster_etf_qld_monthly", "QLD", "SPY"),
 "aster_etf_qqq_monthly_c098": lambda: _monthly_exit("aster_etf_qqq_monthly_c098", "QQQ", "SPY"),
 "aster_etf_qqq_monthly_m150": lambda: _monthly_exit("aster_etf_qqq_monthly_m150", "QQQ", "SPY"),
 "aster_etf_qqq_qld_monthly": lambda: _monthly_exit2("aster_etf_qqq_qld_monthly"),
 "aster_etf_spy_monthly_c098": lambda: _monthly_exit("aster_etf_spy_monthly_c098", "SPY", "QQQ"),
 "aster_etf_spy_monthly_m150": lambda: _monthly_exit("aster_etf_spy_monthly_m150", "SPY", "QQQ"),
 # batch 14: G4 week-52 deadline exits for the six un-driven arms
 "aster_tensor_g4_cash_all_10": lambda: _g4_week52("aster_tensor_g4_cash_all_10"),
 "aster_tensor_g4_cash_cool_25": lambda: _g4_week52("aster_tensor_g4_cash_cool_25"),
 "aster_tensor_g4_cash_hot_25": lambda: _g4_week52("aster_tensor_g4_cash_hot_25"),
 "aster_tensor_g4_delay_all_25": lambda: _g4_week52("aster_tensor_g4_delay_all_25"),
 "aster_tensor_g4_delay_cool_25": lambda: _g4_week52("aster_tensor_g4_delay_cool_25"),
 "aster_tensor_g4_reserve_cool_25": lambda: _g4_week52("aster_tensor_g4_reserve_cool_25"),
 # batch 15: G4 red-timeout 52-week exit, cloud aggressive stop exit,
 # hourly stop exits for the three un-driven floor/delay arms
 "aster_r19_tensor_g4_red_timeout_25": lambda: _red_week52(),
 "aster_r19_timing_cloud_aggressive": lambda: _cloud_stop("aster_r19_timing_cloud_aggressive"),
 "aster_r19_timing_hour_floor0_delay1": lambda: _hour_stop("aster_r19_timing_hour_floor0_delay1"),
 "aster_r19_timing_hour_floor1_delay0": lambda: _hour_stop("aster_r19_timing_hour_floor1_delay0"),
 "aster_r19_timing_hour_floor1_delay1": lambda: _hour_stop("aster_r19_timing_hour_floor1_delay1"),
}

# Buy-hold family: never exit BY DESIGN (engine freq == "BUY_HOLD").
BUY_HOLD_EXEMPT = ["aster_etf_qld_buy_hold", "aster_etf_qqq_buy_hold",
                   "aster_etf_qqq_qld_buy_hold", "aster_etf_spy_buy_hold",
                   "aster_etf_smh_hold_c098", "aster_etf_smh_hold_m150"]
BUY_HOLD_TARGET = {"aster_etf_qld_buy_hold": "QLD",
                   "aster_etf_qqq_buy_hold": "QQQ",
                   "aster_etf_qqq_qld_buy_hold": "QQQ",
                   "aster_etf_spy_buy_hold": "SPY",
                   "aster_etf_smh_hold_c098": "SMH",
                   "aster_etf_smh_hold_m150": "SMH"}


def _vwap_touch_bars4():
    bars = [dict(x) for x in vwap_bars4()]
    bars[-1].update({"h": 300.0, "l": 299.0, "c": 300.0})
    return bars


def _normfail_bars12():
    b = bars12(breakout=False, last_close=18.0, shift_h=8)
    b[-1]["l"] = 18.0
    return b


def _xsp_settle(sid):
    v = xsp_view4(); v["positions"] = xsp_pos4()
    return ev3(sid, v, ctx4(sid, session="2025-10-10", now="2025-10-10T16:05:00"))


def _monthly_exit(sid, target, held_sym):
    bars = {target: flat_barsE(100.0), held_sym: flat_barsE(100.0)}
    if sid.startswith("aster_etf_qqq_qld"):
        bars["QLD"] = flat_barsE(50.0)
    pos = [{"symbol": held_sym, "qty": 10, "avg_price": 100.0,
            "entry_date": "2026-09-02"}]
    # WEIGHT-LAG-ACTIVE-20261031: aster_etf acts on the PREVIOUS
    # evaluation's targets, so drive two evaluations and return the
    # second (the first computes the targets and emits nothing).
    from desk3 import aster_etf
    aster_etf._PENDING_TARGETS.pop(sid, None)
    assert ev3(sid, viewE(bars, positions=pos), CTXE) == []
    return ev3(sid, viewE(bars, positions=pos), CTXE)


def _monthly_exit2(sid):
    bars = {"QQQ": flat_barsE(100.0), "QLD": flat_barsE(50.0),
            "SPY": flat_barsE(100.0)}
    pos = [{"symbol": "SPY", "qty": 10, "avg_price": 100.0,
            "entry_date": "2026-09-02"}]
    # WEIGHT-LAG-ACTIVE-20261031: two evaluations, as in _monthly_exit.
    from desk3 import aster_etf
    aster_etf._PENDING_TARGETS.pop(sid, None)
    assert ev3(sid, viewE(bars, positions=pos), CTXE) == []
    return ev3(sid, viewE(bars, positions=pos), CTXE)


def _g4_week52(sid):
    pos = [{"symbol": "ABC", "qty": 50, "avg_price": 8.0,
            "sessions_held": 260}]
    return ev3(sid, view14([], positions=pos, bars={"ABC": bars14(8.0)}), CTX14)


def _red_week52():
    sid = "aster_r19_tensor_g4_red_timeout_25"
    entry = date(2025, 2, 18)
    monday = entry - timedelta(days=entry.weekday())
    week = monday + timedelta(weeks=51)
    rows = [d for d in SESSIONS15 if week <= d < week + timedelta(days=7)]
    xday = rows[-1]
    pos = [{"symbol": "AAA", "qty": 79, "avg_price": 5.0,
            "opened_at": _at15(entry).isoformat(), "issuer_id": "iss-AAA"}]
    return drive15(sid, g4_view15(_at15(xday), [], positions=pos))


def _cloud_stop(sid):
    v = cloud_fixture15()
    v["positions"] = [{"symbol": "MU", "qty": 5, "avg_price": 110.0,
                       "opened_at": v["now"],
                       "meta": {"stop": 200.0, "target": 300.0}}]
    return drive15(sid, v)


def _hour_stop(sid):
    pos = [{"symbol": "MU", "qty": 9, "avg_price": 100.0,
            "opened_at": NOW_H15.isoformat(),
            "meta": {"stop": 99.0, "target": 110.0}}]
    v = hour_view15(positions=pos,
                    quotes={"MU": {"bid": 98.0, "ask": 98.1}})
    return drive15(sid, v)


def _leaps_b_exit():
    sid = "aster_tensor_leaps_b"
    contracts = [{"symbol": LEAPS_OCC3, "underlying": "ACME",
                  "right": "call", "expiry": "2028-06-16", "strike": 4.5,
                  "delta": 0.70, "exercise_style": "american",
                  "greeks_market_at": "2026-10-26T09:36:55-04:00",
                  "greeks_received_at": "2026-10-26T09:36:58-04:00"}]
    legs = [dict(contracts[0], ratio=1)]
    meta = {"legs": legs, "entry_spot": 5.0, "entry_session": SESSION3,
            "exit_session": "2027-10-26",
            "expiry_exit_session": "2028-06-15", "exit_rule": "fixed",
            "signal_id": "OPT_TENSOR_LEAPS_B:EV1",
            "rule_id": "OPT_TENSOR_LEAPS_B", "G4_event_id": "EV1",
            "original_G4_exit_at": "2027-10-22T15:55:00-04:00"}
    pos = {"symbol": "PKG:TESTLEAPS", "qty": 1, "avg_price": 150.0,
           "opened_at": SESSION3, "metadata": meta}
    now = "2027-10-22T15:56:00-04:00"
    v = exit_view3(pos, now, "2027-10-22")
    v["options_quotes"] = {LEAPS_OCC3: {
        "symbol": LEAPS_OCC3, "feed": "opra", "bid": 2.00, "ask": 2.10,
        "bid_size": 5, "ask_size": 5, "market_at": now, "received_at": now}}
    v["calendar"]["session"] = "2027-10-22"
    return ev3b(sid, v, "2027-10-22", now)


class TestCensusCoverage(unittest.TestCase):
    def test_tables_cover_verifier_lists(self):
        self.assertEqual(len(ENTRY_DRIVES), 22, sorted(ENTRY_DRIVES))
        self.assertEqual(len(EXIT_DRIVES), 50, sorted(EXIT_DRIVES))
        self.assertEqual(len(BUY_HOLD_EXEMPT), 6)
        cfg = {s["id"] for s in json.load(
            open(os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]}
        for sid in list(ENTRY_DRIVES) + list(EXIT_DRIVES) + BUY_HOLD_EXEMPT:
            self.assertIn(sid, cfg, sid)


class TestEntryDrives(unittest.TestCase):
    def test_every_named_sleeve_returns_entry(self):
        for sid, drive in ENTRY_DRIVES.items():
            with self.subTest(sid=sid):
                out = drive()
                self.assertIn("entry", K(out), (sid, out))


class TestExitDrives(unittest.TestCase):
    def test_every_named_sleeve_returns_exit(self):
        for sid, drive in EXIT_DRIVES.items():
            with self.subTest(sid=sid):
                out = drive()
                self.assertIn("exit", K(out), (sid, out))


class TestBuyHoldExemption(unittest.TestCase):
    def test_buy_hold_never_exits_by_design(self):
        import desk3.aster_batch11  # registers SPY specs into the ETF engine
        from desk3 import aster_etf
        for sid in BUY_HOLD_EXEMPT:
            with self.subTest(sid=sid):
                self.assertEqual(aster_etf.SPECS[sid]["freq"], "BUY_HOLD", sid)
                sym = BUY_HOLD_TARGET[sid]
                pos = [{"symbol": sym, "qty": 50, "avg_price": 100.0,
                        "entry_date": "2026-09-02"}]
                out = ev3(sid, viewE({sym: flat_barsE(50.0)}, positions=pos,
                                     now="2026-11-02T09:36:00"), CTXE)
                self.assertEqual(out, [], sid)  # designed: no exit, ever


if __name__ == "__main__":
    unittest.main()
