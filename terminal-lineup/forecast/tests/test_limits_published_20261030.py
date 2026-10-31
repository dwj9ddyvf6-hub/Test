"""Regression blockers for sweep stream 4 (2026-10-30):
RC-12 stated limit published, RC-09 news direction record,
RC-23 live quote capture machinery, RC-30 FE21 acceptance
timestamps. Each test fails on the pre-cure tree."""
import json
import os
import sys

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
MORGUE = os.path.expanduser("~/workspace/morgue")
sys.path.insert(0, SITE)
sys.path.insert(0, MORGUE)


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def test_sector_page_publishes_stated_limit_with_all_names():
    data = _load(os.path.join(SITE, "sector-rotation", "data.json"))
    limit = data.get("stated_limit") or {}
    assert limit.get("state") == "stated_limit"
    assert limit.get("count") == 335
    assert limit.get("found_count") == 0
    assert sorted(limit.get("routes_checked") or []) == [
        "chain_store_metadata", "edgar_company_record",
        "panel_metadata", "terminal_own_stores"]
    assert limit.get("names") == data.get("unmapped_names")
    assert len(limit["names"]) == 335
    html = open(os.path.join(SITE, "sector-rotation",
                             "index.html"), encoding="utf-8").read()
    assert "stated_limit" in html and "unmapped_names" in html


def test_sector_scan_record_evidences_four_routes():
    scan = _load(os.path.join(SITE, "sector-rotation",
                              "sector_scan_20261030.json"))
    assert scan["still_unmapped_count"] == 335
    assert scan["found_count"] == 0
    routes = scan["routes"]
    assert routes["edgar_company_record"]["fields_seen"] == [
        "cik_str", "ticker", "title"]
    assert routes["chain_store_metadata"]["sector_field_present"] \
        is False
    assert routes["panel_metadata"]["sector_field_present"] is False
    assert routes["terminal_own_stores"]["files_scanned"] >= 50


def test_news_direction_lexicon_is_signed_and_auditable():
    import news_direction as nd
    assert nd.headline_direction("Acme Beats Expectations")[0] == 1
    assert nd.headline_direction(
        "Acme Misses Expectations, Cuts Guidance")[0] == -1
    assert nd.headline_direction("Acme Holds Annual Meeting")[0] == 0
    art = nd.direct_article({"id": 1, "headline": "Acme Wins Approval",
                             "symbols": ["ACME"]})
    assert art["direction"] == 1 and art["direction_hits"]
    assert art["direction_method"] == "headline_lexicon_v1"
    again = nd.direct_article(art)
    assert again["direction"] == 1  # never relabelled


def test_news_lane_wires_direction_into_collection():
    src = open(os.path.join(MORGUE, "news_lane.py"),
               encoding="utf-8").read()
    assert "news_direction.direct_article" in src
    reg = _load(os.path.join(SITE, "..", "forecast", "registry.json"))
    e28 = [e for e in reg["engines"] if e["id"] == "engine_28"][0]
    block = e28.get("fe04_news_leg") or {}
    assert block.get("start_date") == "2026-10-30"
    assert "lookahead" in json.dumps(block).lower()
    est = _load(os.path.join(SITE, "gap-destiny",
                             "news_leg_estimation.json"))
    assert est["start_date"] == "2026-10-30"
    assert est["thresholds"]["min_pairs"] == 100


def test_live_quote_capture_parses_and_reads_fixture():
    import capture_session_quality_live as cap
    events = []
    for i in range(10):
        events.append(["ACME", 0, 100.0, 100.10, 500.0, 400.0])
        events.append(["BETA", 0, 50.0, 50.05, 300.0, 300.0])
    per = cap.parse_quote_events(events)
    per_name, session = cap.session_readings(per)
    assert session["names_with_readings"] == 2
    assert per_name["ACME"]["median_spread_share"] > 0
    assert per_name["ACME"]["depth_drop_share"] == 0.0
    src = open(os.path.join(SITE, "capture_session_quality_live.py"),
               encoding="utf-8").read()
    assert "KEEPALIVE" in src and "CHANNEL_OPENED" in src


def test_session_quality_record_names_live_capture():
    rec = _load(os.path.join(SITE, "corrected-band",
                             "session_quality_record.json"))
    assert "live_quote_capture" in rec
    assert "live quote" in rec["absent_inputs"]["spread_z"]


def test_xbrl_record_carries_acceptance_timestamps():
    rec = _load(os.path.join(SITE, "filings-wire",
                             "xbrl_record.json"))
    acc = rec.get("acceptance_timestamps") or {}
    assert acc.get("state") == "recorded_at_filing_level"
    assert acc.get("filers_with_acceptance", 0) >= 40
    assert acc.get("acceptance_filings_total", 0) >= 500
    sample = None
    for f in rec["filers_detail"]:
        if f.get("acceptance_filings"):
            sample = f["acceptance_filings"][0]
            break
    assert sample and "T" in sample["acceptance"]
    assert sample["accession"]


def test_registry_fe21_and_fe06_route_evidence():
    reg = _load(os.path.join(SITE, "..", "forecast", "registry.json"))
    qs = {q["id"]: q for q in reg["research_questions"]}
    assert "acceptance" in qs["fe21"]["route_evidence"]["carries"]
    assert "RC-12" in qs["fe06_sector_diffusion"][
        "route_evidence"]["disposition"]
    assert qs["fe19"]["route_evidence"]["wired"]["state"].startswith(
        "wired_accrual")


def test_no_em_dash_in_new_modules():
    for path in (os.path.join(SITE, "capture_session_quality_live.py"),
                 os.path.join(SITE, "scan_sector_sources.py"),
                 os.path.join(SITE, "estimate_news_leg.py"),
                 os.path.join(MORGUE, "news_direction.py")):
        text = open(path, encoding="utf-8").read()
        assert "—" not in text, path
