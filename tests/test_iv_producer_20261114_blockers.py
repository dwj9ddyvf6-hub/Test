"""IV PRODUCER blockers (Lane C, 2026-11-14; UNFED iron_condor `iv`).

Decision: IV-ROUTE-DECISION-2026-11-14.md — the desk route is the
existing AlpacaOptions route (desk3/producers.py fetch_option_contracts
/ fetch_option_snapshots, feed=indicative) with Black-Scholes inversion
in the producer layer; 15-minute delayed quotes are acceptable by the
owner's standing ruling (2026-11-08/12) and TastyTrade is the simulated
BOOK's options source, not the desk's.

Pinned behavior:
- current IV per watchlist symbol = BS inversion (the vendored
  strategy's own conventions: r=0.04, bisection) of the nearest
  30-45 DTE ATM call mid;
- a persistent ledger (state/iv_ledger.json) accrues ONE observation
  per symbol per quote session; reruns of the same session do not
  duplicate; history is served from the ledger only (no fabricated
  history — the strategy's 60-observation cold start stays honest);
- fail closed: a failed/absent source yields {} (or history-only
  rows), never an invented IV.
"""
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

NOW = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
SPOT = 100.0
TRUE_SIGMA = 0.42


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call(S, K, T, r, sigma):
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)


def _contracts(und, env, ref, max_dte=62):
    exp = (ref + timedelta(days=37)).isoformat()
    out = []
    for strike in (95.0, 100.0, 105.0):
        occ = f"{und}261221C{int(strike * 1000):08d}"
        out.append({"symbol": occ, "strike_price": strike,
                    "expiration_date": exp})
    return out


def _snapshots(occs, env):
    out = {}
    for occ in occs:
        strike = int(occ[-8:]) / 1000.0
        px = _bs_call(SPOT, strike, 37 / 365.0, 0.04, TRUE_SIGMA)
        out[occ] = {"latestQuote": {"bp": px - 0.05, "ap": px + 0.05,
                                    "t": "2026-11-13T20:00:00Z"}}
    return out


def _quotes(symbols, env):
    return {s: {"bp": SPOT - 0.01, "ap": SPOT + 0.01,
                "t": "2026-11-13T20:00:00Z"} for s in symbols}


class TestIVProducer(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "state"))
        return tmp

    def _producer(self, root, **kw):
        from desk3.producers import IVProducer
        kw.setdefault("contracts_fetcher", _contracts)
        kw.setdefault("snapshots_fetcher", _snapshots)
        kw.setdefault("quotes_fetcher", _quotes)
        return IVProducer(root, env={}, watchlist=("NBIS",), **kw)

    def test_current_iv_recovers_the_quoted_sigma(self):
        root = self._root()
        out = self._producer(root)({"now": NOW})
        row = out["iv"]["NBIS"]
        self.assertAlmostEqual(row["current"], TRUE_SIGMA, delta=0.01)
        self.assertEqual(row["history"], [row["current"]])

    def test_ledger_accrues_one_observation_per_session(self):
        root = self._root()
        p = self._producer(root)
        p({"now": NOW})
        p({"now": NOW})  # same quote session: no duplicate
        led = json.load(open(os.path.join(root, "state", "iv_ledger.json")))
        self.assertEqual(len(led["NBIS"]), 1)
        self.assertEqual(led["NBIS"][0]["session"], "2026-11-13")
        out = p({"now": NOW})
        self.assertEqual(len(out["iv"]["NBIS"]["history"]), 1)

    def test_preseeded_history_is_served_verbatim(self):
        root = self._root()
        hist = [{"session": f"2026-09-{d:02d}", "iv": 0.30 + d / 1000.0}
                for d in range(1, 29)]
        with open(os.path.join(root, "state", "iv_ledger.json"), "w") as fh:
            json.dump({"NBIS": hist}, fh)
        out = self._producer(root)({"now": NOW})
        served = out["iv"]["NBIS"]["history"]
        self.assertEqual(served[:28], [h["iv"] for h in hist])
        self.assertEqual(len(served), 29)  # + today's observation

    def test_fetch_failure_fails_closed_and_writes_nothing(self):
        root = self._root()

        def boom(*a, **k):
            raise RuntimeError("source down")

        out = self._producer(root, contracts_fetcher=boom)({"now": NOW})
        self.assertEqual(out, {})
        self.assertFalse(os.path.exists(
            os.path.join(root, "state", "iv_ledger.json")))

    def test_unquotable_contracts_fail_closed_per_symbol(self):
        root = self._root()
        out = self._producer(root, snapshots_fetcher=lambda o, e: {})(
            {"now": NOW})
        self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main()
