"""Original research implementation informed by Saty's public indicators.

NOT a reproduction of Saty's complete discretionary method. No broker integration.
All setup, risk, fill and portfolio choices are proposed research hypotheses.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from hashlib import sha256
from math import floor, isfinite, sqrt
from collections import deque
from typing import Iterable
import json

VERSION = "0.1.0-research"
MULTIPLIERS = (0.0, .236, .382, .5, .618, .786, 1., 1.236, 1.382, 1.5,
               1.618, 1.786, 2., 2.236, 2.618, 3.)


def aware(t: datetime) -> None:
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("timezone-aware timestamps required")


def finite(*values: float) -> None:
    if not all(isfinite(v) for v in values):
        raise ValueError("nonfinite numeric input")


@dataclass(frozen=True)
class Bar:
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def validate(self) -> None:
        aware(self.start); aware(self.end)
        finite(self.open, self.high, self.low, self.close, self.volume)
        if self.end <= self.start or self.low <= 0 or self.volume < 0:
            raise ValueError("invalid interval/price/volume")
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("inconsistent OHLC")


@dataclass(frozen=True)
class Session:
    """Supply from an exchange calendar; no weekday/holiday guessing in the engine."""
    session_id: str
    open: datetime
    entry_start: datetime
    entry_cutoff: datetime
    flat_at: datetime
    close: datetime

    def validate(self) -> None:
        times = (self.open, self.entry_start, self.entry_cutoff, self.flat_at, self.close)
        for t in times: aware(t)
        if not self.open <= self.entry_start < self.entry_cutoff <= self.flat_at <= self.close:
            raise ValueError("invalid session boundaries")


@dataclass(frozen=True)
class DailyReference:
    session_id: str
    period_end: datetime
    available_at: datetime
    previous_close: float
    previous_atr14: float
    provenance: str = "external completed-period feed"

    def validate(self, bar: Bar, session: Session) -> None:
        aware(self.period_end); aware(self.available_at)
        finite(self.previous_close, self.previous_atr14)
        if self.session_id != session.session_id:
            raise ValueError("daily reference belongs to a different session")
        if not self.period_end <= self.available_at <= session.open <= bar.start:
            raise ValueError("daily reference must be known before session opens")
        if self.previous_close <= 0 or self.previous_atr14 <= 0:
            raise ValueError("invalid daily anchor/ATR")

    def levels(self) -> tuple[float, ...]:
        return tuple(sorted({self.previous_close + d * m * self.previous_atr14
                             for d in (-1, 1) for m in MULTIPLIERS
                             if self.previous_close + d * m * self.previous_atr14 > 0}))


@dataclass(frozen=True)
class HigherTimeframe:
    period_end: datetime
    available_at: datetime
    direction: int  # -1 bearish, 0 neutral, +1 bullish
    max_age: timedelta = timedelta(hours=2)

    def validate(self, at: datetime) -> None:
        aware(self.period_end); aware(self.available_at)
        if self.direction not in (-1, 0, 1):
            raise ValueError("invalid higher-timeframe direction")
        if self.max_age <= timedelta(0) or not self.period_end <= self.available_at <= at:
            raise ValueError("future or invalid higher-timeframe snapshot")
        if at - self.period_end > self.max_age:
            raise ValueError("stale higher-timeframe snapshot")


@dataclass(frozen=True)
class Config:
    symbol: str = "SPY"
    ribbon_version: str = "pro"  # pro:8/13/21/48/200; legacy:8/21/34
    setup: str = "compression_break_retest"  # also pullback, break_retest
    atr_period: int = 14
    warmup_bars: int = 1000
    risk_fraction: float = .0025
    max_daily_loss_r: float = 2.
    max_entries: int = 3
    min_reward_risk: float = 1.5
    max_notional_fraction: float = 1.
    pivot_tolerance_atr: float = .10
    stop_buffer_atr: float = .10
    max_chase_atr: float = .40
    max_entry_gap_atr: float = .15
    setup_expiry_bars: int = 3
    cooldown_bars: int = 3
    minimum_compression_bars: int = 3
    maximum_box_bars: int = 30
    point_value: float = 1.
    commission_per_unit_side: float = .005
    slippage_per_unit_side: float = .01

    def __post_init__(self) -> None:
        if self.ribbon_version not in ("pro", "legacy"):
            raise ValueError("unknown ribbon version")
        if self.setup not in ("pullback", "break_retest", "compression_break_retest"):
            raise ValueError("unsupported setup; Vomy/Golden Gate trade rules are specification-only")
        if self.atr_period != 14:
            raise ValueError("verified indicator reconstruction requires ATR14")
        if not self.symbol or self.warmup_bars < self.atr_period:
            raise ValueError("invalid symbol/warmup")
        vals = (self.risk_fraction, self.max_daily_loss_r, self.min_reward_risk,
                self.max_notional_fraction, self.pivot_tolerance_atr, self.stop_buffer_atr,
                self.max_chase_atr, self.max_entry_gap_atr, self.point_value,
                self.commission_per_unit_side, self.slippage_per_unit_side)
        finite(*vals)
        if min(vals) < 0 or not 0 < self.risk_fraction <= .01:
            raise ValueError("invalid risk configuration")
        if self.point_value <= 0 or self.max_notional_fraction <= 0 or self.min_reward_risk <= 0:
            raise ValueError("invalid valuation configuration")
        if self.minimum_compression_bars < 1 or self.maximum_box_bars < self.minimum_compression_bars:
            raise ValueError("invalid compression box lengths")
        if self.max_daily_loss_r <= 0 or min(self.max_entries, self.setup_expiry_bars) < 1 or self.cooldown_bars < 0:
            raise ValueError("invalid risk/expiry limits")

    @property
    def periods(self) -> tuple[int, ...]:
        return (8, 13, 21, 48, 200) if self.ribbon_version == "pro" else (8, 21, 34)

    @property
    def slow(self) -> int:
        return 48 if self.ribbon_version == "pro" else 34

    @property
    def fingerprint(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Features:
    ema: dict[int, float]
    atr: float | None
    buying_proxy: float
    selling_proxy: float
    volume_proxy_valid: bool
    phase: float | None
    compression: bool | None


class Indicators:
    """Causal EMA(first-close seed), ATR(SMA seed then Wilder), OHLCV volume proxy."""
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.ema: dict[int, float] = {}
        self.previous_close: float | None = None
        self.tr_seed: list[float] = []
        self.atr: float | None = None
        self.count = 0
        self.closes: deque[float] = deque(maxlen=21)
        self.phase: float | None = None
        self.previous_bb_kc_delta: float | None = None

    def update(self, b: Bar) -> Features:
        for n in self.cfg.periods:
            old = self.ema.get(n, b.close)
            self.ema[n] = old + 2. / (n + 1.) * (b.close - old)
        tr = b.high - b.low if self.previous_close is None else max(
            b.high - b.low, abs(b.high - self.previous_close), abs(b.low - self.previous_close))
        if self.atr is None:
            self.tr_seed.append(tr)
            if len(self.tr_seed) == self.cfg.atr_period:
                self.atr = sum(self.tr_seed) / self.cfg.atr_period
        else:
            self.atr = ((self.cfg.atr_period - 1) * self.atr + tr) / self.cfg.atr_period
        valid = b.high > b.low and b.volume > 0
        buy = b.volume * (b.close - b.low) / (b.high - b.low) if valid else b.volume / 2.
        sell = b.volume - buy
        self.closes.append(b.close)
        compression = None
        if self.atr is not None and self.atr > 0:
            raw_phase = 100. * (b.close - self.ema[21]) / (3. * self.atr)
            self.phase = raw_phase if self.phase is None else .5 * raw_phase + .5 * self.phase
            if len(self.closes) == 21:
                mean = sum(self.closes) / 21.
                std = sqrt(sum((x - mean) ** 2 for x in self.closes) / 21.)
                delta = 2. * std - 2. * self.atr
                outer = 2. * std - 1.854 * self.atr
                expansion = self.previous_bb_kc_delta is not None and self.previous_bb_kc_delta <= delta
                compression = delta <= 0 and not (expansion and outer > 0)
                self.previous_bb_kc_delta = delta
        self.previous_close = b.close
        self.count += 1
        return Features(dict(self.ema), self.atr, buy, sell, valid, self.phase, compression)


class State(str, Enum):
    IDLE = "IDLE"
    ARMED = "ARMED"
    PENDING = "PENDING_NEXT_OPEN"
    OPEN = "OPEN"
    COOLDOWN = "COOLDOWN"
    HALTED = "HALTED"


@dataclass
class Arm:
    direction: int
    index: int
    high: float
    low: float
    level: float | None = None


@dataclass
class Intent:
    signal_id: str
    at: datetime
    direction: int
    stop: float
    target: float
    reference_entry: float
    atr: float
    pivot: float
    decision_available_at: datetime


@dataclass
class Position:
    signal_id: str
    direction: int
    entry: float
    stop: float
    target: float
    quantity: int
    initial_risk_cash: float
    opened_at: datetime


class ResearchEngine:
    """Single-underlying, single-position, simulated shares/contracts only.

    step consumes one completed execution bar. Candidate at close can fill only at
    the next contiguous bar's open. Stop wins ambiguous same-bar stop+target touches.
    Fill simulation is intentionally pessimistic and is not broker execution logic.
    """
    def __init__(self, cfg: Config, initial_equity: float = 100_000.):
        finite(initial_equity)
        if initial_equity <= 0: raise ValueError("positive equity required")
        self.cfg, self.equity = cfg, initial_equity
        self.ind = Indicators(cfg)
        self.state = State.IDLE
        self.arm: Arm | None = None
        self.intent: Intent | None = None
        self.position: Position | None = None
        self.last_bar: Bar | None = None
        self.session_id: str | None = None
        self.session_equity = initial_equity
        self.daily_risk_budget = initial_equity * cfg.risk_fraction
        self.daily_pnl = 0.
        self.entries = 0
        self.cooldown_until = 0
        self.events: list[dict] = []
        self.seen_ids: set[str] = set()
        self.compressed_bars: deque[Bar] = deque(maxlen=cfg.maximum_box_bars)
        self.released_box: tuple[float, float, int] | None = None

    def event(self, kind: str, at: datetime, **fields) -> None:
        self.events.append({"kind": kind, "at": at.isoformat(), "version": VERSION,
                            "config": self.cfg.fingerprint, **fields})

    def _reset_arm(self) -> None:
        self.arm = None
        self.state = State.IDLE

    def _regime(self, f: Features, b: Bar, htf: HigherTimeframe) -> int:
        e = f.ema
        if b.close >= e[8] >= e[21] >= e[self.cfg.slow] and htf.direction == 1: return 1
        if b.close <= e[8] <= e[21] <= e[self.cfg.slow] and htf.direction == -1: return -1
        return 0

    def _can_enter(self, at: datetime, s: Session) -> bool:
        return s.entry_start <= at < s.entry_cutoff and self.entries < self.cfg.max_entries and \
            self.daily_pnl > -self.cfg.max_daily_loss_r * self.daily_risk_budget and self.equity > 0

    def _nearest_target(self, entry: float, direction: int, levels: Iterable[float]) -> float | None:
        ahead = [p for p in levels if direction * (p - entry) > 1e-10]
        return min(ahead, key=lambda p: abs(p - entry)) if ahead else None

    def _make_intent(self, b: Bar, f: Features, direction: int, stop: float, daily: DailyReference, decision_available_at: datetime) -> None:
        assert f.atr is not None
        aware(decision_available_at)
        if decision_available_at < b.end:
            raise ValueError("decision cannot be available before signal bar closes")
        target = self._nearest_target(b.close, direction, daily.levels())
        risk = direction * (b.close - stop)
        if risk <= 0 or target is None:
            self.event("REJECT", b.end, reason="invalid_stop_or_no_target"); self._reset_arm(); return
        estimated_fill = b.close + direction * self.cfg.slippage_per_unit_side
        net_risk = (direction * (estimated_fill - stop) + self.cfg.slippage_per_unit_side) * self.cfg.point_value + 2 * self.cfg.commission_per_unit_side
        net_reward = (direction * (target - estimated_fill) - self.cfg.slippage_per_unit_side) * self.cfg.point_value - 2 * self.cfg.commission_per_unit_side
        if net_reward < self.cfg.min_reward_risk * net_risk:
            self.event("REJECT", b.end, reason="nearest_level_blocks_reward"); self._reset_arm(); return
        entry_anchor = self.arm.level if self.arm is not None and self.arm.level is not None else f.ema[21]
        if direction * (b.close - entry_anchor) > self.cfg.max_chase_atr * f.atr:
            self.event("REJECT", b.end, reason="chase_distance"); self._reset_arm(); return
        key = f"{VERSION}|{self.cfg.fingerprint}|{self.cfg.symbol}|{self.session_id}|{b.end.isoformat()}|{direction}"
        sid = sha256(key.encode()).hexdigest()[:24]
        if sid in self.seen_ids: return
        self.seen_ids.add(sid)
        self.intent = Intent(sid, b.end, direction, stop, target, b.close, f.atr, entry_anchor, decision_available_at)
        self.state, self.arm = State.PENDING, None
        self.event("INTENT", decision_available_at, signal_id=sid, direction=direction, stop=stop, target=target,
                   reference_entry=b.close, setup=self.cfg.setup, signal_bar_end=b.end.isoformat(),
                   decision_available_at=decision_available_at.isoformat())

    def _fill(self, b: Bar, session: Session, htf: HigherTimeframe) -> None:
        i = self.intent
        assert i is not None
        self.intent = None
        d = i.direction
        fill = b.open + d * self.cfg.slippage_per_unit_side
        reason = None
        # A completed HTF bar learned after the execution open cannot authorize that fill.
        if i.decision_available_at > b.start:
            reason = "signal_unavailable_at_entry_open"
        elif htf.available_at > b.start or htf.period_end > b.start:
            reason = "htf_unavailable_at_entry_open"
        elif htf.direction != d or b.start - htf.period_end > htf.max_age:
            reason = "htf_changed_or_stale_at_open"
        elif b.start != i.at or not self._can_enter(b.start, session):
            reason = "noncontiguous_or_outside_entry_window"
        elif d * (fill - i.reference_entry) > self.cfg.max_entry_gap_atr * i.atr:
            reason = "entry_gap_chase"
        elif d * (fill - i.pivot) > self.cfg.max_chase_atr * i.atr:
            reason = "open_chase_distance"
        risk_points = d * (fill - i.stop)
        reward = d * (i.target - fill)
        net_unit_risk = (risk_points + self.cfg.slippage_per_unit_side) * self.cfg.point_value + 2 * self.cfg.commission_per_unit_side
        net_unit_reward = (reward - self.cfg.slippage_per_unit_side) * self.cfg.point_value - 2 * self.cfg.commission_per_unit_side
        if risk_points <= 0 or net_unit_reward <= 0 or net_unit_reward < self.cfg.min_reward_risk * net_unit_risk:
            reason = reason or "gap_invalidates_stop_or_reward"
        if reason:
            self.event("CANCEL", b.start, signal_id=i.signal_id, reason=reason); self.state = State.IDLE; return
        # Fees and one adverse exit-slippage allowance included in risk sizing.
        unit_risk = risk_points * self.cfg.point_value + 2 * self.cfg.commission_per_unit_side + \
            self.cfg.slippage_per_unit_side * self.cfg.point_value
        remaining = self.cfg.max_daily_loss_r * self.daily_risk_budget + self.daily_pnl
        budget = min(self.equity * self.cfg.risk_fraction, remaining)
        quantity = min(floor(budget / unit_risk),
                       floor(self.equity * self.cfg.max_notional_fraction / (fill * self.cfg.point_value)))
        if quantity <= 0:
            self.event("CANCEL", b.start, signal_id=i.signal_id, reason="risk_budget_below_one_unit")
            self.state = State.IDLE; return
        self.position = Position(i.signal_id, d, fill, i.stop, i.target, quantity,
                                 quantity * unit_risk, b.start)
        self.entries += 1
        self.state = State.OPEN
        self.event("SIMULATED_FILL", b.start, signal_id=i.signal_id, direction=d, price=fill,
                   quantity=quantity, risk_cash=quantity * unit_risk)

    def _exit(self, price: float, at: datetime, reason: str, price_already_slipped: bool = False) -> None:
        p = self.position
        assert p is not None
        fill = price if price_already_slipped else price - p.direction * self.cfg.slippage_per_unit_side
        pnl = p.quantity * (p.direction * (fill - p.entry) * self.cfg.point_value -
                            2 * self.cfg.commission_per_unit_side)
        self.equity += pnl; self.daily_pnl += pnl
        self.event("SIMULATED_EXIT", at, signal_id=p.signal_id, price=fill, quantity=p.quantity,
                   pnl=pnl, r=pnl / p.initial_risk_cash, reason=reason)
        self.position = None
        self.cooldown_until = self.ind.count + self.cfg.cooldown_bars
        self.state = State.COOLDOWN
        if self.daily_pnl <= -self.cfg.max_daily_loss_r * self.daily_risk_budget or self.equity <= 0:
            self.state = State.HALTED
            self.event("HALT", at, reason="daily_loss_limit")

    def _manage_position(self, b: Bar, s: Session) -> None:
        p = self.position
        assert p is not None
        d = p.direction
        stop_touch = b.low <= p.stop if d == 1 else b.high >= p.stop
        target_touch = b.high >= p.target if d == 1 else b.low <= p.target
        # Scheduled liquidation takes precedence at a known execution-bar open.
        if b.start >= s.flat_at:
            self._exit(b.open, b.start, "scheduled_flat"); return
        if stop_touch:
            price = min(b.open, p.stop) if d == 1 else max(b.open, p.stop)
            self._exit(price, b.end, "stop_or_ambiguous_stop_first"); return
        if target_touch:
            self._exit(p.target, b.end, "target"); return
        # The caller must align flat_at with a bar boundary. No fictitious intrabar close.
        if b.end == s.flat_at:
            self._exit(b.close, b.end, "scheduled_flat_close")

    def step(self, b: Bar, as_of: datetime, session: Session,
             daily: DailyReference, htf: HigherTimeframe) -> list[dict]:
        """Reject malformed/future execution bars. Context errors gate new entries; valid-bar exits continue."""
        start_event = len(self.events)
        b.validate(); aware(as_of); session.validate()
        if b.end > as_of: raise ValueError("unclosed bar supplied")
        if not session.open <= b.start < b.end <= session.close:
            raise ValueError("execution bar outside session")
        if b.start < session.flat_at < b.end:
            raise ValueError("flat deadline must align with execution bar boundary")
        if self.last_bar and b.start < self.last_bar.end:
            raise ValueError("duplicate, overlap, or out-of-order bar")
        context_error = None
        try:
            daily.validate(b, session)
            htf.validate(b.end)
        except ValueError as err:
            # Valid execution bars continue to protect an existing position even
            # when the entry-only higher-timeframe context is unavailable/stale.
            if self.position is None:
                raise
            context_error = str(err)
        new_session = session.session_id != self.session_id
        if new_session:
            if self.position:
                raise ValueError("position remained open across session; reconciliation required")
            self.session_id = session.session_id
            self.session_equity = self.equity
            self.daily_risk_budget = self.equity * self.cfg.risk_fraction
            self.daily_pnl, self.entries = 0., 0
            self.state, self.arm, self.intent = State.IDLE, None, None
            self.compressed_bars.clear(); self.released_box = None
            self.event("SESSION", b.start, session_id=self.session_id)
        elif self.last_bar and b.start != self.last_bar.end:
            if self.position:
                raise ValueError("data gap with open position; reconciliation required")
            self.event("DATA_GAP", b.start)
            self.state, self.arm, self.intent = State.IDLE, None, None
            self.compressed_bars.clear(); self.released_box = None
        # Pending decision knows only previous-close information plus opening quote and
        # an HTF context already available at the open. Current-bar close is not used.
        had_position = self.position is not None
        if self.intent and context_error is None: self._fill(b, session, htf)
        if self.position: self._manage_position(b, session)
        f = self.ind.update(b)
        if f.compression:
            self.compressed_bars.append(b)
            self.released_box = None
        elif self.compressed_bars:
            if len(self.compressed_bars) >= self.cfg.minimum_compression_bars:
                self.released_box = (min(x.low for x in self.compressed_bars),
                                     max(x.high for x in self.compressed_bars), self.ind.count)
            self.compressed_bars.clear()
        if self.released_box and self.ind.count - self.released_box[2] > self.cfg.setup_expiry_bars:
            self.released_box = None
        old_bar = self.last_bar
        self.last_bar = b
        if context_error is not None:
            self.arm, self.intent = None, None
            self.event("CONTEXT_BLOCK", b.end, reason=context_error)
            return self.events[start_event:]
        if self.state == State.COOLDOWN and self.ind.count >= self.cooldown_until:
            self.state = State.IDLE
        if self.position or self.state in (State.COOLDOWN, State.HALTED): return self.events[start_event:]
        # No same-bar re-entry after a position exit or canceled opening fill.
        if had_position or any(e["kind"] in ("SIMULATED_FILL", "CANCEL") for e in self.events[start_event:]):
            return self.events[start_event:]
        if self.ind.count < self.cfg.warmup_bars or f.atr is None or f.atr <= 0 or not self._can_enter(b.end, session):
            self.arm = None
            if self.state != State.HALTED: self.state = State.IDLE
            return self.events[start_event:]
        direction = self._regime(f, b, htf)
        if self.arm:
            a = self.arm; d = a.direction
            if self.ind.count - a.index > self.cfg.setup_expiry_bars or htf.direction != d:
                self.event("DISARM", b.end, reason="expired_or_htf_flip"); self._reset_arm()
            elif d * (b.close - (a.low if d == 1 else a.high)) < 0:
                self.event("DISARM", b.end, reason="setup_extreme_lost"); self._reset_arm()
            elif self.cfg.setup == "pullback":
                trigger = a.high if d == 1 else a.low
                if direction == d and d * (b.close - trigger) > 0:
                    stop = (a.low if d == 1 else a.high) - d * self.cfg.stop_buffer_atr * f.atr
                    self._make_intent(b, f, d, stop, daily, as_of)
            else:
                assert a.level is not None
                tol = self.cfg.pivot_tolerance_atr * f.atr
                touched = b.low <= a.level + tol if d == 1 else b.high >= a.level - tol
                held = d * (b.close - a.level) > 0
                if d * (b.close - a.level) < -tol:
                    self.event("DISARM", b.end, reason="broken_level_lost"); self._reset_arm()
                elif touched and held and direction == d:
                    stop = (min(a.level, b.low) if d == 1 else max(a.level, b.high)) - d * self.cfg.stop_buffer_atr * f.atr
                    self._make_intent(b, f, d, stop, daily, as_of)
            return self.events[start_event:]
        # EMA stack alignment may persist during a pivot pullback even while close<EMA8.
        e = f.ema
        trend = 1 if e[8] > e[21] > e[self.cfg.slow] and htf.direction == 1 else \
            -1 if e[8] < e[21] < e[self.cfg.slow] and htf.direction == -1 else 0
        if self.cfg.setup == "pullback" and trend:
            tol = self.cfg.pivot_tolerance_atr * f.atr
            touched = b.low <= e[21] + tol and b.high >= e[21] - tol
            defended = trend * (b.close - e[self.cfg.slow]) > 0
            if touched and defended:
                self.arm = Arm(trend, self.ind.count, b.high, b.low)
                self.state = State.ARMED
                self.event("ARM", b.end, direction=trend, setup=self.cfg.setup)
        elif self.cfg.setup == "compression_break_retest" and direction and self.released_box:
            lo, hi, _ = self.released_box
            level = hi if direction == 1 else lo
            # Phase sign is a documented indicator fact; using it as a mandatory
            # breakout filter is OUR proposed rule, not an attributed Saty threshold.
            if direction * (b.close - level) > 0 and f.phase is not None and direction * f.phase > 0:
                self.arm = Arm(direction, self.ind.count, b.high, b.low, level)
                self.state = State.ARMED
                self.released_box = None
                self.event("ARM", b.end, direction=direction, level=level, setup=self.cfg.setup,
                           box_low=lo, box_high=hi, phase=f.phase)
        elif self.cfg.setup == "break_retest" and direction and old_bar:
            crossed = [p for p in daily.levels()
                       if direction * (old_bar.close - p) <= 0 < direction * (b.close - p)]
            if crossed:
                level = max(crossed) if direction == 1 else min(crossed)
                self.arm = Arm(direction, self.ind.count, b.high, b.low, level)
                self.state = State.ARMED
                self.event("ARM", b.end, direction=direction, level=level, setup=self.cfg.setup)
        return self.events[start_event:]
