"""Blockers: GATE-CURE-ARCHIVE-20261112 — dated retention for the
research-lane ingest drops (STRICTNESS-CENSUS-2026-11-12
NOT-MEASURABLE register: 180 sleeves are unmeasurable because
historical drops are not retained; only the current drop exists
under state/ingest/, and each new drop destroys the prior one).

Cure: an IngestArchiveProducer in the desk's existing ingest
lane (desk3/producers3.py, registered in BATCH3_PRODUCERS like
its sibling ingest producers) copies every current drop file
(*.json directly under state/ingest/) to
state/ingest/archive/YYYY-MM-DD/ (ET date), byte-identical,
refreshing the dated copy when the drop changes within the day
and never touching prior days. Minimum sufficient: it archives
what exists; it builds no producers and fabricates no drops.

Fail direction: pre-cure the producer does not exist, so every
test fails on the import inside the drive.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 11, 12, 15, 0, tzinfo=timezone.utc)  # 10:00 ET


def _producer(root):
    mod = importlib.import_module("desk3.producers3")
    return mod.IngestArchiveProducer(root)


def _root_with_drops(drops):
    root = tempfile.mkdtemp()
    ing = os.path.join(root, "state", "ingest")
    os.makedirs(ing)
    for name, payload in drops.items():
        with open(os.path.join(ing, name), "wb") as fh:
            fh.write(payload)
    return root


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


class TestIngestArchive(unittest.TestCase):
    DROPS = {"fires.json": b'{"generated_at": "2026-11-12", "fires": []}',
             "rule_fires.json": b'{"generated_at": "2026-11-12", "fires": []}',
             "lazarus_fires.json": b'{"generated_at": "2026-11-12", "fires": []}'}

    def test_first_dated_copy_is_byte_identical(self):
        root = _root_with_drops(self.DROPS)
        out = _producer(root)({"now": NOW})
        arch = os.path.join(root, "state", "ingest", "archive",
                            "2026-11-12")
        for name, payload in self.DROPS.items():
            self.assertEqual(_read(os.path.join(arch, name)), payload,
                             name)
        status = out["ingest_archive"]
        self.assertEqual(status["date"], "2026-11-12")
        self.assertEqual(sorted(status["archived"]),
                         sorted(self.DROPS))

    def test_second_call_same_day_copies_nothing_new(self):
        root = _root_with_drops(self.DROPS)
        p = _producer(root)
        p({"now": NOW})
        out = p({"now": NOW + timedelta(hours=2)})
        self.assertEqual(out["ingest_archive"]["archived"], [])
        arch = os.path.join(root, "state", "ingest", "archive",
                            "2026-11-12", "fires.json")
        self.assertEqual(_read(arch), self.DROPS["fires.json"])

    def test_changed_drop_refreshes_the_dated_copy(self):
        root = _root_with_drops(self.DROPS)
        p = _producer(root)
        p({"now": NOW})
        new = b'{"generated_at": "2026-11-12", "fires": [{"symbol": "X"}]}'
        with open(os.path.join(root, "state", "ingest", "fires.json"),
                  "wb") as fh:
            fh.write(new)
        out = p({"now": NOW + timedelta(hours=1)})
        self.assertEqual(out["ingest_archive"]["archived"],
                         ["fires.json"])
        arch = os.path.join(root, "state", "ingest", "archive",
                            "2026-11-12", "fires.json")
        self.assertEqual(_read(arch), new)

    def test_next_day_creates_a_new_dated_dir(self):
        root = _root_with_drops(self.DROPS)
        p = _producer(root)
        p({"now": NOW})
        out = p({"now": NOW + timedelta(days=1)})
        self.assertEqual(out["ingest_archive"]["date"], "2026-11-13")
        arch = os.path.join(root, "state", "ingest", "archive",
                            "2026-11-13", "rule_fires.json")
        self.assertEqual(_read(arch), self.DROPS["rule_fires.json"])
        # the prior day's copy is untouched
        prev = os.path.join(root, "state", "ingest", "archive",
                            "2026-11-12", "rule_fires.json")
        self.assertEqual(_read(prev), self.DROPS["rule_fires.json"])

    def test_absent_drops_are_skipped_not_fabricated(self):
        root = _root_with_drops({})
        out = _producer(root)({"now": NOW})
        status = out["ingest_archive"]
        self.assertEqual(status["archived"], [])
        self.assertEqual(status["present"], [])

    def test_registered_in_batch3(self):
        mod = importlib.import_module("desk3.producers3")
        names = [row[0] for row in mod.BATCH3_PRODUCERS]
        self.assertIn("ingest_archive", names)


if __name__ == "__main__":
    unittest.main()
