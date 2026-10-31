"""Regression blockers for the 2026-10-30 publication cures
(FIX STREAM 2: item 3.1.8 remainder R-31, Engine 12 remainders
R-14/R-15/R-26, FE04 fair gap R-16, FE23 R-27).

Fail directions, each against the pre-cure tree:
- fetch_earnings_calendar.parse_day_payload kept only the symbol
  and discarded the time class, EPS forecast and estimate count
  the source already returns; earnings_record.parse_day_rows
  keeps them (the module did not exist pre-cure).
- No standardized surprise record existed; earnings_record
  .standardized_surprise computes the analyst forecast error SUE
  form and refuses below 4 prior errors.
- No per name priced move record existed; the record on disk now
  carries priced moves counted from it, and priced_moves.py
  exists.
- No fair gap model existed; fair_gap_model.py exists and its
  record decomposes a session's gaps.
- No Form 4 footnote record existed; form4_footnotes
  .parse_form4 resolves footnote ids to text and the labelled
  set measures classifier precision.
- Engine 28's acceptance was a daily proxy only;
  first_minutes.acceptance computes the first 15 minute form and
  refresh_gapdestiny consumes the record.
"""
import importlib.util
import json
import os

LINEUP = os.path.expanduser("~/workspace/terminal-lineup")
SITE = os.path.join(LINEUP, "site")


def _load(name):
    path = os.path.join(SITE, name)
    spec = importlib.util.spec_from_file_location(
        name.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_earnings_record_keeps_full_rows():
    mod = _load("earnings_record.py")
    doc = {"data": {"rows": [{
        "symbol": "AMZN", "time": "time-after-hours",
        "eps": "$1.89", "epsForecast": "$2.01",
        "surprise": "-5.97", "noOfEsts": "14",
        "fiscalQuarterEnding": "Sep/2026"}]}}
    rows = mod.parse_day_rows(doc, "2026-10-29")
    assert rows[0]["eps_actual"] == 1.89
    assert rows[0]["eps_forecast"] == 2.01
    assert rows[0]["time_class"] == "time-after-hours"
    assert rows[0]["no_of_ests"] == 14
    assert mod.timing_quality("time-after-hours") == 1.0
    assert mod.timing_quality("time-not-supplied") == 0.5


def test_standardized_surprise_form_and_floor():
    mod = _load("earnings_record.py")
    reports = [{"eps_actual": a, "eps_forecast": f}
               for a, f in [(1.0, 1.0), (1.2, 1.0), (0.8, 1.0),
                            (1.1, 1.0), (0.9, 1.0), (1.5, 1.0)]]
    out = mod.standardized_surprise(reports)
    assert out["state"] == "recorded"
    assert out["sue_z"] is not None and out["sue_z"] > 1.0
    thin = mod.standardized_surprise(reports[:3])
    assert thin["state"] == "not_recorded"


def test_earnings_record_on_disk():
    with open(os.path.join(SITE, "earnings-record",
                           "record.json"), encoding="utf-8") as fh:
        rec = json.load(fh)
    assert rec["names_with_reports"] > 0
    assert rec["names_with_timing"] > 0


def test_priced_moves_record_on_disk():
    with open(os.path.join(SITE, "earnings-record",
                           "priced_moves.json"),
              encoding="utf-8") as fh:
        rec = json.load(fh)
    assert rec["priced_moves_on_record"] > 0
    for name in rec["names"].values():
        assert name["priced_move_pct"] > 0
        assert name["quotes"]


def test_first_minutes_acceptance_form():
    mod = _load("first_minutes.py")
    bars = [(100.0, 102.0, 99.0, 101.0),
            (101.0, 103.0, 100.0, 102.0),
            (102.0, 102.5, 99.5, 99.8)]
    acc = mod.acceptance(bars, True)
    assert acc is not None and acc < 0.5
    assert mod.acceptance(bars[:2], True) is None
    with open(os.path.join(SITE, "gap-destiny", "first_minutes",
                           "record.json"), encoding="utf-8") as fh:
        rec = json.load(fh)
    assert rec["names_recorded"] > 1000


def test_gapdestiny_consumes_first_minutes():
    with open(os.path.join(SITE, "refresh_gapdestiny.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert "first_minutes_acceptance" in src
    assert "acceptance_source" in src
    assert "is not on " in src or "not on this record" not in src


def test_form4_parse_and_labels():
    mod = _load("form4_footnotes.py")
    xml = b"""<ownershipDocument><footnotes>
      <footnote id="F1">The shares were sold pursuant to a Rule
      10b5-1 trading plan adopted on March 1, 2026.</footnote>
      </footnotes>
      <nonDerivativeTable><nonDerivativeTransaction>
      <transactionCoding><transactionCode>S</transactionCode>
      </transactionCoding>
      <footnoteId id="F1"/></nonDerivativeTransaction>
      </nonDerivativeTable></ownershipDocument>"""
    parsed = mod.parse_form4(xml)
    assert parsed["transactions"][0]["footnote_texts"]
    assert "10b5-1" in parsed["transactions"][0]["footnote_texts"][0]
    assert mod.label_for(
        parsed["transactions"][0]["footnote_texts"][0]) \
        == "plan_10b5_1"
    assert mod.label_for("Ordinary footnote text.") \
        == "discretionary"


def test_form4_record_on_disk():
    with open(os.path.join(SITE, "insider-divergence",
                           "footnotes", "record.json"),
              encoding="utf-8") as fh:
        rec = json.load(fh)
    assert rec["filings_on_record"] > 0
    assert rec["names_with_classified_transactions"] > 0
    assert rec["labelled_footnotes"] >= 20


def test_fair_gap_model_and_record():
    assert os.path.exists(os.path.join(SITE, "fair_gap_model.py"))
    with open(os.path.join(SITE, "gap-destiny",
                           "fair_gap_record.json"),
              encoding="utf-8") as fh:
        rec = json.load(fh)
    assert rec["counts"]["gap_names"] > 1000
    assert rec["counts"]["market_leg"] > 1000
    sample = next(iter(rec["names"].values()))
    assert sample["residual_gap_pct"] is not None
    assert sample["market_leg_pct"] is not None


def test_earningsdistribution_consumes_records():
    with open(os.path.join(SITE, "refresh_earningsdistribution.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert "EARNINGS_RECORD_PATH" in src
    assert "PRICED_MOVES_PATH" in src
    assert "_fe04_page_block" in src
    with open(os.path.join(SITE, "earnings-distribution",
                           "data.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["calendar"]["priced_moves_on_record"] > 0
    assert data["fe04_fair_gap_remainder"]["state"] \
        == "recorded_market_sector"
    assert data["fe18_pead"]["surprise_recorded_names"] > 0


def test_insider_page_classified():
    with open(os.path.join(SITE, "insider-divergence",
                           "data.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    block = data["plan_adjustment"]
    assert block["names_classified"] > 0
    assert block["precision"]["labelled"] >= 20
