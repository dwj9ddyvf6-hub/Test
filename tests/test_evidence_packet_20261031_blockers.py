"""Blockers: EVIDENCE-PACKET-20261031. The quants-mechanisms audit
(item 4) found pieces of an evidence packet scattered across the
desk (feed generated_at/cycle_id, snapshot_hash + producer_errors
on health/terminal, forecast Score period/counts, ensemble epoch
labels) but no single packet joining period + starting capital +
engine version + trade count + self-check flags for any published
figure: the terminal feed shipped no epoch material at all even
though state/capital_epoch.json holds start_equity, epoch start
and benchmarks, no engine-version field existed on feed/health,
and trade count was only the current cycle's orders_placed with
no packet around it.

Cure (DISPLAY only, no number computation changes): build_feed
ships an evidence_packet (period, starting_capital, benchmarks,
engine_version, trade_count with its scope, self_check flags and
a failures list that stays visible when a check fails) plus a
top-level engine_version; cycle._write_terminal reads the capital
epoch and passes it in, and stamps the same packet/version on
health.json and terminal.json; the sleeve_ensemble probe and
full report carry and render the same five-field packet.

Fail direction: on the pre-cure tree there is no evidence_packet
or engine_version anywhere below, so these tests fail."""
import gzip, hashlib, json, os, sys, tempfile, textwrap, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GOOD = '''
def evaluate(view, ctx):
    return []
'''

EPOCH = {"epoch_start_utc": "2026-10-26T20:14:30+00:00",
         "start_equity": 1000000, "benchmarks": ["SPY", "QQQ"]}


def at(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _roll():
    return {"generated_at": "2026-10-31T12:00:00+00:00",
            "cycle_id": "cycle-3-1", "status": "ok",
            "snapshot_hash": "abc123",
            "producer_errors": {},
            "sleeves": {"fed1": {"state": "FED", "status": "ok",
                                 "orders_placed": 2},
                        "fed2": {"state": "FED", "status": "ok",
                                 "orders_placed": 1}}}


class TestFeedEvidencePacket(unittest.TestCase):
    def test_packet_joins_all_five_fields(self):
        from desk3.terminal import build_feed, ENGINE_VERSION
        acct = {"cash": 500.0, "equity": 1000100.0, "status": "ACTIVE"}
        feed = build_feed(_roll(), {"fed1": {"slice_usd": 100.0},
                                    "fed2": {"slice_usd": 100.0}},
                          positions=[], account=acct,
                          capital_epoch=EPOCH)
        self.assertEqual(feed["engine_version"], ENGINE_VERSION)
        pkt = feed["evidence_packet"]
        self.assertEqual(pkt["period"]["start"], EPOCH["epoch_start_utc"])
        self.assertEqual(pkt["period"]["end"], "2026-10-31T12:00:00+00:00")
        self.assertEqual(pkt["starting_capital"], 1000000)
        self.assertEqual(pkt["benchmarks"], ["SPY", "QQQ"])
        self.assertEqual(pkt["engine_version"], ENGINE_VERSION)
        self.assertEqual(pkt["trade_count"], 3)
        self.assertIn("orders_placed", pkt["trade_count_scope"])
        sc = pkt["self_check"]
        self.assertTrue(sc["capital_epoch_present"])
        self.assertTrue(sc["starting_capital_present"])
        self.assertTrue(sc["period_start_present"])
        self.assertTrue(sc["snapshot_hash_present"])
        self.assertEqual(sc["snapshot_hash"], "abc123")
        self.assertFalse(sc["producer_errors_present"])
        self.assertTrue(sc["account_present"])
        self.assertFalse(sc["account_read_failed"])
        self.assertEqual(pkt["failures"], [])

    def test_missing_epoch_is_flagged_never_fabricated(self):
        from desk3.terminal import build_feed
        feed = build_feed(_roll(), {"fed1": {"slice_usd": 100.0}},
                          positions=[], account={"equity": 1.0})
        pkt = feed["evidence_packet"]
        self.assertIsNone(pkt["starting_capital"])
        self.assertIsNone(pkt["period"]["start"])
        self.assertFalse(pkt["self_check"]["capital_epoch_present"])
        self.assertFalse(pkt["self_check"]["starting_capital_present"])
        self.assertTrue(any("capital_epoch" in f for f in pkt["failures"]))

    def test_failures_stay_visible(self):
        from desk3.terminal import build_feed
        roll = _roll()
        roll["producer_errors"] = {"tensor_daily20_bundle":
                                   "bundle_missing_key:tensor_daily20"}
        feed = build_feed(roll, {"fed1": {"slice_usd": 100.0}},
                          positions=[], account=None,
                          account_error="AlpacaError: down",
                          capital_epoch=EPOCH)
        pkt = feed["evidence_packet"]
        sc = pkt["self_check"]
        self.assertTrue(sc["producer_errors_present"])
        self.assertEqual(sc["producer_errors"],
                         {"tensor_daily20_bundle":
                          "bundle_missing_key:tensor_daily20"})
        self.assertFalse(sc["account_present"])
        self.assertTrue(sc["account_read_failed"])
        self.assertEqual(sc["account_error"], "AlpacaError: down")
        joined = " ".join(pkt["failures"])
        self.assertIn("tensor_daily20_bundle", joined)
        self.assertIn("account", joined)

    def test_existing_feed_numbers_unchanged(self):
        # Preservation: the packet is additive; every pre-existing
        # number on the feed is exactly what the old builder made.
        from desk3.terminal import build_feed
        feed = build_feed(_roll(), {"fed1": {"slice_usd": 100.0},
                                    "fed2": {"slice_usd": 250.0}},
                          positions=[], account=None,
                          capital_epoch=EPOCH)
        self.assertEqual(feed["summary"]["orders_placed"], 3)
        self.assertEqual(feed["summary"]["money_assigned_total"], 350.0)
        self.assertEqual(feed["summary"]["strategies_total"], 2)
        self.assertIn("3 order(s) placed", feed["headline"])


class TestCycleStampsPacket(unittest.TestCase):
    def _desk(self, tmp, with_epoch=True):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        fixdir = os.path.join(tmp, "fix"); os.makedirs(fixdir)
        with open(os.path.join(fixdir, "good.py"), "w") as fh:
            fh.write(textwrap.dedent(GOOD))
        broker = FakeBroker(prices={"SPY": 100.0})
        broker.cash = 777.0
        desk = Desk(tmp, broker=broker, sleeve_path=fixdir,
                    timeout_s=10.0)
        if with_epoch:
            with open(os.path.join(tmp, "state",
                                   "capital_epoch.json"), "w") as fh:
                json.dump(EPOCH, fh)
        desk.add_producer(
            "account", lambda ctx: {"positions": []},
            outputs=("positions",), freshness_sla_s=3600)
        desk.add_producer(
            "bars", lambda ctx: {"bars": {"SPY": [
                {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0,
                 "v": 1}]}},
            outputs=("bars",), freshness_sla_s=3600)
        desk.add_sleeve("fed1", "good", inputs=("bars", "positions"),
                        cadence_s=60, slice_usd=10000.0)
        return desk

    def test_cycle_feed_health_terminal_carry_packet(self):
        from desk3.terminal import ENGINE_VERSION
        tmp = tempfile.mkdtemp()
        desk = self._desk(tmp)
        desk.run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state",
                                           "terminal_feed.json")))
        pkt = feed["evidence_packet"]
        self.assertEqual(pkt["starting_capital"], 1000000)
        self.assertEqual(pkt["period"]["start"],
                         EPOCH["epoch_start_utc"])
        self.assertEqual(pkt["benchmarks"], ["SPY", "QQQ"])
        self.assertEqual(feed["engine_version"], ENGINE_VERSION)
        self.assertTrue(pkt["self_check"]["snapshot_hash_present"])
        for name in ("health.json", "terminal.json"):
            doc = json.load(open(os.path.join(tmp, "state", name)))
            self.assertEqual(doc["engine_version"], ENGINE_VERSION, name)
            self.assertEqual(doc["evidence_packet"]["starting_capital"],
                             1000000, name)

    def test_cycle_without_epoch_flags_the_gap(self):
        tmp = tempfile.mkdtemp()
        desk = self._desk(tmp, with_epoch=False)
        desk.run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state",
                                           "terminal_feed.json")))
        pkt = feed["evidence_packet"]
        self.assertIsNone(pkt["starting_capital"])
        self.assertFalse(pkt["self_check"]["capital_epoch_present"])
        self.assertTrue(any("capital_epoch" in f
                            for f in pkt["failures"]))


class TestEnsembleEvidencePacket(unittest.TestCase):
    def test_probe_packet_joins_all_five_fields(self):
        from desk3.forecast import VERSION
        from desk3.forecast import sleeve_ensemble as TOOL
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "capital_epoch.json"), "w") as f:
                json.dump(dict(EPOCH, account="TESTACCT"), f)
            rows = [
                {"event": "fill", "sleeve": "s1",
                 "ts": "2026-10-27T13:00:00+00:00"},
                {"event": "fill", "sleeve": "s2",
                 "ts": "2026-10-28T14:00:00+00:00"},
            ]
            with open(os.path.join(td, "dispatcher.jsonl"), "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            probe = TOOL.probe_v3_state(td)
            pkt = probe["evidence_packet"]
            self.assertEqual(pkt["period"]["start"],
                             EPOCH["epoch_start_utc"])
            self.assertEqual(pkt["starting_capital"], 1000000)
            self.assertEqual(pkt["benchmarks"], ["SPY", "QQQ"])
            self.assertEqual(pkt["engine_version"], VERSION)
            self.assertEqual(probe["engine_version"], VERSION)
            self.assertEqual(pkt["trade_count"], 2)
            self.assertIn("fill", pkt["trade_count_scope"])
            # failures visible: the probe cannot feed honestly and
            # the packet names why instead of hiding it.
            self.assertTrue(pkt["failures"])
            self.assertTrue(any("equity curves" in f
                                for f in pkt["failures"]))
            md = TOOL.render_probe(probe)
            self.assertIn("Evidence packet", md)
            self.assertIn("1000000", md)
            self.assertIn(VERSION, md)

    def test_full_report_packet_and_preserved_numbers(self):
        from desk3.forecast import sleeve_ensemble as TOOL
        # Minimal femto-format record, same shape as the existing
        # ensemble blockers build.
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "rec")
            led = os.path.join(src, "state", "ledger")
            os.makedirs(led)
            days = ["2027-01-04", "2027-01-05", "2027-01-06",
                    "2027-01-07", "2027-01-08", "2027-01-11"]
            import time
            books = {}
            for sid in ("a", "b"):
                curve = []
                eq = 100000.0
                for i, d in enumerate(days):
                    y, m, dd = (int(x) for x in d.split("-"))
                    ts = datetime(y, m, dd, 16, 30,
                                  tzinfo=timezone.utc).timestamp()
                    eq *= 1.001
                    curve.append([ts, eq])
                books[sid] = {"capital": 100000.0, "curve": curve,
                              "n_fills": 2, "positions": {},
                              "trades": [], "cash": 100000.0}
            with open(os.path.join(src, "state", "books.json"),
                      "w") as f:
                json.dump(books, f)
            fills = [{"sleeve": "a", "inst": "EQ:SPY", "side": "buy",
                      "qty": 10, "at": curve_ts} for curve_ts in
                     (books["a"]["curve"][0][0],)]
            raw = "".join(json.dumps(dict(x, kind="book_fill")) + "\n"
                          for x in fills).encode()
            with open(os.path.join(led, "seg-000000.jsonl.gz"),
                      "wb") as f:
                f.write(gzip.compress(raw))
            with open(os.path.join(led, "open.jsonl"), "wb") as f:
                f.write(b"")
            with open(os.path.join(led, "manifest.json"), "w") as f:
                json.dump({"segments": [{"name": "seg-000000.jsonl.gz",
                                         "sha256": hashlib.sha256(
                                             raw).hexdigest()}],
                           "open": {"name": "open.jsonl"}}, f)
            out = os.path.join(td, "out", "rep")
            self.assertEqual(TOOL.main(["--root", src, "--out", out,
                                        "--boot", "20"]), 0)
            rep = json.loads(open(out + ".json").read())
            pkt = rep["evidence_packet"]
            self.assertEqual(pkt["starting_capital"], 100000.0)
            self.assertEqual(pkt["trade_count"], 1)
            self.assertEqual(pkt["engine_version"], rep["version"])
            self.assertEqual(pkt["period"]["start"],
                             rep["calendar"]["first"])
            self.assertEqual(pkt["period"]["end"],
                             rep["calendar"]["last"])
            self.assertTrue(
                pkt["self_check"]["ledger_segments_sha256_checked"])
            md = open(out + ".md").read()
            self.assertIn("Evidence packet", md)
            self.assertIn("ensemble-1", md)


if __name__ == "__main__":
    unittest.main()
