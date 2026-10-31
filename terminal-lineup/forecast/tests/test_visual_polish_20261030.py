"""Regression blockers for the 2026-10-30 site visual polish repair pass.

Each test pins one defect from
research_notes/site-visual-polish-20261030/DEFECTS.md (and the
auto-update wiring defects in AUTOUPDATE.md) so the class cannot
return silently. Source assertions where a full browser harness is
impractical; a real JS parse (node --check) for the two pages whose
scripts were dead.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"


def page(rel):
    return (SITE / rel).read_text(encoding="utf-8")


def script_of(rel):
    m = re.search(r"<script>(.*?)</script>", page(rel), re.S)
    assert m, rel
    return m.group(1)


def test_broken_pages_scripts_parse():
    node = shutil.which("node")
    if not node:
        # Fall back to the pin: the exact quote breaks stay absent.
        assert 'class="claim">The promise' not in page("corrected-band/index.html")
        assert 'type="search" id="q"' not in page("exceedance/index.html")
        return
    for rel in ("corrected-band/index.html", "exceedance/index.html"):
        tmp = Path("/tmp/_vp_check.js")
        tmp.write_text(script_of(rel))
        r = subprocess.run([node, "--check", str(tmp)],
                           capture_output=True, text=True)
        assert r.returncode == 0, (rel, r.stderr[:400])


def test_no_emdash_anywhere_in_page_sources():
    bad = []
    for p in SITE.rglob("index.html"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "—" in t or "&mdash;" in t:
            bad.append(str(p.relative_to(SITE)))
    assert bad == [], bad


def test_grade_a_board_table_scrolls_and_no_dash_placeholder():
    t = page("grade-a-board/index.html")
    assert 'class="scrollx"' in t and "scroll sideways inside it" in t
    assert 'return "—"' not in t


def test_flow_board_wide_table_scrolls_with_hint():
    t = page("flow-board/index.html")
    assert "min-width:1080px" in t
    assert "scroll sideways inside it to see every day" in t


def test_ai_chart_read_level_labels_offset_when_levels_coincide():
    t = page("ai-chart-read/index.html")
    assert "yOff" in t and "xRight" in t
    assert "r.levels126.high === r.levels20.high" in t
    assert "r.levels126.low === r.levels20.low" in t
    assert "paint-order:stroke" in t


def test_mobile_overflow_cures_present():
    assert "@media (max-width:640px)" in page("board/index.html")
    assert "@media (max-width:640px)" in page("screener/index.html")
    assert "table{display:block;overflow-x:auto" in page("record/index.html")
    assert "table{display:block;overflow-x:auto" in page("living-router/index.html")
    pb = page("portfolio-builder/index.html")
    assert ".mix{grid-template-columns:1fr}" in pb


def test_chain_explorer_names_its_sideways_scroll():
    assert "scroll sideways inside it to reach the put side" in page(
        "chain-explorer/index.html")


def test_filings_wire_bare_number_heading_reads_finished():
    t = page("filings-wire/index.html")
    assert "Company number " not in t
    assert "company name not on record" in t


def test_static_gex_prints_rounded_levels():
    t = page("static-gex/index.html")
    assert "Math.round(v * 100) / 100" in t


def test_proving_banner_never_repeats_its_label():
    for rel in ("ai-chart-read/index.html", "pattern-draw/index.html",
                "breakout-scanner/index.html", "momentum-clock/index.html",
                "strat-combos/index.html", "strat-scanner/index.html"):
        t = page(rel)
        assert "function proveNote(state, note)" in t, rel
        assert "proveNote(" in t and "proving_note))" in t, rel


def test_empty_state_headline_not_duplicated():
    assert "No fear day list has been published yet.</strong>" not in page(
        "fear-day/index.html")
    assert "No pullback study has been published yet.</strong>" not in page(
        "pullback-norm/index.html")


def test_holly_ideas_has_no_disclaimer_phrasing():
    assert "not a recommendation" not in page("holly-ideas/index.html")


def test_autoupdate_wiring_staticgex_proofgate_sourceclock():
    runner = page("refresh_tools.py")
    assert '"refresh_staticgex.py"' in runner
    assert '"refresh_proofgate.py"' in runner
    assert '"source_clock_diagnostic.py"' in runner


def test_autoupdate_manifest_rebuilt_by_last_evening_runner():
    runner = page("refresh_tools.py")
    assert 'verify_terminal.sh' in runner


def test_stamp_provenance_maps_source_clock():
    sys.path.insert(0, str(SITE))
    import stamp_provenance
    mapping = stamp_provenance.dir_to_script()
    assert mapping.get("source-clock") == "source_clock_diagnostic.py"


# --- Design pass, 2026-10-30 (DESIGN-BRIEF elements 1 to 11) ---

def test_shared_sheet_linked_on_every_page():
    missing = []
    for p in SITE.rglob("index.html"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "shared.css" not in t or "shared.js" not in t:
            missing.append(str(p.relative_to(SITE)))
    assert missing == [], missing


def test_shared_sheet_has_canonical_tokens_and_components():
    css = (SITE / "shared.css").read_text(encoding="utf-8")
    for token in ("--ink:#17202b", "--bg:#f5f7fa", "--accent:#0b5fa5",
                  "--up:#1d7a3a", "--down:#b03a2e", "--nodata-bg:#eef1f5"):
        assert token in css, token
    for comp in (".topbar", ".verdict", ".meter", ".chip", ".statecard",
                 ".hubgrid", ".hubcard", ".chartbox", ".ladder", ".tiles",
                 ".tape", ".presets", ".related", ".hubsearch"):
        assert comp in css, comp
    assert "—" not in css


def test_hub_is_card_grid_with_search_and_chips():
    hub = page("index.html")
    assert 'class="hubsearch"' in hub
    assert hub.count('class="hubcard"') >= 100
    assert 'class="chip ' in hub
    assert 'id="forecast-engines"' in hub
    assert 'id="ready-to-use"' in hub
    assert "—" not in hub


# --- Final re-inspection pass, 2026-10-30 (D22, D23) ---

def test_verdict_value_keeps_space_after_block_figure():
    js = (SITE / "shared.js").read_text(encoding="utf-8")
    assert "normText" in js and "innerText" in js, \
        "verdict values must come from innerText so a block figure does not glue to its label"


def test_wide_table_scroll_cue_in_shared_shell():
    js = (SITE / "shared.js").read_text(encoding="utf-8")
    css = (SITE / "shared.css").read_text(encoding="utf-8")
    assert "addScrollHints" in js and "scroll sideways inside it" in js
    assert ".scrollhint" in css


def test_hone_shared_body_background_and_focus_ring():
    css = (SITE / "shared.css").read_text(encoding="utf-8")
    assert "body{letter-spacing:0;background:var(--bg);color:var(--ink)}" in css
    assert ":focus-visible" in css
    assert "--faint:#5f7186" in css


def _lum(hexcolor):
    h = hexcolor.lstrip("#")
    vals = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    vals = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in vals]
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def test_hone_faint_token_contrast_on_card_and_bg():
    faint = _lum("#5f7186")
    for bg in ("#ffffff", "#f5f7fa"):
        ratio = (_lum(bg) + 0.05) / (faint + 0.05)
        assert ratio >= 4.5, (bg, ratio)
