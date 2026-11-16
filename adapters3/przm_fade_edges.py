"""v3 sleeve module for przm_fade_edges (PRZM-RECREATION-SPEC-2026-10-29).

Strategy in sleeves/przm_fade_edges.py; plumbing adapter in
adapters/przm_fade_edges.py. LIVE, not parked: the config row of
record (config/sleeves.json) is parked=false, unparked 2026-11-14
(FEED80-PRZM-20261114) when its stated condition was met -- chain
rows now carry gamma+OI (open_interest passed through from the
contracts route; gamma computed by BS at the IV inverted from each
row's own indicative mid, stamped gamma_source=
bs_inverted_indicative_v1). Gamma levels are computed from that
route today; the engine's WAITING_NO_GAMMA_LEVELS state now occurs
only when the real chain has no GEX sign change, a market state
(the config row's parked_reason keeps the full provenance).
CONFIG-TRUTH-20261116 corrected this docstring, which had kept the
install-era parked claim two days after the unpark. INPUTS keeps
the SPY 1-minute SIP bars + options_chain declarations the engine
consumes.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "przm_fade_edges"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'options', 'options_chain', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.przm_fade_edges").evaluate(sctx) or []
