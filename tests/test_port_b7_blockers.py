"""Blockers PORT-B7: batch-7 port fidelity. (1) Every copied sleeve /
adapter / shared-core file is byte-identical to v2 (sha256) — fails on
the pre-port tree (files absent) and on any drift. (2) Fixture drives
through the v3 evaluate(view, ctx) interface prove entry, each designed
exit, and refusals, mirroring v2 tests/test_batch7_fixture.py oracles."""
import hashlib, importlib, json, os, sys, tempfile, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = "/home/hatch/workspace/muse-desk-v2"
sys.path.insert(0, ROOT)
IDS = ["saty_gpt_v02", "saty_gpt_v03", "saty_magnum", "saty_sol",
       "saty_sol_0dte", "snapback", "spx_premium", "tensor_red_dip",
       "tensor_swing", "ts_momentum_decile"]
NOW = "2026-10-23T15:30:00-04:00"
SESSION = date(2026, 10, 23)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _b(t, c, v=10000.0, o=None, h=None, l=None):
    return {"t": t, "o": o if o is not None else c,
            "h": h if h is not None else c * 1.001,
            "l": l if l is not None else c * 0.999, "c": c, "v": v}


def _daily(n, start=100.0, drift=0.001, vol=20000.0):
    days, d = [], date(2026, 10, 22)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    return [_b(f"{x.isoformat()}T04:00:00Z", start * (1 + drift) ** i, v=vol)
            for i, x in enumerate(days)]


def _rth_5min(days=20, base=500.0):
    out, d, made, seq = [], SESSION, 0, []
    while made < days:
        if d.weekday() < 5:
            seq.append(d); made += 1
        d -= timedelta(days=1)
    for di, day in enumerate(sorted(seq)):
        px = base + di * 0.7
        for k in range(78):
            mins = 13 * 60 + 30 + k * 5
            px += 0.02
            out.append(_b(f"{day.isoformat()}T{mins // 60:02d}:{mins % 60:02d}:00Z",
                          round(px, 2), v=50000.0))
    return out


def _today_1min(base=514.0):
    out, px = [], base
    for k in range(0, 360, 5):
        mins = 13 * 60 + 30 + k
        px += 0.01
        out.append(_b(f"2026-10-23T{mins // 60:02d}:{mins % 60:02d}:00Z",
                      round(px, 2), v=8000.0))
    return out


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
    # WEIGHT-LAG-ACTIVE-20261031: ts_momentum_decile holds one
    # evaluation's intents and emits them at the next, with the
    # pending state in the cycle state_dir — so drive two evaluations
    # on ONE state dir: the first computes weights and emits nothing,
    # the second acts on them. Returns (first, second).
    view = _flat(dict(view)); view.setdefault("now", NOW)
    view.setdefault("slice", {"capital_usd": 10000.0, "cash_usd": 10000.0})
    mod = importlib.import_module(f"adapters3.{sid}")
    ctx = {"sleeve_id": sid, "state_dir": tempfile.mkdtemp()}
    return mod.evaluate(view, ctx), mod.evaluate(view, ctx)


# SILENT-SKIP-SIZING-20261116 named deviation (2026-11-16):
# sleeves/tensor_red_dip.py carries one authorized v3-side cure
# (a sized-zero skip now also appends the named sizing_zero_or_cap
# record to the evaluation stamp; sizing math verbatim, adapter
# untouched). Its port bytes are therefore pinned to the cured
# sha256 below instead of the v2 bytes; every other file in this
# class keeps full v2 byte-identity.
TENSOR_RED_DIP_CURED_SHA256 = \
    "b127517f152c66ea558e53d7a630329bd3315cbd5c91adfd575a847b2ccd6700"


class TestByteFidelity(unittest.TestCase):
    def test_sleeves_and_adapters_byte_identical(self):
        for sid in IDS:
            for sub in ("sleeves", "adapters"):
                if (sub, sid) == ("sleeves", "tensor_red_dip"):
                    self.assertEqual(
                        _sha(os.path.join(ROOT, sub, sid + ".py")),
                        TENSOR_RED_DIP_CURED_SHA256, f"{sub}/{sid} cured pin")
                    continue
                self.assertEqual(_sha(os.path.join(ROOT, sub, sid + ".py")),
                                 _sha(os.path.join(V2, sub, sid + ".py")), f"{sub}/{sid}")

    def test_shared_core_byte_identical(self):
        files = ["core/sleeve.py", "core/data.py", "core/early_close.py",
                 "core/saty_bars.py", "core/saty_indicators.py",
                 "core/saty_primitives.py", "core/saty_reference.py",
                 "adapters/_bridge.py", "adapters/_old_bridge.py",
                 "adapters/_common.py", "runtime/models.py"]
        dirs = ["core/saty_gpt_v02", "core/saty_gpt_v03"]
        for dd in dirs:
            for f in sorted(os.listdir(os.path.join(V2, dd))):
                if f.endswith(".py"):
                    files.append(f"{dd}/{f}")
        # WS4-FRACTIONAL-20261114: adapters/_bridge.py was cured
        # in v3 under the owner's any-price ruling (its
        # translate_batch5 fractional skip removed, mirroring
        # desk3/port4_bridge.py); it is pinned to its cured bytes
        # below instead of the v2 source. Any further drift fails.
        diverged = {"adapters/_bridge.py": "e824e897de4085e79b810772107a27308d14526eea635b3a5c121e464eebd98b"}
        for f in files:
            if f in diverged:
                self.assertEqual(_sha(os.path.join(ROOT, f)),
                                 diverged[f], f)
                continue
            self.assertEqual(_sha(os.path.join(ROOT, f)),
                             _sha(os.path.join(V2, f)), f)

    def test_config_rows_registered(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = {r["id"]: r for r in cfg["sleeves"]}
        v2 = {r["id"]: r for r in json.load(open(os.path.join(V2, "config", "sleeves.json")))["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, rows)
            self.assertEqual(rows[sid]["cadence_s"], v2[sid]["cadence_s"])
            self.assertEqual(rows[sid]["slice"], v2[sid]["slice"])
            self.assertTrue(rows[sid]["inputs"])


class TestFixtureDrives(unittest.TestCase):
    def test_tensor_swing_entry_and_exit(self):
        sig = [{"symbol": "AAPL", "confidence": 9, "entry": 150.0, "stop": 140.0,
                "target": 170.0, "phenotype": "P", "regime": "R", "bar_date": "2026-10-22"}]
        out = ev("tensor_swing", {"extra": {"tensor_signals": sig}})
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["stop_price"], 140.0)
        view = {"AAPL": {"bearish_exit": True, "bearish_reason": "fixture", "last_close": 149.0}}
        out2 = ev("tensor_swing", {
            "positions": [{"symbol": "AAPL", "qty": 3, "avg_price": 150.0,
                           "opened_at": "2026-10-20T14:00:00Z", "intent_id": "x"}],
            "extra": {"tensor_exit": view}})
        self.assertEqual(len(out2), 1); self.assertEqual(out2[0]["kind"], "exit")
        self.assertEqual(out2[0]["qty"], 3)

    def test_tensor_red_dip_entry_and_strength_exit(self):
        extra = {"tensor_signals": [{"symbol": "AAPL", "confidence": 9, "phenotype": "P"}],
                 "qqq_day_return": -0.02, "day_returns": {"AAPL": -0.02}}
        out = ev("tensor_red_dip", {"bars": {"AAPL": {"1Day": _daily(5, 100.0, 0.0)}},
                                    "extra": extra})
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 3)
        out2 = ev("tensor_red_dip", {
            "bars": {"AAPL": {"1Day": _daily(10, 104.0, 0.0)},
                     "QQQ": {"1Day": _daily(10, 400.0, 0.0)},
                     "SPY": {"1Day": _daily(10, 500.0, 0.0)}},
            "positions": [{"symbol": "AAPL", "qty": 10, "avg_price": 100.0,
                           "opened_at": "2026-10-20T14:00:00Z", "intent_id": "s"}]})
        exits = [i for i in out2 if i["kind"] == "exit" and i["symbol"] == "AAPL"]
        self.assertTrue(exits and exits[0]["qty"] == 10)

    def test_snapback_91d_exit(self):
        bars = {}
        for s in ("SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMD", "TSLA",
                  "AMZN", "META", "NFLX", "GOOGL"):
            bars[s] = {"1Day": _daily(120, 50.0, 0.0), "1Week": _daily(60, 50.0, 0.0)}
        out = ev("snapback", {"bars": bars, "positions": [
            {"symbol": "MSFT", "qty": 5, "avg_price": 50.0,
             "opened_at": "2026-06-20T14:00:00Z", "intent_id": "seed"}]})
        exits = [i for i in out if i["kind"] == "exit" and i["symbol"] == "MSFT"]
        self.assertTrue(exits and exits[0]["qty"] == 5)

    def test_spx_premium_gate_refusal_and_settlement_exit(self):
        out = ev("spx_premium", {"bars": {"SPY": {"1Week": _daily(30, 500.0),
                                                  "1Day": _daily(30, 500.0)}}})
        self.assertEqual(out, [])  # $10k slice < $37k equity gate: refusal
        pos = [{"symbol": "XSP", "qty": 1, "avg_price": 1.0,
                "opened_at": "2026-10-19T14:00:00Z", "intent_id": "x",
                "expiry": "2026-10-23", "short_occ": "XSP261023P00500000",
                "long_occ": "XSP261023P00495000", "credit": 1.50}]
        out2 = ev("spx_premium", {"positions": pos})
        self.assertEqual(len(out2), 1); self.assertEqual(out2[0]["kind"], "exit")

    def test_ts_momentum_entries_and_rebalance_exit(self):
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
            bars[s] = {"1Day": _daily(260, 100.0, drift=drift)}
        flat = list(SECTOR_MAP)[20]
        bars[flat] = {"1Day": _daily(260, 100.0, drift=-0.001)}
        first, out = ev2("ts_momentum_decile", {"bars": bars, "positions": [
            {"symbol": flat, "qty": 7, "avg_price": 90.0,
             "opened_at": "2026-09-01T14:00:00Z", "intent_id": "seed"}]})
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        entries = [i for i in out if i["kind"] == "entry"]
        exits = [i for i in out if i["kind"] == "exit" and i["symbol"] == flat]
        self.assertTrue(entries); self.assertTrue(exits and exits[0]["qty"] == 7)

    def test_saty_family_evaluates_and_refuses_empty(self):
        bars = {"SPY": {"5Min": _rth_5min(20), "1Min": _today_1min(),
                        "1Day": _daily(60, 480.0)}}
        for sid in ("saty_gpt_v02", "saty_gpt_v03", "saty_magnum", "saty_sol", "saty_sol_0dte"):
            out = ev(sid, {"bars": bars})
            self.assertIsInstance(out, list, sid)
            for i in out:
                self.assertGreater(i["qty"], 0); self.assertIn(i["kind"], ("entry", "exit"))
            self.assertEqual(ev(sid, {}), [], sid)  # no data: fail closed


if __name__ == "__main__":
    unittest.main()
