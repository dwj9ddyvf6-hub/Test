"""Shared interface glue for batch-7 ports — SHIM (D9 cure, AUDIT-CURE-2).

All implementations live once in adapters/_bridge.py; this module
re-exports the batch-7 profile under its historical names. No
strategy math here: bars/positions are re-shaped per the batch-7
contract preserved in the canonical module, and quantities/prices
are carried from the strategy's own Intent (qty default 1 when the
strategy declares none, stamped in the reason — see _bridge).
"""
from __future__ import annotations

import importlib  # noqa: F401  (historical import surface)
import os
import re  # noqa: F401
import sys
from datetime import datetime, timezone  # noqa: F401

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from adapters import _bridge as _B
except ImportError:  # imported as a top-level module
    import _bridge as _B  # noqa: F401
from core.sleeve import Context as OldContext  # noqa: F401,E402

_SIDE_FOR_PI = _B.PI_SIDE

_epoch = _B.epoch_old
old_bars = _B.bars_old
first_bars = _B.first_bars_old
sleeve_state = _B.state_old
equity_of = _B.equity_of
translate = _B.translate_old
run_old_signal = _B.run_old_signal
run_old_persisted = _B.run_old_persisted
