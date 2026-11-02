"""Deterministic opportunity ordering, not learned probabilities or an edge model.

Every candidate has already passed its family's unchanged entry/geometry gates.
Ranking compares net first-obstacle reward/risk first, then a declared regime
tie-break, remaining chase allowance and age. The tuple is an engineering utility
ordering, not a probability, expected return, vote count or sizing instruction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from math import isfinite
from typing import Any, Mapping

from .models import Context, Signal, aware

ROUTING_VERSION = 'independent-family-routing-1'


def candidate_sort_key(signal: Signal) -> tuple[float, int, float, int, str, str, str]:
    """Ascending, arrival-independent priority for a cross-symbol pending batch.

    Locally ranked signals retain their causal decision-time components. External
    signal injection gets cost-adjusted geometry with neutral awareness instead
    of an invented awareness score. Callers must independently enforce expiry,
    quote freshness, no-chase, risk and correlated-thesis admission.
    """
    signal.validate()
    components=OpportunityRouter._components(signal,{})
    routing=signal.metadata.get('routing',{})
    # Ranking metadata cannot overwrite geometry or inject an arbitrary score.
    # Only the bounded, declared regime tie-break survives a cross-symbol batch.
    stored=routing.get('utility_components') if isinstance(routing,dict) else None
    if (isinstance(stored,dict) and routing.get('routing_version')==ROUTING_VERSION
        and routing.get('awareness_status')=='available'
        and type(stored.get('awareness_regime_fit')) is int
        and stored['awareness_regime_fit'] in (0,1)):
        components['awareness_regime_fit']=stored['awareness_regime_fit']
    key=OpportunityRouter._key(components)
    if any(not isfinite(x) for x in key): raise ValueError('invalid candidate priority')
    return (*(-x for x in key),signal.symbol,signal.setup,signal.signal_id)


@dataclass(frozen=True)
class RoutingConfig:
    diagnostic_history_limit: int = 512

    def __post_init__(self) -> None:
        if type(self.diagnostic_history_limit) is not int or self.diagnostic_history_limit < 32:
            raise ValueError('diagnostic history must retain at least 32 events')


class OpportunityRouter:
    """Stateless economic ranking with explicit simultaneous-direction conflict.

    Same-direction, different-family candidates are retained for the portfolio
    controller's correlated-thesis admission. Exact duplicate IDs are collapsed.
    If opposed directions tie on the entire utility tuple, both wait; otherwise
    only the direction of the highest-ranked candidate survives this observation.
    No majority voting rewards redundant indicator families.
    """

    def __init__(self, config: RoutingConfig = RoutingConfig()):
        self.config = config

    @staticmethod
    def _awareness(ctx: Context, snapshot: Any) -> tuple[dict[str, Any], str]:
        if snapshot is None:
            return {}, 'not_supplied'
        try:
            raw = snapshot.to_dict() if hasattr(snapshot, 'to_dict') else snapshot
            if not isinstance(raw, Mapping):
                return {}, 'invalid_snapshot'
            clocks={}
            for key in ('as_of', 'latest_available_at', 'latest_bar_end'):
                value = raw.get(key)
                if value is None: return {}, 'missing_snapshot_chronology'
                at = datetime.fromisoformat(value) if isinstance(value, str) else value
                aware(at)
                clocks[key]=at
                if at > (ctx.execution.bar.end if key == 'latest_bar_end' else ctx.as_of):
                    return {}, 'future_snapshot_ignored'
                if key == 'latest_bar_end' and at != ctx.execution.bar.end:
                    return {}, 'different_execution_observation_ignored'
            if not clocks['latest_bar_end']<=clocks['latest_available_at']<=clocks['as_of']<=ctx.as_of:
                return {}, 'invalid_snapshot_chronology'
            if raw.get('symbol', ctx.execution.symbol) != ctx.execution.symbol:
                return {}, 'different_symbol_ignored'
            inferred = raw.get('inferred', {})
            if not isinstance(inferred, Mapping): return {}, 'invalid_inferences'
            return dict(inferred), 'available'
        except (TypeError, ValueError, AttributeError, OverflowError):
            return {}, 'invalid_snapshot'

    @staticmethod
    def _components(signal: Signal, inferred: dict[str, Any]) -> dict[str, Any]:
        cost = signal.metadata.get('estimated_round_trip_cost', 0.)
        if not isinstance(cost, (int, float)) or not isfinite(cost) or cost < 0:
            raise ValueError('invalid candidate cost estimate')
        risk = signal.direction * (signal.reference_entry - signal.stop) + cost
        reward = signal.direction * (signal.targets[0] - signal.reference_entry) - cost
        if risk <= 0 or reward <= 0:
            raise ValueError('candidate lacks positive net geometry')
        max_chase = signal.metadata.get('maximum_chase_atr', .4)
        if not isinstance(max_chase,(int,float)) or not isfinite(max_chase) or max_chase<0:
            raise ValueError('invalid candidate chase allowance')
        chase = abs(signal.reference_entry - signal.anchor) / signal.atr
        age = signal.metadata.get('candidate_age_bars', 0)
        if not isinstance(age, int) or age < 0: raise ValueError('invalid candidate age')
        # Hypothesis only: use the path label as a tie-break, never as an entry
        # veto, a signal substitute, evidence of edge or a risk multiplier.
        path = inferred.get('path_regime', 'unknown')
        reversal = 'mean_reversion' in signal.setup
        regime_fit = int((path == 'directional' and not reversal) or
                         (path == 'choppy' and reversal))
        return {'net_reward_risk': reward / risk,
                'awareness_regime_fit': regime_fit,
                'remaining_chase_atr': max_chase - chase,
                'candidate_age_bars': age}

    @staticmethod
    def _key(components: dict[str, Any]) -> tuple[float, int, float, int]:
        # Rounding prevents irrelevant floating noise from deciding an economic
        # tie. Components are compared lexicographically, with no fitted weights.
        return (round(components['net_reward_risk'], 12),
                components['awareness_regime_fit'],
                round(components['remaining_chase_atr'], 12),
                -components['candidate_age_bars'])

    def rank(self, ctx: Context, candidates: list[Signal], *, awareness: Any = None
             ) -> tuple[list[Signal], list[dict[str, Any]]]:
        inferred, awareness_status = self._awareness(ctx, awareness)
        events: list[dict[str, Any]] = []
        unique: dict[str, Signal] = {}
        for signal in candidates:
            signal.validate()
            if (signal.symbol!=ctx.execution.symbol or signal.timeframe!=ctx.execution.timeframe
                or signal.reference_horizon!=ctx.reference.horizon):
                raise ValueError('candidate/context identity mismatch')
            if not signal.bar_end<=ctx.execution.bar.end<=ctx.as_of or not signal.available_at<=ctx.as_of<signal.expires_at:
                raise ValueError('candidate unavailable, expired or from a future observation')
            if signal.signal_id in unique:
                if asdict(signal) != asdict(unique[signal.signal_id]):
                    raise ValueError('conflicting candidate signal ID')
                events.append({'event': 'SUPPRESS', 'reason': 'duplicate_candidate_id',
                               'signal_id': signal.signal_id, 'setup': signal.setup})
                continue
            unique[signal.signal_id] = signal
        scored = [(self._components(s, inferred), s) for s in unique.values()]
        scored.sort(key=lambda pair: (*(-x for x in self._key(pair[0])),
                                      pair[1].setup, pair[1].signal_id))
        winner_direction = scored[0][1].direction if scored else None
        if scored:
            top = self._key(scored[0][0])
            top_directions = {s.direction for c, s in scored if self._key(c) == top}
            if len(top_directions) > 1: winner_direction = None
        admitted: list[Signal] = []
        for rank, (components, signal) in enumerate(scored, 1):
            accepted = signal.direction == winner_direction
            detail = {'routing_version': ROUTING_VERSION, 'rank': rank,
                      'utility_components': components, 'utility_is_probability': False,
                      'ordering': ['net_reward_risk', 'awareness_regime_fit',
                                   'remaining_chase_atr', 'younger_candidate'],
                      'awareness_status': awareness_status,
                      'awareness_path_regime': inferred.get('path_regime', 'unknown'),
                      'candidate_count': len(scored)}
            events.append({'event': 'RANK' if accepted else 'SUPPRESS',
                'reason': 'admissible_ranked_candidate' if accepted else
                    'opposed_utility_tie_wait' if winner_direction is None else 'opposed_lower_utility',
                'signal_id': signal.signal_id, 'setup': signal.setup,
                'direction': signal.direction, **detail})
            if accepted:
                admitted.append(replace(signal, metadata={**signal.metadata, 'routing': detail}))
        return admitted, events
