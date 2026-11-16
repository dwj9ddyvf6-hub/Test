"""Milkman 0DTE SPX blockers (MILKMAN-0DTE-INSTALL-20261027).

Install of Claude's Femto-lean milkman-0dte sleeve (branch milkman-0dte,
commit 8c64cd5c per SEMANTIC-AUDIT-2026-10-27 §3.8) into muse-desk-v3,
following the trullas_divergence install pattern. Rules as authored:
SPX 0DTE, paper only, -$10,000 daily stop (Milkman's own figure),
$2,500 premium per trade, max 4 open, |delta| nearest 0.40, ESMON and
OPX4 excluded, inert with the named reason "SPX 0DTE chain not
available" until the chain is proven, never a SPY fallback, never a
model price.

Landing state (named, not hidden): UNFED + PARKED.
  (1) The authored contract pick requires delta; this account tier
      serves options snapshots only via feed=indicative, which carries
      NO greeks, and feed=opra answers 403 (FEED-WIRE-20261025; live
      probe 2026-10-27: SPX lists 504 same-day contracts, quotes
      two-sided, delta absent on every snapshot).
  (2) Entry signals are the Milkman intraday study's lane trades
      (Femto-lean desk/sleeves/milkman/intraday.py). That module was
      not part of the vendored source set and has no v3 counterpart,
      so no lane signal can reach the sleeve until the study is
      ported. The sleeve's entry path is fixture-proven here through
      the named lane_signals seam and emits nothing in production.

Fail direction: on the pre-install tree this file fails at collection
(the modules do not exist). Mutating TARGET_DELTA 0.40 -> 0.55 in
sleeves/milkman_0dte.py makes test_pick_contract_nearest_delta_040
fail; mutating DAILY_STOP makes test_daily_stop fail. Both proven at
install, recorded in MILKMAN-0DTE-SLEEVE-BUILD.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
DAY = "2026-10-27"
START_EQUITY = 10000.0

VENDORED_SHA256 = "202841b379c96120b6e859a4a576d76fde8b4b24f7653b57a56ce7d04be106ee"
PARITY_SHA256 = "47ef6e9a6a9c69f998dbf74ce4563e138ae2ed67b953390801d0145e6e81fa27"


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def occ(cp, k, exp=DAY):
    y, m, d = exp.split("-")
    return f"SPXW{y[2:]}{m}{d}{cp}{int(k * 1000):08d}"


def rows(now, exp=DAY, bid=10.0, ask=10.4, t=None, delta=True):
    """The source test's fixture chain: SPXW calls/puts at deltas
    0.55 / 0.40 / 0.25, two-sided quotes."""
    out = []
    for cp, typ, sgn in (("C", "call", 1), ("P", "put", -1)):
        for k, d in ((5000, 0.55), (5010, 0.40), (5020, 0.25)):
            out.append({"symbol": occ(cp, k, exp), "underlying": "SPX",
                        "root": "SPXW", "expiration": exp, "type": typ,
                        "strike": float(k), "bid": bid, "ask": ask,
                        "delta": (sgn * d) if delta else None,
                        "t": now if t is None else t})
    return out


def _ctx(now, extra=None, equity=START_EQUITY):
    from core.sleeve import Context
    return Context(now=now, session=DAY, equity=equity, extra=extra or {})


def _drive(strat, now, extra=None, slice_state=None, state=None):
    ex = dict(extra or {})
    ex["milkman_state"] = dict(state or {})
    sleeve = strat.Milkman0DTESleeve()
    out = sleeve.signal({}, slice_state or {}, _ctx(now, ex))
    return sleeve, out


def et(h, m, s=5):
    return datetime(2026, 10, 27, h, m, s, tzinfo=ET).timestamp()


class VendoredSource(unittest.TestCase):
    def test_vendored_sleeve_byte_exact_vs_manifest(self):
        p = os.path.join(ROOT, "desk3", "milkman_0dte", "milkman_0dte.py")
        self.assertEqual(_sha(p), VENDORED_SHA256)

    def test_parity_doc_byte_exact(self):
        p = os.path.join(ROOT, "desk3", "milkman_0dte",
                         "2026-10-27-milkman-0dte-parity.md")
        self.assertEqual(_sha(p), PARITY_SHA256)

    def test_provenance_names_the_deferred_pieces(self):
        p = os.path.join(ROOT, "desk3", "milkman_0dte", "PROVENANCE.md")
        text = open(p).read()
        for needle in ("intraday", "delta", "PARKED", "milkman_0dte_chain"):
            self.assertIn(needle, text)


class AuthoredRules(unittest.TestCase):
    def test_constants_as_authored(self):
        from sleeves import milkman_0dte as Z
        self.assertEqual(Z.SID, "mk_zerodte_spx")
        self.assertEqual(Z.DAILY_STOP, -10000.0)
        self.assertEqual(Z.PREMIUM_PER_TRADE, 2500.0)
        self.assertEqual(Z.MAX_OPEN, 4)
        self.assertEqual(Z.TARGET_DELTA, 0.40)
        self.assertEqual(Z.EXCLUDED, ("ESMON", "OPX4"))
        self.assertEqual(Z.ROOTS, ("SPXW", "SPX"))
        self.assertTrue(Z.CONFIG.parked)
        self.assertEqual(Z.CONFIG.cadence_s, 60)

    def test_pick_contract_nearest_delta_040(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        row, why = Z.pick_contract(rows(now), 1, DAY, now)
        self.assertIsNone(why)
        self.assertEqual(row["symbol"], occ("C", 5010))
        row, _ = Z.pick_contract(rows(now), -1, DAY, now)
        self.assertEqual(row["type"], "put")

    def test_pick_contract_rejections(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        self.assertTrue(Z.pick_contract(rows(now, bid=5.0, ask=10.0),
                                        1, DAY, now)[1].startswith("spread"))
        self.assertIn("older", Z.pick_contract(rows(now, t=now - 600),
                                               1, DAY, now)[1])
        self.assertIsNone(Z.pick_contract(rows(now), 1, "2027-04-15", now)[0])
        self.assertIsNone(Z.pick_contract([], 1, DAY, now)[0])
        # no delta on any row (this account tier): no contract, named why,
        # never a model or a guess
        row, why = Z.pick_contract(rows(now, delta=False), 1, DAY, now)
        self.assertIsNone(row)
        self.assertEqual(why, "no delta")

    def test_contracts_for_premium_budget(self):
        from sleeves import milkman_0dte as Z
        self.assertEqual(Z.contracts_for(40.0), 0)
        self.assertEqual(Z.contracts_for(35.0), 1)
        self.assertEqual(Z.contracts_for(4.0), 6)
        self.assertEqual(Z.contracts_for(10.4), 2)


class InertBehaviour(unittest.TestCase):
    def _lane(self):
        return [{"key": "GAP:L|" + DAY, "side": 1}]

    def test_no_probe_record_no_entry_named_reason(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        sleeve, out = _drive(Z, now, {"lane_signals": self._lane(),
                                      "chain_rows": rows(now)})
        self.assertEqual([i for i in out if i.kind == "enter"], [])
        self.assertTrue(sleeve.last_evaluation["inert"].startswith(
            "SPX 0DTE chain not available"))

    def test_probe_unavailable_no_entry(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        sleeve, out = _drive(Z, now, {
            "spx_probe": {"available": False, "underlying": None,
                          "why": "none listed"},
            "lane_signals": self._lane(), "chain_rows": rows(now)})
        self.assertEqual([i for i in out if i.kind == "enter"], [])
        self.assertTrue(sleeve.last_evaluation["inert"].startswith(
            "SPX 0DTE chain not available"))

    def test_never_a_spy_fallback(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        _, out = _drive(Z, now, {"lane_signals": self._lane(),
                                 "chain_rows": rows(now)})
        self.assertTrue(all(not i.symbol.startswith("SPY") for i in out))


class EntryPathFixture(unittest.TestCase):
    """The authored entry path, driven through the named lane_signals
    seam with a delta-carrying fixture chain. In production the seam
    is empty (study unported) and the tier chain carries no delta, so
    this path cannot fire live; both facts are named in PROVENANCE."""

    def _extra(self, now, **kw):
        ex = {"spx_probe": {"available": True, "underlying": "SPXW",
                            "why": None},
              "lane_signals": [{"key": "GAP:L|" + DAY, "side": 1}],
              "chain_rows": rows(now)}
        ex.update(kw)
        return ex

    def test_entry_is_the_quoted_call_at_the_ask(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        sleeve, out = _drive(Z, now, self._extra(now))
        (e,) = [i for i in out if i.kind == "enter"]
        self.assertEqual(e.symbol, occ("C", 5010))
        self.assertEqual(e.qty, 2.0)                    # 2500 // (10.40*100)
        self.assertEqual(e.limit_price, 10.4)           # the quoted ask
        self.assertEqual(e.price_hint, 10.4)
        self.assertEqual(e.position_intent, "buy_to_open")
        st = sleeve.milkman_state
        self.assertEqual(st["open"]["GAP:L|" + DAY]["occ"], e.symbol)

    def test_tier_chain_without_delta_names_the_skip(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 31)
        sleeve, out = _drive(Z, now, self._extra(now, chain_rows=rows(now, delta=False)))
        self.assertEqual([i for i in out if i.kind == "enter"], [])
        self.assertTrue(any("no delta" in x.get("why", "")
                            for x in sleeve.milkman_state["log"]))

    def test_no_entry_in_last_30_minutes(self):
        from sleeves import milkman_0dte as Z
        now = et(15, 35)
        _, out = _drive(Z, now, self._extra(now))
        self.assertEqual([i for i in out if i.kind == "enter"], [])


class StopAndClose(unittest.TestCase):
    def _held_state(self):
        return {"day": DAY, "start_equity": START_EQUITY, "stopped": {},
                "open": {"GAP:L|" + DAY: {"occ": occ("C", 5010), "side": 1,
                                          "qty": 2, "ask": 10.4,
                                          "at": et(9, 31), "session": DAY}},
                "seen": {"GAP:L|" + DAY: "open"}, "log": [], "seq": 0,
                "inert": ""}

    def test_daily_stop_flattens_and_blocks_reentry(self):
        from sleeves import milkman_0dte as Z
        now = et(9, 45)
        held = {occ("C", 5010): 2.0}
        sleeve, out = _drive(Z, now, {"book_pnl": -10000.0,
                                      "chain_rows": rows(now)},
                             slice_state=held, state=self._held_state())
        self.assertEqual(sleeve.milkman_state["stopped"]["pnl"], -10000.0)
        (x,) = [i for i in out if i.kind == "exit"]
        self.assertEqual((x.symbol, x.qty), (occ("C", 5010), 2.0))
        self.assertEqual([i for i in out if i.kind == "enter"], [])
        # -9,999 does NOT trip the stop (boundary as authored)
        sleeve2, out2 = _drive(Z, now, {"book_pnl": -9999.0,
                                        "chain_rows": rows(now)},
                               slice_state=held, state=self._held_state())
        self.assertEqual(sleeve2.milkman_state["stopped"], {})
        self.assertEqual([i for i in out2 if i.kind == "exit"], [])

    def test_hard_exit_before_the_close(self):
        from sleeves import milkman_0dte as Z
        now = et(15, 46, 0)
        held = {occ("C", 5010): 3.0}
        _, out = _drive(Z, now, {"chain_rows": rows(now)},
                        slice_state=held, state=self._held_state())
        (x,) = [i for i in out if i.kind == "exit"]
        self.assertEqual(x.qty, 3.0)
        self.assertIn("hard exit", x.reason)

    def test_signal_exit_sells_the_contract(self):
        from sleeves import milkman_0dte as Z
        now = et(10, 20)
        held = {occ("C", 5010): 2.0}
        sleeve, out = _drive(
            Z, now,
            {"spx_probe": {"available": True, "underlying": "SPXW"},
             "lane_exits": ["GAP:L|" + DAY],
             "chain_rows": rows(now),
             "quotes": {occ("C", 5010): {"bid": 12.0, "ask": 12.4}}},
            slice_state=held, state=self._held_state())
        (x,) = [i for i in out if i.kind == "exit"]
        self.assertEqual(x.price_hint, 12.0)            # the quoted bid
        self.assertNotIn("GAP:L|" + DAY, sleeve.milkman_state["open"])


class ProbeAdapted(unittest.TestCase):
    def test_evaluate_counts_quotes_and_absent_delta(self):
        from desk3.milkman_0dte import spx_probe as SP
        now = et(12, 0, 0)
        contracts = [{"symbol": occ("C", 5000 + 5 * i)} for i in range(12)]
        snaps = {}
        for c in contracts:
            snaps[c["symbol"]] = {"latestQuote": {
                "bp": 10.0, "ap": 10.4,
                "t": datetime.fromtimestamp(now, ET).isoformat()}}
        a = SP.evaluate("SPX", snaps, contracts, now)
        self.assertEqual(a["contracts"], 12)
        self.assertEqual(a["quoted"], 12)
        self.assertEqual(a["fresh"], 12)
        self.assertEqual(a["with_delta"], 0)   # indicative feed: no greeks
        self.assertEqual(a["roots"], {"SPXW": 12})

    def test_availability_roundtrip_and_stale(self):
        from desk3.milkman_0dte import spx_probe as SP
        with tempfile.TemporaryDirectory() as root:
            doc = {"probe": "spx_0dte_chain", "version": SP.PROBE_VERSION,
                   "status": "complete", "available": True,
                   "underlying": "SPXW", "session": DAY, "why": None}
            p = os.path.join(root, SP.PATH)
            os.makedirs(os.path.dirname(p))
            with open(p, "w") as fh:
                json.dump(doc, fh)
            self.assertEqual(SP.availability(root, DAY), ("SPXW", None))
            under, why = SP.availability(root, "2027-04-15")
            self.assertIsNone(under)
            self.assertTrue(why.startswith("SPX 0DTE chain not available"))
            self.assertTrue(SP.done(root, DAY))

    def test_no_record_is_named_not_available(self):
        from desk3.milkman_0dte import spx_probe as SP
        with tempfile.TemporaryDirectory() as root:
            under, why = SP.availability(root, DAY)
            self.assertIsNone(under)
            self.assertIn("has not recorded", why)

    def test_job_outside_rth_records_not_run(self):
        from desk3.milkman_0dte import spx_probe as SP
        with tempfile.TemporaryDirectory() as root:
            info = SP.job(root, env={}, now=et(20, 0, 0))
            self.assertEqual(info.get("status"), "not run")
            doc = SP.read(root)
            self.assertEqual(doc["status"], "incomplete")
            self.assertIsNone(doc["available"])


class RosterWiring(unittest.TestCase):
    def test_config_row_parked_unfed_named(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows_ = cfg["sleeves"] if isinstance(cfg, dict) else cfg
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(rows_), 400)
        (r,) = [x for x in rows_ if x["id"] == "mk_zerodte_spx"]
        self.assertEqual(r["module"], "adapters3.milkman_0dte")
        # UNPARK-REGISTRY-20261114 (owner's all-sleeves-firing
        # order): unparked (was parked with no reason recorded);
        # it now evaluates and reads UNFED on its own named chain
        # input when that product is absent.
        self.assertFalse(r["parked"])
        self.assertEqual(r["params"].get("unparked_on"), "2026-11-14")
        self.assertEqual(r["cadence_s"], 60)
        self.assertEqual(r["session"], "rth")
        self.assertIn("milkman_0dte_chain", r["inputs"])
        self.assertEqual(r["params"]["daily_stop"], -10000.0)
        self.assertEqual(r["params"]["premium_per_trade"], 2500.0)
        self.assertEqual(r["slice"]["capital_usd"], 10000.0)

    def test_adapters3_entrypoint_shape(self):
        import importlib
        m = importlib.import_module("adapters3.milkman_0dte")
        self.assertEqual(m.SLEEVE_ID, "mk_zerodte_spx")
        self.assertIn("milkman_0dte_chain", m.INPUTS)
        self.assertTrue(callable(m.evaluate))


if __name__ == "__main__":
    unittest.main()
