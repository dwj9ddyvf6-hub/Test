"""Independent canonical profile lanes with deterministic context ordering.

Rank is utility only. Mandatory execution admission and account allocation follow.
"""
from collections import deque
from copy import copy, deepcopy
from dataclasses import dataclass, replace
import json

from .raschke_core import _hash, _dt
from .raschke_engine import PolicyEngine, PolicyConfig, Intent, _json
from .awareness import ContextBook, ContextConfig

VERSION="rre-router-2"


@dataclass(frozen=True)
class RouterConfig:
    tick_size: float
    series_id: str
    calendar_version: str
    cost_reserve_price: float=0.0

    def __post_init__(self):
        p=PolicyConfig(self.tick_size,self.series_id,self.calendar_version,"RRE1",self.cost_reserve_price)
        object.__setattr__(self,"tick_size",p.tick_size);object.__setattr__(self,"cost_reserve_price",p.cost_reserve_price)


@dataclass(frozen=True)
class RankedIntent:
    intent: Intent
    rank: tuple
    context_id: str
    context_state: str
    reasons: tuple[str,...]

    def to_dict(self):
        return dict(intent=self.intent.to_dict(),rank=list(self.rank),context_id=self.context_id,
                    context_state=self.context_state,reasons=list(self.reasons),rank_is_probability=False)


def candidate_sort_key(candidate):
    if isinstance(candidate,RankedIntent):return candidate.rank
    raise ValueError("RankedIntent required; admission must not infer a context rank")


def expression_intent(intent,expression):
    if not isinstance(intent,Intent):raise ValueError("Intent required")
    if expression=="linear" and intent.variant in ("RRE1","RRE2"):return intent
    if expression in ("options","SPY_0DTE_LONG") and intent.variant in ("RRE2","RRE3") and intent.symbol=="SPY":
        return replace(intent,variant="RRE3")
    raise ValueError("source is not expressible in requested profile")


class AdaptiveRouter:
    def __init__(self,config,context_config=None):
        if not isinstance(config,RouterConfig):raise ValueError("RouterConfig required")
        context_config=context_config or ContextConfig(config.series_id,config.calendar_version)
        if context_config.series_id!=config.series_id or context_config.calendar_version!=config.calendar_version:raise ValueError("router context lineage mismatch")
        self.config=config
        self.lanes={v:PolicyEngine(PolicyConfig(config.tick_size,config.series_id,config.calendar_version,v,config.cost_reserve_price)) for v in ("RRE1","RRE2")}
        self.context=ContextBook(context_config)
        self._decisions=deque(maxlen=512)
        self.last_candidates=()
        self.counters={"bars":0,"canonical_intents":0,"routed":0,"data_vetoes":0,"shock_vetoes":0,"opposition_waits":0,"rotation_precedence_observations":0}

    @property
    def last_context(self):return self.context.last_snapshot

    @property
    def config_fingerprint(self):return _hash({"version":VERSION,"config":_json(self.config),"context":self.context.config_fingerprint})

    def _clone(self):
        c=copy(self);c.lanes={k:v._clone() for k,v in self.lanes.items()};c.context=self.context._clone()
        c._decisions=deque(self._decisions,maxlen=512);c.counters=dict(self.counters)
        return c

    def _record(self,code,at,**details):
        self._decisions.append(dict(code=code,at=at.isoformat(),details=_json(details)))

    def drain_decisions(self):
        out=tuple(deepcopy(list(self._decisions)));self._decisions.clear();return out

    @property
    def decisions(self):return tuple(deepcopy(list(self._decisions)))

    def update(self,bar,session,reference,now,gates=None):
        now=_dt(now,"now")
        c=self._clone()
        old_end=c.lanes["RRE1"].core._bars[-1].end if c.lanes["RRE1"].core._bars else None
        cross_was_active=c.lanes["RRE2"]._cross is not None
        intents=[]
        for lane in c.lanes.values():
            intents.extend(lane.update(bar,session,reference,now))
        new_end=c.lanes["RRE1"].core._bars[-1].end if c.lanes["RRE1"].core._bars else None
        if new_end==old_end:return ()
        f=c.lanes["RRE2"]._previous
        context=c.context.update(bar,session,now,gates,f)
        for name,lane in c.lanes.items():
            for row in lane.drain_decisions():
                c._record("CANONICAL_"+row["code"],now,lane=name,source_decision=row)
        c.counters["bars"]+=1;c.counters["canonical_intents"]+=len(intents)
        if cross_was_active or c.lanes["RRE2"]._cross is not None:
            obs=context.observed
            rotation_shape=(obs["slow_atr"] is not None and obs["slow_atr"]<=.15 and obs["fast_slope_flips"] is not None and obs["fast_slope_flips"]>=2)
            if rotation_shape:
                c.counters["rotation_precedence_observations"]+=1
                c._record("CANONICAL_ROTATION_PRECEDENCE",now,observation_only=True,cross_was_active=cross_was_active)
        ranked=c.rank_intents(intents,context)
        c.last_candidates=tuple(ranked)
        if context.state in ("DATA_BLOCK","SHOCK_PAUSE"):
            key="data_vetoes" if context.state=="DATA_BLOCK" else "shock_vetoes"
            c.counters[key]+=len(ranked)
            for item in ranked:c._record(context.state,now,source_id=item.intent.source_id,context_id=context.context_id,issues=context.issues)
            routed=()
        else:
            routed=c.resolve_opposition(ranked)
            if ranked and not routed:
                c.counters["opposition_waits"]+=1;c._record("WAIT_EQUAL_OPPOSING_CANDIDATES",now,source_ids=[x.intent.source_id for x in ranked])
            for item in routed:c._record("ROUTED",now,source_id=item.intent.source_id,rank=item.rank,context_id=item.context_id)
        c.counters["routed"]+=len(routed)
        self.__dict__.update(c.__dict__)
        return tuple(routed)

    @staticmethod
    def rank_intents(intents,context):
        """Fixed tuple: context support, reference gross RR, then stable identity.

        Reference RR is gross here because executable costs belong to admission;
        it orders candidates only and is never described as option RR/probability.
        """
        out=[]
        for i in intents:
            support=0;reasons=[]
            if context.state=="DIRECTIONAL" and i.setup in ("PF3_PULSE","FIRST_CROSS") and i.direction==context.direction:
                support=1;reasons.append("DIRECTIONAL_COMPATIBLE")
            elif context.state=="ROTATION" and i.setup=="FAILED_BREAK":
                support=1;reasons.append("ROTATION_COMPATIBLE")
            risk=i.direction*(i.entry_reference-i.stop);reward=i.direction*(i.target-i.entry_reference)
            rr=reward/risk
            rank=(-support,-rr,i.symbol,i.source_id)
            if not reasons:reasons.append("NO_CONTEXT_PREFERENCE")
            out.append(RankedIntent(i,rank,context.context_id,context.state,tuple(reasons)))
        return tuple(sorted(out,key=candidate_sort_key))

    @staticmethod
    def resolve_opposition(ranked):
        ranked=tuple(sorted(ranked,key=candidate_sort_key))
        if not ranked:return ()
        best=ranked[0];key=best.rank[:2]
        leaders=[x for x in ranked if x.rank[:2]==key]
        if len({x.intent.direction for x in leaders})>1:return ()
        # Eligible same-direction alternatives remain available if one cannot be
        # admitted. Opposite lower-ranked theses wait for a genuinely new event.
        return tuple(x for x in ranked if x.intent.direction==best.intent.direction)

    def snapshot(self):
        state=dict(lanes={k:v.snapshot() for k,v in self.lanes.items()},context=self.context.snapshot(),
                   decisions=deepcopy(list(self._decisions)),counters=dict(self.counters),
                   last_candidates=[x.to_dict() for x in self.last_candidates])
        return dict(version=VERSION,config=_json(self.config),config_fingerprint=self.config_fingerprint,state=state,state_sha256=_hash(state))

    dump_state=snapshot

    @classmethod
    def from_snapshot(cls,value):
        try:
            if not isinstance(value,dict) or set(value)!={"version","config","config_fingerprint","state","state_sha256"} or value["version"]!=VERSION or len(json.dumps(value,allow_nan=False))>4_000_000:raise ValueError("invalid router snapshot")
            s=value["state"]
            if set(s)!={"lanes","context","decisions","counters","last_candidates"} or _hash(s)!=value["state_sha256"] or set(s["lanes"])!={"RRE1","RRE2"}:raise ValueError("router state mismatch")
            context=ContextBook.from_snapshot(s["context"])
            obj=cls(RouterConfig(**value["config"]),context.config)
            if value["config_fingerprint"]!=obj.config_fingerprint:raise ValueError("router config mismatch")
            obj.context=context;obj.lanes={k:PolicyEngine.from_snapshot(v) for k,v in s["lanes"].items()}
            for k,lane in obj.lanes.items():
                expected=PolicyConfig(obj.config.tick_size,obj.config.series_id,obj.config.calendar_version,k,obj.config.cost_reserve_price)
                if lane.config!=expected or lane.core.last_now!=context.last_now or lane.core.symbol!=context.symbol or lane._session_id!=(context.session.id if context.session else None):raise ValueError("router lane/context mismatch")
            if obj.lanes["RRE1"].core.snapshot()!=obj.lanes["RRE2"].core.snapshot():raise ValueError("router feature histories diverged")
            if not isinstance(s["decisions"],list) or len(s["decisions"])>512:raise ValueError("unbounded router decisions")
            for row in s["decisions"]:
                if set(row)!={"code","at","details"} or not isinstance(row["details"],dict) or context.last_now is None or _dt(row["at"],"decision")>context.last_now:raise ValueError("invalid router decision")
            obj._decisions=deque(deepcopy(s["decisions"]),maxlen=512)
            if set(s["counters"])!=set(obj.counters) or any(type(x)is not int or x<0 for x in s["counters"].values()):raise ValueError("invalid router counters")
            obj.counters=dict(s["counters"])
            if not isinstance(s["last_candidates"],list) or len(s["last_candidates"])>2:raise ValueError("invalid candidate count")
            candidates=[]
            for row in s["last_candidates"]:
                if set(row)!={"intent","rank","context_id","context_state","reasons","rank_is_probability"} or row["rank_is_probability"] is not False:raise ValueError("invalid ranked record")
                intent=Intent(**row["intent"])
                if context.last_snapshot is None or row["context_id"]!=context.last_snapshot.context_id or intent.available_at!=context.last_now:raise ValueError("candidate context mismatch")
                candidates.append(RankedIntent(intent,tuple(row["rank"]),row["context_id"],row["context_state"],tuple(row["reasons"])))
            if candidates and tuple(candidates)!=obj.rank_intents([x.intent for x in candidates],context.last_snapshot):raise ValueError("rank changed")
            obj.last_candidates=tuple(candidates)
            return obj
        except (KeyError,TypeError,OverflowError,AttributeError) as exc:raise ValueError("malformed router snapshot") from exc

    def load_state(self,value):
        c=self.from_snapshot(value)
        if c.config_fingerprint!=self.config_fingerprint:raise ValueError("router configuration changed")
        self.__dict__.update(c.__dict__)


Router=AdaptiveRouter
