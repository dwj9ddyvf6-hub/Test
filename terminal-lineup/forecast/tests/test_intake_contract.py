"""Regression blockers for the intake contracts (2026-10-29):
anti fixture source rejection (DEEP-PASS 3.1 item 4) and the
evidence CSV intake contract (3.1 item 5).

Run in the existing forecast test setup:
    python3 -m pytest tests/ -q        (from forecast/)
Fail direction: every test here imports site/intake.py, which did
not exist before this adoption, so the whole file fails pre-fix.
"""

import importlib.util
import os

import pytest

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


intake = _load("intake", "intake.py")

GOOD = ("ObservedAt,Entity,Source,Metric,Value\n"
        "2026-10-29T14:00:00Z,SPY,exchange-tape,close,601.25\n")


# ---- anti fixture rejection -------------------------------------------

@pytest.mark.parametrize("label", ["synthetic", "SYNTHETIC SAMPLE",
                                   "fixture", "Fixture_v2", "sample"])
def test_fixture_source_labels_are_refused(label):
    assert intake.is_fixture_source(label)


@pytest.mark.parametrize("label", ["exchange-tape", "Alpaca SIP",
                                   "sampleson & co", "SEC EDGAR", None, ""])
def test_real_source_labels_pass(label):
    assert not intake.is_fixture_source(label)


def test_guarded_reader_refuses_fixture_row_and_names_line():
    text = "date,close,source\n2026-10-29,10,fixture\n"
    with pytest.raises(intake.IntakeError) as exc:
        intake.read_csv_dicts_guarded(text)
    assert "row 2" in str(exc.value)
    assert "not accepted as market input" in str(exc.value)


def test_guarded_reader_accepts_clean_rows_and_caps():
    rows = intake.read_csv_dicts_guarded("date,close\n2026-10-29,10\n")
    assert rows == [{"date": "2026-10-29", "close": "10"}]
    with pytest.raises(intake.IntakeError):
        intake.read_csv_dicts_guarded(b"x" * (intake.MAX_BYTES + 1))
    with pytest.raises(intake.IntakeError):
        intake.read_csv_dicts_guarded("a\n" + "1\n" * (intake.MAX_ROWS + 1))


def test_pinorescape_loader_is_wired_to_the_guard():
    src = open(os.path.join(SITE, "refresh_pinorescape.py")).read()
    assert "read_csv_dicts_guarded" in src
    assert "csv.DictReader" not in src


# ---- evidence CSV contract ---------------------------------------------

def test_evidence_good_row_accepted_with_three_clocks():
    text = ("ObservedAt,PublicAt,ReceivedAt,Entity,Source,Metric,Value,"
            "Unit,Confidence,SourceURL\n"
            "2026-10-29T14:00:00Z,2026-10-29T14:01:00Z,"
            "2026-10-29T14:02:00Z,SPY,exchange-tape,close,601.25,"
            "USD,0.9,https://example.com/feed\n")
    out = intake.parse_evidence_csv(text)
    assert out["accepted_count"] == 1 and out["rejected_count"] == 0
    row = out["accepted"][0]
    assert row["ObservedAt"] == "2026-10-29T14:00:00Z"
    assert row["PublicAt"] == "2026-10-29T14:01:00Z"
    assert row["ReceivedAt"] == "2026-10-29T14:02:00Z"
    assert row["Method"] is None  # absent stays null, never invented


def test_evidence_unknown_and_duplicate_columns_refuse_whole_file():
    with pytest.raises(intake.IntakeError):
        intake.parse_evidence_csv(GOOD.replace("Value", "Value,Bogus"))
    with pytest.raises(intake.IntakeError):
        intake.parse_evidence_csv(
            "ObservedAt,observed_at,Entity,Source,Metric,Value\n"
            "2026-10-29T14:00:00Z,x,SPY,s,m,1\n")
    with pytest.raises(intake.IntakeError):
        intake.parse_evidence_csv("Entity,Source,Metric,Value\nSPY,s,m,1\n")


def test_evidence_per_row_rejections_carry_line_and_reason():
    text = ("ObservedAt,Entity,Source,Metric,Value,Confidence,SourceURL\n"
            "2026-10-29T14:00:00Z,SPY,tape,close,1,0.5,\n"
            "not-a-time,SPY,tape,close,1,0.5,\n"
            "2026-10-29T14:00:00Z,,tape,close,1,0.5,\n"
            "2026-10-29T14:00:00Z,SPY,synthetic,close,1,0.5,\n"
            "2026-10-29T14:00:00Z,SPY,tape,close,1,1.5,\n"
            "2026-10-29T14:00:00Z,SPY,tape,close,1,0.5,ftp://x/y\n")
    out = intake.parse_evidence_csv(text)
    assert out["accepted_count"] == 1
    assert out["rejected_count"] == 5
    reasons = {r["line"]: r["reason"] for r in out["rejected"]}
    assert reasons[3] == "invalid_timestamp:ObservedAt"
    assert reasons[4] == "missing_required:Entity"
    assert reasons[5] == "fixture_source"
    assert reasons[6] == "invalid_confidence"
    assert reasons[7] == "invalid_source_url"
    # nothing silently dropped: accepted plus rejected is every row
    assert out["accepted_count"] + out["rejected_count"] == 6


def test_evidence_caps_and_field_length():
    big_field = "x" * (intake.MAX_FIELD_CHARS + 1)
    with pytest.raises(intake.IntakeError):
        intake.parse_evidence_csv(
            "ObservedAt,Entity,Source,Metric,Value\n"
            f"2026-10-29T14:00:00Z,SPY,tape,close,{big_field}\n")
