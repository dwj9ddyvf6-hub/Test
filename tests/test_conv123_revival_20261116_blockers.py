"""Regression blockers: CONV123-REVIVAL-20261116 (2026-11-16).

Defect class (Conversion Register CONV-123, GOING-LIVE
2026-11-15 class BLOCKED; Lane B's port construction in
BUGLOG_2026-11-15.md): the three Graveyard revival pulses
(turn-of-month, pairs, PEAD) accrue forward under a frozen
revival rule (250 active days, or 100 events for PEAD,
published-direction mean positive at t at or above 2), but the
accrual ledgers were research-lane files no desk producer
served, and each family's trade form lived in
foundry/c3_graveyard.py constructions, not desk evaluators —
so no family could ever fire, however its count accrued.

Cure (this landing): desk3/revival_producers.py (one producer
per ledger, reading the research lane's canonical w7 shadow
ledgers in place — one source of truth, never forked — serving
revival_tom / revival_pairs / revival_pead into the snapshot
and stamping state/revival_<family>.json), desk3/
revival_basket.py (the basket engine with one evaluator per
family: TOM window form, pairs Gatev form, PEAD drift form;
a family trades only when its served revival_state is
REVIVED), adapters3/revival_basket.py, registration in
config/sleeves.json (roster 387 -> 388) and
config/revival_basket_20261116.json (falsifier, kill rule and
sizing byte-identical to the register row; the revival rule
byte-identical to each ledger's genesis row).

Fixture proof level, stated honestly: the PAIRS and PEAD
constructions reproduce the foundry's own published outputs
exactly on the held inputs (c3_results.json: pairs 1,469
active days at +1.04bp, t 1.05, entry counts 26/31/27/26;
PEAD 655 matured events, leg21 -61.05bp, leg5 -78.79bp,
tercile means 372.39 / 311.34). The TOM leg reproduces the
foundry read on the accrual convention (427 priced active
days at +7.72bp, t 1.40; the foundry's 428 counts the grid's
first, unpriceable day as a zero — the one named difference).

Fail direction: on the pre-change tree the producer and
engine modules, the adapter, the registry file and the roster
row do not exist, so the import, membership and fixture tests
error or fail; the pin tests (saty_sol, Tensor hashes) pass
both ways by design.
"""
import hashlib
import json
import os
import statistics
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3 import revival_basket as rb
from desk3 import revival_producers as rp

RESEARCH = os.path.expanduser(
    "~/workspace/research_notes/decisions-api-leverage-20261114")
LEDGER_DIR = os.path.join(RESEARCH, "keepgoing2", "wave7")
REGISTER = os.path.expanduser(
    "~/workspace/research_notes/alpha-hunt-chaos-20261115/"
    "pass2/CONVERSION-REGISTER-2026-11-15.jsonl")
REVIVAL_RULE = ("a leg is declared REVIVED only if its forward read, "
                "at 250 further active days (or 100 further events "
                "for PEAD), shows its published-direction mean "
                "positive with t at or above 2 in the forward "
                "window alone")


def _write_ledger(path, genesis, rows):
    with open(path, "w") as fh:
        fh.write(json.dumps(genesis) + "\n")
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _genesis(leg, extra=None):
    row = {"record_type": "genesis", "leg": leg,
           "registered": "2026-11-15",
           "construction": f"foundry/c3_graveyard.py {leg} leg, frozen",
           "revival_rule": REVIVAL_RULE, "status": "genesis"}
    row.update(extra or {})
    return row


class TestProducersServeRealLedgers(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_all_three_serve_genesis_state_accruing(self):
        for cls, fam in ((rp.RevivalTomProducer, "tom"),
                         (rp.RevivalPairsProducer, "pairs"),
                         (rp.RevivalPeadProducer, "pead")):
            out = cls(self.root)({})
            self.assertEqual(list(out), [f"revival_{fam}"])
            st = out[f"revival_{fam}"]
            self.assertEqual(st["revival_state"], "accruing")
            self.assertEqual(st["accrual_start"], "2026-11-16")
            self.assertEqual(st["revival_rule"], REVIVAL_RULE)
            self.assertEqual(st["registered"], "2026-11-15")
            count = st.get("active_days", st.get("events_matured"))
            self.assertEqual(count, 0)  # accrual starts today
            # desk state carries the same state, readable on disk
            disk = json.load(open(os.path.join(
                self.root, "state", f"revival_{fam}.json")))
            self.assertEqual(disk["revival_state"], "accruing")
            self.assertEqual(disk["revival_rule"], REVIVAL_RULE)

    def test_thresholds_frozen(self):
        self.assertEqual(rp.RevivalTomProducer.THRESHOLD, 250)
        self.assertEqual(rp.RevivalPairsProducer.THRESHOLD, 250)
        self.assertEqual(rp.RevivalPeadProducer.THRESHOLD, 100)

    def test_missing_ledger_fails_closed(self):
        for cls in (rp.RevivalTomProducer, rp.RevivalPairsProducer,
                    rp.RevivalPeadProducer):
            self.assertEqual(
                cls(self.root, ledger_path="/nonexistent/x.jsonl")({}),
                {})

    def test_register_revival_wires_three_producers(self):
        class FakeDesk:
            def __init__(self):
                self.added = []

            def add_producer(self, name, fn, outputs, sla):
                self.added.append((name, outputs))
        desk = FakeDesk()
        rp.register_revival(desk, self.root)
        self.assertEqual(
            desk.added,
            [("revival_tom", ["revival_tom"]),
             ("revival_pairs", ["revival_pairs"]),
             ("revival_pead", ["revival_pead"])])


class TestRevivalRuleFrozenAtCount(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.path = os.path.join(self.root, "ledger.jsonl")

    def _tom_state(self, rets):
        start = date(2026, 11, 16)
        rows = [{"record_type": "active_day", "leg": "TOM",
                 "date": (start + timedelta(days=i)).isoformat(),
                 "ret_bp": r, "status": "accruing"}
                for i, r in enumerate(rets)]
        _write_ledger(self.path, _genesis("TOM"), rows)
        return rp.RevivalTomProducer(
            self.root, ledger_path=self.path)({})["revival_tom"]

    def test_249_days_still_accruing(self):
        st = self._tom_state([10.0, 11.0] * 124 + [10.0])
        self.assertEqual(st["active_days"], 249)
        self.assertEqual(st["revival_state"], "accruing")

    def test_250_positive_days_revived(self):
        st = self._tom_state([10.0, 11.0] * 125)
        self.assertEqual(st["revival_state"], "REVIVED")
        self.assertGreater(st["frozen_t"], 2)

    def test_250_negative_days_reburied(self):
        st = self._tom_state([-10.0, -11.0] * 125)
        self.assertEqual(st["revival_state"], "REBURIED")

    def test_read_frozen_at_the_count(self):
        # 250 strong days, then 60 catastrophic ones: the frozen
        # read (first 250) still revives; the running read shows
        # the later rows and decides nothing.
        st = self._tom_state([10.0, 11.0] * 125 + [-500.0] * 60)
        self.assertEqual(st["active_days"], 310)
        self.assertEqual(st["revival_state"], "REVIVED")
        self.assertLess(st["mean_bp"], st["frozen_mean_bp"])

    def test_pead_100_matured_events_revived(self):
        rows = []
        for i in range(100):
            surprise = float(i - 50)
            rows.append({
                "record_type": "event", "leg": "PEAD",
                "symbol": "NVDA",
                "acceptance_utc": f"2026-11-16T21:00:{i:02d}.000Z",
                "event_date": "2026-11-17",
                "surprise_bp": surprise,
                "drift5_bp": surprise * 5.0,
                "drift21_bp": surprise * 10.0,
                "status": "matured"})
        _write_ledger(self.path, _genesis("PEAD"), rows)
        st = rp.RevivalPeadProducer(
            self.root, ledger_path=self.path)({})["revival_pead"]
        self.assertEqual(st["events_matured"], 100)
        self.assertEqual(st["revival_state"], "REVIVED")
        self.assertGreater(st["frozen_mean_bp"], 0)
        self.assertGreaterEqual(st["frozen_t"], 2)
        self.assertEqual(len(st["events"]), 100)

    def test_pead_unmatured_events_do_not_count(self):
        rows = [{"record_type": "event", "leg": "PEAD",
                 "symbol": "NVDA",
                 "acceptance_utc": f"2026-11-16T21:00:{i:02d}.000Z",
                 "event_date": "2026-11-17", "surprise_bp": 100.0,
                 "drift5_bp": None, "drift21_bp": None,
                 "status": "accruing"} for i in range(100)]
        _write_ledger(self.path, _genesis("PEAD"), rows)
        st = rp.RevivalPeadProducer(
            self.root, ledger_path=self.path)({})["revival_pead"]
        self.assertEqual(st["events_total"], 100)
        self.assertEqual(st["events_matured"], 0)
        self.assertEqual(st["revival_state"], "accruing")


class TestFoundryFixtureProof(unittest.TestCase):
    """Held-history reproduction of the foundry constructions'
    own outputs (foundry/c3_results.json) on the same inputs."""

    @classmethod
    def setUpClass(cls):
        cls.panel = json.load(open(os.path.join(
            RESEARCH, "foundry", "panel100_bars.json")))
        cls.results = json.load(open(os.path.join(
            RESEARCH, "foundry", "c3_results.json")))

    def _closes(self, sym):
        return {r["t"]: r["c"] for r in self.panel[sym]}

    def test_tom_leg_reproduces_foundry(self):
        series = rb.tom_leg_series(self._closes("SPY"))
        vals = [v for _d, v in series]
        n = len(vals)
        mean = statistics.mean(vals) * 1e4
        t = mean / (statistics.stdev([v * 1e4 for v in vals])
                    / (n ** 0.5))
        foundry = self.results["legs"]["TOM"]["full"]["active"]
        # Accrual convention: 427 priced days; the foundry's 428
        # counts the grid's first unpriceable day as a zero.
        self.assertEqual(n, foundry["n"] - 1)
        self.assertAlmostEqual(mean, 7.72, delta=0.05)
        self.assertAlmostEqual(t, foundry["t"], delta=0.02)

    def test_pairs_leg_reproduces_foundry_exactly(self):
        closes = {s: self._closes(s)
                  for s in ("SPY", "XOM", "CVX", "JPM", "BAC",
                            "WMT", "COST", "MA", "V")}
        leg, _pos, trades, _per = rb.pairs_replay(
            closes, sorted(self._closes("SPY")))
        vals = [leg[d] for d in sorted(leg)]
        n = len(vals)
        mean = statistics.mean(vals) * 1e4
        t = mean / (statistics.stdev([v * 1e4 for v in vals])
                    / (n ** 0.5))
        foundry = self.results["legs"]["PAIRS"]["full"]["active"]
        self.assertEqual(n, foundry["n"])          # 1,469
        self.assertAlmostEqual(mean, foundry["mean_bp"],
                               delta=0.02)          # +1.04bp
        self.assertAlmostEqual(t, foundry["t"], delta=0.02)
        self.assertEqual(trades, self.results["pair_trades"])

    def test_pead_leg_reproduces_foundry_exactly(self):
        corp = json.load(open(os.path.join(
            RESEARCH, "keepgoing2", "wave5",
            "w5c_earnings_edgar.json")))
        fb_raw = json.load(open(os.path.join(
            RESEARCH, "keepgoing2", "wave3", "focus_bars.json")))
        fb = {s: {r["t"]: r for r in rows}
              for s, rows in fb_raw.items()}
        fd = {s: sorted(fb[s]) for s in fb}
        spy = fb["SPY"]
        events = []
        for sym, evs in corp["events"].items():
            if sym not in fb:
                continue
            for ev in evs:
                acc = ev["acceptance_utc"]
                aday, atime = acc[:10], acc[11:19]
                ds = fd[sym]
                cand = [d for d in ds
                        if d > aday or (d == aday
                                        and atime < "14:00:00")]
                if not cand:
                    continue
                ed = cand[0]
                i = ds.index(ed)
                if i == 0 or ed not in spy:
                    continue
                prev = ds[i - 1]
                if prev not in spy:
                    continue
                rec = {"surprise_bp":
                       ((fb[sym][ed]["c"] / fb[sym][prev]["c"] - 1.0)
                        - (spy[ed]["c"] / spy[prev]["c"] - 1.0))
                       * 1e4}
                for h, key in ((5, "drift5_bp"), (21, "drift21_bp")):
                    if i + h < len(ds) and ds[i + h] in spy:
                        rec[key] = (
                            (fb[sym][ds[i + h]]["c"]
                             / fb[sym][ed]["c"] - 1.0)
                            - (spy[ds[i + h]]["c"]
                               / spy[ed]["c"] - 1.0)) * 1e4
                events.append(rec)
        stats = rp.pead_leg_stats(events)
        foundry = self.results["pead"]
        self.assertEqual(stats["n"],
                         foundry["events_with_drift21"])  # 655
        self.assertAlmostEqual(stats["leg21_bp"],
                               foundry["leg21_bp"], delta=0.05)
        self.assertAlmostEqual(stats["leg5_bp"],
                               foundry["leg5_bp"], delta=0.05)
        self.assertAlmostEqual(stats["bottom21_bp"],
                               foundry["bottom_tercile_drift21_bp"],
                               delta=0.05)
        self.assertAlmostEqual(stats["top21_bp"],
                               foundry["top_tercile_drift21_bp"],
                               delta=0.05)


def _bar(day, close):
    return {"t": f"{day}T05:00:00Z", "o": close, "h": close,
            "l": close, "c": close, "v": 1000.0}


class TestBasketEvaluatorBehavior(unittest.TestCase):
    def _tom_view(self, state, now="2026-11-30T15:00:00Z",
                  positions=None):
        # Mon 2026-11-30 is the last business day of November.
        return {"now": now,
                "bars": {"SPY|1Day": [_bar("2026-11-27", 500.0),
                                      _bar("2026-11-30", 502.0)]},
                "positions": positions or [],
                "slice": {"cash_usd": 10000.0},
                "revival_tom": {"revival_state": state}}

    def test_no_fired_family_no_trades_even_on_tom_day(self):
        self.assertEqual(
            rb.evaluate("revival_basket", self._tom_view("accruing")),
            [])
        self.assertEqual(
            rb.evaluate("revival_basket",
                        self._tom_view("REBURIED")), [])

    def test_tom_fired_enters_spy_at_half_weight_single_family(self):
        intents = rb.evaluate("revival_basket",
                              self._tom_view("REVIVED"))
        self.assertEqual(len(intents), 1)
        i = intents[0]
        self.assertEqual((i.symbol, i.kind, i.side,
                          i.position_intent),
                         ("SPY", "enter", "buy", "buy_to_open"))
        self.assertAlmostEqual(i.qty * i.price_hint, 5000.0,
                               delta=0.05)

    def test_tom_window_first_three_days(self):
        self.assertTrue(rb.is_tom_day(date(2026, 12, 1)))
        self.assertTrue(rb.is_tom_day(date(2026, 11, 30)))
        self.assertFalse(rb.is_tom_day(date(2026, 11, 16)))

    def test_pairs_gatev_sides_from_replay(self):
        days = []
        d = date(2025, 1, 1)
        while len(days) < 320:
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += timedelta(days=1)

        def series(fn):
            return {days[i]: fn(i) for i in range(len(days))}
        closes = {
            "SPY": series(lambda i: 100.0),
            "XOM": series(lambda i: 100.0 if i % 2 == 0 else 101.0),
            "CVX": series(lambda i: 50.0 if i % 2 == 0 else 50.5),
            "JPM": series(lambda i: 100.0),
            "BAC": series(lambda i: 50.0),
            "WMT": series(lambda i: 100.0),
            "COST": series(lambda i: 50.0),
            "MA": series(lambda i: 100.0),
            "V": series(lambda i: 50.0)}
        for i in range(300, 320):
            closes["XOM"][days[i]] = 120.0 if i % 2 == 0 else 121.0
        desired = rb.pairs_desired(closes, days, 5000.0)
        # XOM/CVX spread rich (pos +1): short XOM, long CVX,
        # alloc/4 per pair split half and half.
        self.assertEqual(desired, {"XOM": -625.0, "CVX": 625.0})

    def test_pead_desired_terciles_and_hold_window(self):
        days = []
        d = date(2026, 10, 1)
        while len(days) < 30:
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += timedelta(days=1)
        events = []
        for j, s in enumerate((-900, -700, -500, -300, -100, 100,
                               300, 500, 900)):
            events.append({"symbol": f"S{j}",
                           "event_date": days[10],
                           "surprise_bp": float(s),
                           "drift21_bp": None, "drift5_bp": None})
        events[-1]["event_date"] = days[-2]   # top, age 1: active
        events[0]["event_date"] = days[3]     # bottom, age 26: out
        desired = rb.pead_desired(events, days, days[-1], 5000.0)
        self.assertEqual(desired["S8"], 1000.0)   # top tercile long
        self.assertNotIn("S0", desired)           # aged out at +21
        self.assertLess(desired["S1"], 0)         # bottom tercile short

    def test_two_fired_families_split_equally(self):
        view = {"revival_tom": {"revival_state": "REVIVED"},
                "revival_pairs": {"revival_state": "REVIVED"},
                "revival_pead": {"revival_state": "accruing"}}
        self.assertEqual(rb.family_allocations(view, 10000.0),
                         {"tom": 5000.0, "pairs": 5000.0})


class TestRegistration(unittest.TestCase):
    def setUp(self):
        self.doc = json.load(open(os.path.join(
            ROOT, "config", "revival_basket_20261116.json")))
        self.reg = {}
        with open(REGISTER) as fh:
            for line in fh:
                if line.strip():
                    d = json.loads(line)
                    self.reg[d["id"]] = d

    def test_registry_text_byte_identical_to_register(self):
        row = self.reg["CONV-123"]
        self.assertEqual(self.doc["falsifier"], row["falsifier"])
        self.assertEqual(self.doc["kill_rule"], row["kill_rule"])
        self.assertEqual(self.doc["sizing"], row["sizing"])
        self.assertEqual(self.doc["revival_rule"], REVIVAL_RULE)
        self.assertEqual(self.doc["accrual_start"], "2026-11-16")
        fams = {f["family"] for f in self.doc["families"]}
        self.assertEqual(fams, {"tom", "pairs", "pead"})

    def test_roster_row_exactly_once_roster_388(self):
        cfg = json.load(open(os.path.join(ROOT, "config",
                                          "sleeves.json")))
        rows = cfg["sleeves"]
        # TOTAL-AUDIT-PIN-REBASE-20261116: struck at 388 on the
        # lane tree (387 + this registration); on main the same
        # registration lands on the 399 roster, so the pin is 400.
        self.assertEqual(len(rows), 400)
        mine = [r for r in rows if r["id"] == "revival_basket"]
        self.assertEqual(len(mine), 1)
        row = mine[0]
        self.assertEqual(row["module"], "adapters3.revival_basket")
        self.assertEqual(row["inputs"], list(rb.INPUTS))
        self.assertTrue(row["own_book_view"])
        self.assertFalse(row["parked"])
        self.assertTrue(os.path.exists(os.path.join(
            ROOT, "adapters3", "revival_basket.py")))
        self.assertEqual(rb.config_rows()[0]["inputs"],
                         row["inputs"])

    def test_run_live_wires_producers(self):
        src = open(os.path.join(ROOT, "desk3", "run_live.py")).read()
        self.assertIn("register_revival(desk, root)", src)


class TestPinsUntouched(unittest.TestCase):
    def test_saty_sol_pin_unchanged(self):
        h = hashlib.sha256(open(os.path.join(
            ROOT, "sleeves", "saty_sol.py"), "rb").read()).hexdigest()
        self.assertEqual(
            h,
            "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea4"
            "16cc08962bdc")

    def test_tensor_engine_hashes_verify(self):
        sys.path.insert(0, os.path.join(ROOT, "vendor"))
        import tensor_exact
        tensor_exact.verify_engine_hashes()


if __name__ == "__main__":
    unittest.main()
