"""PORT-BATCH3 blockers: free_kraken_enj_spot, free_kraken_link_basis,
free_kraken_link_breakdown, free_kraken_link_crowded, free_opt_own_iv,
free_opt_pair, free_opt_parity, free_opt_release, free_opt_tail,
free_opt_wheel.

Oracle: muse-desk-v2 adapters driven on identical fixtures (v2
tests/test_batch3_fixture.py + test_designed_{enj,basis,parity}.py
scenarios). At port time all 26 scenarios produced intent dicts
byte-identical between the v2 adapter and this v3 port (oracle run
recorded in PROGRESS.md). These tests pin the recorded expectations:
entry fires, each designed exit fires, refusals refuse. Fail direction:
on the pre-port tree desk3.sleeves.<id> does not exist -> errors.
"""
import datetime, hashlib, importlib, json, os, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
IDS = ["free_kraken_enj_spot", "free_kraken_link_basis",
       "free_kraken_link_breakdown", "free_kraken_link_crowded",
       "free_opt_own_iv", "free_opt_pair", "free_opt_parity",
       "free_opt_release", "free_opt_tail", "free_opt_wheel"]
NOW = "2026-10-23T10:00:00-04:00"
NOW_UTC = "2026-10-23T14:00:00+00:00"
FRESH = {"t": NOW_UTC, "received_at": NOW_UTC, "ap": 2.5, "bp": 2.4}
CALL = "SPY261030C00500000"
PUT = "SPY261030P00500000"
KNOW = "2026-10-14T04:00:00-04:00"
QUOTE = {"quote": {"bid": 89.5, "ask": 89.6}}
DATES11 = [f"2026-10-{d:02d}" for d in range(2, 13)]


def ev(sid, now=NOW, extra=None, positions=None, bars=None):
    mod = importlib.import_module(f"desk3.sleeves.{sid}")
    view = {"now": now, "extra": extra or {}, "positions": positions or [],
            "bars": bars or {},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    return mod.evaluate(view, {"sleeve_id": sid})


def pos(sym, qty, px, opened):
    return {"symbol": sym, "qty": qty, "avg_price": px,
            "opened_at": opened, "intent_id": "seed"}


def straddle():
    return {"package": {"forecast": 25.0, "iv": 20.0, "legs": [
        {"right": "call", "symbol": CALL, "ask": 2.5, "source_at": NOW_UTC},
        {"right": "put", "symbol": PUT, "ask": 2.4, "source_at": NOW_UTC}]}}


def kraken_bars(bd=True):
    bars = []
    start = datetime.datetime(2026, 10, 10, tzinfo=datetime.timezone.utc)
    for i in range(25):
        t = start + datetime.timedelta(hours=4 * i)
        last = i == 24
        bars.append({"t": t.isoformat().replace("+00:00", "Z"), "o": 100.0,
                     "h": 101.0, "l": 89.0 if (last and bd) else 99.0,
                     "c": 90.0 if (last and bd) else 100.0, "v": 10.0})
    return {"PF_LINKUSD|4Hour": bars}


class TestBatch3Entries(unittest.TestCase):
    def test_own_iv_entry(self):
        out = ev("free_opt_own_iv", extra={"quote": FRESH, **straddle()})
        self.assertEqual(len(out), 2)
        self.assertTrue(all(i["side"] == "buy" and
                            i["position_intent"] == "buy_to_open" for i in out))

    def test_pair_entry(self):
        pkg = {"package": {"legs": [
            {"underlying": "SPY", "symbol": CALL, "ask": 2.5},
            {"underlying": "QQQ", "symbol": "QQQ261030C00350000", "ask": 1.5}],
            "hedge_frozen": True, "hedge": {"ratio": 0.5}}}
        out = ev("free_opt_pair", extra={"quote": FRESH, **pkg})
        self.assertEqual(len(out), 2)

    def test_release_entry_and_unverified_refusal(self):
        ex = {"quote": FRESH, **straddle(),
              "events": [{"session": "2026-10-23", "verified": True}]}
        self.assertEqual(len(ev("free_opt_release", extra=ex)), 2)
        ex["events"] = [{"session": "2026-10-23", "verified": False}]
        self.assertEqual(ev("free_opt_release", extra=ex), [])

    def test_tail_entry_and_threshold_refusal(self):
        q = {"symbol": PUT, "t": NOW_UTC, "received_at": NOW_UTC,
             "ap": 1.2, "bp": 1.1}
        out = ev("free_opt_tail", extra={"quote": q, "underlying_return": -0.05})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], PUT)
        self.assertEqual(ev("free_opt_tail",
                            extra={"quote": q, "underlying_return": -0.01}), [])

    def test_wheel_entry_and_cash_refusal(self):
        q = {"symbol": PUT, "t": NOW_UTC, "received_at": NOW_UTC,
             "ap": 1.2, "bp": 1.1, "strike": 50}
        out = ev("free_opt_wheel", extra={"quote": q, "cash": 100000.0})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["side"], "sell")
        self.assertEqual(out[0]["position_intent"], "sell_to_open")
        self.assertEqual(ev("free_opt_wheel",
                            extra={"quote": q, "cash": 100.0}), [])

    def test_breakdown_entry_and_no_signal(self):
        out = ev("free_kraken_link_breakdown", now=KNOW, extra=QUOTE,
                 bars=kraken_bars(True))
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0]["kind"], out[0]["side"], out[0]["qty"]),
                         ("entry", "sell", 1))
        self.assertEqual(ev("free_kraken_link_breakdown", now=KNOW,
                            extra=QUOTE, bars=kraken_bars(False)), [])

    def test_crowded_entry(self):
        rates = [{"timestamp": f"2026-10-{1 + d // 24:02d}T{d % 24:02d}:00:00+00:00",
                  "fundingRate": 0.0001} for d in range(39)]
        rates.append({"timestamp": "2026-10-14T07:00:00+00:00",
                      "fundingRate": 0.001})
        out = ev("free_kraken_link_crowded", now=KNOW,
                 extra={**QUOTE, "funding_rates": rates}, bars=kraken_bars(True))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["side"], "sell")

    def test_enj_entry_and_balanced_refusal(self):
        def book(bid, ask, bd, ad):
            return {"bids": [[str(bid), str(bd), 1792856027]],
                    "asks": [[str(ask), str(ad), 1792856027]]}
        now = "2026-10-23T12:00:00+00:00"
        out = ev("free_kraken_enj_spot", now=now,
                 extra={"book": book(1.0, 1.001, 300, 100)})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 9990)
        self.assertEqual(ev("free_kraken_enj_spot", now=now,
                            extra={"book": book(1.0, 1.001, 100, 100)}), [])

    def test_basis_entry_and_low_premium_refusal(self):
        t0 = datetime.datetime(2026, 10, 23,
                               tzinfo=datetime.timezone.utc).timestamp()
        now = datetime.datetime.fromtimestamp(
            t0 + 12 * 3600, tz=datetime.timezone.utc).isoformat()

        def extra(bps):
            series = [{"t": t0 + i * 14400, "spot_close": 11.0,
                       "perp_close": 11.0 * (1 + b / 10000)}
                      for i, b in enumerate(bps)]
            return {"basis": {"aligned": 3, "required": 3,
                              "decision": {"status": "READY",
                                           "reason": "fixture"},
                              "series": series},
                    "quote": {"bid": 11.044, "ask": 11.055}}
        out = ev("free_kraken_link_basis", now=now, extra=extra([0, 0, 40]))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["side"], "sell")
        self.assertEqual(ev("free_kraken_link_basis", now=now,
                            extra=extra([0, 0, 10])), [])
        self.assertEqual(ev("free_kraken_link_basis", extra={}), [])

    def test_parity_entry_expands_to_four_legs(self):
        exp = "2026-11-06"
        c1, p1 = "SPY261106C00595000", "SPY261106P00595000"
        c2, p2 = "SPY261106C00600000", "SPY261106P00600000"

        def q(s, st, r, b, a):
            return {"symbol": s, "expiration": exp, "strike": st,
                    "right": r, "bid": b, "ask": a}
        cheap = [q(c1, 595, "call", 12.00, 12.10), q(p1, 595, "put", 7.00, 7.10),
                 q(c2, 600, "call", 10.00, 10.10), q(p2, 600, "put", 9.35, 9.45)]
        out = ev("free_opt_parity", now="2026-10-23T15:00:00+00:00",
                 extra={"parity_quotes": cheap, "parity_spot": 600.0})
        self.assertEqual(len(out), 4)
        self.assertTrue(all(i["package_id"] ==
                            "spy-box-2026-11-06-595-600-long" for i in out))


class TestBatch3Exits(unittest.TestCase):
    QS = {CALL: {"bid": 1.0, "ask": 1.1}, PUT: {"bid": 1.0, "ask": 1.1}}

    def test_own_iv_exit_ten_sessions(self):
        out = ev("free_opt_own_iv",
                 extra={"session_dates": DATES11, "quotes": self.QS},
                 positions=[pos(CALL, 1, 2.0, "2026-10-01T14:00:00+00:00"),
                            pos(PUT, 1, 2.0, "2026-10-01T14:00:00+00:00")])
        self.assertEqual(len(out), 2)
        self.assertTrue(all(i["kind"] == "exit" for i in out))

    def test_pair_exit_ten_sessions(self):
        q2 = "QQQ261030C00350000"
        out = ev("free_opt_pair",
                 extra={"session_dates": DATES11,
                        "quotes": {CALL: {"bid": 1.0, "ask": 1.1},
                                   q2: {"bid": 1.0, "ask": 1.1}}},
                 positions=[pos(CALL, 1, 2.0, "2026-10-01T14:00:00+00:00"),
                            pos(q2, 1, 1.5, "2026-10-01T14:00:00+00:00")])
        self.assertEqual(len(out), 2)
        self.assertTrue(all(i["kind"] == "exit" for i in out))

    def test_release_exit_next_session(self):
        out = ev("free_opt_release",
                 extra={"session_dates": ["2026-10-23"], "quotes": self.QS},
                 positions=[pos(CALL, 1, 2.0, "2026-10-22T14:00:00+00:00"),
                            pos(PUT, 1, 2.0, "2026-10-22T14:00:00+00:00")])
        self.assertEqual(len(out), 2)
        self.assertTrue(all(i["kind"] == "exit" for i in out))

    def test_tail_exit_premium_loss(self):
        out = ev("free_opt_tail",
                 extra={"session_dates": ["2026-10-21", "2026-10-22",
                                          "2026-10-23"],
                        "quotes": {PUT: {"bid": 0.9, "ask": 1.0}}},
                 positions=[pos(PUT, 1, 2.0, "2026-10-20T14:00:00+00:00")])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")

    def test_wheel_exit_at_expiry(self):
        out = ev("free_opt_wheel", extra={"quotes": {}},
                 positions=[pos("SPY261023P00500000", -1, 1.1,
                                "2026-10-20T14:00:00+00:00")])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["position_intent"], "buy_to_close")

    def test_breakdown_and_crowded_exits(self):
        st = {"PF_LINKUSD": {"qty": -1,
                             "entry_due_at": "2026-10-13T08:00:00+00:00"}}
        out = ev("free_kraken_link_breakdown", now=KNOW,
                 extra={**QUOTE, "sleeve_state": st})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["side"], "buy")
        out = ev("free_kraken_link_crowded", now=KNOW,
                 extra={**QUOTE, "sleeve_state": st})
        self.assertEqual(len(out), 1)

    def test_enj_exit_on_depth_flip(self):
        book = {"bids": [["1.0", "100", 1792856027]],
                "asks": [["1.001", "300", 1792856027]]}
        out = ev("free_kraken_enj_spot", now="2026-10-23T12:00:00+00:00",
                 extra={"book": book},
                 positions=[pos("ENJUSD", 9990, 1.001,
                                "2026-10-23T11:00:00+00:00")])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")

    def test_parity_exit_on_convergence(self):
        exp = "2026-11-06"
        c1, p1 = "SPY261106C00595000", "SPY261106P00595000"
        c2, p2 = "SPY261106C00600000", "SPY261106P00600000"

        def q(s, st, r, b, a):
            return {"symbol": s, "expiration": exp, "strike": st,
                    "right": r, "bid": b, "ask": a}
        conv = [q(c1, 595, "call", 12.00, 12.10), q(p1, 595, "put", 7.00, 7.10),
                q(c2, 600, "call", 9.00, 9.10), q(p2, 600, "put", 9.18, 9.28)]
        t = "2026-10-23T15:00:00+00:00"
        st = {c1: {"qty": 1, "entry_due_at": t}, p1: {"qty": -1, "entry_due_at": t},
              c2: {"qty": -1, "entry_due_at": t}, p2: {"qty": 1, "entry_due_at": t}}
        out = ev("free_opt_parity", now="2026-10-23T15:00:00+00:00",
                 extra={"parity_quotes": conv, "parity_spot": 600.0,
                        "sleeve_state": st})
        self.assertEqual(len(out), 4)
        self.assertTrue(all(i["kind"] == "exit" for i in out))


class TestBatch3FidelityAndConfig(unittest.TestCase):
    def test_strategy_files_match_v2_except_import_line(self):
        v2 = "/home/hatch/workspace/muse-desk-v2/sleeves"
        if not os.path.isdir(v2):
            self.skipTest("v2 reference tree absent")
        for sid in IDS:
            a = open(os.path.join(v2, f"{sid}.py")).read().splitlines()
            b = open(os.path.join(ROOT, "desk3", "strategies",
                                  f"{sid}.py")).read().splitlines()
            self.assertEqual(len(a), len(b), sid)
            diffs = [(x, y) for x, y in zip(a, b) if x != y]
            self.assertEqual(len(diffs), 1, (sid, diffs))
            self.assertIn("from core.sleeve import", diffs[0][0])
            self.assertIn("from desk3.contract import", diffs[0][1])

    def test_config_rows_registered_with_inputs(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = {s["id"]: s for s in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, rows)
            self.assertEqual(rows[sid]["module"], f"desk3.sleeves.{sid}")
            self.assertTrue(rows[sid]["inputs"])
            mod = importlib.import_module(f"desk3.sleeves.{sid}")
            self.assertEqual(tuple(rows[sid]["inputs"]), mod.INPUTS)


if __name__ == "__main__":
    unittest.main()
