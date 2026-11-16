"""EXIT-STORM-CURE-20261116 blockers (Mon 2026-11-16 total audit,
EXIT-STORM-ROOT-20261116): beatendown and confluence emitted a
perpetual phantom 13-week BTC exit because their config rows
carried no own_book_view, so cycle.py served them the AGGREGATE
broker book (shape {symbol, qty, avg_price}, no opened_at); the
adapters converted the aggregate BTC/USD lot — a lot neither
sleeve ever bought — into sleeve state with entry_date=None, and
the frozen sleeve law (missing exit_due_date = DUE) fired the
time exit every cycle. In its filling phase the same phantom
exits left phantom derived positions on both sleeves' journal
books (positions built only from exit fills, on symbols the
sleeve never entered).

The cure, pinned here:
* config: both rows carry own_book_view (the CR-S3 cure shape,
  aster_etf_leader1_c098 precedent), so each sleeve evaluates
  against its own journal-derived book and the aggregate-only
  snapshot position is never served to it;
* disposition: desk3.exit_storm_disposition traces each derived
  position per symbol (entry fills absent, exit fills present =
  phantom; any genuine entry fill = untouched) and appends
  phantom_disposition correction rows carrying the cure id and
  every phantom fill's intent id; journal_derived /
  journal_open_costs apply them as a position-only TRANSFER to
  the named holder book, so the two sleeves read clean while the
  aggregate derived position and every spend figure — the
  figures reconcile compares against the broker — are unchanged;
* fixture drive: an aggregate-only snapshot position with no
  opened_at produces exactly the phantom time exit when served
  the aggregate book (the pre-cure serving) and NO time-exit
  intent when served through the cured path (config flag ->
  cycle own_book_positions -> worker positions_override).

The frozen sleeves (sleeves/beatendown.py, sleeves/confluence.py)
and the adapters' pinned port glue are untouched; the stuck BTC
order is untouched; no signal, sizing, stop or threshold changes.
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SATY_SOL_PIN = "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc"
AGGREGATE_BTC = {"symbol": "BTC/USD", "qty": 0.132675707,
                 "avg_price": 76000.0}  # no opened_at: the storm shape


def _config_rows():
    rows = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
    if isinstance(rows, dict):
        rows = rows.get("sleeves") or rows.get("rows") or []
    return {r["id"]: r for r in rows}


def _fill(sid, sym, side, intent, qty, price, iid, ts):
    return {"event": "fill", "sleeve": sid, "symbol": sym,
            "side": side, "position_intent": intent, "qty": qty,
            "price": price, "intent_id": iid, "ts": ts}


def _write_journal(root, rows):
    path = os.path.join(root, "dispatcher.jsonl")
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return path


def _bars():
    base = datetime(2026, 11, 10, tzinfo=timezone.utc)
    rows = [{"t": (base + timedelta(days=i)).isoformat(),
             "o": 76000.0, "h": 76100.0, "l": 75900.0,
             "c": 76050.0, "v": 100.0} for i in range(5)]
    return {"BTC/USD|1Day": rows}


def _serve_and_evaluate(sid, djournal_path, tmp):
    """The cycle+worker serving path, driven from the config row:
    flagged sleeves get their own journal-derived book as a
    positions_override; unflagged sleeves get the raw snapshot
    (the aggregate broker book) itself."""
    from desk3.cycle import own_book_positions
    from desk3.worker import _view_for_task
    import importlib
    row = _config_rows()[sid]
    data = {"now": "2026-11-16T16:00:00+00:00", "bars": _bars(),
            "positions": [dict(AGGREGATE_BTC)],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}}
    task = {}
    if row.get("own_book_view"):
        own = own_book_positions({sid: {"own_book_view": True}},
                                 djournal_path)
        task["positions_override"] = own.get(sid, [])
    view = _view_for_task(data, task)
    mod = importlib.import_module(f"adapters3.{sid}")
    return mod.evaluate(view, {"state_dir": tmp,
                               "now": "2026-11-16T16:00:00+00:00"})


class TestConfigOwnBookView(unittest.TestCase):
    def test_both_rows_carry_own_book_view(self):
        rows = _config_rows()
        for sid in ("beatendown", "confluence"):
            self.assertTrue(rows[sid].get("own_book_view"), sid)


class TestPhantomTrace(unittest.TestCase):
    def _rows(self):
        return [
            # phantom: exit fills only, never entered
            _fill("beatendown", "BTC/USD", "sell", "sell_to_close",
                  1.0, 77000.0, "bd-btc-1", "2026-11-03T13:00:00Z"),
            _fill("beatendown", "BTC/USD", "sell", "sell_to_close",
                  0.5, 78000.0, "bd-btc-2", "2026-11-04T13:00:00Z"),
            # genuine short: entry fill present (mixed exits stay)
            _fill("beatendown", "TSLA", "sell", "sell_to_open",
                  10.0, 200.0, "bd-tsla-open", "2026-10-27T13:00:00Z"),
            _fill("beatendown", "TSLA", "sell", "sell_to_close",
                  4.0, 210.0, "bd-tsla-x", "2026-11-04T13:00:00Z"),
            # genuine long, still open
            _fill("confluence", "ARM", "buy", "buy_to_open",
                  3.0, 100.0, "cf-arm-open", "2026-10-27T13:00:00Z"),
            # phantom on confluence too
            _fill("confluence", "BTC/USD", "sell", "sell_to_close",
                  2.0, 77000.0, "cf-btc-1", "2026-11-03T13:00:00Z"),
        ]

    def test_census_proves_trace_per_position(self):
        from desk3.exit_storm_disposition import phantom_census
        census = phantom_census(self._rows(), epoch_start=None)
        self.assertEqual(sorted(census), ["beatendown", "confluence"])
        btc = census["beatendown"]["BTC/USD"]
        self.assertEqual(btc["derived_qty"], -1.5)
        self.assertEqual(btc["offset_qty"], 1.5)
        self.assertEqual(btc["phantom_intent_ids"],
                         ["bd-btc-1", "bd-btc-2"])
        self.assertEqual(btc["entry_intents"], [])
        self.assertEqual(census["confluence"]["BTC/USD"]
                         ["phantom_intent_ids"], ["cf-btc-1"])

    def test_genuine_entry_positions_are_not_phantom(self):
        from desk3.exit_storm_disposition import phantom_census
        census = phantom_census(self._rows(), epoch_start=None)
        self.assertNotIn("TSLA", census["beatendown"])
        self.assertNotIn("ARM", census.get("confluence", {}))

    def test_disposition_rows_carry_provenance(self):
        from desk3.exit_storm_disposition import (
            CURE_ID, HOLDER_SLEEVE, build_disposition_rows,
            phantom_census)
        rows = build_disposition_rows(
            phantom_census(self._rows(), epoch_start=None),
            ts="2026-11-16T17:00:00+00:00")
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertEqual(r["event"], "phantom_disposition")
            self.assertEqual(r["cure_id"], CURE_ID)
            self.assertEqual(r["correction"], CURE_ID)
            self.assertEqual(r["holder_sleeve"], HOLDER_SLEEVE)
            self.assertTrue(r["phantom_intent_ids"])


class TestDispositionDerivation(unittest.TestCase):
    def _journal(self, root):
        rows = TestPhantomTrace()._rows()
        return _write_journal(root, rows)

    def test_derived_books_clean_aggregate_and_spend_unchanged(self):
        from desk3.exit_storm_disposition import (
            HOLDER_SLEEVE, apply_disposition)
        from desk3.reconcile import journal_derived
        root = tempfile.mkdtemp()
        path = self._journal(root)
        before_pos, before_spend = journal_derived(path)
        self.assertEqual(before_pos["beatendown"]["BTC/USD"], -1.5)
        census, appended = apply_disposition(
            path, ts="2026-11-16T17:00:00+00:00")
        self.assertEqual(len(appended), 2)
        after_pos, after_spend = journal_derived(path)
        # both sleeves read clean of phantom rows
        self.assertNotIn("BTC/USD", after_pos.get("beatendown", {}))
        self.assertNotIn("BTC/USD", after_pos.get("confluence", {}))
        # genuine positions untouched
        self.assertEqual(after_pos["beatendown"]["TSLA"], -14.0)
        self.assertEqual(after_pos["confluence"]["ARM"], 3.0)
        # the phantom book sits on the named holder, identical qty
        self.assertEqual(after_pos[HOLDER_SLEEVE]["BTC/USD"], -3.5)
        # aggregate per-symbol totals unchanged (reconcile truth)
        for sym in ("BTC/USD", "TSLA", "ARM"):
            tot_b = sum(b.get(sym, 0.0) for b in before_pos.values())
            tot_a = sum(b.get(sym, 0.0) for b in after_pos.values())
            self.assertEqual(tot_a, tot_b, sym)
        # spend untouched: the phantom fills really moved cash
        self.assertEqual(after_spend, before_spend)

    def test_open_costs_follow_the_transfer(self):
        from desk3.exit_storm_disposition import (
            HOLDER_SLEEVE, apply_disposition)
        from desk3.reconcile import journal_open_costs
        root = tempfile.mkdtemp()
        path = self._journal(root)
        apply_disposition(path, ts="2026-11-16T17:00:00+00:00")
        costs = journal_open_costs(path)
        self.assertNotIn("BTC/USD", costs.get("beatendown", {}))
        self.assertNotIn("BTC/USD", costs.get("confluence", {}))
        self.assertIn("BTC/USD", costs[HOLDER_SLEEVE])
        self.assertEqual(costs["beatendown"]["TSLA"],
                         costs["beatendown"]["TSLA"])

    def test_disposition_is_idempotent(self):
        from desk3.exit_storm_disposition import apply_disposition
        root = tempfile.mkdtemp()
        path = self._journal(root)
        apply_disposition(path, ts="2026-11-16T17:00:00+00:00")
        _census, again = apply_disposition(
            path, ts="2026-11-16T17:05:00+00:00")
        self.assertEqual(again, [])


class TestFixtureDrive(unittest.TestCase):
    def test_aggregate_serving_produces_exactly_the_phantom_exit(self):
        # The pre-cure serving, driven directly: the aggregate-only
        # snapshot position with no opened_at IS the storm input.
        import importlib
        for sid in ("beatendown", "confluence"):
            tmp = tempfile.mkdtemp()
            mod = importlib.import_module(f"adapters3.{sid}")
            view = {"now": "2026-11-16T16:00:00+00:00",
                    "bars": _bars(),
                    "positions": [dict(AGGREGATE_BTC)],
                    "slice": {"capital_usd": 10000.0,
                              "cash_usd": 10000.0},
                    "params": {}, "extra": {}}
            out = mod.evaluate(view, {"state_dir": tmp,
                                      "now": view["now"]})
            exits = [i for i in out if i.get("kind") == "exit"]
            self.assertEqual(len(exits), 1, sid)
            self.assertIn("13-week time exit due",
                          exits[0]["reason"])

    def test_cured_serving_produces_no_time_exit(self):
        # Post-cure: the config flag routes the sleeve to its own
        # book; the fixture journal holds ONLY the phantom BTC
        # fills plus their disposition, so the own book is empty
        # and the aggregate lot is never served.
        from desk3.exit_storm_disposition import apply_disposition
        for sid in ("beatendown", "confluence"):
            root = tempfile.mkdtemp()
            path = _write_journal(root, [
                _fill(sid, "BTC/USD", "sell", "sell_to_close",
                      1.0, 77000.0, f"{sid}-btc-1",
                      "2026-11-03T13:00:00Z")])
            apply_disposition(path, ts="2026-11-16T17:00:00+00:00")
            out = _serve_and_evaluate(sid, path, tempfile.mkdtemp())
            self.assertEqual(
                [i for i in out if i.get("kind") == "exit"], [], sid)
            self.assertEqual(out, [], sid)


class TestPinsUntouched(unittest.TestCase):
    def test_saty_sol_pin_unchanged(self):
        h = hashlib.sha256()
        with open(os.path.join(ROOT, "sleeves", "saty_sol.py"),
                  "rb") as fh:
            h.update(fh.read())
        self.assertEqual(h.hexdigest(), SATY_SOL_PIN)


if __name__ == "__main__":
    unittest.main()
