"""Regression blockers for the 2026-10-30 visual kit (DESIGN.md build stream 1).

The kit lives in site/visual.css and site/visual.js beside the shared layer.
Each primitive must render non-empty real geometry on a fixture, and must
render its honest state visual (statecard or accrual, never invented
geometry and never a zero presented as a result) on an empty fixture.
Renderers are pure string functions under Node, so the geometry is counted
directly from their output, the same shapes DESIGN section 8 counts in the
rendered DOM.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"

HARNESS = r"""
const VK = require(process.argv[2]);
const out = {};
const S = "2026-10-29";
out.ladder = VK.ladder({levels:[{name:"Call wall",price:600,size:900},{name:"Put wall",price:580,size:300}],current:590,session:S});
out.ladder_empty = VK.ladder({levels:[],session:S});
out.ladder_price_only = VK.ladder({levels:[],current:590,session:S});
out.band = VK.band({items:[{label:"SPY",low:580,high:600,mid:590,current:592}],session:S});
out.band_empty = VK.band({items:[],session:S});
out.curve = VK.curve({points:[{x:"a",y:1},{x:"b",y:3},{x:"c",y:2}],session:S});
out.curve_step = VK.curve({points:[{x:"a",y:1},{x:"b",y:3}],step:true,session:S});
out.curve_empty = VK.curve({points:[{x:"a",y:1}],session:S});
out.dial = VK.dial({value:72,low:0,high:100,session:S});
out.dial_empty = VK.dial({session:S});
out.dial_noscale = VK.dial({value:72,session:S});
out.meter = VK.meterBench({value:0.18,benchmark:0.25,graded:40,needed:120,session:S});
out.meter_ungraded = VK.meterBench({value:null,benchmark:0.25,graded:0,needed:120,session:S});
out.ranked = VK.ranked({rows:[{name:"A",score:9,coverage:"40 of 50"},{name:"B",score:4}],session:S});
out.ranked_empty = VK.ranked({rows:[],session:S});
out.tiles = VK.tiles({items:[{label:"Tech",value:2.5},{label:"Energy",value:-1.2},{label:"Gold",value:null}],session:S});
out.tiles_empty = VK.tiles({items:[],session:S});
out.strip = VK.heatStrip({buckets:[{label:"09",count:3},{label:"10",count:9}],session:S});
out.tape = VK.tape({events:[{time:"2026-10-29T14:00Z",label:"SPY",desc:"Sweep on record",tags:["sweep"]},{time:"2026-10-29T15:00Z",label:"QQQ",desc:"Block on record"}],session:S});
out.tape_empty = VK.tape({events:[],session:S});
out.line = VK.line({series:[{date:"2026-10-27",value:1},{date:"2026-10-28",value:2},{date:"2026-10-29",value:3}],session:S});
out.line_gap = VK.line({series:[{date:"2026-10-25",value:1},{date:"2026-10-26",value:2},{date:"2026-10-27",value:null},{date:"2026-10-28",value:3},{date:"2026-10-29",value:4}],session:S});
out.line_empty = VK.line({series:[{date:"2026-10-29",value:3}],session:S});
out.accrual = VK.accrual({have:22,need:120,unit:"graded",session:S});
out.accrual_ticks = VK.accrual({have:3,need:10,unit:"sessions",session:S});
out.accrual_cal = VK.accrual({mode:"calendar",days:[{date:"2026-10-27",count:0},{date:"2026-10-28",count:4}],session:S});
out.accrual_tl = VK.accrual({mode:"timeline",events:[{date:"2026-10-01",label:"Filed"}],session:S});
out.accrual_empty = VK.accrual({session:S});
out.scatter = VK.scatter({rows:[{x:1,y:2},{x:2,y:3},{x:3,y:5},{x:4,y:null}],session:S,xLabel:"closeness",yLabel:"what happened next"});
out.scatter_fallback = VK.scatter({rows:[{x:5,label:"One"},{x:3,label:"Two"}],session:S});
out.scatter_empty = VK.scatter({rows:[],session:S});
console.log(JSON.stringify(out));
"""


def render():
    node = shutil.which("node")
    assert node, "node is required to prove kit geometry"
    tmp = Path("/tmp/_vk_harness.js")
    tmp.write_text(HARNESS)
    r = subprocess.run([node, str(tmp), str(SITE / "visual.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:600]
    return json.loads(r.stdout)


R = render()


def test_visual_js_parses():
    node = shutil.which("node")
    assert node
    r = subprocess.run([node, "--check", str(SITE / "visual.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:400]


def test_kit_files_carry_shared_tokens_and_no_emdash():
    css = (SITE / "visual.css").read_text(encoding="utf-8")
    js = (SITE / "visual.js").read_text(encoding="utf-8")
    for token in ("var(--ink)", "var(--accent)", "var(--line)", "var(--nodata-bg)"):
        assert token in css, token
    assert ".vk-" in css
    assert "—" not in css and "—" not in js
    # No new palette: the only hex colour allowed is the white shared.css uses.
    hexes = set(re.findall(r"#[0-9a-fA-F]{3,6}", css))
    assert hexes <= {"#fff"}, hexes


def test_binding_contract_is_one_data_file_with_live_rerender():
    js = (SITE / "visual.js").read_text(encoding="utf-8")
    assert 'fetch("data.json"' in js
    assert "data-vk" in js
    assert "15) * 60 * 1000" in js and "5 : 15" in js
    assert "prefers-reduced-motion" in js
    assert "visibilitychange" in js


def test_ladder_geometry_and_states():
    assert R["ladder"].count('class="lrow"') == 2
    assert 'class="lrow price-row"' in R["ladder"] and "590" in R["ladder"]
    assert 'style="width:100%"' in R["ladder"]
    assert "2 levels drawn" in R["ladder"]
    assert "vk-state" in R["ladder_empty"] and "lrow" not in R["ladder_empty"]
    assert "price-row" in R["ladder_price_only"] and "not yet published" in R["ladder_price_only"]


def test_band_geometry_and_state():
    assert "vk-bandrect" in R["band"] and "<svg" in R["band"]
    assert "1 bands drawn" in R["band"]
    assert "vk-state" in R["band_empty"] and "vk-bandrect" not in R["band_empty"]


def test_curve_geometry_and_state():
    assert "vk-line-path" in R["curve"] and R["curve"].count("<path") >= 1
    assert "vk-line-path" in R["curve_step"]
    assert "vk-state" in R["curve_empty"] and "vk-line-path" not in R["curve_empty"]
    assert "Only 1 point" in R["curve_empty"]


def test_dial_geometry_and_states():
    assert "vk-dial-fill" in R["dial"] and "vk-dial-needle" in R["dial"]
    assert ">72<" in R["dial"]
    assert "vk-state" in R["dial_empty"] and "vk-dial-fill" not in R["dial_empty"]
    assert "scale is not stated" in R["dial_noscale"]


def test_meterbench_geometry_and_ungraded_state():
    assert "vk-bench-mark" in R["meter"] and "Simple benchmark 0.25" in R["meter"]
    assert "40 graded, 120 needed" in R["meter"]
    assert "vk-bench-mark" not in R["meter_ungraded"]
    assert "0 graded on record" in R["meter_ungraded"]
    assert "0.18" not in R["meter_ungraded"]


def test_ranked_geometry_and_state():
    assert R["ranked"].count("vk-rrow") == 2
    assert 'style="width:100%"' in R["ranked"]
    assert "40 of 50" in R["ranked"]
    assert "vk-state" in R["ranked_empty"] and "vk-rrow" not in R["ranked_empty"]


def test_tiles_and_strip_geometry_and_state():
    assert 'tile up' in R["tiles"] and 'tile down' in R["tiles"] and 'tile nodata' in R["tiles"]
    assert "2 tiles drawn" in R["tiles"]
    assert "vk-state" in R["tiles_empty"]
    assert R["strip"].count("vk-heat-cell") == 2


def test_tape_geometry_and_quiet_state():
    assert R["tape"].count("trow") == 2
    assert "vk-heatstrip" in R["tape"] and "chip" in R["tape"]
    assert "vk-state" in R["tape_empty"] and "quiet tape" in R["tape_empty"]


def test_line_geometry_gap_and_state():
    assert "vk-line-path" in R["line"] and "3 dated values drawn" in R["line"]
    # A missing session breaks the path: two separate segments, no bridge.
    assert R["line_gap"].count('class="vk-line-path"') == 2
    assert "vk-state" in R["line_empty"] and "vk-line-path" not in R["line_empty"]


def test_accrual_modes_and_state():
    assert "vk-accrual" in R["accrual"] and "22 graded on record" in R["accrual"]
    assert R["accrual_ticks"].count("vk-tick on") == 3
    assert R["accrual_cal"].count("vk-cal-cell") == 2
    assert "vk-timeline" in R["accrual_tl"] and "vk-tl-dot" in R["accrual_tl"]
    assert "vk-state" in R["accrual_empty"]


def test_scatter_geometry_fallback_and_state():
    assert R["scatter"].count('class="vk-dot"') == 3
    assert "1 rows lacked a pair" in R["scatter"]
    assert "vk-rrow" in R["scatter_fallback"]
    assert "vk-state" in R["scatter_empty"]


def test_every_visual_carries_a_receipt():
    for key, html in R.items():
        if key in ("strip",):
            continue
        assert "creceipt" in html, key
        assert "Session 2026-10-29" in html, key


def test_no_zero_presented_as_result_in_empty_states():
    for key in ("band_empty", "curve_empty", "dial_empty", "tiles_empty",
                "ranked_empty", "tape_empty", "line_empty", "scatter_empty"):
        assert "vk-state" in R[key], key
