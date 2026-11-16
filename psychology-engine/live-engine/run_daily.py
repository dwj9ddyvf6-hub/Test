#!/usr/bin/env python3
"""Daily lane: live collectors, compile, consumer file, page, ledger hooks."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import live_all, compute_gauges, compile_state, render_page, fire_hooks
if __name__ == "__main__":
    res = live_all()
    # A4-7 GAUGE-WIRING (NO-PARTIALS DRIVE 2026-11-11): compute_gauges
    # had ZERO callers repo-wide, so the daily lane only READ the
    # gauge CSVs (compile_state's read_gauge) and the gauges froze
    # at their last manual regeneration (G1-G6/G8-G9 at 2026-10-31;
    # G7 hand-regenerated 2026-11-10). Compute runs here, between
    # collection and compile, on every daily run.
    gauges = compute_gauges()
    state = compile_state()
    page = render_page()
    hooks = fire_hooks(state)
    print(f"PSYCHOLOGY ENGINE RECEIPT gauges={len(state['gauges'])} regime={state['regime']} "
          f"composite={state.get('composite_percentile')} hooks={hooks} page={page} live={res}")
