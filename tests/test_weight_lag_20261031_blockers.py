"""Blockers WEIGHT-LAG-20261031: the weight-lag mechanism as a class.

Audit (research_notes/quants-mechanisms-steal-20261031/AUDIT.md, item 1):
the desk had no engine-layer weight lag and no blocker named for
weight-lag as a mechanism; the live target-weight books
(desk3/aster_etf.py, sleeves/momentum_rotation.py,
sleeves/ts_momentum_decile.py) relied on per-sleeve closed-bar gating.

WEIGHT-LAG-ACTIVE-20261031 (owner rulings 2026-10-31 10:39 ET and
2026-10-31 11:44 ET): the one-bar weight lag is APPLIED to the live
books. What this blocker pins:

  - every target-weight book carries the same WEIGHT_LAG_POLICY
    declaration (lag_bars 1, applied True, basis
    closed_bar_gating_only, status ACTIVE, the rulings cited) on
    the module the live cycle actually loads: desk3/aster_etf.py
    itself, desk3/port_b5/momentum_rotation.py and
    adapters3/ts_momentum_decile.py (the byte-identical strategy
    ports under sleeves/ are preservation-pinned and untouched);
  - the lag behavior at each book's consumption point: target
    weights computed at one evaluation are acted on at the NEXT
    evaluation of that book (aster_etf: the previous evaluation's
    target-share counts diffed against current positions; the two
    delegated books: intents held one evaluation at the wrapper,
    pending state persisted under the cycle state_dir when served);
  - the edges: a first evaluation after activation emits nothing
    for newly computed weights, and an evaluation that computes no
    weights (aster window/month gates, a non-due momentum_rotation
    rebalance, a monthly-suppressed ts_momentum_decile evaluation)
    does not advance the lag;
  - aster_etf's observer record stays additive-only (intents
    identical with and without the opt-in journal);
  - the closed-bar basis the declarations rest on (ts_momentum_
    decile's forming bar is excluded from ranking even when it
    carries an extreme return).

Fail direction: with the three books' lag application points
temporarily reverted to the guard behavior, the four behavioral
tests below fail (4 failures); with the lag applied, 12/12 pass.
"""
import importlib
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CORE_FIELDS = ("mechanism", "lag_bars", "applied", "basis", "status")


def _policy(modname):
    mod = importlib.import_module(modname)
    return mod, getattr(mod, "WEIGHT_LAG_POLICY", None)


class TestWeightLagPolicyDeclared(unittest.TestCase):
    BOOKS = ("desk3.aster_etf", "desk3.port_b5.momentum_rotation",
             "adapters3.ts_momentum_decile")

    def test_every_weight_book_declares_the_policy(self):
        for name in self.BOOKS:
            _mod, pol = _policy(name)
            self.assertIsInstance(pol, dict, name)
            self.assertEqual(pol["mechanism"], "weight-lag", name)
            # The behavioral lag IS landed on the live books.
            self.assertEqual(pol["lag_bars"], 1, name)
            self.assertIs(pol["applied"], True, name)
            self.assertEqual(pol["basis"], "closed_bar_gating_only", name)
            self.assertEqual(pol["status"], "ACTIVE", name)

    def test_policies_agree_across_books(self):
        pols = [_policy(n)[1] for n in self.BOOKS]
        for field in CORE_FIELDS:
            self.assertEqual(len({str(p[field]) for p in pols}), 1, field)

    def test_reason_and_ruling_are_stated(self):
        for name in self.BOOKS:
            _mod, pol = _policy(name)
            self.assertIn("look-ahead", pol["reason"], name)
            self.assertIn("closed", pol["reason"].lower(), name)
            self.assertIn("2026-10-31", pol["ruling_needed"], name)
            self.assertIn("one-bar", pol["ruling_needed"], name)

    def test_lag_declared_in_source(self):
        for rel in ("desk3/aster_etf.py",
                    "desk3/port_b5/momentum_rotation.py",
                    "adapters3/ts_momentum_decile.py"):
            with open(os.path.join(ROOT, rel)) as fh:
                src = fh.read()
            self.assertIn('"lag_bars": 1', src, rel)
            self.assertIn('"applied": True', src, rel)

    def test_no_shift_form_in_source(self):
        # The lag lives at each book's consumption point, not as a
        # pandas-style bar shift inside the strategy ports.
        for rel in ("desk3/aster_etf.py",
                    "desk3/port_b5/momentum_rotation.py",
                    "adapters3/ts_momentum_decile.py",
                    "sleeves/momentum_rotation.py",
                    "sleeves/ts_momentum_decile.py"):
            with open(os.path.join(ROOT, rel)) as fh:
                self.assertNotIn("shift(1)", fh.read(), rel)

    def test_strategy_ports_stay_preservation_clean(self):
        # The declarations live in the v3 entrypoints precisely so
        # the byte-identical ports keep their port-fidelity pins:
        # the pinned sleeve files carry no policy block.
        for rel in ("sleeves/momentum_rotation.py",
                    "sleeves/ts_momentum_decile.py"):
            with open(os.path.join(ROOT, rel)) as fh:
                self.assertNotIn("WEIGHT_LAG_POLICY", fh.read(), rel)
        import sleeves.momentum_rotation as mr
        self.assertEqual(mr.TARGET_WEIGHT, 0.20)  # sizing untouched


def _flat_bars(px, n=130):
    return [{"t": "2026-01-%02d" % ((i % 28) + 1), "o": px, "h": px,
             "l": px, "c": px, "v": 1000} for i in range(n)]


def _etf_view(px=100.0, extra=None, positions=None):
    return {"now": "2026-10-01T09:36:00",
            "bars": {"QQQ": _flat_bars(px)},
            "positions": positions or [], "quotes": {},
            "extra": extra or {}}


CTX = {"session": "2026-10-01", "now": "2026-10-01T09:36:00",
       "slice": {"capital_usd": 10000.0}}


class TestAsterEtfObserverIsAdditiveOnly(unittest.TestCase):
    def setUp(self):
        import desk3.aster_etf as aster
        aster._PENDING_TARGETS.clear()

    def test_intents_identical_with_and_without_journal(self):
        import desk3.aster_etf as aster
        from desk3.aster_etf import evaluate
        # Same lag position for both drives: reset the pending
        # state between them (the lag itself is stateful by design).
        plain = evaluate("aster_etf_qqq_buy_hold", _etf_view(), dict(CTX))
        aster._PENDING_TARGETS.clear()
        journal = {"records": []}
        served = evaluate("aster_etf_qqq_buy_hold",
                          _etf_view(extra={"weight_lag_journal": journal}),
                          dict(CTX))
        self.assertEqual(plain, served)
        self.assertEqual(len(journal["records"]), 1)
        rec = journal["records"][0]
        self.assertEqual(rec["mechanism"], "weight-lag")
        self.assertEqual(rec["lag_bars"], 1)
        self.assertEqual(rec["status"], "ACTIVE")


class TestAsterEtfLagBehavior(unittest.TestCase):
    def setUp(self):
        import desk3.aster_etf as aster
        aster._PENDING_TARGETS.clear()

    def test_first_evaluation_nothing_second_acts(self):
        from desk3.aster_etf import evaluate
        first = evaluate("aster_etf_qqq_buy_hold", _etf_view(), dict(CTX))
        self.assertEqual(first, [])  # newly computed weights held
        second = evaluate("aster_etf_qqq_buy_hold", _etf_view(), dict(CTX))
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0]["kind"], "entry")
        self.assertEqual(second[0]["symbol"], "QQQ")
        self.assertEqual(second[0]["qty"], 100)

    def test_lagged_targets_diffed_against_current_positions(self):
        from desk3.aster_etf import evaluate
        sid = "aster_etf_qqq_monthly_c098"
        # Eval 1 at px 100: pending target = floor(0.98*10000/100) = 98.
        self.assertEqual(evaluate(sid, _etf_view(100.0), dict(CTX)), [])
        # Eval 2 at px 50 with 50 held (entered last month): the
        # LAGGED target (98) is diffed, not the recomputed one
        # (floor(0.98*10000/50) = 196): buy exactly 48.
        pos = [{"symbol": "QQQ", "qty": 50,
                "opened_at": "2026-09-01T14:00:00Z"}]
        out = evaluate(sid, _etf_view(50.0, positions=pos), dict(CTX))
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["qty"], 48)


def _bd(t, o, h, l, c, v=1000000):
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def _daily_dicts(closes, start=datetime(2026, 5, 1, 4, 0,
                                         tzinfo=timezone.utc)):
    out, d = [], start
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        out.append(_bd(d.strftime("%Y-%m-%dT%H:%M:%SZ"), c, c * 1.003,
                       c * 0.997, c))
        d += timedelta(days=1)
    return out


class TestMomentumRotationLagBehavior(unittest.TestCase):
    def test_lag_holds_one_evaluation_and_non_due_does_not_advance(self):
        mod = importlib.import_module("desk3.port_b5.momentum_rotation")
        bars = {"SPY|1Day": _daily_dicts([100 + i * 0.43
                                          for i in range(70)]),
                "QQQ|1Day": _daily_dicts([200.0] * 70)}
        sd = tempfile.mkdtemp()
        ctx = {"sleeve_id": "momentum_rotation", "state_dir": sd,
               "cycle_id": "cyc-test"}

        def drive(now):
            view = {"now": now, "bars": bars,
                    "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
            return mod.evaluate(view, dict(ctx))

        # First (due) evaluation: weights computed, nothing emitted.
        self.assertEqual(drive("2026-10-21T16:00:00-04:00"), [])
        self.assertTrue(os.path.exists(
            os.path.join(sd, "weight_lag_pending.json")))
        # Next-day evaluation is a non-due rebalance (weekly): it
        # returns no intents and must NOT advance the lag.
        self.assertEqual(drive("2026-10-22T16:00:00-04:00"), [])
        # Next due evaluation (+7d): the pending intents are emitted.
        out = drive("2026-10-28T16:00:00-04:00")
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertTrue(entries)
        self.assertEqual(entries[0]["symbol"], "SPY")
        # WS4-FRACTIONAL-20261114: the held intent now carries the
        # fractional expression of the same $2,000 budget (15.423768)
        self.assertEqual(entries[0]["qty"], 15.423768)


def _b(t, c, v=10000.0):
    return {"t": t, "o": c, "h": c * 1.001, "l": c * 0.999, "c": c, "v": v}


def _daily(n, start=100.0, drift=0.001, vol=20000.0):
    days, d = [], date(2026, 10, 22)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    return [_b(f"{x.isoformat()}T04:00:00Z", start * (1 + drift) ** i,
               v=vol) for i, x in enumerate(days)]


def _ts_view(positions=None):
    from sleeves.ts_momentum_decile import SECTOR_MAP
    by_sector = {}
    for s, sec in SECTOR_MAP.items():
        by_sector.setdefault(sec, []).append(s)
    syms = (by_sector["SEMI"] + by_sector["SOFTWARE"]
            + by_sector["BIOTECH"] + by_sector["ENERGY"]
            + by_sector["FIN"])
    top = {"NVDA": 0.009594, "AMD": 0.009594}
    mid = {"SOXL", "BNTX", "MRNA", "MSFT", "XOM", "JPM", "BAC"}
    bars = {}
    for s in syms:
        drift = top.get(s, 0.002681 if s in mid else 0.001566)
        bars[f"{s}|1Day"] = _daily(260, 100.0, drift=drift)
    flat = list(SECTOR_MAP)[20]
    bars[f"{flat}|1Day"] = _daily(260, 100.0, drift=-0.001)
    view = {"now": "2026-10-23T15:30:00-04:00", "bars": bars,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    if positions is not None:
        view["positions"] = positions
    return view, flat


class TestTsMomentumLagBehavior(unittest.TestCase):
    def test_lag_holds_one_evaluation_and_suppression_does_not_advance(self):
        mod = importlib.import_module("adapters3.ts_momentum_decile")
        seeded = [{"symbol": None, "qty": 7, "avg_price": 90.0,
                   "opened_at": "2026-09-01T14:00:00Z", "intent_id": "seed"}]
        view, flat = _ts_view()
        seeded[0]["symbol"] = flat
        view["positions"] = seeded
        sd = tempfile.mkdtemp()
        ctx = {"sleeve_id": "ts_momentum_decile", "state_dir": sd}
        # First evaluation: weights computed, nothing emitted.
        self.assertEqual(mod.evaluate(view, dict(ctx)), [])
        self.assertTrue(os.path.exists(
            os.path.join(sd, "weight_lag_pending.json")))
        # Second evaluation: the pending intents are emitted.
        out = mod.evaluate(view, dict(ctx))
        entries = [i for i in out if i["kind"] == "entry"]
        exits = [i for i in out if i["kind"] == "exit"
                 and i["symbol"] == flat]
        self.assertTrue(entries)
        self.assertTrue(exits and exits[0]["qty"] == 7)
        # A monthly-suppressed evaluation (holdings entered this
        # month) computes no weights and must not advance the lag:
        # on a fresh state dir it stores nothing, so the following
        # initial-allocation drive is still a first evaluation.
        view2, _flat2 = _ts_view()
        view2["positions"] = [{"symbol": flat, "qty": 7,
                               "avg_price": 90.0,
                               "opened_at": "2026-10-01T14:00:00Z",
                               "intent_id": "seed2"}]
        sd2 = tempfile.mkdtemp()
        ctx2 = {"sleeve_id": "ts_momentum_decile", "state_dir": sd2}
        self.assertEqual(mod.evaluate(view2, dict(ctx2)), [])
        self.assertFalse(os.path.exists(
            os.path.join(sd2, "weight_lag_pending.json")))
        view3, _flat3 = _ts_view(positions=[])
        self.assertEqual(mod.evaluate(view3, dict(ctx2)), [])
        out3 = mod.evaluate(view3, dict(ctx2))
        self.assertTrue([i for i in out3 if i["kind"] == "entry"])


class TestClosedBarBasisIsReal(unittest.TestCase):
    def test_ts_momentum_forming_bar_excluded_from_ranking(self):
        # 260 flat bars per symbol; BBB's LAST bar is dated after the
        # session (a forming bar) and carries a 10x close. If that
        # bar leaked into ranking, BBB would take the single decile
        # slot; with it dropped, both score 0.0 and the stable sort
        # keeps AAA first.
        from datetime import datetime, timedelta, timezone
        from sleeves.ts_momentum_decile import rank_decile
        start = datetime(2025, 12, 1, tzinfo=timezone.utc)

        def series(spike):
            out = []
            for i in range(260):
                d = start + timedelta(days=i)
                c = 1000.0 if (spike and i == 259) else 100.0
                out.append({"t": d.timestamp(), "o": c, "h": c,
                            "l": c, "c": c, "v": 20000})
            return out

        bars = {"AAA": series(False), "BBB": series(True)}
        decile, eligible, _stats = rank_decile(bars, "2026-08-17")
        self.assertEqual(eligible, 2)
        self.assertEqual(decile, ["AAA"])


if __name__ == "__main__":
    unittest.main()
