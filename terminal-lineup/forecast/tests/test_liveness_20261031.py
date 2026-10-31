"""Liveness blocker (LIVENESS-20261031).

The serve-live cure: pages poll their own data file on the cadence
their inputs arrive at, the top bar carries a live clock, producer
lanes run by cadence class with watermarks, and the publish step
proves served bytes equal disk bytes. These tests fail on the
pre-cure tree (no live.js, no serve_live.py, no lane runner, no
publish step in republish_one.sh).
"""
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
INFO_MAP = (SITE.parents[1] / "research_notes" /
            "terminal-visual-expression-20261031" / "INFO-MAP.md")


def cadence_from_info_map():
    rows = {}
    for line in INFO_MAP.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) >= 8 and parts[-1] in (
                "intraday-minutes", "daily-close", "weekly",
                "static-study") and re.fullmatch(
                r"[a-z0-9][a-z0-9\-]*", parts[0]):
            rows[parts[0]] = parts[-1]
    return rows


def test_live_js_covers_every_page_with_its_info_map_cadence():
    live = (SITE / "live.js").read_text(encoding="utf-8")
    m = re.search(r"var CADENCE = (\{.*?\});", live, re.S)
    assert m, "live.js carries no CADENCE map"
    baked = json.loads(m.group(1))
    assert baked == cadence_from_info_map()
    assert len(baked) == 102


def test_live_js_poll_and_stale_contracts():
    live = (SITE / "live.js").read_text(encoding="utf-8")
    assert '"intraday-minutes": 180000' in live   # a few minutes
    assert '"daily-close": 3600000' in live       # hourly
    assert '"static-study": 0' in live            # as-of only, no poll
    assert "no-store" in live                     # cache-free re-fetch
    assert "__pageChartsRerender" in live         # re-render in place
    assert "Market closed" in live and "Stale" in live


def test_shared_shell_loads_live_layer_and_styles_exist():
    shared = (SITE / "shared.js").read_text(encoding="utf-8")
    assert '"live.js"' in shared
    css = (SITE / "visual.css").read_text(encoding="utf-8")
    assert ".livedot" in css and ".liveind.stale" in css
    charts = (SITE / "page_charts.js").read_text(encoding="utf-8")
    assert "__pageChartsRerender" in charts


def test_serve_and_publish_steps_exist_and_are_wired():
    serve = (SITE / "serve_live.py").read_text(encoding="utf-8")
    assert "ThreadingHTTPServer" in serve and "desk" in serve
    publish = (SITE / "publish_live.py").read_text(encoding="utf-8")
    assert "byte-identical" in publish and "desk/index.html" in publish
    repub = (SITE / "republish_one.sh").read_text(encoding="utf-8")
    assert repub.index("verify_terminal.sh") < repub.index("publish_live.py")
    for runner in ("refresh_engines.py", "refresh_tools.py"):
        body = (SITE / runner).read_text(encoding="utf-8")
        assert "publish_live.py" in body, runner


def test_lane_runner_has_four_lanes_watermark_and_market_gate():
    lane = (SITE / "lane_run.py").read_text(encoding="utf-8")
    for name in ("intraday", "hourly", "daily-close", "weekly"):
        assert f'"{name}"' in lane or f"'{name}'" in lane, name
    assert "lane_state.json" in lane and "lane_freshness.log" in lane
    assert "tape_family_run.py" in lane
    assert "market_open" in lane and "America/New_York" in lane
    assert "refresh_hub.py" in lane  # hub refresh closes every lane


def test_lane_crons_are_scheduled():
    cron_root = SITE.parents[1] / "cron.d"
    found = {p.name.split("__")[0] for p in cron_root.rglob("terminal-*.md")}
    assert {"terminal-intraday-lane", "terminal-hourly-lane",
            "terminal-daily-close-lane",
            "terminal-weekly-lane"} <= found
