"""Regression blockers for the terminal health loop cure round 1,
site/rendering and book-usability class (2026-10-31).

D-R1-15: site/hub_chips.json contradicted the hub page it feeds.
It held 95 entries (49 live, 38 ungraded, 8 waiting, 0 stale)
while site/index.html printed 102 tools (50 live, 8 waiting, 35
not yet graded, 9 stale) and carded 7 tools the file omitted
(13f-tracker, greeks-sketch, odds-cards, one-page-report,
payoff-sketch, promoted-book, smart-money-tracker). Root: the
file was the hub producer's stale-recovery memory (last
non-stale chip per slug) being read as a census. Cure: the
memory moved to hub_chip_memory.json and hub_chips.json is now
the final census, regenerated from the same finished cards the
hub count line is counted from.

D-R1-23: the served terminal was down and nothing restarted it.
site/.live-server.pid named a dead PID, the port answered
nothing, and no cron or watchdog owned serve_live.py. Cure:
site/watch_serve_live.py proves the hub and a real data file by
HTTP 200, restarts the server when they do not answer, stamps
serve_live_state.json, runs at the head of every producer lane,
and has its own 15-minute cron (terminal-live-server-watchdog).
"""
import json
import re
import urllib.request
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
AUDIT_MISSING = ("13f-tracker", "greeks-sketch", "odds-cards",
                 "one-page-report", "payoff-sketch", "promoted-book",
                 "smart-money-tracker")


def hub_card_census():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    census = {}
    for card in re.findall(r'<article class="hubcard".*?</article>',
                           hub, re.S):
        slug = re.search(r'href="([a-z0-9-]+)/"', card)
        chip = re.search(r'class="chip ([a-z]+)"', card)
        assert slug and chip, "hub card without slug or chip"
        census[slug.group(1)] = chip.group(1)
    return hub, census


def test_hub_chips_file_matches_hub_card_census():
    hub, census = hub_card_census()
    assert len(census) == 102, len(census)
    chips = json.loads((SITE / "hub_chips.json").read_text(
        encoding="utf-8"))
    assert chips == census
    m = re.search(
        r"(\d+) tools in the lineup: (\d+) live, (\d+) waiting, "
        r"(\d+) not yet graded, (\d+) stale", hub)
    assert m, "hub count line not in its published form"
    total, live, waiting, ungraded, stale = (
        int(x) for x in m.groups())
    values = list(chips.values())
    assert total == len(chips)
    assert live == values.count("live")
    assert waiting == values.count("waiting")
    assert ungraded == values.count("ungraded")
    assert stale == values.count("stale")


def test_hub_chips_covers_stale_calculator_and_audit_named_cards():
    chips = json.loads((SITE / "hub_chips.json").read_text(
        encoding="utf-8"))
    for slug in AUDIT_MISSING:
        assert slug in chips, slug
    # The census carries the final chip word, Stale included: a
    # stale card is recorded stale, never as its pre-stale chip.
    _, census = hub_card_census()
    stale = [s for s, c in census.items() if c == "stale"]
    assert stale, "expected at least one stale card in this census"
    for slug in stale:
        assert chips[slug] == "stale", slug


def test_hub_producer_separates_census_from_recovery_memory():
    src = (SITE / "refresh_hub.py").read_text(encoding="utf-8")
    assert "hub_chip_memory.json" in src
    assert "hub_chips.json" in src
    # The memory is the recovery input; the census is written from
    # the finished cards, never read back as producer state.
    assert "memory_path" in src and "census_path" in src
    assert (SITE / "hub_chip_memory.json").exists()


def test_watchdog_probes_real_pages_and_restarts_server():
    src = (SITE / "watch_serve_live.py").read_text(encoding="utf-8")
    assert "index.html" in src and "morning-map/data.json" in src
    assert "serve_live.py" in src          # the restart path
    assert "serve_live_state.json" in src  # the named outcome stamp
    assert "200" in src                    # proof is HTTP 200


def test_watchdog_is_wired_into_lanes_and_its_own_cron():
    lane = (SITE / "lane_run.py").read_text(encoding="utf-8")
    assert "watch_serve_live.py" in lane
    cron_root = SITE.parents[1] / "cron.d"
    found = {p.name.split("__")[0]
             for p in cron_root.rglob("terminal-*.md")}
    assert "terminal-live-server-watchdog" in found


def test_live_server_answers_hub_and_data_with_200():
    for path in ("index.html", "morning-map/data.json"):
        req = urllib.request.Request(
            f"http://127.0.0.1:8766/{path}",
            headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200, path
    state = json.loads((SITE / "serve_live_state.json").read_text(
        encoding="utf-8"))
    assert state["up"] is True
    assert all(v == 200 for v in state["probes"].values())
