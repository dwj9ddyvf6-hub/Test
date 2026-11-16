"""Batch-5 adapter glue — SHIM (D9 cure, AUDIT-CURE-2).

All implementations live once in adapters/_bridge.py; this module
re-exports the batch-5 profile under its historical names. Strategy
math lives verbatim in sleeves/<id>.py; no strategy logic here.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime  # noqa: F401  (historical import surface)
from zoneinfo import ZoneInfo  # noqa: F401

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from adapters import _bridge as _B
except ImportError:  # imported as a top-level module
    import _bridge as _B  # noqa: F401
from core.sleeve import Context as OldContext  # noqa: F401,E402

ET = _B.ET
_PI_SIDE = _B.PI_SIDE

_epoch = _B.epoch_batch5
bar_dicts = _B.bars_batch5
bars_map = _B.bars_map_batch5
session_of = _B.session_of
equity_of = _B.equity_of
state_from_positions = _B.state_batch5
old_context = _B.old_context_batch5
translate = _B.translate_batch5
run_old = _B.run_old_batch5
run_old_persisted = _B.run_old_batch5_persisted
