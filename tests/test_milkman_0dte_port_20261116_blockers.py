"""Milkman 0DTE intraday-study port blockers (MILKMAN-0DTE-PORT-20261116).

PROVENANCE gap 1 (MILKMAN-0DTE-INSTALL-20261027) stood since install:
mk_zerodte_spx's entry signals are lane trades from the Milkman
intraday study (Femto-lean desk/sleeves/milkman/intraday.py), which
was never ported, so adapters/milkman_0dte.py left lane_signals
empty and the sleeve could never enter.

The study was recovered from GitHub Femto-lean branch milkman-0dte
@ 8c64cd5cc53a (the vendored sleeve's own commit) via the ghapi
route and landed:
  * desk3/milkman_0dte/intraday.py  byte-exact provenance artifact
    (blob d6339131541cc460b7650d468d99cd691606f6f8)
  * desk3/milkman_0dte/mlib.py      byte-exact study library
    (blob 0e488ae7ad34c37197b7141afb3ba5d1483892f6)
  * desk3/milkman_0dte/intraday_study.py  the live v3-native port:
    detection line-for-line from the vendored module (pinned
    structurally below), dependency shims only.
Adapters/milkman_0dte.py now builds the study Panel from the
snapshot's SPY bars and fills lane_signals / lane_exits under the
vendored authored sleeve's own eligibility rules (same_bar /
missed / LATE=2 / ESMON+OPX4 excluded).

Proof levels in this file:
  * differential: the port's lane_trades are compared EXACTLY
    against the byte-exact vendored module (stub-loaded with the
    port's own calendar shim) on synthetic tapes;
  * hand-computed: GAP / DGG / CASCADE lane values on the femto
    fixture tape (prior close 100, ATR14 exactly 2) computed from
    the study's stated level arithmetic, plus the LEMA train-era
    threshold quantile and the MDL same-bar shape;
  * wiring: a fresh GAP lane trade on a one-bar live panel enters
    through the full adapter + sleeve path on a fixture chain;
    stale / same-bar / no-bar cases produce no signals, named.

Named limitation (not a pass): the LEMA lane's 2000-2012 train
threshold is not computable from the snapshot's 500-day daily
history, so LEMA yields no live signals; the rule is proven here
on train-era fixtures and the live-depth behaviour is pinned.

Fail direction: on the pre-port tree this file fails at collection
(desk3.milkman_0dte.intraday_study does not exist). Mutating the
port (e.g. LV 0.382 -> 0.5, or LATE 2 -> 99 in the adapter's
eligibility) fails the hand-computed / wiring tests.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import types
import unittest
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
DAY = "2027-04-14"  # a Wednesday, full session (the femto fixture day)

INTRADAY_SHA256 = "77034c9fc88edea81fa304e2bd7cbe13b952b739a4b8fd9accf1c873b7785362"
MLIB_SHA256 = "0c6823c0c1a55ca8520f5121c8660ff46170813a67fb24a2c5e51adb16a536b9"
SATY_SOL_SHA256 = "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc"


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def et(d, hh, mm, ss=0):
    return datetime.combine(date.fromisoformat(d), dtime(hh, mm, ss), ET).timestamp()


def bar(t, o, h, l, c, v=1e5):
    return {"t": t, "o": o, "h": max(h, o, c), "l": min(l, o, c), "c": c, "v": v}


def _full_day(d):
    from desk3.milkman_0dte import intraday_study as I
    return I.full_day(d)


def sessions_before(end, n):
    out, d = [], date.fromisoformat(end) - timedelta(days=1)
    while len(out) < n:
        if _full_day(d):
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out[::-1]


def flat_session(d, base=100.0):
    """A full RTH session at `base`: daily range exactly 2, close base
    (the femto fixture: prior close 100, ATR14 exactly 2)."""
    out = []
    for k in range(390):
        hh, mm = divmod(570 + k, 60)
        out.append(bar(et(d, hh, mm), base,
                       base + (1.0 if k == 100 else 0.05),
                       base - (1.0 if k == 200 else 0.05), base))
    return out


def history(day, n=6):
    out = []
    for d in sessions_before(day, n):
        out += flat_session(d)
    return out


def climb(d, open_, step, k_stop=390, n=390):
    out, c = [], open_
    for k in range(n):
        hh, mm = divmod(570 + k, 60)
        o = c
        c = round(c + step, 4) if k < k_stop else c
        out.append(bar(et(d, hh, mm), o, max(o, c) + 0.01, min(o, c) - 0.01, c))
    return out


def _load_vendored_original():
    """Stub-load the byte-exact vendored intraday.py (its femto
    framework imports do not exist in v3) with the port's calendar
    shim and the vendored mlib, for differential comparison."""
    from desk3.milkman_0dte import intraday_study as P
    spec = importlib.util.spec_from_file_location(
        "milkman_mlib_ref", os.path.join(ROOT, "desk3", "milkman_0dte", "mlib.py"))
    mlib = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mlib)

    def mod(name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m
        return m

    class _Stub:
        def __init__(self, *a, **k):
            pass

    vend = types.ModuleType("vendored_ref")
    vend.load = lambda name: mlib
    milk = mod("ref.desk.sleeves.milkman", MARGIN_RATE=0.08)
    milk.__path__ = []
    milk.vendored = vend
    mod("ref.desk.contract", Intent=_Stub, OrderSpec=_Stub,
        Sleeve=object, SleeveConfig=_Stub)
    desk = mod("ref.desk", calendar=P.cal)
    desk.__path__ = []
    sleeves = mod("ref.desk.sleeves")
    sleeves.__path__ = []
    spec = importlib.util.spec_from_file_location(
        "ref.desk.sleeves.milkman.intraday",
        os.path.join(ROOT, "desk3", "milkman_0dte", "intraday.py"))
    orig = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = orig
    spec.loader.exec_module(orig)
    return orig


def _all_lanes(mod_, P):
    res = {}
    if P.live_di is None:
        return res
    for setup, (_, picks) in mod_.SETUPS.items():
        for sd, cell in picks:
            trs = mod_.lane_trades(setup, P, P.live_di, cell, sd)
            res[(setup, sd, cell)] = [
                (t["key"], t["decide"],
                 None if t.get("exit") is None else
                 (t["exit"][0], round(float(t["exit"][1]), 8)))
                for t in trs]
    return res


class VendoredPins(unittest.TestCase):
    def test_vendored_intraday_byte_exact(self):
        p = os.path.join(ROOT, "desk3", "milkman_0dte", "intraday.py")
        self.assertEqual(_sha(p), INTRADAY_SHA256)

    def test_vendored_mlib_byte_exact(self):
        p = os.path.join(ROOT, "desk3", "milkman_0dte", "mlib.py")
        self.assertEqual(_sha(p), MLIB_SHA256)

    def test_source_pin_verbatim(self):
        from desk3.milkman_0dte import intraday_study as I
        self.assertEqual(I.SOURCE["commit"],
                         "0be4c57569e363d052bd23564cf0664697439927")
        self.assertEqual(I.SOURCE["blob"], "9ea632d0b65cebcd7f4bbd4adcf4537c1b5c2a3c")
        self.assertEqual(I.SOURCE["blob2"], "410af17efea5b359fb4197ae3bad5903bc152ae5")
        self.assertEqual(I.LATE, 2)
        self.assertIn("ESMON", I.SETUPS)
        self.assertIn("OPX4", I.SETUPS)

    def test_detection_body_identical_to_vendored(self):
        """From SOURCE to the end of lane_trades/_next_full_days, the
        port is the vendored text except the M() loader line."""
        vend = open(os.path.join(ROOT, "desk3", "milkman_0dte", "intraday.py")).read()
        port = open(os.path.join(ROOT, "desk3", "milkman_0dte", "intraday_study.py")).read()
        marker = "# --------------------------------------------------------------------------------------------- the sleeve"
        v = vend[vend.index("SOURCE ="):vend.index(marker)]
        p = port[port.index("SOURCE ="):]
        v = v.replace('def M():\n    return V.load("mlib")\n',
                      'def M():\n    return _mlib\n')
        self.assertEqual(p.rstrip(), v.rstrip())


class DifferentialParity(unittest.TestCase):
    """The port reproduces the recovered study's own port, trade for
    trade, on synthetic tapes (the study's recorded examples are
    its femto parity receipt: 1,778 cases / 26,854 lane trades /
    0 diffs — this is the v3 port against that same module)."""

    @classmethod
    def setUpClass(cls):
        cls.orig = _load_vendored_original()

    def _compare(self, m1, d1=None, h1=None):
        from desk3.milkman_0dte import intraday_study as P
        Po = self.orig.Panel(list(m1), d1, h1, today=DAY)
        Pp = P.Panel(list(m1), d1, h1, today=DAY)
        self.assertEqual(_all_lanes(self.orig, Po), _all_lanes(P, Pp))

    def test_gap_climb_tape(self):
        self._compare(history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60))

    def test_gap_down_climb_tape(self):
        self._compare(history(DAY) + climb(DAY, 99.95, -0.02, k_stop=60))

    def test_partial_live_tape(self):
        self._compare(history(DAY) + climb(DAY, 100.05, 0.03)[:120])

    def test_flat_tape(self):
        self._compare(history(DAY) + flat_session(DAY))


class HandComputed(unittest.TestCase):
    """Values computed by hand from the study's stated arithmetic on
    the fixture tape (PDC 100, ATR14 2, open 100.05, +0.02/min)."""

    @classmethod
    def setUpClass(cls):
        from desk3.milkman_0dte import intraday_study as I
        cls.I = I
        cls.P = I.Panel(history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60),
                        today=DAY)

    def test_panel_day_facts(self):
        P, di = self.P, self.P.live_di
        self.assertEqual(P.PDC[di], 100.0)
        self.assertEqual(P.ATR[di], 2.0)

    def test_gap_momentum_long(self):
        # gap +0.05% -> bucket (0.0, 0.1]; momentum side is long:
        # entry the open bar at 100.05, target open + 0.5*ATR =
        # 101.05, stop the prior close 100.0; exit at the target.
        (t,) = self.I.lane_trades(
            "GAP", self.P, self.P.live_di,
            "bucket=0.0-0.1;stopATR=0.5;target=full", 1)
        s0 = int(self.P.S0[self.P.live_di])
        self.assertEqual(t["decide"], s0)
        self.assertEqual(t["ep"], 100.05)
        self.assertEqual(t["tgt"], 101.05)
        self.assertEqual(t["stp"], 100.0)
        self.assertEqual(t["exit"], (s0 + 49, 101.05))
        self.assertEqual(t["key"], f"{s0}|101.050000|100.000000")

    def test_day_golden_gate_long(self):
        # levels off PDC/ATR: 38.2% = 100.764 (entry), 61.8% =
        # 101.236 (target), 23.6% = 100.472 (stop).
        (t,) = self.I.lane_trades(
            "DGG", self.P, self.P.live_di, "cohort=live;filter=none", 1)
        self.assertAlmostEqual(t["ep"], 100.764)
        self.assertAlmostEqual(t["tgt"], 101.236)
        self.assertAlmostEqual(t["stp"], 100.472)

    def test_cascade_first_rung(self):
        trs = self.I.lane_trades(
            "CASCADE", self.P, self.P.live_di, "window=all", 1)
        first = trs[0]
        self.assertAlmostEqual(first["ep"], 100.472)   # 23.6% level
        self.assertAlmostEqual(first["tgt"], 100.764)  # next: 38.2%
        self.assertAlmostEqual(first["stp"], 100.0)    # prev: 0%

    def test_lema_threshold_train_era(self):
        # The femto divergence-7 fixture: daily bars 2011-2013 with
        # body/range ratios cycling deterministically; the 0.8
        # quantile of the pre-2013 rows is hand-computed here.
        import numpy as np
        I = self.I
        d1, d, k = [], date(2011, 1, 3), 0
        while d < date(2013, 3, 1):
            if I.full_day(d):
                body = 0.1 + 0.8 * ((k * 37) % 100) / 100.0
                d1.append({"t": et(d.isoformat(), 9, 30), "o": 100.0,
                           "h": 101.0, "l": 100.0, "c": 100.0 + body, "v": 1})
                k += 1
            d += timedelta(days=1)
        P = I.Panel([], d1)
        train = [x for x in d1 if I.cal._as_date(x["t"]) < date(2013, 1, 1)]
        want = float(np.quantile(
            [abs(x["c"] - x["o"]) / (x["h"] - x["l"]) for x in train], 0.8))
        self.assertAlmostEqual(I.lema_threshold(P, 0.8), want, places=12)
        self.assertAlmostEqual(want, 0.732, places=9)

    def test_lema_threshold_absent_on_recent_history_only(self):
        # The named live limitation: with no 2000-2012 sessions in
        # the daily table the threshold is None and the lane is dark.
        I = self.I
        P = I.Panel(history(DAY), today=None)
        self.assertIsNone(I.lema_threshold(P, 0.8))

    def test_mdl_same_bar_shape(self):
        # The femto divergence-1 fixture: the fill bar also touches
        # the stop, so decide == exit bar (the wiring must not enter).
        import numpy as np
        I = self.I
        m1 = history(DAY)
        c = 100.0
        for kk in range(240, 600):
            hh, mm = divmod(kk, 60)
            o, c = c, (100.10 if kk % 2 else 100.0)
            m1.append(bar(et(DAY, hh, mm), o, max(o, c) + 0.02,
                          min(o, c) - 0.02, c))
        F = I._mdl_frame(I.Panel(m1, today=DAY))
        i = int(np.flatnonzero(F["m3"] == 27)[-1])
        A, Cl = F["ATR3"][i], F["C3"][i]
        lim = Cl - A
        stp = lim - max(1.5 * A, 0.04)
        m1.append(bar(et(DAY, 10, 0), 100.0, 100.02, stp - 0.05, 100.0))
        P = I.Panel(m1, today=DAY)
        (tr,) = I.lane_trades("MDL", P, P.live_di, "er=0.35;k=1.0", 1)
        self.assertEqual(tr["decide"], tr["exit"][0])


class _Bar:
    def __init__(self, r):
        self.t = datetime.fromtimestamp(r["t"], ET).isoformat()
        self.o, self.h, self.l, self.c = r["o"], r["h"], r["l"], r["c"]
        self.v = r.get("v", 0.0)


class _Ctx:
    """The SnapshotSleeveContext bars() surface the adapter reads."""

    def __init__(self, bars_map):
        self._bars = bars_map

    def bars(self, symbol, tf, n):
        return [_Bar(r) for r in self._bars.get(f"{symbol}|{tf}", [])][-int(n):]


class AdapterWiring(unittest.TestCase):
    def _ctx(self, m1, d1=(), h1=()):
        return _Ctx({"SPY|1Min": list(m1), "SPY|1Day": list(d1),
                     "SPY|1Hour": list(h1)})

    def test_fresh_gap_trade_is_a_lane_signal(self):
        from adapters.milkman_0dte import lane_signals_for
        # Live panel with only the 09:30 bar present: the GAP
        # momentum-long trade decided on that bar (decide == jmax,
        # within LATE) and has not exited.
        m1 = history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60)[:1]
        signals, exits, note = lane_signals_for(self._ctx(m1), DAY, set())
        self.assertEqual(note, "")
        self.assertEqual(exits, [])
        self.assertIn({"key": f"GAP:L|{DAY}|2340|101.050000|100.000000"
                              .replace("2340", str(6 * 390)),
                       "side": 1}, signals)

    def test_stale_gap_trade_is_missed_not_signalled(self):
        from adapters.milkman_0dte import lane_signals_for
        # The full morning is present: the GAP trade decided at the
        # open, long past LATE, and already exited — no signal.
        m1 = history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60)
        signals, exits, note = lane_signals_for(self._ctx(m1), DAY, set())
        self.assertEqual(note, "")
        self.assertFalse(any(s["key"].startswith("GAP:L|") for s in signals))
        self.assertEqual(exits, [])

    def test_open_trade_exit_is_a_lane_exit(self):
        from adapters.milkman_0dte import lane_signals_for
        m1 = history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60)
        s0 = 6 * 390
        key = f"GAP:L|{DAY}|{s0}|101.050000|100.000000"
        signals, exits, note = lane_signals_for(self._ctx(m1), DAY, {key})
        self.assertIn(key, exits)

    def test_no_bars_fails_closed_named(self):
        from adapters.milkman_0dte import lane_signals_for
        signals, exits, note = lane_signals_for(self._ctx([]), DAY, set())
        self.assertEqual((signals, exits), ([], []))
        self.assertIn("no SPY 1Min bars", note)

    def test_early_close_session_not_traded(self):
        from adapters.milkman_0dte import lane_signals_for
        hd = "2026-11-27"  # day after Thanksgiving: 13:00 close
        m1 = history(hd, 3) + climb(hd, 100.05, 0.02, n=210)
        signals, exits, note = lane_signals_for(self._ctx(m1), hd, set())
        self.assertEqual((signals, exits), ([], []))
        self.assertIn("not a full session", note)

    def test_no_esmon_or_opx4_signals_ever(self):
        from adapters.milkman_0dte import lane_signals_for
        m1 = history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60)[:1]
        signals, _, _ = lane_signals_for(self._ctx(m1), DAY, set())
        self.assertFalse(any(s["key"].split(":")[0] in ("ESMON", "OPX4")
                             for s in signals))


def _occ(cp, k, exp=DAY):
    y, m, d = exp.split("-")
    return f"SPXW{y[2:]}{m}{d}{cp}{int(k * 1000):08d}"


def _chain_rows(now):
    out = []
    for cp, typ, sgn in (("C", "call", 1), ("P", "put", -1)):
        for k, dl in ((5000, 0.55), (5010, 0.40), (5020, 0.25)):
            out.append({"symbol": _occ(cp, k), "root": "SPXW",
                        "expiration": DAY, "type": typ, "strike": float(k),
                        "bid": 10.0, "ask": 10.4, "delta": sgn * dl, "t": now})
    return out


class FullEntryPath(unittest.TestCase):
    """Through adapters3 + adapters + sleeve: a study lane signal on
    the snapshot's SPY bars becomes the authored SPX 0DTE entry."""

    def test_gap_signal_enters_the_delta_040_call_at_the_ask(self):
        import tempfile
        from adapters3 import milkman_0dte as A3
        m1 = history(DAY) + climb(DAY, 100.05, 0.02, k_stop=60)[:1]
        now = datetime(2027, 4, 14, 9, 31, 5, tzinfo=ET)
        now_ts = now.timestamp()
        bars = {}
        for tf, rows in (("1Min", m1), ("1Day", []), ("1Hour", [])):
            bars[f"SPY|{tf}"] = [
                {"t": datetime.fromtimestamp(r["t"], ET).isoformat(),
                 "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"],
                 "v": r["v"]} for r in rows]
        view = {"now": now.isoformat(), "bars": bars, "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {"extra": {
                    "spx_probe": {"available": True, "underlying": "SPXW",
                                  "why": None},
                    "chain_rows": _chain_rows(now_ts), "quotes": {}}}}
        with tempfile.TemporaryDirectory() as sd:
            out = A3.evaluate(view, {"state_dir": sd,
                                     "now": now.isoformat()})
        entries = [i for i in out if i["kind"] == "entry"]
        (e,) = entries
        self.assertEqual(e["symbol"], _occ("C", 5010))
        self.assertEqual(e["qty"], 2.0)
        self.assertEqual(e["limit_price"], 10.4)
        self.assertIn("GAP:L|" + DAY, e["reason"])

    def test_adapters3_inputs_declare_the_spy_panel(self):
        from adapters3 import milkman_0dte as A3
        self.assertIn("bars:SPY:1Min", A3.INPUTS)
        self.assertIn("bars_1min", A3.INPUTS)
        self.assertIn("milkman_0dte_chain", A3.INPUTS)


class TruthSurfaces(unittest.TestCase):
    def test_provenance_gap1_closed_and_lema_named(self):
        text = open(os.path.join(
            ROOT, "desk3", "milkman_0dte", "PROVENANCE.md")).read()
        self.assertIn("Gap 1 CLOSED", text)
        self.assertIn("MILKMAN-0DTE-PORT-20261116", text)
        self.assertIn(INTRADAY_SHA256, text)
        self.assertIn("LEMA", text)

    def test_config_row_names_the_port(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows_ = cfg["sleeves"] if isinstance(cfg, dict) else cfg
        (r,) = [x for x in rows_ if x["id"] == "mk_zerodte_spx"]
        self.assertIn("bars:SPY:1Min", r["inputs"])
        self.assertIn("MILKMAN-0DTE-PORT-20261116",
                      r["params"]["entry_blocked_reason"])
        self.assertNotIn("lane_signals stay empty",
                         r["params"]["entry_blocked_reason"])
        # sizing / stop untouched by the port
        self.assertEqual(r["params"]["daily_stop"], -10000.0)
        self.assertEqual(r["params"]["premium_per_trade"], 2500.0)
        self.assertEqual(r["slice"]["capital_usd"], 10000.0)

    def test_saty_sol_pin_unchanged(self):
        self.assertEqual(
            _sha(os.path.join(ROOT, "sleeves", "saty_sol.py")),
            SATY_SOL_SHA256)


if __name__ == "__main__":
    unittest.main()
