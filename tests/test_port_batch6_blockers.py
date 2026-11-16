"""Batch-6 port blockers (PORT6): every batch-6 sleeve fixture-drives
through its v3 adapter evaluate(view, ctx) on the SAME fixture inputs
as v2's tests/test_port_batch6.py + test_port_batch6_saty.py +
test_batch5_fixtures.py (raschke), and produces the SAME intents those
v2 tests record as the oracle (entry fires, each designed exit fires,
refusals refuse). Strategy files must be byte-identical to v2.
Fail direction: on the pre-port tree these modules do not exist.
"""
import hashlib
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = "/home/hatch/workspace/muse-desk-v2"
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
IDS = ["raschke_rre", "red_day_reversal", "rsi_meanrev", "rsi_meanrev_options",
       "rule_1d_cyan_smallcap", "rule_1d_green_tom", "rule_1h_cyan_raw",
       "rule_1w_cyan_mom_adx", "rule_1w_swing_beta_wt", "saty_day"]


def evaluate(sid, view, state_dir=None):
    mod = importlib.import_module(f"desk_sleeves.{sid}")
    ctx = {"cycle_id": "fix-1", "sleeve_id": sid,
           "state_dir": state_dir or tempfile.mkdtemp(),
           "snapshot_hash": "fix"}
    return mod.evaluate(view, ctx)


def daily(closes, start=date(2025, 1, 1), vol=200000.0):
    out = []
    for i, c in enumerate(closes):
        d = start + timedelta(days=i)
        out.append({"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c * 1.01,
                    "l": c * 0.99, "c": c, "v": vol})
    return out


def last_date(start, n):
    return (start + timedelta(days=n - 1)).isoformat()


def view_for(now_iso, bars, positions=None, extra=None, **kw):
    v = {"now": now_iso, "bars": bars, "positions": positions or [],
         "extra": extra or {}}
    v.update(kw)
    return v


def seeded(symbol, qty, price, ts):
    return [{"symbol": symbol, "qty": qty, "avg_price": price,
             "opened_at": ts, "intent_id": "seed-1"}]


RSI_ENTRY_CLOSES = ([100.0] * 240
                    + [104.0, 108.0, 112.0, 116.0, 120.0, 124.0, 128.0,
                       132.0, 136.0, 140.0, 126.0, 112.0])


class TestByteIdentity(unittest.TestCase):
    def test_strategies_and_core_byte_identical_to_v2(self):
        for sid in IDS:
            if sid == "raschke_rre":
                # MIDNA RULING R2-RRE-20261025: the section-7
                # event seam in sleeves/raschke_rre.py is wired
                # to the desk macro calendar by owner-delegated
                # ruling, so this ONE wrapper legitimately
                # diverges from v2; its core/raschke_rre engine
                # package stays byte-identical (checked below)
                # and the seam is pinned by
                # test_raschke_rre_event_feed_blockers.py.
                continue
            if sid == "saty_day":
                # SATY-DAY-STOP-20261116 (desk full audit
                # escalation 6, owner ruling 2026-11-16): the
                # daily stop takes the Saty family standard
                # fraction 0.01 of slice equity (saty_magnum
                # SESSION_STOP_PCT, saty_sol_0dte
                # DAILY_LOSS_FRACTION), replacing v2's
                # DAILY_STOP_USD = 10000.0 — 100% of the $10,000
                # slice, i.e. no stop. This ONE sleeve
                # legitimately diverges from v2 by that cure
                # only; the divergence is confined to the
                # daily-stop hunks and pinned by
                # test_risk_shapes_20261116_blockers.py
                # (TestSatyDayV2DivergenceConfinement).
                continue
            a = open(os.path.join(ROOT, "sleeves", sid + ".py"), "rb").read()
            b = open(os.path.join(V2, "sleeves", sid + ".py"), "rb").read()
            self.assertEqual(hashlib.sha256(a).hexdigest(),
                             hashlib.sha256(b).hexdigest(), sid)
        for rel in ("core/sleeve.py", "core/data.py", "core/early_close.py",
                    "core/saty_bars.py", "core/saty_indicators.py",
                    "core/saty_primitives.py", "core/raschke_rre/__init__.py",
                    "core/raschke_rre/admission.py", "core/raschke_rre/awareness.py",
                    "core/raschke_rre/raschke_core.py",
                    "core/raschke_rre/raschke_engine.py",
                    "core/raschke_rre/router.py"):
            a = open(os.path.join(ROOT, rel), "rb").read()
            b = open(os.path.join(V2, rel), "rb").read()
            self.assertEqual(a, b, rel)

    def test_config_rows_match_v2(self):
        v3 = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]}
        v2 = {s["id"]: s for s in json.load(open(os.path.join(V2, "config", "sleeves.json")))["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, v3)
            for k in ("cadence_s", "slice", "bp_buffer_frac", "flat_by_close",
                      "flatten_time_et", "session", "parked"):
                self.assertEqual(v3[sid][k], v2[sid][k], f"{sid}.{k}")
            self.assertTrue(v3[sid]["inputs"], sid)


class TestRedDay(unittest.TestCase):
    def test_entry(self):
        closes = [50.0 + 50.0 * i / 208 for i in range(209)] + [96.5]
        now = f"{last_date(date(2025, 1, 1), len(closes))}T10:00:00-04:00"
        out = evaluate("red_day_reversal",
                       view_for(now, {"SPY|1Day": daily(closes)}))
        self.assertEqual(len(out), 1, out)
        i = out[0]
        self.assertEqual((i["kind"], i["symbol"], i["side"]), ("entry", "SPY", "buy"))
        self.assertEqual(i["stop_price"], round(96.5 * 0.98, 2))

    def test_exit(self):
        closes = [90.0] * 209 + [104.5]
        now = f"{last_date(date(2025, 1, 1), len(closes))}T10:00:00-04:00"
        out = evaluate("red_day_reversal",
                       view_for(now, {"SPY|1Day": daily(closes)},
                                positions=seeded("SPY", 50, 100.0, "2025-07-26T14:00:00Z")))
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertEqual((exits[0]["qty"], exits[0]["side"]), (50, "sell"))

    def test_no_signal_refuses(self):
        closes = [100.0] * 210
        now = f"{last_date(date(2025, 1, 1), len(closes))}T10:00:00-04:00"
        self.assertEqual(evaluate("red_day_reversal",
                                  view_for(now, {"SPY|1Day": daily(closes)})), [])


class TestRsiMeanrev(unittest.TestCase):
    def _now(self):
        return f"{last_date(date(2025, 1, 1), len(RSI_ENTRY_CLOSES))}T10:00:00-04:00"

    def test_entry(self):
        extra = {"earnings": {"SPY": None}, "earnings_fresh": True}
        out = evaluate("rsi_meanrev",
                       view_for(self._now(), {"SPY|1Day": daily(RSI_ENTRY_CLOSES)}, extra=extra))
        self.assertEqual(len(out), 1, out)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["stop_price"], round(112.0 * 0.92, 2))

    def test_entry_vetoed_on_stale_earnings(self):
        extra = {"earnings": {"SPY": None}, "earnings_fresh": False}
        out = evaluate("rsi_meanrev",
                       view_for(self._now(), {"SPY|1Day": daily(RSI_ENTRY_CLOSES)}, extra=extra))
        self.assertEqual(out, [])

    def test_exit(self):
        closes = [100.0] * 240 + [110.0, 120.0, 118.0, 114.0, 110.0, 106.0]
        now = f"{last_date(date(2025, 1, 1), len(closes))}T10:00:00-04:00"
        out = evaluate("rsi_meanrev",
                       view_for(now, {"SPY|1Day": daily(closes)},
                                positions=seeded("SPY", 50, 100.0, "2025-08-31T14:00:00Z")))
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertEqual(exits[0]["qty"], 50)


def _opt_extra(session_d):
    exp = session_d + timedelta(days=21)
    chain, quotes = [], {}
    for strike in range(100, 126):
        occ = f"SPY{exp:%y%m%d}C{strike * 1000:08d}"
        chain.append({"symbol": occ, "strike": float(strike),
                      "expiration": exp.isoformat()})
        if strike == 112:
            quotes[occ] = {"bid": 0.29, "ask": 0.30}
        elif strike == 121:
            quotes[occ] = {"bid": 0.10, "ask": 0.11}
        else:
            quotes[occ] = {"bid": 0.05, "ask": 0.06}
    return {"chains": {"SPY": chain}, "quotes": quotes}


class TestRsiOptions(unittest.TestCase):
    def test_entry(self):
        session_d = date(2025, 1, 1) + timedelta(days=len(RSI_ENTRY_CLOSES) - 1)
        out = evaluate("rsi_meanrev_options",
                       view_for(f"{session_d.isoformat()}T10:00:00-04:00",
                                {"SPY|1Day": daily(RSI_ENTRY_CLOSES)},
                                extra=_opt_extra(session_d)))
        self.assertEqual(len(out), 1, out)
        i = out[0]
        self.assertEqual((i["kind"], i["symbol"], i["qty"]), ("entry", "SPY", 1))
        self.assertIn("call_debit_spread", i["reason"])

    def test_exit_rsi_overbought(self):
        closes = [100.0] * 240 + [110.0, 120.0, 130.0, 140.0, 150.0, 160.0]
        now = f"{last_date(date(2025, 1, 1), len(closes))}T10:00:00-04:00"
        out = evaluate("rsi_meanrev_options",
                       view_for(now, {"SPY|1Day": daily(closes)},
                                positions=seeded("SPY", 1, 3.0, "2025-08-31T14:00:00Z")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1, out)


def _rule_entry(_sid, feats, px=7.0, sym="MU", n=25):
    bars = daily([px] * n, vol=200000.0)
    session = last_date(date(2025, 1, 1), n)
    extra = {"rule_fires": {sym: [{"date": session, "features": feats}]}}
    return bars, session, extra, sym


class TestRuleSleeves(unittest.TestCase):
    def test_smallcap_entry_and_exit(self):
        bars, session, extra, sym = _rule_entry("x", {"pxn": 2, "di": 0.0})
        extra["log_mcap"] = {"MU": 9.0}
        out = evaluate("rule_1d_cyan_smallcap",
                       view_for(f"{session}T10:00:00-04:00", {"MU|1Day": bars}, extra=extra))
        self.assertEqual(len(out), 1, out)
        self.assertEqual(out[0]["qty"], 14)
        bars30 = daily([7.0] * 30, vol=200000.0)
        now = f"{last_date(date(2025, 1, 1), 30)}T10:00:00-04:00"
        out = evaluate("rule_1d_cyan_smallcap",
                       view_for(now, {"MU|1Day": bars30},
                                positions=seeded("MU", 10, 7.0, "2025-01-02T14:00:00Z")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1, out)

    def test_green_tom_entry_and_exit(self):
        days = []
        d = date(2025, 8, 1)
        while d <= date(2025, 9, 2):
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += timedelta(days=1)
        bars = daily([20.0] * 25, start=date(2025, 8, 9), vol=100000.0)
        session = "2025-09-02"
        extra = {"rule_fires": {"MU": [{"date": session, "features":
                                        {"mom121": 0.7, "disp": 0.025, "tom": 0}}]},
                 "trading_days": days}
        out = evaluate("rule_1d_green_tom",
                       view_for(f"{session}T10:00:00-04:00", {"MU|1Day": bars}, extra=extra))
        self.assertEqual(len(out), 1, out)
        self.assertEqual(out[0]["qty"], 5)
        bars70 = daily([20.0] * 70, vol=100000.0)
        now = f"{last_date(date(2025, 1, 1), 70)}T10:00:00-04:00"
        out = evaluate("rule_1d_green_tom",
                       view_for(now, {"MU|1Day": bars70},
                                positions=seeded("MU", 5, 20.0, "2025-01-02T14:00:00Z")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1, out)

    def test_1w_mom_adx_entry_and_exit(self):
        bars, session, extra, sym = _rule_entry("x", {"dv": 7.0, "mom": 0.5, "adx": 30.0}, px=20.0)
        out = evaluate("rule_1w_cyan_mom_adx",
                       view_for(f"{session}T10:00:00-04:00", {"MU|1Day": bars}, extra=extra))
        self.assertEqual(len(out), 1, out)
        bars130 = daily([20.0] * 130, vol=100000.0)
        now = f"{last_date(date(2025, 1, 1), 130)}T10:00:00-04:00"
        out = evaluate("rule_1w_cyan_mom_adx",
                       view_for(now, {"MU|1Day": bars130},
                                positions=seeded("MU", 5, 20.0, "2025-01-02T14:00:00Z")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1, out)

    def test_1w_swing_beta_entry_and_exit(self):
        bars, session, extra, sym = _rule_entry("x", {"beta": 1.5, "wt1": 30.0, "ribbons": 0.02}, px=20.0)
        out = evaluate("rule_1w_swing_beta_wt",
                       view_for(f"{session}T10:00:00-04:00", {"MU|1Day": bars}, extra=extra))
        self.assertEqual(len(out), 1, out)
        bars130 = daily([20.0] * 130, vol=100000.0)
        now = f"{last_date(date(2025, 1, 1), 130)}T10:00:00-04:00"
        out = evaluate("rule_1w_swing_beta_wt",
                       view_for(now, {"MU|1Day": bars130},
                                positions=seeded("MU", 5, 20.0, "2025-01-02T14:00:00Z")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1, out)

    def test_rule_refuses_without_fire(self):
        bars = daily([7.0] * 25, vol=200000.0)
        session = last_date(date(2025, 1, 1), 25)
        out = evaluate("rule_1d_cyan_smallcap",
                       view_for(f"{session}T10:00:00-04:00", {"MU|1Day": bars}))
        self.assertEqual(out, [])


def _hourly(n, start=datetime(2026, 10, 19, 13, 0, tzinfo=timezone.utc), px=10.0):
    return [{"t": (start + timedelta(hours=i)).isoformat().replace("+00:00", "Z"),
             "o": px, "h": px * 1.01, "l": px * 0.99, "c": px, "v": 1000.0}
            for i in range(n)]


class TestRule1h(unittest.TestCase):
    def test_entry_and_exit(self):
        hb = _hourly(120)
        last_iso = datetime.fromisoformat(hb[-1]["t"].replace("Z", "+00:00")).isoformat()
        sig_date = datetime.fromisoformat(hb[-1]["t"].replace("Z", "+00:00")).astimezone(ET).date()
        dbars = daily([10.0] * 25, start=sig_date - timedelta(days=24), vol=200000.0)
        extra = {"rule_fires_1h": {"MU": [{"t": last_iso, "rangeatr": 3.0,
                                           "wtgap": 7.0, "smhUp": 1}]}}
        out = evaluate("rule_1h_cyan_raw",
                       view_for("2026-10-21T12:30:00-04:00",
                                {"MU|1Hour": hb, "MU|1Day": dbars}, extra=extra))
        self.assertEqual(len(out), 1, out)
        self.assertEqual(out[0]["qty"], 10)
        hb2 = _hourly(12, start=datetime(2026, 10, 21, 13, 0, tzinfo=timezone.utc))
        out = evaluate("rule_1h_cyan_raw",
                       view_for("2026-10-21T12:30:00-04:00", {"MU|1Hour": hb2},
                                positions=seeded("MU", 5, 10.0, "2026-10-21T13:00:00+00:00")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1, out)


def _rth5(day, base=600.0, drift=0.05):
    out, t, i = [], datetime(2026, 10, day, 9, 30, tzinfo=ET), 0
    while t < datetime(2026, 10, day, 16, 0, tzinfo=ET):
        c = base + drift * i
        out.append({"t": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "o": c, "h": c + 0.3, "l": c - 0.3, "c": c, "v": 10000})
        t += timedelta(minutes=5)
        i += 1
    return out


class TestRaschkeRre(unittest.TestCase):
    def test_drive_evaluates_deterministically(self):
        bars = {"SPY|5Min": _rth5(20) + _rth5(21)}
        v = view_for("2026-10-21T15:00:00-04:00", bars)
        sd = tempfile.mkdtemp()
        out1 = evaluate("raschke_rre", v, state_dir=sd)
        out2 = evaluate("raschke_rre", v, state_dir=sd)
        self.assertIsInstance(out1, list)
        self.assertEqual(out1, out2)


# ---------------- saty_day (builders ported from v2 test_port_batch6_saty) ----
SESSION = "2026-10-21"
SESSION_D = date(2026, 10, 21)
MID = 3.05


def _b(t_epoch, o, h, l, c, v=10000.0):
    return {"t": t_epoch, "o": o, "h": h, "l": l, "c": c, "v": v}


def _trading_days_before(n, end=SESSION_D):
    days, d = [], end - timedelta(days=1)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return sorted(days)


def _rth_closes():
    pts = []
    for i in range(78):
        if i <= 20:
            c = 500.0 + 4.0 * i / 20
        elif i <= 50:
            c = 504.0 - 8.0 * (i - 20) / 30
        else:
            c = 496.0 + 4.0 * (i - 50) / 27
        pts.append(round(c, 4))
    pts[-1] = 500.0
    return pts


def _hist_bars(days):
    out = []
    prev_close = 500.0
    for d in days:
        base = datetime.combine(d, time(4, 0), tzinfo=ET)
        t = base
        for _ in range(66):
            out.append(_b(t.timestamp(), prev_close, prev_close + 0.3,
                          prev_close - 0.3, prev_close))
            t += timedelta(minutes=5)
        prev = prev_close
        for c in _rth_closes():
            o = prev
            h = max(o, c) + (1.0 if c == 504.0 else 0.15)
            l = min(o, c) - (1.0 if c == 496.0 else 0.15)
            out.append(_b(t.timestamp(), o, h, l, c))
            prev = c
            t += timedelta(minutes=5)
        for _ in range(48):
            out.append(_b(t.timestamp(), prev, prev + 0.3, prev - 0.3, prev))
            t += timedelta(minutes=5)
        prev_close = prev
    return out


def _today_1m(waypoints, start=time(9, 30)):
    wps = [(datetime.combine(SESSION_D, w, tzinfo=ET), p) for w, p in waypoints]
    out, cur, wi = [], wps[0][1], 0
    t, end = wps[0][0], wps[-1][0]
    while t < end:
        nxt = t + timedelta(minutes=1)
        while wi + 1 < len(wps) and wps[wi + 1][0] <= t:
            wi += 1
        a_t, a_p = wps[wi]
        if wi + 1 < len(wps):
            b_t, b_p = wps[wi + 1]
            frac = (nxt - a_t).total_seconds() / (b_t - a_t).total_seconds()
            c = a_p + (b_p - a_p) * min(1.0, max(0.0, frac))
        else:
            c = a_p
        out.append(_b(t.timestamp(), cur, max(cur, c), min(cur, c), c))
        cur = c
        t = nxt
    return out


def _agg_5m(m1):
    out = []
    for i in range(0, len(m1), 5):
        grp = m1[i:i + 5]
        if grp:
            out.append(_b(grp[0]["t"], grp[0]["o"], max(b["h"] for b in grp),
                          min(b["l"] for b in grp), grp[-1]["c"],
                          sum(b["v"] for b in grp)))
    return out


def _occ_for(exp, kind, strike):
    return f"SPY{exp:%y%m%d}{kind}{int(round(strike * 1000)):08d}"


EXPIRIES = [date(2026, 10, 21), date(2026, 10, 22),
            date(2026, 10, 23), date(2026, 10, 26)]


def _chains():
    rows = []
    for exp in EXPIRIES:
        for kind in ("C", "P"):
            for strike in range(470, 531):
                rows.append({"symbol": _occ_for(exp, kind, strike),
                             "strike": float(strike),
                             "expiration": exp.isoformat()})
    return {"SPY": rows}


def _fresh_quotes(now_epoch, mid=MID, spread=0.10):
    t_iso = datetime.fromtimestamp(now_epoch, tz=ET).astimezone(
        timezone.utc).isoformat().replace("+00:00", "Z")
    return {c["symbol"]: {"symbol": c["symbol"], "bp": mid - spread / 2,
                          "ap": mid + spread / 2, "t": t_iso,
                          "received_at": t_iso}
            for rows in _chains().values() for c in rows}


def _snap_quotes(mid=MID):
    return {c["symbol"]: {"bid": mid - 0.05, "ask": mid + 0.05}
            for rows in _chains().values() for c in rows}


def _saty_view(now_hhmm, spy1=None, qqq1=None, fq=None, positions=None):
    days = _trading_days_before(110)
    hist = _hist_bars(days)
    spy5, qqq5 = list(hist), list(hist)
    if spy1:
        spy5 += _agg_5m(spy1)
    if qqq1:
        qqq5 += _agg_5m(qqq1)
    bars = {"SPY|5Min": spy5, "QQQ|5Min": qqq5}
    if spy1:
        bars["SPY|1Min"] = spy1
    if qqq1:
        bars["QQQ|1Min"] = qqq1
    now = datetime.combine(SESSION_D, now_hhmm, tzinfo=ET)
    payload = {"chains": _chains(), "quotes": _snap_quotes(),
               "fresh_quotes": fq or {}, "latest_quote": {}}
    return {"now": now.isoformat(), "bars": bars,
            "positions": positions or [], "extra": {},
            "options": {"SPY": payload},
            "slice": {"capital_usd": 100000.0, "cash_usd": 100000.0}}


def _saty_position(qty=4, entry_hhmm=time(10, 5), spot=503.9):
    et = datetime.combine(SESSION_D, entry_hhmm, tzinfo=ET).timestamp()
    return [{"symbol": "SPY", "qty": qty, "avg_price": MID,
             "opened_at": datetime.fromtimestamp(et, tz=ET).isoformat(),
             "occ": _occ_for(date(2026, 10, 21), "C", 504),
             "entry_px": MID, "entry_premium": MID, "entry_spot": spot,
             "entry_t": et, "fill_t": et, "signal_date": SESSION,
             "expiry": "2026-10-21", "strike": 504.0, "intent_id": "seed-1"}]


class TestSatyDay(unittest.TestCase):
    def test_warmup_blocked_refuses(self):
        def flat_5m(days=20, px=500.0):
            out = []
            d = date(2026, 9, 28)
            made = 0
            while made < days:
                if d.weekday() < 5:
                    base = datetime.combine(d, time(13, 30), tzinfo=timezone.utc)
                    for i in range(78):
                        t = base + timedelta(minutes=5 * i)
                        out.append({"t": t.isoformat().replace("+00:00", "Z"),
                                    "o": px, "h": px + 1, "l": px - 1, "c": px, "v": 1000.0})
                    made += 1
                d += timedelta(days=1)
            return out
        v = view_for("2026-10-21T10:00:00-04:00",
                     {"SPY|5Min": flat_5m(), "QQQ|5Min": flat_5m()})
        self.assertEqual(evaluate("saty_day", v), [])

    def test_golden_gate_entry(self):
        spy1 = _today_1m([(time(9, 30), 500.0), (time(9, 55), 503.0),
                          (time(10, 4), 503.9), (time(10, 5), 504.2),
                          (time(11, 0), 504.5)])
        qqq1 = _today_1m([(time(9, 30), 500.0), (time(10, 5), 506.0),
                          (time(16, 0), 506.0)])
        now = datetime.combine(SESSION_D, time(10, 6), tzinfo=ET)
        v = _saty_view(time(10, 6), spy1=spy1, qqq1=qqq1,
                       fq=_fresh_quotes(now.timestamp()))
        out = evaluate("saty_day", v)
        self.assertEqual(len(out), 1, out)
        it = out[0]
        self.assertEqual((it["kind"], it["symbol"]), ("entry", "SPY261021C00504000"))
        self.assertEqual(it["position_intent"], "buy_to_open")
        self.assertEqual(it["side"], "buy")
        self.assertEqual(it["qty"], 13)
        self.assertEqual(it["limit_price"], MID)
        self.assertIn("setup=gg", it["reason"])

    def test_gg_kill_exit(self):
        spy1 = _today_1m([(time(9, 30), 500.0), (time(10, 5), 504.0),
                          (time(10, 30), 503.0), (time(10, 40), 501.0),
                          (time(11, 0), 501.0)])
        qqq1 = _today_1m([(time(9, 30), 500.0), (time(16, 0), 500.0)])
        now = datetime.combine(SESSION_D, time(10, 41), tzinfo=ET)
        v = _saty_view(time(10, 41), spy1=spy1, qqq1=qqq1,
                       fq=_fresh_quotes(now.timestamp()),
                       positions=_saty_position(qty=4))
        out = evaluate("saty_day", v)
        self.assertEqual(len(out), 1, out)
        it = out[0]
        self.assertEqual((it["kind"], it["qty"]), ("exit", 4))
        self.assertEqual(it["position_intent"], "sell_to_close")
        self.assertIn("gg_kill", it["reason"])


class TestRegistryDeclaration(unittest.TestCase):
    def test_inputs_match_adapter_declarations(self):
        from desk3.port_batch6 import config_rows
        for row in config_rows():
            mod = importlib.import_module(f"desk_sleeves.{row['id']}")
            self.assertEqual(tuple(row["inputs"]), tuple(mod.INPUTS), row["id"])
            self.assertEqual(row["module"], row["id"])


if __name__ == "__main__":
    unittest.main()
