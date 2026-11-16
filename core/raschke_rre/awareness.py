"""Bounded causal context. Original fixed hypotheses, never probabilities.

The required gates are explicit caller attestations, not authenticated discovery.
Missing optional historical normalization is None, not a fabricated neutral ratio.
"""
from collections import deque
from copy import copy
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from types import MappingProxyType
import json
import math

from .raschke_core import Bar, Session, Features, _dt, _hash, _number, _integer
from .raschke_engine import _json

VERSION = "rre-context-2"
STATES = ("DATA_BLOCK", "SHOCK_PAUSE", "COMPRESSION", "DIRECTIONAL", "ROTATION", "TRANSITION")


@dataclass(frozen=True)
class ContextConfig:
    series_id: str
    calendar_version: str
    efficiency_bars: int = 6
    opening_range_bars: int = 6
    baseline_sessions: int = 20
    history_limit: int = 40
    hysteresis_bars: int = 2
    shock_tr_atr: float = 3.0
    compression_range_ratio: float = .65
    directional_efficiency: float = .55
    rotation_efficiency: float = .35
    weak_slow_atr: float = .15
    max_bar_delay_seconds: float = 300.0

    def __post_init__(self):
        for key in ("series_id", "calendar_version"):
            if not isinstance(getattr(self,key),str) or not getattr(self,key).strip():
                raise ValueError("context lineage/calendar required")
        for key in ("efficiency_bars","opening_range_bars","baseline_sessions","history_limit","hysteresis_bars"):
            _integer(getattr(self,key),key,1)
            if getattr(self,key)>288: raise ValueError("unbounded context window")
        if self.history_limit < self.baseline_sessions: raise ValueError("insufficient history capacity")
        for key in ("shock_tr_atr","compression_range_ratio","directional_efficiency","rotation_efficiency","weak_slow_atr","max_bar_delay_seconds"):
            object.__setattr__(self,key,_number(getattr(self,key),key,strictly_positive=True))
        if not 0 < self.rotation_efficiency < self.directional_efficiency <= 1:
            raise ValueError("invalid efficiency thresholds")
        if self.max_bar_delay_seconds>300: raise ValueError("context freshness cannot extend intent TTL")


@dataclass(frozen=True)
class ContextGates:
    """Current causal-sequence quality; full-session completeness is separate.

    sequence_complete cannot repair a locally observed missing bar. After such a
    gap, Core must re-warm, and optional full-session OR/normalization stay absent.
    """
    evidence_id: str
    session_id: str
    known_at: datetime
    valid_until: datetime
    calendar_verified: bool
    event_coverage_known: bool
    events_clear: bool
    feed_verified: bool
    sequence_complete: bool

    def __post_init__(self):
        for key in ("evidence_id","session_id"):
            if not isinstance(getattr(self,key),str) or not getattr(self,key).strip(): raise ValueError("gate identity required")
        for key in ("known_at","valid_until"):
            object.__setattr__(self,key,_dt(getattr(self,key),key))
        if self.valid_until<=self.known_at: raise ValueError("invalid gate validity")
        for key in ("calendar_verified","event_coverage_known","events_clear","feed_verified","sequence_complete"):
            if type(getattr(self,key)) is not bool: raise ValueError("explicit gate boolean required")


AwarenessGates = ContextGates


@dataclass(frozen=True)
class ContextSnapshot:
    context_id: str
    symbol: str
    session_id: str
    as_of: datetime
    bar_end: datetime
    available_at: datetime
    state: str
    raw_state: str
    direction: int
    observed: object
    quality: object
    issues: tuple[str, ...]
    evidence_id: str | None
    config_fingerprint: str

    def to_dict(self):
        return dict(context_id=self.context_id,symbol=self.symbol,session_id=self.session_id,
                    as_of=self.as_of.isoformat(),bar_end=self.bar_end.isoformat(),available_at=self.available_at.isoformat(),
                    state=self.state,raw_state=self.raw_state,direction=self.direction,
                    observed=dict(self.observed),quality=dict(self.quality),issues=list(self.issues),
                    evidence_id=self.evidence_id,config_fingerprint=self.config_fingerprint)

    @property
    def inferred(self):
        return MappingProxyType({"state":self.state,"raw_state":self.raw_state,"direction":self.direction})


@dataclass(frozen=True)
class _History:
    session: Session
    available_at: datetime
    slots: tuple[tuple[float, float], ...]


class ContextBook:
    def __init__(self,config):
        if not isinstance(config,ContextConfig): raise ValueError("ContextConfig required")
        self.config=config
        self.symbol=None;self.session=None;self.last_now=None
        self._bars=[];self._slots=[];self._history=[];self._baseline=[]
        self._closes=deque(maxlen=config.efficiency_bars+1)
        self._complete=True;self._high=None;self._low=None;self._volume=0.0
        self._or_high=None;self._or_low=None;self._previous_close=None;self._previous_atr=None
        self._stable="TRANSITION";self._pending=None;self._pending_count=0
        self.last_snapshot=None
        self.observation_only_or_breakouts=0

    @property
    def config_fingerprint(self): return _hash({"version":VERSION,"config":_json(self.config)})

    def _clone(self):
        c=copy(self)
        for key in ("_bars","_slots","_history","_baseline"): setattr(c,key,list(getattr(self,key)))
        c._closes=deque(self._closes,maxlen=self._closes.maxlen)
        return c

    def update(self,bar,session,now,gates=None,features=None):
        if not isinstance(bar,Bar) or not isinstance(session,Session): raise ValueError("Bar/Session required")
        now=_dt(now,"now")
        if gates is not None and not isinstance(gates,ContextGates): raise ValueError("ContextGates required")
        if self.last_now is not None and now<self.last_now: raise ValueError("backward context clock")
        if bar.available_at>now or bar.session_id!=session.id: raise ValueError("unavailable or wrong-session bar")
        if self.symbol is not None and bar.symbol!=self.symbol: raise ValueError("context symbol changed")
        if (bar.end-bar.start).total_seconds()!=300 or not session.open<=bar.start<bar.end<=session.close:
            raise ValueError("invalid context bar/session")
        duration=(session.close-session.open).total_seconds()
        if duration%300 or not 0<duration<=86400 or (bar.start-session.open).total_seconds()%300:
            raise ValueError("invalid context grid")
        new=self.session is None or self.session.id!=session.id
        if not new and self.session!=session: raise ValueError("context calendar revision")
        for old in self._bars:
            if old.end==bar.end or old.start==bar.start:
                if old!=bar or session!=self.session: raise ValueError("conflicting context duplicate")
                return self.last_snapshot
        if self._bars and bar.start<self._bars[-1].end: raise ValueError("out-of-order context")
        if new and (bar.start!=session.open or self.session and session.open<self.session.close):
            raise ValueError("invalid new context session")
        if features is not None:
            if not isinstance(features,Features) or features.symbol!=bar.symbol or features.bar_end!=bar.end or features.available_at!=bar.available_at or features.close!=bar.close:
                raise ValueError("feature/context provenance mismatch")
            for name in ("atr14","slow","dfast"):_number(getattr(features,name),name)
            if features.atr14<0 or len(features.fast_slope_signs)!=6 or any(type(x)is not int or x not in (-1,0,1) for x in features.fast_slope_signs):
                raise ValueError("invalid context feature values")
        c=self._clone()
        result=c._advance(bar,session,now,gates,features,new)
        self.__dict__.update(c.__dict__)
        return result

    def _advance(self,bar,session,now,gates,f,new):
        gap=bool(self._bars and not new and bar.start!=self._bars[-1].end)
        if new:
            chained=bool(self.session and session.previous_id==self.session.id and self._bars and self._bars[-1].end==self.session.close)
            if self.session and self._complete and self._bars[-1].end==self.session.close:
                self._history.append(_History(self.session,self._bars[-1].available_at,tuple(self._slots)))
                self._history=self._history[-self.config.history_limit:]
            if self.session and not chained:
                self._previous_atr=None;self._previous_close=None
            self._baseline=[h for h in self._history if h.session.close-h.session.open==session.close-session.open and h.available_at<=session.open][-self.config.baseline_sessions:]
            self.session=session;self._bars=[];self._slots=[];self._closes.clear();self._complete=True
            self._high=self._low=None;self._volume=0.0;self._or_high=self._or_low=None
            self._stable="TRANSITION";self._pending=None;self._pending_count=0
        if gap:
            self._complete=False;self._closes.clear();self._or_high=self._or_low=None
            self._previous_atr=None;self._previous_close=None
            self._stable="TRANSITION";self._pending=None;self._pending_count=0
        tr=bar.high-bar.low if self._previous_close is None else max(bar.high-bar.low,abs(bar.high-self._previous_close),abs(bar.low-self._previous_close))
        shock_ratio=tr/self._previous_atr if self._previous_atr is not None and self._previous_atr>0 else None
        self._bars.append(bar);self._closes.append(bar.close)
        self._high=bar.high if self._high is None else max(self._high,bar.high)
        self._low=bar.low if self._low is None else min(self._low,bar.low)
        self._volume+=bar.volume
        if not math.isfinite(self._volume): raise ValueError("context volume overflow")
        self._slots.append((self._high-self._low,self._volume))
        slot=int((bar.end-session.open).total_seconds()/300)
        baseline_ready=len(self._baseline)==self.config.baseline_sessions
        range_ratio=volume_ratio=None
        if baseline_ready and self._complete:
            ranges=[h.slots[slot-1][0] for h in self._baseline]
            volumes=[h.slots[slot-1][1] for h in self._baseline]
            r,v=median(ranges),median(volumes)
            range_ratio=(self._high-self._low)/r if r>0 else None
            volume_ratio=self._volume/v if v>0 else None
        efficiency=None;direction=0
        if len(self._closes)==self._closes.maxlen:
            closes=list(self._closes);move=closes[-1]-closes[0]
            distance=math.fsum(abs(b-a) for a,b in zip(closes,closes[1:]))
            efficiency=abs(move)/distance if distance>0 else 0.0
            direction=1 if move>1e-9 else -1 if move < -1e-9 else 0
        if self._complete and slot==self.config.opening_range_bars:
            self._or_high=max(b.high for b in self._bars);self._or_low=min(b.low for b in self._bars)
        or_break=0
        if self._or_high is not None and slot>self.config.opening_range_bars:
            or_break=1 if bar.close>self._or_high else -1 if bar.close<self._or_low else 0
            if or_break:self.observation_only_or_breakouts+=1
        slow_atr=abs(f.slow)/f.atr14 if f is not None and f.atr14>0 else None
        flips=sum(a*b<0 for a,b in zip(f.fast_slope_signs,f.fast_slope_signs[1:])) if f is not None else None
        issues=[]
        if gates is None:issues.append("GATES_MISSING")
        elif gates.session_id!=session.id or not gates.known_at<=now<gates.valid_until:
            issues.append("GATES_INVALID_SESSION_OR_TIME")
        else:
            for key in ("calendar_verified","event_coverage_known","events_clear","feed_verified","sequence_complete"):
                if not getattr(gates,key):issues.append(key.upper())
        if (now-bar.available_at).total_seconds()>=self.config.max_bar_delay_seconds or (bar.available_at-bar.end).total_seconds()>=self.config.max_bar_delay_seconds:
            issues.append("BAR_STALE")
        if issues:raw="DATA_BLOCK"
        elif shock_ratio is not None and shock_ratio>=self.config.shock_tr_atr:raw="SHOCK_PAUSE"
        elif range_ratio is not None and range_ratio<=self.config.compression_range_ratio and efficiency is not None and efficiency<=self.config.rotation_efficiency:raw="COMPRESSION"
        elif efficiency is not None and efficiency>=self.config.directional_efficiency and slow_atr is not None and slow_atr>self.config.weak_slow_atr:raw="DIRECTIONAL"
        elif efficiency is not None and efficiency<=self.config.rotation_efficiency and slow_atr is not None and slow_atr<=self.config.weak_slow_atr and flips is not None and flips>=2:raw="ROTATION"
        else:raw="TRANSITION"
        if raw in ("DATA_BLOCK","SHOCK_PAUSE"):
            state=raw;self._stable="TRANSITION";self._pending=None;self._pending_count=0
        else:
            if raw==self._stable:self._pending=None;self._pending_count=0
            else:
                self._pending_count=self._pending_count+1 if self._pending==raw else 1
                self._pending=raw
                if self._pending_count>=self.config.hysteresis_bars:
                    self._stable=raw;self._pending=None;self._pending_count=0
            state=self._stable
        observed=dict(efficiency_ratio=efficiency,slow_atr=slow_atr,fast_slope_flips=flips,
                      true_range=tr,previous_atr14=self._previous_atr,shock_tr_atr=shock_ratio,
                      cumulative_range=self._high-self._low,cumulative_volume=self._volume,
                      range_ratio=range_ratio,cumulative_volume_ratio=volume_ratio,
                      opening_range_high=self._or_high,opening_range_low=self._or_low,
                      opening_range_breakout_direction=or_break,session_slot=slot)
        if any(isinstance(x,float) and not math.isfinite(x) for x in observed.values()):raise ValueError("context derived nonfinite")
        quality=dict(baseline_count=len(self._baseline),baseline_ready=baseline_ready,
                     session_complete_so_far=self._complete,features_ready=f is not None,
                     required_gates_pass=not issues,opening_range_ready=self._or_high is not None,
                     rank_is_probability=False,breakout_is_observation_only=True)
        payload=dict(symbol=bar.symbol,session_id=session.id,as_of=now.isoformat(),bar_end=bar.end.isoformat(),
                     available_at=bar.available_at.isoformat(),state=state,raw_state=raw,direction=direction,
                     observed=observed,quality=quality,issues=issues,evidence_id=gates.evidence_id if gates else None,
                     config_fingerprint=self.config_fingerprint)
        snapshot=ContextSnapshot(_hash(payload),bar.symbol,session.id,now,bar.end,bar.available_at,state,raw,direction,
                                 MappingProxyType(observed),MappingProxyType(quality),tuple(issues),payload["evidence_id"],self.config_fingerprint)
        self.last_snapshot=snapshot;self.last_now=now;self.symbol=bar.symbol
        self._previous_close=bar.close;self._previous_atr=float(f.atr14) if f is not None else None
        return snapshot

    def snapshot(self):
        state=dict(symbol=self.symbol,session=_json(self.session),last_now=_json(self.last_now),
                   bars=_json(self._bars),slots=_json(self._slots),history=_json(self._history),baseline=_json(self._baseline),
                   closes=list(self._closes),complete=self._complete,high=self._high,low=self._low,volume=self._volume,
                   or_high=self._or_high,or_low=self._or_low,previous_close=self._previous_close,previous_atr=self._previous_atr,
                   stable=self._stable,pending=self._pending,pending_count=self._pending_count,
                   last_snapshot=self.last_snapshot.to_dict() if self.last_snapshot else None,
                   observation_only_or_breakouts=self.observation_only_or_breakouts)
        return dict(version=VERSION,config=_json(self.config),config_fingerprint=self.config_fingerprint,state=state,state_sha256=_hash(state))

    dump_state=snapshot

    @classmethod
    def from_snapshot(cls,value):
        try:
            if not isinstance(value,dict) or set(value)!={"version","config","config_fingerprint","state","state_sha256"} or value["version"]!=VERSION or len(json.dumps(value,allow_nan=False))>3_000_000:
                raise ValueError("invalid context snapshot envelope")
            obj=cls(ContextConfig(**value["config"]));s=value["state"]
            if value["config_fingerprint"]!=obj.config_fingerprint or set(s)!=set(obj.snapshot()["state"]) or _hash(s)!=value["state_sha256"]:
                raise ValueError("context snapshot hash/config mismatch")
            obj._restore(s)
            return obj
        except (KeyError,TypeError,OverflowError,AttributeError) as exc:raise ValueError("malformed context snapshot") from exc

    def load_state(self,value):
        c=self.from_snapshot(value)
        if c.config_fingerprint!=self.config_fingerprint:raise ValueError("context config changed")
        self.__dict__.update(c.__dict__)

    def _restore(self,s):
        self.symbol=s["symbol"];self.session=Session(**s["session"]) if s["session"] else None
        self.last_now=_dt(s["last_now"],"last_now") if s["last_now"] else None
        if len(s["bars"])>288:raise ValueError("unbounded context bars")
        self._bars=[Bar(**x) for x in s["bars"]]
        self._slots=[tuple(_number(v,"slot",minimum=0) for v in x) for x in s["slots"]]
        if len(self._slots)!=len(self._bars) or any(len(x)!=2 for x in self._slots):raise ValueError("context slots mismatch")
        def histories(items):
            if len(items)>self.config.history_limit:raise ValueError("unbounded history")
            out=[]
            for item in items:
                ses=Session(**item["session"]);at=_dt(item["available_at"],"history availability")
                slots=tuple(tuple(_number(v,"historical slot",minimum=0) for v in x) for x in item["slots"])
                if len(slots)!=(ses.close-ses.open).total_seconds()/300 or len(slots)>288 or any(len(x)!=2 for x in slots) or at<ses.close or self.session is None or at>self.session.open:
                    raise ValueError("historical completeness/availability mismatch")
                if any(a[0]>b[0] or a[1]>b[1] for a,b in zip(slots,slots[1:])):raise ValueError("nonmonotonic history")
                out.append(_History(ses,at,slots))
            if any(a.session.close>b.session.open for a,b in zip(out,out[1:])):raise ValueError("nonchronological history")
            return out
        self._history=histories(s["history"]);self._baseline=histories(s["baseline"])
        if len(self._baseline)>self.config.baseline_sessions or any(x not in self._history for x in self._baseline):raise ValueError("invalid frozen baseline")
        if type(s["complete"])is not bool:raise ValueError("invalid completeness")
        self._complete=s["complete"]
        self._closes=deque((_number(x,"close",strictly_positive=True) for x in s["closes"]),maxlen=self.config.efficiency_bars+1)
        if len(s["closes"])>self._closes.maxlen:raise ValueError("unbounded close window")
        for name,key in (("_high","high"),("_low","low"),("_volume","volume"),("_or_high","or_high"),("_or_low","or_low"),("_previous_close","previous_close"),("_previous_atr","previous_atr")):
            setattr(self,name,None if s[key] is None else _number(s[key],key,minimum=0))
        self._stable=s["stable"];self._pending=s["pending"];self._pending_count=_integer(s["pending_count"],"pending_count")
        if self._stable not in STATES[2:] or self._pending not in (*STATES[2:],None) or self._pending_count>=self.config.hysteresis_bars or (self._pending is None)!=(self._pending_count==0):raise ValueError("invalid hysteresis state")
        self.observation_only_or_breakouts=_integer(s["observation_only_or_breakouts"],"breakout count")
        if bool(self._bars)!=bool(self.session) or bool(self._bars)!=bool(self.last_now):raise ValueError("empty context mismatch")
        if self._bars:
            if any(b.symbol!=self.symbol or b.session_id!=self.session.id or b.available_at>self.last_now or not self.session.open<=b.start<b.end<=self.session.close or (b.end-b.start).total_seconds()!=300 for b in self._bars):raise ValueError("context retained provenance mismatch")
            if any(a.end>b.start for a,b in zip(self._bars,self._bars[1:])):raise ValueError("context retained order")
            if self._complete and (self._bars[0].start!=self.session.open or any(a.end!=b.start for a,b in zip(self._bars,self._bars[1:]))):raise ValueError("false complete context")
            if self._previous_close!=self._bars[-1].close or self._high!=max(x.high for x in self._bars) or self._low!=min(x.low for x in self._bars):raise ValueError("context extrema mismatch")
            volume=0.0;high=low=None;computed=[]
            for b in self._bars:
                volume+=b.volume;high=b.high if high is None else max(high,b.high);low=b.low if low is None else min(low,b.low);computed.append((high-low,volume))
            if computed!=self._slots or volume!=self._volume:raise ValueError("context cumulative mismatch")
            if list(self._closes)!=[b.close for b in self._bars[-len(self._closes):]]:raise ValueError("context close window mismatch")
        if s["last_snapshot"] is not None:
            p=dict(s["last_snapshot"]);identity=p.pop("context_id")
            if _hash(p)!=identity or p["config_fingerprint"]!=self.config_fingerprint:raise ValueError("context record identity mismatch")
            for key in ("as_of","bar_end","available_at"):p[key]=_dt(p[key],key)
            if not self._bars or p["as_of"]!=self.last_now or p["bar_end"]!=self._bars[-1].end or p["available_at"]!=self._bars[-1].available_at or p["symbol"]!=self.symbol or p["session_id"]!=self.session.id or p["state"] not in STATES or p["raw_state"] not in STATES:raise ValueError("context record provenance")
            p["observed"]=MappingProxyType(p["observed"]);p["quality"]=MappingProxyType(p["quality"]);p["issues"]=tuple(p["issues"])
            self.last_snapshot=ContextSnapshot(context_id=identity,**p)
        elif self._bars:raise ValueError("missing context record")

