"""The Ausar Tensor state-repair source, run as-is: desk/vendor/ausar_ts (vendored byte-exact from
codex-complete-archive artifacts/ausar-corrected-incomplete-2026-10-11 9de7747):

  * backend/tensor_runtime.py — the TensorRuntime manager (frame cycles, census, ranked entries, 20-bar exits)
    and its native-bar / calendar / cooldown functions;
  * backend/tensor_strategy.py — StateRepairPolicy (the frozen R11 rule, sizing, ranking);
  * backend/tensor_engine.py — the pinned v690 state-feature transport under Node
    (strategies/tensor_state_repair/engine, 26 files bound by SOURCE_MANIFEST.json, verified before execution);
  * backend/tensor_actions.py — TensorActions, the observed corporate actions of the strategy-owned books (Yahoo
    split / dividend events applied to the local ledger, dividend receivables, probe coverage before entries);
  * strategies/enrollment-1h.json / enrollment-1wk.json (1,820 / 1,813 names) and verified-ineligible-assets.json.

The runtime's and TensorActions' sibling imports are bound to package-scoped shims that hold the exact source
definitions they read — nothing else of those source modules exists here:
  * .providers: NY, utc_clock (backend/providers.py, verbatim) and _nyse -> the XNYS adapter
    (desk.feedlib.r19_source.DeskXNYS, identical to exchange_calendars XNYS 2000-2040 on every call made:
    tools/parity/r19_calendar.py);
  * .store: DeskError, symbol, cents, checked_cents, now (backend/store.py, verbatim);
  * .trading: ACTIVE (backend/trading.py, verbatim).
No source broker, order, transport or credential code is vendored or imported."""
import re
import sys
import types
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

PKG = "desk.vendor.ausar_ts.backend"
UTC = timezone.utc


class DeskError(Exception):
    def __init__(self, detail: str, status: int = 409):
        self.detail, self.status = detail, status
        super().__init__(detail)


def symbol(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{0,9}(?:[.-][A-Z0-9]{1,4})?", value) or len(value) > 15:
        raise DeskError("Enter a valid equity symbol, such as AAPL or BRK.B", 422)
    return value


def cents(value: Decimal) -> int:
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def checked_cents(value: int, name="Ledger value") -> int:
    """SQLite promotes overflowing arithmetic to REAL; reject it before writing."""
    if not isinstance(value, int) or not -(2 ** 63) <= value <= 2 ** 63 - 1:
        raise DeskError(name + " exceeds the exact integer-cents ledger range", 422)
    return value


def now() -> str:
    return datetime.now(UTC).isoformat()


def utc_clock(clock=None):
    value = clock or datetime.now(UTC)
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise DeskError("Clock must have a timezone", 422)
    return value.astimezone(UTC)


ACTIVE = {"queued", "open", "partially_filled", "blocked", "submitting", "cancel_requested"}
NY = ZoneInfo("America/New_York")


def install_shims():
    from .r19_source import DeskXNYS
    if PKG + ".store" not in sys.modules:
        m = types.ModuleType(PKG + ".store")
        m.__doc__ = "desk shim: backend/store.py's DeskError, symbol, cents, checked_cents and now (verbatim)"
        m.DeskError, m.symbol, m.cents, m.checked_cents, m.now = DeskError, symbol, cents, checked_cents, now
        sys.modules[PKG + ".store"] = m
    if PKG + ".providers" not in sys.modules:
        m = types.ModuleType(PKG + ".providers")
        m.__doc__ = "desk shim: backend/providers.py's NY and utc_clock (verbatim); _nyse -> the XNYS adapter"
        m.NY, m.utc_clock, m._nyse = NY, utc_clock, DeskXNYS
        sys.modules[PKG + ".providers"] = m
    if PKG + ".trading" not in sys.modules:
        m = types.ModuleType(PKG + ".trading")
        m.__doc__ = "desk shim: backend/trading.py's ACTIVE intent statuses (verbatim)"
        m.ACTIVE = ACTIVE
        sys.modules[PKG + ".trading"] = m


def vendored():
    install_shims()
    import importlib
    return {n: importlib.import_module(PKG + "." + n)
            for n in ("tensor_runtime", "tensor_strategy", "tensor_engine", "tensor_actions")}
