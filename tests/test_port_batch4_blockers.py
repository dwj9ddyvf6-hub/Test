"""Batch-4 port blockers (PORT-4): sleeves fwd_alpaca_ada_rsi2,
fwd_alpaca_enj_iu_body, fwd_alpaca_link_ai_volume, fwd_coinbase_sma200,
gate_1h, iron_condor, leader_d, leader_sc, leaps_momentum, legends_ema.

Proof standard: for every fixture scenario (entry / each designed exit /
refusal), the v3 sleeve's intents must equal the v2 adapter's intents on
the SAME fixture inputs — the v2 adapter itself, run in a subprocess
(tests/port4_oracle.py), is the oracle. Scenarios are v2's own fixture
scenarios (tests/test_batch3_fixture.py + test_batch4_fixture.py).
Vendored strategy files are sha256-pinned to the v2 sources.

IU-BODY-ORDER-LOGIC-20261116 amendment (dated estate form, same
day): the roster-module pin below is superseded for exactly one
sleeve. fwd_alpaca_enj_iu_body's vendored strategy returns [] by
source design (it preserves a source with no order logic), so the
total audit's cure built the faithful IU-body order logic
desk-side (desk3/iu_body.py, proven against the archive reducer
itself in desk3/iu_body_fidelity_result.json) and repointed the
roster row at adapters3.fwd_alpaca_enj_iu_body. The vendored file
and the desk3.sleeves port adapter stay byte-identical, and this
file's sha pins and oracle scenarios — which exercise
desk3.sleeves.fwd_alpaca_enj_iu_body directly — stand verbatim.
The other nine sleeves' module pins are unchanged.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _find_v2():
    """The v2 oracle tree is a property of this box, not of this
    repo's location: the old form (sibling of ROOT) silently broke
    in any relocated checkout (the 2026-11-08 clean-export gate ran
    from ~/.cache and found ~/.cache/muse-desk-v2, which does not
    exist: 24 errors). Resolution order: explicit env override,
    sibling of this repo, the canonical workspace location. The
    sibling is the fallback so a genuine absence still names the
    expected place in the failure."""
    cands = [os.environ.get("MUSE_DESK_V2_DIR"),
             os.path.join(os.path.dirname(ROOT), "muse-desk-v2"),
             os.path.expanduser("~/workspace/muse-desk-v2")]
    for cand in cands:
        if cand and os.path.isdir(cand):
            return cand
    return cands[1]


V2 = _find_v2()
ORACLE = os.path.join(ROOT, "tests", "port4_oracle.py")
UTC = timezone.utc
END = date(2026, 10, 20)

SLEEVES = ["fwd_alpaca_ada_rsi2", "fwd_alpaca_enj_iu_body",
           "fwd_alpaca_link_ai_volume", "fwd_coinbase_sma200", "gate_1h",
           "iron_condor", "leader_d", "leader_sc", "leaps_momentum",
           "legends_ema"]

STRATEGY_SHA256 = {
    "fwd_alpaca_ada_rsi2": "442c45e987ce7b5929819bbad85187ef4d4e2f5fb0a443cdc4f537f14055203f",
    "fwd_alpaca_enj_iu_body": "171f5f79f1ae9a3d799a7408bc1f786c4309a16ed39e41627bf3d133d9ad9b6a",
    "fwd_alpaca_link_ai_volume": "e945d57aad2e2f0c53e61183ad3e03ffa5022f08837b6d7801b5ae5ef4e268f4",
    "fwd_coinbase_sma200": "7952c82cfce681424625dde4c05606e99c8feca59216ce1a095dd34479b892b9",
    "gate_1h": "7654d892fc4c9e11e88c2add53dad8b75c1457ca35ea48d78254ac0c99a8a5d6",
    "iron_condor": "566bc90eef756a6f67532bfe6ad298f7c4e25b056c8359b5145c8c16bb0d48df",
    "leader_d": "8f6fb8780727ebf870f3b91dfb01caa9bcf1cf7d4585f2a209477797382e0416",
    "leader_sc": "0287eba4aa070cdc3ae6caf499413789e891a6d56fa92d48fe9cb890f8eb3124",
    "leaps_momentum": "2c56d64bca83b7e7ba88992adb0dcab75789aebedd84e45041000013b400a216",
    "legends_ema": "d81965376f86aa09253741e205c877d33645569f5874a2abd047c6bff398a7a9",
}
CORE_SHA256 = "951d23c323b9ff8f74f8dd3ba01f7ed07aff8bf9b4f1a59c4e51188514b0d1cf"
JOURNAL_SHA256 = "7cff3e86e7c1eea4c45cce7dc6cd687bb39ef8f60ea74b8fa27b1af495bdeaee"


# ---------------------------------------------------------------- fixtures
def weekdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return list(reversed(out))


def daily(end, n, start_c, end_c, vol=200000.0):
    bars = []
    for i, d in enumerate(weekdays(end, n)):
        c = start_c + (end_c - start_c) * (i / max(1, n - 1))
        bars.append({"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c + 1,
                     "l": c - 1, "c": c, "v": vol})
    return bars


def cal_daily(end, n, start_c, end_c):
    bars = []
    for i in range(n):
        d = end - timedelta(days=n - 1 - i)
        c = start_c + (end_c - start_c) * (i / max(1, n - 1))
        bars.append({"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c + 1,
                     "l": c - 1, "c": c, "v": 1000})
    return bars


def ada_bars():
    bars = []
    end_open = datetime(2026, 10, 23, 12, 59, tzinfo=UTC)
    for i in range(210):
        t = end_open - timedelta(hours=209 - i)
        bars.append({"t": t.isoformat().replace("+00:00", "Z"), "o": 0.5,
                     "h": 0.5, "l": 0.5, "c": 0.5, "v": 100.0})
    return bars


def link_4h():
    now_z = datetime(2026, 10, 23, 14, 2, tzinfo=UTC)
    last_open = now_z - timedelta(hours=4)
    bars = []
    for i in range(65):
        t = last_open - timedelta(hours=4 * (64 - i))
        bars.append({"t": t.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                     "o": 15.0, "h": 15.2, "l": 14.8, "c": 15.0, "v": 1000})
    return bars


def gate_h1():
    bars = []
    d = datetime(2026, 10, 20, 13, tzinfo=UTC)
    for i in range(28):
        t = d + timedelta(hours=i + (17 * (i // 7)))
        bars.append({"t": t.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                     "o": 50.0, "h": 51.0, "l": 49.0, "c": 50.5, "v": 5000})
    return bars


def legends_bars():
    sessions = [date(2026, 10, d) for d in (15, 16, 19, 20, 21, 22)]
    m15 = []
    for si, sd in enumerate(sessions):
        setup = si == len(sessions) - 1
        t0 = datetime(sd.year, sd.month, sd.day, 13, 30, tzinfo=UTC)
        for i in range(26):
            t = t0 + timedelta(minutes=15 * i)
            if setup:
                o = 100 + i * 0.8; c = o + 0.8; h = c + 0.3; l = o + 0.1
            else:
                o = h = l = c = 100.0
            m15.append({"t": t.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "o": o, "h": h, "l": l, "c": c, "v": 1000})
    daily_bars = []
    for i, d in enumerate(weekdays(date(2026, 10, 22), 14)):
        c = 120.8 if i == 13 else 100.0
        daily_bars.append({"t": f"{d.isoformat()}T04:00:00Z", "o": c,
                           "h": c + 2, "l": c - 2, "c": c, "v": 10000})
    return m15, daily_bars


def condor_extra():
    sess = date(2026, 10, 23)
    exp = (sess + timedelta(days=37)).isoformat()

    def occ(kind, strike):
        return f"NBIS{exp[2:4]}{exp[5:7]}{exp[8:10]}{kind}{int(strike * 1000):08d}"

    chain, quotes = {"put": [], "call": []}, {}
    for strike in range(70, 146):
        for kind, key in (("P", "put"), ("C", "call")):
            o = occ(kind, strike)
            chain[key].append({"symbol": o, "strike": float(strike),
                               "expiration": exp})
            bid = max(0.1, (strike - 60) * 0.05) if key == "put" else \
                max(0.1, (160 - strike) * 0.05)
            quotes[o] = {"bid": round(bid, 2), "ask": round(bid * 1.02, 2)}
    return {"chains": {"NBIS": chain}, "quotes": quotes,
            "iv": {"NBIS": 0.65},
            "iv_history": {"NBIS": [0.3 + 0.004 * i for i in range(100)]},
            "earnings_in_days": {"NBIS": 60}, "vix": 20.0}


def leaps_chain_extra():
    sess = date(2026, 10, 21)
    exp = (sess + timedelta(days=400)).isoformat()
    occ = f"AAPL{exp[2:4]}{exp[5:7]}{exp[8:10]}C00080000"
    return occ, exp


def pos(sym, qty, px, opened):
    return {"symbol": sym, "qty": qty, "avg_price": px,
            "opened_at": opened, "intent_id": "seed"}


ADA_QUOTE = {"bid": 0.499, "ask": 0.5, "exchange_at": "2026-10-23T14:00:00+00:00"}
LINK_QUOTE = {"bid": 14.9, "ask": 15.0, "exchange_at": "2026-10-23T14:02:00+00:00"}
_M15, _DB = legends_bars()
_OCC, _EXP = leaps_chain_extra()
_SC_SYMS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO",
            "JPM", "XOM", "UNH"]
_SC_BARS = {}
for _s in _SC_SYMS:
    _SC_BARS[f"{_s}|1Day"] = daily(END, 260, 40, 50,
                                   vol=1000.0 if _s == "AAPL" else 200000.0)

SCENARIOS = [
    # name, sleeve, now, bars, extra, positions, cash
    ("ada_entry", "fwd_alpaca_ada_rsi2", "2026-10-23T10:00:00-04:00",
     {"ADA/USD|1Hour": ada_bars()},
     {"features": {"long_signal": True}, "quote": ADA_QUOTE}, [], 10000.0),
    ("ada_fence_no_features", "fwd_alpaca_ada_rsi2", "2026-10-23T10:00:00-04:00",
     {"ADA/USD|1Hour": ada_bars()}, {"quote": ADA_QUOTE}, [], 10000.0),
    ("ada_exit_close_signal", "fwd_alpaca_ada_rsi2", "2026-10-23T10:00:00-04:00",
     {"ADA/USD|1Hour": ada_bars()},
     {"features": {"long_close_signal": True}, "quote": ADA_QUOTE},
     [pos("ADA/USD", 20000, 0.5, "2026-10-23T12:00:00+00:00")], 10000.0),
    ("enj_blocked_monitor", "fwd_alpaca_enj_iu_body", "2026-10-23T10:00:00-04:00",
     {"ENJ/USD|1Min": [{"t": "2026-10-23T13:59:00Z", "o": 0.1, "h": 0.11,
                        "l": 0.09, "c": 0.1, "v": 100}]}, {}, [], 10000.0),
    ("link_fence_no_features", "fwd_alpaca_link_ai_volume",
     "2026-10-23T10:02:00-04:00", {"LINK/USD|4Hour": link_4h()}, {}, [], 10000.0),
    ("link_exit", "fwd_alpaca_link_ai_volume", "2026-10-23T10:02:00-04:00",
     {"LINK/USD|4Hour": link_4h()}, {"quote": LINK_QUOTE},
     [pos("LINK/USD", 10, 15.0, "2026-10-22T10:00:00Z")], 10000.0),
    ("link_entry_fractional", "fwd_alpaca_link_ai_volume",
     "2026-10-23T10:02:00-04:00", {"LINK/USD|4Hour": link_4h()},
     {"features": {"long_signal": True}, "quote": LINK_QUOTE}, [], 10000.0),
    ("coinbase_outside_window", "fwd_coinbase_sma200", "2026-10-23T10:00:00-04:00",
     {"BTC-USD|1Day": cal_daily(END, 210, 50000, 60000)}, {}, [], 10000.0),
    ("coinbase_entry", "fwd_coinbase_sma200", "2026-10-21T00:02:00+00:00",
     {"BTC-USD|1Day": cal_daily(END, 210, 50000, 60000)}, {}, [], 10000.0),
    ("gate_entry", "gate_1h", "2026-10-23T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 260, 40, 50), "AAPL|1Hour": gate_h1()},
     {"leader_events": {"AAPL": "2026-10-19"},
      "gate_1h_enhance": {"enabled": False}}, [], 10000.0),
    ("gate_exit", "gate_1h", "2026-10-23T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 260, 40, 50), "AAPL|1Hour": gate_h1()}, {},
     [pos("AAPL", 3, 50.0, "2026-10-20T13:00:00+00:00")], 10000.0),
    ("condor_max_hold_exit", "iron_condor", "2026-10-23T10:00:00-04:00",
     {"NBIS|1Day": daily(END, 40, 90, 100)}, {},
     [pos("NBIS", 2, 3.0, "2026-09-14T04:00:00Z")], 10000.0),
    ("condor_entry_4leg", "iron_condor", "2026-10-23T10:00:00-04:00",
     {"NBIS|1Day": daily(END, 40, 90, 100)}, condor_extra(), [], 1000000.0),
    ("leader_d_entry", "leader_d", "2026-10-21T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 260, 40, 50)},
     {"leader_events": {"AAPL": "2026-10-20"}, "spy_down_regime": True},
     [], 10000.0),
    ("leader_d_exit", "leader_d", "2026-10-21T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 260, 40, 50)}, {},
     [pos("AAPL", 4, 45.0, "2026-09-15T04:00:00Z")], 10000.0),
    ("leader_sc_entry", "leader_sc", "2026-10-21T10:00:00-04:00", _SC_BARS,
     {"leader_events": {"AAPL": "2026-10-20"}, "spy_down_regime": True},
     [], 10000.0),
    ("leader_sc_exit", "leader_sc", "2026-10-21T10:00:00-04:00", _SC_BARS, {},
     [pos("AAPL", 4, 45.0, "2026-09-15T04:00:00Z")], 10000.0),
    ("leaps_no_book_refusal", "leaps_momentum", "2026-10-21T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 40, 90, 100)}, {}, [], 10000.0),
    ("leaps_entry", "leaps_momentum", "2026-10-21T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 40, 90, 100)},
     {"momentum_book": {"AAPL": {"qty": 500}}, "momentum_book_age_days": 1.0,
      "chains": {"AAPL": [{"symbol": _OCC, "strike": 80.0, "expiration": _EXP}]},
      "quotes": {_OCC: {"bid": 25.0, "ask": 25.5}}}, [], 100000.0),
    ("leaps_exit_stop30", "leaps_momentum", "2026-10-21T10:00:00-04:00",
     {"AAPL|1Day": daily(END, 40, 90, 100)},
     {"momentum_book": {"AAPL": {"qty": 500}}, "momentum_book_age_days": 1.0,
      "quotes": {_OCC: {"bid": 19.0, "ask": 21.0}},
      "sleeve_state": {"AAPL": {"position": {
          "qty": 2, "occ": _OCC, "expiry": _EXP,
          "entry_premium": 30.0, "strike": 80.0}}}}, [], 100000.0),
    ("legends_entry", "legends_ema", "2026-10-23T09:35:00-04:00",
     {"QQQ|15Min": _M15, "QQQ|1Day": _DB}, {}, [], 10000.0),
    ("legends_flat_exit", "legends_ema", "2026-10-23T16:00:00-04:00",
     {"QQQ|1Day": _DB}, {},
     [pos("QQQ", 5, 100.0, "2026-10-23T14:00:00Z")], 10000.0),
]


def oracle_intents(sc):
    payload = {"sleeve_id": sc[1], "now": sc[2], "bars": sc[3],
               "extra": sc[4], "positions": sc[5], "cash": sc[6]}
    env = dict(os.environ, MUSE_DESK_V2_DIR=V2)
    r = subprocess.run([sys.executable, ORACLE], input=json.dumps(payload),
                       capture_output=True, text=True, cwd=V2, timeout=120,
                       env=env)
    if r.returncode != 0:
        raise AssertionError(f"oracle failed for {sc[0]}: {r.stderr[-2000:]}")
    return json.loads(r.stdout)


def v3_intents(sc):
    from desk3.sleeves import __name__ as _pkg  # noqa: F401
    import importlib
    mod = importlib.import_module(f"desk3.sleeves.{sc[1]}")
    bars = {}
    for key, rows in sc[3].items():
        sym, tf = key.rsplit("|", 1)
        bars.setdefault(sym, {})[tf] = rows
    view = {"now_iso": sc[2], "bars": bars,
            "positions": {sc[1]: sc[5]},
            "slice": {sc[1]: {"capital_usd": sc[6], "cash_usd": sc[6]}},
            "params": {sc[1]: {"extra": sc[4]}}}
    outs = []
    for _ in range(2):  # determinism: two fresh state dirs, same output
        with tempfile.TemporaryDirectory() as td:
            ctx = {"sleeve_id": sc[1], "state_dir": td,
                   "cycle_id": "test", "snapshot_hash": "test"}
            outs.append(mod.evaluate(view, ctx))
    if json.dumps(outs[0], sort_keys=True) != json.dumps(outs[1], sort_keys=True):
        raise AssertionError(f"v3 nondeterministic for {sc[0]}")
    return outs[0]


class TestPortBatch4Equivalence(unittest.TestCase):
    # WS4-FRACTIONAL-20261114: legends_ema's risk sizing now
    # expresses fractionally; the v2 oracle's whole-share qty for
    # this scenario is superseded by the recorded value below.
    # Every other field of every scenario still matches the oracle
    # byte-for-byte.
    WS4_ORACLE_QTY = {"legends_entry": 12.5}

    def test_scenarios_match_v2_oracle(self):
        for sc in SCENARIOS:
            with self.subTest(scenario=sc[0]):
                got, want = v3_intents(sc), oracle_intents(sc)
                if sc[0] in self.WS4_ORACLE_QTY:
                    self.assertEqual(len(got), len(want))
                    for g, w in zip(got, want):
                        self.assertEqual(g.pop("qty"),
                                         self.WS4_ORACLE_QTY[sc[0]])
                        w.pop("qty", None)
                self.assertEqual(got, want)

    def test_scenario_outcomes_are_designed(self):
        """Guard against vacuous equality (both sides empty everywhere):
        entries fire, exits fire, refusals refuse — per v2's own asserts."""
        by = {sc[0]: v3_intents(sc) for sc in SCENARIOS}
        self.assertEqual(by["ada_fence_no_features"], [])
        self.assertEqual(by["enj_blocked_monitor"], [])
        self.assertEqual(by["link_fence_no_features"], [])
        self.assertEqual(by["coinbase_outside_window"], [])
        self.assertEqual(by["leaps_no_book_refusal"], [])
        e = by["ada_entry"]
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["kind"], e[0]["limit_price"], e[0]["qty"]),
                         ("entry", 0.5, 20000))
        self.assertEqual(by["ada_exit_close_signal"][0]["kind"], "exit")
        x = by["link_exit"]
        self.assertEqual((x[0]["qty"], x[0]["limit_price"]), (10, 14.9))
        self.assertAlmostEqual(by["link_entry_fractional"][0]["qty"],
                               10000.0 / 15.0, places=6)
        self.assertEqual(by["coinbase_entry"][0]["qty"], 0.01)
        g = by["gate_entry"]
        self.assertEqual((g[0]["qty"], g[0]["stop_price"]), (2, 37.5))
        self.assertEqual(by["gate_exit"][0]["qty"], 3)
        self.assertEqual(len(by["condor_max_hold_exit"]), 1)
        legs = by["condor_entry_4leg"]
        self.assertEqual(len(legs), 4)
        self.assertEqual(sorted(i["position_intent"] for i in legs),
                         ["buy_to_open", "buy_to_open",
                          "sell_to_open", "sell_to_open"])
        self.assertEqual((by["leader_d_entry"][0]["qty"],
                          by["leader_d_entry"][0]["stop_price"]), (2, 37.5))
        self.assertEqual(by["leader_d_exit"][0]["qty"], 4)
        self.assertEqual(by["leader_sc_entry"][0]["symbol"], "AAPL")
        self.assertEqual(len(by["leader_sc_exit"]), 1)
        self.assertEqual(by["leaps_entry"][0]["qty"], 1)
        self.assertIn("stop_minus30pct", by["leaps_exit_stop30"][0]["reason"])
        lg = by["legends_entry"]
        # WS4: the exit carries the actual held 12.5 (pre-cure
        # the exit int-truncated the fractional position to 12)
        self.assertEqual((lg[0]["side"], lg[0]["qty"]), ("sell", 12.5))
        self.assertEqual(by["legends_flat_exit"][0]["qty"], 5)


class TestPortBatch4Fidelity(unittest.TestCase):
    # WS4-FRACTIONAL-20261114: gate_1h, leader_d, leader_sc and
    # legends_ema were cured IN V3 under the owner's any-price ruling
    # (fractional sizing at the source); their pins below are the
    # cured v3 bytes and the v2-source equality no longer applies to
    # them (the v3 copy is the governed copy). Every other file keeps
    # both assertions at full strength.
    WS4_CURED = {"gate_1h", "leader_d", "leader_sc", "legends_ema"}

    def test_strategy_files_byte_identical_to_v2(self):
        for sid, want in STRATEGY_SHA256.items():
            p = os.path.join(ROOT, "desk3", "vendor", "sleeves", f"{sid}.py")
            got = hashlib.sha256(open(p, "rb").read()).hexdigest()
            self.assertEqual(got, want, sid)
            if sid in self.WS4_CURED:
                continue
            src = os.path.join(V2, "sleeves", f"{sid}.py")
            self.assertEqual(got, hashlib.sha256(open(src, "rb").read()).hexdigest(),
                             f"{sid} vs live v2 source")

    def test_vendor_core_and_journal_pinned(self):
        for rel, want in (("desk3/vendor/core/sleeve.py", CORE_SHA256),
                          ("desk3/vendor/runtime/journal.py", JOURNAL_SHA256)):
            got = hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()
            self.assertEqual(got, want, rel)

    def test_config_rows_registered(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = {r["id"]: r for r in cfg["sleeves"]}
        v2rows = {r["id"]: r for r in
                  json.load(open(os.path.join(V2, "config", "sleeves.json")))["sleeves"]}
        for sid in SLEEVES:
            self.assertIn(sid, rows)
            # IU-BODY-ORDER-LOGIC-20261116 (see header amendment):
            # this one row's module is the faithful desk-side
            # implementation; the port adapter remains pinned by
            # the sha and oracle tests in this file.
            want_module = ("adapters3.fwd_alpaca_enj_iu_body"
                           if sid == "fwd_alpaca_enj_iu_body"
                           else f"desk3.sleeves.{sid}")
            self.assertEqual(rows[sid]["module"], want_module)
            self.assertEqual(rows[sid]["cadence_s"], v2rows[sid]["cadence_s"], sid)
            self.assertEqual(rows[sid]["slice"], v2rows[sid]["slice"], sid)
            self.assertTrue(rows[sid]["inputs"], sid)

    def test_registry_inputs_declared(self):
        import importlib
        from desk3.registry import Registry
        reg = Registry()
        mods = {}
        all_inputs = set()
        for sid in SLEEVES:
            mod = importlib.import_module(f"desk3.sleeves.{sid}")
            mods[sid] = mod
            self.assertTrue(mod.INPUTS, sid)
            all_inputs.update(mod.INPUTS)
        reg.register_producer("warm", outputs=tuple(sorted(all_inputs)),
                              freshness_sla_s=10 ** 9)
        for sid in SLEEVES:
            reg.register_sleeve(sid, mods[sid].INPUTS)
        reg.mark_produced("warm", ts=1000.0)
        fed = reg.fed_states(now=1001.0)
        for sid in SLEEVES:
            self.assertEqual(fed[sid]["state"], "FED", sid)


if __name__ == "__main__":
    unittest.main()
