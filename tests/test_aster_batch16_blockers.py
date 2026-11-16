"""ASTER-B16 blockers: overnight 5bp, trader Donchian55, Tensor D20 x2,
saty_research shell. Fail-first: engine desk3/aster_batch16.py absent ->
imports error. Fixtures prove entry, EVERY designed exit, refusals, and
E2E round-trips to flat on the FakeBroker per family."""
import importlib, json, math, os, sys, tempfile, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ON = "aster_r19_timing_overnight_5bp"
DON = "aster_trader_donchian55"
D20T = "aster_tensor_d20_tensor"
D20P = "aster_tensor_d20_pv"
SATY = "aster_saty_research"
IDS = [ON, DON, D20T, D20P, SATY]


def ev(sid, view, ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(view, ctx)


# ---------------------------------------------------------------- overnight
def _bizdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def on_view(today_ret=0.02, hist_ret=0.001, n_hist=130, now="2026-10-23T15:31:00-04:00",
            positions=None, price=50.0):
    days = _bizdays(date(2026, 10, 23), n_hist + 1)  # last = today
    bars = []
    for d in days:
        r = today_ret if d == days[-1] else hist_ret
        bars.append({"t": f"{d}T12:30:00-04:00", "o": 100, "h": 100, "l": 100, "c": 100.0, "v": 1000})
        bars.append({"t": f"{d}T14:30:00-04:00", "o": 100, "h": 101, "l": 100, "c": 100.0 * (1 + r), "v": 1000})
    sessions = [str(d) for d in days] + ["2026-10-26"]
    return {"now": now, "bars": {"MU|30Min": bars},
            "quotes": {"MU": {"bid": price - 0.1, "ask": price}},
            "positions": positions or [], "extra": {"session_dates": sessions},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class TestOvernight5bp(unittest.TestCase):
    def test_entry_fires_and_sizes_with_5bp_fee(self):
        o = ev(ON, on_view())
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["symbol"], "MU")
        # budget min(cash, 0.1*slice)=1000; qty=floor(1000/(50*1.0005))=19
        self.assertEqual(o[0]["qty"], 19)
        self.assertIn("overnight", o[0]["reason"])
        self.assertTrue(o[0]["exit_at"].startswith("2026-10-26"))

    def test_scheduled_time_exit_next_open(self):
        pos = [{"symbol": "MU", "qty": 19, "avg_price": 50.0,
                "exit_at": "2026-10-26T09:30:00-04:00"}]
        v = on_view(now="2026-10-26T09:31:00-04:00", positions=pos)
        o = ev(ON, v)
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["kind"], "exit")
        self.assertIn("scheduled_time_exit", o[0]["reason"])

    def test_refusals(self):
        self.assertEqual(ev(ON, on_view(now="2026-10-23T15:36:00-04:00")), [])  # window closed
        self.assertEqual(ev(ON, on_view(now="2026-10-23T15:29:00-04:00")), [])  # too early
        self.assertEqual(ev(ON, on_view(today_ret=0.0005)), [])                  # below p80
        self.assertEqual(ev(ON, on_view(n_hist=100)), [])                        # <126 history
        pos = [{"symbol": "MU", "qty": 5, "avg_price": 50.0,
                "exit_at": "2026-10-26T09:30:00-04:00"}]
        self.assertEqual(ev(ON, on_view(positions=pos)), [])                     # already held

    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        broker = FakeBroker(prices={"MU": 50.0})
        disp = Dispatcher(tempfile.mkdtemp(), broker,
                          slices={ON: {"capital_usd": 10000.0, "cash_usd": 10000.0}},
                          price_lookup=lambda s: 50.0)
        e = ev(ON, on_view())[0]
        self.assertEqual(disp.process_intent(e, ON)["status"], "filled")
        self.assertEqual(broker.get_positions(), {"MU": 19.0})
        pos = [{"symbol": "MU", "qty": 19, "avg_price": 50.0,
                "exit_at": "2026-10-26T09:30:00-04:00"}]
        x = ev(ON, on_view(now="2026-10-26T09:31:00-04:00", positions=pos))[0]
        self.assertEqual(disp.process_intent(x, ON)["status"], "filled")
        self.assertEqual(broker.get_positions(), {})


# ---------------------------------------------------------------- donchian55
def don_bars(n=260, last_close=None, drop_last=False):
    bars = []
    for i in range(n):
        c = 100.0 + i * 0.4
        bars.append({"t": f"2026-01-{(i % 28) + 1:02d}", "o": c, "h": c + 0.5,
                     "l": c - 0.5, "c": c, "v": 10_000_000})
    if last_close is not None:
        bars[-1] = dict(bars[-1], c=last_close, h=last_close + 0.5, l=last_close - 0.5)
    if drop_last:
        bars[-1] = dict(bars[-1], c=50.0, h=50.5, l=49.5)
    return bars


def don_view(barsmap=None, positions=None, cash=10000.0):
    return {"now": "2026-10-23T15:00:00-04:00",
            "bars": barsmap if barsmap is not None else {"SPY|1Day": don_bars(last_close=210.0)},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": cash}}


class TestDonchian55(unittest.TestCase):
    def test_entry_fires_with_risk_and_notional_caps(self):
        o = ev(DON, don_view())
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["symbol"], "SPY")
        self.assertEqual(o[0]["kind"], "entry")
        # notional cap 1000/210 -> 4 shares; risk cap floor(50/(2*atr)) larger
        self.assertEqual(o[0]["qty"], 4)
        self.assertIsNotNone(o[0]["stop_price"])
        self.assertLess(o[0]["stop_price"], 210.0)

    def test_refusals(self):
        self.assertEqual(ev(DON, don_view({"SPY|1Day": don_bars()})), [])          # no breakout
        self.assertEqual(ev(DON, don_view({"SPY|1Day": don_bars(200, 210.0)})), [])  # warmup <252
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 200.0, "bars_held": 3}]
        self.assertEqual(ev(DON, don_view(positions=pos)), [])                     # already held

    def test_exit_close_below_prior20_low(self):
        bars = don_bars(last_close=205.0)
        bars[-1] = dict(bars[-1], c=100.0, h=100.5, l=99.5)  # below prior-20 low & sma200
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 200.0, "bars_held": 5}]
        o = ev(DON, don_view({"SPY|1Day": bars}, positions=pos))
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["kind"], "exit")
        self.assertIn("close_below", o[0]["reason"])

    def test_exit_initial_2atr_stop(self):
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 200.0, "bars_held": 5,
                "stop_price": 195.0}]
        bars = don_bars(last_close=194.0)
        o = ev(DON, don_view({"SPY|1Day": bars}, positions=pos))
        self.assertEqual(len(o), 1)
        self.assertIn("initial_2atr_stop", o[0]["reason"])

    def test_exit_126_bar_timeout(self):
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 200.0, "bars_held": 126}]
        o = ev(DON, don_view(positions=pos))
        self.assertEqual(len(o), 1)
        self.assertIn("126", o[0]["reason"])
        pos[0]["bars_held"] = 125
        self.assertEqual(ev(DON, don_view(positions=pos)), [])

    def test_ranking_stronger_breakout_first(self):
        m = {"SPY|1Day": don_bars(last_close=210.0), "QQQ|1Day": don_bars(last_close=260.0)}
        o = ev(DON, don_view(m))
        self.assertEqual([i["symbol"] for i in o], ["QQQ", "SPY"])

    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        broker = FakeBroker(prices={"SPY": 210.0})
        disp = Dispatcher(tempfile.mkdtemp(), broker,
                          slices={DON: {"capital_usd": 10000.0, "cash_usd": 10000.0}},
                          price_lookup=lambda s: 210.0)
        e = ev(DON, don_view())[0]
        self.assertEqual(disp.process_intent(e, DON)["status"], "filled")
        self.assertEqual(broker.get_positions(), {"SPY": 4.0})
        pos = [{"symbol": "SPY", "qty": 4, "avg_price": 210.0, "bars_held": 126}]
        xv = don_view(positions=pos); xv["now"] = "2026-10-24T15:00:00-04:00"
        x = ev(DON, xv)[0]
        self.assertEqual(disp.process_intent(x, DON)["status"], "filled")
        self.assertEqual(broker.get_positions(), {})


# ---------------------------------------------------------------- tensor D20
ASSETS = os.path.join(ROOT, "desk3", "aster_d20_assets")
ANCHORS = json.load(open(os.path.join(ASSETS, "DAILY_SOURCE_ANCHORS.json")))["symbols"]
# Recipe verified against the archive module (backend/tensor_daily_models
# .evaluate_daily20): BOTH frozen models select ADSK on these features
# (PV 0.032837683351856994, TENSOR 0.010204886593293511).
RECIPE = dict(ret20=-0.0004355548709383747, ret60=0.6079143587172864,
              atr_pct=0.047010904409629364, rvol=1.901925765372908,
              logdv=16.300964163076298, emadist=1.0704537780305432)
FLAT = dict(ret20=0.0088016164457693, ret60=0.0204419295075573, atr_pct=0.02803251644423662,
            rvol=0.8958896630129507, logdv=17.744238400270266, emadist=0.17484478091587152)


def d20_rows(sym="ADSK", p=RECIPE, n=240, status="ready", close=100.0):
    a = ANCHORS[sym]; t0 = a["first_timestamp"]
    atr14 = p["atr_pct"] * close
    rows = []
    for i in range(n):
        ts = t0 + i * 86400
        rows.append({"symbol": sym, "bar_index": i, "timestamp": ts,
                     "completed_at": ts + 3600, "usable_at": ts + 3600,
                     "source_origin_timestamp": t0, "native_status": status,
                     "open": close, "close": close, "volume": 100000.0,
                     "atr14": atr14, "return20": p["ret20"], "return60": p["ret60"],
                     "rvol": p["rvol"], "dollar_volume20": math.expm1(p["logdv"]),
                     "ema21": close - p["emadist"] * atr14,
                     "bullish_votes": 3.0, "bearish_votes": 3.0,
                     "ribbon_inversion_count": 8.0, "ribbon_width": 0.05, "ribbon_slope": 0.0004,
                     "obv_slope5": 3000.0, "squeeze_on": 1.0, "squeeze_momentum": 0.005 * atr14,
                     "squeeze_length": 14.0, "ut_regime": "bullish",
                     "mcdx_position": 56.0, "mcdx_position_delta3": 0.18,
                     "macd_histogram": 0.008 * atr14, "efficiency10": 0.29,
                     "normalized_sign_entropy20": 0.62,
                     "prior_sell_avwap": close - 0.5 * atr14,
                     "prior_sell_completed_at": ts - 3600, "overhead60_atr": 1.2,
                     "vote_stoch": 0.0, "vote_aroon": 1.0, "vote_di": 1.0, "vote_obv": 1.0,
                     "vote_squeeze": -1.0, "vote_pivot": 1.0, "vote_wave": 1.0})
    return rows


def d20_view(rowsmap=None, positions=None):
    return {"now": "2026-10-23T15:00:00-04:00",
            "tensor_daily20": rowsmap if rowsmap is not None else {"ADSK": d20_rows()},
            "bars": {}, "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class TestTensorD20(unittest.TestCase):
    def test_assets_verify_against_frozen_pins(self):
        from desk3 import aster_batch16 as b16
        v = b16.verify_d20_assets()
        self.assertEqual(v["status"], "PASS")
        self.assertEqual(v["canonical_symbols"], 1817)

    def test_model_math_matches_exported_oracles(self):
        from desk3 import aster_batch16 as b16
        for name, oracle in (("price_volume", "price_volume-oracle.json"),
                             ("price_volume_plus_tensor", "price_volume_plus_tensor-oracle.json")):
            src = json.load(open(os.path.join(
                "/home/hatch/workspace/.scratch-ausar-archive/handoff-20261024",
                "source/strategies/tensor_daily20/models", oracle)))
            model = b16._load_d20_models()["models"][name]
            for vec, expected in zip(src["vectors"], src["expected_predictions"]):
                feats = dict(zip(model["columns"], vec))
                self.assertAlmostEqual(model_predict(model, feats), expected, places=9)

    def test_entry_fires_both_models(self):
        for sid, score in ((D20P, 0.032837683351856994), (D20T, 0.010204886593293511)):
            o = ev(sid, d20_view())
            self.assertEqual(len(o), 1, sid)
            self.assertEqual(o[0]["symbol"], "ADSK")
            self.assertEqual(o[0]["qty"], 10)  # min(0.1*10000, 1% DV)/100
            self.assertIn(f"{score:.6f}", o[0]["reason"])

    def test_refusals(self):
        for sid in (D20P, D20T):
            self.assertEqual(ev(sid, d20_view({"ADSK": d20_rows(p=FLAT)})), [], sid)       # below threshold
            self.assertEqual(ev(sid, d20_view({"ADSK": d20_rows(n=239)})), [], sid)        # phase miss
            self.assertEqual(ev(sid, d20_view({"ADSK": d20_rows(n=100)})), [], sid)        # warmup
            self.assertEqual(ev(sid, d20_view({"ADSK": d20_rows(status="warming")})), [], sid)
            self.assertEqual(ev(sid, d20_view({"ADSK": d20_rows(close=4.0)})), [], sid)    # price < 5
            pos = [{"symbol": "ADSK", "qty": 10, "avg_price": 100.0, "bars_held": 3}]
            self.assertEqual(ev(sid, d20_view(positions=pos)), [], sid)                    # already held

    def test_exit_after_20_holding_bars_only(self):
        for sid in (D20P, D20T):
            pos = [{"symbol": "ADSK", "qty": 10, "avg_price": 100.0, "bars_held": 20}]
            o = ev(sid, d20_view(positions=pos))
            self.assertEqual(len(o), 1, sid)
            self.assertIn("hold_20_bars", o[0]["reason"])
            pos[0]["bars_held"] = 19
            self.assertEqual(ev(sid, d20_view(positions=pos)), [], sid)
            pos[0]["bars_held"] = 10  # -50% close: NO price stop by design
            self.assertEqual(ev(sid, d20_view({"ADSK": d20_rows(close=50.0)}, positions=pos)), [], sid)

    def test_integrity_tamper_fails_closed(self):
        from desk3 import aster_batch16 as b16
        import shutil
        tmp = tempfile.mkdtemp()
        shutil.copytree(ASSETS, tmp, dirs_exist_ok=True)
        p = os.path.join(tmp, "price_volume.json")
        body = bytearray(open(p, "rb").read()); body[100] ^= 1
        open(p, "wb").write(bytes(body))
        with self.assertRaises(Exception):
            b16._load_d20_models(tmp)

    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sid = D20P
        broker = FakeBroker(prices={"ADSK": 100.0})
        disp = Dispatcher(tempfile.mkdtemp(), broker,
                          slices={sid: {"capital_usd": 10000.0, "cash_usd": 10000.0}},
                          price_lookup=lambda s: 100.0)
        e = ev(sid, d20_view())[0]
        self.assertEqual(disp.process_intent(e, sid)["status"], "filled")
        self.assertEqual(broker.get_positions(), {"ADSK": 10.0})
        pos = [{"symbol": "ADSK", "qty": 10, "avg_price": 100.0, "bars_held": 20}]
        xv = d20_view(positions=pos); xv["now"] = "2026-11-13T15:00:00-05:00"
        x = ev(sid, xv)[0]
        self.assertEqual(disp.process_intent(x, sid)["status"], "filled")
        self.assertEqual(broker.get_positions(), {})


def model_predict(model, feats):
    from desk3 import aster_batch16 as b16
    return b16._d20_predict(model, feats)


# ---------------------------------------------------------------- saty_research
def saty_candidate(**kw):
    c = {"symbol": "SPY", "family": "trend_break", "direction": "long",
         "entry": 600.0, "invalidation": 598.0, "targets": [604.0, 606.0],
         "context": 0.8, "age_min": 5}
    c.update(kw)
    return c


def saty_view(cands=None, positions=None, now="2026-10-23T14:00:00-04:00",
              quote_at="2026-10-23T13:59:58-04:00", mid=600.0, state=None):
    return {"now": now,
            "saty_setups": cands if cands is not None else [saty_candidate()],
            "quotes": {"SPY": {"bid": mid - 0.05, "ask": mid + 0.05, "at": quote_at}},
            "bars": {"SPY|10Min": [{"t": "2026-10-23T13:50:00-04:00", "o": mid, "h": mid,
                                    "l": mid, "c": mid, "v": 1000}]},
            "positions": positions or [],
            "saty_state": state or {"entries_today": 0, "realized_r_today": 0.0},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class TestSatyResearch(unittest.TestCase):
    def test_entry_fires_risk_sized(self):
        o = ev(SATY, saty_view())
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["kind"], "entry")
        self.assertEqual(o[0]["qty"], 12)  # floor($25 risk / $2 risk-per-share)
        self.assertEqual(o[0]["side"], "buy")

    def test_mean_reversion_half_risk(self):
        o = ev(SATY, saty_view([saty_candidate(family="mean_reversion_fade")]))
        self.assertEqual(o[0]["qty"], 6)  # floor($12.50 / $2)

    def test_refusals(self):
        self.assertEqual(ev(SATY, saty_view(quote_at="2026-10-23T13:59:50-04:00")), [])  # quote 8s stale > 5s
        self.assertEqual(ev(SATY, saty_view(state={"entries_today": 3, "realized_r_today": 0.0})), [])
        self.assertEqual(ev(SATY, saty_view(state={"entries_today": 0, "realized_r_today": -2.0})), [])
        self.assertEqual(ev(SATY, saty_view(now="2026-10-23T15:45:00-04:00",
                                            quote_at="2026-10-23T15:44:58-04:00")), [])  # entry deadline
        self.assertEqual(ev(SATY, saty_view(mid=604.5)), [])                              # no room to T1
        self.assertEqual(ev(SATY, saty_view(cands=[])), [])
        conflict = [saty_candidate(), saty_candidate(family="rev", direction="short",
                                                     entry=600.0, invalidation=602.0, targets=[596.0])]
        self.assertEqual(ev(SATY, saty_view(conflict)), [])                               # equal-rank conflict waits

    def test_open_risk_cap_refuses_second_full_risk(self):
        pos = [{"symbol": "SPY", "qty": 12, "avg_price": 600.0, "invalidation": 598.0,
                "targets": [604.0], "direction": "long"}]
        self.assertEqual(ev(SATY, saty_view(positions=pos)), [])  # 1R correlated cap already used

    def test_exit_invalidation(self):
        pos = [{"symbol": "SPY", "qty": 12, "avg_price": 600.0, "invalidation": 598.0,
                "targets": [604.0, 606.0], "direction": "long"}]
        o = ev(SATY, saty_view(cands=[], positions=pos, mid=597.5))
        self.assertEqual(len(o), 1)
        self.assertIn("structural_invalidation", o[0]["reason"])

    def test_exit_target_scale_then_trail(self):
        pos = [{"symbol": "SPY", "qty": 12, "avg_price": 600.0, "invalidation": 598.0,
                "targets": [604.0, 606.0], "direction": "long"}]
        o = ev(SATY, saty_view(cands=[], positions=pos, mid=604.2))
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["qty"], 6)  # scale half at T1
        self.assertIn("target1_scale", o[0]["reason"])
        pos[0]["scaled"] = True
        o = ev(SATY, saty_view(cands=[], positions=pos, mid=599.9))
        self.assertEqual(len(o), 1)
        self.assertIn("trail", o[0]["reason"])

    def test_exit_final_deadline_flattens(self):
        pos = [{"symbol": "SPY", "qty": 12, "avg_price": 600.0, "invalidation": 598.0,
                "targets": [604.0], "direction": "long"}]
        o = ev(SATY, saty_view(cands=[], positions=pos, now="2026-10-23T15:51:00-04:00",
                               quote_at="2026-10-23T15:50:58-04:00"))
        self.assertEqual(len(o), 1)
        self.assertIn("final_exit_deadline", o[0]["reason"])

    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        broker = FakeBroker(prices={"SPY": 600.0})
        disp = Dispatcher(tempfile.mkdtemp(), broker,
                          slices={SATY: {"capital_usd": 10000.0, "cash_usd": 10000.0}},
                          price_lookup=lambda s: 600.0)
        e = ev(SATY, saty_view())[0]
        self.assertEqual(disp.process_intent(e, SATY)["status"], "filled")
        self.assertEqual(broker.get_positions(), {"SPY": 12.0})
        pos = [{"symbol": "SPY", "qty": 12, "avg_price": 600.0, "invalidation": 598.0,
                "targets": [604.0], "direction": "long"}]
        x = ev(SATY, saty_view(cands=[], positions=pos, mid=597.5,
                               now="2026-10-23T14:05:00-04:00",
                               quote_at="2026-10-23T14:04:58-04:00"))[0]
        self.assertEqual(disp.process_intent(x, SATY)["status"], "filled")
        self.assertEqual(broker.get_positions(), {})


# ---------------------------------------------------------------- registry/config
class TestConfigAndFedState(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        cfg = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, cfg)
            self.assertEqual(cfg[sid]["slice"]["capital_usd"], 10000.0)
            self.assertEqual(cfg[sid]["module"], f"adapters3.{sid}")
            m = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(tuple(cfg[sid]["inputs"]), tuple(m.INPUTS))

    def test_unfed_by_construction(self):
        from desk3 import aster_batch16 as b16
        from desk3.registry import Registry
        r = Registry()
        for p in b16.PRODUCERS:
            r.register_producer(p["name"], p["outputs"], p["freshness_sla_s"])
        cfg = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]}
        for sid in IDS:
            r.register_sleeve(sid, cfg[sid]["inputs"])
        # live producers in run_live produce ONLY bars + positions
        r.mark_produced_keys("bars", {"bars"}, 1000.0)
        r.mark_produced_keys("broker_readback", {"positions"}, 1000.0)
        st = r.fed_states(1000.0)
        self.assertEqual(st[DON]["state"], "FED")
        self.assertEqual(st[ON]["state"], "UNFED")     # quotes producer absent
        self.assertEqual(st[D20T]["state"], "UNFED")   # tensor_daily20 producer absent
        self.assertEqual(st[D20P]["state"], "UNFED")
        self.assertEqual(st[SATY]["state"], "UNFED")   # saty_setups producer absent


if __name__ == "__main__":
    unittest.main()
