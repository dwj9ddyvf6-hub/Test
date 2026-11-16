"""Edge batch 14 blockers — ENH2-* (2026-10-24), second Edge look over
aurelia_ndx, beatendown, bilbo_options, capitulation,
capitulation_options, confluence, donchian, donchian_crypto,
earnings_buyback, em_1587; VERIFY-ONLY evidence drives for
daily_cyan_gbm + bb_rsi_divergence.

All cures live at the adapter layer (desk3/enhance14.py + adapters3
wiring; adapters/capitulation.py tranche-plan feed) — the sha-pinned
strategy files are never edited. Each gate: default ON, OFF restores
the pre-change rule exactly, paired records on
desk3.enhance14.LAST_PAIRED / adapters.capitulation.LAST_PAIRED.
Fail-first: every treatment test fails on the pre-cure tree (no
enhance14 wiring / no plan feed).
"""
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import test_port_batch1_blockers as b1  # noqa: E402
from desk3 import enhance14  # noqa: E402

NOW = "2026-10-23T14:00:00-04:00"
SLICE = {"capital_usd": 10000.0, "cash_usd": 10000.0}


def ev(sid, view, ctx=None):
    ctx = ctx or {"sleeve_id": sid, "state_dir": tempfile.mkdtemp(),
                  "cycle_id": "fx14"}
    return importlib.import_module(f"adapters3.{sid}").evaluate(view, ctx)


def view(bars=None, params=None, positions=None, options=None, now=NOW):
    return {"now": now, "bars": bars or {}, "positions": positions or [],
            "params": params or {}, "slice": dict(SLICE),
            "options": options or {}}


def paired(sid):
    return [r for r in enhance14.LAST_PAIRED if r["sleeve"] == sid]


# ------------------------------------------------------------- aurelia_ndx
class TestAureliaCompletePlan(unittest.TestCase):
    def setUp(self):
        import sleeves.aurelia_ndx as strat
        strat._EMITTED_SESSIONS.clear()
        enhance14.LAST_PAIRED.clear()
        self.dir = tempfile.mkdtemp()

    def _bars(self, with_bil=True):
        bars = {("GLD", "1Day"): b1.flat(2, 200.0),
                ("QQQ", "1Day"): b1.flat(2, 500.0),
                ("TQQQ", "1Day"): b1.flat(2, 50.0)}
        if with_bil:
            bars[("BIL", "1Day")] = b1.flat(2, 90.0)
        return {f"{s}|{tf}": rows for (s, tf), rows in bars.items()}

    def _view(self, with_bil=True, extra_over=None):
        extra = {"exposures": {"ndx": 0.5, "gold": 0.0}}
        if extra_over:
            extra.update(extra_over)
        return view(bars=self._bars(with_bil),
                    params={"extra": extra})

    def _ctx(self):
        return {"sleeve_id": "aurelia_ndx", "state_dir": self.dir,
                "cycle_id": "fx14"}

    def test_complete_bars_emit_full_plan(self):
        out = ev("aurelia_ndx", self._view(True), self._ctx())
        self.assertEqual(sorted(i["symbol"] for i in out), ["BIL", "QQQ"])

    def test_missing_leg_bar_defers_whole_plan_then_completes(self):
        out = ev("aurelia_ndx", self._view(False), self._ctx())
        self.assertEqual(out, [])  # pre-change: QQQ subset emitted + frozen
        recs = [r for r in paired("aurelia_ndx")
                if r["treatment_decision"] == "refuse"]
        self.assertTrue(recs)
        self.assertEqual(recs[-1]["missing_bars"], ["BIL"])
        # freeze NOT consumed: with complete bars the plan still fires
        out2 = ev("aurelia_ndx", self._view(True), self._ctx())
        self.assertEqual(sorted(i["symbol"] for i in out2), ["BIL", "QQQ"])

    def test_switch_off_restores_partial_emit(self):
        out = ev("aurelia_ndx",
                 self._view(False, {"aurelia_ndx_enh2":
                                    {"complete_plan": False}}),
                 self._ctx())
        self.assertEqual([i["symbol"] for i in out], ["QQQ"])


# -------------------------------------------------------------- beatendown
class TestBeatendownReprice(unittest.TestCase):
    R1 = {"E_WEEK_BIGRANGE": True, "X_SECT_LEAD": True, "Q_LAM_HIGH": True}

    def _view(self, extra_over=None):
        qual = {"symbol": "BEAT", "close": 50.0,
                "wcloses": [100.0] * 52, "feat": dict(self.R1)}
        extra = {"qualifiers": [qual],
                 "vix": [20.0, 19.0, "2026-10-23", "fixture"]}
        if extra_over:
            extra.update(extra_over)
        bars = {"BEAT|1Day": b1.bars_for([50.0] * 9 + [60.0])}
        return view(bars=bars, params={"extra": extra})

    def test_sizes_off_current_bar_not_signal_week_close(self):
        out = ev("beatendown", self._view())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 5)        # 3000 // 60
        self.assertEqual(out[0]["price_hint"], 60.0)
        rec = paired("beatendown")[-1]
        self.assertEqual((rec["control_px"], rec["treatment_px"]),
                         (50.0, 60.0))
        self.assertEqual((rec["control_qty"], rec["treatment_qty"]), (6, 5))

    def test_switch_off_restores_qualifier_close_sizing(self):
        out = ev("beatendown", self._view(
            {"beatendown_enh2": {"current_bar_pricing": False}}))
        self.assertEqual((out[0]["qty"], out[0]["price_hint"]), (6, 50.0))


# -------------------------------------------------------------- confluence
class TestConfluenceDedupe(unittest.TestCase):
    R1 = {"E_WEEK_BIGRANGE": True, "X_SECT_LEAD": True, "Q_LAM_HIGH": True}
    R2 = {"E_ENR_EXTENSION": True, "X_DOLLAR_WEAK": True, "Q_LAM_HIGH": True}

    def _view(self, extra_over=None):
        qual = {"symbol": "CONF", "close": 50.0,
                "feat": {**self.R1, **self.R2}}
        extra = {"qualifiers": [qual, dict(qual)],
                 "vix": [20.0, 19.0, "2026-10-23", "fixture"]}
        if extra_over:
            extra.update(extra_over)
        return view(params={"extra": extra})

    def test_duplicate_qualifier_enters_once(self):
        out = ev("confluence", self._view())
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)

    def test_switch_off_restores_duplicate_entries(self):
        out = ev("confluence", self._view(
            {"confluence_enh2": {"dedupe_entries": False}}))
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 2)


# --------------------------------------------------------------- donchian
class TestDonchianChaseGate(unittest.TestCase):
    def _view(self, closes, highs, lows, extra_over=None):
        bars = b1.bars_for(closes, highs=highs, lows=lows,
                           vols=[1000.0] * len(closes))
        extra = {}
        if extra_over:
            extra.update(extra_over)
        return view(bars={"TEST|1Day": bars},
                    params={"universe": ["TEST"], "extra": extra})

    def test_chase_beyond_stop_distance_refused(self):
        v = self._view([100.0] * 29 + [120.0], [101.0] * 29 + [121.0],
                       [99.0] * 29 + [119.0])
        self.assertEqual(ev("donchian", v), [])
        rec = paired("donchian")[-1]
        self.assertEqual(rec["treatment_decision"], "refuse")
        self.assertGreater(rec["chase_premium"], 2 * rec["atr"])

    def test_switch_off_restores_chase_entry(self):
        v = self._view([100.0] * 29 + [120.0], [101.0] * 29 + [121.0],
                       [99.0] * 29 + [119.0],
                       {"donchian_enh2": {"chase_gate": False}})
        out = ev("donchian", v)
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_ordinary_breakout_still_enters(self):
        v = self._view([100.0] * 29 + [105.0], [101.0] * 29 + [106.0],
                       [99.0] * 30)
        out = ev("donchian", v)
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


# --------------------------------------------------------- stale-bar gates
def _spaced_bars(end_iso, n, span_s, px=100.0):
    end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    out = []
    for i in range(n):
        t = end - timedelta(seconds=span_s * (n - 1 - i))
        out.append({"t": t.isoformat().replace("+00:00", "Z"),
                    "o": px, "h": px + 1, "l": px - 1, "c": px,
                    "v": 1000.0})
    return out


class TestDonchianCryptoStaleGate(unittest.TestCase):
    def _bars(self, end_iso):
        bars = _spaced_bars(end_iso, 45, 900)
        for b in bars[:-1]:
            b.update({"o": 100.0, "h": 101.0, "l": 99.0, "c": 100.0,
                      "v": 10.0})
        # modest breakout (premium 3 < 2xATR): the sleeve's own ENH1
        # chase gate must not refuse this fixture — ENH2 is the gate
        # under test here.
        bars[-1].update({"o": 100.0, "h": 105.0, "l": 103.0, "c": 104.0,
                         "v": 10.0})
        return bars

    def _view(self, end_iso, extra_over=None):
        extra = {}
        if extra_over:
            extra.update(extra_over)
        return view(bars={"SOLUSD|15Min": self._bars(end_iso)},
                    params={"extra": extra},
                    now="2026-10-23T18:00:00Z")

    def test_stale_breakout_refused(self):
        # last bar started 3h before now (span 900s): feed is dead
        v = self._view("2026-10-23T14:45:00Z")
        self.assertEqual(ev("donchian_crypto", v), [])

    def test_fresh_breakout_enters(self):
        v = self._view("2026-10-23T17:45:00Z")
        out = ev("donchian_crypto", v)
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_switch_off_restores_stale_entry(self):
        v = self._view("2026-10-23T14:45:00Z",
                       {"donchian_crypto_enh2": {"stale_bar_gate": False}})
        out = ev("donchian_crypto", v)
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


class TestStaleGateUnits(unittest.TestCase):
    """Filter-level drives for the remaining stale gates + em_1587
    (the gate is the unit under test; entry production for these
    sleeves is oracle-covered by the port suites)."""

    def _entry(self, sid, symbol, **kw):
        it = {"kind": "entry", "symbol": symbol, "qty": 1,
              "price_hint": 100.0, "side": "buy", "order_type": "market",
              "reason": f"{sid} entry"}
        it.update(kw)
        return it

    def test_bilbo_stale_5min_refused_fresh_passes_exit_untouched(self):
        stale = _spaced_bars("2026-10-23T14:55:00Z", 10, 300, 150.0)
        v = view(bars={"NVDA|5Min": stale}, now="2026-10-23T18:00:00Z")
        self.assertEqual(enhance14.filter_entries(
            "bilbo_options", [self._entry("bilbo_options", "NVDA")], v), [])
        exit_it = {"kind": "exit", "symbol": "NVDA", "qty": 1}
        self.assertEqual(enhance14.filter_entries(
            "bilbo_options", [exit_it], v), [exit_it])
        fresh = _spaced_bars("2026-10-23T17:55:00Z", 10, 300, 150.0)
        v2 = view(bars={"NVDA|5Min": fresh}, now="2026-10-23T18:00:00Z")
        self.assertEqual(len(enhance14.filter_entries(
            "bilbo_options", [self._entry("bilbo_options", "NVDA")], v2)), 1)

    def test_capopt_stale_1hour_refused(self):
        stale = _spaced_bars("2026-10-23T07:00:00Z", 10, 3600)
        v = view(bars={"CAP|1Hour": stale}, now="2026-10-23T18:00:00Z")
        self.assertEqual(enhance14.filter_entries(
            "capitulation_options",
            [self._entry("capitulation_options", "CAP")], v), [])
        fresh = _spaced_bars("2026-10-23T17:00:00Z", 10, 3600)
        v2 = view(bars={"CAP|1Hour": fresh}, now="2026-10-23T18:00:00Z")
        self.assertEqual(len(enhance14.filter_entries(
            "capitulation_options",
            [self._entry("capitulation_options", "CAP")], v2)), 1)

    def test_earnings_buyback_stale_daily_refused(self):
        old = [{"t": "2026-10-01T14:00:00Z", "o": 50, "h": 51, "l": 49,
                "c": 50, "v": 1000.0}]
        v = view(bars={"EB|1Day": old}, now="2026-10-23T18:00:00Z")
        self.assertEqual(enhance14.filter_entries(
            "earnings_buyback", [self._entry("earnings_buyback", "EB")],
            v), [])
        fresh = [{"t": "2026-10-22T14:00:00Z", "o": 50, "h": 51, "l": 49,
                  "c": 50, "v": 1000.0}]
        v2 = view(bars={"EB|1Day": fresh}, now="2026-10-23T18:00:00Z")
        self.assertEqual(len(enhance14.filter_entries(
            "earnings_buyback", [self._entry("earnings_buyback", "EB")],
            v2)), 1)

    def test_em1587_target_consumed_refused(self):
        reason = ("em_1587: em_1587 enter break long: regime=CONFIRM "
                  "target=WALL_UP 512.30 (1R=2.50, room=9.00); occ=X")
        it = self._entry("em_1587", "SPY", price_hint=515.0,
                         reason=reason, limit_price=3.0)
        self.assertEqual(enhance14.filter_entries("em_1587", [it],
                                                  view()), [])
        it2 = self._entry("em_1587", "SPY", price_hint=505.0,
                          reason=reason, limit_price=3.0)
        self.assertEqual(len(enhance14.filter_entries(
            "em_1587", [it2], view())), 1)
        short_reason = ("em_1587: em_1587 enter break short: "
                        "regime=CONFIRM target=WALL_DN 487.70 "
                        "(1R=2.50, room=9.00); occ=Y")
        it3 = self._entry("em_1587", "SPY", price_hint=485.0,
                          reason=short_reason, limit_price=3.0)
        self.assertEqual(enhance14.filter_entries("em_1587", [it3],
                                                  view()), [])
        off = view(params={"extra": {"em_1587_enh2":
                                      {"target_consumed": False}}})
        self.assertEqual(len(enhance14.filter_entries(
            "em_1587", [it], off)), 1)


# ------------------------------------------------------------- capitulation
class TestCapitulationTrancheFeed(unittest.TestCase):
    def _cap_daily(self, closes=None):
        closes = closes or [100.0] * 260
        return b1.bars_for(closes, highs=[104.0] * len(closes),
                           lows=[96.0] * len(closes),
                           vols=[1000.0] * len(closes))

    def _cap_h1_crash(self):
        closes = [110.0 - 0.19 * i for i in range(59)] + [100.0]
        vols = [1000.0] * 58 + [6000.0, 1000.0]
        out = []
        base = datetime(2026, 10, 21, 17, 0, tzinfo=timezone.utc)
        for i, c in enumerate(closes):
            t = base + timedelta(hours=i)
            o = closes[i - 1] if i else c + 0.19
            out.append({"t": t.isoformat().replace("+00:00", "Z"),
                        "o": float(o), "h": float(max(o, c) + 0.1),
                        "l": float(min(o, c) - 0.1), "c": float(c),
                        "v": float(vols[i])})
        return out

    def _pass1(self, state_dir, feed_off=False):
        extra = {"fear_ok": True, "earnings_fresh": True,
                 "earnings": {"CAP": None}}
        if feed_off:
            extra["capitulation_improve"] = {"tranche_plan_feed": False}
        v = view(bars={"CAP|1Day": self._cap_daily(),
                       "CAP|1Hour": self._cap_h1_crash()},
                 params={"universe": ["CAP"], "extra": extra})
        ctx = {"sleeve_id": "capitulation", "state_dir": state_dir,
               "cycle_id": "fx14"}
        return ev("capitulation", v, ctx), ctx

    def _pass2(self, ctx):
        closes = [100.0] * 255 + [101.0, 102.0, 103.0, 104.0, 105.0]
        pos = [{"symbol": "CAP", "qty": 1, "avg_price": 100.0,
                "opened_at": "2026-10-23T14:00:00Z", "intent_id": "cap-1"}]
        v = view(bars={"CAP|1Day": self._cap_daily(closes),
                       "CAP|1Hour": self._cap_h1_crash()},
                 params={"universe": ["CAP"],
                         "extra": {"fear_ok": True,
                                   "earnings_fresh": True,
                                   "earnings": {"CAP": None}}},
                 positions=pos)
        return ev("capitulation", v, ctx)

    def test_tranche2_fires_from_adapter_plan(self):
        d = tempfile.mkdtemp()
        out1, ctx = self._pass1(d)
        entries = [i for i in out1 if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        # WS4-FRACTIONAL-20261114: tranche 1 is half of the
        # fractional full size 3.125 (was whole-share 1 of full 3)
        self.assertEqual(entries[0]["qty"], 1.5625)
        plan_path = os.path.join(d, "capitulation_tranche_plans.json")
        self.assertTrue(os.path.exists(plan_path))
        plan = json.load(open(plan_path))
        # WS4: tranche 2 = full 3.125 - tranche 1 1.5625
        self.assertEqual(plan["CAP"]["tranche2_qty"], 1.5625)
        self.assertEqual(plan["CAP"]["full_qty"], 3.125)  # WS4 fractional full
        out2 = self._pass2(ctx)
        t2 = [i for i in out2 if i["kind"] == "entry"
              and "tranche2" in (i.get("reason") or "")]
        self.assertEqual(len(t2), 1)
        self.assertEqual(t2[0]["qty"], 1.5625)  # WS4: full - tranche 1

    def test_feed_off_at_entry_means_no_tranche2(self):
        d = tempfile.mkdtemp()
        _out1, ctx = self._pass1(d, feed_off=True)
        self.assertFalse(os.path.exists(
            os.path.join(d, "capitulation_tranche_plans.json")))
        out2 = self._pass2(ctx)
        t2 = [i for i in out2 if i["kind"] == "entry"
              and "tranche2" in (i.get("reason") or "")]
        self.assertEqual(t2, [])


# ------------------------------------------------------------ VERIFY-ONLY
class TestVerifyOnlyEvidence(unittest.TestCase):
    def test_daily_cyan_gbm_entry_exit_and_p90_record(self):
        bars = b1.flat(25, 50.0, v=30000.0)
        params = {"extra": {"dcg_scores": {"GBM": 0.01}}}
        got = b1.drive2("daily_cyan_gbm",
                        bars_by_key={("GBM", "1Day"): bars}, params=params)
        self.assertEqual(len([i for i in got if i["kind"] == "entry"]), 1)
        got = b1.drive2("daily_cyan_gbm",
                        bars_by_key={("GBM", "1Day"): bars},
                        seeded_fills=[b1.fill("GBM", 2, 50.0,
                                              "2026-09-01T14:00:00Z")])
        self.assertEqual(len([i for i in got if i["kind"] == "exit"]), 1)
        # p90 paired record at the strategy layer: 10 delivered
        # scores, only the top name clears the session's own p90.
        import sleeves.daily_cyan_gbm as dcg
        from types import SimpleNamespace
        scores = {f"S{i}": 0.001 * (i + 1) for i in range(9)}
        scores["TOP"] = 0.01
        journal = {"records": []}
        extra = {"dcg_scores": scores,
                 "daily_cyan_gbm_exp_journal": journal}
        bars_map = {s: b1.flat(25, 50.0, v=30000.0) for s in scores}
        ctx = SimpleNamespace(session="2026-10-23", equity=10000.0,
                              extra=extra)
        out = dcg.signal(bars_map, {}, ctx)
        self.assertEqual([i.symbol for i in out], ["TOP"])
        rec = journal["records"][-1]
        self.assertEqual(rec["treatment_eligible"], ["TOP"])
        self.assertEqual(rec["p90"], dcg.percentile90(
            [float(s) for s in scores.values()]))

    def test_bb_rsi_gates_bind(self):
        case = b1.TestBatch1Equivalence()
        bars = case._bb_bars()
        base = {"extra": case._bb_extra(bars)}
        got = b1.drive2(
            "bb_rsi_divergence",
            bars_by_key={("SPY", "1Hour"): case._bb_view_bars(bars)},
            params=base, now=case._bb_now(bars))
        self.assertEqual(len([i for i in got if i["kind"] == "entry"]), 1)
        # stale quote (>60s) -> no entry (fresh-quote gate binds)
        stale_q = dict(case._bb_quote(bars))
        stale_q["t"] = bars[-1]["t"] + 3600.0 - 300.0
        got = b1.drive2(
            "bb_rsi_divergence",
            bars_by_key={("SPY", "1Hour"): case._bb_view_bars(bars)},
            params={"extra": case._bb_extra(bars, latest_quote={
                "SPY": stale_q})},
            now=case._bb_now(bars))
        self.assertEqual(got, [])
        # wide quote (>15bps spread) -> no entry (spread gate binds)
        wide_q = dict(case._bb_quote(bars))
        wide_q["bp"] = wide_q["ap"] - 1.00
        got = b1.drive2(
            "bb_rsi_divergence",
            bars_by_key={("SPY", "1Hour"): case._bb_view_bars(bars)},
            params={"extra": case._bb_extra(bars, latest_quote={
                "SPY": wide_q})},
            now=case._bb_now(bars))
        self.assertEqual(got, [])


if __name__ == "__main__":
    unittest.main()
