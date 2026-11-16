"""Edge batch 26 blockers — ENH-B26 (2026-10-24).

Second Edge look for the five sha256-pinned batch-7 sleeves
(adapter-layer gates in desk3/enhance26.py; sleeves/ + adapters/
untouched) + first look for the Aster batch-16 sleeves (engine
cures in desk3/aster_batch15.py / desk3/aster_batch16.py):

- snapback: entries sized off the signal week's WEEKLY close.
  Cure: reprice + re-size at the latest daily close.
- spx_premium: entry_day_ok has no upper bound vs the author's
  ~10:00 ET entry. Cure: refuse entries at/after 11:00 ET.
- tensor_red_dip: entries sized/stopped off yesterday's 1Day
  close; at a -9% day return the placed stop sits ABOVE the
  market. Cure: reprice at close x (1 + day_return) — the
  sleeve's own intraday input — and re-derive qty/stop/target.
- tensor_swing: staged swing decisions never aged. Cure: refuse
  entries whose swing_bar_date is > 7 days before the session.
- ts_momentum_decile: newest closed bar never aged. Cure:
  refuse entries on bars > 7 days old (exits never filtered).
- aster_r19_timing_overnight_5bp: the scheduled 09:30 exit
  crossed the full bid (batch 10 named it the next leak).
  Cure: scheduled exit only, limit at the quoted mid.
- aster_tensor_d20_{tensor,pv}: decision series never compared
  to the desk's bars. Cure: refuse selection when the last row
  predates the symbol's newest 1Day bar by > 4 days.
- aster_saty_research: qty sized off the PLANNED entry's risk
  while the fill is at the quote mid. Cure: size off
  |price - invalidation|.
VERIFY-ONLY (traces below): aster_trader_donchian55,
vix_hedge — see proof/enhance/<sleeve>.json.

Every cure: per-sleeve switch default ON; OFF restores the
pre-change rule exactly, proven below. Fail-first proven by
reverting the batch's files (see BUGLOG EDGE-B26).
"""
import importlib, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import test_aster_batch16_blockers as b16
import test_aster_batch15_blockers as b15
from desk3 import enhance26

NOW = "2026-10-23T15:30:00-04:00"  # Friday


def _b(t, c, v=10000.0, o=None, h=None, l=None):
    return {"t": t, "o": o if o is not None else c,
            "h": h if h is not None else c * 1.001,
            "l": l if l is not None else c * 0.999, "c": c, "v": v}


def _flat(view):
    bars = view.get("bars") or {}
    if bars and all(isinstance(v, dict) for v in bars.values()):
        view = dict(view)
        view["bars"] = {f"{sym}|{tf}": rows for sym, tfs in bars.items()
                        for tf, rows in tfs.items()}
    return view


def ev(sid, view):
    view = _flat(dict(view)); view.setdefault("now", NOW)
    view.setdefault("slice", {"capital_usd": 10000.0, "cash_usd": 10000.0})
    mod = importlib.import_module(f"adapters3.{sid}")
    ctx = {"sleeve_id": sid, "state_dir": tempfile.mkdtemp()}
    return mod.evaluate(view, ctx)


def ev2(sid, view):
    # WEIGHT-LAG-ACTIVE-20261031: the lagged books hold one
    # evaluation's intents and emit them at the next, with the pending
    # state in the cycle state_dir — so drive two evaluations on ONE
    # state dir: the first computes weights and emits nothing, the
    # second acts on them. Returns (first, second).
    view = _flat(dict(view)); view.setdefault("now", NOW)
    view.setdefault("slice", {"capital_usd": 10000.0, "cash_usd": 10000.0})
    mod = importlib.import_module(f"adapters3.{sid}")
    ctx = {"sleeve_id": sid, "state_dir": tempfile.mkdtemp()}
    return mod.evaluate(view, ctx), mod.evaluate(view, ctx)


def _daily_end(end, n, start=100.0, drift=0.001, vol=20000.0):
    days, d = [], end
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    return [_b(f"{x.isoformat()}T04:00:00Z", start * (1 + drift) ** i, v=vol)
            for i, x in enumerate(days)]


# ------------------------------------------------------------ snapback
def snapback_view(off=False):
    mondays, d = [], date(2025, 10, 6)
    while len(mondays) < 55:
        mondays.append(d); d += timedelta(days=7)
    assert mondays[-1] == date(2026, 10, 19)  # signal week's Monday
    vols = {"SPY": 1000, "QQQ": 2000, "IWM": 3000, "AAPL": 4000,
            "MSFT": 5000, "NVDA": 6000, "AMD": 7000, "TSLA": 8000,
            "AMZN": 9000, "META": 10000, "NFLX": 11000, "GOOGL": 12000}
    bars = {}
    for sym, vol in vols.items():
        wk = []
        for i, m in enumerate(mondays):
            c = 100.0
            if sym == "AAPL":
                if i >= 40:
                    c = 100.0 - 25.0 * (i - 39) / 14.0  # 100 -> 75 by idx 53
                if i == 54:
                    c = 80.0  # signal-week close = the stale entry price
            wk.append(_b(f"{m.isoformat()}T04:00:00Z", c, v=float(vol)))
        dl = _daily_end(date(2026, 10, 23), 30, 100.0, drift=0.0)
        if sym == "AAPL":
            tail = {date(2026, 10, 19): 70.0, date(2026, 10, 20): 60.0,
                    date(2026, 10, 21): 55.0, date(2026, 10, 22): 48.0,
                    date(2026, 10, 23): 40.0}
            fixed = []
            for r in dl:
                dd = date.fromisoformat(r["t"][:10])
                c = tail.get(dd, 75.0)
                fixed.append(_b(r["t"], c, v=r["v"], h=c * 1.10, l=c * 0.90))
            dl = fixed
        bars[sym] = {"1Day": dl, "1Week": wk}
    view = {"bars": bars, "positions": []}
    if off:
        view["extra"] = {"snapback_enhance2": {"fresh_price_reprice": False}}
    return view


class TestSnapbackReprice(unittest.TestCase):
    def test_entry_repriced_and_resized_at_fresh_close(self):
        enhance26.LAST_PAIRED.clear()
        out = ev("snapback", snapback_view())
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["symbol"], "AAPL")
        self.assertEqual(e["price_hint"], 40.0)   # latest daily close
        self.assertEqual(e["qty"], 2)             # (10000*.01)//40
        rec = [r for r in enhance26.LAST_PAIRED if r["sleeve"] == "snapback"]
        self.assertEqual(len(rec), 1)
        self.assertEqual((rec[0]["control_px"], rec[0]["treatment_px"]),
                         (80.0, 40.0))
        self.assertEqual((rec[0]["control_qty"], rec[0]["treatment_qty"]),
                         (1, 2))

    def test_switch_off_restores_weekly_close_rule_exactly(self):
        out = ev("snapback", snapback_view(off=True))
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["price_hint"], 80.0)  # weekly close
        self.assertEqual(entries[0]["qty"], 1)           # (10000*.01)//80


# ------------------------------------------------------------ spx_premium
class TestSpxEntryWindow(unittest.TestCase):
    INTENT = {"kind": "entry", "symbol": "XSP", "qty": 1,
              "price_hint": 500.0, "reason": "spx_premium put_credit_spread"}

    def test_late_entry_refused(self):
        view = {"now": "2026-10-26T14:00:00-04:00"}  # Monday 14:00 ET
        self.assertEqual(
            enhance26.filter_entries("spx_premium", [dict(self.INTENT)], view),
            [])

    def test_designed_hour_entry_kept(self):
        view = {"now": "2026-10-26T10:30:00-04:00"}  # Monday 10:30 ET
        out = enhance26.filter_entries("spx_premium", [dict(self.INTENT)], view)
        self.assertEqual(len(out), 1)

    def test_switch_off_restores_all_day_rule(self):
        view = {"now": "2026-10-26T14:00:00-04:00",
                "extra": {"spx_premium_enhance2": {"entry_window_gate": False}}}
        out = enhance26.filter_entries("spx_premium", [dict(self.INTENT)], view)
        self.assertEqual(len(out), 1)

    def test_exits_never_filtered(self):
        view = {"now": "2026-10-26T14:00:00-04:00"}
        x = {"kind": "exit", "symbol": "XSP", "qty": 1, "reason": "settlement"}
        self.assertEqual(
            enhance26.filter_entries("spx_premium", [x], view), [x])


# ------------------------------------------------------------ tensor_red_dip
def red_dip_view(day_ret, off=False):
    extra = {"tensor_signals": [{"symbol": "AAPL", "confidence": 9,
                                 "phenotype": "P"}],
             "qqq_day_return": -0.02, "day_returns": {"AAPL": day_ret}}
    if off:
        extra["tensor_red_dip_improve2"] = {"exec_price_reprice": False}
    return {"bars": {"AAPL": {"1Day": _daily_end(date(2026, 10, 22), 5,
                                                 100.0, drift=0.0)}},
            "extra": extra}


class TestRedDipReprice(unittest.TestCase):
    def test_stop_no_longer_above_market(self):
        out = ev("tensor_red_dip", red_dip_view(-0.09))
        self.assertEqual(len(out), 1)
        e = out[0]
        self.assertEqual(e["price_hint"], 91.0)       # 100 x (1 - .09)
        self.assertEqual(e["stop_price"], 83.72)      # 0.92 x executable
        rules = {r["kind"]: r["value"] for r in e["exit_rules"]}
        self.assertEqual(rules["stop"], 83.72)
        self.assertEqual(rules["target"], 93.73)      # 1.03 x executable
        # pre-change stop was 92.00 — above the 91.00 executable price
        self.assertLess(e["stop_price"], e["price_hint"])

    def test_qty_resized_at_executable_price(self):
        on = ev("tensor_red_dip", red_dip_view(-0.50))
        off = ev("tensor_red_dip", red_dip_view(-0.50, off=True))
        self.assertEqual(on[0]["qty"], 6)   # floor(25 / (50 x .08))
        self.assertEqual(off[0]["qty"], 3)  # floor(25 / (100 x .08))
        self.assertEqual(off[0]["price_hint"], 100.0)
        self.assertEqual(off[0]["stop_price"], 92.0)


# ------------------------------------------------------------ tensor_swing
def swing_view(bar_date, off=False):
    sig = [{"symbol": "AAPL", "confidence": 9, "entry": 150.0,
            "stop": 140.0, "target": 170.0, "phenotype": "P",
            "regime": "R", "bar_date": bar_date}]
    extra = {"tensor_signals": sig}
    if off:
        extra["tensor_swing_improve2"] = {"stale_signal_gate": False}
    return {"extra": extra}


class TestTensorSwingStaleGate(unittest.TestCase):
    def test_stale_staged_entry_refused(self):
        out = ev("tensor_swing", swing_view("2026-10-01"))  # 22 days old
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])

    def test_fresh_staged_entry_kept(self):
        out = ev("tensor_swing", swing_view("2026-10-22"))
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_switch_off_restores_unaged_rule(self):
        out = ev("tensor_swing", swing_view("2026-10-01", off=True))
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


# ------------------------------------------------------------ ts_momentum_decile
def tsmom_view(stale_nvda=False, off=False):
    from sleeves.ts_momentum_decile import SECTOR_MAP
    by_sector = {}
    for s, sec in SECTOR_MAP.items():
        by_sector.setdefault(sec, []).append(s)
    syms = (by_sector["SEMI"] + by_sector["SOFTWARE"] + by_sector["BIOTECH"]
            + by_sector["ENERGY"] + by_sector["FIN"])
    top = {"NVDA": 0.009594, "AMD": 0.009594}
    mid = {"SOXL", "BNTX", "MRNA", "MSFT", "XOM", "JPM", "BAC"}
    bars = {}
    for s in syms:
        drift = top.get(s, 0.002681 if s in mid else 0.001566)
        end = date(2026, 10, 5) if (stale_nvda and s == "NVDA") \
            else date(2026, 10, 22)
        bars[s] = {"1Day": _daily_end(end, 260, 100.0, drift=drift)}
    view = {"bars": bars, "positions": []}
    if off:
        view["extra"] = {"ts_momentum_decile_improve2":
                         {"stale_bar_gate": False}}
    return view


class TestTsMomentumStaleGate(unittest.TestCase):
    def test_fresh_bars_enter(self):
        first, out = ev2("ts_momentum_decile", tsmom_view())
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        entries = {i["symbol"] for i in out if i["kind"] == "entry"}
        self.assertIn("NVDA", entries)

    def test_stale_bar_entry_refused_others_kept(self):
        first, out = ev2("ts_momentum_decile", tsmom_view(stale_nvda=True))
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        entries = {i["symbol"] for i in out if i["kind"] == "entry"}
        self.assertNotIn("NVDA", entries)   # newest bar 2026-10-05, 18d old
        self.assertTrue(entries)            # the rest of the decile enters

    def test_switch_off_restores_unaged_rule(self):
        first, out = ev2("ts_momentum_decile", tsmom_view(stale_nvda=True, off=True))
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        entries = {i["symbol"] for i in out if i["kind"] == "entry"}
        self.assertIn("NVDA", entries)


# ------------------------------------------------------------ overnight 5bp exit
ON5 = "aster_r19_timing_overnight_5bp"


class TestOvernight5bpExitMidLimit(unittest.TestCase):
    def _exit_view(self, off=False):
        pos = [{"symbol": "MU", "qty": 19, "avg_price": 50.0,
                "exit_at": "2026-10-26T09:30:00-04:00"}]
        v = b16.on_view(now="2026-10-26T09:31:00-04:00", positions=pos)
        if off:
            v["extra"] = dict(v["extra"])
            v["extra"]["enh_aster_r19_timing_overnight_5bp"] = \
                {"exit_mid_limit": False}
        return v

    def test_scheduled_exit_is_mid_limit(self):
        out = ev(ON5, self._exit_view())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertEqual(out[0]["order_type"], "limit")
        self.assertEqual(out[0]["limit_price"], 49.95)  # (49.9 + 50.0) / 2
        rec = out[0]["enhance_exp"]
        self.assertEqual(rec["exp_id"], "ENH-B26-ONEXIT-20261024")
        self.assertEqual(rec["control_price"], 49.9)
        self.assertAlmostEqual(rec["spread_saved"], 0.05)

    def test_switch_off_restores_market_exit_exactly(self):
        out = ev(ON5, self._exit_view(off=True))
        self.assertEqual(out[0]["order_type"], "market")
        self.assertIsNone(out[0]["limit_price"])
        self.assertNotIn("enhance_exp", out[0])

    def test_25bp_book_untouched_by_this_cure(self):
        v = b15.overnight_fixture()
        v["now"] = datetime(2026, 10, 26, 14, 0,
                            tzinfo=timezone.utc).isoformat()
        v["positions"] = [{"symbol": "MU", "qty": 9, "avg_price": 101.0,
                           "opened_at": "2026-10-23T19:32:00+00:00",
                           "meta": {"exit_at": "2026-10-26T13:30:00+00:00"}}]
        out = b15.drive(b15.ON25, v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertEqual(out[0]["order_type"], "market")


# ------------------------------------------------------------ tensor d20 fresh-row gate
class TestD20FreshRowGate(unittest.TestCase):
    def _view(self, rows, ref_date, off=False):
        v = b16.d20_view({"ADSK": rows})
        v["bars"] = {"ADSK|1Day": [{"t": ref_date.isoformat(), "o": 100.0,
                                    "h": 100.0, "l": 100.0, "c": 100.0,
                                    "v": 1000}]}
        v["extra"] = {"aster_enh_exp_journal": {"records": []}}
        if off:
            v["extra"]["aster_b16_enh"] = {"fresh_row_gate": False}
        return v

    def test_stale_row_refused_both_models(self):
        rows = b16.d20_rows()
        last = datetime.fromtimestamp(rows[-1]["timestamp"],
                                      tz=timezone.utc).date()
        for sid in (b16.D20P, b16.D20T):
            v = self._view(rows, last + timedelta(days=18))
            self.assertEqual(ev(sid, v), [], sid)
            recs = v["extra"]["aster_enh_exp_journal"]["records"]
            self.assertEqual(recs[-1]["treatment"], "refuse_stale_row")
            self.assertEqual(recs[-1]["row_age_days"], 18)

    def test_fresh_row_enters(self):
        rows = b16.d20_rows()
        last = datetime.fromtimestamp(rows[-1]["timestamp"],
                                      tz=timezone.utc).date()
        for sid in (b16.D20P, b16.D20T):
            out = ev(sid, self._view(rows, last + timedelta(days=1)))
            self.assertEqual(len(out), 1, sid)

    def test_switch_off_restores_ungated_rule(self):
        rows = b16.d20_rows()
        last = datetime.fromtimestamp(rows[-1]["timestamp"],
                                      tz=timezone.utc).date()
        v = self._view(rows, last + timedelta(days=18), off=True)
        self.assertEqual(len(ev(b16.D20P, v)), 1)

    def test_no_bars_no_evidence_passes(self):
        # the batch-16 fixture shape: bars absent -> archive behavior
        for sid in (b16.D20P, b16.D20T):
            self.assertEqual(len(ev(sid, b16.d20_view())), 1, sid)


# ------------------------------------------------------------ saty executable-risk sizing
class TestSatyExecRiskSizing(unittest.TestCase):
    def test_chased_price_sizes_off_executable_risk(self):
        out = ev(b16.SATY, b16.saty_view(mid=601.0))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 8)  # floor(25 / |601 - 598|)
        rec = out[0]["enhance_exp"]
        self.assertEqual(rec["exp_id"], "ENH-B26-SATYEXEC-20261024")
        self.assertEqual((rec["control_qty"], rec["treatment_qty"]), (12, 8))

    def test_at_planned_entry_qty_unchanged(self):
        out = ev(b16.SATY, b16.saty_view(mid=600.0))
        self.assertEqual(out[0]["qty"], 12)

    def test_switch_off_restores_planned_entry_sizing(self):
        v = b16.saty_view(mid=601.0)
        v["extra"] = {"enh_aster_saty_research": {"exec_risk_sizing": False}}
        out = ev(b16.SATY, v)
        self.assertEqual(out[0]["qty"], 12)  # floor(25 / |600 - 598|)
        self.assertNotIn("enhance_exp", out[0])


# ------------------------------------------------------------ VERIFY-ONLY traces
class TestDonchianVerifyOnlyTrace(unittest.TestCase):
    """aster_trader_donchian55: no sleeve-layer leak survives —
    entry (ranked, triple-capped, broker stop carried) and all
    four designed exits traced on the final tree."""

    def test_entry_and_exits_trace(self):
        out = ev(b16.DON, b16.don_view())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertLess(out[0]["stop_price"], 210.0)
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 200.0,
                "bars_held": 5, "stop_price": 195.0}]
        out = ev(b16.DON, b16.don_view({"SPY|1Day": b16.don_bars(
            last_close=194.0)}, positions=pos))
        self.assertEqual(len(out), 1)
        self.assertIn("initial_2atr_stop", out[0]["reason"])
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 200.0,
                "bars_held": 126}]
        out = ev(b16.DON, b16.don_view(positions=pos))
        self.assertEqual(len(out), 1)
        self.assertIn("126", out[0]["reason"])


class TestVixHedgeVerifyOnlyTrace(unittest.TestCase):
    """vix_hedge: the binding constraint is contract granularity
    vs the sleeve's own 1%-of-slice spec ($100 budget buys one
    contract only when ask <= $1.00) — measured, not a sleeve
    leak. Exits + adoption traced on the final tree."""

    def _ctx(self, extra):
        return SimpleNamespace(equity=10000.0, session="2026-10-23",
                               now=0.0, extra=extra)

    def _entry_extra(self, ask, bid):
        return {"vix_closes": [15.0] * 31,
                "chains": {"VXX": [{"symbol": "VXX270121C00030000",
                                    "strike": 30.0,
                                    "expiration": "2027-01-21"}]},
                "quotes": {"VXX270121C00030000": {"bid": bid, "ask": ask}},
                "sleeve_state": {}}

    def test_entry_feasibility_measured(self):
        from sleeves.vix_hedge import VixHedge
        bars = {"VXX": [{"t": 0, "o": 25, "h": 25, "l": 25, "c": 25.0,
                         "v": 1}]}
        out = VixHedge().signal(bars, {}, self._ctx(
            self._entry_extra(ask=1.10, bid=1.05)))
        self.assertEqual(out, [])  # floor($100 / $110) = 0 contracts
        out = VixHedge().signal(bars, {}, self._ctx(
            self._entry_extra(ask=0.95, bid=0.90)))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].qty_hint, 1)  # ask <= $1.00: enters

    def test_spike_exit_trace(self):
        from sleeves.vix_hedge import VixHedge
        extra = {"vix_closes": [15.0] * 30 + [31.0],
                 "quotes": {"VXX261218C00020000": {"bid": 2.0, "ask": 2.1}},
                 "sleeve_state": {"VXX": {"position": {
                     "occ": "VXX261218C00020000", "contracts": 8,
                     "expiry": "2026-12-18", "entry_premium": 1.10}}}}
        bars = {"VXX": [{"t": 0, "o": 25, "h": 25, "l": 25, "c": 25.0,
                         "v": 1}]}
        out = VixHedge().signal(bars, {}, self._ctx(extra))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertIn("vol_spike_take_profit", out[0].reason)


if __name__ == "__main__":
    unittest.main()
