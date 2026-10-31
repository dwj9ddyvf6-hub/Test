"""Regression blockers for the D-HUB cure (2026-10-30): the hub page
has a producer wired into the tools chain, and the hub's headline
numbers can never again disagree with its own cards.

Defect: the hub (site/index.html) was the one terminal page with no
producer and no refresh chain; its counts, chips and as-of dates
were hand-typed and aged daily (audit 2026-10-30: refresh chain
NONE; the count line said 53 live and 9 waiting while the cards
themselves carried 54 live and 8 waiting chips).
"""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"


def test_hub_producer_exists_and_is_wired_last_into_tools_chain():
    assert (SITE / "refresh_hub.py").exists()
    runner = (SITE / "refresh_tools.py").read_text(encoding="utf-8")
    assert 'run_one("refresh_hub.py")' in runner
    # The hub refresh must run before the manifest rebuild and smoke
    # check so both see the hub's final state for the evening.
    assert (runner.index('run_one("refresh_hub.py")')
            < runner.index("verify_terminal.sh"))


def test_hub_count_line_matches_its_own_cards():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    chips = re.findall(r'class="chip ([a-z]+)"', hub)
    assert len(chips) == 100, len(chips)
    m = re.search(
        r"(\d+) tools in the lineup: (\d+) live, (\d+) waiting, "
        r"(\d+) not yet graded, (\d+) stale", hub)
    assert m, "hub count line not in its published form"
    total, live, waiting, ungraded, stale = (int(x) for x in m.groups())
    assert total == len(chips)
    assert live == chips.count("live")
    assert waiting == chips.count("waiting")
    assert ungraded == chips.count("ungraded")
    assert stale == chips.count("stale")
    meter = re.search(r"(\d+) of 100 tools live today", hub)
    assert meter and int(meter.group(1)) == live


def test_hub_has_no_em_dashes():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    assert "—" not in hub
