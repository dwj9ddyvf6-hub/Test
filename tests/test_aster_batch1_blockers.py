"""Aster batch 1 blockers (ASTER-B1-1): public_recipe RSI2 + squeeze,
tensor hourly/weekly state-repair, confirmed absorption ENJ/LINK 4h,
native SMA200 BTC_ETH + ETH books, opening_gamma A/B.

Oracle: staged archive (trader_signals.py, tensor_strategy.py,
absorption/signals.py + rules-v1.json, prospective_native_math.py,
r19_options.py + options_rules.json) — see desk3/aster_batch1.py.
Fail direction: pre-build none of adapters3.aster_* batch-1 modules
exist, so every drive errors on import.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
IDS = ["aster_rsi2_1d", "aster_squeeze_1d", "aster_tensor_h1_recovery",
       "aster_tensor_w1_recovery", "aster_abs_enj_4h", "aster_abs_link_4h",
       "aster_native_btc_eth_sma200", "aster_native_eth_sma200",
       "aster_open_gamma_a", "aster_open_gamma_b"]


def ctx(sd=None):
    return {"sleeve_id": "x", "state_dir": sd or tempfile.mkdtemp(),
            "cycle_id": "fx"}


def ev(sid, view, c=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, c or ctx())


def daily(closes, sym="SPY"):
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return {f"{sym}|1Day": [
        {"t": (base + timedelta(days=i)).isoformat(), "o": c,
         "h": c * 1.001, "l": c * 0.999, "c": c, "v": 100000}
        for i, c in enumerate(closes)]}


def slice10k():
    return {"capital_usd": 10000.0, "cash_usd": 10000.0}


class TestRegistry(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        cfg = {s["id"]: s for s in json.load(
            open(os.path.join(ROOT, "config/sleeves.json")))["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, cfg, sid)
            self.assertEqual(cfg[sid]["slice"]["capital_usd"], 10000.0)
            self.assertEqual(cfg[sid]["module"], f"adapters3.{sid}")
            mod = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(list(mod.INPUTS), list(cfg[sid]["inputs"]),
                             sid)

    def test_empty_view_fails_closed(self):
        for sid in IDS:
            self.assertEqual(ev(sid, {"now": "2026-10-23T13:37:00+00:00",
                                      "bars": {}, "positions": []}), [],
                             sid)


class TestRsi2(unittest.TestCase):
    def entry_view(self):
        closes = [100 + 0.3 * i for i in range(258)] + [175.0, 170.0]
        return {"now": "2026-10-23T14:00:00+00:00", "bars": daily(closes),
                "positions": [], "slice": slice10k()}

    def test_entry_fires(self):
        out = ev("aster_rsi2_1d", self.entry_view())
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0]["kind"], out[0]["symbol"],
                          out[0]["side"]), ("entry", "SPY", "buy"))
        # cap = min(0.1*10000, 0.01*DV20, cash) = $1000 @ 170.
        # WS4-FRACTIONAL-20261114: the same budget now expresses
        # fractionally (5.882352) instead of 5 whole shares.
        self.assertEqual(out[0]["qty"], 5.882352)  # floor6(1000/170)
        self.assertIsNone(out[0]["stop_price"])  # no initial ATR stop

    def test_exit_close_above_sma5(self):
        closes = [100 + 0.3 * i for i in range(260)]
        pos = [{"symbol": "SPY", "qty": 10, "avg_price": 150.0,
                "bars_held": 2}]
        out = ev("aster_rsi2_1d", {"now": "2026-10-23T14:00:00+00:00",
                                   "bars": daily(closes),
                                   "positions": pos, "slice": slice10k()})
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("close_above_sma5", out[0]["reason"])

    def test_exit_time_10_bars(self):
        pos = [{"symbol": "SPY", "qty": 10, "avg_price": 100.0,
                "bars_held": 10}]
        out = ev("aster_rsi2_1d", {"now": "2026-10-23T14:00:00+00:00",
                                   "bars": daily([100.0] * 260),
                                   "positions": pos, "slice": slice10k()})
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("10_completed_holding_bars", out[0]["reason"])

    def test_refusals(self):
        up = [100 + 0.3 * i for i in range(260)]
        self.assertEqual(ev("aster_rsi2_1d",
                            {"now": "2026-10-23T14:00:00+00:00",
                             "bars": daily(up), "positions": [],
                             "slice": slice10k()}), [])  # no dip
        self.assertEqual(ev("aster_rsi2_1d",
                            {"now": "2026-10-23T14:00:00+00:00",
                             "bars": daily(up[:100]),
                             "positions": []}), [])  # warmup <252
        down = [300 - 0.3 * i for i in range(258)] + [130.0, 125.0]
        self.assertEqual(ev("aster_rsi2_1d",
                            {"now": "2026-10-23T14:00:00+00:00",
                             "bars": daily(down), "positions": [],
                             "slice": slice10k()}), [])  # below SMA200


def squeeze_bars(extra=()):
    ohlc, price = [], 100.0
    for i in range(259):
        o = price
        c = price + (0.05 if i % 2 == 0 else -0.05)
        ohlc.append((o, max(o, c) + 0.05, min(o, c) - 0.05, c))
        price = c
    ohlc.append((100.0, 103.2, 99.9, 103.0))
    ohlc.extend(extra)
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [{"t": (base + timedelta(days=i)).isoformat(), "o": o,
             "h": h, "l": l, "c": c, "v": 100000}
            for i, (o, h, l, c) in enumerate(ohlc)]


class TestSqueeze(unittest.TestCase):
    def view(self, bars, positions=None):
        return {"now": "2026-10-23T14:00:00+00:00",
                "bars": {"SPY|1Day": bars}, "positions": positions or [],
                "slice": slice10k()}

    def test_entry_fires_with_2atr_stop(self):
        out = ev("aster_squeeze_1d", self.view(squeeze_bars()))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertIsNotNone(out[0]["stop_price"])
        self.assertLess(out[0]["stop_price"], 103.0)

    def test_exit_rule_close_below_ema20_momentum(self):
        extra, p = [], 103.0
        for _ in range(8):
            extra.append((p, p + 0.1, p - 1.3, p - 1.2))
            p -= 1.2
        pos = [{"symbol": "SPY", "qty": 5, "avg_price": 103.0,
                "bars_held": 8, "stop_price": 90.0}]
        out = ev("aster_squeeze_1d",
                 self.view(squeeze_bars(extra), pos))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("momentum_nonpositive", out[0]["reason"])

    def test_exit_initial_2atr_stop(self):
        bars = squeeze_bars([(103.0, 103.1, 101.0, 102.8)])
        pos = [{"symbol": "SPY", "qty": 5, "avg_price": 103.0,
                "bars_held": 1, "stop_price": 102.0}]
        out = ev("aster_squeeze_1d", self.view(bars, pos))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("2atr_stop", out[0]["reason"])

    def test_exit_time_20_bars(self):
        pos = [{"symbol": "SPY", "qty": 5, "avg_price": 100.0,
                "bars_held": 20}]
        out = ev("aster_squeeze_1d", self.view(squeeze_bars(), pos))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("20_completed_holding_bars", out[0]["reason"])

    def test_refusal_no_release(self):
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        up = [{"t": (base + timedelta(days=i)).isoformat(),
               "o": 100 + 0.5 * i, "h": 100.3 + 0.5 * i,
               "l": 99.7 + 0.5 * i, "c": 100.2 + 0.5 * i, "v": 100000}
              for i in range(260)]
        self.assertEqual(ev("aster_squeeze_1d", self.view(up)), [])


def trow(idx, votes, frame="1h", **kw):
    bull = sum(1 for v in votes if v == 1)
    bear = sum(1 for v in votes if v == -1)
    d = {"bar_index": idx, "votes": votes, "bullish_votes": bull,
         "bearish_votes": bear, "total_votes": bull + bear,
         "balance": bull - bear, "close": 50.0, "atr14": 1.0,
         "dollar_volume20": 2_000_000, "volume": 100000,
         "obv_slope5": 500.0, "native_status": "ready", "frame": frame}
    d.update(kw)
    return d


def repair_panel(frame="1h"):
    return [trow(240, [-1, -1, -1, -1, 1, -1, -1], frame),
            trow(241, [-1, -1, 1, -1, 1, -1, -1], frame),
            trow(242, [1, -1, 1, -1, 1, -1, -1], frame),
            trow(243, [1, 1, 1, -1, 1, -1, -1], frame)]


class TestTensorRecovery(unittest.TestCase):
    def view(self, panels, positions=None, frame_key="tensor",
             bars=None):
        return {"now": "2026-10-23T14:00:00+00:00", frame_key: panels,
                "bars": bars or {}, "positions": positions or [],
                "slice": slice10k()}

    def test_entry_hourly(self):
        out = ev("aster_tensor_h1_recovery",
                 self.view({"ACME": repair_panel()}))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        # floor(min(1000, 0.01*2M, 10000)/(50*1.001)) = 19
        self.assertEqual(out[0]["qty"], 19)

    def test_entry_weekly_own_frame(self):
        # AMENDED 2026-11-12 (GATE-CURE-W1-20261112, STRICTNESS-
        # CENSUS proposal 7): the 234-bar minimum now reads the
        # underlying daily source series instead of the weekly
        # panel index, so the fixture supplies a 250-bar daily
        # series; the assertion (entry on the sleeve's own frame)
        # is unchanged. Pre-amendment copy preserved in
        # ~/workspace/.gatecure-20261112/pre/tests/.
        out = ev("aster_tensor_w1_recovery",
                 self.view({"ACME": repair_panel("1wk")},
                           bars=daily([50.0] * 250, "ACME")))
        self.assertEqual(len(out), 1)

    def test_frame_mismatch_refuses(self):
        self.assertEqual(ev("aster_tensor_w1_recovery",
                            self.view({"ACME": repair_panel("1h")})), [])
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"ACME": repair_panel("1wk")})), [])

    def test_exit_20_native_bars(self):
        panel = [trow(240, [1, 1, 1, -1, 1, -1, -1])]
        pos = [{"symbol": "ACME", "qty": 10, "avg_price": 50.0,
                "entry_bar_index": 220}]
        out = ev("aster_tensor_h1_recovery", self.view({"ACME": panel},
                                                       pos))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("hold_20_native_bars", out[0]["reason"])
        pos[0]["entry_bar_index"] = 230
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"ACME": panel}, pos)), [])

    def test_refusals(self):
        flat = [trow(i, [1, 1, 1, -1, 1, -1, -1]) for i in range(240, 244)]
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"ACME": flat})), [])  # no repair
        miss = repair_panel()
        miss[3] = {**miss[3], "votes": [1, 1, 1, None, 1, -1, -1],
                   "total_votes": 6, "bullish_votes": 4,
                   "bearish_votes": 2, "balance": 2}
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"ACME": miss})), [])  # votes <7
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"SPY": repair_panel()})), [])
        cheap = repair_panel()
        cheap[3] = {**cheap[3], "close": 4.0}
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"ACME": cheap})), [])  # price <5
        dry = repair_panel()
        dry[3] = {**dry[3], "dollar_volume20": 500_000}
        self.assertEqual(ev("aster_tensor_h1_recovery",
                            self.view({"ACME": dry})), [])  # DV20 < $1M


ABS_NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def abs_bars(n=302):
    out = []
    for i in range(n):
        t = ABS_NOW - timedelta(hours=4 * (n - i))
        o = c = 2.0
        h, l, v = 2.02, 1.98, 1000.0
        if i == n - 2:
            o, c, h, l, v = 2.0, 1.90, 2.0, 1.88, 5000.0
        if i == n - 1:
            o, c, h, l = 1.90, 1.96, 1.97, 1.89
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l,
                    "c": c, "v": v})
    return out


class TestAbsorption(unittest.TestCase):
    def view(self, bars, positions=None, sym="ENJUSDT"):
        return {"now": ABS_NOW.isoformat(), "bars": {f"{sym}|4Hour": bars},
                "quotes": {}, "positions": positions or [],
                "slice": slice10k()}

    def test_entry_enj_and_link(self):
        out = ev("aster_abs_enj_4h", self.view(abs_bars()))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertAlmostEqual(out[0]["qty"], 10000 / (1.96 * 1.001),
                               places=4)  # full cash incl. 10bp fee
        out = ev("aster_abs_link_4h",
                 self.view(abs_bars(), sym="LINKUSDT"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "LINKUSDT")

    def test_refusals(self):
        b = abs_bars()
        b[-1] = {**b[-1], "o": 1.90, "c": 1.87, "h": 1.92, "l": 1.85}
        self.assertEqual(ev("aster_abs_enj_4h", self.view(b)), [])
        self.assertEqual(ev("aster_abs_enj_4h",
                            self.view(abs_bars(100))), [])  # warmup 300
        self.assertEqual(ev("aster_abs_link_4h",
                            self.view(abs_bars())), [])  # wrong symbol

    def test_exit_deadline_16h_never_resets(self):
        pos = [{"symbol": "ENJUSDT", "qty": 1000.0, "avg_price": 1.96,
                "opened_at": (ABS_NOW - timedelta(hours=20)).isoformat()}]
        out = ev("aster_abs_enj_4h", self.view(abs_bars(), pos))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("deadline_16h", out[0]["reason"])
        pos[0]["opened_at"] = (ABS_NOW - timedelta(hours=10)).isoformat()
        self.assertEqual(ev("aster_abs_enj_4h",
                            self.view(abs_bars(), pos)), [])


class TestNative(unittest.TestCase):
    def bars(self, btc, eth):
        out = {}
        out.update(daily(btc, "BTC-USD"))
        out.update(daily(eth, "ETH-USD"))
        return out

    def test_pair_buys_only_above_sma200(self):
        btc = [100 + 0.5 * i for i in range(210)]
        eth = [300 - 0.5 * i for i in range(210)]
        out = ev("aster_native_btc_eth_sma200",
                 {"now": "2026-10-23T14:00:00+00:00",
                  "bars": self.bars(btc, eth), "positions": [],
                  "slice": slice10k()})
        # BROKER-422-ASTER-CRYPTO-20261027: emitted orders carry the
        # Alpaca trading dialect BTC/USD (was BTC-USD, which Alpaca
        # 422s as asset-not-found); bars fixtures keep the internal
        # dialect, which is the input contract.
        self.assertEqual([o["symbol"] for o in out], ["BTC/USD"])
        self.assertAlmostEqual(out[0]["qty"] * 204.5, 4990.0, delta=30.0)

    def test_eth_book_full_weight_and_gate_off(self):
        up = [100 + 0.5 * i for i in range(210)]
        down = [300 - 0.5 * i for i in range(210)]
        out = ev("aster_native_eth_sma200",
                 {"now": "2026-10-23T14:00:00+00:00",
                  "bars": self.bars(up, up), "positions": [],
                  "slice": slice10k()})
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0]["qty"] * 204.5, 9980.0, delta=30.0)
        self.assertEqual(ev("aster_native_eth_sma200",
                            {"now": "2026-10-23T14:00:00+00:00",
                             "bars": self.bars(up, down), "positions": [],
                             "slice": slice10k()}), [])

    def test_exit_sells_before_buys(self):
        btc = [100 + 0.5 * i for i in range(210)]
        eth = [300 - 0.5 * i for i in range(210)]
        pos = [{"symbol": "ETH-USD", "qty": 10.0, "avg_price": 200.0}]
        out = ev("aster_native_btc_eth_sma200",
                 {"now": "2026-10-23T14:00:00+00:00",
                  "bars": self.bars(btc, eth), "positions": pos,
                  "slice": {"capital_usd": 10000.0, "cash_usd": 8000.0}})
        self.assertEqual(out[0]["kind"], "exit")
        # BROKER-422-ASTER-CRYPTO-20261027: broker dialect on emit.
        self.assertEqual(out[0]["symbol"], "ETH/USD")
        self.assertEqual(out[0]["qty"], 10.0)  # full reduction to cash
        self.assertEqual(out[1]["symbol"], "BTC/USD")

    def test_warmup_refuses(self):
        short = [100 + 0.5 * i for i in range(100)]
        self.assertEqual(ev("aster_native_eth_sma200",
                            {"now": "2026-10-23T14:00:00+00:00",
                             "bars": self.bars(short, short),
                             "positions": []}), [])


SESS, PREV = "2026-10-23", "2026-10-22"
OPENED = datetime(2026, 10, 23, 9, 30, tzinfo=ET)
GNOW = datetime(2026, 10, 23, 9, 37, tzinfo=ET)


def iso(d):
    return d.astimezone(timezone.utc).isoformat()


def gamma_event(**kw):
    e = {"event_id": "E1", "symbol": "SPY", "session": SESS,
         "prior_afternoon_session": PREV,
         "first_5min_start_at": iso(OPENED),
         "first_5min_end_at": iso(OPENED + timedelta(minutes=5)),
         "first_5min_received_at": iso(OPENED + timedelta(minutes=5,
                                                           seconds=1)),
         "break_market_at": iso(GNOW - timedelta(seconds=2)),
         "break_received_at": iso(GNOW - timedelta(seconds=1)),
         "R5_signal_at": iso(datetime(2026, 10, 22, 15, 0, tzinfo=ET)),
         "R5_received_at": iso(datetime(2026, 10, 22, 15, 1, tzinfo=ET)),
         "first_5min_low": 99.5, "observed_break_price": 99.0,
         "first_5min_return": -0.008, "causal_R5_prior_afternoon": True,
         "first_5min_complete": True, "source_sha256": "a" * 64}
    e.update(kw)
    return e


def gamma_cal():
    return {"session": SESS, "previous_session": PREV, "open": iso(OPENED),
            "verified": True}


def put_chain(expiry, ask, occ, delta=-0.55):
    return [{"symbol": occ, "underlying": "SPY", "right": "put",
             "expiry": expiry, "strike": 99.0, "delta": delta,
             "bid": ask - 0.1, "ask": ask, "bid_size": 50,
             "ask_size": 50}]


class TestOpeningGamma(unittest.TestCase):
    def view(self, chain, event=None, now=GNOW, positions=None):
        return {"now": iso(now), "calendar": gamma_cal(),
                "opening_events": [event or gamma_event()],
                "options": chain,
                "quotes": {"SPY": {"bid": 98.9, "ask": 99.1}},
                "positions": positions or [], "slice": slice10k(),
                "market_open": True}

    def test_entry_a_dte0_2_risk_2pct(self):
        chain = put_chain("2026-10-24", 0.90, "SPY261024P00099000")
        out = ev("aster_open_gamma_a", self.view(chain))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["legs"][0]["right"], "put")
        # risk $200 / (90*1.0015) -> 2 contracts
        self.assertEqual(out[0]["qty"], 2)

    def test_entry_b_dte7_14_risk_half_pct(self):
        chain = put_chain("2026-10-31", 0.40, "SPY261031P00099000")
        out = ev("aster_open_gamma_b", self.view(chain))
        self.assertEqual(len(out), 1)
        # risk $50 / (40*1.0015) -> 1 contract
        self.assertEqual(out[0]["qty"], 1)

    def test_refusals(self):
        chain_a = put_chain("2026-10-24", 0.90, "SPY261024P00099000")
        # B book cannot use the A book's DTE window
        self.assertEqual(ev("aster_open_gamma_b", self.view(chain_a)), [])
        # premium cap: ask 3.00 -> 3.03% of spot > A cap 2.5%
        rich = put_chain("2026-10-24", 3.00, "SPY261024P00099000")
        self.assertEqual(ev("aster_open_gamma_a", self.view(rich)), [])
        # outside 09:35-09:45 ET window
        self.assertEqual(ev("aster_open_gamma_a",
                            self.view(chain_a, now=datetime(
                                2026, 10, 23, 9, 50, tzinfo=ET))), [])
        # stale break quote (>5s)
        stale = gamma_event(
            break_market_at=iso(GNOW - timedelta(seconds=30)),
            break_received_at=iso(GNOW - timedelta(seconds=29)))
        self.assertEqual(ev("aster_open_gamma_a",
                            self.view(chain_a, event=stale)), [])
        # no causal R5 / positive first-5min return / break above low
        self.assertEqual(ev("aster_open_gamma_a", self.view(
            chain_a, event=gamma_event(causal_R5_prior_afternoon=False))),
            [])
        self.assertEqual(ev("aster_open_gamma_a", self.view(
            chain_a, event=gamma_event(first_5min_return=0.004))), [])
        self.assertEqual(ev("aster_open_gamma_a", self.view(
            chain_a, event=gamma_event(observed_break_price=99.6))), [])

    def test_exit_flat_1000_and_overdue(self):
        occ = "SPY261024P00099000"
        pos = [{"symbol": occ, "qty": 2, "avg_price": 0.9,
                "entry_session": SESS,
                "legs": [{"symbol": occ, "underlying": "SPY",
                          "right": "put", "expiry": "2026-10-24",
                          "strike": 99.0, "ratio": 1}]}]
        v = self.view([], now=datetime(2026, 10, 23, 10, 0, tzinfo=ET),
                      positions=pos)
        v["opening_events"] = []
        out = ev("aster_open_gamma_a", v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("same_day_1000_exit", out[0]["reason"])
        v["now"] = iso(datetime(2026, 10, 23, 9, 50, tzinfo=ET))
        self.assertEqual(ev("aster_open_gamma_a", v), [])


class TestE2E(unittest.TestCase):
    def test_rsi2_round_trip_fake_broker_flat(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        import tempfile as tf
        closes = [100 + 0.3 * i for i in range(258)] + [175.0, 170.0]
        view = {"now": "2026-10-23T14:00:00+00:00", "bars": daily(closes),
                "positions": [], "slice": slice10k()}
        entry = ev("aster_rsi2_1d", view)[0]
        broker = FakeBroker(prices={"SPY": 170.0})
        disp = Dispatcher(tf.mkdtemp(), broker,
                          slices={"aster_rsi2_1d": {
                              "capital_usd": 10000.0, "cash_usd": 10000.0}},
                          price_lookup=lambda s: 170.0)
        intent = {"intent_id": entry["intent_id"], "kind": "entry",
                  "symbol": "SPY", "side": "buy", "qty": entry["qty"],
                  "price_hint": 170.0}
        r = disp.process_intent(intent, "aster_rsi2_1d")
        self.assertEqual(r["status"], "filled")
        # WS4: the filled position is the fractional quantity
        self.assertEqual(broker.get_positions(), {"SPY": 5.882352})
        up = [100 + 0.3 * i for i in range(260)]
        pos = [{"symbol": "SPY", "qty": 5, "avg_price": 170.0,
                "bars_held": 2}]
        exit_ = ev("aster_rsi2_1d",
                   {"now": "2026-10-23T15:00:00+00:00", "bars": daily(up),
                    "positions": pos, "slice": slice10k()})[0]
        intent2 = {"intent_id": exit_["intent_id"] + "-x", "kind": "exit",
                   # WS4: the exit sells the ACTUAL held quantity
                   # (5.882352 entered fractionally), not the old
                   # whole-share 5 — a whole-share exit would strand
                   # the fractional remainder.
                   "symbol": "SPY", "side": "sell", "qty": 5.882352,
                   "price_hint": 177.7}
        broker.prices["SPY"] = 177.7
        r2 = disp.process_intent(intent2, "aster_rsi2_1d")
        self.assertEqual(r2["status"], "filled")
        self.assertEqual(broker.get_positions(), {})  # flat

    def test_native_round_trip_fake_broker_flat(self):
        from desk3.broker import FakeBroker
        btc = [100 + 0.5 * i for i in range(210)]
        bars = {}
        bars.update(daily(btc, "BTC-USD"))
        bars.update(daily(btc, "ETH-USD"))
        view = {"now": "2026-10-23T14:00:00+00:00", "bars": bars,
                "positions": [], "slice": slice10k()}
        entry = ev("aster_native_eth_sma200", view)[0]
        broker = FakeBroker(prices={"ETH-USD": 204.5})
        broker.submit_order("v3-t1", "ETH-USD", "buy", entry["qty"],
                            "market")
        got = broker.get_order_by_client_id("v3-t1")
        self.assertEqual(got["status"], "filled")
        down = [300 - 0.5 * i for i in range(210)]
        bars2 = {}
        bars2.update(daily(btc, "BTC-USD"))
        bars2.update(daily(down, "ETH-USD"))
        pos = [{"symbol": "ETH-USD", "qty": entry["qty"],
                "avg_price": 204.5}]
        exit_ = ev("aster_native_eth_sma200",
                   {"now": "2026-10-24T14:00:00+00:00", "bars": bars2,
                    "positions": pos,
                    "slice": {"capital_usd": 10000.0,
                              "cash_usd": 20.0}})[0]
        self.assertEqual(exit_["kind"], "exit")
        broker.submit_order("v3-t2", "ETH-USD", "sell", entry["qty"],
                            "market")
        broker.get_order_by_client_id("v3-t2")
        self.assertEqual(broker.get_positions(), {})  # flat


if __name__ == "__main__":
    unittest.main()
