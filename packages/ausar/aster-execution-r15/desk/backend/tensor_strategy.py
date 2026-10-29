"""Frozen, long-only Tensor state-repair rules for independent paper books.

This module does not fetch data, place orders, mutate cooldowns, or fit models.
``StateRepairPolicy.evaluate`` consumes the native adapter's TensorSnapshot (or
an equivalent dict). Features must be the last four *observed* native bars,
with explicit millisecond availability clocks and the canonical vote order
``stoch, aroon, di, obv, squeeze, pivot, wave``. The caller persists each
origin's ``next_eligible_bar_index`` even when cash/capacity denies the entry.

An entry is at the next observed native open; its exit is at the open whose
index is ``actual_entry_bar_index + 20``. Neither is a wall-clock duration.
Hourly and weekly policies operate separate books. Their performance cannot
be added into an untested combined portfolio.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_FLOOR, localcontext
import hashlib
import json
import math
import re
from typing import Any, ClassVar


VOTE_NAMES = ("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave")
EXCLUDED_SYMBOLS = frozenset({"SPY", "QQQ", "B", "GOLD"})
RESEARCH_SOURCE_SHA256 = "7c993b29e2232d68f1fe2f98c08a9584bad7fff172b8083e51c22fa9429ef69f"
_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
_SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")


def _field(value: Any, name: str) -> Any:
    return value[name] if isinstance(value, Mapping) else getattr(value, name)


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"invalid {label}")
    return value


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"invalid {label}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"nonfinite {label}")
    return result


def _hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError(f"invalid {label}")
    return value.lower()


def _decimal(value: Any, label: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"invalid {label}")
    result = Decimal(str(value))
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError(f"invalid {label}")
    return result


@dataclass(frozen=True)
class StateRepairSignal:
    """A causal opportunity; eligibility is distinct from a funded order."""

    signal_id: str
    symbol: str
    frame: str
    origin_bar_index: int
    origin_bar_id: str
    source_origin_timestamp_ms: int
    decision_at_ms: int
    earliest_entry_bar_index: int
    next_eligible_bar_index: int
    hold_native_bars: int
    balance: int
    balance_change_3: int
    increasing_vote_count: int
    score: float
    close: float
    atr14: float
    volume: float
    dollar_volume20: float
    source_manifest_sha256: str
    input_sha256: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class StateRepairDecision:
    signal: StateRepairSignal | None
    reason: str

    @property
    def originated(self) -> bool:
        return self.signal is not None


@dataclass(frozen=True)
class EntrySizing:
    """Whole-share debit including the frozen ten-basis-point buy cost."""

    shares: int
    execution_price: Decimal
    capped_budget: Decimal
    gross: Decimal
    fee: Decimal
    total_debit: Decimal
    settled_cash_after: Decimal
    reason: str

    @property
    def allowed(self) -> bool:
        return self.shares > 0


@dataclass(frozen=True)
class _Point:
    index: int
    bar_id: str
    timestamp_ms: int
    completed_at_ms: int
    usable_at_ms: int
    origin_ms: int
    status: str
    votes: tuple[int | None, ...]
    balance: int
    total_votes: int
    close: float
    atr14: float
    volume: float
    obv_slope5: float
    dollar_volume20: float


def _point(value: Any, symbol: str, frame: str, as_of_ms: int) -> _Point:
    if _field(value, "symbol") != symbol or _field(value, "frame") != frame:
        raise ValueError("feature identity mismatch")
    index = _integer(_field(value, "bar_index"), "bar index")
    bar_id = _field(value, "bar_id")
    if not isinstance(bar_id, str) or not bar_id or len(bar_id) > 256:
        raise ValueError("invalid bar id")
    timestamp = _integer(_field(value, "timestamp_ms"), "timestamp")
    completed = _integer(_field(value, "completed_at_ms"), "completion")
    usable = _integer(_field(value, "usable_at_ms"), "availability")
    origin = _integer(_field(value, "source_origin_timestamp_ms"), "source origin")
    if not origin <= timestamp < completed <= usable <= as_of_ms:
        raise ValueError("noncausal feature clocks")
    status = _field(value, "native_status")
    if status not in {"ready", "warming"}:
        raise ValueError("invalid native status")
    raw_votes = _field(value, "votes")
    if isinstance(raw_votes, Mapping):
        if set(raw_votes) != set(VOTE_NAMES):
            raise ValueError("invalid vote channels")
        votes = tuple(raw_votes[name] for name in VOTE_NAMES)
    elif isinstance(raw_votes, Sequence) and not isinstance(raw_votes, (str, bytes)):
        votes = tuple(raw_votes)
    else:
        raise ValueError("invalid votes")
    if len(votes) != 7 or any(v is not None and (type(v) is not int or v not in (-1, 1)) for v in votes):
        raise ValueError("invalid signed votes")
    bullish = _integer(_field(value, "bullish_votes"), "bullish count")
    bearish = _integer(_field(value, "bearish_votes"), "bearish count")
    total = _integer(_field(value, "total_votes"), "total count")
    if bullish != votes.count(1) or bearish != votes.count(-1) or total != bullish + bearish:
        raise ValueError("vote counts do not reconcile")
    close = _finite(_field(value, "close"), "close")
    atr = _finite(_field(value, "atr14"), "ATR")
    volume = _finite(_field(value, "volume"), "volume")
    slope = _finite(_field(value, "obv_slope5"), "OBV slope")
    dv = _finite(_field(value, "dollar_volume20"), "native dollar volume")
    if close <= 0 or atr < 0 or volume < 0 or dv < 0:
        raise ValueError("invalid price/ATR/volume")
    return _Point(index, bar_id, timestamp, completed, usable, origin, status,
                  votes, bullish - bearish, total, close, atr, volume, slope, dv)


@dataclass(frozen=True)
class StateRepairPolicy:
    """Exact R11 mechanism preset, bound to a frozen engine manifest.

    ``source_manifest_sha256`` is mandatory: obtain it from the native
    adapter's frozen source manifest, then persist it with the book config.
    All economic parameters are constants, not tunable constructor fields.
    """

    frame: str
    source_manifest_sha256: str
    NAME: ClassVar[str] = "TENSOR_STATE_REPAIR"
    VERSION: ClassVar[str] = "r11-paper-v1"
    HOLD_NATIVE_BARS: ClassVar[int] = 20
    COOLDOWN_NATIVE_BARS: ClassVar[int] = 20
    MAX_POSITIONS: ClassVar[int] = 10
    SIDE_COST: ClassVar[Decimal] = Decimal("0.001")

    def __post_init__(self) -> None:
        if self.frame not in {"1h", "1wk"}:
            raise ValueError("state repair permits only separate 1h and 1wk books")
        object.__setattr__(self, "source_manifest_sha256", _hash(self.source_manifest_sha256, "source manifest hash"))

    @property
    def manifest(self) -> dict:
        return {
            "name": self.NAME, "version": self.VERSION, "frame": self.frame,
            "mode": "paper", "side": "long", "research_source_sha256": RESEARCH_SOURCE_SHA256,
            "source_manifest_sha256": self.source_manifest_sha256,
            "excluded_symbols": sorted(EXCLUDED_SYMBOLS), "minimum_source_bars": 234,
            "minimum_close": 5, "minimum_mean20_native_bar_dollar_volume": 1_000_000,
            "minimum_atr14_exclusive": 0, "current_and_lag3_total_votes": 7,
            "minimum_balance_change_3": 2, "minimum_distinct_increasing_channels": 2,
            "increasing_channel_rule": "any signed numeric increase in last three adjacent transitions; null comparison false",
            "glyph_requirement": None, "cooldown_native_bars": 20,
            "cooldown_consumption": "originated opportunity, including capacity/cash denials",
            "entry": "next observed native open", "exit": "actual entry bar index + 20, at open",
            "hold_native_bars": 20, "priority": "descending repair + .01*balance + .001*clip(OBV_slope5/volume,-10,10); symbol ascending",
            "max_positions": 10, "equity_fraction": "0.10", "native_dollar_volume_fraction": "0.01",
            "cash": "settled cash only", "settlement": "next exchange-session open after sell",
            "buy_cost_fraction": "0.001", "sell_cost_fraction": "0.001",
            "share_rule": "floor(min(.1*equity,.01*mean20NativeDollarVolume,settledCash)/(executionPrice*1.001))",
        }

    @property
    def policy_sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def evaluate(self, symbol: str, snapshot: Any, *, as_of_ms: int,
                 next_eligible_bar_index: int | None = None) -> StateRepairDecision:
        """Fail closed on warming, future, malformed, or incompatible data.

        Only caller-owned persisted cooldown is consulted. Generating a
        signal does not reserve funds, imply a fill, or release that cooldown.
        A revised history must retain its original source-origin/index mapping
        in the runtime, or be quarantined before calling this function.
        """
        try:
            _integer(as_of_ms, "decision clock")
            if not isinstance(symbol, str) or not _SYMBOL.fullmatch(symbol):
                return StateRepairDecision(None, "invalid_symbol")
            if symbol in EXCLUDED_SYMBOLS:
                return StateRepairDecision(None, "excluded_symbol")
            if _field(snapshot, "symbol") != symbol or _field(snapshot, "frame") != self.frame:
                return StateRepairDecision(None, "snapshot_identity_mismatch")
            snapshot_as_of = _integer(_field(snapshot, "as_of_ms"), "snapshot clock")
            if snapshot_as_of > as_of_ms:
                return StateRepairDecision(None, "future_snapshot")
            manifest_hash = _hash(_field(snapshot, "source_manifest_sha256"), "source manifest hash")
            if manifest_hash != self.source_manifest_sha256:
                return StateRepairDecision(None, "source_manifest_mismatch")
            input_hash = _hash(_field(snapshot, "input_sha256"), "input hash")
            count = _integer(_field(snapshot, "source_bar_count"), "source count")
            if count < 234:
                return StateRepairDecision(None, "warming")
            raw_points = _field(snapshot, "features")
            if not isinstance(raw_points, Sequence) or isinstance(raw_points, (str, bytes)) or len(raw_points) != 4:
                return StateRepairDecision(None, "missing_four_bar_panel")
            points = tuple(_point(p, symbol, self.frame, snapshot_as_of) for p in raw_points)
            current = points[-1]
            if [p.index for p in points] != list(range(count - 4, count)):
                return StateRepairDecision(None, "noncontiguous_native_indices")
            if len({p.bar_id for p in points}) != 4 or any(a.timestamp_ms >= b.timestamp_ms or a.completed_at_ms >= b.completed_at_ms or a.usable_at_ms > b.usable_at_ms for a, b in zip(points, points[1:])):
                return StateRepairDecision(None, "nonmonotone_native_bars")
            origin = _integer(_field(snapshot, "source_origin_timestamp_ms"), "snapshot source origin")
            if any(p.origin_ms != origin for p in points):
                return StateRepairDecision(None, "source_origin_mismatch")
            if current.status != "ready":
                return StateRepairDecision(None, "warming")
            if current.close < 5 or current.dollar_volume20 < 1_000_000 or current.atr14 <= 0:
                return StateRepairDecision(None, "ineligible_price_liquidity_or_atr")
            if next_eligible_bar_index is not None:
                _integer(next_eligible_bar_index, "cooldown index", minimum=-1)
                if current.index < next_eligible_bar_index:
                    return StateRepairDecision(None, "cooldown")
            repair = current.balance - points[0].balance
            increasing = sum(any(a.votes[k] is not None and b.votes[k] is not None and b.votes[k] > a.votes[k] for a, b in zip(points, points[1:])) for k in range(7))
            if current.total_votes != 7 or points[0].total_votes != 7 or repair < 2 or increasing < 2:
                return StateRepairDecision(None, "no_state_repair")
            ratio = current.obv_slope5 / current.volume if current.volume > 0 else 0.0
            # Research uses ratio fillna(0), then clips infinities to +/-10.
            ratio = min(10.0, max(-10.0, ratio))
            score = repair + .01 * current.balance + .001 * ratio
            policy_hash = self.policy_sha256
            identity = {"policy_sha256": policy_hash, "symbol": symbol,
                        "source_origin_timestamp_ms": origin, "bar_id": current.bar_id,
                        "origin_bar_index": current.index}
            signal_id = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            signal = StateRepairSignal(signal_id, symbol, self.frame, current.index,
                current.bar_id, origin, current.usable_at_ms, current.index + 1,
                current.index + 20, 20, current.balance, repair, increasing, score,
                current.close, current.atr14, current.volume, current.dollar_volume20,
                manifest_hash, input_hash, policy_hash)
            return StateRepairDecision(signal, "state_repair")
        except (KeyError, AttributeError, ValueError, TypeError, ArithmeticError):
            return StateRepairDecision(None, "invalid_feature_panel")

    @staticmethod
    def exit_bar_index(actual_entry_bar_index: int) -> int:
        """Use the observed entry index, including any runtime-documented delay."""
        return _integer(actual_entry_bar_index, "entry index") + 20

    @staticmethod
    def exit_due(actual_entry_bar_index: int, observed_open_bar_index: int) -> bool:
        """Late delivery still services the exit; no synthesized missing bar."""
        return _integer(observed_open_bar_index, "observed open index") >= StateRepairPolicy.exit_bar_index(actual_entry_bar_index)

    def size_entry(self, signal: StateRepairSignal, *, execution_price: Any,
                   equity: Any, settled_cash: Any, open_positions: int,
                   already_held: bool = False) -> EntrySizing:
        """Cap total debit, whole shares, ten slots, and settled cash.

        Equity may include unsettled proceeds but settled_cash must exclude
        them and any existing order reservations. The runtime must perform the
        reservation and submission transaction atomically after this pure
        calculation and recheck inputs when fills arrive.
        """
        if not isinstance(signal, StateRepairSignal) or signal.frame != self.frame or signal.policy_sha256 != self.policy_sha256:
            raise ValueError("signal does not belong to this frozen policy")
        if not isinstance(already_held, bool):
            raise ValueError("already_held must be boolean")
        slots = _integer(open_positions, "open positions")
        with localcontext() as context:
            context.prec = 50
            price = _decimal(execution_price, "execution price", positive=True)
            eq = _decimal(equity, "equity")
            cash = _decimal(settled_cash, "settled cash")
            dv = _decimal(signal.dollar_volume20, "native dollar volume")
            budget = min(Decimal("0.1") * eq, Decimal("0.01") * dv, cash)
            reason = "already_held" if already_held else "positions_full" if slots >= 10 else ""
            shares = 0 if reason else int((budget / (price * (1 + self.SIDE_COST))).to_integral_value(rounding=ROUND_FLOOR))
            if shares < 1 and not reason:
                reason = "insufficient_settled_cash_or_capacity"
            gross = Decimal(shares) * price
            fee = gross * self.SIDE_COST
            debit = gross + fee
            if debit > budget or debit > cash:
                raise ArithmeticError("entry debit exceeds frozen cash/capacity bound")
            return EntrySizing(shares, price, budget, gross, fee, debit, cash - debit, reason or "sized")


def rank_signals(signals: Sequence[StateRepairSignal]) -> tuple[StateRepairSignal, ...]:
    """Rank competing same-frame opportunities; never duplicate a symbol."""
    if any(not isinstance(s, StateRepairSignal) or not math.isfinite(s.score) for s in signals):
        raise ValueError("invalid state-repair signals")
    if len({s.frame for s in signals}) > 1 or len({s.policy_sha256 for s in signals}) > 1:
        raise ValueError("independent policy books cannot share a ranking queue")
    if len({s.symbol for s in signals}) != len(signals):
        raise ValueError("duplicate symbols in opportunity batch")
    return tuple(sorted(signals, key=lambda signal: (-signal.score, signal.symbol)))
