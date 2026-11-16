"""QULLA-EVIDENCE-ERROR blockers (NO-PARTIALS DRIVE 2026-11-11):
QullaFileProducer served cache/qulla/proposals.json on session and
shape alone. A scan that FAILED inside the v2 engine still writes
a file with the right session and an empty proposals list
(evidence.error set; live artifact 2026-11-11: "RuntimeError:
qulla frames incomplete", intraday_rows 0), so qullamaggie and
qullamaggie_paper read FED on an engine-failed empty scan and
nothing named it.

Cure: the producer fails closed by name when evidence.error is
non-empty (last_error "qulla_scan_evidence_error:<...>"), the
posture of every other producer on this desk.

Fail direction on the pre-cure tree: the evidence-error fixture
below is SERVED (returns {"qulla": doc}).
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.producers_g4 import QullaFileProducer, _expected_qulla_session, ET


def _root_with_file(doc):
    root = tempfile.mkdtemp(prefix="qullaev_")
    cache = os.path.join(root, "cache", "qulla")
    os.makedirs(cache, exist_ok=True)
    with open(os.path.join(cache, "proposals.json"), "w") as fh:
        json.dump(doc, fh)
    return root


def _pctx():
    now = datetime.now(timezone.utc)
    return {"now": now}, _expected_qulla_session(
        now.astimezone(ET).date())


class TestQullaEvidenceError(unittest.TestCase):

    def test_failed_scan_is_not_served(self):
        pctx, session = _pctx()
        doc = {"session": session, "proposals": [],
               "evidence": {"error": "RuntimeError: qulla frames "
                                     "incomplete",
                            "intraday_rows": 0, "daily_rows": 10752}}
        prod = QullaFileProducer(_root_with_file(doc))
        self.assertEqual(prod(pctx), {})
        self.assertTrue(
            prod.last_error.startswith("qulla_scan_evidence_error:"),
            prod.last_error)

    def test_clean_scan_still_serves(self):
        pctx, session = _pctx()
        doc = {"session": session,
               "proposals": [{"symbol": "AAA"}],
               "evidence": {"intraday_rows": 1200}}
        prod = QullaFileProducer(_root_with_file(doc))
        out = prod(pctx)
        self.assertEqual(out.get("qulla", {}).get("session"), session)
        self.assertIsNone(prod.last_error)

    def test_stale_session_still_names_stale(self):
        pctx, _session = _pctx()
        doc = {"session": "2000-01-03", "proposals": [],
               "evidence": {"error": "RuntimeError: frames"}}
        prod = QullaFileProducer(_root_with_file(doc))
        self.assertEqual(prod(pctx), {})
        self.assertEqual(prod.last_error, "stale_qulla_session")


if __name__ == "__main__":
    unittest.main()
