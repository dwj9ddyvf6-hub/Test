"""Shared v2->old-interface translation — SHIM (D9 cure, AUDIT-CURE-2).

All implementations live once in adapters/_bridge.py; this module
re-exports the _common profile under its historical names so existing
adapter imports (`from adapters._common import *`, CANDIDATES, ...)
keep working byte-for-byte. No strategy math here.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone  # noqa: F401  (historical star-import surface)
from zoneinfo import ZoneInfo  # noqa: F401

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from adapters import _bridge as _B
except ImportError:  # imported as a top-level module
    import _bridge as _B  # noqa: F401

CANDIDATES = _B.CANDIDATES
ET = _B.ET
OldContext = _B.OldContext

_epoch = _B.epoch_common
bar_dict = _B.bar_dict_common
fetch_bars = _B.fetch_bars
symbols_for = _B.symbols_for
sleeve_state_from_positions = _B.state_common
make_old_context = _B.make_old_context
translate_intents = _B.translate_common
held_map = _B.held_map
