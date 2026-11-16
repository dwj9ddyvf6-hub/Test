"""F2-SHIM-TYPES-20261115 blockers: shim/adapter extra-field type defects.

Defect class: a shim stamps an extra field whose type mismatches its
consumer's documented expectation, crashing the sleeve's signal().

Cured pairs (both in desk3/sleeves/iron_condor.py, the port-4 shim):
  1. extra["vix"]: shim stamped a 4-tuple (last, prev, date, source);
     the vendor strategy documents float | None and calls float(vix)
     -> TypeError on every session served from warmed VIX bars
     (Unblock-2 replay: every session from 2026-09-01).
  2. extra["chains"]: shim merged the live options payload's flat
     row list {SYM: [rows]} through untouched; the vendor strategy
     documents {SYM: {"put": [...], "call": [...]}} and build_condor
     calls chain_by_kind.get("put") -> AttributeError on every entry
     evaluation that passed the vix/IV/earnings gates.

Checked-and-cleared pairs pinned here so nobody "fixes" them:
  adapters/{beatendown,confluence,momentum}.py stamp the same vix
  4-tuple, but THEIR strategies (sleeves/<id>.py) document and unpack
  exactly that tuple — correct for their consumers.

Fail direction proven on preserved pre-cure copies in /tmp (see
BUGLOG_2026-11-15.md, F2-SHIM-TYPES-20261115).
"""
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.sleeves import iron_condor as shim  # noqa: E402


def _weekdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return list(reversed(out))


def _daily(end, n, c0, c1):
    return [{"t": f"{d.isoformat()}T04:00:00Z", "o": c0, "h": c0 + 1,
             "l": c0 - 1, "c": c0 + (c1 - c0) * i / max(1, n - 1),
             "v": 200000.0}
            for i, d in enumerate(_weekdays(end, n))]


def _live_payload(sess):
    """Live producer shape (desk3/producers.py build_options_payload):
    chains {UND: [flat rows carrying "right"]}, quotes {OCC: {bid, ask}}."""
    exp = (sess + timedelta(days=37)).isoformat()
    rows, quotes = [], {}
    for strike in range(70, 146):
        for kind, right in (("P", "put"), ("C", "call")):
            occ = f"NBIS{exp[2:4]}{exp[5:7]}{exp[8:10]}{kind}{int(strike * 1000):08d}"
            rows.append({"symbol": occ, "strike": float(strike),
                         "expiration": exp, "right": right})
            bid = max(0.1, (strike - 60) * 0.05) if right == "put" \
                else max(0.1, (160 - strike) * 0.05)
            quotes[occ] = {"bid": round(bid, 2), "ask": round(bid * 1.02, 2)}
    return {"chains": {"NBIS": rows}, "quotes": quotes}


def _view(sess, full=False, vix_c1=20.0):
    view = {"now_iso": f"{sess.isoformat()}T14:00:00+00:00",
            "bars": {"NBIS|1Day": _daily(sess, 40, 90, 100),
                     "VIX|1Day": _daily(sess, 10, 19, vix_c1)},
            "positions": [],
            "slice": {"iron_condor": {"capital_usd": 1000000.0,
                                      "cash_usd": 1000000.0}},
            "params": {"iron_condor": {}},
            "options": {}, "earnings": {}, "iv": {}, "quotes": {}}
    if full:
        view["options"] = {"NBIS": _live_payload(sess)}
        view["iv"] = {"NBIS": {"current": 0.65,
                               "history": [0.3 + 0.004 * i for i in range(100)]}}
        view["earnings"] = {"earnings": {
            "NBIS": (sess + timedelta(days=90)).isoformat()}}
    return view


class ShimTypeF2Blockers(unittest.TestCase):
    def _eval(self, view):
        with tempfile.TemporaryDirectory() as td:
            return shim.evaluate(view, {"sleeve_id": "iron_condor",
                                        "state_dir": td})

    def test_vix_stamp_no_crash_from_2026_09_01(self):
        # The replay's crash window: VIX bars served, no params vix.
        for sess in (date(2026, 9, 1), date(2026, 9, 14),
                     date(2026, 10, 26), date(2026, 11, 13)):
            out = self._eval(_view(sess))
            self.assertIsInstance(out, list)

    def test_vix_scalar_gate_actually_compares(self):
        # VIX close 40 > VIX_MAX 35: the cured scalar stamp must gate
        # entries OUT (a stamp that merely avoided the crash by being
        # swallowed would let the entry through).
        out = self._eval(_view(date(2026, 10, 23), full=True, vix_c1=40.0))
        self.assertEqual(out, [])
        out = self._eval(_view(date(2026, 10, 23), full=True, vix_c1=20.0))
        self.assertEqual(len(out), 4)

    def test_chains_live_flat_shape_reaches_build_condor(self):
        # Full live-shaped drive: entry fires and fans out to 4 legs.
        out = self._eval(_view(date(2026, 10, 23), full=True))
        self.assertEqual(len(out), 4)
        self.assertTrue(all(d.get("condor") for d in out))
        kinds = {d["position_intent"] for d in out}
        self.assertEqual(kinds, {"sell_to_open", "buy_to_open"})

    def test_chains_by_kind_grouping_and_occ_fallback(self):
        rows = [{"symbol": "NBIS261129P00090000", "strike": 90.0},
                {"symbol": "NBIS261129C00110000", "strike": 110.0},
                {"symbol": "NBIS261129C00120000", "strike": 120.0,
                 "right": "call"},
                {"symbol": "JUNK", "strike": 1.0}]
        grouped = shim._chains_by_kind(rows)
        self.assertEqual([r["strike"] for r in grouped["put"]], [90.0])
        self.assertEqual([r["strike"] for r in grouped["call"]],
                         [110.0, 120.0])
        already = {"put": [1], "call": [2]}
        self.assertIs(shim._chains_by_kind(already), already)

    def test_replay_sessions_2026_09_01_onward_zero_crashes(self):
        sessions, d = [], date(2026, 9, 1)
        while d <= date(2026, 9, 14):
            if d.weekday() < 5:
                sessions.append(d)
            d += timedelta(days=1)
        sessions += [date(2026, 9, 21), date(2026, 9, 28),
                     date(2026, 10, 5), date(2026, 10, 12),
                     date(2026, 10, 19), date(2026, 10, 26),
                     date(2026, 11, 2), date(2026, 11, 9),
                     date(2026, 11, 13)]
        self.assertEqual(len(sessions), 19)
        for sess in sessions:
            self.assertIsInstance(self._eval(_view(sess)), list)
            self.assertEqual(len(self._eval(_view(sess, full=True))), 4)

    def test_tuple_vix_consumers_checked_and_cleared(self):
        # beatendown / confluence / momentum strategies DOCUMENT the
        # 4-tuple and unpack it; their adapters' tuple stamps are
        # correct for their consumers and must NOT be "cured".
        for sid in ("beatendown", "confluence", "momentum"):
            strat_src = open(os.path.join(ROOT, "sleeves", f"{sid}.py")).read()
            self.assertIn("(close, prev", strat_src.replace(
                "(close, prev_close", "(close, prev"))
            self.assertIn("vclose", strat_src)
            adap_src = open(os.path.join(ROOT, "adapters", f"{sid}.py")).read()
            self.assertIn('"cache")', adap_src)


if __name__ == "__main__":
    unittest.main()
