"""Freshness blocker (FRESHNESS-CURE-20261031, spec 14.3.6 / A1).

Before this cure the terminal had four disagreeing freshness fields
and live.js measured the data file's Last-Modified stamp, which
enrich_all.py rewrites hourly, so a stale reading was drawn as
current on every page. These tests fail on the pre-cure tree (no
freshness.py, live.js labelled "Updated <file clock>", refresh_hub
used its own field order and never inserted a missing date span).
"""
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
sys.path.insert(0, str(SITE))

import freshness  # noqa: E402


def test_canonical_resolver_prefers_reading_fields():
    assert freshness.reading_date({"session": "2026-10-30"}) == date(2026, 10, 30)
    assert freshness.reading_date({"as_of": "2026-10-14"}) == date(2026, 10, 14)
    assert freshness.reading_date({"freshest_date": "2026-10-14"}) == date(2026, 10, 14)
    assert freshness.reading_date({"state": {"date": "2026-10-31"}}) == date(2026, 10, 31)
    assert freshness.reading_date({"record_surface": {
        "current_reading": {"as_of": "2026-10-29"}}}) == date(2026, 10, 29)
    assert freshness.reading_date({"tool": "x"}) is None


def test_series_start_in_as_of_field_is_not_a_reading_date():
    data = {"as_of": "2000-03-01", "generated_at": "2026-10-31T16:43:34+00:00"}
    assert freshness.reading_date(data) == date(2026, 10, 31)


def test_live_js_reads_reading_date_never_file_clock():
    live = (SITE / "live.js").read_text(encoding="utf-8")
    assert "Reading as of " in live
    assert "readingDateOf" in live
    assert "fp: hash(text)" in live  # fingerprint is content, not LM
    builder = (SITE / "build_live_js.py").read_text(encoding="utf-8")
    assert "readingDateOf" in builder  # regeneration preserves the cure


def test_visual_kit_session_mirrors_canonical_order():
    visual = (SITE / "visual.js").read_text(encoding="utf-8")
    assert "freshest_date" in visual and "scored_run_session" in visual
    assert "current_reading" in visual


def test_hub_staleness_is_cadence_aware_and_shares_resolver():
    src = (SITE / "refresh_hub.py").read_text(encoding="utf-8")
    assert "freshness" in src and "is_stale" in src
    assert "No reading date" in src  # dateless cards say so plainly
    sys.path.insert(0, str(SITE))
    import importlib
    hub = importlib.import_module("refresh_hub")
    latest = date(2026, 10, 30)
    assert hub.is_stale("touch-surface", date(2026, 10, 29), latest)
    assert not hub.is_stale("touch-surface", date(2026, 10, 30), latest)
    assert not hub.is_stale("filings-wire", date(2026, 10, 25), latest)
    assert hub.is_stale("filings-wire", date(2026, 10, 15), latest)
    assert not hub.is_stale("graveyard", date(2020, 1, 1), latest)
    assert not hub.is_stale("13f-tracker", date(2026, 6, 30), latest)


def test_enrich_does_not_restamp_unchanged_files(tmp_path):
    import record_surface
    page = tmp_path / "demo-page"
    page.mkdir()
    data = page / "data.json"
    data.write_text(json.dumps({"tool": "demo", "session": "2026-10-30"}))
    record_surface.enrich_file(data)
    record_surface.enrich_file(data)  # steady state reached
    first = data.stat().st_mtime_ns
    record_surface.enrich_file(data)
    assert data.stat().st_mtime_ns == first  # no hourly mtime churn


def test_every_hub_card_prints_a_date_beside_its_chip():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<article class="hubcard".*?</article>', hub, re.S)
    assert len(cards) >= 90
    missing = [c[:60] for c in cards if 'class="updated"' not in c]
    assert not missing, f"dateless hub cards remain: {missing}"


def test_stale_daily_pages_are_chipped_stale_on_hub():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    cards = {}
    for c in re.findall(r'<article class="hubcard".*?</article>', hub, re.S):
        m = re.search(r'href="([a-z0-9-]+)/"', c)
        if m:
            cards[m.group(1)] = c
    import importlib
    hub_mod = importlib.import_module("refresh_hub")
    latest = hub_mod.latest_completed_session(date.today())
    offenders = []
    for slug, card in cards.items():
        path = SITE / slug / "data.json"
        if not path.exists() or slug in hub_mod.NO_DATA:
            continue
        try:
            d = freshness.reading_date(json.loads(path.read_text()))
        except Exception:
            continue
        if d is None:
            continue
        if hub_mod.is_stale(slug, d, latest) and 'chip stale' not in card:
            offenders.append(slug)
    assert not offenders, f"stale pages not chipped stale: {offenders}"


def test_no_hub_card_carries_both_a_date_and_the_dateless_span():
    # Regression blocker, HUB-DUAL-LABEL-20261031: a card whose page
    # gained a reading date kept the "No reading date on record" span
    # an earlier run had inserted, so 9 cards printed a true As-of
    # date beside a claim that no date exists. The generator now
    # replaces the dateless span when a date resolves.
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    bad = []
    for c in re.findall(r'<article class="hubcard".*?</article>',
                         hub, re.S):
        if "No reading date on record" in c and "As of " in c:
            m = re.search(r'href="([a-z0-9-]+)/"', c)
            bad.append(m.group(1) if m else c[:60])
    assert not bad, f"cards with contradictory date labels: {bad}"
