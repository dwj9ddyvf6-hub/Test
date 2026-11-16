"""Batch-2 port blockers (PORT-B2): donchian_crypto, earnings_buyback,
em_1587, ema_vwap, ema_vwap_options, fear_premium, free_etf,
free_kraken_ada_basis, free_kraken_ada_breakdown, free_kraken_ada_crowded.

Oracle: muse-desk-v2's own fixture drives (tests/test_batch1_fixtures.py
donchian_crypto; tests/test_batch2_fixture.py for the rest;
tests/test_designed_basis.py for the authored basis logic). Same fixture
inputs are fed through the v3 worker entrypoint evaluate(view, ctx);
assertions are v2's own (kind/symbol/side/qty/reason). Strategy and
adapter files are sha256-pinned to the v2 copies, so any drift in the
ported math fails here before behavior is even driven.

Fail direction: on the pre-port tree adapters3/sleeves/adapters do not
exist, so every drive errors and the hash pins fail.
"""
import hashlib, importlib, json, os, sys, tempfile, unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
V2 = "/home/hatch/workspace/muse-desk-v2"
ET = ZoneInfo("America/New_York")
IDS = ["donchian_crypto", "earnings_buyback", "em_1587", "ema_vwap",
       "ema_vwap_options", "fear_premium", "free_etf",
       "free_kraken_ada_basis", "free_kraken_ada_breakdown",
       "free_kraken_ada_crowded"]


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def drive(sid, bars=None, now="2026-10-23T15:00:00-04:00", extra=None,
          positions=None, params=None, capital=100000.0):
    mod = importlib.import_module(f"adapters3.{sid}")
    p = dict(params or {})
    if extra is not None:
        p["extra"] = extra
    view = {"now": now, "bars": bars or {}, "positions": positions or [],
            "slice": {"capital_usd": capital, "cash_usd": capital},
            "params": p, "session_fills": []}
    ctx = {"state_dir": tempfile.mkdtemp(prefix=f"v3b2-{sid}-"),
           "sleeve_id": sid, "cycle_id": "fixture"}
    return mod.evaluate(view, ctx)


def positions_from_fills(fills):
    pos = {}
    for f in fills or []:
        sym = f["symbol"]
        q = float(f["qty"]) * (1 if f.get("side") == "buy" else -1)
        cur = pos.get(sym)
        if cur is None:
            pos[sym] = {"symbol": sym, "qty": q,
                        "avg_price": float(f.get("price", 0)),
                        "opened_at": f.get("ts"),
                        "intent_id": f.get("intent_id")}
        else:
            cur["qty"] += q
    return [p for p in pos.values() if p["qty"] != 0]


def biz_days(end, n):
    days, d = [], end
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return sorted(days)


def daily(end, closes, vol=1000.0, last_hl=None):
    days = biz_days(end, len(closes))
    out = []
    for d, c in zip(days, closes):
        h = l = c
        if last_hl and d == days[-1]:
            h, l = last_hl
        out.append({"t": f"{d.isoformat()}T00:00:00Z", "o": float(c),
                    "h": float(h), "l": float(l), "c": float(c), "v": vol})
    return out


END = date(2026, 10, 22)
NOW = "2026-10-23T15:00:00-04:00"
XYZ_BARS = daily(END, [100.0] * 34 + [97.0], last_hl=(100.0, 96.0))


# SILENT-SKIP-SIZING-20261116 named deviation (2026-11-16):
# sleeves/free_etf.py carries one authorized v3-side cure (a
# whole-share target that floors to 0 with nothing held now enters
# the same dollar target fractionally; adapter untouched, held-name
# behavior unchanged). Its port bytes are pinned to the cured
# sha256 below instead of the v2 bytes; every other sleeve and
# every adapter in this class keeps full v2 byte-identity.
FREE_ETF_CURED_SHA256 = \
    "9a59efbb8944a364623e9e067a236d0dd198a598e5236cfae5d15f1f0af1474f"


class TestByteIdentityAndConfig(unittest.TestCase):
    def test_sleeve_and_adapter_bytes_match_v2(self):
        for sid in IDS:
            if sid == "free_etf":
                self.assertEqual(_sha(os.path.join(ROOT, "sleeves", f"{sid}.py")),
                                 FREE_ETF_CURED_SHA256, sid)
            else:
                self.assertEqual(_sha(os.path.join(ROOT, "sleeves", f"{sid}.py")),
                                 _sha(os.path.join(V2, "sleeves", f"{sid}.py")), sid)
            self.assertEqual(_sha(os.path.join(ROOT, "adapters", f"{sid}.py")),
                             _sha(os.path.join(V2, "adapters", f"{sid}.py")), sid)

    def test_config_rows_match_v2(self):
        from desk3.port_batch2 import CONFIG_ROWS, INPUTS, register
        v2 = {s["id"]: s for s in
              json.load(open(os.path.join(V2, "config", "sleeves.json")))["sleeves"]}
        cfg = {r["id"]: r for r in
               json.load(open(os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]}
        # CONFIG-DECISIONS-20261104: ema_vwap_options is a verified
        # multi-day swing design; its ported flatten demand was
        # never implemented in either tree, so both v3 sources
        # (CONFIG_ROWS and the live config) carry the decided
        # divergence from v2, pinned here by name. Every other
        # field of every batch-2 row still matches v2 exactly.
        decided = {("ema_vwap_options", "flat_by_close"): False,
                   ("ema_vwap_options", "flatten_time_et"): None}
        # CONFIG-DECISIONS-20261104 (park half): the three batch-2
        # free_kraken rows are parked in the live config, so their
        # params carry the dated parked_reason v2 never had. The
        # port template (CONFIG_ROWS) is untouched, per the ENJ
        # park precedent; the live row must equal v2's params plus
        # exactly that stamp.
        decided_park = {"free_kraken_ada_basis",
                        "free_kraken_ada_breakdown",
                        "free_kraken_ada_crowded"}
        for sid in IDS:
            for k in ("cadence_s", "slice", "bp_buffer_frac", "flat_by_close",
                      "flatten_time_et", "session", "params"):
                if k == "params" and sid in decided_park:
                    self.assertEqual(CONFIG_ROWS[sid].get(k),
                                     v2[sid].get(k), (sid, k))
                    cparams = dict(cfg[sid].get(k) or {})
                    reason = cparams.pop("parked_reason", "")
                    # CLEAR-THE-BOARD-20261114: the rows are
                    # unparked and fed; the stamp is the CTB stamp
                    # and keeps the PF-DOOR-20261104 provenance.
                    self.assertIn("CLEAR-THE-BOARD-20261114", reason, sid)
                    self.assertIn("PF_", reason, sid)
                    self.assertIn("PF-DOOR-20261104", reason, sid)
                    self.assertEqual(cparams, v2[sid].get(k), (sid, k))
                    continue
                if (sid, k) in decided:
                    self.assertEqual(CONFIG_ROWS[sid].get(k),
                                     decided[(sid, k)], (sid, k))
                    self.assertEqual(cfg[sid].get(k),
                                     decided[(sid, k)], (sid, k))
                    continue
                self.assertEqual(CONFIG_ROWS[sid].get(k), v2[sid].get(k), (sid, k))
                self.assertEqual(cfg[sid].get(k), v2[sid].get(k), (sid, k))
            self.assertTrue(INPUTS[sid], sid)

    def test_registry_unfed_when_producer_missing(self):
        from desk3.port_batch2 import register
        from desk3.registry import Registry
        reg = register(Registry())
        fed = reg.fed_states(now=1000.0)
        for sid in IDS:
            self.assertEqual(fed[sid]["state"], "UNFED", sid)
        for name in ("bars", "broker_readback", "options", "kraken",
                     "earnings", "buyback_scan", "quotes", "vix", "etf_books"):
            reg.mark_produced(name, ts=1000.0)
        fed = reg.fed_states(now=1100.0)
        for sid in IDS:
            self.assertEqual(fed[sid]["state"], "FED", sid)


class TestDonchianCrypto(unittest.TestCase):
    def _bars(self, closes, highs, lows, vols):
        days = biz_days(date(2026, 10, 23), len(closes))
        return [{"t": f"{d.isoformat()}T14:00:00Z", "o": float(c),
                 "h": float(h), "l": float(l), "c": float(c), "v": float(v)}
                for d, c, h, l, v in zip(days, closes, highs, lows, vols)]

    def test_entry_and_exit(self):
        bars = self._bars([100.0] * 44 + [110.0], [106.25] * 44 + [112.0],
                          [93.75] * 44 + [99.5], [10.0] * 45)
        out = drive("donchian_crypto", {"SOLUSD|15Min": bars},
                    now="2026-10-23T14:00:00-04:00", capital=10000.0)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 1)
        self.assertEqual(out[0]["symbol"], "SOLUSD")
        xbars = self._bars([100.0] * 14 + [90.0], [101.0] * 15,
                           [99.0] * 14 + [89.0], [10.0] * 15)
        fills = [{"symbol": "SOLUSD", "qty": 2, "side": "buy", "price": 100.0,
                  "ts": "2026-10-20T14:00:00Z", "intent_id": "seed"}]
        out = drive("donchian_crypto", {"SOLUSD|15Min": xbars},
                    now="2026-10-23T14:00:00-04:00", capital=10000.0,
                    positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["qty"], 2)

    def test_refusal_no_bars(self):
        self.assertEqual(drive("donchian_crypto", {},
                               now="2026-10-23T14:00:00-04:00"), [])


class TestEmaVwap(unittest.TestCase):
    def test_entry_control_rule(self):
        out = drive("ema_vwap", {"XYZ|1Day": XYZ_BARS},
                    params={"symbols": ["XYZ"]},
                    extra={"ema_vwap_improve": {"deviation_geometry_gate": False}})
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["symbol"], e[0]["side"], e[0]["qty"]),
                         ("XYZ", "buy", 32))
        self.assertEqual(e[0]["stop_price"], 72.75)

    def test_entry_refused_by_enhance_gate_default_on(self):
        out = drive("ema_vwap", {"XYZ|1Day": XYZ_BARS},
                    params={"symbols": ["XYZ"]}, extra={})
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])

    def test_exit_profit_target(self):
        bars = daily(END, [90.0] * 30 + [100.0] * 5)
        first = bars[0]["t"][:10]
        extra = {"sleeve_state": {"XYZ": {"position": {
            "entry_px": 90.0, "qty": 10, "entry_date": first}}}}
        fills = [{"symbol": "XYZ", "qty": 10, "side": "buy", "price": 90.0,
                  "ts": "2026-09-14T14:00:00Z", "intent_id": "seed"}]
        out = drive("ema_vwap", {"XYZ|1Day": bars}, params={"symbols": ["XYZ"]},
                    extra=extra, positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual((x[0]["qty"], x[0]["side"]), (10, "sell"))


OPT_CHAIN = {"XYZ": [
    {"symbol": "XYZ261112C00095000", "strike": 95.0, "expiration": "2026-11-12"},
    {"symbol": "XYZ261112C00105000", "strike": 105.0, "expiration": "2026-11-12"}]}
OPT_QUOTES = {"XYZ261112C00095000": {"bid": 1.95, "ask": 2.0},
              "XYZ261112C00105000": {"bid": 0.5, "ask": 0.6}}


class TestEmaVwapOptions(unittest.TestCase):
    def test_entry_call_debit_spread_fans_out(self):
        out = drive("ema_vwap_options", {"XYZ|1Day": XYZ_BARS},
                    params={"symbols": ["XYZ"]},
                    extra={"chains": OPT_CHAIN, "quotes": OPT_QUOTES})
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 2)
        self.assertTrue(all(i["qty"] == 1 for i in e))
        by = {i["symbol"]: i for i in e}
        self.assertEqual(by["XYZ261112C00095000"]["position_intent"], "buy_to_open")
        self.assertEqual(by["XYZ261112C00105000"]["position_intent"], "sell_to_open")
        self.assertIn("call_debit_spread", e[0]["reason"])

    def test_exit_dte_time_stop(self):
        pos = {"qty": 1, "entry_debit": 1.5,
               "spread": {"long_leg": {"occ": "XYZ261112C00095000"},
                          "short_leg": {"occ": "XYZ261112C00105000"},
                          "expiry": "2026-10-28", "width": 10.0, "debit": 1.5,
                          "max_profit": 8.5}}
        extra = {"quotes": OPT_QUOTES, "sleeve_state": {"XYZ": {"position": pos}}}
        fills = [{"symbol": "XYZ261112C00095000", "qty": 1, "side": "buy",
                  "price": 2.0, "ts": "2026-10-01T14:00:00Z", "intent_id": "seed"},
                 {"symbol": "XYZ261112C00105000", "qty": 1, "side": "sell",
                  "price": 0.5, "ts": "2026-10-01T14:00:00Z", "intent_id": "seed"}]
        out = drive("ema_vwap_options", {"XYZ|1Day": daily(END, [100.0] * 35)},
                    params={"symbols": ["XYZ"]}, extra=extra,
                    positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 2)
        self.assertIn("dte_time_stop_7", x[0]["reason"])

    def test_refusal_no_chain(self):
        out = drive("ema_vwap_options", {"XYZ|1Day": XYZ_BARS},
                    params={"symbols": ["XYZ"]}, extra={})
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])


EARN_CHAIN = {"XYZ": [{"symbol": "XYZ261127C00105000", "strike": 105.0,
                       "expiration": "2026-11-27"}]}
EARN_QUOTES = {"XYZ261127C00105000": {"bid": 0.38, "ask": 0.40}}


class TestEarningsBuyback(unittest.TestCase):
    def test_entry_long_call_fallback_control(self):
        extra = {"scan_signals": [{"symbol": "XYZ", "buyback_pct": 7.5,
                                   "filing_date": "2026-10-13"}],
                 "earnings": {"XYZ": "2026-11-02"}, "scan_age_days": 1.0,
                 "chains": EARN_CHAIN, "quotes": EARN_QUOTES,
                 "earnings_buyback_improve": {"expiry_gap_gate": False}}
        out = drive("earnings_buyback", {"XYZ|1Day": daily(END, [100.0] * 5)},
                    extra=extra)
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0]["qty"], 12)
        self.assertIn("long_call", e[0]["reason"])

    def test_exit_t_plus_15(self):
        pos = {"qty": 2, "kind": "long_call", "occ": "XYZ261127C00105000",
               "earnings_date": "2026-10-01", "debit": 0.40,
               "expiry": "2026-11-27"}
        extra = {"quotes": EARN_QUOTES, "sleeve_state": {"XYZ": {"position": pos}}}
        fills = [{"symbol": "XYZ261127C00105000", "qty": 2, "side": "buy",
                  "price": 0.40, "ts": "2026-09-20T14:00:00Z", "intent_id": "seed"}]
        out = drive("earnings_buyback",
                    {"XYZ|1Day": daily(date(2026, 10, 23), [100.0] * 20)},
                    extra=extra, positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual((x[0]["qty"], x[0]["symbol"]), (2, "XYZ261127C00105000"))
        self.assertIn("time_stop_t_plus_15", x[0]["reason"])

    def test_refusal_stale_scan(self):
        extra = {"scan_signals": [{"symbol": "XYZ", "buyback_pct": 7.5,
                                   "filing_date": "2026-10-13"}],
                 "earnings": {"XYZ": "2026-11-02"}, "scan_age_days": 99.0,
                 "chains": EARN_CHAIN, "quotes": EARN_QUOTES}
        out = drive("earnings_buyback", {"XYZ|1Day": daily(END, [100.0] * 5)},
                    extra=extra)
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])


FEAR_CHAIN = {"XYZ": [
    {"symbol": "XYZ261122P00080000", "strike": 80.0, "expiration": "2026-11-22"},
    {"symbol": "XYZ261122P00085000", "strike": 85.0, "expiration": "2026-11-22"},
    {"symbol": "XYZ261122P00090000", "strike": 90.0, "expiration": "2026-11-22"}]}
FEAR_QUOTES = {"XYZ261122P00085000": {"bid": 1.0, "ask": 1.05},
               "XYZ261122P00080000": {"bid": 0.48, "ask": 0.5},
               "XYZ261122P00090000": {"bid": 9.0, "ask": 9.1}}


class TestFearPremium(unittest.TestCase):
    def test_entry_put_credit_spread_on_red_day(self):
        bars = daily(END, [100.0] * 69 + [94.0])
        extra = {"universe": ["XYZ"], "chains": FEAR_CHAIN, "quotes": FEAR_QUOTES}
        out = drive("fear_premium",
                    {"XYZ|1Day": bars, "QQQ|1Day": daily(END, [500.0] * 70)},
                    extra=extra)
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 2)
        by = {i["symbol"]: i for i in e}
        self.assertEqual(by["XYZ261122P00085000"]["position_intent"], "sell_to_open")
        self.assertEqual(by["XYZ261122P00080000"]["position_intent"], "buy_to_open")
        self.assertIn("put_credit_spread", e[0]["reason"])

    def test_exit_profit_target(self):
        pos = {"qty": 1, "entry_credit": 2.0, "entry_date": "2026-10-20",
               "spread": {"short_occ": "XYZ261122P00085000",
                          "long_occ": "XYZ261122P00080000",
                          "expiry": "2026-12-30"}}
        quotes = {"XYZ261122P00085000": {"bid": 0.55, "ask": 0.6},
                  "XYZ261122P00080000": {"bid": 0.1, "ask": 0.15}}
        extra = {"universe": ["XYZ"], "quotes": quotes,
                 "sleeve_state": {"XYZ": {"position": pos}}}
        fills = [{"symbol": "XYZ261122P00085000", "qty": 1, "side": "sell",
                  "price": 1.0, "ts": "2026-10-20T14:00:00Z", "intent_id": "seed"},
                 {"symbol": "XYZ261122P00080000", "qty": 1, "side": "buy",
                  "price": 0.5, "ts": "2026-10-20T14:00:00Z", "intent_id": "seed"}]
        out = drive("fear_premium", {"XYZ|1Day": daily(END, [100.0] * 20)},
                    extra=extra, positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 2)
        self.assertIn("profit_target_50pct", x[0]["reason"])

    def test_refusal_no_red_day(self):
        extra = {"universe": ["XYZ"], "chains": FEAR_CHAIN, "quotes": FEAR_QUOTES}
        out = drive("fear_premium",
                    {"XYZ|1Day": daily(END, [100.0] * 70),
                     "QQQ|1Day": daily(END, [500.0] * 70)}, extra=extra)
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])


class TestFreeEtf(unittest.TestCase):
    def _hist(self):
        rows = [{"session": f"2025-{(i % 12) + 1:02d}-01", "close": 100.0 + i * 0.1}
                for i in range(252)]
        return {"SPY": rows}

    def _quote(self, ts):
        return {"SPY": {"t": ts, "received_at": ts, "bp": 499.9, "ap": 500.0}}

    def test_entry_fixed_weight_book_in_window(self):
        now = "2026-10-14T09:37:00-04:00"
        extra = {"etf_books": [{"id": "B1", "fixed_weights": {"SPY": 0.5}}],
                 "etf_receipt": {"histories": self._hist(),
                                 "source_receipts_verified": True, "feed": "sip",
                                 "adjustment": "all", "signal_session": "2026-10-13"},
                 "quotes": self._quote(now), "held_rows": {}}
        out = drive("free_etf", {}, now=now, extra=extra)
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["symbol"], e[0]["qty"]), ("SPY", 10))

    def test_exit_deselected_holding(self):
        now = "2026-10-14T10:00:00-04:00"
        extra = {"etf_books": [], "etf_receipt": {}, "quotes": self._quote(now),
                 "held_rows": {"FREE_ETF_B1_SPY": 5}}
        fills = [{"symbol": "SPY", "qty": 5, "side": "buy", "price": 500.0,
                  "ts": "2026-10-14T13:37:00Z", "intent_id": "seed"}]
        out = drive("free_etf", {}, now=now, extra=extra,
                    positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["qty"], 5)
        self.assertIn("deselected", x[0]["reason"])

    def test_refusal_outside_entry_window(self):
        now = "2026-10-14T10:00:00-04:00"
        extra = {"etf_books": [{"id": "B1", "fixed_weights": {"SPY": 0.5}}],
                 "etf_receipt": {"histories": self._hist(),
                                 "source_receipts_verified": True, "feed": "sip",
                                 "adjustment": "all", "signal_session": "2026-10-13"},
                 "quotes": self._quote(now), "held_rows": {}}
        out = drive("free_etf", {}, now=now, extra=extra)
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])


def _kraken_bars():
    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    out = []
    for i in range(24):
        t = start + timedelta(hours=4 * i)
        c = 1.5 if i == 23 else 2.0
        lo = 1.4 if i == 23 else 1.9
        out.append({"t": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "o": 2.0,
                    "h": 2.1, "l": lo, "c": c, "v": 100.0})
    return out


KRAKEN_NOW = "2026-10-23T04:00:00+00:00"
KRAKEN_QUOTE = {"quote": {"bid": 1.49, "ask": 1.51}}


class TestKrakenAda(unittest.TestCase):
    def test_breakdown_entry_short(self):
        out = drive("free_kraken_ada_breakdown",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra=dict(KRAKEN_QUOTE))
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["side"], e[0]["qty"]), ("sell", 1))

    def test_breakdown_exit_cover_due(self):
        extra = dict(KRAKEN_QUOTE)
        extra["sleeve_state"] = {"PF_ADAUSD": {
            "qty": -1, "entry_due_at": "2026-10-23T04:00:00+00:00"}}
        fills = [{"symbol": "PF_ADAUSD", "qty": 1, "side": "sell", "price": 1.49,
                  "ts": "2026-10-23T04:00:00Z", "intent_id": "seed"}]
        out = drive("free_kraken_ada_breakdown",
                    {"PF_ADAUSD|240Min": _kraken_bars()},
                    now="2026-10-23T21:00:00+00:00", extra=extra,
                    positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual((x[0]["side"], x[0]["qty"]), ("buy", 1))

    def test_crowded_entry_funding_gate_and_exit(self):
        rates = []
        now_dt = datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)
        base = now_dt - timedelta(days=80)
        for i in range(39):
            rates.append({"timestamp": (base + timedelta(days=2 * i)).isoformat(),
                          "fundingRate": 0.0001})
        rates.append({"timestamp": (now_dt - timedelta(hours=1)).isoformat(),
                      "fundingRate": 0.01})
        extra = dict(KRAKEN_QUOTE)
        extra["funding_rates"] = rates
        out = drive("free_kraken_ada_crowded",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra=extra)
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["side"], e[0]["qty"]), ("sell", 1))
        extra2 = dict(KRAKEN_QUOTE)
        extra2["sleeve_state"] = {"PF_ADAUSD": {
            "qty": -1, "entry_due_at": "2026-10-23T04:00:00+00:00"}}
        fills = [{"symbol": "PF_ADAUSD", "qty": 1, "side": "sell", "price": 1.49,
                  "ts": "2026-10-23T04:00:00Z", "intent_id": "seed"}]
        out = drive("free_kraken_ada_crowded",
                    {"PF_ADAUSD|240Min": _kraken_bars()},
                    now="2026-10-23T21:00:00+00:00", extra=extra2,
                    positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["side"], "buy")

    def test_crowded_refusal_no_funding_spike(self):
        out = drive("free_kraken_ada_crowded",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra=dict(KRAKEN_QUOTE))
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])


class TestKrakenAdaBasisDesigned(unittest.TestCase):
    """Authored basis logic (v2 test_designed_basis.py oracle, ADA row)."""
    T0 = datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc).timestamp()

    def _series(self, bps_list, spot=0.20):
        return [{"t": self.T0 + i * 14400, "spot_close": spot,
                 "perp_close": spot * (1 + bps / 10000.0)}
                for i, bps in enumerate(bps_list)]

    def _extra(self, bps_list, quote, aligned=3, required=3, spot=0.20):
        return {"basis": {"aligned": aligned, "required": required,
                          "decision": {"status": "READY" if aligned == required
                                       else "BLOCKED_INPUT", "reason": "fixture"},
                          "series": self._series(bps_list, spot)},
                "quote": quote}

    def test_entry_fires_at_40bps_and_refusals(self):
        now = datetime.fromtimestamp(self.T0 + 12 * 3600, tz=timezone.utc).isoformat()
        spot = 0.20
        bid = spot * 1.004
        out = drive("free_kraken_ada_basis", {}, now=now,
                    extra=self._extra([0, 0, 40], {"bid": bid, "ask": bid + spot * 0.001}))
        e = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["symbol"], e[0]["side"]), ("PF_ADAUSD", "sell"))
        # 10bps below threshold / crossed quote / unready basis all refuse
        bid10 = spot * 1.001
        self.assertEqual(drive("free_kraken_ada_basis", {}, now=now,
                               extra=self._extra([0, 0, 10], {"bid": bid10, "ask": bid10 * 1.001})), [])
        self.assertEqual(drive("free_kraken_ada_basis", {}, now=now,
                               extra=self._extra([0, 0, 40], {"bid": bid * 1.01, "ask": bid})), [])
        self.assertEqual(drive("free_kraken_ada_basis", {}, now=now,
                               extra=self._extra([0, 0, 40], {"bid": bid, "ask": bid * 1.001},
                                                 aligned=2, required=3)), [])
        self.assertEqual(drive("free_kraken_ada_basis", {}, now=now, extra={}), [])

    def test_exit_on_normalization_and_hold(self):
        now = datetime.fromtimestamp(self.T0 + 12 * 3600, tz=timezone.utc).isoformat()
        spot = 0.20
        entry_iso = datetime.fromtimestamp(self.T0 + 8 * 3600, tz=timezone.utc).isoformat()
        ask = spot * 1.0003
        extra = self._extra([40, 40, 3], {"bid": ask * 0.999, "ask": ask})
        extra["sleeve_state"] = {"PF_ADAUSD": {"qty": -1, "entry_due_at": entry_iso}}
        fills = [{"symbol": "PF_ADAUSD", "qty": 1, "side": "sell", "price": ask,
                  "ts": entry_iso, "intent_id": "seed"}]
        out = drive("free_kraken_ada_basis", {}, now=now, extra=extra,
                    positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["side"], "buy")


def _5m(day, hh, mm, n, px):
    t = datetime.combine(day, time(hh, mm), tzinfo=ET)
    out = []
    for _ in range(n):
        out.append({"t": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "o": px, "h": px, "l": px, "c": px, "v": 10000.0})
        t += timedelta(minutes=5)
    return out


class TestEm1587(unittest.TestCase):
    def test_full_frame_no_signal(self):
        bars = {"SPY|5Min": _5m(date(2026, 10, 20), 9, 30, 78, 700.0)
                + _5m(date(2026, 10, 21), 9, 30, 7, 700.0),
                "QQQ|5Min": _5m(date(2026, 10, 20), 9, 30, 78, 600.0)
                + _5m(date(2026, 10, 21), 9, 30, 7, 600.0)}
        out = drive("em_1587", bars, now="2026-10-21T10:05:00-04:00",
                    extra={"vix_series": [{"date": "2026-10-20", "close": 14.0}]})
        self.assertEqual(out, [])

    def test_exit_overnight_flat(self):
        pos = {"occ": "SPY261020C00700000", "qty": 1, "entry_px": 2.0,
               "signal_date": "2026-10-20"}
        extra = {"sleeve_state": {"SPY": {"position": pos}}}
        fills = [{"symbol": "SPY261020C00700000", "qty": 1, "side": "buy",
                  "price": 2.0, "ts": "2026-10-20T15:00:00-04:00",
                  "intent_id": "seed"}]
        out = drive("em_1587", {}, now="2026-10-21T11:29:00-04:00",
                    extra=extra, positions=positions_from_fills(fills))
        x = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(x), 1)
        self.assertEqual((x[0]["symbol"], x[0]["qty"]),
                         ("SPY261020C00700000", 1))
        self.assertIn("overnight_flat", x[0]["reason"])


if __name__ == "__main__":
    unittest.main()
