"""Aster batch 11 blockers (ASTER-B11): 3x SPY etf + 7x LINKUSDT crypto.

Oracle: staged archive source — r19_etf.py + etf_rules.json (SPY_HOLD_FULL
BUY_HOLD gross 1.0 {SPY:1}; SPY_MONTHLY MONTHLY gross 0.98/1.5 {SPY:1};
09:35-09:40 ET window, whole shares, sells before buys, no price exit for
buy-hold) and r19_crypto.py _signal + absorption/signals.py (shock =
vol>2*EMA20 incl., close<open, close<EMA50 incl.; confirm = close>open and
close>shock midpoint; >=300 bars; breakout = close>prior-20 high;
funding gates only the funding variants; fixed16 deadline exit survives
missing inputs; sizing fullcash net 10bp fee / volume1pct = 1% of
preceding bar volume). Fail-first: adapters/engine absent pre-build.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
ETF = ["aster_etf_spy_buy_hold", "aster_etf_spy_monthly_c098", "aster_etf_spy_monthly_m150"]
P = "aster_r19_linkusdt_"
ABS_FC, ABS_VC = P+"absorption_base_fixed16_fullcash", P+"absorption_base_fixed16_volume1pct"
NEG_FC, NEG_VC = P+"absorption_negative_funding_fixed16_fullcash", P+"absorption_negative_funding_fixed16_volume1pct"
NON_FC, NON_VC = P+"absorption_nonnegative_funding_fixed16_fullcash", P+"absorption_nonnegative_funding_fixed16_volume1pct"
BRK_FC = P+"breakout_base_fixed16_fullcash"
# VARIATION-ROSTERING-20261115 (2026-11-15): the two F4 _varsg forms
# of the absorption_negative_funding pair are rostered batch-11
# sleeves (desk3.aster_batch11.config_rows derives from the b11
# SPECS, which now carry them); they join CRYPTO so the registry,
# exit and fed-state loops cover them like their parents.
NEG_FC_SG, NEG_VC_SG = NEG_FC+"_varsg", NEG_VC+"_varsg"
CRYPTO = [ABS_FC, ABS_VC, NEG_FC, NEG_VC, NON_FC, NON_VC, BRK_FC,
          NEG_FC_SG, NEG_VC_SG]
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)

def flat_bars(px, n=130):
    return [{"t": f"2026-01-{(i%28)+1:02d}", "o": px, "h": px, "l": px, "c": px, "v": 1000} for i in range(n)]

def ev_etf(sid, barsmap, positions=None, now="2026-10-01T09:36:00", extra=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": now, "bars": barsmap, "positions": positions or [], "quotes": {}, "extra": extra or {}}
    return mod.evaluate(view, {"session": "2026-10-01", "now": now, "slice": {"capital_usd": 10000.0}})

def ev_etf2(sid, barsmap, positions=None, now="2026-10-01T09:36:00", extra=None):
    # WEIGHT-LAG-ACTIVE-20261031: aster_etf acts on the PREVIOUS
    # evaluation's targets. Clear stale pending state, then drive two
    # evaluations: the first computes weights and emits nothing, the
    # second acts on them. Returns (first, second).
    from desk3 import aster_etf
    aster_etf._PENDING_TARGETS.pop(sid, None)
    return (ev_etf(sid, barsmap, positions, now, extra),
            ev_etf(sid, barsmap, positions, now, extra))

def abs_bars(n=302):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i)); o = c = 20.0; h = 20.2; l = 19.8; v = 1000.0
        if i == n - 2: o, c, h, l, v = 20.0, 19.0, 20.0, 18.8, 5000.0
        if i == n - 1: o, c = 19.0, 19.6
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l, "c": c, "v": v})
    return out

def brk_bars(n=25, breakout=True, vol=100000.0):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        c = 11.0 if (breakout and i == n - 1) else 10.0
        out.append({"t": t.isoformat(), "o": 10.0, "h": 10.5, "l": 9.5, "c": c, "v": vol})
    return out

def drive(sid, brs=None, funding=-0.01, positions=None, cash=10000.0):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": NOW.isoformat(), "bars": {"LINKUSDT|4Hour": brs if brs is not None else abs_bars()},
            "funding": {"LINKUSDT": funding} if funding is not None else {},
            "positions": positions or [], "slice": {"capital_usd": 10000.0, "cash_usd": cash},
            "params": {}, "extra": {}, "session_fills": []}
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx", "state_dir": tempfile.mkdtemp()})

def pos(hours=20, qty=100.0):
    return [{"symbol": "LINKUSDT", "qty": qty, "avg_price": 20.0,
             "opened_at": (NOW - timedelta(hours=hours)).isoformat()}]

class TestEtfEntries(unittest.TestCase):
    def test_spy_entries(self):
        cases = {ETF[0]: 100, ETF[1]: 98, ETF[2]: 150}
        for sid, qty in cases.items():
            first, o = ev_etf2(sid, {"SPY": flat_bars(100.0)})
            self.assertEqual(first, [], sid)  # weight lag: first evaluation emits nothing
            self.assertEqual(len(o), 1, sid); self.assertEqual(o[0]["symbol"], "SPY")
            self.assertEqual(o[0]["qty"], qty, sid); self.assertEqual(o[0]["kind"], "entry")
    def test_buy_hold_never_exits(self):
        p = [{"symbol": "SPY", "qty": 50, "avg_price": 100.0, "entry_date": "2026-09-02"}]
        self.assertEqual(ev_etf(ETF[0], {"SPY": flat_bars(50.0)}, positions=p, now="2026-11-02T09:36:00"), [])
    def test_monthly_reduce_and_same_month_no_churn(self):
        p = [{"symbol": "SPY", "qty": 150, "avg_price": 100.0, "entry_date": "2026-09-02"}]
        first, o = ev_etf2(ETF[1], {"SPY": flat_bars(100.0)}, positions=p)
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        self.assertEqual(len(o), 1); self.assertEqual(o[0]["side"], "sell"); self.assertEqual(o[0]["qty"], 52)
        p[0]["entry_date"] = "2026-10-01"
        self.assertEqual(ev_etf(ETF[1], {"SPY": flat_bars(100.0)}, positions=p), [])
    def test_refusals_window_and_missing_bars(self):
        self.assertEqual(ev_etf(ETF[0], {"SPY": flat_bars(100.0)}, now="2026-10-01T10:00:00"), [])
        self.assertEqual(ev_etf(ETF[0], {}), [])
    def test_e2e_fake_broker_etf(self):
        from desk3.broker import FakeBroker
        b = FakeBroker(prices={"SPY": 100.0})
        first, o = ev_etf2(ETF[1], {"SPY": flat_bars(100.0)})
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        for i in o:
            b.get_order_by_client_id(b.submit_order(f"e-{i['intent_id']}", i["symbol"], i["side"], i["qty"], "market")["client_order_id"])
        self.assertEqual(b.get_positions(), {"SPY": 98.0})
        p = [{"symbol": "SPY", "qty": 98, "avg_price": 100.0, "entry_date": "2026-09-02"}]
        # Weight lag: the first November evaluation diffs the LAGGED
        # target (98, already held) and emits nothing; the recomputed
        # target (196 at $50) is acted on at the next evaluation.
        o2_first = ev_etf(ETF[1], {"SPY": flat_bars(50.0)}, positions=p, now="2026-11-02T09:36:00")
        self.assertEqual(o2_first, [])
        o2 = ev_etf(ETF[1], {"SPY": flat_bars(50.0)}, positions=p, now="2026-11-02T09:36:00")
        # target at $50 = 196 shares > held: buy more, not an exit; use price rise to force reduce-to-flat check via m150->c098 cross-check instead
        self.assertTrue(all(x["side"] == "buy" for x in o2))

class TestCryptoEntries(unittest.TestCase):
    def test_absorption_base_ignores_funding(self):
        for f in (None, -0.01, 0.005):
            o = drive(ABS_FC, funding=f); self.assertEqual(len(o), 1, f); self.assertEqual(o[0].kind, "enter")
    def test_absorption_fullcash_sizing(self):
        o = drive(ABS_FC); self.assertAlmostEqual(o[0].qty, 10000 * 0.999 / 19.6, places=4)
    def test_absorption_volume_cap(self):
        o = drive(ABS_VC); self.assertAlmostEqual(o[0].qty, 50.0)  # 1% of shock-bar volume 5000 (preceding bar)
    def test_negative_funding_gate(self):
        self.assertEqual(len(drive(NEG_FC, funding=-0.001)), 1)
        self.assertEqual(drive(NEG_FC, funding=0.0), [])
        self.assertEqual(drive(NEG_FC, funding=0.001), [])
        self.assertEqual(drive(NEG_FC, funding=None), [])
        o = drive(NEG_VC, funding=-0.001); self.assertAlmostEqual(o[0].qty, 50.0)
    def test_nonnegative_funding_gate(self):
        self.assertEqual(len(drive(NON_FC, funding=0.0)), 1)
        self.assertEqual(len(drive(NON_FC, funding=0.002)), 1)
        self.assertEqual(drive(NON_FC, funding=-0.001), [])
        self.assertEqual(drive(NON_FC, funding=None), [])
        o = drive(NON_VC, funding=0.0); self.assertAlmostEqual(o[0].qty, 50.0)
    def test_breakout_entry_and_refusals(self):
        o = drive(BRK_FC, brs=brk_bars(), funding=None)
        self.assertEqual(len(o), 1); self.assertAlmostEqual(o[0].qty, 10000 * 0.999 / 11.0, places=4)
        self.assertEqual(drive(BRK_FC, brs=brk_bars(breakout=False), funding=None), [])
        self.assertEqual(drive(BRK_FC, brs=brk_bars(n=20), funding=None), [])
        self.assertEqual(len(drive(BRK_FC, brs=brk_bars(), funding=0.005)), 1)  # funding never gates control
    def test_absorption_refusals(self):
        self.assertEqual(drive(ABS_FC, brs=abs_bars()[:200]), [])       # <300 warmup
        flat = [{"t": (NOW - timedelta(hours=4 * (302 - i))).isoformat(), "o": 20.0, "h": 20.2, "l": 19.8, "c": 20.0, "v": 1000.0} for i in range(302)]
        self.assertEqual(drive(ABS_FC, brs=flat), [])                    # no shock/confirm
        self.assertEqual(drive(ABS_FC, positions=pos(hours=1)), [])      # occupied: no new entry, no exit yet

class TestCryptoExits(unittest.TestCase):
    def test_fixed16_exit_all_arms(self):
        for sid in CRYPTO:
            o = drive(sid, positions=pos(hours=17)); self.assertEqual([x.kind for x in o], ["exit"], sid)
            self.assertEqual(drive(sid, positions=pos(hours=8)), [], sid)
    def test_deadline_survives_missing_inputs(self):
        for sid in CRYPTO:
            o = drive(sid, brs=[], funding=None, positions=pos(hours=100))
            self.assertEqual(len(o), 1, sid)
    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sid = BRK_FC; out = drive(sid, brs=brk_bars(), funding=None); self.assertEqual(len(out), 1)
        tmp = tempfile.mkdtemp(); broker = FakeBroker(prices={"LINKUSDT": 11.0})
        disp = Dispatcher(tmp, broker, slices={sid: {"capital_usd": 10000.0, "cash_usd": 10000.0}})
        def as_dict(i, n):
            return {"intent_id": f"{sid}-e2e-{n}", "kind": "entry" if i.kind == "enter" else "exit",
                    "symbol": i.symbol, "side": i.side, "qty": i.qty, "order_type": "market",
                    "price_hint": i.price_hint}
        r = disp.process_intent(as_dict(out[0], 1), sid); self.assertEqual(r["status"], "filled")
        held = disp.slice_for(sid)["positions"]; self.assertIn("LINK/USD", held)  # BLOCKED-EXIT-20261029: broker dialect at the door
        ex = drive(sid, brs=brk_bars(), funding=None, positions=pos(hours=20, qty=held["LINK/USD"]["qty"]))
        r2 = disp.process_intent(as_dict(ex[0], 2), sid); self.assertEqual(r2["status"], "filled")
        self.assertEqual(disp.slice_for(sid)["positions"], {})

class TestRegistry(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.aster_batch11 import config_rows
        rows = {r["id"]: r for r in config_rows()}
        # GOING-LIVE-VARIATIONS-20261115: the two CONV-29 r19
        # varhx2 variation sleeves joined the batch11 registry
        # (hold 32 against the parents' 16); the registry census
        # below carries them beside ETF + CRYPTO.
        VARHX2 = ["aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2",
                  "aster_r19_linkusdt_absorption_base_fixed16_volume1pct_varhx2"]
        self.assertEqual(sorted(rows), sorted(ETF + CRYPTO + VARHX2))
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in ETF + CRYPTO + VARHX2:
            self.assertIn(sid, have); self.assertEqual(have[sid]["inputs"], rows[sid]["inputs"])
            self.assertEqual(have[sid]["slice"]["capital_usd"], 10000.0)
            self.assertEqual(tuple(importlib.import_module(f"adapters3.{sid}").INPUTS), tuple(rows[sid]["inputs"]))
    def test_unfed_when_funding_missing(self):
        from desk3.registry import Registry
        reg = Registry()
        reg.register_producer("bars", ("bars",), 14400); reg.register_producer("binance_funding", ("funding",), 28800)
        reg.register_producer("broker_readback", ("positions",), 900)
        for sid in CRYPTO: reg.register_sleeve(sid, ("bars", "funding", "positions"))
        reg.mark_produced("bars", ts=1000.0); reg.mark_produced("broker_readback", ts=1000.0)
        fed = reg.fed_states(now=1000.0)
        for sid in CRYPTO: self.assertEqual(fed[sid]["state"], "UNFED", sid)
        reg.mark_produced("binance_funding", ts=1000.0)
        fed = reg.fed_states(now=1000.0)
        for sid in CRYPTO: self.assertEqual(fed[sid]["state"], "FED", sid)

if __name__ == "__main__":
    unittest.main()
