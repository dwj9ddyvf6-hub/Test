"""Causal five-minute price-momentum core; standard library, no execution code.

F and S advance on accepted RTH bars, including declared adjacent sessions.
lookback bounds retained bars; the first complete slope vector is bar 26.
"""
from collections import deque
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from hashlib import sha256
import json
import math

VERSION = "raschke-core-1"


def _dt(value, name):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{name}: invalid ISO datetime") from exc
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name}: timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _number(value, name, minimum=None, strictly_positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: finite number required")
    try:
        value = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name}: finite number required") from exc
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f"{name}: invalid numeric value")
    if strictly_positive and value <= 0:
        raise ValueError(f"{name}: positive value required")
    return value


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name}: integer >= {minimum} required")
    return value


def _identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: nonempty string required")
    return value


@dataclass(frozen=True)
class Bar:
    symbol: str
    start: datetime
    end: datetime
    available_at: datetime
    session_id: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        _identifier(self.symbol, "symbol")
        _identifier(self.session_id, "session_id")
        for key in ("start", "end", "available_at"):
            object.__setattr__(self, key, _dt(getattr(self, key), key))
        if not self.start < self.end <= self.available_at:
            raise ValueError("bar must end after start and be available no earlier than end")
        for key in ("open", "high", "low", "close"):
            object.__setattr__(self, key, _number(getattr(self, key), key, strictly_positive=True))
        object.__setattr__(self, "volume", _number(self.volume, "volume", minimum=0))
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("inconsistent OHLC")


@dataclass(frozen=True)
class Session:
    id: str
    open: datetime
    close: datetime
    previous_id: str | None = None

    def __post_init__(self):
        _identifier(self.id, "session id")
        object.__setattr__(self, "open", _dt(self.open, "session open"))
        object.__setattr__(self, "close", _dt(self.close, "session close"))
        if self.open >= self.close:
            raise ValueError("session open must precede close")
        if self.previous_id is not None:
            _identifier(self.previous_id, "previous_id")
            if self.previous_id == self.id:
                raise ValueError("session cannot precede itself")


@dataclass(frozen=True)
class Features:
    symbol: str
    bar_end: datetime
    available_at: datetime
    close: float
    atr14: float
    ema20: float
    m2: float
    fast: float
    slow: float
    dm2: float
    dfast: float
    dslow: float
    pf3: int
    vwap: float | None
    fast_slope_signs: tuple[int, ...]
    bar_count: int
    session_bar_count: int
    generation: int


def _record(value):
    return {f.name: (getattr(value, f.name).isoformat()
                     if isinstance(getattr(value, f.name), datetime)
                     else getattr(value, f.name)) for f in fields(value)}


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


class Core:
    def __init__(self, lookback=64, interval_seconds=300, tick_epsilon=1e-9):
        self.lookback = _integer(lookback, "lookback", 64)
        self.interval_seconds = _integer(interval_seconds, "interval_seconds", 1)
        self.tick_epsilon = _number(tick_epsilon, "tick_epsilon", minimum=0)
        self.symbol = None
        self.current_session = None
        self._sessions = {}
        self.last_now = None
        self.reset_count = 0
        self.reasons = deque(maxlen=32)
        self._clear_formula()
        self.session_bar_count = 0
        self._vwap_volume = 0.0
        self._vwap_notional = 0.0
        self._vwap_complete = True

    @property
    def config(self):
        return {"lookback": self.lookback, "interval_seconds": self.interval_seconds,
                "tick_epsilon": self.tick_epsilon}

    @property
    def config_fingerprint(self):
        return _hash({"version": VERSION, **self.config})

    def _clear_formula(self):
        self._bars = deque(maxlen=self.lookback)
        self._fast_history = deque(maxlen=16)
        self._fast_signs = deque(maxlen=6)
        self._tr_seed = []
        self._ema_seed = []
        self._atr = self._ema = None
        self._last_m2 = self._last_fast = self._last_slow = None
        self.bar_count = 0

    def _reason(self, code, bar):
        self.reasons.append({"code": code, "bar_end": bar.end.isoformat(),
                             "generation": self.reset_count})

    def _sign(self, value):
        return 1 if value > self.tick_epsilon else -1 if value < -self.tick_epsilon else 0

    def update(self, bar, session, now):
        """Accept one finalized grid-aligned bar, atomically rejecting bad inputs.

        An exact retained duplicate returns None without changing state. Valid gaps
        reset formula history; incomplete current-session VWAP stays unknown.
        """
        if not isinstance(bar, Bar) or not isinstance(session, Session):
            raise ValueError("Bar and Session instances required")
        now = _dt(now, "now")
        if self.last_now is not None and now < self.last_now:
            raise ValueError("now moved backwards")
        if bar.available_at > now:
            raise ValueError("bar is not available yet")
        if bar.symbol != self.symbol and self.symbol is not None:
            raise ValueError("Core is bound to one symbol")
        if bar.session_id != session.id:
            raise ValueError("bar/session identity mismatch")
        if (bar.end - bar.start).total_seconds() != self.interval_seconds:
            raise ValueError("wrong bar duration")
        if (session.close - session.open).total_seconds() % self.interval_seconds:
            raise ValueError("session duration is not an integer number of intervals")
        if not session.open <= bar.start < bar.end <= session.close:
            raise ValueError("bar outside session")
        if (bar.start - session.open).total_seconds() % self.interval_seconds:
            raise ValueError("bar not aligned to session grid")
        if session.id in self._sessions and session != self._sessions[session.id]:
            raise ValueError("conflicting session revision")
        for existing in self._bars:
            if existing.start == bar.start or existing.end == bar.end:
                if existing == bar:
                    # Only permit a duplicate under the same calendar metadata.
                    if session.id == self.current_session.id and session != self.current_session:
                        raise ValueError("conflicting duplicate calendar")
                    return None
                raise ValueError("conflicting bar revision")
        last = self._bars[-1] if self._bars else None
        if last and bar.start < last.end:
            raise ValueError("out-of-order or overlapping bar")
        new_session = self.current_session is None or session.id != self.current_session.id
        if new_session:
            if bar.start != session.open:
                raise ValueError("first observed bar of a session must open at session open")
            if self.current_session and session.open < self.current_session.close:
                raise ValueError("nonmonotonic/overlapping session")

        reset_reason = None
        if last:
            if new_session and session.previous_id != self.current_session.id:
                reset_reason = "UNKNOWN_SESSION_CHAIN_RESET"
            elif new_session and last.end != self.current_session.close:
                reset_reason = "MISSING_SESSION_TAIL_RESET"
            elif not new_session and bar.start != last.end:
                reset_reason = "INTRADAY_GAP_RESET"

        # Compute on an independent bounded state copy: numeric overflow and any
        # later validation error must not leave half-updated recursive state.
        candidate = self._clone()
        if reset_reason:
            candidate._clear_formula()
            candidate.reset_count += 1
            candidate._reason(reset_reason, bar)
            if not new_session:
                candidate._vwap_complete = False
        if new_session:
            candidate.current_session = session
            candidate.session_bar_count = 0
            candidate._vwap_volume = candidate._vwap_notional = 0.0
            candidate._vwap_complete = True
        try:
            result = candidate._accept(bar, now)
        except OverflowError as exc:
            raise ValueError("indicator calculation overflow") from exc
        self.__dict__.update(candidate.__dict__)
        return result

    def _clone(self):
        """Transactional container copy; immutable observations are safely shared.

        Keep the accepted-state arithmetic and snapshot contract unchanged. Every
        mutable container owned by Core is copied; Bar, Session, datetime and
        numeric/string members are immutable. Reset-reason records have the fixed
        flat scalar schema validated by _restore_state.
        """
        candidate = object.__new__(type(self))
        candidate.__dict__ = self.__dict__.copy()
        candidate._bars = deque(self._bars, maxlen=self._bars.maxlen)
        candidate._fast_history = deque(self._fast_history, maxlen=self._fast_history.maxlen)
        candidate._fast_signs = deque(self._fast_signs, maxlen=self._fast_signs.maxlen)
        candidate._tr_seed = self._tr_seed.copy()
        candidate._ema_seed = self._ema_seed.copy()
        candidate._sessions = self._sessions.copy()
        candidate.reasons = deque((record.copy() for record in self.reasons),
                                  maxlen=self.reasons.maxlen)
        return candidate

    def _accept(self, bar, now):
        previous_close = self._bars[-1].close if self._bars else None
        tr = bar.high - bar.low if previous_close is None else max(
            bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close))
        self._bars.append(bar)
        self._sessions[self.current_session.id] = self.current_session
        used_sessions = {x.session_id for x in self._bars}
        self._sessions = {key:value for key,value in self._sessions.items() if key in used_sessions}
        self.bar_count += 1
        self.session_bar_count += 1
        self.symbol = bar.symbol
        self.last_now = now
        if self._atr is None:
            self._tr_seed.append(tr)
            if len(self._tr_seed) == 14:
                self._atr = math.fsum(self._tr_seed) / 14
                self._tr_seed.clear()
        else:
            self._atr += (tr - self._atr) / 14
        if self._ema is None:
            self._ema_seed.append(bar.close)
            if len(self._ema_seed) == 20:
                self._ema = math.fsum(self._ema_seed) / 20
                self._ema_seed.clear()
        else:
            self._ema += (bar.close - self._ema) * (2 / 21)
        typical = math.fsum((bar.high / 3, bar.low / 3, bar.close / 3))
        self._vwap_volume += bar.volume
        self._vwap_notional += typical * bar.volume
        if not math.isfinite(self._vwap_volume) or not math.isfinite(self._vwap_notional):
            raise ValueError("VWAP accumulation overflow")
        closes = [x.close for x in self._bars]
        m2 = closes[-1] - closes[-3] if len(closes) >= 3 else None
        fast = (math.fsum(closes[-3:]) / 3 - math.fsum(closes[-10:]) / 10
                if len(closes) >= 10 else None)
        if fast is not None:
            self._fast_history.append(fast)
        slow = math.fsum(self._fast_history) / 16 if len(self._fast_history) == 16 else None
        dm2 = m2 - self._last_m2 if m2 is not None and self._last_m2 is not None else None
        dfast = fast - self._last_fast if fast is not None and self._last_fast is not None else None
        dslow = slow - self._last_slow if slow is not None and self._last_slow is not None else None
        if dfast is not None:
            self._fast_signs.append(self._sign(dfast))
        self._last_m2, self._last_fast, self._last_slow = m2, fast, slow
        for value in (self._atr, self._ema, m2, fast, slow, dm2, dfast, dslow):
            if value is not None and not math.isfinite(value):
                raise ValueError("indicator calculation overflow")
        if dslow is None:
            return None
        signs = (self._sign(dm2), self._sign(dfast), self._sign(dslow))
        pf3 = signs[0] if signs[0] != 0 and signs.count(signs[0]) == 3 else 0
        vwap = self._vwap_notional / self._vwap_volume if self._vwap_complete and self._vwap_volume > 0 else None
        return Features(bar.symbol, bar.end, bar.available_at, bar.close,
                        self._atr, self._ema, m2, fast, slow, dm2, dfast, dslow,
                        pf3, vwap, tuple(self._fast_signs), self.bar_count,
                        self.session_bar_count, self.reset_count)

    def snapshot(self):
        state = {
            "symbol": self.symbol, "current_session": _record(self.current_session) if self.current_session else None,
            "sessions": [_record(s) for s in sorted(self._sessions.values(), key=lambda x:x.open)],
            "last_now": self.last_now.isoformat() if self.last_now else None,
            "reset_count": self.reset_count, "reasons": list(self.reasons),
            "bars": [_record(x) for x in self._bars], "bar_count": self.bar_count,
            "session_bar_count": self.session_bar_count,
            "fast_history": list(self._fast_history), "fast_signs": list(self._fast_signs),
            "tr_seed": list(self._tr_seed), "ema_seed": list(self._ema_seed),
            "atr": self._atr, "ema": self._ema,
            "last_m2": self._last_m2, "last_fast": self._last_fast, "last_slow": self._last_slow,
            "vwap_volume": self._vwap_volume, "vwap_notional": self._vwap_notional,
            "vwap_complete": self._vwap_complete,
        }
        return {"version": VERSION, "config": self.config,
                "config_fingerprint": self.config_fingerprint,
                "state": state, "state_sha256": _hash(state)}

    @classmethod
    def from_snapshot(cls, value):
        if not isinstance(value, dict) or set(value) != {"version", "config", "config_fingerprint", "state", "state_sha256"}:
            raise ValueError("invalid snapshot envelope")
        if value["version"] != VERSION or not isinstance(value["config"], dict) or set(value["config"]) != {"lookback", "interval_seconds", "tick_epsilon"}:
            raise ValueError("snapshot version/config mismatch")
        obj = cls(**value["config"])
        if value["config_fingerprint"] != obj.config_fingerprint:
            raise ValueError("snapshot config fingerprint mismatch")
        s = value["state"]
        if not isinstance(s, dict) or set(s) != set(obj.snapshot()["state"]):
            raise ValueError("invalid snapshot state fields")
        try:
            if _hash(s) != value["state_sha256"]:
                raise ValueError("snapshot state hash mismatch")
            obj._restore_state(s)
        except (TypeError, KeyError, OverflowError) as exc:
            raise ValueError("invalid snapshot state") from exc
        return obj

    def load_snapshot(self, value):
        candidate = self.from_snapshot(value)
        if candidate.config_fingerprint != self.config_fingerprint:
            raise ValueError("cannot load different configuration")
        self.__dict__.update(candidate.__dict__)

    def _restore_state(self, s):
        count = _integer(s["bar_count"], "bar_count")
        reset = _integer(s["reset_count"], "reset_count")
        session_count = _integer(s["session_bar_count"], "session_bar_count")
        if not isinstance(s["bars"], list) or len(s["bars"]) != min(count, self.lookback):
            raise ValueError("snapshot bar count mismatch")
        bars = [Bar(**x) for x in s["bars"]]
        if not isinstance(s["sessions"],list) or len(s["sessions"]) > self.lookback:
            raise ValueError("invalid retained sessions")
        sessions = [Session(**x) for x in s["sessions"]]
        registry = {x.id:x for x in sessions}
        if len(registry) != len(sessions) or set(registry) != {b.session_id for b in bars}:
            raise ValueError("session registry mismatch")
        if any(a.close > b.open for a,b in zip(sessions,sessions[1:])):
            raise ValueError("session registry is not chronological")
        for b in bars:
            declared = registry[b.session_id]
            if not declared.open <= b.start < b.end <= declared.close or (b.start-declared.open).total_seconds() % self.interval_seconds:
                raise ValueError("retained bar calendar mismatch")
        if any((x.close-x.open).total_seconds() % self.interval_seconds for x in sessions):
            raise ValueError("retained calendar interval mismatch")
        session = Session(**s["current_session"]) if s["current_session"] is not None else None
        last_now = _dt(s["last_now"], "last_now") if s["last_now"] is not None else None
        if count == 0:
            if any((bars, session, last_now, s["symbol"], session_count, reset, s["reasons"])):
                raise ValueError("invalid empty snapshot")
        else:
            _identifier(s["symbol"], "symbol")
            if session is None or last_now is None or session_count < 1:
                raise ValueError("missing snapshot session/clock")
            if registry.get(session.id) != session:
                raise ValueError("current calendar registry mismatch")
            if any(x.symbol != s["symbol"] or x.available_at > last_now or
                   (x.end-x.start).total_seconds() != self.interval_seconds for x in bars):
                raise ValueError("invalid snapshot bars")
            if any(a.end > b.start for a, b in zip(bars, bars[1:])):
                raise ValueError("snapshot bars out of order")
            if not (bars[-1].session_id == session.id and session.open <= bars[-1].start < bars[-1].end <= session.close):
                raise ValueError("snapshot current session mismatch")
            if (bars[-1].start-session.open).total_seconds() % self.interval_seconds:
                raise ValueError("snapshot grid mismatch")
            ordinal = int((bars[-1].end-session.open).total_seconds()/self.interval_seconds)
            if session_count != ordinal:
                # Missing bars are reflected by an incomplete VWAP and a lower
                # observed count, not silently counted as accepted observations.
                if s["vwap_complete"] or not 1 <= session_count <= ordinal:
                    raise ValueError("snapshot session count mismatch")
        expected_lengths = {"fast_history": min(max(count-9, 0),16),
                            "fast_signs": min(max(count-10, 0),6),
                            "tr_seed": count if count < 14 else 0,
                            "ema_seed": count if count < 20 else 0}
        sequences = {}
        for key, length in expected_lengths.items():
            if not isinstance(s[key], list) or len(s[key]) != length:
                raise ValueError(f"invalid {key} length")
            if key == "fast_signs":
                if any(isinstance(x,bool) or not isinstance(x,int) or x not in (-1,0,1) for x in s[key]):
                    raise ValueError("invalid slope signs")
                sequences[key] = list(s[key])
            else:
                sequences[key] = [_number(x,key,minimum=0 if key in ("tr_seed","ema_seed") else None) for x in s[key]]
        numbers = {}
        for key, threshold in (("atr",14),("ema",20),("last_m2",3),("last_fast",10),("last_slow",25)):
            if (s[key] is None) != (count < threshold):
                raise ValueError(f"invalid {key} availability")
            numbers[key] = None if s[key] is None else _number(s[key],key,minimum=0 if key in ("atr","ema") else None)
        closes = [x.close for x in bars]
        if count >= 3 and numbers["last_m2"] != closes[-1]-closes[-3]:
            raise ValueError("snapshot momentum mismatch")
        if count >= 10 and (numbers["last_fast"] != math.fsum(closes[-3:])/3-math.fsum(closes[-10:])/10 or numbers["last_fast"] != sequences["fast_history"][-1]):
            raise ValueError("snapshot fast mismatch")
        if count >= 25 and numbers["last_slow"] != math.fsum(sequences["fast_history"])/16:
            raise ValueError("snapshot slow mismatch")
        volume = _number(s["vwap_volume"], "vwap_volume", minimum=0)
        notional = _number(s["vwap_notional"], "vwap_notional", minimum=0)
        if not isinstance(s["vwap_complete"], bool) or (volume == 0) != (notional == 0):
            raise ValueError("invalid snapshot VWAP")
        if count == 0 and (volume or notional or not s["vwap_complete"]):
            raise ValueError("invalid empty VWAP")
        if not isinstance(s["reasons"], list) or len(s["reasons"]) > 32:
            raise ValueError("invalid reasons")
        reasons = []
        for r in s["reasons"]:
            if not isinstance(r,dict) or set(r) != {"code","bar_end","generation"}:
                raise ValueError("invalid reason record")
            if r["code"] not in {"INTRADAY_GAP_RESET", "UNKNOWN_SESSION_CHAIN_RESET", "MISSING_SESSION_TAIL_RESET"}:
                raise ValueError("invalid reset reason")
            generation = _integer(r["generation"], "generation", 1)
            at = _dt(r["bar_end"], "reason bar_end")
            if generation > reset or last_now is None or at > last_now:
                raise ValueError("invalid reason provenance")
            reasons.append({"code":r["code"],"bar_end":at.isoformat(),"generation":generation})
        if reset == 0 and reasons or reset > 0 and (not reasons or reasons[-1]["generation"] != reset):
            raise ValueError("reset/reasons mismatch")
        self.symbol, self.current_session, self.last_now = s["symbol"], session, last_now
        self._sessions = registry
        self.reset_count, self.bar_count, self.session_bar_count = reset, count, session_count
        self._bars = deque(bars,maxlen=self.lookback)
        self._fast_history = deque(sequences["fast_history"],maxlen=16)
        self._fast_signs = deque(sequences["fast_signs"],maxlen=6)
        self._tr_seed, self._ema_seed = sequences["tr_seed"], sequences["ema_seed"]
        self._atr, self._ema = numbers["atr"], numbers["ema"]
        self._last_m2, self._last_fast, self._last_slow = (numbers[k] for k in ("last_m2","last_fast","last_slow"))
        self._vwap_volume, self._vwap_notional = volume, notional
        self._vwap_complete = s["vwap_complete"]
        self.reasons = deque(reasons,maxlen=32)
