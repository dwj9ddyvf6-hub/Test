"""Versioned, timezone-aware contracts for the executable Saty research system."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from math import isfinite
from typing import Any
from core.saty_gpt_v03.reference import Bar, Features, Session

VERSION = '0.3.0'

def aware(t: datetime) -> None:
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')

def number(*values: float) -> None:
    if not all(isfinite(v) for v in values):
        raise ValueError('finite numbers required')

def stable_id(*parts: Any) -> str:
    return sha256('|'.join(str(x) for x in parts).encode()).hexdigest()[:28]

def jsonable(x: Any) -> Any:
    if isinstance(x, datetime): return x.isoformat()
    if isinstance(x, timedelta): return x.total_seconds()
    if hasattr(x, '__dataclass_fields__'): return jsonable(asdict(x))
    if isinstance(x, dict): return {str(k): jsonable(v) for k,v in x.items()}
    if isinstance(x, (tuple,list)): return [jsonable(v) for v in x]
    return x

@dataclass(frozen=True)
class Observation:
    symbol: str
    timeframe: str
    bar: Bar
    available_at: datetime
    provider: str = 'caller'
    venue: str = 'US'
    session_policy: str = 'regular'
    adjustment: str = 'raw'
    revision: str = '0'
    def validate(self) -> None:
        self.bar.validate(); aware(self.available_at)
        if self.available_at < self.bar.end: raise ValueError('bar available before close')
        if not self.symbol or not self.timeframe or not self.provider: raise ValueError('missing lineage')
    @property
    def event_id(self) -> str:
        return stable_id(self.symbol,self.timeframe,self.bar.end.isoformat(),self.provider,self.revision)

@dataclass(frozen=True)
class Frame:
    observation: Observation
    features: Features
    count: int
    @property
    def bar(self) -> Bar: return self.observation.bar
    @property
    def available_at(self) -> datetime: return self.observation.available_at
    @property
    def timeframe(self) -> str: return self.observation.timeframe
    @property
    def symbol(self) -> str: return self.observation.symbol

@dataclass(frozen=True)
class Pivot:
    kind: str
    price: float
    bar_end: datetime
    confirmed_at: datetime
    phase: float | None
    timeframe: str

@dataclass(frozen=True)
class Level:
    price: float
    kind: str
    timeframe: str
    known_at: datetime
    source: str = 'causal_structure'
    lower: float | None = None
    upper: float | None = None

@dataclass(frozen=True)
class Reference:
    horizon: str
    period_end: datetime
    available_at: datetime
    close: float
    atr: float
    valid_from: datetime
    valid_until: datetime
    period_id: str = ''
    def validate(self, at: datetime) -> None:
        for t in (at,self.period_end,self.available_at,self.valid_from,self.valid_until): aware(t)
        number(self.close,self.atr)
        if self.close<=0 or self.atr<=0: raise ValueError('invalid reference prices')
        if not self.period_end<=self.available_at<=self.valid_from<=at<self.valid_until: raise ValueError('future, stale or misaligned reference')
    def price(self, multiple: float) -> float: return self.close+multiple*self.atr

@dataclass(frozen=True)
class Context:
    as_of: datetime
    execution: Frame
    frames: dict[str, Frame]
    reference: Reference
    levels: tuple[Level,...] = ()
    pivots: tuple[Pivot,...] = ()
    session: Session | None = None
    blockers: tuple[str,...] = ()
    vix: float | None = None
    vix_available_at: datetime | None = None
    metadata: dict[str,Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Signal:
    signal_id: str
    symbol: str
    timeframe: str
    setup: str
    direction: int
    bar_end: datetime
    available_at: datetime
    expires_at: datetime
    reference_entry: float
    stop: float
    targets: tuple[float,...]
    atr: float
    anchor: float
    reference_horizon: str
    risk_multiplier: float = 1.0
    metadata: dict[str,Any] = field(default_factory=dict)
    def validate(self) -> None:
        for t in (self.bar_end,self.available_at,self.expires_at): aware(t)
        number(self.reference_entry,self.stop,self.atr,self.anchor,self.risk_multiplier,*self.targets)
        if self.direction not in (-1,1) or not self.bar_end<=self.available_at<self.expires_at: raise ValueError('invalid signal chronology/direction')
        if self.atr<=0 or not 0<self.risk_multiplier<=1 or self.reference_entry<=0 or self.stop<=0: raise ValueError('invalid signal risk')
        if self.direction*(self.reference_entry-self.stop)<=0 or not self.targets: raise ValueError('invalid signal stop/targets')
        if any(self.direction*(t-self.reference_entry)<=0 for t in self.targets): raise ValueError('target behind entry')
        if any(self.direction*(b-a)<=0 for a,b in zip(self.targets,self.targets[1:])): raise ValueError('unordered targets')

@dataclass(frozen=True)
class Instrument:
    symbol: str
    underlying: str
    asset_type: str = 'equity'
    multiplier: float = 1.0
    tick_size: float = .01
    correlation_group: str = ''
    shortable: bool = False
    option_type: str | None = None
    strike: float | None = None
    expiry: datetime | None = None
    exercise_style: str | None = None
    settlement: str | None = None

@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    at: datetime
    received_at: datetime
    def validate(self, now: datetime, max_age: timedelta=timedelta(seconds=5)) -> None:
        for t in (self.at,self.received_at,now): aware(t)
        number(self.bid,self.ask)
        if not self.at<=self.received_at<=now or now-self.at>max_age: raise ValueError('future/stale quote')
        if self.bid<0 or self.ask<=0 or self.bid>self.ask or min(self.bid_size,self.ask_size)<0: raise ValueError('invalid quote')

@dataclass(frozen=True)
class OrderRequest:
    client_order_id: str
    symbol: str
    side: str
    quantity: int
    limit_price: float
    created_at: datetime
    expires_at: datetime
    signal_id: str
    episode_id: str
    purpose: str = 'entry'
    lot_id: str | None = None

@dataclass(frozen=True)
class Fill:
    fill_id: str
    client_order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    at: datetime
    fee: float = 0.0

# Wire decoders use explicit schemas, never executable object deserialization.
def observation_from_dict(d: dict) -> Observation:
    b=dict(d['bar']); b['start']=datetime.fromisoformat(b['start']); b['end']=datetime.fromisoformat(b['end'])
    return Observation(**{**d,'bar':Bar(**b),'available_at':datetime.fromisoformat(d['available_at'])})

def reference_from_dict(d: dict) -> Reference:
    return Reference(**{**d,**{k:datetime.fromisoformat(d[k]) for k in ('period_end','available_at','valid_from','valid_until')}})

def signal_from_dict(d: dict) -> Signal:
    return Signal(**{**d,**{k:datetime.fromisoformat(d[k]) for k in ('bar_end','available_at','expires_at')},'targets':tuple(d['targets'])})

def instrument_from_dict(d: dict) -> Instrument:
    return Instrument(**{**d,'expiry':datetime.fromisoformat(d['expiry']) if d.get('expiry') else None})

def quote_from_dict(d: dict) -> Quote:
    return Quote(**{**d,'at':datetime.fromisoformat(d['at']),'received_at':datetime.fromisoformat(d['received_at'])})

def order_from_dict(d: dict) -> OrderRequest:
    return OrderRequest(**{**d,'created_at':datetime.fromisoformat(d['created_at']),'expires_at':datetime.fromisoformat(d['expires_at'])})

def fill_from_dict(d: dict) -> Fill:
    return Fill(**{**d,'at':datetime.fromisoformat(d['at'])})

def session_from_dict(d: dict) -> Session:
    return Session(**{**d,**{k:datetime.fromisoformat(d[k]) for k in ('open','entry_start','entry_cutoff','flat_at','close')}})
