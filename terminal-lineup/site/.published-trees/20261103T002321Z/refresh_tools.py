#!/usr/bin/env python3
"""Daily refresh runner for the terminal tools that are not engines.

Hookup cure (terminal-total-hookup, 2026-10-29): 50 tool refreshers
ran only by hand. The engine runner (refresh_engines.py) covers the
30 forecast engines plus a few tools named in the forecast program
record, the tape orchestrator (tape_family_run.py) covers the nine
tape consumers, and the daily stores job covers Dark Prints, Short
Volume and State Analogue. Everything else drifted: consumers read
older sessions than their producers (Board behind Screener,
Horizon Grades and Signal Feed behind the Record and Flow Tape,
the Strat family behind the panel), because no scheduled run owned
them and no order was enforced.

This runner is that single run for the remaining tools:
- It runs the refreshers in dependency order: producers first
  (Morning Map, Board, chain, calendar), then the panel family and
  the Strat family built on it, then the slow money and options
  families, then the assemblies that read other tools, then a
  re-run of the tape family orchestrator so Agent Debate is
  refreshed after Second Opinion has advanced (its cross-family
  session refusal was the named stale stamp in cure stream D),
  and the two audit tools (Receipts, Proving Ground) last of all,
  so their coverage is assembled from the freshest records.
- A refresher that exits non-zero is named in the failure list and
  the run exits 1. Its page keeps its previous data; the failure
  is loud, never hidden.
- The Record is not re-run here: the engine runner owns it and
  runs earlier the same evening. Horizon Grades and Signal Feed
  run in the assembly group, after the Board and tape families
  they aggregate.

Usage: python3 refresh_tools.py
Exit 0 only when every refresher in the chain succeeds.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

try:
    import terminal_common as _tc
except ImportError:  # runner stays runnable standalone
    _tc = None

GROUPS = [
    ("producers", [
        "refresh_morning_map.py",
        "refresh_board.py",
        "refresh_chain.py",
        # Expected Move Map (EXPECTED-MOVE-FILING-20261030): its
        # refresher ran only by hand, so the page drifted behind
        # its filing log. It runs here, after the chain refresh
        # its chain_map leg reads.
        "refresh_expected_move.py",
        "refresh_pinwatch.py",
        "refresh_earningscal.py",
        "refresh_weekahead.py",
    ]),
    ("panel and strat family", [
        "refresh_breadth.py",
        "refresh_rotation.py",
        "refresh_screener.py",
        # The Strat Scanner is the producer for the whole chart
        # family: AI Chart Read, Breakout Scanner, Momentum Clock
        # and Pattern Draw all fail closed when the label record
        # ends on an older session than the price history, so the
        # scanner and its direct consumers run before them, and
        # Pattern Draw (which reads the chart history AI Chart
        # Read ships) runs after AI Chart Read (hookup cure,
        # 2026-10-29: the original order ran the consumers first
        # and all four refused on the frozen 2026-10-23 labels).
        "refresh_stratscanner.py",
        "refresh_stratcombos.py",
        "refresh_reversalwire.py",
        "refresh_aichartread.py",
        "refresh_breakoutscanner.py",
        "refresh_correlation.py",
        "refresh_momentumclock.py",
        "refresh_grademycall.py",
        "refresh_unusualvolume.py",
        "refresh_patterndraw.py",
        "refresh_gammaladder.py",
        "refresh_staticgex.py",
        "refresh_hollyideas.py",
        "refresh_portfolio.py",
    ]),
    ("slow money and options families", [
        "refresh_insider.py",
        "refresh_13ftracker.py",
        "refresh_smartmoney.py",
        "refresh_filings.py",
        "refresh_squeeze.py",
        "refresh_ivweather.py",
        "refresh_skewlens.py",
        "refresh_fearday.py",
        "refresh_feardayforecaster.py",
        "refresh_gapfill.py",
        "refresh_openingrange.py",
        "pullback_study.py",
        "refresh_pullback.py",
        "refresh_echolens.py",
    ]),
    ("assemblies", [
        "refresh_second_opinion.py",
        "refresh_promotedbook.py",
        "refresh_echoboard.py",
        "refresh_watchlistpulse.py",
        "refresh_regime.py",
        "refresh_signalfeed.py",
        "refresh_horizongrades.py",
        "refresh_decaywatch.py",
        "refresh_router.py",
        "refresh_survivorswire.py",
        "refresh_graveyard.py",
        "refresh_oddscards.py",
        "refresh_onepagereport.py",
    ]),
    ("audit tools last", [
        "refresh_proofgate.py",
        "refresh_receipts.py",
        "refresh_provingground.py",
    ]),
]


def run_one(script):
    print(f"start {script}", flush=True)
    t0 = time.time()
    r = subprocess.run([sys.executable, str(HERE / script)],
                       capture_output=True, text=True)
    dt = time.time() - t0
    print(f"done {script} in {dt:.0f}s exit {r.returncode}", flush=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        if tail:
            print(f"  last line: {tail[-1]}", flush=True)
    return r.returncode


def main():
    failures = []
    ran = 0
    # Panel advance first (PANEL-SAME-DAY-20261031): the panel
    # family below reads the price panel, whose advance lane
    # defaults to the freshest completed session. Running it at
    # the head of this 19:00 chain gives the panel family its
    # own same-evening producer, so a Friday session lands on
    # Friday evening instead of waiting for the next weekday's
    # engine run. A failed advance is named as a failure and the
    # refreshers still run on the panel on record (they fail
    # closed where their session guards require agreement), so
    # the lag is loud, never silent.
    print("group: price panel advance", flush=True)
    if run_one("advance_price_panel.py") != 0:
        failures.append("advance_price_panel.py")
    else:
        ran += 1
    for group, scripts in GROUPS:
        print(f"group: {group}", flush=True)
        for script in scripts:
            if not (HERE / script).exists():
                failures.append(f"{script} (missing)")
                continue
            if run_one(script) != 0:
                failures.append(script)
            else:
                ran += 1
    # Tape family re-sync, after Second Opinion has advanced in the
    # assembly group: Agent Debate reads both the tape family and
    # Second Opinion, so it can only go current after both have run.
    print("group: tape family re-sync", flush=True)
    if run_one("tape_family_run.py") != 0:
        failures.append("tape_family_run.py")
    else:
        ran += 1
    # Panel consumer re-sync (PANEL-RESYNC-20261031): every page
    # whose published stamp derives from the price panel
    # (board_bt_bars.json) must run AFTER the panel's last advance
    # of the day. The three earnings and insider engines, the
    # intake and family engines and the priced move record are
    # owned by the engines chain, which runs earlier; when the
    # panel advance at the head of THIS chain (or the morgue
    # postclose rescore) landed a newer session than the engines
    # chain saw, those consumers stayed one session behind until
    # the next weekday (proven 2026-10-31: the panel reached
    # 2026-10-30 at 05:46 UTC while earnings-distribution,
    # insider-divergence and gamma-earnings-trap still published
    # panel_last_session 2026-10-29 and every priced name still
    # carried spot_session 2026-10-29). This group re-runs every
    # panel_last_session publisher and the priced move record
    # against the panel as it stands at the end of this chain,
    # then the earnings calendar, which republishes the priced
    # moves, from the fresh record. A failure is named like any
    # other leg and the run exits 1.
    print("group: panel consumer re-sync", flush=True)
    for script in ("priced_moves.py",
                   "refresh_earningsdistribution.py",
                   "refresh_insiderdivergence.py",
                   "refresh_gammaearningstrap.py",
                   "refresh_intakebias.py",
                   "refresh_familyfracture.py",
                   "refresh_earningscal.py"):
        if not (HERE / script).exists():
            failures.append(f"{script} (missing)")
            continue
        if run_one(script) != 0:
            failures.append(script)
        else:
            ran += 1
    # Source clock diagnostic last: it reads the refresh logs the
    # day's runs have written, so it can only go current after them.
    print("group: source clock diagnostic", flush=True)
    if run_one("source_clock_diagnostic.py") != 0:
        failures.append("source_clock_diagnostic.py")
    else:
        ran += 1
    # D-HUB cure (2026-10-30): the hub page had no producer at all;
    # its counts, chips and as-of dates were hand-typed and aged.
    # refresh_hub.py recomputes those factual parts from each card
    # page's own data file. It runs here, after every page in every
    # evening chain has refreshed and before the manifest rebuild,
    # so the hub publishes the day's final state and the manifest
    # and smoke check see it.
    print("group: hub refresh", flush=True)
    if run_one("refresh_hub.py") != 0:
        failures.append("refresh_hub.py")
    else:
        ran += 1
    # A-D4 cure: rebuild the asset manifest and re-run the served
    # smoke check at the end of the last scheduled writer of the
    # evening, so the manifest is current overnight instead of
    # going stale from 19:00 until the next engine run.
    print("group: record surface enrich", flush=True)
    if run_one("enrich_all.py") != 0:
        failures.append("enrich_all.py")
    else:
        ran += 1
    print("group: manifest rebuild and smoke check", flush=True)
    verify = subprocess.run(["bash", str(HERE / "verify_terminal.sh")],
                            capture_output=True, text=True)
    print(verify.stdout.strip().splitlines()[-1] if verify.stdout.strip() else "",
          flush=True)
    if verify.returncode != 0:
        failures.append("verify_terminal.sh (manifest rebuild)")
    # Publish step (serve-live route, 2026-10-31): after verify, prove
    # the always-on server serves this exact tree (publish_live.py).
    pub = subprocess.run([sys.executable, str(HERE / "publish_live.py")],
                         capture_output=True, text=True)
    print(pub.stdout.strip().splitlines()[-1] if pub.stdout.strip() else "",
          flush=True)
    if pub.returncode != 0:
        failures.append("publish proof (publish_live.py) failed")
    # Provenance stamp (R-09 cure, 2026-10-30): this runner
    # publishes no page of its own, so its run summary is the
    # record it stamps, the same shipyard stamp every refresher
    # it runs carries on its page.
    summary = {"runner": "refresh_tools.py",
               "tool_refreshers_succeeded": ran, "failures": failures}
    summary = _tc.stamp_for_script(summary, __file__) \
        if _tc is not None else summary
    print(f"run provenance: feed={summary.get('feed')} "
          f"price_basis={summary.get('price_basis')} "
          f"execution_pricing={summary.get('execution_pricing')}")
    print(f"tool refreshers succeeded: {ran}")
    if failures:
        print("FAILURES: " + "; ".join(failures))
        return 1
    print("FAILURES: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
