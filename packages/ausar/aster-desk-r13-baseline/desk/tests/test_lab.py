import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager

from backend.lab import Lab
from backend.research import Research
from backend.store import DeskError, Store
from backend.trading import TradingDesk


class LabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "desk.sqlite")
        self.lab = Lab(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def registration(self):
        return {"title": "Data provenance check", "hypothesis": "Source times are retained", "method": "Compare archive receipts with feed dates", "dataset": "Configured watchlist feeds", "primary_metric": "Timestamp mismatches", "null_controls": "Shuffled source times", "acceptance_criteria": "No unexpected mismatch", "target_sample": 10, "source_pins": ["example@abc"]}

    def test_append_only_inbox_and_durable_reader_cursor(self):
        first = self.lab.message({"sender": "operator", "recipient": "all", "topic": "First", "body": "Evidence one"})
        second = self.lab.message({"sender": "operator", "recipient": "all", "topic": "Second", "body": "Evidence two"})
        self.lab.cursor("chief", first["id"])
        with self.assertRaises(DeskError):
            self.lab.cursor("chief", second["id"] + 1)
        with self.assertRaises(DeskError):
            self.lab.cursor("chief", 0)
        reopened = Lab(Store(self.store.path)).snapshot()
        self.assertEqual([m["body"] for m in reopened["inbox"]], ["Evidence two", "Evidence one"])
        self.assertEqual(reopened["cursors"][0]["through_id"], first["id"])

    def test_preregistration_is_immutable_and_rejections_remain(self):
        study = self.lab.register(self.registration())
        original_hash = study["registration_hash"]
        self.lab.study_update(study["id"], {"status": "running", "results": "Execution started"})
        self.lab.study_update(study["id"], {"status": "rejected", "results": "Two invalid source times", "sample_count": 10, "limitations": "A small sample"})
        with self.assertRaises(DeskError):
            self.lab.study_update(study["id"], {"status": "running"})
        self.lab.study_update(study["id"], {"status": "archived"})
        final = self.lab.study(study["id"])
        self.assertEqual(final["registration"], self.registration())
        self.assertEqual(final["registration_hash"], original_hash)
        self.assertEqual(len(final["results"]), 3)
        self.assertEqual(final["results"][1]["status"], "rejected")

    def test_artifacts_have_content_hash_and_exact_source_pin(self):
        artifact = self.lab.artifact({"name": "Source sample", "content": "receipt\nsecond line", "source": "feed", "source_pin": "repo@commit:path"})
        self.assertEqual(artifact["sha256"], hashlib.sha256(b"receipt\nsecond line").hexdigest())
        self.assertEqual(self.lab.export()["lab_artifacts"][0]["content"], "receipt\nsecond line")

    def test_proposal_cannot_install_strategy_and_requires_valid_decision(self):
        with self.assertRaises(DeskError):
            self.lab.proposal({"title": "Trade rule", "rationale": "x", "evidence": "x", "policy_patch": {"strategy": "buy"}})
        proposal = self.lab.proposal({"title": "Fee measurement", "rationale": "Use measured fee", "evidence": "Recorded statements", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        with self.assertRaises(DeskError):
            self.lab.decision(proposal["id"], "accepted", "Skip approval")
        self.lab.decision(proposal["id"], "approved", "Approved by operator")
        result = self.lab.decision(proposal["id"], "accepted", "Observation accepted")
        self.assertEqual(len(result["decisions"]), 2)
        with self.assertRaises(DeskError):
            self.lab.decision(proposal["id"], "approved", "Overwrite")
        self.assertEqual(self.store.snapshot({})["orders"], [])

    def test_alert_deduplication_acknowledgement_and_recovery(self):
        first = self.lab.alert("heartbeat", "critical", "Stale heartbeat")
        again = self.lab.alert("heartbeat", "critical", "Stale heartbeat")
        self.assertEqual(first["id"], again["id"])
        self.lab.update_alert(first["id"], "ack")
        self.lab.resolve_key("heartbeat")
        self.assertEqual(self.lab.snapshot()["alerts"][0]["status"], "resolved")
        self.lab.alert("heartbeat", "critical", "Stale heartbeat")
        self.assertEqual(self.lab.snapshot()["alerts"][0]["status"], "open")

    def test_recurrence_and_severity_escalation_require_fresh_acknowledgement(self):
        original = self.lab.alert("reconciliation", "warning", "Read unavailable")
        acknowledged = self.lab.update_alert(original["id"], "ack")
        self.assertIsNotNone(acknowledged["acknowledged_at"])
        escalated = self.lab.alert("reconciliation", "critical", "Ownership discrepancy")
        self.assertEqual(escalated["id"], original["id"])
        self.assertEqual(escalated["status"], "open")
        self.assertIsNone(escalated["acknowledged_at"])
        self.lab.update_alert(original["id"], "ack")
        self.lab.resolve_key("reconciliation")
        recurrence = self.lab.alert("reconciliation", "critical", "Ownership discrepancy")
        self.assertEqual(recurrence["status"], "open")
        self.assertIsNone(recurrence["acknowledged_at"])
        self.assertIsNone(recurrence["resolved_at"])

    def test_operational_handoffs_do_not_duplicate_or_create_trades(self):
        data = {"books": [{"id": "main", "name": "Main", "cash": 0, "equity": 0}], "fills": [{"id": "f1", "symbol": "AAPL", "quantity": 1}], "intents": []}
        self.lab.operate(data, {"running": True})
        self.lab.operate(data, {"running": True})
        snapshot = self.lab.snapshot()
        self.assertEqual(snapshot["inbox_total"], 2)
        self.assertEqual(snapshot["strategy_count"], 0)
        self.assertEqual(self.store.snapshot({})["orders"], [])

    def test_approved_policy_applies_then_guard_restores_its_before_state(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Measure fee model", "rationale": "Observed simulation costs", "evidence": "Independent execution receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}, "rollback_drawdown_pct": 5})
        with self.assertRaises(DeskError):
            self.lab.apply(proposal["id"])
        self.lab.decision(proposal["id"], "approved", "Operator accepts trial and rollback guard")
        applied = self.lab.apply(proposal["id"])
        self.assertEqual(applied["status"], "observing")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 1)
        snapshot = trading.snapshot()
        snapshot["books"][0]["account"]["drawdown_percent"] = 6
        self.lab.operate(snapshot)
        self.assertEqual(self.lab.proposal_get(proposal["id"])["status"], "rolled_back")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 0)
        self.assertEqual(trading.snapshot()["intents"], [])

    def test_policy_guard_preserves_a_newer_operator_policy(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}, "rollback_drawdown_pct": 5})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        self.lab.apply(proposal["id"])
        trading.set_book("main", {"fees_per_order": 2})
        snapshot = trading.snapshot()
        snapshot["books"][0]["account"]["drawdown_percent"] = 6
        self.lab.operate(snapshot)
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 2)
        self.assertTrue(any(a["dedupe_key"].startswith("proposal-conflict:") for a in self.lab.snapshot()["alerts"]))

    def test_apply_records_its_committed_hash_when_response_sees_a_newer_policy(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee trial", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        original = trading.set_book
        committed_hash = None
        def later_read_view(*args, **kwargs):
            nonlocal committed_hash
            committed_hash = original(*args, **kwargs)["policy_hash"]
            original("main", {"policy": {"fees_per_order": 2}})
            return trading.snapshot()["books"][0]
        with patch.object(trading, "set_book", side_effect=later_read_view):
            result = self.lab.apply(proposal["id"])
        self.assertEqual(result["applied_policy_hash"], committed_hash)
        self.assertNotEqual(result["applied_policy_hash"], trading.snapshot()["books"][0]["policy_hash"])
        with self.assertRaises(DeskError):
            self.lab.rollback(proposal["id"], "Restore the trial")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 2)

    def test_apply_response_failure_preserves_a_committed_policy_and_idempotent_retry(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee trial", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        original = trading.set_book
        def response_failed(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("Response read failed after the policy transaction")
        with patch.object(trading, "set_book", side_effect=response_failed):
            with self.assertRaises(RuntimeError):
                self.lab.apply(proposal["id"])
        recovered = self.lab.proposal_get(proposal["id"])
        self.assertEqual(recovered["status"], "observing")
        self.assertEqual(recovered["applied_policy_hash"], trading.snapshot()["books"][0]["policy_hash"])
        version = trading.snapshot()["books"][0]["policy_version"]
        self.assertEqual(self.lab.apply(proposal["id"])["status"], "observing")
        self.assertEqual(trading.snapshot()["books"][0]["policy_version"], version)

    def test_policy_guard_does_not_act_on_incomplete_or_stale_marks(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}, "rollback_drawdown_pct": 5})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        self.lab.apply(proposal["id"])
        for key in ("missing_marks", "stale_marks"):
            snapshot = trading.snapshot()
            snapshot["books"][0]["account"]["drawdown_percent"] = 6
            snapshot["books"][0]["account"][key] = 1
            self.lab.operate(snapshot)
            self.assertEqual(self.lab.proposal_get(proposal["id"])["status"], "observing")
            self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 1)

    def test_rollback_recovers_committed_policy_without_replacing_later_operator_update(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        self.lab.apply(proposal["id"])
        with patch.object(self.lab, "_finish_rollback", side_effect=RuntimeError("process interrupted after policy commit")):
            with self.assertRaises(RuntimeError):
                self.lab.rollback(proposal["id"], "Restore measured policy")
        self.assertEqual(self.lab.proposal_get(proposal["id"])["status"], "rolling_back")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 0)
        trading.set_book("main", {"policy": {"fees_per_order": 2}})
        reopened = Lab(Store(self.store.path))
        reopened.bind(trading)
        reopened.operate(trading.snapshot())
        reopened.operate(trading.snapshot())
        result = reopened.proposal_get(proposal["id"])
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 2)
        self.assertEqual(len([d for d in result["decisions"] if d["decision"] == "rollback"]), 1)

    def test_rollback_response_error_recovers_its_committed_restore_without_replaying(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee trial", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        self.lab.apply(proposal["id"])
        original = trading.set_book
        def failed_read_after_restore(*args, **kwargs):
            original(*args, **kwargs)
            original("main", {"policy": {"fees_per_order": 2}})
            raise DeskError("Read failed after the restoration committed", 503)
        with patch.object(trading, "set_book", side_effect=failed_read_after_restore):
            result = self.lab.rollback(proposal["id"], "Restore the trial")
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(len([d for d in result["decisions"] if d["decision"] == "rollback"]), 1)
        version = trading.snapshot()["books"][0]["policy_version"]
        self.lab.rollback(proposal["id"], "Idempotent retry")
        self.assertEqual(trading.snapshot()["books"][0]["policy_version"], version)
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 2)

    def test_applied_policy_is_recovered_from_its_exact_actor_after_interruption(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        self.lab.apply(proposal["id"])
        with self.store.transaction() as con:
            con.execute("UPDATE lab_proposals SET status='applying',applied_policy_hash=NULL WHERE id=?", (proposal["id"],))
        self.lab.operate(trading.snapshot())
        recovered = self.lab.proposal_get(proposal["id"])
        self.assertEqual(recovered["status"], "observing")
        self.assertEqual(recovered["applied_policy_hash"], trading.snapshot()["books"][0]["policy_hash"])

    def test_observer_cannot_reset_active_apply_or_overwrite_concurrent_rollback(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 1}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        original = trading.set_book
        def interleaved(*args, **kwargs):
            self.lab.operate(trading.snapshot())
            self.assertEqual(self.lab.proposal_get(proposal["id"])["status"], "applying")
            changed = original(*args, **kwargs)
            self.lab.operate(trading.snapshot())
            self.lab.rollback(proposal["id"], "Operator restores during application handoff")
            return changed
        with patch.object(trading, "set_book", side_effect=interleaved):
            # Rollback itself needs the original method rather than recursion.
            def guarded(*args, **kwargs):
                return interleaved(*args, **kwargs) if kwargs.get("actor", "").startswith("proposal:") else original(*args, **kwargs)
            trading.set_book.side_effect = guarded
            result = self.lab.apply(proposal["id"])
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 0)

    def test_expired_apply_token_cannot_change_policy_after_rollback_decision(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 2}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        original = trading.set_book
        def expired_worker(*args, **kwargs):
            with self.store.transaction() as con:
                con.execute("UPDATE lab_proposals SET stage_until=0 WHERE id=?", (proposal["id"],))
            self.lab.operate(trading.snapshot())
            self.assertEqual(self.lab.proposal_get(proposal["id"])["status"], "approved")
            self.lab.rollback(proposal["id"], "Cancel expired application")
            return original(*args, **kwargs)
        with patch.object(trading, "set_book", side_effect=expired_worker):
            with self.assertRaises(DeskError):
                self.lab.apply(proposal["id"])
        self.assertEqual(self.lab.proposal_get(proposal["id"])["status"], "rolled_back")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 0)

    def test_stale_observer_preserves_a_fresh_application_token(self):
        trading = TradingDesk(self.store)
        self.lab.bind(trading)
        proposal = self.lab.proposal({"title": "Fee model", "rationale": "Measure", "evidence": "Receipts", "book_id": "main", "policy_patch": {"fees_per_order": 2}})
        self.lab.decision(proposal["id"], "approved", "Trial approved")
        original_transaction = self.store.transaction
        with original_transaction() as con:
            con.execute("UPDATE lab_proposals SET status='applying',stage_until=0,stage_token='expired-token' WHERE id=?", (proposal["id"],))
        replaced = False
        @contextmanager
        def concurrent_replacement():
            nonlocal replaced
            # This interleaves after the observer reads its expired row and
            # before its recovery transaction. Another observer has recovered
            # that row and a fresh explicit apply now owns a different token.
            if not replaced:
                replaced = True
                with original_transaction() as con:
                    con.execute("UPDATE lab_proposals SET status='applying',stage_until=9999999999,stage_token='fresh-token' WHERE id=?", (proposal["id"],))
            with original_transaction() as con:
                yield con
        with patch.object(self.store, "transaction", concurrent_replacement):
            self.lab._observe_proposals(trading.snapshot()["books"])
        result = self.lab.proposal_get(proposal["id"])
        self.assertEqual(result["status"], "applying")
        self.assertEqual(result["stage_token"], "fresh-token")
        self.assertEqual(trading.snapshot()["books"][0]["policy"]["fees_per_order"], 0)

    def test_completed_agent_review_preserves_one_artifact_and_one_message(self):
        task = {"id": "test-task", "title": "Source review"}
        with self.store.transaction() as con:
            self.lab.record_agent_review(con, task, "Source receipt abc: no claim of edge")
            self.lab.record_agent_review(con, task, "Source receipt abc: no claim of edge")
        data = self.lab.snapshot()
        self.assertEqual(data["inbox_total"], 1)
        self.assertEqual(len(data["artifacts"]), 1)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "desk.sqlite")

    def tearDown(self):
        self.tmp.cleanup()

    def test_native_fetch_uses_bounded_redirect_aware_transport_and_preserves_injection(self):
        research = Research(self.store)
        with patch("backend.research.bounded_http", return_value=(200, b"Source receipt")) as request:
            self.assertEqual(research._fetch("https://fixture.invalid/source", {"User-Agent": "fixture-contact"}), b"Source receipt")
            self.assertEqual(request.call_args.args, ("GET", "https://fixture.invalid/source"))
            self.assertEqual(request.call_args.kwargs["headers"]["User-Agent"], "fixture-contact")
            self.assertEqual(request.call_args.kwargs["timeout_seconds"], 8)
            self.assertEqual(request.call_args.kwargs["maximum_bytes"], 2_000_000)
            self.assertTrue(request.call_args.kwargs["follow_redirects"])
        with patch("backend.research.bounded_http", return_value=(429, b"Private provider response")):
            with self.assertRaisesRegex(RuntimeError, "unsuccessful HTTP status") as failed:
                research._fetch("https://fixture.invalid/source")
            self.assertNotIn("Private", str(failed.exception))
        research.transport = lambda url, headers: b"Injected source receipt"
        with patch("backend.research.bounded_http") as request:
            self.assertEqual(research._fetch("https://fixture.invalid/source"), b"Injected source receipt")
            request.assert_not_called()

    def test_source_times_hashes_and_repeated_collection_are_preserved(self):
        feed = b'<rss><channel><item><title>Company releases results</title><link>https://example.org/a</link><pubDate>Wed, 07 Oct 2026 20:00:00 GMT</pubDate><description>Source text</description></item></channel></rss>'
        research = Research(self.store, transport=lambda url, headers: feed)
        research.sec_user_agent = ""
        research.collect(["AAPL"], force=True)
        research.collect(["AAPL"], force=True)
        data = research.snapshot()
        self.assertEqual(data["receipt_count"], 1)
        self.assertEqual(data["receipts"][0]["source_time"], "2026-10-07T20:00:00+00:00")
        self.assertEqual(data["receipts"][0]["payload"]["title"], "Company releases results")
        self.assertEqual(data["trade_decisions"], 0)
        self.assertEqual(self.store.snapshot({})["orders"], [])

    def test_source_failure_does_not_fabricate_receipts_or_success(self):
        research = Research(self.store, transport=lambda url, headers: b"<html>Blocked</html>")
        research.sec_user_agent = ""
        result = research.collect(["MSFT"], force=True)
        self.assertTrue(result["results"][0]["errors"])
        self.assertEqual(research.snapshot()["receipt_count"], 0)
        self.assertIsNone(research.snapshot()["collections"][0]["last_success"])

    def test_accepted_atom_feed_retains_alternate_link_published_time_and_hash(self):
        feed = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Issuer report</title><link rel="self" href="https://example.org/feed-entry"/><link rel="alternate" href="https://example.org/report"/><published>2026-10-07T16:00:00-04:00</published><summary>Source statement</summary></entry></feed>'
        research = Research(self.store, transport=lambda url, headers: feed)
        research.sec_user_agent = ""
        research.collect(["AAPL"], force=True)
        research.collect(["AAPL"], force=True)
        snapshot = research.snapshot()
        self.assertEqual(snapshot["receipt_count"], 1)
        receipt = snapshot["receipts"][0]
        self.assertEqual(receipt["source_time"], "2026-10-07T20:00:00+00:00")
        self.assertEqual(receipt["payload"]["url"], "https://example.org/report")
        self.assertEqual(receipt["payload"]["summary"], "Source statement")
        raw = json.dumps(receipt["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        self.assertEqual(receipt["sha256"], hashlib.sha256(raw).hexdigest())

    def test_sec_source_identity_and_accession_are_stored(self):
        def fetch(url, headers):
            self.assertEqual(headers["User-Agent"], "test-contact")
            if "company_tickers" in url:
                return json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}).encode()
            return json.dumps({"name": "Apple", "filings": {"recent": {"accessionNumber": ["0000320193-26-000001"], "filingDate": ["2026-10-07"], "reportDate": ["2026-09-30"], "acceptanceDateTime": ["2026-10-07T20:00:00Z"], "form": ["10-Q"], "primaryDocument": ["aapl.htm"]}}}).encode()
        research = Research(self.store, transport=fetch)
        research.sec_user_agent = "test-contact"
        self.assertEqual(research.filings("AAPL")["status"], "collected")
        receipt = research.snapshot()["receipts"][0]
        self.assertEqual(receipt["payload"]["form"], "10-Q")
        self.assertIn("000032019326000001/aapl.htm", receipt["payload"]["url"])


if __name__ == "__main__":
    unittest.main()
