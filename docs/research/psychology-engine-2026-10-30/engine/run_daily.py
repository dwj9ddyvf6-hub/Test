#!/usr/bin/env python3
"""Daily lane: live collectors, compile, consumer file, page, ledger hooks."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import live_all, compile_state, render_page, fire_hooks
if __name__ == "__main__":
    res = live_all()
    state = compile_state()
    page = render_page()
    hooks = fire_hooks(state)
    print(f"PSYCHOLOGY ENGINE RECEIPT gauges={len(state['gauges'])} regime={state['regime']} "
          f"composite={state.get('composite_percentile')} hooks={hooks} page={page} live={res}")
