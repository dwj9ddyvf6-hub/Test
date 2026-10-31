"""Regression blockers for the 2026-10-30 tool visuals (build stream 2).

site/tool-visual.js maps each tool page's own data.json fields onto the
shared VisualKit primitives. These tests pin: the adapter file parses,
every build-list tool page carries the kit tags and host, every adapter
slug matches a wired page, no em dash ships, and the momentum adapter
passes its window (a missing window argument once silently emptied
every row and the page fell back to a state card).
"""
import re
import shutil
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
TOOL_PAGES = """13f-tracker activity-profile alert-tape breakout-scanner chain-explorer correlation-web dark-prints decay-watch earnings-calendar earnings-drift echo-lens expected-move expiry-pin-watch fear-day fear-day-forecaster filings-wire flow-board flow-engine flow-tape gap-fill golden-sweep-wire grade-a-board grade-my-call graveyard holly-ideas horizon-grades insider-wire iv-weather momentum-clock morning-map odds-cards one-page-report portfolio-builder promoted-book proving-ground pullback-norm receipts regime-dial replication-wire reversal-wire router sector-rotation short-volume signal-feed skew-lens smart-money-tracker squeeze-watch state-analogue static-gex strat-combos strat-scanner survivors-wire unusual-volume wall-check week-ahead watchlist-pulse""".split()
PRESERVED = """ai-chart-read breadth-meter gamma-ladder pattern-draw payoff-sketch premium-meter tape-heatmap agent-debate echo-board opening-range screener second-opinion""".split()


def test_tool_visual_parses():
    node = shutil.which("node")
    assert node
    r = subprocess.run([node, "--check", str(SITE / "tool-visual.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:400]


def test_no_emdash_in_tool_visual():
    assert "—" not in (SITE / "tool-visual.js").read_text()


def test_every_tool_page_wired():
    for slug in TOOL_PAGES:
        html = (SITE / slug / "index.html").read_text()
        assert 'href="../visual.css"' in html, slug
        assert 'src="../visual.js"' in html, slug
        assert 'src="../tool-visual.js"' in html, slug
        assert 'id="vkHost"' in html, slug


def test_adapters_cover_exactly_the_tool_pages():
    src = (SITE / "tool-visual.js").read_text()
    slugs = set(re.findall(r'"([a-z0-9-]+)": function \(d, s\)', src))
    assert slugs == set(TOOL_PAGES), (sorted(slugs ^ set(TOOL_PAGES)))


def test_preserved_pages_carry_no_tool_host():
    for slug in PRESERVED:
        html = (SITE / slug / "index.html").read_text()
        assert 'id="vkHost"' not in html, slug
        assert "tool-visual.js" not in html, slug


def test_momentum_window_argument_present():
    src = (SITE / "tool-visual.js").read_text()
    assert 'windowChange(d, s, "Biggest rises over the last 21 sessions"' in src
    assert 'offers.", 21);' in src


def test_greeks_curve_drawn_on_load():
    html = (SITE / "greeks-sketch" / "index.html").read_text()
    assert "function drawCurve(" in html
    assert "drawCurve(S,K,days,volPct,ratePct,divPct,isCall);" in html
    assert 'id="curveBox"' in html
