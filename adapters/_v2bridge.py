"""Shared v2<->old-contract bridge for batch-3 adapters — SHIM
(D9 cure, AUDIT-CURE-2).

All implementations live once in adapters/_bridge.py; this module
re-exports the _v2bridge profile under its historical names (it is
imported both as adapters._v2bridge and as top-level _v2bridge).
No strategy math here.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone  # noqa: F401  (historical import surface)
from zoneinfo import ZoneInfo  # noqa: F401

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from adapters import _bridge as _B
except ImportError:  # imported as a top-level module
    import _bridge as _B  # noqa: F401
from core.sleeve import Context as OldContext  # noqa: F401,E402

ET = _B.ET
_PI_SIDE = _B.PI_SIDE

_epoch = _B.epoch_v2
old_bars = _B.bars_v2
build_extra = _B.build_extra
old_context = _B.old_context_v2
_derive_side = _B._derive_side_v2
_derive_pi = _B._derive_pi_v2
to_v2_intents = _B.to_v2_intents
