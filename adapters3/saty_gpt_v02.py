"""v3 sleeve module for saty_gpt_v02 — faithful port (batch 7).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_b7_blockers.py). This module
is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds the v2
SleeveContext from the cycle snapshot and delegates. The journal path
is set on the context so the v2 persisted-journal channel
(serve_journal / gpt_v02_journal) works across cycles.

R6 AGGREGATION CACHE (MIDNA RULING 2026-10-25, R-6 shape): before
delegating, the snapshot's SPY 5Min series is pre-aggregated to 10Min
on the production side (desk3/saty_v02_agg.py, bounded cache) and
supplied through the strategy's existing bars_10m door, so the
byte-identical strategy no longer re-derives its execution clock from
~8k 5Min bars via the O(bars x sessions) Calendar.session_at scan on
every pass (measured 5.30s -> 0.91s on the 2026-10-25 live snapshot;
output identity proven by the golden battery in
tests/test_saty_v02_agg_blockers.py: intents and the full evaluation
stamp identical, except stamp['frames'], which truthfully censuses
the door shape). Any anomaly (duplicate/unparseable 5Min bars, a
producer-supplied bars_10m, or no 5Min series) leaves the view
untouched and the original path runs exactly as before."""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "saty_gpt_v02"
INPUTS = ['bars', 'quotes', 'options', 'session_fills']


def _preaggregated_view(view):
    try:
        bars = (view or {}).get("bars") or {}
        rows5 = bars.get("SPY|5Min")
        if not rows5:
            return view
        if ((view.get("extra") or {}).get("bars_10m")):
            return view  # a producer already serves the 10m door
        from desk3.saty_v02_agg import cached_aggregate_10m
        agg = cached_aggregate_10m(rows5)
        if agg is None:
            return view  # anomaly: original path, untouched
        out = dict(view)
        new_bars = dict(bars)
        del new_bars["SPY|5Min"]
        out["bars"] = new_bars
        extra = dict(view.get("extra") or {})
        extra["bars_10m"] = {"SPY": agg}
        out["extra"] = extra
        return out
    except Exception:
        return view  # the cache can only decline, never break the pass


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, _preaggregated_view(view), ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.saty_gpt_v02").evaluate(sctx) or []
