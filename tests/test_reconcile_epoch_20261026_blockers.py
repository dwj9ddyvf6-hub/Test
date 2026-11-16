"""Blockers: RECONCILE-EPOCH-20261026 — reconcile's journal-derived
truth was not scoped to the capital epoch, so the account switch
(Stage C, epoch 2026-10-26T20:14:30Z, new paper account PA36X7WU3)
never actually reset it.

Pre-cure defect: desk3/reconcile.py journal_derived() summed EVERY
'fill' event ever written to state/dispatcher.jsonl (5,829 historical
fills from the old account, netting to 39 nonzero symbols across 23
sleeves) with no epoch/account/timestamp scoping. Stage C recorded
baseline {positions: {}} for the new empty book, but expected =
baseline + the ENTIRE journal, so every cycle produced 39
position_qty discrepancies, halted 23 sleeves, and the Dispatcher
rejected every entry from them as reconcile_halt. Cash only looked
consistent because the recorded cash_offset (-1765114.11) encoded
the pre-epoch journal spend.

Cure (at the source, desk3/reconcile.py only): journal_derived()
loads state/capital_epoch.json's epoch_start_utc (the file's first
reader — Stage C wrote it write-only) and counts ONLY fills with
ts >= epoch_start, for positions AND spend; a fill with no ts (or an
unparseable ts) counts as pre-epoch and is excluded. The
record_baseline branch uses the same epoch-scoped spend, so its
cash_offset is re-derived against the epoch in the same pass. A
state dir with NO capital_epoch.json keeps the legacy unscoped
behavior exactly (day-one / fixture paths preserved). Tolerances
QTY_TOL / CASH_TOL_USD and the guard's halt semantics are untouched:
a genuine post-epoch mismatch still halts exactly its sleeve, and a
post-epoch cash mismatch still sets cash_halt.

Fail direction: on the pre-cure code (a) fails with position_qty
discrepancies + halted sleeves from pre-epoch fills, and (d) fails
with cash_offset -1765114.11 instead of -1707192.00; the guard pins
(b), (c), the legacy-fallback pin (e) and the saty_sol pin (f) pass
both before and after, as designed. See BUGLOG_2026-10-26.md.
"""
import hashlib, json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

EPOCH = "2026-10-26T20:14:30.681985+00:00"
PRE = "2026-10-25T02:37:24.700418+00:00"   # before the epoch
POST = "2026-10-26T21:00:00+00:00"        # after the epoch


def _state(tmp, with_epoch=True):
    state = os.path.join(tmp, "state")
    os.makedirs(state, exist_ok=True)
    if with_epoch:
        with open(os.path.join(state, "capital_epoch.json"), "w") as fh:
            json.dump({"epoch_start_utc": EPOCH, "account": "PA36X7WU3",
                       "start_equity": 1000000, "ts": EPOCH,
                       "reason": "account_switch"}, fh)
    return state


def _fill(state, sleeve, symbol, side, qty, price, ts="__pre__"):
    from desk3.journal import append_line
    row = {"event": "fill", "intent_id": f"{sleeve}-x", "sleeve": sleeve,
           "client_order_id": f"v3-{sleeve}-x", "symbol": symbol,
           "side": side, "qty": qty, "price": price,
           "position_intent": None}
    if ts == "__pre__":
        row["ts"] = PRE
    elif ts is not None:
        row["ts"] = ts
    append_line(os.path.join(state, "dispatcher.jsonl"), row)


class TestEpochScoping(unittest.TestCase):
    def test_a_pre_epoch_fills_do_not_halt(self):
        from desk3.reconcile import journal_derived, reconcile
        tmp = tempfile.mkdtemp()
        state = _state(tmp)
        # Pre-epoch fills netting nonzero (the live failure shape),
        # incl. one fill with NO ts (must count as pre-epoch).
        _fill(state, "s_old", "AAA", "buy", 100, 10.0)
        _fill(state, "s_old", "BBB", "buy", 5, 2.0, ts=None)
        _fill(state, "s_old2", "CCC", "sell", 3, 1.0)
        positions, spend = journal_derived(
            os.path.join(state, "dispatcher.jsonl"))
        self.assertEqual(positions, {})
        self.assertEqual(spend, {})
        caps = {"s_old": 20000.0, "s_old2": 31000.0}
        rep = reconcile(state, {}, broker_cash=50000.0,
                        slice_capital=caps, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED", rep)
        rep = reconcile(state, {}, broker_cash=50000.0,
                        slice_capital=caps)
        self.assertTrue(rep["ok"], rep)
        self.assertEqual(rep["status"], "OK")
        self.assertEqual(rep["discrepancies"], [])
        self.assertEqual(rep["halted_sleeves"], [])
        self.assertFalse(rep["cash_halt"])

    def test_b_post_epoch_mismatch_still_halts_exactly_that_sleeve(self):
        from desk3.reconcile import reconcile
        tmp = tempfile.mkdtemp()
        state = _state(tmp)
        caps = {"s_new": 10000.0, "s_other": 10000.0}
        rep = reconcile(state, {}, broker_cash=20000.0,
                        slice_capital=caps, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED", rep)
        _fill(state, "s_new", "QQQ", "buy", 7, 100.0, ts=POST)
        # Broker agrees with the post-epoch journal: clean.
        rep = reconcile(state, {"QQQ": 7.0}, broker_cash=19300.0,
                        slice_capital=caps)
        self.assertTrue(rep["ok"], rep)
        # Broker disagrees: exactly s_new halts (guard not weakened).
        rep = reconcile(state, {}, broker_cash=19300.0,
                        slice_capital=caps)
        self.assertFalse(rep["ok"], rep)
        self.assertEqual(rep["halted_sleeves"], ["s_new"])
        self.assertEqual(rep["discrepancies"][0]["kind"], "position_qty")
        self.assertEqual(rep["discrepancies"][0]["symbol"], "QQQ")
        self.assertEqual(rep["discrepancies"][0]["expected_qty"], 7.0)

    def test_c_post_epoch_cash_mismatch_still_sets_cash_halt(self):
        from desk3.reconcile import reconcile
        tmp = tempfile.mkdtemp()
        state = _state(tmp)
        caps = {"s_new": 10000.0}
        reconcile(state, {}, broker_cash=10000.0, slice_capital=caps,
                  record_baseline=True)
        _fill(state, "s_new", "QQQ", "buy", 1, 100.0, ts=POST)
        # Positions agree; cash is $900 short of the expected $9900.
        rep = reconcile(state, {"QQQ": 1.0}, broker_cash=9000.0,
                        slice_capital=caps)
        self.assertFalse(rep["ok"], rep)
        self.assertTrue(rep["cash_halt"])
        self.assertEqual(rep["discrepancies"][0]["kind"], "cash")
        self.assertEqual(rep["discrepancies"][0]["expected_cash_usd"],
                         9900.0)

    def test_d_record_baseline_at_epoch_rederives_cash_offset(self):
        from desk3.reconcile import reconcile
        tmp = tempfile.mkdtemp()
        state = _state(tmp)
        # Pre-epoch NET spend of exactly -$57,922.11 (the live
        # journal's signed total): under the epoch it must NOT
        # enter the offset formula.
        _fill(state, "s_old", "OLD", "sell", 1, 57922.11)
        rep = reconcile(state, {}, broker_cash=1000000.0,
                        slice_capital={"a": 2707192.0},
                        record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED", rep)
        self.assertEqual(rep["baseline"]["positions"], {})
        self.assertAlmostEqual(rep["baseline"]["cash_offset_usd"],
                               -1707192.00, places=6)

    def test_e_no_epoch_file_preserves_legacy_unscoped_behavior(self):
        from desk3.reconcile import reconcile
        tmp = tempfile.mkdtemp()
        state = _state(tmp, with_epoch=False)
        _fill(state, "s_a", "AAA", "buy", 4, 10.0)
        rep = reconcile(state, {}, slice_capital={"s_a": 1000.0})
        self.assertFalse(rep["ok"], rep)
        self.assertEqual(rep["halted_sleeves"], ["s_a"])


class TestRails(unittest.TestCase):
    def test_f_saty_sol_byte_identical(self):
        path = os.path.join(ROOT, "sleeves", "saty_sol.py")
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(
            digest,
            "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc")


if __name__ == "__main__":
    unittest.main()
