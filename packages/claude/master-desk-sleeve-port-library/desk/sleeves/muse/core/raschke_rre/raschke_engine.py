"""Closed-bar research policy. No orders, fills, positions or broker connectivity.

Canonical numerical deadband is 1e-9 price units, matching raschke_core.
RRE3 uses the RRE2 policy and identical underlying source IDs.
"""
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import json
import math

from .raschke_core import Bar, Core, Features, Session, _dt, _hash, _number, _integer

VERSION = "raschke-policy-1"
MAX_SNAPSHOT_BYTES = 256_000
COUNTERS = ("bars", "pulse_arms", "cross_arms", "cancelled", "attempts", "rejected", "intents")


def _id(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{name}: nonempty string of at most256 characters required")
    return value


def _json(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        return {f.name: _json(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, deque)):
        return [_json(x) for x in value]
    return value


def _copy_tree(value):
    """Copy small episode/diagnostic trees without traversing frozen core data."""
    if type(value) is dict:
        return {key: _copy_tree(item) for key, item in value.items()}
    if type(value) is list:
        return [_copy_tree(item) for item in value]
    if type(value) is tuple:
        return tuple(_copy_tree(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool, datetime)):
        return value
    # Keep extension/debug metadata isolated, even if outside the JSON contract.
    return deepcopy(value)


@dataclass(frozen=True)
class PriorSessionReference:
    """Caller-attested complete prior RTH HLC, frozen before this session opens."""
    symbol: str
    session_id: str
    previous_session: Session
    available_at: datetime
    high: float
    low: float
    close: float
    series_id: str
    calendar_version: str
    complete: bool

    def __post_init__(self):
        for name in ("symbol", "session_id", "series_id", "calendar_version"):
            _id(getattr(self, name), name)
        if not isinstance(self.previous_session, Session):
            raise ValueError("previous_session must be a Session")
        _id(self.previous_session.id, "previous session id")
        object.__setattr__(self, "available_at", _dt(self.available_at, "reference availability"))
        for name in ("high", "low", "close"):
            object.__setattr__(self, name, _number(getattr(self, name), name, strictly_positive=True))
        if not self.low <= self.close <= self.high:
            raise ValueError("reference HLC inconsistent")
        if not isinstance(self.complete, bool):
            raise ValueError("complete must be an explicit boolean")
        if self.available_at < self.previous_session.close:
            raise ValueError("reference unavailable before prior session closes")

    @property
    def reference_id(self):
        return _hash(self.to_dict())

    def to_dict(self):
        return _json(self)

    @classmethod
    def from_dict(cls, value):
        try:
            value = dict(value)
            value["previous_session"] = Session(**value["previous_session"])
            return cls(**value)
        except (TypeError, KeyError) as exc:
            raise ValueError("invalid reference record") from exc


# Short alias for callers; the identity/availability contract is unchanged.
Reference = PriorSessionReference


@dataclass(frozen=True)
class PolicyConfig:
    tick_size: float
    series_id: str
    calendar_version: str
    variant: str = "RRE1"
    cost_reserve_price: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "tick_size", _number(self.tick_size, "tick_size", strictly_positive=True))
        object.__setattr__(self, "cost_reserve_price", _number(self.cost_reserve_price, "cost_reserve_price", minimum=0))
        _id(self.series_id, "series_id")
        _id(self.calendar_version, "calendar_version")
        if self.variant not in ("RRE1", "RRE2", "RRE3"):
            raise ValueError("variant must be RRE1, RRE2 or RRE3")


@dataclass(frozen=True)
class Intent:
    source_id: str
    variant: str
    setup: str
    symbol: str
    direction: int
    signal_at: datetime
    available_at: datetime
    expires_at: datetime
    entry_reference: float
    trigger: float
    stop: float
    target: float
    atr14: float
    session_id: str
    generation: int
    episode_id: str
    session_close: datetime
    series_id: str
    calendar_version: str
    reference_id: str
    max_hold_seconds: int = 1800

    def __post_init__(self):
        for name in ("source_id", "setup", "symbol", "session_id", "episode_id", "series_id", "calendar_version", "reference_id"):
            _id(getattr(self, name), name)
        if self.variant not in ("RRE1", "RRE2", "RRE3") or type(self.direction) is not int or self.direction not in (-1, 1):
            raise ValueError("invalid intent variant/direction")
        for name in ("signal_at", "available_at", "expires_at", "session_close"):
            object.__setattr__(self, name, _dt(getattr(self, name), name))
        if not self.signal_at <= self.available_at < self.expires_at <= self.session_close:
            raise ValueError("invalid intent availability/expiry")
        for name in ("entry_reference", "trigger", "stop", "target", "atr14"):
            object.__setattr__(self, name, _number(getattr(self, name), name, strictly_positive=True))
        if self.direction * (self.entry_reference-self.stop) <= 0 or self.direction*(self.target-self.entry_reference) <= 0:
            raise ValueError("invalid directional intent geometry")
        _integer(self.generation, "generation")
        if self.max_hold_seconds != 1800 or type(self.max_hold_seconds) is not int:
            raise ValueError("canonical hold obligation is1800 seconds")

    @property
    def max_chase_price(self):
        """Maximum price distance from frozen trigger, not an absolute price."""
        return 0.2*self.atr14

    def to_dict(self):
        return _json(self)


EntryIntent = Intent


class PolicyEngine:
    """Single-series deterministic research state; callers serialize update calls.

    update validates the reference BEFORE mutating the core. All successful state
    changes commit together from an isolated bounded state copy. Bad inputs raise ValueError;
    valid observations with no qualifying intent return an empty tuple.
    """
    def __init__(self, config=None, *, variant="RRE1", tick_size=None,
                 series_id=None, calendar_version=None, cost_reserve_price=0.0):
        if config is None:
            config = PolicyConfig(tick_size, series_id, calendar_version, variant, cost_reserve_price)
        if not isinstance(config, PolicyConfig):
            raise ValueError("PolicyConfig required")
        self.config = config
        self.core = Core(lookback=64, interval_seconds=300, tick_epsilon=1e-9)
        self._session_id = None
        self._generation = 0
        self._reference = None
        self._previous = None
        self._pulse = None
        self._cross = None
        self._decisions = deque(maxlen=128)
        self.counters = {k: 0 for k in COUNTERS}

    @property
    def base_variant(self):
        return "RRE1" if self.config.variant == "RRE1" else "RRE2"

    @property
    def config_fingerprint(self):
        return _hash({"version": VERSION, "policy": _json(self.config), "core": self.core.config})

    @property
    def signal_fingerprint(self):
        cfg = _json(self.config)
        cfg["variant"] = self.base_variant
        return _hash({"version": VERSION, "policy": cfg, "core": self.core.config})

    def _count(self, key):
        self.counters[key] = min(self.counters[key]+1, 2**63-1)

    def _decision(self, code, bar, setup=None, episode=None, **details):
        self._decisions.append(dict(code=code, at=bar.end.isoformat(), setup=setup,
                                    episode_id=episode, details=details))

    def drain_decisions(self):
        result = tuple(deepcopy(list(self._decisions)))
        self._decisions.clear()
        return result

    @property
    def decisions(self):
        return tuple(deepcopy(list(self._decisions)))

    def status(self):
        return dict(variant=self.config.variant, base_variant=self.base_variant,
                    session_id=self._session_id, generation=self._generation,
                    ready=self._previous is not None, pulse=deepcopy(self._pulse),
                    first_cross=deepcopy(self._cross), counters=dict(self.counters),
                    reference_id=self._reference.reference_id if self._reference else None)

    def _validate_reference(self, bar, session, reference, now):
        if not isinstance(bar, Bar) or not isinstance(session, Session) or not isinstance(reference, PriorSessionReference):
            raise ValueError("Bar, Session and PriorSessionReference required")
        now = _dt(now, "now")
        for value in (bar.symbol, bar.session_id, session.id):
            _id(value, "series/session identity")
        if reference.symbol != bar.symbol or reference.session_id != session.id or bar.session_id != session.id:
            raise ValueError("reference symbol/current session mismatch")
        if self.config.variant == "RRE3" and bar.symbol != "SPY":
            raise ValueError("RRE3 underlying observations must be SPY")
        if reference.series_id != self.config.series_id or reference.calendar_version != self.config.calendar_version:
            raise ValueError("reference lineage/calendar mismatch")
        if not reference.complete:
            raise ValueError("complete prior-session coverage required")
        prior = reference.previous_session
        if session.previous_id is None or prior.id != session.previous_id or prior.close > session.open:
            raise ValueError("reference is not declared immediately preceding session")
        if not prior.close <= reference.available_at <= session.open or reference.available_at > now:
            raise ValueError("reference must be known and frozen by session open")
        registered = self.core._sessions.get(prior.id)
        if registered is not None and registered != prior:
            raise ValueError("conflicting prior registered calendar")
        if self._session_id == session.id and self._reference != reference:
            raise ValueError("reference revision within session; explicit replay required")
        return now

    def _clone(self):
        """Independent transaction state, sharing only immutable domain records.

        The public coordinator may use this private protocol to stage independent
        policy lanes. Formula evaluation remains in Core.update; no precomputed
        feature bypass or changed state-machine rule is introduced.
        """
        candidate = object.__new__(type(self))
        candidate.__dict__ = self.__dict__.copy()
        candidate.core = self.core._clone()
        candidate._pulse = _copy_tree(self._pulse)
        candidate._cross = _copy_tree(self._cross)
        candidate._decisions = deque((_copy_tree(record) for record in self._decisions),
                                    maxlen=self._decisions.maxlen)
        candidate.counters = self.counters.copy()
        return candidate

    def update(self, bar, session, reference, now):
        now = self._validate_reference(bar, session, reference, now)
        candidate = self._clone()
        prior_end = candidate.core._bars[-1].end if candidate.core._bars else None
        f = candidate.core.update(bar, session, now)
        accepted_end = candidate.core._bars[-1].end if candidate.core._bars else None
        if accepted_end == prior_end:  # Core authenticated an exact retained duplicate.
            return ()
        candidate._count("bars")
        reset = candidate._session_id != session.id or candidate._generation != candidate.core.reset_count
        if reset:
            if candidate._pulse or candidate._cross:
                candidate._count("cancelled")
                candidate._decision("CANCEL_SESSION_OR_GENERATION_RESET", bar)
            candidate._previous = candidate._pulse = candidate._cross = None
        candidate._session_id, candidate._generation = session.id, candidate.core.reset_count
        candidate._reference = reference
        result = () if f is None else candidate._advance_policy(bar, f, session, now)
        self.__dict__.update(candidate.__dict__)
        return result

    def _sign(self, x):
        return self.core._sign(x)

    def _rounded(self, price, upward):
        value = (Decimal(str(price))/Decimal(str(self.config.tick_size))).to_integral_value(
            rounding=ROUND_CEILING if upward else ROUND_FLOOR)*Decimal(str(self.config.tick_size))
        return _number(float(value), "rounded price")

    def _trigger(self, bar, d):
        anchor = bar.high if d == 1 else bar.low
        return self._rounded(Decimal(str(anchor))+Decimal(d)*Decimal(str(self.config.tick_size)), d == 1)

    def _stop(self, adverse, atr, d):
        return self._rounded(Decimal(str(adverse))-Decimal(d)*Decimal("0.1")*Decimal(str(atr)), d == -1)

    def _episode_id(self, setup, bar, d):
        return _hash(dict(config=self.signal_fingerprint, symbol=bar.symbol, session=bar.session_id,
                          generation=self._generation, setup=setup, arm=bar.end.isoformat(),
                          direction=d, reference=self._reference.reference_id))

    def _advance_policy(self, bar, f, session, now):
        """Internal pure-policy seam; public callers must use update, not fixtures."""
        result = []
        if self.base_variant == "RRE1":
            self._pulse_step(bar, f, session, now, result)
        else:
            self._context_step(bar, f, session, now, result)
        self._previous = f
        return tuple(result)

    def _pulse_step(self, bar, f, session, now, result):
        if self._pulse:
            a, self._pulse = self._pulse, None  # Consume the only next-bar opportunity.
            contiguous = bar.start == _dt(a["arm_end"], "arm_end") and f.bar_count == a["arm_count"]+1
            if contiguous and f.pf3 == a["direction"] and a["direction"]*(bar.close-a["trigger"]) >= 0:
                item = self._attempt("PF3_PULSE", a, bar, f, session, now)
                if item: result.append(item)
            else:
                self._count("cancelled")
                self._decision("PULSE_NEXT_BAR_FAILED", bar, "PF3_PULSE", a["episode_id"])
        prev = self._previous
        if prev is not None and f.bar_count >= 27 and f.pf3 in (-1,1) and f.pf3 != prev.pf3:
            if not math.isfinite(f.atr14) or f.atr14 <= 0:
                self._decision("WAIT_INVALID_ATR", bar, "PF3_PULSE")
                return
            d = f.pf3
            self._pulse = dict(episode_id=self._episode_id("PF3_PULSE",bar,d), direction=d,
                               arm_end=bar.end.isoformat(), arm_count=f.bar_count,
                               atr=f.atr14, trigger=self._trigger(bar,d),
                               stop=self._stop(bar.low if d == 1 else bar.high,f.atr14,d))
            if self._pulse["trigger"] <= 0 or self._pulse["stop"] <= 0:
                self._pulse = None
                self._decision("WAIT_NONPOSITIVE_ARM_GEOMETRY",bar,"PF3_PULSE")
                return
            self._count("pulse_arms")
            self._decision("PULSE_ARMED",bar,"PF3_PULSE",self._pulse["episode_id"])

    def _cancel_cross(self, code, bar):
        a, self._cross = self._cross, None
        if a:
            self._count("cancelled")
            self._decision(code,bar,"FIRST_CROSS",a["episode_id"])

    def _context_step(self, bar, f, session, now, result):
        had_cross = self._cross is not None
        prev = self._previous
        d = self._sign(f.slow)
        crossed = prev is not None and d != 0 and self._sign(prev.slow) != d
        if crossed:
            self._cancel_cross("CANCEL_SUPERSEDED_CROSS",bar)
            self._cross = dict(episode_id=self._episode_id("FIRST_CROSS",bar,d), direction=d,
                               arm_end=bar.end.isoformat(), arm_count=f.bar_count,
                               deadline=(bar.end+timedelta(minutes=65)).isoformat(),
                               phase="WAIT_FIRST_PULLBACK", last_pullback=None,
                               adverse=None, atr=None, trigger=None, stop=None)
            self._count("cross_arms")
            self._decision("FIRST_CROSS_ARMED",bar,"FIRST_CROSS",self._cross["episode_id"])
            return  # A cross and its first pullback may not share a bar.
        if self._cross:
            a = self._cross; d = a["direction"]
            age = f.bar_count-a["arm_count"]
            if age > 12 or now >= _dt(a["deadline"],"cross deadline"):
                self._cancel_cross("CANCEL_CROSS_EXPIRED",bar)
            elif self._sign(f.slow) != d:
                self._cancel_cross("CANCEL_SLOW_SIDE",bar)
            else:
                slope = d*self._sign(f.dfast)
                if a["phase"] == "WAIT_FIRST_PULLBACK":
                    if age > 0 and slope < 0:
                        a["phase"] = "FIRST_PULLBACK"
                        a["last_pullback"] = {"high":bar.high,"low":bar.low,"end":bar.end.isoformat()}
                        a["adverse"] = bar.low if d == 1 else bar.high
                        self._decision("FIRST_PULLBACK_STARTED",bar,"FIRST_CROSS",a["episode_id"])
                elif a["phase"] == "FIRST_PULLBACK":
                    # Include zero-slope bars AND the first resumption wick.
                    a["adverse"] = min(a["adverse"],bar.low) if d == 1 else max(a["adverse"],bar.high)
                    if slope < 0:
                        a["last_pullback"] = {"high":bar.high,"low":bar.low,"end":bar.end.isoformat()}
                    elif slope > 0:
                        if f.atr14 <= 0:
                            self._cancel_cross("CANCEL_INVALID_ATR",bar)
                            return
                        anchor = a["last_pullback"]
                        boundary = anchor["high"] if d == 1 else anchor["low"]
                        a["trigger"] = self._rounded(Decimal(str(boundary))+Decimal(d)*Decimal(str(self.config.tick_size)),d == 1)
                        a["atr"] = f.atr14
                        a["stop"] = self._stop(a["adverse"],f.atr14,d)
                        if a["trigger"] <= 0 or a["stop"] <= 0:
                            self._cancel_cross("CANCEL_NONPOSITIVE_ARM_GEOMETRY",bar)
                            return
                        a["phase"] = "WAIT_PRICE_CONFIRMATION"
                        self._decision("FIRST_RESUMPTION",bar,"FIRST_CROSS",a["episode_id"])
                        if d*(bar.close-a["trigger"]) >= 0:
                            self._cross = None
                            item = self._attempt("FIRST_CROSS",a,bar,f,session,now)
                            if item: result.append(item)
                else:
                    invalidated = bar.low <= a["stop"] if d == 1 else bar.high >= a["stop"]
                    if invalidated:
                        self._cancel_cross("CANCEL_STRUCTURAL_WICK",bar)
                    elif slope < 0:
                        self._cancel_cross("CANCEL_SECOND_PULLBACK",bar)
                    elif slope > 0 and d*(bar.close-a["trigger"]) >= 0:
                        self._cross = None
                        item = self._attempt("FIRST_CROSS",a,bar,f,session,now)
                        if item: result.append(item)
        if had_cross:
            return  # Do not bypass a just-cancelled/consumed directional thesis.
        self._rotation_step(bar,f,session,now,result)

    def _rotation_step(self, bar, f, session, now, result):
        if f.atr14 <= 0 or len(f.fast_slope_signs) != 6:
            return
        flips = sum(a*b < 0 for a,b in zip(f.fast_slope_signs,f.fast_slope_signs[1:]))
        if abs(f.slow)/f.atr14 > 0.15 or flips < 2:
            return
        ref = self._reference; tick = self.config.tick_size
        low_penetration = float(Decimal(str(ref.low))-Decimal(str(tick)))
        high_penetration = float(Decimal(str(ref.high))+Decimal(str(tick)))
        long_trigger = self._rounded(Decimal(str(ref.low))+Decimal(str(tick)),True)
        short_trigger = self._rounded(Decimal(str(ref.high))-Decimal(str(tick)),False)
        below, above = bar.low <= low_penetration, bar.high >= high_penetration
        if below and above:
            self._decision("WAIT_AMBIGUOUS_DOUBLE_SWEEP",bar,"FAILED_BREAK")
            return
        d = 1 if below and bar.close >= long_trigger else -1 if above and bar.close <= short_trigger else 0
        if not d:
            return
        a = dict(episode_id=self._episode_id("FAILED_BREAK",bar,d), direction=d, atr=f.atr14,
                 trigger=long_trigger if d == 1 else short_trigger,
                 stop=self._stop(bar.low if d == 1 else bar.high,f.atr14,d))
        item = self._attempt("FAILED_BREAK",a,bar,f,session,now,required_destination=f.vwap)
        if item: result.append(item)

    def _attempt(self, setup, a, bar, f, session, now, required_destination=None):
        self._count("attempts")
        d, entry, trigger, stop, atr = a["direction"],bar.close,a["trigger"],a["stop"],a["atr"]
        def reject(code,**details):
            self._count("rejected");self._decision(code,bar,setup,a["episode_id"],**details)
            return None
        cutoff = session.close-timedelta(minutes=5)
        expiry = min(bar.end+timedelta(minutes=5),cutoff)
        if bar.end < session.open+timedelta(minutes=30):
            return reject("REJECT_ENTRY_WINDOW")
        if now >= expiry or bar.available_at >= expiry:
            return reject("REJECT_INTENT_EXPIRED")
        if not all(math.isfinite(x) and x > 0 for x in (entry,trigger,stop,atr)):
            return reject("REJECT_NONPOSITIVE_GEOMETRY")
        if d*(entry-trigger) < 0 or abs(entry-trigger) > 0.2*atr+1e-12:
            return reject("REJECT_CHASE",distance=abs(entry-trigger),maximum=0.2*atr)
        risk = d*(entry-stop)
        if risk <= 0:
            return reject("REJECT_STOP_GEOMETRY")
        nominal = float(Decimal(str(entry))+Decimal(d)*Decimal("1.5")*(Decimal(d)*(Decimal(str(entry))-Decimal(str(stop)))))
        levels = [x for x in (self._reference.high,self._reference.low,self._reference.close) if d*(x-entry) > 0]
        if setup == "FAILED_BREAK":
            if required_destination is None or not math.isfinite(required_destination) or d*(required_destination-entry) <= 0:
                return reject("REJECT_VWAP_DESTINATION")
            levels.append(required_destination)
        target = min([nominal]+levels) if d == 1 else max([nominal]+levels)
        if not math.isfinite(target) or target <= 0:
            return reject("REJECT_TARGET_GEOMETRY")
        target = self._rounded(target,d == -1)  # Never round through a nearer obstacle.
        cost = self.config.cost_reserve_price
        reward = d*(target-entry)-cost
        net_rr = reward/(risk+cost)
        if reward <= 0 or net_rr+1e-12 < 1.2:
            return reject("REJECT_NET_RR",net_rr=net_rr,target=target)
        source_id = _hash(dict(episode_id=a["episode_id"],confirmation=bar.end.isoformat(),setup=setup))
        # Processing time is the earliest executable intent availability. The bar
        # availability remains independently preserved in the core snapshot.
        intent = Intent(source_id,self.config.variant,setup,bar.symbol,d,bar.end,now,expiry,
                        entry,trigger,stop,target,atr,session.id,f.generation,a["episode_id"],
                        session.close,self.config.series_id,self.config.calendar_version,
                        self._reference.reference_id)
        self._count("intents")
        self._decision("INTENT",bar,setup,a["episode_id"],source_id=source_id,
                       net_rr=net_rr,trigger=trigger,stop=stop,target=target,
                       source_available_at=bar.available_at.isoformat(),decision_at=now.isoformat())
        return intent

    def snapshot(self):
        state = dict(core=self.core.snapshot(),session_id=self._session_id,generation=self._generation,
                     reference=self._reference.to_dict() if self._reference else None,
                     previous=_json(self._previous),pulse=deepcopy(self._pulse),cross=deepcopy(self._cross),
                     decisions=deepcopy(list(self._decisions)),counters=dict(self.counters))
        return dict(version=VERSION,config=_json(self.config),config_fingerprint=self.config_fingerprint,
                    state=state,state_sha256=_hash(state))

    dump_state = snapshot

    @classmethod
    def from_snapshot(cls, value):
        try:
            if not isinstance(value,dict) or set(value) != {"version","config","config_fingerprint","state","state_sha256"}:
                raise ValueError("invalid policy snapshot envelope")
            if len(json.dumps(value,allow_nan=False)) > MAX_SNAPSHOT_BYTES or value["version"] != VERSION:
                raise ValueError("snapshot size/version mismatch")
            obj = cls(PolicyConfig(**value["config"]))
            if value["config_fingerprint"] != obj.config_fingerprint:
                raise ValueError("policy configuration fingerprint mismatch")
            s = value["state"]
            if not isinstance(s,dict) or set(s) != set(obj.snapshot()["state"]) or _hash(s) != value["state_sha256"]:
                raise ValueError("invalid policy state fields/hash")
            obj.core = Core.from_snapshot(s["core"])
            if obj.core.config != Core().config:
                raise ValueError("noncanonical core configuration")
            obj._restore_policy(s)
            return obj
        except (TypeError,KeyError,OverflowError,AttributeError) as exc:
            raise ValueError("malformed policy snapshot") from exc

    def load_snapshot(self,value):
        candidate = self.from_snapshot(value)
        if candidate.config_fingerprint != self.config_fingerprint:
            raise ValueError("cannot load different policy configuration")
        self.__dict__.update(candidate.__dict__)

    load_state = load_snapshot

    def _restore_policy(self,s):
        self._session_id=s["session_id"]
        self._generation=_integer(s["generation"],"generation")
        if self._generation != self.core.reset_count:
            raise ValueError("policy/core generation mismatch")
        self._reference=PriorSessionReference.from_dict(s["reference"]) if s["reference"] is not None else None
        if self.core.current_session is None:
            if any(x is not None for x in (self._session_id,self._reference,s["previous"],s["pulse"],s["cross"])):
                raise ValueError("nonempty policy with empty core")
        else:
            last=self.core._bars[-1]
            if self._session_id != self.core.current_session.id or self._reference is None:
                raise ValueError("missing current policy session/reference")
            self._validate_reference(last,self.core.current_session,self._reference,self.core.last_now)
        self._previous=None
        if s["previous"] is not None:
            p=dict(s["previous"])
            for name in ("bar_end","available_at"):p[name]=_dt(p[name],name)
            p["fast_slope_signs"]=tuple(p["fast_slope_signs"])
            f=Features(**p)
            for name in ("close","atr14","ema20","m2","fast","slow","dm2","dfast","dslow"):
                _number(getattr(f,name),name)
            if f.vwap is not None:_number(f.vwap,"vwap",strictly_positive=True)
            if f.pf3 not in (-1,0,1) or type(f.pf3) is not int or len(f.fast_slope_signs)!=6 or any(type(x)is not int or x not in (-1,0,1) for x in f.fast_slope_signs):
                raise ValueError("invalid previous feature signs")
            if not self.core._bars or f.bar_end != self.core._bars[-1].end or f.available_at != self.core._bars[-1].available_at or f.symbol != self.core.symbol:
                raise ValueError("previous feature observation mismatch")
            if f.bar_count != self.core.bar_count or f.session_bar_count != self.core.session_bar_count or f.generation != self._generation:
                raise ValueError("previous feature counts mismatch")
            if f.fast != self.core._last_fast or f.slow != self.core._last_slow or f.m2 != self.core._last_m2 or f.close != self.core._bars[-1].close or f.atr14 != self.core._atr or f.ema20 != self.core._ema:
                raise ValueError("previous feature/core numeric mismatch")
            signs=[self._sign(x) for x in (f.dm2,f.dfast,f.dslow)]
            expected=signs[0] if signs[0] and signs.count(signs[0])==3 else 0
            if f.pf3 != expected or tuple(self.core._fast_signs)!=f.fast_slope_signs:
                raise ValueError("previous PF3/sign mismatch")
            self._previous=f
        if (self._previous is None) != (self.core.bar_count < 26):
            raise ValueError("previous feature readiness mismatch")
        self._pulse=self._restore_episode(s["pulse"],"pulse")
        self._cross=self._restore_episode(s["cross"],"cross")
        if self.base_variant=="RRE1" and self._cross or self.base_variant=="RRE2" and self._pulse:
            raise ValueError("wrong profile episode")
        if not isinstance(s["decisions"],list) or len(s["decisions"])>128:
            raise ValueError("unbounded decision tail")
        for r in s["decisions"]:
            if not isinstance(r,dict) or set(r)!={"code","at","setup","episode_id","details"} or not isinstance(r["details"],dict):
                raise ValueError("invalid decision record")
            _id(r["code"],"decision code")
            at=_dt(r["at"],"decision at")
            if self.core.last_now is None or at>self.core.last_now:
                raise ValueError("future decision")
        self._decisions=deque(deepcopy(s["decisions"]),maxlen=128)
        if not isinstance(s["counters"],dict) or set(s["counters"])!=set(COUNTERS):
            raise ValueError("invalid counters")
        self.counters={k:_integer(v,k) for k,v in s["counters"].items()}
        if any(v>2**63-1 for v in self.counters.values()) or self.counters["bars"]<self.core.bar_count:
            raise ValueError("invalid counter bounds")

    def _restore_episode(self,value,kind):
        if value is None:return None
        pulse_fields={"episode_id","direction","arm_end","arm_count","atr","trigger","stop"}
        cross_fields={"episode_id","direction","arm_end","arm_count","deadline","phase","last_pullback","adverse","atr","trigger","stop"}
        if not isinstance(value,dict) or set(value)!=(pulse_fields if kind=="pulse" else cross_fields) or self._previous is None:
            raise ValueError("invalid episode shape/readiness")
        a=deepcopy(value);_id(a["episode_id"],"episode id")
        if type(a["direction"])is not int or a["direction"] not in (-1,1):raise ValueError("episode direction")
        arm_count=_integer(a["arm_count"],"arm_count",27)
        arm_end=_dt(a["arm_end"],"arm_end")
        age=self.core.bar_count-arm_count
        if age<0 or arm_end>self.core._bars[-1].end or arm_end<self.core.current_session.open:
            raise ValueError("episode arm provenance")
        if (self.core._bars[-1].end-arm_end).total_seconds()!=age*300:
            raise ValueError("episode age/grid mismatch")
        if kind=="pulse":
            if age!=0:raise ValueError("pulse survived its only confirmation bar")
        else:
            if age>12 or _dt(a["deadline"],"deadline")!=arm_end+timedelta(minutes=65):raise ValueError("cross deadline")
            if a["phase"] not in ("WAIT_FIRST_PULLBACK","FIRST_PULLBACK","WAIT_PRICE_CONFIRMATION"):raise ValueError("cross phase")
            lp=a["last_pullback"]
            if a["phase"]=="WAIT_FIRST_PULLBACK":
                if any(a[k]is not None for k in ("last_pullback","adverse","atr","trigger","stop")):raise ValueError("premature pullback fields")
            else:
                if not isinstance(lp,dict) or set(lp)!={"high","low","end"}:raise ValueError("pullback shape")
                h=_number(lp["high"],"pullback high",strictly_positive=True);lo=_number(lp["low"],"pullback low",strictly_positive=True)
                if h<lo or not arm_end<_dt(lp["end"],"pullback end")<=self.core._bars[-1].end:raise ValueError("pullback chronology/geometry")
                _number(a["adverse"],"adverse",strictly_positive=True)
                if a["direction"]==1 and a["adverse"]>lo or a["direction"]==-1 and a["adverse"]<h:raise ValueError("pullback adverse extreme")
            if a["phase"]!="WAIT_PRICE_CONFIRMATION":
                if any(a[k]is not None for k in ("atr","trigger","stop")):raise ValueError("premature frozen geometry")
                return a
        for k in ("atr","trigger","stop"):_number(a[k],k,strictly_positive=True)
        if a["direction"]*(a["trigger"]-a["stop"])<=0:raise ValueError("episode stop geometry")
        return a
