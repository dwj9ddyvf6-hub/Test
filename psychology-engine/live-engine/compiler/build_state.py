#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import compile_state, live_collect
if __name__ == "__main__":
    # TRADING-PATH-VIX-20261031: an out-of-band compile advances
    # the state date, so it must run the Cboe collect first, or
    # the VIX line it publishes can lag the state date silently.
    # The daily lane already collects before compiling; this
    # manual entry point was the hole.
    print(live_collect("cboe"))
    import json; s = compile_state(); print(s["regime"], s.get("composite_percentile"))
