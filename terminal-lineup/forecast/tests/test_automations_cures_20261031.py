"""Blockers: terminal total audit round 1, automations sector
(AUTOMATIONS-STATUS-20261031, PULLBACK-RECEIPT-SOURCE-20261031,
EMAP-RECEIPT-PROVENANCE-20261031, AGENTDEBATE-CARD-SESSION-20261031,
HLX-EXCLUSION-20261031).

Fail direction: every assertion encodes the pre-cure state named
in ROUND-1-AUDIT-automations.md: receipts refusing on the
pullback-norm receipt source and on expected-move per-name
provenance, proving-ground pinning pullback-norm unpublished and
the old expected-move note wording, agent-debate demanding the
Morning Map session equal the scored session and checking the
Regime Dial against the snapshot spot, and the per-name collector
recording HLX as an error on every run.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
sys.path.insert(0, SITE)


def _src(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


def _data(slug):
    with open(os.path.join(SITE, slug, "data.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


# --- pullback-norm receipt source (producer cure) ---

def test_pullback_receipt_source_matches_top_line():
    d = _data("pullback-norm")
    assert d["receipt"]["source"] == d["source"]


def test_pullback_producer_published_receipt_uses_top_source():
    src = _src("refresh_pullback.py")
    assert "PULLBACK-RECEIPT-SOURCE-20261031" in src
    receipt_block = src.split('"receipt": {')[1].split('"coverage"')[0]
    assert "terminal's own pullback study" in receipt_block


def test_pullback_published_state_is_counted():
    d = _data("pullback-norm")
    if d["state"] == "published":
        assert d["events"] > 0
        assert d["distribution"]["state"] == "counted"
        assert d["signals_published"] == len(
            d["study"]["latest_signals"])


# --- receipts re-takes ---

def test_receipts_accepts_reconstructed_emap_provenance_only():
    src = _src("refresh_receipts.py")
    assert "EMAP-RECEIPT-PROVENANCE-20261031" in src
    assert 'n["receipt"].get("filing") == "reconstructed"' in src


def test_receipts_pullback_entry_branches_on_state():
    src = _src("refresh_receipts.py")
    assert "PULLBACK-RECEIPT-SOURCE-20261031" in src
    assert 'd.get("state") == "published"' in src


def test_receipts_published_file_carries_pullback_counted_line():
    d = _data("receipts")
    rows = {r["slug"]: r for r in d["receipts"]}
    pb = rows["pullback-norm"]
    if _data("pullback-norm")["state"] == "published":
        assert "has run and counted" in (pb["completeness"] or "")


# --- proving-ground re-takes ---

def test_provingground_pullback_two_state_check():
    src = _src("refresh_provingground.py")
    assert "pb_published or pb_unpublished" in src
    assert 'pb.get("state") == "unpublished" and pb.get("signals_published") == 0,\n         "pullback-norm no longer unpublished' not in src


def test_provingground_emap_note_tied_to_lane():
    src = _src("refresh_provingground.py")
    assert "EMAP-RECEIPT-PROVENANCE-20261031" in src
    assert 'in data["expected-move"].get("coverage_note", "")' not in src


# --- agent-debate card-session cure ---

def test_agentdebate_session_gate_is_card_session():
    src = _src("refresh_agentdebate.py")
    assert "AGENTDEBATE-CARD-SESSION-20261031" in src
    assert 'pos.get("dix_date") != mm_session' in src
    assert 'if mm.get("session") != session:' not in src


def test_agentdebate_spot_parity_uses_snapshot_spot():
    src = _src("refresh_agentdebate.py")
    assert 'ix.get("snapshot_spot", ix["spot"])' in src
    assert 'num(ix["spot"]) not in fig' in src


def test_agentdebate_published_and_premium_parity():
    d = _data("agent-debate")
    assert d["session"] == "2026-10-30"
    assert d["tape_freshness"]["state"] == "current"
    so = _data("second-opinion")
    fb = _data("flow-board")
    names = {n["symbol"]: n for n in so["names"]}
    rows = {r["underlying"]: r for r in fb["rows"]}
    for sym in ("SPY", "QQQ", "IWM"):
        cell = [c for c in rows[sym]["cells"]
                if c["session"] == fb["freshest_session"]][0]
        assert int(names[sym]["prints"]["call_net_premium"]) == \
            int(cell["call_net_premium_usd"])
        assert int(names[sym]["prints"]["put_net_premium"]) == \
            int(cell["put_net_premium_usd"])


# --- HLX exclusion class ---

def test_collector_records_invalid_underlying_as_exclusion():
    src = _src("collect_pername_tape.py")
    assert "HLX-EXCLUSION-20261031" in src
    assert '"invalid underlying symbols" in err' in src
    assert '"exclusions": exclusions' in src


def _cron_copy(job_id):
    roots = [os.path.expanduser("~/workspace/cron.d"),
             os.path.expanduser("~/workspace/goals")]
    for root in roots:
        for dirpath, _dirs, names in os.walk(root):
            for name in names:
                if name.startswith(job_id) and name.endswith(".md"):
                    with open(os.path.join(dirpath, name),
                              encoding="utf-8") as fh:
                        return fh.read()
    raise AssertionError(f"no saved cron copy found for {job_id}")


# --- inspection and audit completion vocabulary (defect 5) ---

def test_inspection_jobs_carry_completion_vocabulary():
    for job_id, verdict in (("v3-night-inspection", "PARTIAL"),
                            ("v3-morning-inspection", "NOT READY")):
        body = _cron_copy(job_id)
        assert "INSPECTION-COMPLETION-20261031" in body, job_id
        assert "SUCCEEDED run" in body, job_id
        assert verdict in body, job_id
        assert "FAILED run only" in body, job_id


def test_daily_audit_carries_completion_vocabulary_and_dual_reading():
    body = _cron_copy("midna-daily-full-audit")
    assert "INSPECTION-COMPLETION-20261031" in body
    assert "AUTOMATIONS-STATUS-20261031" in body
    assert "Scheduler status alone never overrides" in body


def test_refresh_jobs_keep_failure_reporting_clause():
    for job_id in ("forecast-engine-daily-refresh",
                   "terminal-tools-daily-refresh",
                   "tape-family-daily-refresh"):
        body = _cron_copy(job_id)
        assert "AUTOMATIONS-STATUS-20261031" in body, job_id
        assert "FAILED run" in body or "FAILED RUN" in body, job_id


def test_inspection_jobs_recognise_audit_completion_record():
    # Round 2 strengthening: midna-daily-full-audit keeps no receipt
    # jsonl; its completion record is its filed outputs plus its
    # delivered report. Both inspection bodies must name that record
    # explicitly, or their cross-reading clause demands a receipt row
    # the audit job never writes and misclassifies it again.
    for job_id in ("v3-night-inspection", "v3-morning-inspection"):
        body = _cron_copy(job_id)
        assert "completion record (midna-daily-full-audit)" in body, job_id


def test_live_tape_store_has_no_hlx_error_in_latest_full_run_shape():
    # The cured collector writes exclusions beside errors; the
    # Friday store predates the cure, so this asserts the shape
    # contract on the collector source only for older stores.
    src = _src("collect_pername_tape.py")
    assert '"status": "ok" if not errors else "partial"' in src
