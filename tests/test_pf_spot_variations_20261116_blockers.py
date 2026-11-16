"""PF-SPOT-VARIATIONS-20261116 blockers (desk full audit
escalation 3; owner ruling 2026-11-16 09:22 ET: "Fix them").

Defect: six free_kraken sleeves (free_kraken_ada_basis,
free_kraken_ada_breakdown, free_kraken_ada_crowded,
free_kraken_link_basis, free_kraken_link_breakdown,
free_kraken_link_crowded) are written against PF_ADAUSD /
PF_LINKUSD perpetuals, which are not Alpaca instruments; their
exits exist in code but no position can ever exist. The
registered question covering them is CAND-CTB-SPOT-ADA/LINK.

Cure (this landing): the spot-expression variation of each PF
sleeve as a NEW sleeve beside its parent (variation doctrine:
own id, own falsifier, own grade path — registered in
config/pf_spot_variations_20261116.json), rostered live in
config/sleeves.json (roster 381 -> 387). Signal sources are the
parents' own readings, unchanged (basis series for the basis
pair; the breakdown construction on the served spot 4h tape;
that construction plus the PF funding gate, retained as a
conditioner from the same kraken.funding PF series, for the
crowded pair). The traded instruments are the Alpaca-listed
spot pairs ADA/USD and LINK/USD. Registered expression rule:
Alpaca serves no crypto spot shorting, so the short side is a
named no-trade, never a fabricated short; the basis variations
trade the lawful spot direction (long spot on a perp discount
beyond the parent's 25bps band, exit at the -5bps mirror
normalization or the parent's 16h hold).

The six parents are byte-untouched (file and roster-row sha256
pins below, computed on pre-cure HEAD 8096eed) and keep failing
closed by name at the PF_ seam (the dispatcher pin at the end:
a PF_ADAUSD entry from a PF parent is still intent_recorded,
never submitted).

Fail direction: on the pre-cure tree the variation ids, modules
and registry do not exist, so the roster/registry/behavior
tests fail; the parent pins and the PF seam pin pass on both
trees by design (they pin what the cure must not move).

AMENDMENT 2026-11-16 (MAKE-IT-WORK Decision C,
PF-PAIRED-RV-20261116; owner ruling 2026-11-16 12:46 ET): the
expression of the four short-side variations (ada/link
breakdown + crowded) changed from the named no-trade to the
paired relative-value expression (LONG BTC/USD spot on
entry_ready, 16h hold, spread grading). ONLY the pins in
TestBreakdownExpression and TestCrowdedExpression that pinned
the old named-no-trade behavior are amended below, each with a
dated note; the basis-pair pins, the parent pins and the
PF-seam pin are untouched and still pass. The paired
expression's own behavior is pinned by
tests/test_pf_paired_rv_20261116_blockers.py.
"""
import hashlib
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PARENTS = ["free_kraken_ada_basis", "free_kraken_ada_breakdown",
           "free_kraken_ada_crowded", "free_kraken_link_basis",
           "free_kraken_link_breakdown", "free_kraken_link_crowded"]
VARIATIONS = [p + "_varspot" for p in PARENTS]
CANDIDATE = {"free_kraken_ada_basis_varspot": "CAND-CTB-SPOT-ADA",
             "free_kraken_ada_breakdown_varspot": "CAND-CTB-SPOT-ADA",
             "free_kraken_ada_crowded_varspot": "CAND-CTB-SPOT-ADA",
             "free_kraken_link_basis_varspot": "CAND-CTB-SPOT-LINK",
             "free_kraken_link_breakdown_varspot": "CAND-CTB-SPOT-LINK",
             "free_kraken_link_crowded_varspot": "CAND-CTB-SPOT-LINK"}
MODULES = {"free_kraken_ada_basis_varspot":
           "adapters3.free_kraken_ada_basis_varspot",
           "free_kraken_ada_breakdown_varspot":
           "adapters3.free_kraken_ada_breakdown_varspot",
           "free_kraken_ada_crowded_varspot":
           "adapters3.free_kraken_ada_crowded_varspot",
           "free_kraken_link_basis_varspot":
           "desk3.sleeves.free_kraken_link_basis_varspot",
           "free_kraken_link_breakdown_varspot":
           "desk3.sleeves.free_kraken_link_breakdown_varspot",
           "free_kraken_link_crowded_varspot":
           "desk3.sleeves.free_kraken_link_crowded_varspot"}
# OBV-CLASS-20261116 re-pin (2026-11-16): two pins below were
# re-based because OBV-CLASS-20261116 added own_book_view: true to
# those parents' roster rows (free_kraken_ada_basis,
# free_kraken_link_basis). Verified: each amended row differs from
# its pre-OBV row by exactly that one key.
PARENT_ROW_SHA256 = {
    "free_kraken_ada_basis":
    "90768a9e1587bee56f4b5e65ea71691356c571d5b85ec8d75a836c3df8c63284",
    "free_kraken_ada_breakdown":
    "af647b9af0f74808898da6acb7394417d92f279ba1fcc88bf4ab8eb70d1d670a",
    "free_kraken_ada_crowded":
    "38f89aaaf1a2e95704357d5d27c3f4d936dd39d1cec5e1c1fbc35a93bba22f5d",
    "free_kraken_link_basis":
    "161f7dc6a9a2291536af21237201e1e63226815c56c6c19632b078462d7d8e47",
    "free_kraken_link_breakdown":
    "912ab4794252b82b32d097fff4926ff121b7be102832c19a92cdafc4a29b0828",
    "free_kraken_link_crowded":
    "9a3f1fa67f996f9fdc6c5fdd345538d89a4e37172ba9797de9f515542a6f2b13"}
PARENT_FILE_SHA256 = {
    "sleeves/free_kraken_ada_basis.py":
    "bbbda755fb4cb11f55a7eb02da5e3a06573c6c79f02424aef95fca198fc7bf18",
    "sleeves/free_kraken_ada_breakdown.py":
    "a244bf67fa547e4424347e8990fe3ec2b3fea38b8a00b59d9dc1604a31126c4f",
    # Re-pinned TOTAL-AUDIT-PIN-REBASE-20261116: the parent file
    # TOTAL-AUDIT-PIN-REBASE-20261116 (6): a tranche-4
    # annotation briefly changed these bytes and this pin
    # followed it; the annotation was removed the same day
    # (the file is port byte-pinned and its provenance lives
    # in constants-ledger-20261116.md), restoring this pin.
    "sleeves/free_kraken_ada_crowded.py":
    "85b5ebea605d7182cab6ec8b55425a749e2464b6f82ce2387373f4e284b2f777",
    "adapters/free_kraken_ada_basis.py":
    "ac823e6c5b2843bbd60bc84c8afc6dce0a41b1671bc8a95487e9174d09bc6867",
    "adapters/free_kraken_ada_breakdown.py":
    "f64a45d7e7bac91253f189fecb0d6b1967d5566fa8333b5260470366a92d5b23",
    "adapters/free_kraken_ada_crowded.py":
    "348a266a399b7cebcaecd947348ecdb2dc3148ca6fdc0eb08a9e32e573e71538",
    "adapters3/free_kraken_ada_basis.py":
    "005a626628b42e1b5c89cea4e9b38c76a0fc2592f7278b3fc1c953cb270f4103",
    "adapters3/free_kraken_ada_breakdown.py":
    "774eb2ccf27a76e378e6dd07d543a9367f47f8a8f85ee8d7e8ca5b97fe037c0e",
    "adapters3/free_kraken_ada_crowded.py":
    "110693333739b7a798b5664479e52082a066d22a1d54bddd183356163347a7b8",
    "desk3/strategies/free_kraken_link_basis.py":
    "66d6307fa98e85eb1cb21f1cdf60be4a10b99b42b618dfcb28427d7d06baf021",
    "desk3/strategies/free_kraken_link_breakdown.py":
    "be427ed66b7b8534f015d5f2e1e3673c4a820771cd6da80d1fbd84ccb4facef9",
    # TOTAL-AUDIT-PIN-REBASE-20261116 (6): same restoration
    # as the ada_crowded entry above.
    "desk3/strategies/free_kraken_link_crowded.py":
    "c9b22591486a66c0ee2ea09ce22d95bc9450f08a06ba2d23f9a12c2ab09cbf1f",
    "desk3/sleeves/free_kraken_link_basis.py":
    "92b02bc64327756d502ca94641edaecb5c81372e05830891109d4ddaf92ff303",
    "desk3/sleeves/free_kraken_link_breakdown.py":
    "41c2f24f96f95e75ed6b453cda4edb3d411068074852830a54278706b99e279d",
    "desk3/sleeves/free_kraken_link_crowded.py":
    "709b83aa0c378080b7dec7ed42a4d3b7d8e22eb990ccd2f137fd9b3110148d23"}


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _rows():
    return json.load(open(os.path.join(
        ROOT, "config", "sleeves.json")))["sleeves"]


NOW = datetime(2026, 11, 16, 16, 0, tzinfo=timezone.utc)


def _series(spot_close, perp_close, n=3):
    """Aligned completed pairs ending 4h before NOW."""
    out = []
    t0 = NOW - timedelta(hours=4 * n)
    for i in range(n):
        out.append({"t": (t0 + timedelta(hours=4 * i)).timestamp(),
                    "spot_close": spot_close,
                    "perp_close": perp_close})
    return out


def _basis_extra(spot_close, perp_close):
    return {"basis": {"aligned": 3, "required": 3,
                      "series": _series(spot_close, perp_close)},
            "spot_reference": {
                "price": spot_close,
                "bar_t": (NOW - timedelta(hours=4)).isoformat()}}


def _ctx(extra, now=NOW):
    from desk3.contract import Context
    return Context(now=now.timestamp(), session="2026-11-16",
                   equity=10000.0, extra=extra)


def _breakdown_bars(symbol, signal_close=0.9, n=30):
    """Spot bars whose newest due signal bar closes below the
    prior 20 lows (all 1.0): a textbook parent breakdown."""
    bars = []
    t0 = NOW - timedelta(hours=4 * (n + 2))
    for i in range(n):
        close = 1.0 if i < n - 1 else signal_close
        bars.append({"t": (t0 + timedelta(hours=4 * i)).timestamp(),
                     "o": 1.0, "h": 1.01, "l": 0.99, "c": close,
                     "v": 10.0})
    return {symbol: bars}


def _funding(now=NOW, latest=0.001):
    """40 hourly prints in the last 90 days; the latest is the
    maximum, above zero and the 75th percentile, and fresh."""
    out = []
    for i in range(40):
        ts = now - timedelta(hours=40 - i)
        out.append({"timestamp": ts.isoformat(),
                    "fundingRate": latest if i == 39 else 0.0001})
    return out


class TestRosterAndRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = _rows()
        cls.by_id = {}
        for r in cls.rows:
            cls.by_id.setdefault(r["id"], []).append(r)
        cls.reg = json.load(open(os.path.join(
            ROOT, "config", "pf_spot_variations_20261116.json")))

    def test_roster_387_and_variations_present_exactly_once(self):
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(self.rows), 400)
        for vid in VARIATIONS:
            self.assertEqual(len(self.by_id.get(vid, [])), 1, vid)

    def test_variation_rows_are_parent_copies_in_the_named_fields(self):
        for pid, vid in zip(PARENTS, VARIATIONS):
            a = dict(self.by_id[pid][0])
            b = dict(self.by_id[vid][0])
            diff = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
            self.assertTrue(diff <= {"id", "module", "inputs", "params"},
                            (vid, diff))
            self.assertEqual(b["module"], MODULES[vid], vid)
            self.assertFalse(b["parked"], vid)
            self.assertEqual(b["slice"], a["slice"], vid)
            stamp = (b.get("params") or {}).get("parked_reason") or ""
            self.assertIn("PF-SPOT-VARIATIONS-20261116", stamp, vid)
            self.assertIn(CANDIDATE[vid], stamp, vid)
            mod = importlib.import_module(b["module"])
            self.assertEqual(mod.SLEEVE_ID, vid, vid)

    def test_parents_byte_untouched(self):
        for pid, want in PARENT_ROW_SHA256.items():
            row = self.by_id[pid][0]
            self.assertEqual(_sha(json.dumps(row, sort_keys=True).encode()),
                             want, pid)
        for path, want in PARENT_FILE_SHA256.items():
            with open(os.path.join(ROOT, path), "rb") as fh:
                self.assertEqual(_sha(fh.read()), want, path)

    def test_registry_entries_carry_falsifier_and_grade_path(self):
        by_id = {v["id"]: v for v in self.reg["variations"]}
        self.assertEqual(set(by_id), set(VARIATIONS))
        for vid in VARIATIONS:
            v = by_id[vid]
            self.assertEqual(v["parent"], vid[:-len("_varspot")], vid)
            self.assertEqual(v["candidate"], CANDIDATE[vid], vid)
            self.assertIn("40 registered signal events", v["falsifier"], vid)
            self.assertIn("killed, not loosened",
                          v["falsifier"].lower(), vid)
            self.assertIn("B5", v["grade_path"], vid)
            self.assertIn("retires the variation", v["kill_rule"], vid)
            self.assertIn("PF-SPOT-VARIATIONS-20261116", v["status"], vid)


class TestBasisExpression(unittest.TestCase):
    def _check(self, strat_mod, symbol):
        # Perp discount beyond the band -> LONG spot entry.
        extra = _basis_extra(1.00, 0.997)  # basis -30bps
        intents = strat_mod.signal({}, {}, _ctx(extra))
        self.assertEqual(len(intents), 1, symbol)
        it = intents[0]
        self.assertEqual((it.kind, it.symbol), ("enter", symbol))
        self.assertEqual(it.qty_hint, 1)
        self.assertIn("buy_to_open", it.reason)
        # Perp premium (the parent's own entry side) -> named
        # no-trade, no intent, never a fabricated short.
        dec = strat_mod.spot_decision(_series(1.00, 1.003),
                                      _basis_extra(1.00, 1.003), NOW)
        self.assertEqual(dec["status"], "named_no_trade_premium_side")
        self.assertEqual(
            strat_mod.signal({}, {}, _ctx(_basis_extra(1.00, 1.003))), [])
        # Inside the band -> awaiting, no intent.
        dec = strat_mod.spot_decision(_series(1.00, 1.001),
                                      _basis_extra(1.00, 1.001), NOW)
        self.assertEqual(dec["status"], "QUALIFIED/AWAITING SIGNAL")
        # Long open + basis normalized (>= -5bps) -> exit.
        extra = _basis_extra(1.00, 0.9996)  # basis -4bps
        extra["sleeve_state"] = {symbol: {
            "qty": 1, "entry_due_at": (NOW - timedelta(hours=1)).isoformat()}}
        intents = strat_mod.signal({}, {}, _ctx(extra))
        self.assertEqual(len(intents), 1, symbol)
        self.assertEqual((intents[0].kind, intents[0].symbol),
                         ("exit", symbol))
        self.assertIn("sell_to_close", intents[0].reason)
        # Long open + discount still beyond exit + hold elapsed -> exit.
        extra = _basis_extra(1.00, 0.997)
        extra["sleeve_state"] = {symbol: {
            "qty": 1,
            "entry_due_at": (NOW - timedelta(hours=17)).isoformat()}}
        intents = strat_mod.signal({}, {}, _ctx(extra))
        self.assertEqual(len(intents), 1, symbol)
        self.assertEqual(intents[0].kind, "exit")
        # Long open + discount beyond exit + hold not elapsed -> hold.
        extra = _basis_extra(1.00, 0.997)
        extra["sleeve_state"] = {symbol: {
            "qty": 1, "entry_due_at": (NOW - timedelta(hours=1)).isoformat()}}
        self.assertEqual(strat_mod.signal({}, {}, _ctx(extra)), [])
        # Stale spot reference -> no entry even on a discount.
        extra = _basis_extra(1.00, 0.997)
        extra["spot_reference"] = {
            "price": 1.0, "bar_t": (NOW - timedelta(hours=12)).isoformat()}
        self.assertEqual(strat_mod.signal({}, {}, _ctx(extra)), [])

    def test_ada_basis_varspot(self):
        from sleeves import free_kraken_ada_basis_varspot as m
        self._check(m, "ADA/USD")

    def test_link_basis_varspot(self):
        from desk3.strategies import free_kraken_link_basis_varspot as m
        self._check(m, "LINK/USD")


class TestBreakdownExpression(unittest.TestCase):
    def _check(self, strat_mod, parent_mod, symbol):
        bars = _breakdown_bars(symbol)
        rows = parent_mod.normalize(bars[symbol])
        # The parent's own decision on the same spot rows is
        # entry_ready: the construction is the parent's, on spot.
        self.assertEqual(
            parent_mod.breakdown_decision(rows, NOW)["status"],
            "entry_ready")
        dec = strat_mod.spot_decision(rows, NOW)
        # AMENDED PIN 2026-11-16 (PF-PAIRED-RV-20261116, MAKE-IT-WORK
        # Decision C): entry_ready maps to the paired relative-value
        # expression, not the old named no-trade; the parent's event
        # id is still carried unchanged.
        self.assertEqual(dec["status"], "paired_rv_entry_ready")
        self.assertEqual(dec["signal_event_id"],
                         parent_mod.breakdown_decision(
                             rows, NOW, instrument=symbol)["signal_event_id"])
        # No fabricated short is ever emitted: with no BTC/USD
        # anchor tape served, the paired leg fails closed with a
        # named abstention and zero intents.
        extra = {"view": symbol}
        self.assertEqual(strat_mod.signal(bars, {}, _ctx(extra)), [])
        paired = extra.get("enhance_paired") or []
        self.assertEqual(len(paired), 1)
        self.assertEqual(paired[0]["treatment_decision"],
                         "named_abstention_anchor_stale")
        abst = extra.get("paired_rv_abstentions") or []
        self.assertEqual(len(abst), 1)
        self.assertEqual(abst[0]["status"],
                         "named_abstention_anchor_stale")
        # No breakdown on the tape -> no signal event.
        flat = {symbol: [dict(b, c=1.0) for b in bars[symbol]]}
        dec = strat_mod.spot_decision(parent_mod.normalize(flat[symbol]),
                                      NOW)
        self.assertNotEqual(dec["status"], "paired_rv_entry_ready")

    def test_ada_breakdown_varspot(self):
        from sleeves import free_kraken_ada_breakdown_varspot as m
        from sleeves import free_kraken_ada_breakdown as p
        self._check(m, p, "ADA/USD")

    def test_link_breakdown_varspot(self):
        from desk3.strategies import free_kraken_link_breakdown_varspot as m
        from desk3.strategies import free_kraken_link_breakdown as p
        self._check(m, p, "LINK/USD")


class TestCrowdedExpression(unittest.TestCase):
    def _check(self, strat_mod, parent_mod, symbol):
        bars = _breakdown_bars(symbol)
        rows = parent_mod.normalize(bars[symbol])
        rates = _funding()
        # Parent decision on spot rows + PF funding: entry_ready.
        self.assertEqual(
            parent_mod.crowded_decision(rows, rates, NOW)["status"],
            "entry_ready")
        dec = strat_mod.spot_decision(rows, rates, NOW)
        # AMENDED PIN 2026-11-16 (PF-PAIRED-RV-20261116, MAKE-IT-WORK
        # Decision C): entry_ready maps to the paired relative-value
        # expression, not the old named no-trade.
        self.assertEqual(dec["status"], "paired_rv_entry_ready")
        extra = {"funding_rates": rates}
        # No BTC/USD anchor tape served -> named abstention, zero
        # intents (never a fabricated short).
        self.assertEqual(strat_mod.signal(bars, {}, _ctx(extra)), [])
        abst = extra.get("paired_rv_abstentions") or []
        self.assertEqual(len(abst), 1)
        self.assertEqual(abst[0]["status"],
                         "named_abstention_anchor_stale")
        # Funding gate fails (latest print not crowded) -> the
        # parent's gate binds the variation identically.
        cold = _funding(latest=0.0001)
        dec = strat_mod.spot_decision(rows, cold, NOW)
        self.assertEqual(dec["status"], "QUALIFIED/AWAITING SIGNAL")
        # Stale funding -> the parent's freshness refusal binds.
        stale = [{"timestamp": (NOW - timedelta(hours=5)).isoformat(),
                  "fundingRate": 0.001}] * 40
        dec = strat_mod.spot_decision(rows, stale, NOW)
        self.assertEqual(dec["status"], "REFUSED_STALE_FUNDING")

    def test_ada_crowded_varspot(self):
        from sleeves import free_kraken_ada_crowded_varspot as m
        from sleeves import free_kraken_ada_crowded as p
        self._check(m, p, "ADA/USD")

    def test_link_crowded_varspot(self):
        from desk3.strategies import free_kraken_link_crowded_varspot as m
        from desk3.strategies import free_kraken_link_crowded as p
        self._check(m, p, "LINK/USD")


class TestAdapterPaths(unittest.TestCase):
    """The rostered modules evaluate through the worker's path on
    a synthetic snapshot view (basis discount -> one spot entry
    intent on the listed symbol; breakdown tape -> no intents)."""

    def _view(self, symbol, basis_entry, spot_close=1.0):
        # A fresh spot tape: 30 flat 4h bars, the newest opened
        # 4h before NOW (inside the variation's freshness gate).
        tape = []
        t0 = NOW - timedelta(hours=4 * 30)
        for i in range(30):
            t = t0 + timedelta(hours=4 * i)
            tape.append({"t": t.isoformat(), "o": spot_close,
                         "h": spot_close, "l": spot_close,
                         "c": spot_close, "v": 10.0})
        view = {"now": NOW.isoformat(),
                "bars": {f"{symbol}|4Hour": tape,
                         f"{symbol}|240Min": tape},
                "positions": [], "extra": {},
                "kraken_inputs": {"sleeves": {basis_entry[0]: basis_entry[1]}},
                "kraken": {"sleeves": {basis_entry[0]: basis_entry[1]}},
                "kraken.funding": {}}
        return view

    def test_link_basis_adapter_emits_spot_entry(self):
        mod = importlib.import_module(MODULES["free_kraken_link_basis_varspot"])
        entry = ("free_kraken_link_basis",
                 {"basis": {"aligned": 3, "required": 3,
                            "series": _series(9.0, 8.973)},
                  "quote": {"bid": 8.97, "ask": 8.98}})
        view = self._view("LINK/USD", entry, spot_close=9.0)
        out = mod.evaluate(view, {"sleeve_id": mod.SLEEVE_ID})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "LINK/USD")
        self.assertEqual(entries[0]["side"], "buy")

    def test_ada_basis_adapter_emits_spot_entry(self):
        mod = importlib.import_module(MODULES["free_kraken_ada_basis_varspot"])
        entry = ("free_kraken_ada_basis",
                 {"basis": {"aligned": 3, "required": 3,
                            "series": _series(1.0, 0.997)},
                  "quote": {"bid": 0.99, "ask": 1.0}})
        view = self._view("ADA/USD", entry)
        out = mod.evaluate(view, {"sleeve_id": mod.SLEEVE_ID,
                                  "state_dir": tempfile.mkdtemp()})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "ADA/USD")
        self.assertEqual(entries[0]["side"], "buy")


class TestPfSeamUnchanged(unittest.TestCase):
    def test_pf_entry_still_recorded_never_submitted(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher

        class LiveBookFake(FakeBroker):
            live_book = True

        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"PF_ADAUSD": 100.0})
        d = Dispatcher(tmp, broker,
                       slices={"free_kraken_ada_breakdown":
                               {"capital_usd": 10000, "cash_usd": 10000}},
                       price_lookup=lambda s: 100.0)
        r = d.process_intent(
            {"intent_id": "pf1", "kind": "entry", "symbol": "PF_ADAUSD",
             "side": "sell", "qty": 1, "order_type": "market",
             "time_in_force": "gtc", "price_hint": 100.0},
            "free_kraken_ada_breakdown")
        self.assertEqual(r["status"], "recorded", r)
        self.assertEqual(broker.submit_count, 0)


if __name__ == "__main__":
    unittest.main()
