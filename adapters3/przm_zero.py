"""v3 sleeve module for przm_zero (PRZM-RECREATION-SPEC-2026-10-29).

Strategy in sleeves/przm_zero.py; plumbing adapter in
adapters/przm_zero.py. PRZM-TAPE-20261114 (CLEAR THE BOARD WS3): the
signed options print tape is now served by PrzmTapeProducer
(desk3/przm_tape.py, real Alpaca v1beta1 prints, provenance in the
module docstring); evaluate() injects the view's przm_prints into
the adapter's params extra when config params carry none, so the
frozen strategy consumes them through its authored channel.
Outside the RTH window the producer serves nothing and the sleeve
keeps its named WAITING_NO_PRINT_TAPE state.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "przm_zero"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'options', 'options_chain', 'positions', 'quotes', 'session_fills', 'przm_prints']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    # PRZM-TAPE-20261114: serve the producer's tape through the
    # strategy's authored params channel when config carries none.
    prints = (view or {}).get("przm_prints")
    if prints:
        extra = dict(sctx.params.get("extra") or {})
        if not extra.get("przm_prints"):
            extra["przm_prints"] = prints
            sctx.params["extra"] = extra
    return importlib.import_module("adapters.przm_zero").evaluate(sctx) or []
