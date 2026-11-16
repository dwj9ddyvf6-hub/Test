"""EDGE-16 blockers (Harden+Enhance Edge pass batch 16).

ENH2 adapter-level decision changes (default ON; OFF restores the
pre-change rule exactly; vendor/strategy files untouched):
- free_opt_pair / free_opt_release: refuse a package whose legs carry
  mismatched (or unparseable) OCC expiries — the package is priced as
  one simultaneous structure; legs expiring on different dates leave
  an unhedged residual after the first expiry.
- free_opt_tail: refuse a put with fewer than 5 calendar days to
  expiry — the designed exit stack (5 sessions / 50% premium loss)
  cannot run inside that life; theta crush is the binding leak.
- free_opt_wheel: refuse selling a put expiring on/before the entry
  session (zero-life premium sale, same class as tail's first ENH).
- free_opt_parity: refuse a box whose expiry is > 60 DTE — the edge
  is locked only at expiry, so a long-dated box locks the slice's
  capital for the same 0.30/share edge a short box pays in weeks.

Fail direction: on the pre-ENH2 tree every *_refused_on case emits
(the adapter had no such filter), so these tests fail there.
"""
import importlib, os, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
NOW = "2026-10-23T10:00:00-04:00"
NOW_UTC = "2026-10-23T14:00:00+00:00"
FRESH = {"t": NOW_UTC, "received_at": NOW_UTC, "ap": 2.5, "bp": 2.4}
CALL = "SPY261030C00500000"
PUT = "SPY261030P00500000"


def ev(sid, now=NOW, extra=None, positions=None, bars=None):
    mod = importlib.import_module(f"desk3.sleeves.{sid}")
    view = {"now": now, "extra": extra or {}, "positions": positions or [],
            "bars": bars or {},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    return mod.evaluate(view, {"sleeve_id": sid})


def pair_pkg(sym2, enh2=None):
    ex = {"quote": FRESH, "package": {"legs": [
        {"underlying": "SPY", "symbol": CALL, "ask": 2.5},
        {"underlying": "QQQ", "symbol": sym2, "ask": 1.5}],
        "hedge_frozen": True, "hedge": {"ratio": 0.5}}}
    if enh2 is not None:
        ex["free_opt_pair_enh2"] = {"enabled": enh2}
    return ex


def straddle(call, put, enh2=None):
    ex = {"quote": FRESH, "package": {"legs": [
        {"right": "call", "symbol": call, "ask": 2.5, "source_at": NOW_UTC},
        {"right": "put", "symbol": put, "ask": 2.4, "source_at": NOW_UTC}]},
        "events": [{"session": "2026-10-23", "verified": True}]}
    if enh2 is not None:
        ex["free_opt_release_enh2"] = {"enabled": enh2}
    return ex


class TestPairExpiryCoherence(unittest.TestCase):
    def test_mismatched_expiry_refused_on(self):
        out = ev("free_opt_pair", extra=pair_pkg("QQQ261106C00350000"))
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])

    def test_mismatched_expiry_enters_off(self):
        out = ev("free_opt_pair",
                 extra=pair_pkg("QQQ261106C00350000", enh2=False))
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 2)

    def test_matched_expiry_still_enters_on(self):
        out = ev("free_opt_pair", extra=pair_pkg("QQQ261030C00350000"))
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 2)


class TestReleaseExpiryCoherence(unittest.TestCase):
    def test_mismatched_expiry_refused_on(self):
        out = ev("free_opt_release",
                 extra=straddle(CALL, "SPY261106P00500000"))
        self.assertEqual(out, [])

    def test_mismatched_expiry_enters_off(self):
        out = ev("free_opt_release",
                 extra=straddle(CALL, "SPY261106P00500000", enh2=False))
        self.assertEqual(len(out), 2)

    def test_matched_expiry_still_enters_on(self):
        out = ev("free_opt_release", extra=straddle(CALL, PUT))
        self.assertEqual(len(out), 2)


class TestTailMinLife(unittest.TestCase):
    def _q(self, sym):
        return {"symbol": sym, "t": NOW_UTC, "received_at": NOW_UTC,
                "ap": 1.2, "bp": 1.1}

    def test_short_life_put_refused_on(self):
        out = ev("free_opt_tail",
                 extra={"quote": self._q("SPY261026P00500000"),
                        "underlying_return": -0.05})
        self.assertEqual(out, [])

    def test_short_life_put_enters_off(self):
        out = ev("free_opt_tail",
                 extra={"quote": self._q("SPY261026P00500000"),
                        "underlying_return": -0.05,
                        "free_opt_tail_enh2": {"enabled": False}})
        self.assertEqual(len(out), 1)

    def test_normal_life_put_still_enters_on(self):
        out = ev("free_opt_tail",
                 extra={"quote": self._q(PUT), "underlying_return": -0.05})
        self.assertEqual(len(out), 1)


class TestWheelZeroLifePut(unittest.TestCase):
    def _q(self, sym):
        return {"symbol": sym, "t": NOW_UTC, "received_at": NOW_UTC,
                "ap": 1.2, "bp": 1.1, "strike": 50}

    def test_zero_life_put_refused_on(self):
        out = ev("free_opt_wheel",
                 extra={"quote": self._q("SPY261023P00500000"),
                        "cash": 100000.0})
        self.assertEqual([i for i in out if i["kind"] == "entry"], [])

    def test_zero_life_put_enters_off(self):
        out = ev("free_opt_wheel",
                 extra={"quote": self._q("SPY261023P00500000"),
                        "cash": 100000.0,
                        "free_opt_wheel_enh2": {"enabled": False}})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_normal_put_still_enters_on(self):
        out = ev("free_opt_wheel",
                 extra={"quote": self._q(PUT), "cash": 100000.0})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


class TestParityDteCap(unittest.TestCase):
    def _quotes(self, exp, occs):
        def q(s, st, r, b, a):
            return {"symbol": s, "expiration": exp, "strike": st,
                    "right": r, "bid": b, "ask": a}
        c1, p1, c2, p2 = occs
        return [q(c1, 595, "call", 12.00, 12.10), q(p1, 595, "put", 7.00, 7.10),
                q(c2, 600, "call", 10.00, 10.10), q(p2, 600, "put", 9.35, 9.45)]

    def test_long_dated_box_refused_on(self):
        occs = ("SPY270219C00595000", "SPY270219P00595000",
                "SPY270219C00600000", "SPY270219P00600000")
        out = ev("free_opt_parity", now="2026-10-23T15:00:00+00:00",
                 extra={"parity_quotes": self._quotes("2027-02-19", occs),
                        "parity_spot": 600.0})
        self.assertEqual(out, [])

    def test_long_dated_box_enters_off(self):
        occs = ("SPY270219C00595000", "SPY270219P00595000",
                "SPY270219C00600000", "SPY270219P00600000")
        out = ev("free_opt_parity", now="2026-10-23T15:00:00+00:00",
                 extra={"parity_quotes": self._quotes("2027-02-19", occs),
                        "parity_spot": 600.0,
                        "free_opt_parity_enh2": {"enabled": False}})
        self.assertEqual(len(out), 4)

    def test_near_box_still_enters_on(self):
        occs = ("SPY261106C00595000", "SPY261106P00595000",
                "SPY261106C00600000", "SPY261106P00600000")
        out = ev("free_opt_parity", now="2026-10-23T15:00:00+00:00",
                 extra={"parity_quotes": self._quotes("2026-11-06", occs),
                        "parity_spot": 600.0})
        self.assertEqual(len(out), 4)


if __name__ == "__main__":
    unittest.main()
