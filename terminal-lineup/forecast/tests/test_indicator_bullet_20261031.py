"""Regression blockers for the indicator cure (2026-10-31, spec 14.2
current-state row + 14.5).

Old behaviour (fails these tests): current-state-vs-range readings
were drawn as radial gauges / semicircle dials (angle encoding):
VisualKit.gaugeZones and VisualKit.dial emitted arc paths with
vk-dial-fill / vk-dial-needle, Market Mood's pipeline emitted arc
SVGs, Breadth Meter's page drew semicircle arcs, hub gauge minis
extracted the gauge SVG, and the kit's one bullet (meterBench) had
no zone/sparkline form. Chart text sat at 11px and nav/preset
targets were 3px-padded, under the 14.5 phone floors.

New behaviour: one shared VisualKit.bullet component (length bar on
zone bands + benchmark tick + exact value + zone word + sparkline
when history is handed in); gaugeZones/dial delegate to it; the hub
mini, Market Mood and Breadth Meter all render the linear form.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
WORKSPACE = Path(__file__).resolve().parents[3]

HARNESS = r"""
const VK = require(process.argv[2]);
const out = {};
const S = "2026-10-30";
const zones = [{to:25,label:"Extreme fear"},{to:50,label:"Fearful"},{to:75,label:"Neutral"},{to:100,label:"Greed"}];
out.bullet = VK.bullet({value:30.1, low:0, high:100, zones:zones, session:S,
  history:[{date:"2026-10-28",value:28},{date:"2026-10-29",value:31},{date:"2026-10-30",value:30.1}]});
out.bullet_nobench = VK.bullet({value:50, low:0, high:100, zones:zones, session:S});
out.bullet_bench = VK.bullet({value:50, low:0, high:100, benchmark:75, session:S});
out.bullet_raw = VK.bullet({value:50, low:0, high:100, zones:zones, raw:true});
out.bullet_empty = VK.bullet({session:S});
out.bullet_noscale = VK.bullet({value:72, session:S});
out.gauge = VK.gaugeZones({value:72, low:0, high:100, zones:zones, session:S});
out.dial = VK.dial({value:72, low:0, high:100, session:S});
out.dial_empty = VK.dial({session:S});
console.log(JSON.stringify(out));
"""


def render():
    node = shutil.which("node")
    assert node, "node is required to prove bullet geometry"
    tmp = Path("/tmp/_bullet_harness.js")
    tmp.write_text(HARNESS)
    r = subprocess.run([node, str(tmp), str(SITE / "visual.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:600]
    return json.loads(r.stdout)


R = render()


def test_bullet_is_length_with_zones_value_and_zone_word():
    b = R["bullet"]
    assert 'class="vk-bullet-fill" style="width:30.1%"' in b
    assert b.count("vk-bullet-seg") == 4
    assert "30.1 · Fearful" in b, "exact value plus zone word must print"
    assert "Extreme fear 0" in b and "100 Greed" in b


def test_bullet_pairs_sparkline_when_history_exists():
    assert "vk-bullet-spark" in R["bullet"] and "<svg" in R["bullet"]
    assert "vk-bullet-spark" not in R["bullet_nobench"]


def test_bullet_benchmark_tick():
    assert "vk-bench-mark" in R["bullet_bench"]
    assert 'left:75%' in R["bullet_bench"]


def test_bullet_raw_is_the_mini_form():
    assert R["bullet_raw"].startswith('<div class="vk-bullet">')
    assert "creceipt" not in R["bullet_raw"]


def test_bullet_fails_closed():
    assert "vk-state" in R["bullet_empty"] and "vk-bullet-fill" not in R["bullet_empty"]
    assert "scale is not stated" in R["bullet_noscale"]


def test_no_radial_geometry_remains_in_kit_current_state():
    for key in ("bullet", "gauge", "dial"):
        html = R[key]
        assert "vk-dial-needle" not in html, key
        assert "vk-dial-fill" not in html, key
        assert "vk-bullet-fill" in html, key
    assert "vk-state" in R["dial_empty"]


def test_sources_carry_no_arc_gauge_renderer():
    js = (SITE / "visual.js").read_text(encoding="utf-8")
    assert "function bullet(" in js and "bullet: bullet" in js
    assert "function gaugeZones(input) { return bullet(input || {}); }" in js
    pc = (SITE / "page_charts.js").read_text(encoding="utf-8")
    assert "VisualKit.bullet({ value: comp" in pc, "hub gauge mini must be a bullet"
    pipe = (WORKSPACE / "terminal-lineup" / "psychology-engine"
            / "pipeline.py").read_text(encoding="utf-8")
    assert "gauge-marker" in pipe and "polar(" not in pipe.split("def gauge_svg")[1].split("def pct_words")[0]
    breadth = (SITE / "breadth-meter" / "index.html").read_text(encoding="utf-8")
    assert "btrack" in breadth and "bfill" in breadth and "sparkSvg" in breadth
    assert "A 80 80" not in breadth, "semicircle arc must be gone"


def test_phone_floors_14_5():
    css = (SITE / "visual.css").read_text(encoding="utf-8")
    assert ".vk-axis{font-size:16px" in css
    assert ".vk-note{font-size:16px" in css
    assert ".vk-bullet-track" in css and ".vk-bullet-value" in css
    shared = (SITE / "shared.css").read_text(encoding="utf-8")
    assert "min-height:44px" in shared, "44px touch-target floor"
    nav = re.search(r"\.topbar nav a\{[^}]*\}", shared)
    assert nav and "min-height:44px" in nav.group(0)
