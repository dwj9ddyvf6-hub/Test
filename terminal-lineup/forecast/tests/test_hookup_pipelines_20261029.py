"""Regression blockers for the terminal hookup pipelines cure
(2026-10-29, stream 2).

Each test fails on the pre-cure state:
- 49 tool refreshers ran only by hand and no runner owned them
  (refresh_tools.py did not exist).
- The Expected Move page shipped chain_map in its data file but
  never rendered it.
- The hub described the pre-cure chain state (no snapshot on
  record, 0 snapshots) and the stale October 12 earnings list.
- Receipts and Proving Ground claimed coverage of every tool
  while carrying 18 and 42 entries; their pages now state the
  partial coverage plainly.
"""

import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "..", "site")


def read(rel):
    with open(os.path.join(SITE, rel), encoding="utf-8") as fh:
        return fh.read()


def test_refresh_tools_covers_every_manual_refresher():
    src = read("refresh_tools.py")
    tree = ast.parse(src)
    groups = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(
                node.targets[0], "id", "") == "GROUPS":
            groups = ast.literal_eval(node.value)
    assert groups is not None
    chained = [s for _name, scripts in groups for s in scripts]
    # Every refresher not owned by the engine runner, the tape
    # orchestrator, or the daily stores job must be chained here.
    manual = [
        "refresh_morning_map.py", "refresh_board.py",
        "refresh_chain.py", "refresh_pinwatch.py",
        "refresh_earningscal.py", "refresh_weekahead.py",
        "refresh_breadth.py", "refresh_rotation.py",
        "refresh_screener.py", "refresh_aichartread.py",
        "refresh_breakoutscanner.py", "refresh_correlation.py",
        "refresh_momentumclock.py", "refresh_grademycall.py",
        "refresh_unusualvolume.py", "refresh_stratscanner.py",
        "refresh_stratcombos.py", "refresh_reversalwire.py",
        "refresh_patterndraw.py", "refresh_gammaladder.py",
        "refresh_hollyideas.py", "refresh_portfolio.py",
        "refresh_insider.py", "refresh_13ftracker.py",
        "refresh_smartmoney.py", "refresh_filings.py",
        "refresh_squeeze.py", "refresh_ivweather.py",
        "refresh_skewlens.py", "refresh_fearday.py",
        "refresh_feardayforecaster.py", "refresh_gapfill.py",
        "refresh_openingrange.py", "refresh_pullback.py",
        "refresh_echolens.py", "refresh_second_opinion.py",
        "refresh_promotedbook.py",
        "refresh_echoboard.py", "refresh_watchlistpulse.py",
        "refresh_regime.py", "refresh_signalfeed.py",
        "refresh_horizongrades.py", "refresh_decaywatch.py",
        "refresh_router.py", "refresh_survivorswire.py",
        "refresh_graveyard.py", "refresh_oddscards.py",
        "refresh_onepagereport.py", "refresh_receipts.py",
        "refresh_provingground.py",
    ]
    for script in manual:
        assert script in chained, script
        assert os.path.exists(os.path.join(SITE, script)), script
    # Audit tools run last, after every assembly they describe.
    assert groups[-1][1] == ["refresh_proofgate.py",
                             "refresh_receipts.py",
                             "refresh_provingground.py"]
    # The tape family is re-run after the assemblies so Agent
    # Debate refreshes after Second Opinion advances.
    assert "tape_family_run.py" in src


def test_expected_move_page_renders_chain_map():
    page = read(os.path.join("expected-move", "index.html"))
    assert 'id="chainmap"' in page
    assert "data.chain_map" in page
    assert "Chain map from the freshest snapshot" in page


def test_hub_has_no_stale_pre_cure_claims():
    hub = read("index.html")
    for stale in (
            "No chain snapshot is on record yet",
            "the chain archive holds 0 snapshots",
            "list recorded on October 12, 2026",
            "75 alerts kept for Tuesday, October 27, 2026",
            "2 days are on record (October 26 and 27, 2026)",
            "the two recorded trading days (October 26 and 27, 2026)",
            "four real alerts from Tuesday, October 27, 2026"):
        assert stale not in hub, stale
    cards = re.findall(r'<article class="hubcard".*?</article>',
                       hub, re.S)
    assert len(cards) == 100
    hrefs = [re.search(r'href="([a-z0-9-]+)/"', c).group(1)
             for c in cards]
    assert len(set(hrefs)) == 100


def test_audit_pages_state_partial_coverage():
    assert "Coverage is partial" in read(
        os.path.join("receipts", "index.html"))
    assert "Coverage is partial" in read(
        os.path.join("proving-ground", "index.html"))
    hub = read("index.html")
    assert "Coverage is partial today" in hub


def test_engine12_reads_the_producers_governing_calendar():
    # Engine 12 fail-closed on every run after the earnings
    # calendar producer moved to the re-checked record: it kept
    # rebuilding its calendar from the two raw desk records and
    # demanded their 2026-10-12 stamp equal the published stamp.
    src = read("refresh_earningsdistribution.py")
    assert "FRESH_CAL_PATH" in src
    assert "governing_cal_paths" in src
    # Its recorded in-history reconstruction is pinned to the
    # recorded panel shape as a prefix of the advanced panel,
    # never to the panel's current length.
    assert "spy_recorded" in src
    assert 'spy_rows[-1][0] != EXPECT_PANEL_LAST' not in src


def test_consumers_do_not_demand_cross_producer_session_equality():
    # The recurring defect class of this stream: a consumer
    # demanding that a different producer's session field equal
    # its own, which refused every coherent cycle once the
    # producers' rhythms diverged by one session.
    tools = read("refresh_tools.py")
    panel = tools.split('"panel and strat family"')[1].split("]),")[0]
    assert panel.index("refresh_stratscanner.py") < panel.index(
        "refresh_aichartread.py")
    assert panel.index("refresh_aichartread.py") < panel.index(
        "refresh_patterndraw.py")
    gamma = read("refresh_gammaladder.py")
    assert 'pinwatch.get("newest_session")' not in gamma
    assert "pins_counted" in gamma
    pullback = read("refresh_pullback.py")
    assert 'feed.get("as_of_session") != card.get("as_of")' \
        not in pullback
    assert 'history["sessions"] < 399' in pullback
    chain = read("refresh_chain.py")
    assert 'lane.get("last_date") != as_of' in chain
    so = read("refresh_second_opinion.py")
    assert "if tape_session < session:" in so
    debate = read("refresh_agentdebate.py")
    assert 'fb.get("freshest_session")' in debate
    assert 'c.get("session") == fb.get("freshest_session")' in debate
    tape_run = read("tape_family_run.py")
    assert "JOINED_CONSUMERS" in tape_run


def test_signal_feed_matches_graded_records():
    # Signal Feed pinned two pre-grading states: the Record's
    # map cards had to be ungraded forever, and the Flow Tape's
    # note had to claim its alerts were ungraded forever. Both
    # records grade now; the feed derives per-card states and
    # verifies the count, and the tape's note is generated from
    # the grading record.
    sf = read("refresh_signalfeed.py")
    assert "map_card_graded" in sf
    assert "Grading has landed" in sf
    ft = read("refresh_flow_tape.py")
    assert "grading_note_text()" in ft
    assert "GRADES_PATH" in ft


def test_engine_pages_state_follows_the_record():
    # Static page words that contradicted the same file's own
    # counts: Engine 20 claimed no round issued beside
    # rounds_issued 1; Engine 27 claimed no pin and no recorded
    # morning beside pins 3 and records 2 graded; Engine 28
    # printed a recorded count from one quantity beside a graded
    # count from all of them.
    e20 = read("refresh_calibrationleague.py")
    assert 'if rounds_issued else' in e20
    e27 = read("refresh_pinorescape.py")
    assert 'if pins_on_record else' in e27
    assert 'if mine["forecasts"] else' in e27
    e28 = read("refresh_gapdestiny.py")
    assert '"forecasts_recorded": mine["forecasts"]' in e28
    assert '"gap_sets_recorded": main_recorded' in e28


def test_exceedance_build_series_matches_brute_force():
    # The runtime cure replaced per-session window sorts with
    # sliding sorted windows and prefix sums. On a synthetic
    # series the flags and scores must match the original
    # brute-force construction exactly.
    import importlib.util
    import math
    spec = importlib.util.spec_from_file_location(
        "refresh_exceedance",
        os.path.join(SITE, "refresh_exceedance.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = []
    price = 100.0
    for i in range(300):
        price *= 1.0 + 0.01 * math.sin(i * 0.7) + (
            0.02 if i % 37 == 0 else 0.0)
        rows.append(["2026-01-%02d" % (i % 28 + 1), price * 0.99,
                     price * 1.01, price * 0.98, price, 1000])
    got = mod.build_series(rows, {})
    # Brute-force thresholds from the shipped definition.
    for t in range(mod.FLAG_START, 300):
        g = mod.quantile(got["abs_gap"][t - mod.FLAG_WINDOW:t],
                         mod.TOP_FIFTH)
        v = mod.quantile(got["vols"][t - mod.FLAG_WINDOW:t],
                         mod.TOP_FIFTH)
        assert got["gap_flag"][t] == (got["abs_gap"][t] >= g), t
        assert got["vol_flag"][t] == (got["vols"][t] >= v), t
        assert got["score"][t] == int(got["gap_flag"][t]) + int(
            got["vol_flag"][t]), t


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    sys.exit(0)
