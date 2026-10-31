"""Regression blockers for the charts-IA phase (2026-10-31).

Covers: the VisualKit INFO-MAP vocabulary renderers exist and draw to
scale; the shared nav is in the ruled order with Desk last; the hub
carries the ruled section order with truthful counts; the desk
publish copy matches its source byte for byte; Market Mood's gauges
are real SVG dials with unchanged values.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
WORKSPACE = SITE.parents[1]


def _node(expr):
    out = subprocess.run(["node", "-e", expr], capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_visualkit_vocabulary_and_scale():
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const need=['area','sparkline','fan','distribution','heatmap',"
        "'gaugeZones','timeline','countBars','donut','line','curve',"
        "'band','dial'];"
        "for (const n of need) if (typeof VK[n]!=='function') "
        "throw new Error('missing '+n);"
        "const g=VK.gaugeZones({value:50,low:0,high:100,"
        "zones:[{to:100,label:'x'}]});"
        "if (!g.includes('<svg')) throw new Error('gauge no svg');"
        "const d=VK.distribution({buckets:[{label:'a',value:0},"
        "{label:'b',value:10}]});"
        "if (!d.includes('<svg')) throw new Error('dist no svg');"
        "const dn=VK.donut({slices:[{label:'a',value:3},"
        "{label:'b',value:1}]});"
        "if (!dn.includes('75%')) throw new Error('donut share wrong');"
        "const e=VK.donut({slices:[]});"
        "if (e.includes('<svg')) throw new Error('empty donut drew');"
        "console.log('ok');"
    )
    assert "ok" in _node(js)


def test_nav_order_desk_last():
    shared = (SITE / "shared.js").read_text()
    nav = re.search(r'\[\["Forecast Engines".*?\]\]', shared, re.S)
    assert nav, "nav array not found"
    labels = re.findall(r'\["([A-Za-z ]+)", root', nav.group(0))
    assert labels == ["Forecast Engines", "Market Tools", "Modules",
                      "The Record", "Desk"], labels
    assert 'root + "desk/"' in shared


def test_hub_sections_and_counts():
    hub = (SITE / "index.html").read_text()
    order = [hub.find('id="visual-front"'),
             hub.find('id="forecast-engines"'),
             hub.find('id="ready-to-use"'),
             hub.find('id="modules"'),
             hub.find('id="the-record"'),
             hub.find('id="desk"')]
    assert all(x >= 0 for x in order), order
    assert order == sorted(order), order
    cards = re.findall(r'<article class="hubcard".*?</article>',
                       hub, re.S)
    assert len(cards) == 102
    assert len(re.findall(r'class="mini"', hub)) == 102
    assert len(re.findall(r'data-vf="', hub)) == 8
    chips = {}
    for c in re.findall(r'class="chip ([a-z]+)"', hub):
        chips[c] = chips.get(c, 0) + 1
    line = re.search(r'<p class="hubcount">([^<]*)</p>', hub).group(1)
    assert line.startswith(
        f"102 tools in the lineup: {chips.get('live', 0)} live, "
        f"{chips.get('waiting', 0)} waiting, "
        f"{chips.get('ungraded', 0)} not yet graded, "
        f"{chips.get('stale', 0)} stale"), line


def test_desk_publish_copy_matches_source():
    # The desk feed is live and moves on its own cycle, so the blocker
    # proves the producer: a fresh publish must be byte-identical.
    out = subprocess.run(
        ["python3", str(SITE / "publish_desk.py")],
        capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    src = WORKSPACE / "muse-desk-v3" / "terminal"
    for name in ("index.html", "terminal_feed.json"):
        a = hashlib.sha256((src / name).read_bytes()).hexdigest()
        b = hashlib.sha256(
            (SITE / "desk" / name).read_bytes()).hexdigest()
        assert a == b, name


def test_market_mood_gauge_dials_values_unchanged():
    html = (SITE / "market-mood" / "index.html").read_text()
    data = json.loads((SITE / "market-mood" / "data.json").read_text())
    comp = data["state"]["composite_percentile"]
    assert html.count("Gauge reading") >= 5
    assert f'<p class="bignum">{comp}</p>' in html
    pipe = (WORKSPACE / "terminal-lineup" / "psychology-engine"
            / "pipeline.py").read_text()
    assert "def gauge_svg" in pipe
