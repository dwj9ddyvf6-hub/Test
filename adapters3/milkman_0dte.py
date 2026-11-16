"""v3 sleeve module for mk_zerodte_spx (Milkman 0DTE SPX).

Strategy in sleeves/milkman_0dte.py; plumbing adapter in
adapters/milkman_0dte.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from
the cycle snapshot and delegates.

INPUTS is the producer-registry declaration. MILKMAN-CHAIN-
20261114 (CLEAR THE BOARD WS3): 'milkman_0dte_chain' is now served
by MilkmanChainProducer (desk3/milkman_chain.py) in the RTH
window: real indicative bid/ask, spot recovered by put-call
parity, delta COMPUTED per row and stamped
delta_source=bs_parity_indicative_v1 (rows that do not invert
keep delta None, the strategy's authored fail-closed path).
evaluate() injects the payload as options_chain("SPX") on a
shallow copy of the view — the shared options product is never
mutated and never carries the computed delta (that question, for
the gamma pair, is a separate Triad decision).

MILKMAN-0DTE-PORT-20261116: PROVENANCE gap 1 is CLOSED. The
Milkman intraday study is ported (desk3/milkman_0dte/
intraday_study.py, the logic-identical port of Femto-lean
desk/sleeves/milkman/intraday.py at milkman-0dte@8c64cd5c,
vendored byte-exact beside it as intraday.py with the study's
own mlib.py), and adapters/milkman_0dte.py builds its Panel from
the snapshot's SPY bars — hence the 'bars_1min' and
'bars:SPY:1Min' declarations below (the warm SPY 1-minute SIP
product, the same door the other SPY intraday sleeves declare) —
and fills lane_signals / lane_exits with the study's authored
lane trades under the vendored sleeve's own eligibility rules.
One lane-level data-depth limitation stands, named in the port
and in PROVENANCE.md: the LEMA lane's train-period (2000-2012)
threshold cannot be computed from the snapshot's 500-day daily
history, so that lane alone produces no live signals; the rule
is ported and fixture-proven, and every other lane runs.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "mk_zerodte_spx"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'positions', 'milkman_0dte_chain']


def evaluate(view, ctx):
    import importlib
    v = view or {}
    payload = v.get("milkman_0dte_chain")
    if payload:
        v = dict(v)
        opts = dict(v.get("options") or {})
        opts["SPX"] = payload
        v["options"] = opts
    sctx = SnapshotSleeveContext(SLEEVE_ID, v, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.milkman_0dte").evaluate(sctx) or []
