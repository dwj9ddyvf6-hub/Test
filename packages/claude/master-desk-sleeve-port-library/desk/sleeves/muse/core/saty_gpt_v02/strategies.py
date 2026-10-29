"""Original, versioned mechanical hypotheses derived from Saty's public vocabulary.

This is a causal signal generator, not a reproduction of discretionary trading or
an execution service. Every numeric setup/risk threshold here is a research
hypothesis. Indicator values and confirmed structure are supplied by Context.
One instance owns one symbol/execution clock and one active candidate. Opposite
directions use symmetric mechanics; that symmetry is not a performance claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from typing import Any
import json

from core.saty_gpt_v02.reference import MULTIPLIERS
from .models import Context, Pivot, Signal, aware, jsonable, stable_id

SETUPS = (
    'vomy_early13', 'vomy_confirmed48', 'vomy_pro21', 'golden_gate',
    'compression_retest', 'compression_breakout', 'pivot_pullback',
    'atr_retest', 'divergence_mean_reversion', 'phase_mean_reversion',
)
SOURCES = {
    'vomy_early13': 'https://x.com/satymahajan/status/1648369109774614532',
    'vomy_confirmed48': 'https://x.com/satymahajan/status/1648369109774614532',
    'vomy_pro21': 'https://bsky.app/profile/satymahajan.bsky.social/post/3lffzdxtwo22c',
    'golden_gate': 'https://x.com/satymahajan/status/1683915837822885893',
    'compression_retest': 'https://bsky.app/profile/satymahajan.bsky.social/post/3lf5s72nnn22h',
    'compression_breakout': 'https://bsky.app/profile/satymahajan.bsky.social/post/3lf5s72nnn22h',
    'pivot_pullback': 'https://www.satyland.com/pivotribbon',
    'atr_retest': 'https://www.satyland.com/atrlevels',
    'divergence_mean_reversion': 'https://www.satyland.com/phaseoscillator',
    'phase_mean_reversion': 'https://x.com/satymahajan/status/1686515505882882049',
}
METHOD_VERSION = 'mechanical-hypothesis-1'


@dataclass(frozen=True)
class StrategyConfig:
    enabled: tuple[str, ...] = SETUPS
    warmup_bars: int = 1000
    minimum_trend_bars: int = 3
    transition_memory_bars: int = 12
    setup_expiry_bars: int = 6
    minimum_compression_bars: int = 3
    maximum_compression_bars: int = 30
    compression_stop: str = 'boundary'  # midpoint is a separate dated hypothesis
    tolerance_atr: float = .10
    stop_buffer_atr: float = .10
    max_chase_atr: float = .40
    minimum_net_reward_risk: float = 1.5
    # Price-unit estimate including round-trip costs. Actual fills must recheck.
    estimated_round_trip_cost: float = .02
    minimum_phase_divergence: float = 5.
    minimum_price_divergence_atr: float = .05
    maximum_pivot_separation_bars: int = 50
    maximum_pivot_age_bars: int = 50
    phase_exit_threshold: float = 61.8
    countertrend_risk_multiplier: float = .5
    context_timeframe: str | None = None
    require_context_alignment: bool = False
    max_context_age_seconds: float = 86400.
    max_data_lag_seconds: float = 300.

    def __post_init__(self) -> None:
        if not self.enabled or len(set(self.enabled)) != len(self.enabled) or any(x not in SETUPS for x in self.enabled):
            raise ValueError('unknown, duplicate or empty setup selection')
        if min(self.warmup_bars, self.minimum_trend_bars, self.transition_memory_bars,
               self.setup_expiry_bars, self.minimum_compression_bars,
               self.maximum_pivot_separation_bars, self.maximum_pivot_age_bars) < 1:
            raise ValueError('positive bar counts required')
        if self.maximum_compression_bars < self.minimum_compression_bars:
            raise ValueError('invalid compression lengths')
        if self.compression_stop not in ('boundary', 'midpoint'):
            raise ValueError('unknown compression stop hypothesis')
        values = (self.tolerance_atr, self.stop_buffer_atr, self.max_chase_atr,
                  self.minimum_net_reward_risk, self.estimated_round_trip_cost,
                  self.minimum_phase_divergence, self.minimum_price_divergence_atr,
                  self.max_context_age_seconds, self.max_data_lag_seconds)
        if any(not isfinite(x) or x < 0 for x in values) or self.minimum_net_reward_risk <= 0:
            raise ValueError('invalid strategy parameters')
        if self.phase_exit_threshold not in (61.8, 100.) or not 0 < self.countertrend_risk_multiplier <= 1:
            raise ValueError('invalid phase/risk configuration')
        if self.require_context_alignment and not self.context_timeframe:
            raise ValueError('alignment requires an explicit context timeframe')

    @property
    def fingerprint(self) -> str:
        return stable_id(METHOD_VERSION, json.dumps(asdict(self), sort_keys=True))


class StrategyEngine:
    """Closed-observation router; update returns intents, never hypothetical fills.

    Decisions record WAIT/ARM/CANCEL/REJECT/SIGNAL and exactly one ROUTE for every
    accepted new execution observation. Data blockers cancel entry candidates;
    protective exits belong to the independent portfolio/execution controller.
    """
    def __init__(self, config: StrategyConfig = StrategyConfig()):
        self.config = config
        self.decisions: list[dict[str, Any]] = []
        self._state: dict[str, Any] = {
            'identity': None, 'last': None, 'index': 0, 'arm': None,
            'compressed': [], 'box': None, 'trend_direction': 0,
            'trend_run': 0, 'trend_memory': 0, 'trend_memory_index': 0,
            'used_pivots': [], 'seen_signals': [], 'reference_key': None,
        }

    def dump_state(self) -> dict[str, Any]:
        return json.loads(json.dumps({'version': METHOD_VERSION,
            'config': self.config.fingerprint, 'state': self._state,
            'decisions': self.decisions}))

    def load_state(self, payload: dict[str, Any]) -> None:
        if payload.get('version') != METHOD_VERSION or payload.get('config') != self.config.fingerprint:
            raise ValueError('strategy checkpoint version/config mismatch')
        data = json.loads(json.dumps(payload))
        if set(data.get('state', {})) != set(self._state) or not isinstance(data.get('decisions'), list):
            raise ValueError('invalid strategy checkpoint schema')
        self._state = data['state']; self.decisions = data['decisions']

    def _record(self, ctx: Context, event: str, reason: str, **fields: Any) -> None:
        self.decisions.append({'event': event, 'reason': reason,
            'at': ctx.as_of.isoformat(), 'bar_end': ctx.execution.bar.end.isoformat(),
            'symbol': ctx.execution.symbol, 'timeframe': ctx.execution.timeframe,
            'method_version': METHOD_VERSION, 'config': self.config.fingerprint,
            **jsonable(fields)})

    @staticmethod
    def _reference_key(ctx: Context) -> str:
        r = ctx.reference
        return stable_id(r.horizon, r.period_id, r.period_end, r.close, r.atr)

    @staticmethod
    def _stack(ema: dict[int, float]) -> int:
        if ema[8] > ema[21] > ema[48]: return 1
        if ema[8] < ema[21] < ema[48]: return -1
        return 0

    def _data_error(self, ctx: Context) -> str | None:
        try:
            aware(ctx.as_of); ctx.execution.observation.validate()
            b = ctx.execution.bar; f = ctx.execution.features
            if not b.end <= ctx.execution.available_at <= ctx.as_of:
                return 'execution_not_available'
            if (ctx.as_of - ctx.execution.available_at).total_seconds() > self.config.max_data_lag_seconds:
                return 'stale_execution'
            ctx.reference.validate(ctx.as_of)
            if not ctx.reference.horizon: return 'missing_reference_horizon'
            if ctx.blockers: return 'context_blockers:' + ','.join(ctx.blockers)
            if ctx.execution.count < self.config.warmup_bars: return 'warmup'
            if f.atr is None or f.atr <= 0 or not isfinite(f.atr): return 'invalid_atr'
            if any(n not in f.ema or not isfinite(f.ema[n]) or f.ema[n] <= 0 for n in (8,13,21,48,200)):
                return 'missing_pro_ribbon'
            if f.phase is not None and not isfinite(f.phase): return 'invalid_phase'
            needs_compression=any(x.startswith('compression') for x in self.config.enabled)
            needs_phase=needs_compression or any('mean_reversion' in x for x in self.config.enabled)
            if needs_phase and f.phase is None: return 'missing_phase_observation'
            if needs_compression and not isinstance(f.compression,bool): return 'missing_compression_observation'
            if ctx.session is not None:
                ctx.session.validate()
                if not ctx.session.entry_start <= ctx.as_of < ctx.session.entry_cutoff:
                    return 'outside_entry_window'
                if b.start < ctx.session.open or b.end > ctx.session.close: return 'session_mismatch'
            if self.config.context_timeframe and self.config.context_timeframe not in ctx.frames:
                return 'missing_context_clock'
            for clock, frame in ctx.frames.items():
                frame.observation.validate()
                if clock != frame.timeframe or frame.symbol != ctx.execution.symbol:
                    return 'context_identity_mismatch'
                if frame.bar.end > b.end or frame.available_at > ctx.as_of:
                    return 'future_context'
                if frame.observation.session_policy != ctx.execution.observation.session_policy:
                    return 'session_policy_mismatch'
            if self.config.context_timeframe:
                frame = ctx.frames[self.config.context_timeframe]
                if (ctx.as_of - frame.bar.end).total_seconds() > self.config.max_context_age_seconds:
                    return 'stale_context_clock'
                if any(n not in frame.features.ema for n in (8,21,48)):
                    return 'context_ribbon_missing'
        except (TypeError, ValueError, OverflowError):
            return 'invalid_context_contract'
        return None

    def _context_direction(self, ctx: Context) -> int | None:
        if not self.config.context_timeframe: return None
        return self._stack(ctx.frames[self.config.context_timeframe].features.ema)

    def _pivots(self, ctx: Context) -> list[Pivot]:
        # Never treat a retrospectively plotted pivot as known at its bar time.
        out = []
        for p in ctx.pivots:
            try:
                aware(p.bar_end); aware(p.confirmed_at)
                if (p.kind in ('high','low') and p.timeframe == ctx.execution.timeframe
                    and p.bar_end <= ctx.execution.bar.end
                    and p.bar_end <= p.confirmed_at <= ctx.as_of
                    and isfinite(p.price) and p.price > 0
                    and (p.phase is None or isfinite(p.phase))): out.append(p)
            except (TypeError, ValueError): pass
        return sorted(out, key=lambda p: (p.bar_end, p.confirmed_at))

    def _levels(self, ctx: Context) -> list[float]:
        r = ctx.reference
        out = [r.price(d*m) for d in (-1,1) for m in MULTIPLIERS if r.price(d*m)>0]
        for level in ctx.levels:
            try:
                aware(level.known_at)
                if level.known_at <= ctx.as_of and isfinite(level.price) and level.price > 0:
                    # Use the near boundary of a zone in _targets, not its far edge.
                    out.extend(x for x in (level.lower,level.price,level.upper) if x is not None and isfinite(x) and x>0)
            except (TypeError, ValueError): pass
        return sorted(set(out))

    def _arm(self, ctx: Context, setup: str, direction: int, **fields: Any) -> None:
        self._state['arm'] = {'setup': setup, 'direction': direction,
            'index': self._state['index'], 'reference_key': self._reference_key(ctx),
            'reference_horizon': ctx.reference.horizon, 'period_id': ctx.reference.period_id,
            'reference_close': ctx.reference.close, 'reference_atr': ctx.reference.atr,
            **jsonable(fields)}
        self._record(ctx, 'ARM', 'observed_arming_event', setup=setup, direction=direction, details=fields)

    def _cancel(self, ctx: Context, reason: str) -> None:
        if self._state['arm']:
            self._record(ctx, 'CANCEL', reason, setup=self._state['arm']['setup'])
            self._state['arm'] = None

    def _signal(self, ctx: Context, setup: str, d: int, stop: float, anchor: float,
                destination: float | None = None, named_targets: tuple[float,...] = (),
                countertrend: bool = False, **metadata: Any) -> list[Signal]:
        f = ctx.execution.features; b = ctx.execution.bar; atr = f.atr
        assert atr is not None
        entry = b.close; reason = None
        if d*(entry-stop) <= 0 or stop <= 0: reason = 'invalid_structural_stop'
        elif abs(entry-anchor) > self.config.max_chase_atr*atr: reason = 'no_chase'
        elif self.config.require_context_alignment and self._context_direction(ctx) != d and not countertrend:
            reason = 'context_direction_conflict'
        ahead = [p for p in self._levels(ctx) if d*(p-entry)>1e-9]
        if destination is not None:
            if d*(destination-entry)<=0: reason = reason or 'destination_already_behind'
            ahead = [p for p in ahead if d*(destination-p)>=0]
            ahead.append(destination)
        if not ahead: reason = reason or 'no_opposing_target'
        targets: tuple[float,...] = ()
        if ahead:
            first = min(ahead, key=lambda p: d*(p-entry))
            targets = tuple(sorted({first, *(p for p in named_targets if d*(p-entry)>0),
                                    *(() if destination is None else (destination,))}, reverse=d<0))
            cost = self.config.estimated_round_trip_cost
            net_reward = d*(first-entry)-cost; net_risk = d*(entry-stop)+cost
            if net_reward <= 0 or net_reward < self.config.minimum_net_reward_risk*net_risk:
                reason = reason or 'insufficient_net_room_to_first_obstacle'
        if reason:
            self._record(ctx, 'REJECT', reason, setup=setup, direction=d,
                         reference_entry=entry, stop=stop, targets=targets)
            self._state['arm'] = None
            return []
        period = b.end-b.start
        expires = ctx.as_of + period*self.config.setup_expiry_bars
        if ctx.session: expires = min(expires, ctx.session.entry_cutoff)
        if expires <= ctx.as_of:
            self._record(ctx, 'REJECT', 'no_execution_time', setup=setup); return []
        sid = stable_id(METHOD_VERSION,self.config.fingerprint,ctx.execution.symbol,
            ctx.execution.timeframe,setup,d,b.end,ctx.reference.horizon,ctx.reference.period_id)
        if sid in self._state['seen_signals']: return []
        arm = self._state['arm'] or {}
        signal = Signal(sid,ctx.execution.symbol,ctx.execution.timeframe,setup,d,b.end,
            ctx.as_of,expires,entry,stop,targets,atr,anchor,ctx.reference.horizon,
            self.config.countertrend_risk_multiplier if countertrend else 1.,
            {'method_version':METHOD_VERSION,'evidence_status':'original_mechanical_hypothesis',
             'source_url':SOURCES[setup], 'config':self.config.fingerprint,
             'reference_period_id':ctx.reference.period_id,'reference_close':ctx.reference.close,
             'reference_atr':ctx.reference.atr,'context_direction':self._context_direction(ctx),
             'reference_period_end':ctx.reference.period_end.isoformat(),
             'reference_available_at':ctx.reference.available_at.isoformat(),
             'source_observation_id':ctx.execution.observation.event_id,
             'context_clocks':{k:{'bar_end':v.bar.end.isoformat(),'available_at':v.available_at.isoformat()}
                               for k,v in ctx.frames.items()},
             'execution_clock':ctx.execution.timeframe,'reference_horizon':ctx.reference.horizon,
             'estimated_round_trip_cost':self.config.estimated_round_trip_cost,
             'first_obstacle':targets[0],'armed_index':arm.get('index'),
             'fill_requires_fresh_quote_and_risk_recheck':True,**metadata})
        signal.validate(); self._state['seen_signals'].append(sid)
        self._state['arm'] = None
        self._record(ctx, 'SIGNAL', 'confirmed_and_geometry_admissible', signal=signal)
        return [signal]

    def _route(self, ctx: Context, route: str, reason: str) -> None:
        self._record(ctx, 'ROUTE', reason, route=route)

    def _wait(self, ctx: Context, reason: str) -> list[Signal]:
        self._record(ctx, 'WAIT', reason); return []

    def _active(self, ctx: Context) -> list[Signal]:
        a = self._state['arm']; setup = a['setup']; d = a['direction']
        b = ctx.execution.bar; f = ctx.execution.features; e=f.ema; atr=f.atr
        assert atr is not None
        tol=self.config.tolerance_atr*atr; buf=self.config.stop_buffer_atr*atr
        route = 'EXTENSION_REVERSAL' if 'mean_reversion' in setup else \
                'COMPRESSION' if setup.startswith('compression') else \
                'TREND_TRANSITION' if setup.startswith('vomy') else 'TREND_CONTINUATION'
        self._route(ctx,route,'active_candidate')
        if self._state['index']-a['index'] > self.config.setup_expiry_bars:
            self._cancel(ctx,'candidate_expired'); return self._wait(ctx,'expired')
        if a['reference_key'] != self._reference_key(ctx):
            self._cancel(ctx,'reference_period_changed'); return self._wait(ctx,'reference_changed')
        if setup == 'golden_gate' and d*((b.high if d==1 else b.low)-a['destination'])>=0:
            self._cancel(ctx,'golden_gate_target_touched_before_entry'); return self._wait(ctx,'target_already_touched')
        if 'invalidation' in a and d*(b.close-a['invalidation'])<0:
            self._cancel(ctx,'structural_invalidation'); return self._wait(ctx,'structure_failed')
        if setup in ('vomy_early13','vomy_confirmed48','vomy_pro21'):
            n = {'vomy_early13':13,'vomy_confirmed48':48,'vomy_pro21':21}[setup]
            anchor=e[n]
            touched=b.low<=anchor+tol if d==1 else b.high>=anchor-tol
            rejected=d*(b.close-anchor)>0 and d*(b.close-b.open)>0
            if touched and rejected:
                stop=(b.low if d==1 else b.high)-d*buf
                return self._signal(ctx,setup,d,stop,anchor,ema_variant=n,
                    transition_stage='early_rejection' if n==13 else 'confirmed_retest' if n==48 else 'pro21_rejection')
        elif setup == 'golden_gate':
            if a['stage']=='pullback':
                gate_touch=b.low<=a['anchor']+tol if d==1 else b.high>=a['anchor']-tol
                ribbon_touch=b.low<=e[21]+tol if d==1 else b.high>=e[21]-tol
                if (gate_touch or ribbon_touch) and d*(b.close-e[48])>0:
                    a.update(stage='recovery',trigger=b.high if d==1 else b.low,
                        stop=(b.low if d==1 else b.high)-d*buf,
                        recovery_anchor=a['anchor'] if gate_touch else e[21],
                        invalidation=(b.low if d==1 else b.high)-d*buf)
                    self._record(ctx,'ARM','golden_gate_pullback_observed',setup=setup)
            elif d*(b.close-a['trigger'])>0 and d*(b.close-e[8])>=0:
                return self._signal(ctx,setup,d,a['stop'],a['recovery_anchor'],
                    destination=a['destination'],named_targets=(a['partial'],),
                    gate_opening=a['anchor'],gate_midpoint=a['partial'],gate_completion=a['destination'])
        elif setup in ('compression_retest','atr_retest'):
            anchor=a['anchor']; touched=b.low<=anchor+tol if d==1 else b.high>=anchor-tol
            if d*(b.close-anchor)<-tol:
                self._cancel(ctx,'breakout_edge_lost'); return self._wait(ctx,'failed_retest')
            if touched and d*(b.close-anchor)>0 and self._stack(e)==d:
                stop=(min(anchor,b.low) if d==1 else max(anchor,b.high))-d*buf
                if setup=='compression_retest' and self.config.compression_stop=='midpoint':
                    stop=(a['box_low']+a['box_high'])/2
                return self._signal(ctx,setup,d,stop,anchor,compression_stop=self.config.compression_stop if setup.startswith('compression') else None)
        elif setup=='pivot_pullback':
            if d*(b.close-a['trigger'])>0 and d*(b.close-e[8])>=0 and self._stack(e)==d:
                return self._signal(ctx,setup,d,a['stop'],a['anchor'])
        elif setup in ('divergence_mean_reversion','phase_mean_reversion'):
            if d*(b.close-a['trigger'])>0 and d*(b.close-e[8])>0:
                return self._signal(ctx,setup,d,a['stop'],a['trigger'],
                    destination=e[21],countertrend=True,structure_trigger=a['trigger'],
                    pivot_evidence=a.get('pivot_evidence'),phase_exit_threshold=self.config.phase_exit_threshold)
        return self._wait(ctx,'awaiting_completed_bar_confirmation')

    def _divergence(self, ctx: Context, pivots: list[Pivot]) -> bool:
        if 'divergence_mean_reversion' not in self.config.enabled: return False
        atr=ctx.execution.features.atr; assert atr is not None
        for d,kind in ((1,'low'),(-1,'high')):
            same=[p for p in pivots if p.kind==kind and p.phase is not None]
            if len(same)<2: continue
            p,q=same[-2:]
            if q.bar_end-p.bar_end > (ctx.execution.bar.end-ctx.execution.bar.start)*self.config.maximum_pivot_separation_bars:
                continue
            if ctx.as_of-q.confirmed_at > (ctx.execution.bar.end-ctx.execution.bar.start)*self.config.maximum_pivot_age_bars:
                continue
            key=stable_id(kind,p.bar_end,q.bar_end,q.confirmed_at)
            if key in self._state['used_pivots']: continue
            if d*(p.price-q.price) < self.config.minimum_price_divergence_atr*atr: continue
            if d*(q.phase-p.phase) < self.config.minimum_phase_divergence: continue
            if min(d*p.phase,d*q.phase)>-self.config.phase_exit_threshold: continue
            middle=[x for x in pivots if x.kind!=kind and p.bar_end<x.bar_end<q.bar_end]
            if not middle: continue
            trigger=max(x.price for x in middle) if d==1 else min(x.price for x in middle)
            self._state['used_pivots'].append(key)
            self._arm(ctx,'divergence_mean_reversion',d,trigger=trigger,
                stop=q.price-d*self.config.stop_buffer_atr*atr,
                invalidation=q.price-d*self.config.stop_buffer_atr*atr,
                pivot_evidence=jsonable([p,q,*middle]))
            return True
        return False

    def update(self, ctx: Context) -> list[Signal]:
        error=self._data_error(ctx); b=ctx.execution.bar
        last=self._state['last']
        identity=[ctx.execution.symbol,ctx.execution.timeframe]
        if self._state['identity'] not in (None,identity): error=error or 'engine_identity_changed'
        if last and b.end.isoformat()==last['end']:
            if ctx.execution.observation.event_id==last['event_id'] and error is None: return []
            if ctx.execution.observation.event_id!=last['event_id']:
                error=error or 'historical_revision_requires_replay'
        if last and (b.start<datetime.fromisoformat(last['end']) or ctx.as_of<datetime.fromisoformat(last['as_of'])):
            error=error or 'nonmonotonic_observation'
        if error:
            self._cancel(ctx,error); self._state['compressed']=[]; self._state['box']=None
            self._route(ctx,'INVALID',error); return self._wait(ctx,error)
        # Any missing interval destroys a consecutive-bar box/candidate. Calendared
        # overnight gaps also reset them; no synthetic bars bridge a session.
        if last and b.start>datetime.fromisoformat(last['end']):
            self._cancel(ctx,'execution_gap'); self._state['compressed']=[]; self._state['box']=None
            self._state['trend_run']=0; self._state['trend_memory']=0
            last=None  # Do not infer a contiguous close crossing across absent bars.
        self._state['identity']=identity; self._state['index']+=1
        f=ctx.execution.features; e=f.ema; atr=f.atr; assert atr is not None
        old_memory=self._state['trend_memory']
        if self._state['index']-self._state['trend_memory_index']>self.config.transition_memory_bars: old_memory=0
        stack=self._stack(e)
        self._state['trend_run']=self._state['trend_run']+1 if stack and stack==self._state['trend_direction'] else int(bool(stack))
        self._state['trend_direction']=stack
        if self._state['trend_run']>=self.config.minimum_trend_bars:
            self._state['trend_memory']=stack; self._state['trend_memory_index']=self._state['index']
        self._state['last']={'end':b.end.isoformat(),'as_of':ctx.as_of.isoformat(),
            'event_id':ctx.execution.observation.event_id,'close':b.close,'high':b.high,'low':b.low,
            'ema':{str(k):v for k,v in e.items()},'phase':f.phase}
        refkey=self._reference_key(ctx)
        if self._state['reference_key'] not in (None,refkey):
            self._state['compressed']=[]; self._state['box']=None
        self._state['reference_key']=refkey
        if self._state['arm']: return self._active(ctx)
        enabled=self.config.enabled; tol=self.config.tolerance_atr*atr; buf=self.config.stop_buffer_atr*atr
        comp_enabled=any(x.startswith('compression') for x in enabled)
        if comp_enabled:
            if f.compression is True:
                self._state['compressed'].append({'high':b.high,'low':b.low})
                self._state['compressed']=self._state['compressed'][-self.config.maximum_compression_bars:]
                self._state['box']=None; self._route(ctx,'COMPRESSION','compression_active')
                return self._wait(ctx,'range_still_compressing')
            compressed=self._state['compressed']; self._state['compressed']=[]
            if len(compressed)>=self.config.minimum_compression_bars:
                self._state['box']={'low':min(x['low'] for x in compressed),
                    'high':max(x['high'] for x in compressed),'index':self._state['index']}
            box=self._state['box']
            if box and self._state['index']-box['index']>self.config.setup_expiry_bars:
                self._record(ctx,'CANCEL','compression_range_expired'); self._state['box']=None; box=None
            if box:
                self._route(ctx,'COMPRESSION','frozen_prebreak_range')
                d=1 if b.close>box['high'] else -1 if b.close<box['low'] else 0
                if d and stack==d and f.phase is not None and d*f.phase>0:
                    setup=next(x for x in enabled if x.startswith('compression'))
                    anchor=box['high'] if d==1 else box['low']; self._state['box']=None
                    if setup=='compression_breakout':
                        stop=(box['low'] if d==1 else box['high'])-d*buf
                        if self.config.compression_stop=='midpoint': stop=(box['high']+box['low'])/2
                        return self._signal(ctx,setup,d,stop,anchor,compression_stop=self.config.compression_stop,
                            box_low=box['low'],box_high=box['high'])
                    self._arm(ctx,setup,d,anchor=anchor,box_low=box['low'],box_high=box['high'],
                        invalidation=(b.low if d==1 else b.high)-d*buf)
                    return self._wait(ctx,'breakout_armed_for_retest')
                return self._wait(ctx,'no_aligned_breakout')
        # Transition chronology uses a previously established trend, never a
        # required future 13/48 crossover. Test each variant independently.
        if last and old_memory:
            d=-old_memory
            for setup in enabled:
                if setup not in ('vomy_early13','vomy_confirmed48'): continue
                n=13 if setup=='vomy_early13' else 48
                crossed=d*(last['close']-last['ema'][str(n)])<=0<d*(b.close-e[n])
                if crossed and (setup!='vomy_early13' or d*(b.close-e[8])>0):
                    self._route(ctx,'TREND_TRANSITION','prior_trend_then_ema_loss')
                    self._arm(ctx,setup,d,invalidation=(b.low if d==1 else b.high)-d*buf)
                    return self._wait(ctx,'awaiting_ema_rejection_or_retest')
        if last and 'vomy_pro21' in enabled:
            for d in (1,-1):
                if d*(e[21]-e[48])>0 and d*(e[21]-last['ema']['21'])>0 and d*(last['close']-last['ema']['21'])>0:
                    touched=b.low<=e[21]+tol if d==1 else b.high>=e[21]-tol
                    if touched and d*(b.close-e[21])>0 and d*(b.close-b.open)>0:
                        self._route(ctx,'TREND_TRANSITION','pro21_directional_rejection')
                        return self._signal(ctx,'vomy_pro21',d,(b.low if d==1 else b.high)-d*buf,e[21],ema_variant=21)
        # Confirmed pivots and subsequent structure break prevent oscillator-only
        # contrarian entries. An intact extreme trend can remain a WAIT indefinitely.
        pivots=self._pivots(ctx)
        if self._divergence(ctx,pivots):
            self._route(ctx,'EXTENSION_REVERSAL','confirmed_pivot_divergence')
            return self._wait(ctx,'divergence_requires_subsequent_structure_break')
        if last and 'phase_mean_reversion' in enabled and f.phase is not None and last['phase'] is not None:
            t=self.config.phase_exit_threshold
            for d in (1,-1):
                if d*last['phase']<=-t<d*f.phase:
                    candidates=[p for p in pivots if p.kind==('low' if d==1 else 'high')
                        and ctx.as_of-p.confirmed_at <= (b.end-b.start)*self.config.maximum_pivot_age_bars]
                    if candidates:
                        p=candidates[-1]; self._route(ctx,'EXTENSION_REVERSAL','phase_zone_exit_with_confirmed_pivot')
                        self._arm(ctx,'phase_mean_reversion',d,trigger=b.high if d==1 else b.low,
                            stop=p.price-d*buf,invalidation=p.price-d*buf,pivot_evidence=jsonable(p))
                        return self._wait(ctx,'zone_exit_requires_subsequent_price_confirmation')
        if stack:
            d=stack
            if self.config.require_context_alignment and self._context_direction(ctx)!=d:
                self._route(ctx,'NEUTRAL','context_conflict'); return self._wait(ctx,'context_direction_conflict')
            if last and 'golden_gate' in enabled:
                gate=ctx.reference.price(d*.382); destination=ctx.reference.price(d*.618)
                if d*(last['close']-gate)<=0<d*(b.close-gate):
                    self._route(ctx,'TREND_CONTINUATION','golden_gate_cross')
                    if d*((b.high if d==1 else b.low)-destination)>=0:
                        self._record(ctx,'CANCEL','golden_gate_target_touched_before_entry')
                        return self._wait(ctx,'target_already_touched')
                    self._arm(ctx,'golden_gate',d,stage='pullback',anchor=gate,destination=destination,
                        partial=ctx.reference.price(d*.5),invalidation=e[48]-d*buf)
                    return self._wait(ctx,'gate_cross_requires_pullback')
            if 'pivot_pullback' in enabled:
                if b.low<=e[21]+tol and b.high>=e[21]-tol and d*(b.close-e[48])>0:
                    self._route(ctx,'TREND_CONTINUATION','pivot_overlap')
                    stop=(b.low if d==1 else b.high)-d*buf
                    self._arm(ctx,'pivot_pullback',d,trigger=b.high if d==1 else b.low,
                        stop=stop,anchor=e[21],invalidation=stop)
                    return self._wait(ctx,'pullback_requires_recovery')
            if last and 'atr_retest' in enabled:
                crossed=[p for p in (ctx.reference.price(d*m) for d in (-1,1) for m in MULTIPLIERS)
                    if p>0 and d*(last['close']-p)<=0<d*(b.close-p)]
                if crossed:
                    anchor=max(crossed) if d==1 else min(crossed)
                    self._route(ctx,'TREND_CONTINUATION','atr_level_cross')
                    self._arm(ctx,'atr_retest',d,anchor=anchor,invalidation=(b.low if d==1 else b.high)-d*buf)
                    return self._wait(ctx,'level_cross_requires_retest')
            self._route(ctx,'TREND_CONTINUATION','directional_ribbon_without_setup')
            return self._wait(ctx,'no_eligible_continuation_event')
        self._route(ctx,'NEUTRAL','no_eligible_state_event')
        return self._wait(ctx,'no_setup')
