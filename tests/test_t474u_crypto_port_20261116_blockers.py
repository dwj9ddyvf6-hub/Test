"""T474U-CRYPTO-PORT-20261116 blockers.

Defect: the 9 crypto sleeves of GrokBot's t474u intake
(crypto_bratr_ada/enj/link, crypto_mfi_ada/enj/link,
crypto_stdev_ada/enj/link; COMMITMENTS GROKBOT-T474U-INTAKE-20261114)
stood BLOCKED since 2026-11-15: no faithful desk-side port of md2's
mdesk/engines/t474u_x.py existed, and no book vehicle exists for
ADA/ENJ/LINK underlyings (the book is options only; no US-listed
options on those underlyings; no substitute may be invented).

Cure (this landing):
- desk3/t474u_crypto.py: function-for-function port of the source
  CryptoFilterTwin (4h 10-bar breakout host; bar_range_atr k=2.0,
  mfi_gate theta=15, btc_stdev k=0.5 frozen params; MIN_4H=300
  warm-up gate; fixed16h exit from confirm_t; pos_frac 0.25 of the
  $10k slice) + adapters3 wrappers + config rows (24h session).
- Vehicles from the desk's own records: ADA/USD and LINK/USD Alpaca
  spot; ENJ via the dispatcher's kraken_paper class (the 3 ENJ ids
  join ENJ_PAPER_SLEEVES; rows carry own_book_view).
- Fidelity proven in proof/t474u/ (harness + result): the ported
  signal code reproduces historical_fires.json (counts + last_t)
  and the original code's fire lists exactly, and the ported trade
  simulation reproduces sweeps.json IS/OOS fee-stress metrics
  field-for-field, for the 9 sleeves and the 3 BTC controls.

Fail direction: on the pre-cure tree desk3/t474u_crypto.py and the
adapters do not exist (imports fail), config/sleeves.json carries
none of the 9 ids, and ENJ_PAPER_SLEEVES lacks the 3 ENJ ids —
every test below fails there. Verified on a git-archive copy of
the pre-cure tree (9728bd56) at landing.
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3 import t474u_crypto as T  # noqa: E402
from desk3.dispatcher import ENJ_PAPER_SLEEVES  # noqa: E402

IDS = [f"crypto_{k}_{b}" for k in ("bratr", "mfi", "stdev")
       for b in ("ada", "enj", "link")]
# Gate-wired coverage names, literal (blocker ratchet): the nine
# adapter modules adapters3.crypto_bratr_ada, adapters3.crypto_bratr_enj,
# adapters3.crypto_bratr_link, adapters3.crypto_mfi_ada,
# adapters3.crypto_mfi_enj, adapters3.crypto_mfi_link,
# adapters3.crypto_stdev_ada, adapters3.crypto_stdev_enj,
# adapters3.crypto_stdev_link, over the engine desk3.t474u_crypto.
ADAPTER_MODULES = tuple(f"adapters3.{sid}" for sid in IDS)
PROOF = os.path.join(ROOT, "proof", "t474u")


def _load(name):
    return json.load(open(os.path.join(PROOF, name)))


def _bars(inst):
    raw = _load(f"bars_{inst}.json")
    return [{"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4],
             "v": r[5]} for r in raw]


def _view(bars, sym):
    rows = [{"t": datetime.fromtimestamp(b["t"], timezone.utc).isoformat(),
             "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
             "v": b["v"]} for b in bars]
    return {"bars": {f"{sym}|4Hour": rows}, "positions": [],
            "slice": {"cash_usd": 10000.0}}


class TestRegistration(unittest.TestCase):
    def test_config_rows_exactly_the_nine_new(self):
        rows = json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))["sleeves"]
        by_id = {r["id"]: r for r in rows}
        for sid in IDS:
            self.assertIn(sid, by_id)
            r = by_id[sid]
            self.assertEqual(r["module"], f"adapters3.{sid}")
            self.assertEqual(r["session"], "24h")
            self.assertEqual(r["cadence_s"], 14400)
            self.assertFalse(r["parked"])
            self.assertEqual(r["slice"]["capital_usd"], 10000.0)
        for sid in ("crypto_bratr_enj", "crypto_mfi_enj",
                    "crypto_stdev_enj"):
            self.assertTrue(by_id[sid].get("own_book_view"), sid)
            self.assertIn("ENJ-PAPER-20261116",
                          by_id[sid]["params"]["parked_reason"])

    def test_adapters_import_and_delegate(self):
        import importlib
        for sid in IDS:
            m = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(m.SLEEVE_ID, sid)
            self.assertEqual(m.evaluate({"bars": {}, "positions": []}),
                             [])

    def test_config_rows_match_engine(self):
        rows = {r["id"]: r for r in T.config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))


class TestFrozenParams(unittest.TestCase):
    def test_params_are_the_frozen_source_values(self):
        self.assertEqual(T.PARAMS["bar_range_atr"]["k"], 2.0)
        self.assertEqual(T.PARAMS["bar_range_atr"]["atr_n"], 14)
        self.assertEqual(T.PARAMS["mfi_gate"]["theta"], 15.0)
        self.assertEqual(T.PARAMS["mfi_gate"]["mfi_n"], 14)
        self.assertEqual(T.PARAMS["mfi_gate"]["sma_n"], 30)
        self.assertEqual(T.PARAMS["btc_stdev"]["k"], 0.5)
        self.assertEqual(T.PARAMS["btc_stdev"]["n"], 20)
        self.assertEqual(T.MIN_4H, 300)
        self.assertEqual(T.POS_FRAC, 0.25)
        self.assertEqual(T.HOLD_H, 16)
        self.assertEqual(T.FEE_1X_CRYPTO, 0.001)


class TestFidelity(unittest.TestCase):
    def test_fires_match_recorded_and_original_code(self):
        fires_ref = _load("historical_fires.json")
        orig = _load("original_code_fires.json")["sleeves"]
        for base, inst in (("ADA", "ADA-USDT"), ("ENJ", "ENJ-USDT"),
                           ("LINK", "LINK-USDT"), ("BTC", "BTC-USDT")):
            bars = _bars(inst)
            self.assertEqual(len(bars), 399)
            for kind in ("bratr", "mfi", "stdev"):
                sid = f"crypto_{kind}_{base.lower()}"
                idx = T.fires_series(kind, bars)
                self.assertEqual(idx, orig[sid]["indices"], sid)
                self.assertEqual(len(idx), fires_ref[sid]["n_fires"], sid)
                self.assertEqual(float(bars[idx[-1]]["t"]),
                                 fires_ref[sid]["last_t"], sid)

    def test_trade_metrics_match_recorded_sweeps(self):
        sweeps = _load("sweeps_expected.json")
        fam = {"bratr": "bar_range_atr", "mfi": "mfi_gate",
               "stdev": "btc_stdev"}
        for base, inst in (("ADA", "ADA-USDT"), ("ENJ", "ENJ-USDT"),
                           ("LINK", "LINK-USDT")):
            bars = _bars(inst)
            for kind in ("bratr", "mfi", "stdev"):
                exp = sweeps["families"][fam[kind]][f"{base}USDT"]
                self.assertEqual(T.simulate_trades(kind, bars),
                                 {"IS": exp["IS"], "OOS": exp["OOS"]},
                                 f"crypto_{kind}_{base.lower()}")

    def test_result_file_passes(self):
        res = _load("t474u_fidelity_result.json")
        self.assertTrue(res["pass"])
        for sid in IDS:
            self.assertEqual(res["sleeves"][sid]["verdict"], "PASS", sid)


class TestLiveEvaluate(unittest.TestCase):
    # Each sleeve is driven to its own last recorded fire bar at
    # index >= 300 (original_code_fires.json); bar index 320 is a
    # fire for none of the 9.
    def test_entry_fires_on_recorded_fire_bar(self):
        orig = _load("original_code_fires.json")["sleeves"]
        for base, inst in (("ADA", "ADA-USDT"), ("ENJ", "ENJ-USDT"),
                           ("LINK", "LINK-USDT")):
            bars = _bars(inst)
            for kind in ("bratr", "mfi", "stdev"):
                sid = f"crypto_{kind}_{base.lower()}"
                fi = max(i for i in orig[sid]["indices"] if i >= 300)
                out = T.evaluate(sid, _view(bars[:fi + 1], f"{base}/USD"),
                                 {"state_dir": tempfile.mkdtemp()})
                self.assertEqual(len(out), 1, sid)
                d = out[0]
                self.assertEqual(d["kind"], "entry")
                self.assertEqual(d["symbol"], f"{base}/USD")
                self.assertEqual(d["side"], "buy")
                self.assertEqual(d["time_in_force"], "gtc")
                self.assertAlmostEqual(
                    d["qty"], 0.25 * 10000.0 / bars[fi]["c"], places=6)
                self.assertEqual(d["price_hint"], bars[fi]["c"])

    def test_no_fire_on_non_fire_bar(self):
        for base, inst in (("ADA", "ADA-USDT"), ("ENJ", "ENJ-USDT"),
                           ("LINK", "LINK-USDT")):
            bars = _bars(inst)
            for kind in ("bratr", "mfi", "stdev"):
                sid = f"crypto_{kind}_{base.lower()}"
                out = T.evaluate(sid, _view(bars[:321], f"{base}/USD"),
                                 {"state_dir": tempfile.mkdtemp()})
                self.assertEqual(out, [], sid)

    def test_warmup_gate_299_bars(self):
        bars = _bars("ADA-USDT")
        out = T.evaluate("crypto_bratr_ada",
                         _view(bars[:299], "ADA/USD"),
                         {"state_dir": tempfile.mkdtemp()})
        self.assertEqual(out, [])

    def test_exit_fixed16h_from_confirm_t(self):
        tmp = tempfile.mkdtemp()
        sid = "crypto_mfi_link"
        bars = _bars("LINK-USDT")
        view = _view(bars[:338], "LINK/USD")
        out = T.evaluate(sid, view, {"state_dir": tmp})
        self.assertEqual(len(out), 1)  # entry writes confirm_t state
        view2 = _view(bars, "LINK/USD")
        view2["positions"] = [{"symbol": "LINK/USD", "qty": out[0]["qty"],
                               "avg_price": bars[337]["c"]}]
        confirm = datetime.fromtimestamp(bars[337]["t"] + 4 * 3600,
                                         timezone.utc)
        early = T.evaluate(sid, view2, {
            "state_dir": tmp,
            "now": (confirm + timedelta(hours=15)).isoformat()})
        self.assertEqual(early, [])
        due = T.evaluate(sid, view2, {
            "state_dir": tmp,
            "now": (confirm + timedelta(hours=16)).isoformat()})
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0]["kind"], "exit")
        self.assertEqual(due[0]["position_intent"], "sell_to_close")


class TestVehicles(unittest.TestCase):
    def test_enj_ids_in_kraken_paper_class(self):
        for sid in ("crypto_bratr_enj", "crypto_mfi_enj",
                    "crypto_stdev_enj"):
            self.assertIn(sid, ENJ_PAPER_SLEEVES)
        for sid in IDS:
            if "enj" not in sid:
                self.assertNotIn(sid, ENJ_PAPER_SLEEVES)

    def test_enj_entry_fills_kraken_paper_never_submits(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher

        class LiveBookFake(FakeBroker):
            live_book = True

        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = Dispatcher(tmp, broker,
                       slices={"crypto_bratr_enj":
                               {"capital_usd": 10000, "cash_usd": 10000}},
                       price_lookup=lambda s: None)
        intent = {"intent_id": "t474u-enj-1", "kind": "entry",
                  "symbol": "ENJ/USD", "side": "buy", "qty": 100,
                  "order_type": "market", "time_in_force": "gtc",
                  "price_hint": 0.02, "position_intent": "buy_to_open"}
        r = d.process_intent(intent, "crypto_bratr_enj")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(r["venue"], "kraken_paper")
        self.assertEqual(broker.submit_count, 0)


class TestPinsUntouched(unittest.TestCase):
    def test_saty_sol_pin_unchanged(self):
        h = hashlib.sha256(open(os.path.join(
            ROOT, "sleeves", "saty_sol.py"), "rb").read()).hexdigest()
        self.assertEqual(
            h, "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416"
               "cc08962bdc")


if __name__ == "__main__":
    unittest.main()
