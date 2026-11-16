"""Blockers: TERM-1 desk terminal feed + page (freshness, plain language,
per-strategy state) and RES-1 research lane isolation (shadow candidates
cannot dispatch, write only to their own journal space, promotion is an
explicit registry move, never automatic)."""
import hashlib, json, os, sys, tempfile, textwrap, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = timezone.utc

GOOD = '''
def evaluate(view, ctx):
    return [{"intent_id": ctx["cycle_id"] + "-e1", "kind": "entry",
             "symbol": "SPY", "side": "buy", "qty": 1,
             "limit_price": 100.0, "order_type": "limit"}]
'''
BANNED = ["unfed", "dispatcher", "snapshot", "sleeve", "wedged"]


def at(ts):
    return datetime.fromtimestamp(ts, tz=ET)


def _desk(tmp):
    from desk3.cycle import Desk
    from desk3.broker import FakeBroker
    fixdir = os.path.join(tmp, "fix"); os.makedirs(fixdir)
    with open(os.path.join(fixdir, "good.py"), "w") as fh:
        fh.write(textwrap.dedent(GOOD))
    desk = Desk(tmp, broker=FakeBroker(prices={"SPY": 100.0}),
                sleeve_path=fixdir, timeout_s=10.0)
    desk.add_producer("bars", lambda ctx: {"bars": {"SPY": [
        {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]},
        "positions": {"fed1": [{"symbol": "SPY", "qty": 2}]}},
        outputs=("bars", "positions"), freshness_sla_s=3600)
    desk.add_sleeve("fed1", "good", inputs=("bars",), cadence_s=60, slice_usd=10000.0)
    desk.add_sleeve("ghost", "good", inputs=("bars", "phantom"), cadence_s=60, slice_usd=5000.0)
    desk.add_sleeve("resting", "good", inputs=("bars",), cadence_s=60,
                    slice_usd=2500.0, parked=True)
    return desk


class TestTerminalFeed(unittest.TestCase):
    def test_feed_per_strategy_state_and_summary(self):
        tmp = tempfile.mkdtemp()
        desk = _desk(tmp)
        desk.run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state", "terminal_feed.json")))
        rows = {r["name"]: r for r in feed["strategies"]}
        self.assertEqual(rows["fed1"]["status"], "Ready")
        self.assertEqual(rows["ghost"]["status"], "Waiting for data")
        self.assertEqual(rows["resting"]["status"], "Paused")
        self.assertEqual(rows["fed1"]["money_assigned"], 10000.0)
        self.assertEqual(rows["fed1"]["open_positions"][0]["symbol"], "SPY")
        self.assertTrue(rows["fed1"]["last_action"])
        s = feed["summary"]
        self.assertEqual(s["strategies_total"], 3)
        self.assertEqual(s["waiting_for_data"], 1)
        self.assertEqual(s["paused"], 1)
        self.assertEqual(s["orders_placed"], 1)
        self.assertEqual(s["open_positions"], 1)
        self.assertTrue(feed["generated_at"])
        self.assertTrue(feed["cycle_id"])

    def test_freshness_advances_across_two_cycles(self):
        tmp = tempfile.mkdtemp()
        desk = _desk(tmp)
        desk.run_cycle(now=at(20000))
        p = os.path.join(tmp, "state", "terminal_feed.json")
        first = json.load(open(p))
        desk.run_cycle(now=at(20300))
        second = json.load(open(p))
        self.assertGreater(second["generated_at"], first["generated_at"])
        self.assertNotEqual(second["cycle_id"], first["cycle_id"])

    def test_feed_and_page_plain_language(self):
        tmp = tempfile.mkdtemp()
        _desk(tmp).run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state", "terminal_feed.json")))
        blob = json.dumps({k: feed[k] for k in ("headline", "strategies", "summary")}).lower()
        for w in BANNED:
            self.assertNotIn(w, blob)
        page = open(os.path.join(ROOT, "terminal", "index.html")).read()
        for w in BANNED:
            self.assertNotIn(w, page.lower())
        self.assertIn("terminal_feed.json", page)
        self.assertTrue(("setInterval" in page) or ("http-equiv=\"refresh\"" in page))


ROGUE = '''
def evaluate(view, ctx):
    return ctx.dispatch({"intent_id": "rogue-1", "kind": "entry",
                         "symbol": "SPY", "side": "buy", "qty": 1})
'''


def _registry(tmp, module_file, module_name, cid="cand1"):
    cdir = os.path.join(tmp, "candidates"); os.makedirs(cdir, exist_ok=True)
    with open(os.path.join(cdir, module_name + ".py"), "w") as fh:
        fh.write(textwrap.dedent(module_file))
    reg = os.path.join(cdir, "registry.json")
    with open(reg, "w") as fh:
        json.dump({"candidates": [{"id": cid, "module": module_name,
                                   "status": "shadow", "inputs": ["bars"]}]}, fh)
    return reg, cdir


class TestResearchLane(unittest.TestCase):
    SNAP = {"bars": {"QQQ": [{"c": 100.0}, {"c": 101.0}, {"c": 103.0}]}}

    def test_rogue_candidate_dies_at_boundary_no_dispatch(self):
        from desk3.research import evaluate_candidates
        from desk3.journal import read_lines
        tmp = tempfile.mkdtemp()
        reg, cdir = _registry(tmp, ROGUE, "rogue")
        state = os.path.join(tmp, "state")
        res = evaluate_candidates(self.SNAP, reg, state, cdir)
        self.assertEqual(res["cand1"]["status"], "blocked_order_attempt")
        rows = read_lines(os.path.join(state, "research", "cand1", "journal.jsonl"))
        self.assertTrue(any(r.get("event") == "blocked_order_attempt" for r in rows))
        # nothing anywhere else: no dispatcher journal, no other namespace
        self.assertFalse(os.path.exists(os.path.join(state, "dispatcher.jsonl")))
        self.assertEqual(os.listdir(os.path.join(state, "research")), ["cand1"])

    def test_example_candidate_end_to_end_shadow(self):
        from desk3.research import evaluate_candidates
        from desk3.journal import read_lines
        tmp = tempfile.mkdtemp()
        state = os.path.join(tmp, "state")
        res = evaluate_candidates(self.SNAP, os.path.join(ROOT, "candidates", "registry.json"),
                                  state, os.path.join(ROOT, "candidates"))
        self.assertEqual(res["example_momentum_shadow"]["status"], "ok")
        self.assertEqual(res["example_momentum_shadow"]["signals"], 1)
        rows = read_lines(os.path.join(state, "research", "example_momentum_shadow", "journal.jsonl"))
        sig = [r for r in rows if r.get("event") == "shadow_signal"]
        self.assertEqual(len(sig), 1)
        self.assertEqual(sig[0]["symbol"], "QQQ")
        self.assertFalse(sig[0]["can_be_ordered"])

    def test_evaluation_never_promotes_and_promotion_is_explicit(self):
        from desk3.research import evaluate_candidates, promote_candidate
        tmp = tempfile.mkdtemp()
        reg, cdir = _registry(tmp, "def evaluate(view, ctx):\n    return []\n", "quiet")
        roster = os.path.join(ROOT, "config", "sleeves.json")
        roster_hash = hashlib.sha256(open(roster, "rb").read()).hexdigest()
        reg_hash = hashlib.sha256(open(reg, "rb").read()).hexdigest()
        evaluate_candidates(self.SNAP, reg, os.path.join(tmp, "state"), cdir)
        self.assertEqual(hashlib.sha256(open(reg, "rb").read()).hexdigest(), reg_hash)
        log = os.path.join(cdir, "PROMOTIONS.md")
        promote_candidate(reg, "cand1", log)
        doc = json.load(open(reg))
        self.assertEqual(doc["candidates"][0]["status"], "promoted")
        self.assertIn("cand1", open(log).read())
        # promotion alone does NOT add it to the trading roster
        self.assertEqual(hashlib.sha256(open(roster, "rb").read()).hexdigest(), roster_hash)
        self.assertNotIn("cand1", open(roster).read())


if __name__ == "__main__":
    unittest.main()
