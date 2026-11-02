"""Regression blockers for WEEK-READINESS-20261102 terminal cures.

Classes covered:
1. Proving Ground hub check (refresh_provingground.py): the hub
   card grid must list each tool exactly once, but featured tiles
   and the Needs Attention monitor link tools again by design.
   The pre-cure check counted every href on the page and refused
   every run (exit 1, "hub links a tool more than once", proven
   live 2026-11-02 before the cure).
2. Filings Wire reading date: the page's canonical as_of is its
   checked date, not the freshest filing inside the collection.
3. Skew Lens reading date: as_of is the modelled freshest date
   when modelled figures exist (the live arm), not the retired
   recorded ledger's freshest date.
4. Hub static-study class: grade-a-board and decay-watch carry
   subject/event dates, never a session Stale chip.
"""
import importlib.util
import json
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parents[2] / "site"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SITE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_provingground_counts_card_grid_only():
    pg = _load("refresh_provingground")
    hub = (
        '<div class="vftile"><h3><a href="alpha/">Alpha</a></h3></div>'
        '<article class="hubcard"><h3><a href="alpha/">Alpha</a></h3></article>'
        '<article class="hubcard"><h3><a href="beta/">Beta</a></h3></article>'
        '<ul class="exceptionlist"><li><a href="beta/">Beta</a></li></ul>')
    links = pg.hub_card_links(hub)
    assert links == ["alpha", "beta"]
    assert len(links) == len(set(links))


def test_provingground_detects_duplicate_card():
    pg = _load("refresh_provingground")
    hub = (
        '<article class="hubcard"><h3><a href="alpha/">A</a></h3></article>'
        '<article class="hubcard"><h3><a href="alpha/">A2</a></h3></article>')
    links = pg.hub_card_links(hub)
    assert len(links) != len(set(links))


def test_provingground_main_uses_card_grid():
    src = (SITE / "refresh_provingground.py").read_text()
    assert "hub_card_links(hub)" in src
    assert 'hub_links = re.findall(r\'href="([a-z0-9-]+)/", hub)' not in src


def test_live_hub_card_grid_unique_and_covers_classification():
    pg = _load("refresh_provingground")
    hub = (SITE / "index.html").read_text()
    links = pg.hub_card_links(hub)
    assert len(links) == len(set(links))
    classified = {slug for _, slug, _, _ in pg.TOOLS}
    assert classified <= set(links)


def test_filings_producer_stamps_checked_as_as_of():
    src = (SITE / "refresh_filings.py").read_text()
    assert src.count('"as_of": as_of') == 2  # both published states


def test_skewlens_producer_stamps_live_arm_as_of():
    src = (SITE / "refresh_skewlens.py").read_text()
    assert '"as_of": (modelled["freshest_date"] if modelled["figures"]' in src


def test_filings_live_reading_date_is_checked_date():
    data = json.loads((SITE / "filings-wire" / "data.json").read_text())
    assert data["as_of"] == data["checked"]


def test_skewlens_live_reading_date_is_modelled_date():
    data = json.loads((SITE / "skew-lens" / "data.json").read_text())
    if data["modelled_figures"]:
        assert data["as_of"] == data["modelled_freshest_date"]


def test_hub_static_study_class_includes_finished_studies():
    src = (SITE / "refresh_hub.py").read_text()
    m = re.search(r"STATIC_STUDY = \{(.*?)\}", src, re.S)
    assert m and '"grade-a-board"' in m.group(1)
    assert '"decay-watch"' in m.group(1)
