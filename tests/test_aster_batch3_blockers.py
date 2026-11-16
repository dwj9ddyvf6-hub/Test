"""Blockers: Aster batch 3 (ASTER-B3) — recovery RSI2 vertical x4,
tensor_leaps x2, recovery VWAP20 long x4 (TSV rows 26-35).

Faithful port of archive r19_options.py recovery/tensor_leaps rules:
recovery_signal (close>SMA200; RSI2<10 Wilder-archive recursion;
VWAP20 close<=0.98*VWAP20 of typical price), entry window 09:35-09:40
ET, signal = previous session, universe [IWM,QQQ,SPY] lexicographic,
DTE/delta contract selection, vertical wing = strike nearest
spot*1.02, debit/width + premium/spot caps, risk sizing
qty=floor(risk/(debit+fees)) capped by displayed size, exits: fixed
5th-session close-5m, touch bid>=entry_spot*1.02, pre-expiry
close-15m, assignment, european expiry settle; tensor_leaps consumes
qualified native G4 events (Tensor products at the sleeve layer),
540-720 DTE / 0.6-0.8 delta, 365-calendar-day checkpoint + original
G4 deadline/event exits. Slice $10,000; risk A=2% ($200), B=0.5% ($50).
Inputs are v3 producer keys (bars/options_chain/quotes/positions/
tensor) — absent producers => UNFED in the registry, never fake-fed.
Fail direction: pre-build tree has no adapters3.aster_* modules.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import date, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IDS = {
 "aster_rec_rsi2_vertical_fixed_a": dict(book="OPT_RSI2_VERTICAL_FIXED_A", signal="RSI2", structure="vertical", exit_rule="fixed", risk=0.02),
 "aster_rec_rsi2_vertical_fixed_b": dict(book="OPT_RSI2_VERTICAL_FIXED_B", signal="RSI2", structure="vertical", exit_rule="fixed", risk=0.005),
 "aster_rec_rsi2_vertical_touch_a": dict(book="OPT_RSI2_VERTICAL_TOUCH_A", signal="RSI2", structure="vertical", exit_rule="touch", risk=0.02),
 "aster_rec_rsi2_vertical_touch_b": dict(book="OPT_RSI2_VERTICAL_TOUCH_B", signal="RSI2", structure="vertical", exit_rule="touch", risk=0.005),
 "aster_tensor_leaps_a": dict(book="OPT_TENSOR_LEAPS_A", signal=None, structure="long", exit_rule=None, risk=0.02),
 "aster_tensor_leaps_b": dict(book="OPT_TENSOR_LEAPS_B", signal=None, structure="long", exit_rule=None, risk=0.005),
 "aster_rec_vwap20_long_fixed_a": dict(book="OPT_VWAP20_LONG_FIXED_A", signal="VWAP20", structure="long", exit_rule="fixed", risk=0.02),
 "aster_rec_vwap20_long_fixed_b": dict(book="OPT_VWAP20_LONG_FIXED_B", signal="VWAP20", structure="long", exit_rule="fixed", risk=0.005),
 "aster_rec_vwap20_long_touch_a": dict(book="OPT_VWAP20_LONG_TOUCH_A", signal="VWAP20", structure="long", exit_rule="touch", risk=0.02),
 "aster_rec_vwap20_long_touch_b": dict(book="OPT_VWAP20_LONG_TOUCH_B", signal="VWAP20", structure="long", exit_rule="touch", risk=0.005),
}
REC_IDS = [s for s in IDS if s.startswith("aster_rec_")]
ENTRY_NOW = "2026-10-26T09:37:00-04:00"   # Monday, inside 09:35-09:40
SESSION = "2026-10-26"
PREV = "2026-10-23"                        # Friday


def bizdays(end, n):
    out, d = [], date.fromisoformat(end)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return list(reversed(out))


def future_sessions(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


FUTURE = future_sessions(SESSION, 320)


def bars(closes, end=PREV, volumes=None):
    days = bizdays(end, len(closes))
    rows = []
    for i, (d, c) in enumerate(zip(days, closes)):
        rows.append({"session": d, "date": d, "t": f"{d}T14:30:00-04:00",
                     "o": c, "h": c + 0.5, "l": c - 0.5, "c": c,
                     "v": (volumes[i] if volumes else 1000.0),
                     "complete": True,
                     "usable_after": f"{d}T20:00:00-04:00"})
    return rows


def rsi_closes():
    cs = [100.0 + 0.1 * i for i in range(195)] + [120.0, 118.0, 116.0, 114.0, 112.0]
    return cs  # last close 112 > SMA200 ~109.9, RSI2 crushed by 4 down closes


def rise_closes():
    return [100.0 + 0.1 * i for i in range(200)]  # RSI2 high: no recovery signal


def vwap_closes(dip=True):
    cs = [100.0 + 0.15 * i for i in range(200)]
    if dip:
        cs[-1] = 124.0  # <= 0.98 * VWAP20(~126.7), still > SMA200(~114.9)
    return cs


LONG_OCC = "SPY261113C00118000"
WING_OCC = "SPY261113C00123000"
EXPIRY = "2026-11-13"


def chain(long_ask=3.00, long_bid=2.90, wing_ask=1.20, wing_bid=1.10,
          long_delta=0.55, wing_strike=123.0, wing_occ=WING_OCC, size=10):
    mk = "2026-10-26T09:36:55-04:00"; rc = "2026-10-26T09:36:58-04:00"
    contracts = [
        {"symbol": LONG_OCC, "underlying": "SPY", "right": "call",
         "expiry": EXPIRY, "strike": 118.0, "delta": long_delta,
         "exercise_style": "american",
         "greeks_market_at": mk, "greeks_received_at": rc},
        {"symbol": wing_occ, "underlying": "SPY", "right": "call",
         "expiry": EXPIRY, "strike": wing_strike, "delta": 0.30,
         "exercise_style": "american",
         "greeks_market_at": mk, "greeks_received_at": rc}]
    quotes = {
        LONG_OCC: {"symbol": LONG_OCC, "feed": "opra", "bid": long_bid,
                   "ask": long_ask, "bid_size": size, "ask_size": size,
                   "market_at": "2026-10-26T09:36:56-04:00", "received_at": rc},
        wing_occ: {"symbol": wing_occ, "feed": "opra", "bid": wing_bid,
                   "ask": wing_ask, "bid_size": size, "ask_size": size,
                   "market_at": "2026-10-26T09:36:56-04:00", "received_at": rc}}
    return contracts, quotes


def cheap_chain():
    return chain(long_ask=0.30, long_bid=0.28, wing_ask=0.02, wing_bid=0.01,
                 wing_strike=120.0, wing_occ="SPY261113C00120000")


LEAPS_OCC = "ACME280616C00004500"
LEAPS_EXP = "2028-06-16"


def leaps_chain(occ=LEAPS_OCC, und="ACME", strike=4.5, ask=1.50, bid=1.40,
                delta=0.70, size=5, expiry=LEAPS_EXP):
    mk = "2026-10-26T09:36:55-04:00"; rc = "2026-10-26T09:36:58-04:00"
    contracts = [{"symbol": occ, "underlying": und, "right": "call",
                  "expiry": expiry, "strike": strike, "delta": delta,
                  "exercise_style": "american",
                  "greeks_market_at": mk, "greeks_received_at": rc}]
    quotes = {occ: {"symbol": occ, "feed": "opra", "bid": bid, "ask": ask,
                    "bid_size": size, "ask_size": size,
                    "market_at": "2026-10-26T09:36:56-04:00",
                    "received_at": rc}}
    return contracts, quotes


def g4_event(sym="ACME", **kw):
    e = {"event_id": "EV1", "symbol": sym, "qualified_native_G4": True,
         "source_sha256": "a" * 16, "signal_end": "2026-10-23T20:00:00-04:00",
         "available_at": "2026-10-24T12:00:00-04:00",
         "entry_session": SESSION,
         "original_G4_exit_at": "2027-10-22T15:55:00-04:00",
         "original_G4_exit_session": "2027-10-22"}
    e.update(kw)
    return e


def calendar():
    prev_map, closes = {}, {}
    all_days = FUTURE
    for i, d in enumerate(all_days):
        if i:
            prev_map[d] = all_days[i - 1]
        closes[d] = f"{d}T16:00:00-04:00"
    return {"session": SESSION, "previous_session": PREV,
            "future_sessions": FUTURE, "previous_session_by_date":
            {EXPIRY: "2026-11-12", LEAPS_EXP: "2028-06-15"},
            "option_close_by_date": closes}


def base_view(sid):
    spec = IDS[sid]
    closes = rsi_closes() if spec["signal"] == "RSI2" else vwap_closes()
    contracts, quotes = chain()
    v = {"now": ENTRY_NOW,
         "bars": {"SPY": bars(closes), "QQQ": bars(rise_closes()),
                  "IWM": bars(rise_closes())},
         "options_chain": {"SPY": contracts},
         "quotes": {"SPY": {"symbol": "SPY", "feed": "sip", "bid": 117.98,
                            "ask": 118.02, "bid_size": 100, "ask_size": 100,
                            "market_at": "2026-10-26T09:36:56-04:00",
                            "received_at": "2026-10-26T09:36:58-04:00"}},
         "options_quotes": quotes,
         "positions": [],
         "calendar": calendar(),
         "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
         "extra": {"market_open": True,
                   "option_fees": {"per_contract_per_fill": 0.65,
                                   "explicit_paper_assumption": True,
                                   "version": "aster-fixture-1"}},
         "params": {}}
    return v


def leaps_view(sid, micro=False):
    if micro:
        contracts, quotes = leaps_chain(
            occ="PENY280616C00001350", und="PENY", strike=1.35,
            ask=0.40, bid=0.36)
        und, spot = "PENY", (1.49, 1.51)
        ev = g4_event(sym="PENY")
    else:
        contracts, quotes = leaps_chain()
        und, spot = "ACME", (4.98, 5.02)
        ev = g4_event()
    v = base_view(sid)
    v["bars"] = {}
    v["options_chain"] = {und: contracts}
    v["options_quotes"] = quotes
    v["quotes"] = {und: {"symbol": und, "feed": "sip", "bid": spot[0],
                         "ask": spot[1], "bid_size": 100, "ask_size": 100,
                         "market_at": "2026-10-26T09:36:56-04:00",
                         "received_at": "2026-10-26T09:36:58-04:00"}}
    v["extra"]["tensor_G4_events"] = [ev]
    v["extra"]["installed_at"] = "2026-10-20T00:00:00-04:00"
    return v


def ev(sid, view, session=SESSION, now=ENTRY_NOW):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, {"sleeve_id": sid, "session": session, "now": now,
               "state_dir": "/tmp"})


def entry_view_for(sid):
    v = leaps_view(sid, micro=sid.endswith("_b")) \
        if sid.startswith("aster_tensor") else base_view(sid)
    if sid.endswith("_b") and sid.startswith("aster_rec_"):
        contracts, quotes = cheap_chain()
        v["options_chain"] = {"SPY": contracts}
        v["options_quotes"] = quotes
    if IDS[sid]["structure"] == "long" and sid.startswith("aster_rec_"):
        # long-only chain; ask 1.50 -> per-package 150.65 fits the $200
        # A budget and (via cheap_chain scale) is refused for B below in
        # its own test; B long sleeves get a 0.40-ask chain here.
        if sid.endswith("_b"):
            contracts, quotes = chain(long_ask=0.40, long_bid=0.36)
        else:
            contracts, quotes = chain(long_ask=1.50, long_bid=1.40)
        v["options_chain"] = {"SPY": contracts[:1]}  # long only, no wing leg
        v["options_quotes"] = {LONG_OCC: quotes[LONG_OCC]}
    return v


class TestEntries(unittest.TestCase):
    def test_entry_fires_for_every_sleeve(self):
        for sid in IDS:
            out = ev(sid, entry_view_for(sid))
            self.assertEqual(len(out), 1, sid)
            i = out[0]
            self.assertEqual(i["kind"], "entry", sid)
            self.assertEqual(i["side"], "buy", sid)
            self.assertEqual(i["position_intent"], "buy_to_open", sid)
            self.assertIn(sid, i["intent_id"], sid)
            self.assertTrue(i["legs"], sid)

    def test_vertical_structure_and_sizing(self):
        out = ev("aster_rec_rsi2_vertical_fixed_a",
                 entry_view_for("aster_rec_rsi2_vertical_fixed_a"))
        i = out[0]
        self.assertEqual([l["symbol"] for l in i["legs"]], [LONG_OCC, WING_OCC])
        self.assertEqual([l["ratio"] for l in i["legs"]], [1, -1])
        # debit (3.00-1.10)*100=190 + fees 2*0.65=1.30 -> floor(200/191.30)=1
        self.assertEqual(i["qty"], 1)
        self.assertAlmostEqual(i["price_hint"], 190.0)
        meta = i["metadata"]
        self.assertEqual(meta["exit_session"], "2026-10-30")  # 5th session, entry day = session 1 (archive sessions[4])
        self.assertEqual(meta["exit_rule"], "fixed")
        self.assertEqual(meta["rule_id"], "OPT_RSI2_VERTICAL_FIXED_A")

    def test_long_recovery_sizing(self):
        # Standard 3.00-ask chain: per-package 300.65 > $200 A risk
        # budget -> faithful source sizing refuses (qty would be 0).
        v0 = base_view("aster_rec_vwap20_long_fixed_a")
        contracts, quotes = chain()
        v0["options_chain"] = {"SPY": contracts[:1]}
        v0["options_quotes"] = {LONG_OCC: quotes[LONG_OCC]}
        self.assertEqual(ev("aster_rec_vwap20_long_fixed_a", v0), [])
        contracts, quotes = chain(long_ask=1.50, long_bid=1.40)
        v = entry_view_for("aster_rec_vwap20_long_fixed_a")
        v["options_chain"] = {"SPY": contracts[:1]}
        v["options_quotes"] = {LONG_OCC: quotes[LONG_OCC]}
        out = ev("aster_rec_vwap20_long_fixed_a", v)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 1)  # floor(200/150.65)=1

    def test_b_sleeve_sizes_smaller(self):
        out = ev("aster_rec_rsi2_vertical_fixed_b",
                 entry_view_for("aster_rec_rsi2_vertical_fixed_b"))
        # cheap chain: debit 28 + 1.30 fees -> floor(50/29.30)=1
        self.assertEqual(out[0]["qty"], 1)

    def test_leaps_entry(self):
        out = ev("aster_tensor_leaps_a", entry_view_for("aster_tensor_leaps_a"))
        i = out[0]
        self.assertEqual(i["legs"][0]["symbol"], LEAPS_OCC)
        self.assertEqual(i["qty"], 1)  # floor(200/150.65)
        self.assertEqual(i["metadata"]["G4_event_id"], "EV1")
        self.assertEqual(i["metadata"]["original_G4_exit_at"],
                         "2027-10-22T15:55:00-04:00")
        out_b = ev("aster_tensor_leaps_b",
                   entry_view_for("aster_tensor_leaps_b"))
        self.assertEqual(out_b[0]["qty"], 1)  # micro chain floor(50/40.65)

    def test_determinism(self):
        sid = "aster_rec_rsi2_vertical_touch_a"
        self.assertEqual(ev(sid, entry_view_for(sid)),
                         ev(sid, entry_view_for(sid)))


class TestRefusals(unittest.TestCase):
    def test_no_signal_no_entry(self):
        for sid in REC_IDS:
            v = base_view(sid)
            v["bars"]["SPY"] = bars(rise_closes())  # RSI high / VWAP not dipped
            self.assertEqual(ev(sid, v), [], sid)

    def test_warmup_refuses(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        v = base_view(sid)
        v["bars"]["SPY"] = bars(rsi_closes()[:199])
        self.assertEqual(ev(sid, v), [])

    def test_stale_signal_refuses(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        v = base_view(sid)
        v["bars"]["SPY"] = bars(rsi_closes(), end="2026-10-22")
        self.assertEqual(ev(sid, v), [])

    def test_outside_window_and_market_closed(self):
        sid = "aster_rec_vwap20_long_fixed_a"
        v = entry_view_for(sid)
        v["now"] = "2026-10-26T10:00:00-04:00"
        self.assertEqual(ev(sid, v, now="2026-10-26T10:00:00-04:00",
                            session=SESSION), [])
        v2 = entry_view_for(sid)
        v2["extra"]["market_open"] = False
        self.assertEqual(ev(sid, v2), [])

    def test_no_qualified_contract(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        v = base_view(sid)
        contracts, quotes = chain(long_delta=0.90)
        v["options_chain"] = {"SPY": contracts}
        v["options_quotes"] = quotes
        self.assertEqual(ev(sid, v), [])

    def test_debit_width_cap_refuses(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        v = base_view(sid)
        contracts, quotes = chain(long_ask=3.40, wing_bid=0.05, wing_ask=0.10)
        v["options_chain"] = {"SPY": contracts}
        v["options_quotes"] = quotes
        self.assertEqual(ev(sid, v), [])  # debit 335 / width 500 = 0.67 > 0.60

    def test_premium_spot_cap_refuses_leaps(self):
        sid = "aster_tensor_leaps_a"
        v = leaps_view(sid)
        contracts, quotes = leaps_chain(ask=60.00, bid=59.00)
        v["options_chain"] = {"ACME": contracts}
        v["options_quotes"] = quotes
        self.assertEqual(ev(sid, v), [])

    def test_b_unaffordable_on_standard_chain(self):
        sid = "aster_rec_rsi2_vertical_fixed_b"
        v = base_view(sid)  # per-package 191.30 > $50 B risk budget
        self.assertEqual(ev(sid, v), [])

    def test_leaps_requires_qualified_g4(self):
        sid = "aster_tensor_leaps_a"
        v = leaps_view(sid)
        v["extra"]["tensor_G4_events"] = []
        self.assertEqual(ev(sid, v), [])
        v = leaps_view(sid)
        v["extra"]["tensor_G4_events"] = [
            g4_event(signal_end="2026-10-19T20:00:00-04:00")]  # pre-install
        self.assertEqual(ev(sid, v), [])
        v = leaps_view(sid)
        v["extra"]["tensor_G4_events"] = [
            g4_event(original_G4_exit_at="2026-10-25T15:55:00-04:00")]
        self.assertEqual(ev(sid, v), [])  # deadline already passed

    def test_no_reentry_while_holding(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        v = entry_view_for(sid)
        v["positions"] = [held_position()]
        self.assertEqual(ev(sid, v, now=ENTRY_NOW, session=SESSION), [])


def held_position(**meta_kw):
    contracts, _ = chain()
    legs = [dict(contracts[0], ratio=1), dict(contracts[1], ratio=-1)]
    meta = {"legs": legs, "entry_spot": 118.0, "entry_session": SESSION,
            "exit_session": "2026-10-30", "expiry_exit_session": "2026-11-12",
            "exit_rule": "fixed", "signal_id": "OPT_RSI2_VERTICAL_FIXED_A:SPY:x",
            "rule_id": "OPT_RSI2_VERTICAL_FIXED_A"}
    meta.update(meta_kw)
    return {"symbol": "PKG:TESTVERT", "qty": 1, "avg_price": 190.0,
            "opened_at": SESSION, "metadata": meta}


def exit_view(pos, now, session, und_bid=118.0):
    _, quotes = chain()
    quotes[LONG_OCC].update({"bid": 4.00, "ask": 4.10,
                             "market_at": now, "received_at": now})
    quotes[WING_OCC].update({"bid": 0.50, "ask": 0.55,
                             "market_at": now, "received_at": now})
    cal = calendar()
    cal["session"] = session
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


class TestExits(unittest.TestCase):
    def test_fixed_exit_at_fifth_session(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        now = "2026-10-30T15:56:00-04:00"
        out = ev(sid, exit_view(held_position(), now, "2026-10-30"),
                 session="2026-10-30", now=now)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertIn("planned_session_exit", out[0]["reason"])

    def test_fixed_no_exit_before_deadline(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        now = "2026-10-29T15:56:00-04:00"
        out = ev(sid, exit_view(held_position(), now, "2026-10-29"),
                 session="2026-10-29", now=now)
        self.assertEqual(out, [])

    def test_touch_exit_on_two_percent_recovery(self):
        sid = "aster_rec_rsi2_vertical_touch_a"
        pos = held_position(exit_rule="touch")
        now = "2026-10-28T10:15:00-04:00"
        out = ev(sid, exit_view(pos, now, "2026-10-28", und_bid=120.50),
                 session="2026-10-28", now=now)
        self.assertEqual(len(out), 1)
        self.assertIn("two_percent_recovery", out[0]["reason"])
        out2 = ev(sid, exit_view(pos, now, "2026-10-28", und_bid=119.00),
                  session="2026-10-28", now=now)
        self.assertEqual(out2, [])

    def test_touch_falls_back_to_deadline(self):
        sid = "aster_rec_rsi2_vertical_touch_b"
        pos = held_position(exit_rule="touch")
        now = "2026-10-30T15:56:00-04:00"
        out = ev(sid, exit_view(pos, now, "2026-10-30", und_bid=119.00),
                 session="2026-10-30", now=now)
        self.assertEqual(len(out), 1)

    def test_pre_expiry_guard_exit(self):
        sid = "aster_rec_vwap20_long_fixed_a"
        pos = held_position(exit_session="2026-11-20")
        now = "2026-11-12T15:46:00-05:00"
        out = ev(sid, exit_view(pos, now, "2026-11-12"),
                 session="2026-11-12", now=now)
        self.assertEqual(len(out), 1)
        self.assertIn("pre_expiry", out[0]["reason"])

    def test_assignment_exit(self):
        sid = "aster_rec_vwap20_long_touch_a"
        pos = held_position(exit_rule="touch")
        now = "2026-10-28T10:15:00-04:00"
        v = exit_view(pos, now, "2026-10-28")
        v["extra"]["assignment_alerts"] = {"SPY": {
            "assignment_alert": True, "verified": True,
            "source_sha256": "b" * 16, "received_at": now}}
        out = ev(sid, v, session="2026-10-28", now=now)
        self.assertEqual(len(out), 1)
        self.assertIn("assignment", out[0]["reason"])

    def test_european_settle_at_expiry(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        contracts, _ = chain()
        legs = [dict(contracts[0], ratio=1, exercise_style="european"),
                dict(contracts[1], ratio=-1, exercise_style="european")]
        legs[0]["expiry"] = legs[1]["expiry"] = "2026-10-28"
        pos = held_position()
        pos["metadata"]["legs"] = legs
        now = "2026-10-28T16:01:00-04:00"
        v = exit_view(pos, now, "2026-10-28")
        v["calendar"]["option_close_by_date"]["2026-10-28"] = \
            "2026-10-28T16:00:00-04:00"
        out = ev(sid, v, session="2026-10-28", now=now)
        self.assertEqual(len(out), 1)
        self.assertIn("official_PM_expiry", out[0]["reason"])

    def test_leaps_g4_deadline_and_event_exits(self):
        sid = "aster_tensor_leaps_a"
        contracts, quotes = leaps_chain()
        legs = [dict(contracts[0], ratio=1)]
        meta = {"legs": legs, "entry_spot": 5.0, "entry_session": SESSION,
                "exit_session": "2027-10-26",
                "expiry_exit_session": "2028-06-15", "exit_rule": "fixed",
                "signal_id": "OPT_TENSOR_LEAPS_A:EV1",
                "rule_id": "OPT_TENSOR_LEAPS_A", "G4_event_id": "EV1",
                "original_G4_exit_at": "2027-10-22T15:55:00-04:00"}
        pos = {"symbol": "PKG:TESTLEAPS", "qty": 1, "avg_price": 150.0,
               "opened_at": SESSION, "metadata": meta}
        now = "2027-10-22T15:56:00-04:00"
        v = exit_view(pos, now, "2027-10-22")
        v["options_quotes"] = {LEAPS_OCC: {
            "symbol": LEAPS_OCC, "feed": "opra", "bid": 2.00, "ask": 2.10,
            "bid_size": 5, "ask_size": 5, "market_at": now,
            "received_at": now}}
        v["calendar"]["session"] = "2027-10-22"
        out = ev(sid, v, session="2027-10-22", now=now)
        self.assertEqual(len(out), 1)
        self.assertIn("original_G4_saved_deadline", out[0]["reason"])
        # not due: deadline future, no exit event
        now2 = "2026-12-01T10:00:00-05:00"
        v2 = exit_view(pos, now2, "2026-12-01")
        v2["options_quotes"] = v["options_quotes"]
        v2["calendar"]["session"] = "2026-12-01"
        self.assertEqual(ev(sid, v2, session="2026-12-01", now=now2), [])
        # G4 exit event fires early exit
        v2["options_quotes"] = {LEAPS_OCC: {
            "symbol": LEAPS_OCC, "feed": "opra", "bid": 2.00, "ask": 2.10,
            "bid_size": 5, "ask_size": 5, "market_at": now2,
            "received_at": now2}}
        v2["extra"]["tensor_G4_exit_events"] = [{
            "event_id": "EV1", "qualified_native_G4": True,
            "exit_due": True, "source_sha256": "c" * 16,
            "available_at": "2026-11-30T12:00:00-05:00"}]
        out3 = ev(sid, v2, session="2026-12-01", now=now2)
        self.assertEqual(len(out3), 1)
        self.assertIn("original_G4_state_or_time", out3[0]["reason"])


class TestRegistryAndE2E(unittest.TestCase):
    def test_specs_match_archive_books(self):
        from desk3.aster_batch3 import SPECS
        self.assertEqual(sorted(SPECS), sorted(IDS))
        for sid, want in IDS.items():
            s = SPECS[sid]
            self.assertEqual(s["book"], want["book"], sid)
            self.assertEqual(s["risk_fraction"], want["risk"], sid)
            self.assertEqual(s["structure"], want["structure"], sid)

    def test_config_rows_and_inputs(self):
        from desk3.aster_batch3 import config_rows, INPUTS
        rows = {r["id"]: r for r in config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, have)
            self.assertEqual(have[sid]["inputs"], list(INPUTS))
            self.assertEqual(have[sid]["slice"]["capital_usd"], 10000.0)
            self.assertEqual(
                importlib.import_module(f"adapters3.{sid}").INPUTS, INPUTS)

    def test_unfed_registry(self):
        from desk3.aster_batch3 import register
        from desk3.registry import Registry
        reg = register(Registry())
        states = reg.fed_states(1_700_000_000.0)
        for sid in IDS:
            self.assertEqual(states[sid]["state"], "UNFED", sid)
            self.assertIn("options_chain", states[sid]["missing"], sid)

    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sid = "aster_rec_rsi2_vertical_fixed_a"
        out = ev(sid, entry_view_for(sid))
        self.assertEqual(len(out), 1)
        pkg = out[0]["symbol"]
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={pkg: 190.0})
        disp = Dispatcher(tmp, broker,
                          slices={sid: {"capital_usd": 10000.0,
                                        "cash_usd": 10000.0}})
        r = disp.process_intent(out[0], sid)
        self.assertEqual(r["status"], "filled")
        held = disp.slice_for(sid)["positions"]
        self.assertIn(pkg, held)
        pos = held_position()
        pos["symbol"] = pkg
        pos["qty"] = held[pkg]["qty"]
        now = "2026-10-30T15:56:00-04:00"
        exits = ev(sid, exit_view(pos, now, "2026-10-30"),
                   session="2026-10-30", now=now)
        self.assertEqual(len(exits), 1)
        broker.prices[pkg] = 350.0
        r2 = disp.process_intent(exits[0], sid)
        self.assertEqual(r2["status"], "filled")
        self.assertEqual(disp.slice_for(sid)["positions"], {})


if __name__ == "__main__":
    unittest.main()
