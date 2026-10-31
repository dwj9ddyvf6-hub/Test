"""Regression blockers for the 2026-10-31 encoding and multivariate
cures (spec 14.1, 14.2, 14.4; AUDIT cure classes for encodings).

Each test names the old behaviour it blocks:
- charts stretched by preserveAspectRatio="none" (14.1.6)
- line charts with no value axis and silent truncation (14.1.3/14.1.7)
- area charts captioned as if filled area carries the value (14.1.1)
- heatmap magnitude riding opacity, values only in hover titles (14.1.4)
- calendar counts carried by tint / hover only (14.1.7)
- composition drawn as a donut (angle and area) instead of a stacked
  bar of lengths (14.2 composition)
- tiles carrying a quantity by tint alone, with no length (14.5.1)
- negative ranked bars drawn identically to positive ones (14.2)
- unlabelled scatter points (14.1.7)
- fan bands with no on-chart band names (14.2 uncertainty)
- correlation-web leading with tiles instead of a relationship form,
  and earnings-distribution leading with tier counts instead of a
  distribution (14.2)
"""
import json
import shutil
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"

HARNESS = r"""
const VK = require(process.argv[2]);
const out = {};
const S = "2026-10-30";
out.line = VK.line({series:[{date:"2026-10-28",value:10},{date:"2026-10-29",value:14},{date:"2026-10-30",value:12}],session:S});
out.line_zero = VK.line({series:[{date:"a",value:-2},{date:"b",value:3}],session:S});
out.area = VK.area({series:[{date:"a",value:5},{date:"b",value:7}],session:S});
out.curve = VK.curve({points:[{x:"a",y:10},{x:"b",y:14}],session:S});
out.heatmap = VK.heatmap({cells:[[1.5,-2],[0.5,3]],rowLabels:["A","B"],colLabels:["X","Y"],session:S});
out.cal = VK.accrual({mode:"calendar",days:[{date:"2026-10-30",count:7}],session:S});
out.donut = VK.donut({slices:[{label:"Alpha",value:30},{label:"Beta",value:70}],session:S});
out.stacked = VK.stackedBar({slices:[{label:"Alpha",value:30},{label:"Beta",value:70}],session:S});
out.tiles = VK.tiles({items:[{label:"A",value:5},{label:"B",value:-2}],session:S});
out.ranked = VK.ranked({rows:[{name:"A",score:-4},{name:"B",score:3}],session:S});
out.scatter = VK.scatter({rows:[{label:"SPY",x:1,y:2},{label:"QQQ",x:2,y:3},{label:"AAPL",x:3,y:1}],session:S});
out.fan = VK.fan({steps:[{label:"1 day",low:1,high:3,low2:0,high2:4}],session:S});
console.log(JSON.stringify(out));
"""


def render():
    node = shutil.which("node")
    assert node, "node is required to prove kit geometry"
    tmp = Path("/tmp/_encoding_harness.js")
    tmp.write_text(HARNESS)
    r = subprocess.run([node, str(tmp), str(SITE / "visual.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:600]
    return json.loads(r.stdout)


R = render()


def test_no_chart_is_stretched():
    for key, html in R.items():
        assert 'preserveAspectRatio="none"' not in html, key
    assert 'preserveAspectRatio="xMidYMid meet"' in R["line"]


def test_line_has_axis_and_names_truncation():
    assert "vk-grid" in R["line"]
    assert "zero is outside it" in R["line"]
    assert 'class="vk-zero"' in R["line_zero"]


def test_area_line_carries_value_not_the_fill():
    assert "size of the move is easy to see" not in R["area"]
    assert "zero is outside it" in R["area"]
    assert "zero is outside it" in R["curve"]


def test_heatmap_values_printed_not_opacity_or_hover():
    assert "opacity=" not in R["heatmap"]
    assert ">1.5<" in R["heatmap"] and ">-2<" in R["heatmap"]
    assert "Each cell prints its exact value" in R["heatmap"]


def test_calendar_prints_its_count():
    assert "30 · 7" in R["cal"]


def test_composition_is_a_stacked_bar_of_lengths():
    for html in (R["donut"], R["stacked"]):
        assert "stacked bar" in html
        assert "Alpha 30 (30%)" in html and "Beta 70 (70%)" in html
        assert "vk-slice" in html and "<path" not in html


def test_tiles_carry_a_length_bar():
    assert "width:100%" in R["tiles"]
    assert "var(--down)" in R["tiles"]


def test_negative_ranked_bar_is_down_coloured():
    assert "background:var(--down)" in R["ranked"]


def test_scatter_points_are_labelled_with_values():
    assert "SPY 1, 2" in R["scatter"]


def test_fan_bands_are_named_on_the_chart():
    assert "Inner band: the narrower published range" in R["fan"]
    assert "Outer band: the wider published range" in R["fan"]


def test_relationship_and_distribution_leads_use_their_forms():
    tool = (SITE / "tool-visual.js").read_text(encoding="utf-8")
    eng = (SITE / "engine-visual.js").read_text(encoding="utf-8")
    assert "VisualKit.scatter" in tool
    assert '"correlation-web"' in tool
    assert "VisualKit.distribution" in eng
    assert '"earnings-distribution"' in eng


def test_no_emdash_in_cured_renderers():
    for name in ("visual.js", "tool-visual.js", "engine-visual.js"):
        assert "—" not in (SITE / name).read_text(encoding="utf-8"), name
