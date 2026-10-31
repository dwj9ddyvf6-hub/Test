"""Regression blockers for the 2026-10-30 engine visual build (stream 3).

Pins: every forecast engine page on the build list (plus the Board and
the Record) carries the visual kit host and loads the shared kit files;
the binding layer reads only each page's own data.json; the accrual
pairing never counts a target field as its own progress (the
idio-liquidity 100 percent defect); preserved pages (the two engines
whose truthful visual is the shared count meter, and the hub, which has
no producer) are not wired with a second visual.
"""
import re
import shutil
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"

WIRED = ("calibration-league capitulation-clock completion-clock corrected-band "
         "earnings-distribution exceedance fear-day-triangulation gamma-earnings-trap "
         "gap-destiny half-life-clock honest-pop idio-liquidity in-regime-oracle "
         "insider-divergence intake-bias living-router mortality-curve own-norm-depth "
         "pin-or-escape self-analogue silent-accumulation sponsored-reset streak-trap "
         "stress-reversal touch-surface vol-clock vol-term-shape wall-lifetime "
         "board record").split()

PRESERVED = ["abstention-signal", "family-fracture"]


def page(slug):
    return (SITE / slug / "index.html").read_text(encoding="utf-8")


def test_every_wired_page_carries_the_kit():
    for slug in WIRED:
        html = page(slug)
        assert 'href="../visual.css"' in html, slug
        assert 'src="../visual.js" defer' in html, slug
        assert 'src="../engine-visual.js" defer' in html, slug
        assert 'id="vkHost"' in html, slug
        assert html.index('id="vkHost"') > html.index("</header>"), slug


def test_preserved_pages_not_double_wired():
    for slug in PRESERVED:
        assert 'id="vkHost"' not in page(slug), slug
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'id="vkHost"' not in hub


def test_binding_reads_only_own_data_and_no_em_dash():
    js = (SITE / "engine-visual.js").read_text(encoding="utf-8")
    assert 'fetch("data.json"' in js
    assert "http" not in js.replace("https://", "")  # no external or cross-page fetch
    assert "\u2014" not in js
    for slug in WIRED:
        assert "\u2014" not in page(slug).split('id="vkHost"')[1].split("</div>")[0], slug


def test_target_never_counts_as_its_own_progress():
    js = (SITE / "engine-visual.js").read_text(encoding="utf-8")
    m = re.search(r"var haveKey.*?\[0\];", js, re.S)
    assert m and "!/target/.test(k)" in m.group(0)


def test_engine_visual_parses():
    node = shutil.which("node")
    assert node, "node required"
    out = subprocess.run([node, "--check", str(SITE / "engine-visual.js")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
