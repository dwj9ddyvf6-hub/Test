"""Regression blockers for the terminal total audit round 1
tools-b re-cures (2026-10-31, addendum defects A1 to A4).

Covered cures:
- PANEL-RESYNC-20261031: panel-derived earnings and insider
  tools still published panel_last_session 2026-10-29 after the
  source panel advanced to 2026-10-30, and every priced name
  still carried spot_session 2026-10-29. The engines chain ran
  priced_moves.py before its panel advance, and no chain re-ran
  the panel_last_session publishers after the day's last panel
  advance. refresh_engines.py now runs priced moves after the
  advance, and refresh_tools.py ends with a panel consumer
  re-sync group naming every panel_last_session publisher plus
  the priced move record and the earnings calendar.
- MANIFEST-SHARED-WRITE-20261031: a standalone refresher still
  broke smoke_check.py because the manifest rebuild lived only
  in the scheduled chains and the opt-in republish_one.sh
  wrapper. terminal_common.py, the one module every refresher
  imports, now rebuilds the manifest at process exit whenever a
  served file changed during the process.
- SKEW-VISUAL-20261031: skew-lens had no visual at all; its
  assigned P3 Curve adapter now lives in tool-visual.js, fed by
  its own modelled_figures (recorded figures as the fallback),
  and the page carries the visual kit and host.
- HOLLY-WRAP-20261031: holly-ideas facts lines carried
  white-space:nowrap and overflowed a 390px viewport sideways.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")

PANEL_STAMPED = ("earnings-distribution", "insider-divergence",
                 "gamma-earnings-trap", "intake-bias",
                 "family-fracture")


def _load_json(rel, base=SITE):
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _source(name, base=SITE):
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return fh.read()


def _panel():
    with open(PANEL_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ---- A1: panel stamps agree with the source panel --------------

def test_panel_last_session_matches_panel_spy_last_row():
    panel = _panel()
    spy_last = panel["SPY"][-1][0]
    for slug in PANEL_STAMPED:
        data = _load_json(os.path.join(slug, "data.json"))
        assert data["panel_last_session"] == spy_last, slug


def test_priced_moves_spot_matches_panel_last_row_per_name():
    panel = _panel()
    record = _load_json(os.path.join("earnings-record",
                                     "priced_moves.json"))
    assert record["priced_moves_on_record"] >= 1
    for sym, row in record["names"].items():
        assert row["spot_session"] == panel[sym][-1][0], sym
        assert row["spot"] == panel[sym][-1][4], sym


def test_tools_chain_ends_with_panel_consumer_resync():
    src = _source("refresh_tools.py")
    resync = src.index("panel consumer re-sync")
    assert src.index("advance_price_panel.py") < resync
    assert resync < src.index("refresh_hub.py")
    for script in ("priced_moves.py",
                   "refresh_earningsdistribution.py",
                   "refresh_insiderdivergence.py",
                   "refresh_gammaearningstrap.py",
                   "refresh_intakebias.py",
                   "refresh_familyfracture.py",
                   "refresh_earningscal.py"):
        assert script in src[resync:], script


def test_engines_chain_priced_moves_after_panel_advance():
    src = _source("refresh_engines.py")
    assert src.index('"price-panel-advance"') < src.index(
        'str(HERE / "priced_moves.py")')


# ---- A2: manifest rebuild is part of the shared write path ------

def test_terminal_common_carries_manifest_sync():
    src = _source("terminal_common.py")
    assert "MANIFEST-SHARED-WRITE-20261031" in src
    assert "_sync_manifest_on_exit" in src
    assert "_atexit.register" in src


def test_standalone_refresher_leaves_smoke_passing(tmp_path):
    """The audit exercise, both directions. House refreshers are
    deterministic (dates come from their records, never the
    clock), so a same-source rerun cannot stale the manifest on
    demand; the exercise therefore runs in a scratch copy of the
    shared write path: a mini site tree with the real
    terminal_common.py and smoke_check.py, and a refresher that
    writes its data file the way every house refresher does
    (import terminal_common, stamp, dump). With manifest sync
    disabled (the pre-cure behaviour) smoke_check.py fails after
    the standalone run; with it enabled, smoke_check.py passes.
    The real tree is then exercised the audit's way as well: one
    real standalone refresher, then smoke_check.py must pass."""
    import shutil
    mini = tmp_path / "site"
    (mini / "faketool").mkdir(parents=True)
    for name in ("terminal_common.py", "smoke_check.py"):
        shutil.copy(os.path.join(SITE, name), mini / name)
    (mini / "index.html").write_text("<html>hub</html>\n")
    (mini / "faketool" / "index.html").write_text(
        "<html>fake</html>\n")
    (mini / "faketool" / "data.json").write_text(
        '{"value": 1}\n')
    (mini / "refresh_faketool.py").write_text(
        "import json, os, sys\n"
        "sys.path.insert(0, os.path.dirname(os.path.abspath("
        "__file__)))\n"
        "import terminal_common as tc\n"
        "doc = tc.stamp_for_script({'value': 2}, __file__)\n"
        "p = os.path.join(os.path.dirname(os.path.abspath("
        "__file__)), 'faketool', 'data.json')\n"
        "with open(p, 'w', encoding='utf-8') as fh:\n"
        "    json.dump(doc, fh, indent=2, sort_keys=True)\n"
        "    fh.write('\\n')\n")
    r = subprocess.run(
        [sys.executable, "smoke_check.py", "--write-manifest"],
        cwd=mini, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-400:]

    env_off = dict(os.environ, TERMINAL_NO_MANIFEST_SYNC="1")
    r = subprocess.run(
        [sys.executable, "refresh_faketool.py"],
        cwd=mini, env=env_off, capture_output=True, text=True,
        timeout=120)
    assert r.returncode == 0, r.stderr[-400:]
    r = subprocess.run(
        [sys.executable, "smoke_check.py"],
        cwd=mini, capture_output=True, text=True, timeout=120)
    assert r.returncode != 0, (
        "pre-cure direction lost: smoke passed after a standalone "
        "refresher with manifest sync disabled")

    # Restore the pre-run bytes, rebuild, then the cured direction.
    (mini / "faketool" / "data.json").write_text('{"value": 1}\n')
    subprocess.run(
        [sys.executable, "smoke_check.py", "--write-manifest"],
        cwd=mini, capture_output=True, text=True, timeout=120)
    env_on = dict(os.environ)
    env_on.pop("TERMINAL_NO_MANIFEST_SYNC", None)
    r = subprocess.run(
        [sys.executable, "refresh_faketool.py"],
        cwd=mini, env=env_on, capture_output=True, text=True,
        timeout=120)
    assert r.returncode == 0, r.stderr[-400:]
    r = subprocess.run(
        [sys.executable, "smoke_check.py"],
        cwd=mini, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr

    r = subprocess.run(
        [sys.executable, "refresh_earningscal.py"],
        cwd=SITE, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-400:]
    r = subprocess.run(
        [sys.executable, "smoke_check.py"],
        cwd=SITE, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr


# ---- A3: skew-lens visual ---------------------------------------

def test_skew_page_carries_visual_kit():
    html = _source(os.path.join("skew-lens", "index.html"))
    assert 'href="../visual.css"' in html
    assert 'src="../visual.js"' in html
    assert 'src="../tool-visual.js"' in html
    assert 'id="vkHost"' in html


def test_skew_adapter_is_p3_curve_from_own_figures():
    src = _source("tool-visual.js")
    assert '"skew-lens": function' in src
    block = src.split('"skew-lens": function')[1].split(
        '"smart-money-tracker"')[0]
    assert "modelled_figures" in block
    assert "VisualKit.curve" in block
    assert "put_percent" in block and "call_percent" in block


def test_skew_render_has_nonempty_curve_geometry():
    from playwright.sync_api import sync_playwright
    import functools
    import http.server
    import threading
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=SITE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0),
                                             handler)
    threading.Thread(target=server.serve_forever,
                     daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1200,
                                              "height": 900})
            page.goto(f"http://127.0.0.1:{server.server_address[1]}"
                      "/skew-lens/")
            page.wait_for_selector("#vkHost svg path.vk-line-path",
                                   timeout=20000)
            host = page.inner_html("#vkHost")
            d_attr = page.get_attribute(
                "#vkHost svg path.vk-line-path", "d")
            browser.close()
    finally:
        server.shutdown()
    assert d_attr and len(d_attr) > 10
    data = _load_json(os.path.join("skew-lens", "data.json"))
    fig = data["modelled_figures"][0]
    assert str(fig["put_percent"]) in host or \
        str(int(fig["put_percent"])) in host


# ---- A4: holly-ideas phone width --------------------------------

def test_holly_facts_line_can_wrap():
    html = _source(os.path.join("holly-ideas", "index.html"))
    facts = [ln for ln in html.splitlines() if ".idea .facts{" in ln]
    assert facts and "nowrap" not in facts[0]


def test_holly_render_fits_390px():
    from playwright.sync_api import sync_playwright
    import functools
    import http.server
    import threading
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=SITE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0),
                                             handler)
    threading.Thread(target=server.serve_forever,
                     daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 390,
                                              "height": 844})
            page.goto(f"http://127.0.0.1:{server.server_address[1]}"
                      "/holly-ideas/")
            page.wait_for_selector(".idea .facts", timeout=20000)
            width = page.evaluate(
                "document.documentElement.scrollWidth")
            facts_box = page.evaluate(
                "var f=document.querySelector('.idea .facts');"
                "var r=f.getBoundingClientRect();"
                "({right: r.right, text: f.textContent})")
            browser.close()
    finally:
        server.shutdown()
    assert width <= 390, width
    assert facts_box["right"] <= 390.5, facts_box
    assert facts_box["text"].strip()


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
