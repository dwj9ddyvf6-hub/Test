# R10 independently versioned derivative; synthetic/reference repairs only.
# No original archive is edited. No broker or native data authentication.
"""Executable specified UIR/CRG mathematics, provenance gates and causal clocks.

This is not a trained strategy, event database, broker, or profitability backtest.
Fitted quantities are admitted only with explicit model provenance. Missing inputs
produce recorded abstentions. Underspecified estimators stay outside canonical
claims; see IMPLEMENTATION_DECISIONS.json. Synthetic tests do not measure alpha.
"""
from __future__ import annotations
R10_REPAIR_VERSION = "r10-information-catalyst-repair-v1"

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import expm1, fsum, isfinite, sqrt
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo
import re

import numpy as np

NY = ZoneInfo('America/New_York')


def number(x, name='number') -> float:
    if isinstance(x, (bool, np.bool_)) or x is None:
        raise ValueError(f'{name}: required finite real number')
    try:
        y = float(x)
    except (ValueError, TypeError):
        raise ValueError(f'{name}: required finite real number') from None
    if not isfinite(y):
        raise ValueError(f'{name}: required finite real number')
    return y


def stamp(x) -> datetime:
    if not isinstance(x, str) or not x:
        raise ValueError('explicit timezone timestamp required')
    try:
        d = datetime.fromisoformat(x.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('invalid timestamp') from None
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError('explicit timezone required')
    return d.astimezone(timezone.utc)


def hash64(x) -> bool:
    return isinstance(x, str) and bool(re.fullmatch('[0-9a-f]{64}', x))


def numeric_array(x, dimensions: int, name='array') -> np.ndarray:
    raw = np.asarray(x)
    if raw.dtype.kind not in 'fiu' or raw.ndim != dimensions:
        raise ValueError(f'{name}: numeric {dimensions}-dimensional array required')
    a = raw.astype(float)
    if not np.all(np.isfinite(a)):
        raise ValueError(f'{name}: nonfinite observation')
    return a


@dataclass(frozen=True)
class Gate:
    status: str
    reasons: tuple[str, ...] = ()
    values: Mapping[str, float] = field(default_factory=dict)

    @property
    def accepted(self):
        return self.status == 'QUALIFIED_RESEARCH_CANDIDATE'


@dataclass(frozen=True)
class Session:
    opened: datetime
    closed: datetime


class SessionClock:
    """Caller supplies a pinned complete exchange calendar, never weekday guesses."""
    def __init__(self, rows: Sequence[Mapping[str, str]]):
        self.sessions = tuple(Session(stamp(r['open']), stamp(r['close'])) for r in rows)
        if not self.sessions:
            raise ValueError('empty calendar')
        previous = None
        for s in self.sessions:
            if s.opened >= s.closed or (previous and s.opened <= previous):
                raise ValueError('unordered/overlapping/empty sessions')
            previous = s.closed

    def event_age(self, public_at: str, now_at: str) -> float:
        public, now = stamp(public_at), stamp(now_at)
        if now < public:
            raise ValueError('decision before publication')
        if public < self.sessions[0].opened and public.date() < self.sessions[0].opened.date():
            raise ValueError('calendar does not establish first eligible session')
        if now > self.sessions[-1].closed:
            raise ValueError('calendar incomplete through observation')
        age = 0.0
        for s in self.sessions:
            if s.closed <= public:
                continue
            start = max(public, s.opened)
            if now <= start:
                break
            age += min(1.0, (min(now, s.closed)-start).total_seconds() /
                       (s.closed-start).total_seconds())
        return age

    def horizon_close(self, public_at: str, eligible_sessions=20) -> datetime:
        if isinstance(eligible_sessions, bool) or not isinstance(eligible_sessions, int) or eligible_sessions <= 0:
            raise ValueError('positive session horizon required')
        public = stamp(public_at)
        # The original origin must be covered before counting eligible sessions;
        # starting a truncated calendar later must never silently restart age.
        self.event_age(public_at, public_at)
        eligible = [s for s in self.sessions if s.closed > public]
        if len(eligible) < eligible_sessions:
            raise ValueError('calendar incomplete through original horizon')
        return eligible[eligible_sessions-1].closed

    def next_session(self, at: str) -> Session:
        d = stamp(at)
        for s in self.sessions:
            if s.opened > d:
                return s
        raise ValueError('calendar incomplete')

    def first_full_after_receipt(self, receipt_at: str) -> int:
        d = stamp(receipt_at)
        for i, s in enumerate(self.sessions):
            if s.opened >= d:
                return i
        raise ValueError('calendar incomplete')

    def after(self, session_index: int, additional: int) -> Session:
        if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in (session_index,additional)):
            raise ValueError('invalid deadline')
        if not 0 <= session_index+additional < len(self.sessions):
            raise ValueError('calendar incomplete through deadline')
        return self.sessions[session_index+additional]


def response_fraction(age, knot_values) -> float:
    h = number(age, 'age')
    v = numeric_array(knot_values, 1, 'H knots')
    if h < 0 or len(v) != 6 or np.any(v < 0) or np.any(v > 1):
        raise ValueError('invalid response curve')
    if np.any(np.diff(v) < 0) or v[-1] != 1:
        raise ValueError('monotone bounded curve with H(20)=1 required')
    return float(np.interp(h, [0, 1, 2, 5, 10, 20], v))


def receiver_coefficient(x, y, penalty=1.0) -> float:
    """Exact constrained one-coefficient ridge, not unconstrained then sign reversal."""
    x, y = numeric_array(x, 1), numeric_array(y, 1)
    p = number(penalty)
    if not len(x) or len(x) != len(y) or p <= 0:
        raise ValueError('paired observations and positive penalty required')
    return max(0.0, float(np.dot(x, y) / (np.dot(x, x)+p)))


def original_impact(sigma_horizon, coefficient, exposure, direction, surprise):
    sig, b, a, s, q = map(number, (sigma_horizon, coefficient, exposure, direction, surprise))
    if sig <= 0 or b < 0 or not 0 < a <= 1 or s not in (-1, 1):
        raise ValueError('invalid volatility/coefficient/exposure/direction')
    return max(-0.05, min(0.05, sig*b*a*s*q))


def unresolved_impact(mu, H, C, discount=0.5):
    mu, H, C, discount = map(number, (mu, H, C, discount))
    if abs(mu) > 0.05 or not 0 <= H <= 1 or not 0 <= discount <= 1:
        raise ValueError('invalid bounded impact/response/discount')
    if mu == 0:
        return 0.0
    d = 1.0 if mu > 0 else -1.0
    raw = (1-H)*mu-discount*(C-H*mu)
    return d*max(0.0, min(d*mu, d*raw))


def directional_edge(u, se_mean, roundtrip_cost):
    u, se, cost = map(number, (u, se_mean, roundtrip_cost))
    if abs(u) > 0.05 or se < 0 or cost < 0:
        raise ValueError('invalid uncertainty or cost')
    if u == 0:
        return -cost
    d = 1 if u > 0 else -1
    adjusted = u-d*1.645*se
    # For a long, extreme uncertainty is harmlessly rejected rather than overflow.
    if adjusted > 700:
        return float('-inf')
    return d*expm1(adjusted)-cost


def factor_residual(stock_log, market_log, sector_log, intercept, market_beta, sector_beta,
                    elapsed_daily_fraction=1.0):
    a, m, z, intercept, bm, bz, dt = map(number,
        (stock_log, market_log, sector_log, intercept, market_beta, sector_beta, elapsed_daily_fraction))
    if dt < 0:
        raise ValueError('negative interval')
    return a-(intercept*dt+bm*m+bz*z)


UIR_REQUIRED = (
    'first_publication_utc', 'provider_receipt_utc', 'first_ingestion_utc',
    'document_version', 'document_sha256', 'inference_completed_utc',
    'encoder_id_and_hash', 'source_permanent_id', 'receiver_permanent_id',
    'edge_known_at_utc', 'edge_direction', 'directional_exposure_fraction',
    'event_class', 'closed_quote_bar_time_utc', 'knowledge_vintage',
    'classifier_hash', 'evidence_spans', 'event_cluster_id', 'relation_type',
    'orientation_supported', 'calendar_hash', 'model_manifest',
    'price', 'market_cap', 'dollar_adv20', 'history_sessions',
    'ordinary_us_common_stock', 'halted', 'source_forecast_risk_units',
    'sigma_horizon', 'receiver_coefficient', 'class_event_clusters',
    'H_knots', 'absorption_C', 'SE_mean', 'roundtrip_cost',
    'source_label_matured', 'receiver_label_matured', 'formation_at',
    'training_only_transforms', 'synchronized_factor_marks', 'source_pipeline_oof',
    'bar_received_at',
)


def model_errors(manifest, decision, public=None):
    errors = []
    if not isinstance(manifest, Mapping):
        return ['MODEL_MANIFEST_MISSING']
    try:
        trained = stamp(manifest['trained_at'])
        label = stamp(manifest['latest_label_received_at'])
        knowledge = stamp(manifest['knowledge_cutoff'])
        if label > trained or trained >= decision or knowledge > trained:
            errors.append('MODEL_CHRONOLOGY')
        if public is not None and trained >= public:
            errors.append('MODEL_NOT_FROZEN_BEFORE_EVENT')
        if not hash64(manifest['sha256']) or not manifest['id']:
            errors.append('MODEL_IDENTITY')
        if number(manifest['training_years']) < 5:
            errors.append('FIVE_YEAR_INITIAL_TRAINING_REQUIRED')
        if manifest.get('historical_checkpoint_audited') is not True:
            errors.append('MODEL_VINTAGE_UNVERIFIED')
    except (KeyError, ValueError, TypeError):
        errors.append('MODEL_MANIFEST_INCOMPLETE')
    return errors


def quote_errors(quote, decision, maximum_age):
    errors = []
    if not isinstance(quote, Mapping):
        return ['EXECUTABLE_QUOTE_MISSING']
    try:
        qtime, received = stamp(quote['at']), stamp(quote['received_at'])
        bid, ask = number(quote['bid']), number(quote['ask'])
        if not 0 < bid <= ask or number(quote['ask_shares']) <= 0 or number(quote['bid_shares']) <= 0:
            errors.append('QUOTE_PRICE_OR_SIZE')
        if qtime > received or received > decision or qtime > decision:
            errors.append('QUOTE_FUTURE_OR_REVERSED_TIME')
        if (decision-qtime).total_seconds() > maximum_age:
            errors.append('QUOTE_STALE')
        if quote.get('tradable') is not True:
            errors.append('QUOTE_NOT_TRADABLE')
    except (KeyError, ValueError, TypeError):
        errors.append('QUOTE_INCOMPLETE')
    return errors


def evaluate_uir(record: Mapping, decision_at: str, clock: SessionClock, phase='formation', ticket=None) -> Gate:
    errors = [f'MISSING:{k}' for k in UIR_REQUIRED if k not in record or record[k] is None]
    try:
        decision = stamp(decision_at)
    except ValueError:
        return Gate('DATA_HOLD', ('DECISION_TIMESTAMP',))
    if errors:
        return Gate('DATA_HOLD', tuple(errors))
    try:
        pub, receipt, ingestion, inference = [stamp(record[k]) for k in
            ('first_publication_utc','provider_receipt_utc','first_ingestion_utc','inference_completed_utc')]
        formation = stamp(record['formation_at'])
        if phase == 'formation' and decision != formation:
            errors.append('FORMATION_DECISION_NOT_EXACT_FROZEN_COHORT')
        bar = stamp(record['closed_quote_bar_time_utc'])
        if not bar <= stamp(record['bar_received_at']) <= decision:
            errors.append('BAR_RECEIPT_CHRONOLOGY')
        if not pub <= receipt <= ingestion <= inference <= formation <= decision:
            errors.append('DOCUMENT_AVAILABILITY_OR_FORMATION')
        ft = formation.astimezone(NY)
        if ft.hour != 18 or ft.minute != 30 or ft.second != 0 or ft.microsecond != 0:
            errors.append('FORMATION_CLOCK')
        if not any(s.opened.astimezone(NY).date() == ft.date() for s in clock.sessions):
            errors.append('FORMATION_NOT_EXCHANGE_SESSION')
        if receipt.astimezone(NY).date() == ft.date() and receipt.astimezone(NY).time() > datetime.min.replace(hour=17).time():
            errors.append('AFTER_1700_RECEIPT')
        if phase == 'formation' and (bar > formation or (bar.astimezone(NY).date() == ft.date() and bar.astimezone(NY).hour >= 16 and bar.astimezone(NY).time() > datetime.min.replace(hour=16).time())):
            errors.append('INITIAL_BAR_CUTOFF')
        if bar > decision:
            errors.append('FUTURE_BAR')
        if stamp(record['edge_known_at_utc']) >= pub:
            errors.append('EDGE_NOT_PRE_EVENT')
        if stamp(record['knowledge_vintage']) > pub:
            errors.append('FUTURE_KNOWLEDGE_VINTAGE')
        errors.extend(model_errors(record['model_manifest'], decision, pub))
        if not all(hash64(record[k]) for k in ('document_sha256','classifier_hash','calendar_hash')):
            errors.append('INPUT_HASH')
        if not record['document_version'] or not record['encoder_id_and_hash'] or not record['evidence_spans'] or not record['event_cluster_id']:
            errors.append('DOCUMENT_CLASSIFIER_IDENTITY')
        if not record['source_permanent_id'] or not record['receiver_permanent_id'] or record['source_permanent_id'] == record['receiver_permanent_id']:
            errors.append('SECURITY_IDENTITY')
        class_map = {'demand':(1, 1, 'supplier'), 'interruption':(-1, -1, 'customer')}
        if record['event_class'] not in class_map:
            errors.append('EXCLUDED_OR_AMBIGUOUS_EVENT')
        else:
            kappa, direction, relation = class_map[record['event_class']]
            if number(record['edge_direction']) != direction or record['relation_type'] != relation:
                errors.append('DIRECTIONAL_DENOMINATOR')
        if record['orientation_supported'] is not True:
            errors.append('OPERATING_ORIENTATION_UNSUPPORTED')
        if record['ordinary_us_common_stock'] is not True or record['halted'] is not False:
            errors.append('UNIVERSE_OR_HALT')
        if number(record['price']) < 10 or number(record['market_cap']) < 2e9 or number(record['dollar_adv20']) < 5e7 or number(record['history_sessions']) < 252:
            errors.append('UNIVERSE_FLOORS')
        if number(record['class_event_clusters']) < 100:
            errors.append('SPARSE_CLASS_NO_TRANSMISSION')
        for k in ('source_label_matured','receiver_label_matured','training_only_transforms','synchronized_factor_marks','source_pipeline_oof'):
            if record[k] is not True:
                errors.append(k.upper())
        age = clock.event_age(record['first_publication_utc'], decision_at)
        if age >= 20:
            return Gate('EXPIRED', ('ORIGINAL_HORIZON',))
        if age > 10:
            errors.append('NEW_ENTRY_TOO_OLD')
        H = response_fraction(age, record['H_knots'])
        q = class_map.get(record['event_class'],(1,1,''))[0]*number(record['source_forecast_risk_units'])
        mu = original_impact(record['sigma_horizon'],record['receiver_coefficient'],
            record['directional_exposure_fraction'],record['edge_direction'],q)
        u = unresolved_impact(mu,H,record['absorption_C'])
        edge = directional_edge(u,record['SE_mean'],record['roundtrip_cost'])
        if u <= 0:
            errors.append('CANONICAL_LONG_ONLY_NO_POSITIVE_FORECAST')
        if edge <= 0.002:
            errors.append('POST_COST_FLOOR')
        if phase == 'entry':
            if not isinstance(ticket, Mapping) or ticket.get('schema') != 'R10_UIR_FROZEN_CANDIDATE_V1':
                errors.append('FROZEN_CANDIDATE_REQUIRED')
            else:
                frozen = ticket.get('fields')
                if not isinstance(frozen, Mapping) or ticket.get('sha256') != candidate_hash(frozen):
                    errors.append('CANDIDATE_HASH_MISMATCH')
                elif set(frozen) != set(UIR_REQUIRED)-set(UIR_REFRESH_FIELDS):
                    errors.append('CANDIDATE_FIELD_SET_MISMATCH')
                elif any(record.get(k) != v for k,v in frozen.items()):
                    errors.append('FROZEN_CANDIDATE_INPUT_CHANGED')
            dt = decision.astimezone(NY)
            session = clock.next_session(formation.isoformat())
            if dt.date()!=session.opened.astimezone(NY).date() or not (dt.hour == 9 and dt.minute >= 45):
                errors.append('ENTRY_WINDOW')
            errors.extend(quote_errors(record.get('quote'), decision, 2))
            if bar.astimezone(NY).date() == dt.date() and (bar.astimezone(NY).hour > 9 or bar.astimezone(NY).hour == 9 and bar.astimezone(NY).minute >= 45):
                errors.append('PREENTRY_MARK_CUTOFF')
        elif phase != 'formation':
            errors.append('UNKNOWN_PHASE')
        values={'age':age,'q':q,'mu_residual_log':mu,'u_residual_log':u,'H':H,'net_directional_relative_edge':edge}
    except (ValueError, TypeError, KeyError, OverflowError):
        return Gate('DATA_HOLD', tuple(errors+['INVALID_REQUIRED_INPUT']))
    return Gate('NO_TRADE' if errors else 'QUALIFIED_RESEARCH_CANDIDATE',tuple(errors),values)


UIR_REFRESH_FIELDS = ('closed_quote_bar_time_utc', 'bar_received_at', 'absorption_C',
                      'roundtrip_cost', 'price', 'halted')

def candidate_hash(fields):
    import hashlib, json
    return hashlib.sha256(json.dumps(fields,sort_keys=True,separators=(',',':'),
                                    allow_nan=False).encode()).hexdigest()

def freeze_uir_candidate(record, decision_at, clock):
    import json
    gate=evaluate_uir(record,decision_at,clock)
    if not gate.accepted:
        raise ValueError('Candidate did not pass reference qualification: '+','.join(gate.reasons))
    fields=json.loads(json.dumps({k:record[k] for k in UIR_REQUIRED if k not in UIR_REFRESH_FIELDS},allow_nan=False))
    return {'schema':'R10_UIR_FROZEN_CANDIDATE_V1','fields':fields,'sha256':candidate_hash(fields),
            'raw_source_authentication':False,'activation_authorized':False}


class RelayLedger:
    """One independent economic shock per receiver; repeats never reset origins."""
    def __init__(self, clock: SessionClock):
        self.clock, self.rows, self.blocked_until, self.log = clock, {}, {}, []
        self.cluster_origins = {}
        self.last_known_at = {}

    def observe(self, receiver, cluster, public_at, mu, known_at):
        pub, known, mu = stamp(public_at), stamp(known_at), number(mu)
        if not receiver or not cluster or known < pub:
            raise ValueError('event identity/chronology')
        if receiver in self.last_known_at and known < self.last_known_at[receiver]:
            raise ValueError('processed receipt clock cannot move backward')
        # Validate the full original horizon before mutating processed state.
        horizon = self.clock.horizon_close(public_at)
        self.last_known_at[receiver] = known
        until = self.blocked_until.get(receiver)
        if until is not None and known < until:
            if (receiver,cluster) not in self.cluster_origins:
                self.cluster_origins[receiver,cluster]=pub
                self.blocked_until[receiver]=max(until,horizon)
            self.log.append({'receiver':receiver,'action':'BLOCKED','cluster':cluster})
            return 'BLOCKED'
        previous = self.rows.get(receiver)
        if (receiver,cluster) in self.cluster_origins and (not previous or previous['cluster']!=cluster):
            self.log.append({'receiver':receiver,'action':'DUPLICATE_RETIRED_NO_REVIVAL'})
            return 'DUPLICATE_RETIRED_NO_REVIVAL'
        if previous and known>=previous['horizon'] and previous['state']=='ACTIVE':
            previous['state']='EXPIRED'
        if previous and previous['cluster'] != cluster and known < previous['horizon']:
            latest = max(pub, previous['public'])
            self.cluster_origins[receiver,cluster]=pub
            self.blocked_until[receiver] = self.clock.horizon_close(latest.isoformat())
            previous['state']='RETIRED_SECOND_EVENT'
            self.log.append({'receiver':receiver,'action':'EXIT_NEXT_WINDOW','cluster':cluster})
            return 'EXIT_NEXT_WINDOW'
        if previous and previous['cluster'] == cluster:
            if previous['state'] != 'ACTIVE':
                self.log.append({'receiver':receiver,'action':'DUPLICATE_RETIRED_NO_REVIVAL'})
                return 'DUPLICATE_RETIRED_NO_REVIVAL'
            if mu*previous['mu'] < 0:
                previous['state']='REJECTED_OPPOSING_DUPLICATE'
                self.log.append({'receiver':receiver,'action':'OPPOSING_DUPLICATE'})
                return 'OPPOSING_DUPLICATE'
            if abs(mu) > abs(previous['mu']):
                previous['mu']=mu
            self.log.append({'receiver':receiver,'action':'DUPLICATE_NO_RESET'})
            return 'DUPLICATE_NO_RESET'
        self.rows[receiver]={'cluster':cluster,'public':pub,'horizon':horizon,'mu':mu,'state':'ACTIVE'}
        self.cluster_origins[receiver,cluster]=pub
        self.log.append({'receiver':receiver,'action':'NEW'})
        return 'NEW'

    def retire(self, receiver, reason):
        if receiver in self.rows:
            self.rows[receiver]['state']='RETIRED'
            self.log.append({'receiver':receiver,'action':'RETIRED','reason':reason})


def uir_weights(names, edges, annual_covariance, sectors, shocks):
    n=len(names)
    if not n or n != len(set(names)) or len(edges) != n or len(sectors)!=n or len(shocks)!=n:
        raise ValueError('aligned distinct eligible names required')
    e=numeric_array(edges,1); cov=numeric_array(annual_covariance,2)
    if cov.shape!=(n,n) or np.any(e<=0) or not np.allclose(cov,cov.T) or np.linalg.eigvalsh(cov).min() < -1e-10 or np.any(np.diag(cov)<=0):
        raise ValueError('positive edge and valid covariance required')
    selected=sorted(range(n),key=lambda i:(-e[i],names[i]))[:30]
    scores=e/np.diag(cov); w=np.zeros(n)
    for _ in range(n+2):
        available=[]
        for i in selected:
            sec=float(sum(w[j] for j in range(n) if sectors[j]==sectors[i]))
            shock=float(sum(w[j] for j in range(n) if shocks[j]==shocks[i]))
            if min(.04-w[i],.25-sec,.15-shock) > 1e-12:
                available.append(i)
        remaining=.95-float(w.sum())
        if not available or remaining<=1e-12:
            break
        proposals={i:remaining*scores[i]/sum(scores[j] for j in available) for i in available}
        # Proportional simultaneous step bounded by all group and individual caps.
        scale=1.0
        for i in available:
            scale=min(scale,(.04-w[i])/proposals[i])
        for groups,cap in ((sectors,.25),(shocks,.15)):
            for group in set(groups):
                ids=[i for i in available if groups[i]==group]
                proposed=sum(proposals[i] for i in ids)
                if proposed:
                    used=sum(w[j] for j in range(n) if groups[j]==group)
                    scale=min(scale,(cap-used)/proposed)
        if scale<=1e-12:
            break
        for i in available:
            w[i]+=scale*proposals[i]
    vol=sqrt(max(0,float(w@cov@w)))
    if vol>.12:
        w*=.12/vol
    return dict(zip(names,map(float,w)))


def unlevered_cash_flow(cfo, cash_capex, cash_interest, reported_tax):
    cfo,capex,interest,t=map(number,(cfo,cash_capex,cash_interest,reported_tax))
    if capex<0 or interest<0:
        raise ValueError('cash spending uses positive USD magnitude')
    return cfo-capex+interest*(1-max(0,min(.35,t)))


def capital_bridge(price, shares, financial_debt, unrestricted_cash, *,
                   convertible_debt=0, converted_shares=0, convertible_mode='none'):
    p,n,d,c,cd,cn=map(number,(price,shares,financial_debt,unrestricted_cash,convertible_debt,converted_shares))
    if p<=0 or n<=0 or min(d,c,cd,cn)<0 or convertible_mode not in ('none','debt','converted'):
        raise ValueError('invalid bridge')
    if convertible_mode=='none' and (cd or cn):
        raise ValueError('unclassified convertible')
    if convertible_mode=='debt' and cn:
        raise ValueError('convertible double count')
    if convertible_mode=='converted' and cd:
        raise ValueError('convertible double count')
    # debt input excludes the separately identified convertible instrument.
    D=d+cd-c; N=n+cn; E=p*N+D
    if E<=0:
        raise ValueError('nonpositive enterprise value')
    return {'E':E,'D':D,'N':N}


def capitalization_set(peer_multiples, lower_plausible, upper_plausible):
    a=numeric_array(peer_multiples,1)
    lo,hi=number(lower_plausible),number(upper_plausible)
    if len(a)<30 or lo<=0 or hi<lo or np.any(a<lo) or np.any(a>hi):
        raise ValueError('30 valid peers and frozen plausibility policy required')
    quartiles=np.quantile(a,[.25,.5,.75],method='linear')
    result=np.array([.85*quartiles[0],*quartiles,1.15*quartiles[-1]])
    if np.any(result<=0) or np.any(result<lo) or np.any(result>hi):
        raise ValueError('stress endpoints violate frozen plausibility policy')
    return tuple(map(float,result))


def valuation_stats(annual_draws, multiples, enterprise_value, revenue, prior_annual):
    q=numeric_array(annual_draws,1); m=numeric_array(multiples,1)
    E,R,Qprior=map(number,(enterprise_value,revenue,prior_annual))
    if not len(q) or not len(m) or np.any(m<=0) or E<=0 or R<=0:
        raise ValueError('valid annual draws, multiple, EV and revenue required')
    hurdle=max(E/x for x in m)
    med=float(np.median(q))
    return {'p':float(np.mean(q>hurdle)),'G':min((x*med-E)/E for x in m),
            'Delta':(med-Qprior)/R,'Q_median':med,'robust_hurdle':hurdle}


def annual_joint_draws(quarter_predictions, heldout_residual_vectors, trailing_revenue):
    predictions=numeric_array(quarter_predictions,1)
    residuals=numeric_array(heldout_residual_vectors,2)
    R=number(trailing_revenue)
    if predictions.shape!=(4,) or residuals.shape[1]!=4 or not len(residuals) or R<=0:
        raise ValueError('four aligned quarter heads and joint residual vectors required')
    # Predictions and residual vectors are in trailing-revenue-normalized units.
    return R*np.sum(predictions+residuals,axis=1)


def expected_shortfall(gross_policy_draws, separately_modeled_costs, tail=.05):
    gross=numeric_array(gross_policy_draws,1)
    cost=numeric_array(separately_modeled_costs,1)
    tail=number(tail)
    if not len(gross) or len(gross)!=len(cost) or np.any(cost<0) or not 0<tail<=1:
        raise ValueError('paired policy draw costs required')
    losses=np.sort(gross-cost)
    mass=tail*len(losses); whole=int(mass); remainder=mass-whole
    total=float(losses[:whole].sum())
    if remainder>0:
        total+=remainder*losses[whole]
    return max(0,-total/mass)


def crg_weight(ES):
    es=number(ES)
    if es<0:
        raise ValueError('nonnegative expected loss magnitude required')
    return min(.05,.0025/max(es,.08))


def crg_portfolio(candidates):
    """Greedy frozen rank order, known industry/shared-source caps; cash remainder."""
    if not isinstance(candidates,Sequence):
        raise ValueError('candidate sequence required')
    seen=set(); stock={}; industry={}; customers={}; used=0.0
    ordered=sorted(candidates,key=lambda c:(-number(c['rank']),c['security_id']))
    for c in ordered:
        name,ind,customer=c['security_id'],c['industry'],c['major_customer_or_contract']
        if not name or name in seen or not ind or not customer:
            raise ValueError('unique issuer and known shared exposure required')
        seen.add(name)
        if number(c['rank'])<=0:
            continue
        size=min(crg_weight(c['ES']),1-used,.25-industry.get(ind,0),.1-customers.get(customer,0))
        size=max(0.0,size)
        stock[name]=size; used+=size
        industry[ind]=industry.get(ind,0)+size
        customers[customer]=customers.get(customer,0)+size
    return {'weights':stock,'cash':max(0.0,1-used),'shared_demand_25pct_loss':{key:.25*w for key,w in customers.items()}}


def crg_side_cost(half_spread, explicit_fee_rate, sigma20, order_shares, ADV_shares):
    spread,fees,sigma,q,adv=map(number,(half_spread,explicit_fee_rate,sigma20,order_shares,ADV_shares))
    if min(spread,fees,sigma)<0 or q<0 or adv<=0:
        raise ValueError('cost units/inputs')
    if q==0:
        return {'all_in':0.0,'fill_concession':0.0,'fee_rate':fees}
    allin=max(.001,spread+fees+.25*sigma*sqrt(q/adv))
    return {'all_in':allin,'fill_concession':allin-fees,'fee_rate':fees}


def episode_accounting(buys, sells, dividends_usd, reserved_capital):
    A, dividends=number(reserved_capital),number(dividends_usd)
    if A<=0 or dividends<0:
        raise ValueError('reserved capital and dividend ledger required')
    quantities=[]; reference=[]; actual=[]; concessions=[]; fees=[]
    for sign,legs in ((-1,buys),(1,sells)):
        total=0.0
        for leg in legs:
            q,mid,fill,fee=map(number,(leg['quantity'],leg['midpoint'],leg['fill'],leg['fees_usd']))
            if q<=0 or mid<=0 or fill<=0 or fee<0:
                raise ValueError('executed positive fill legs only')
            total+=q; reference.append(sign*q*mid); actual.append(sign*q*fill)
            concessions.append(-sign*q*(fill-mid)); fees.append(fee)
        quantities.append(total)
    if quantities[0]!=quantities[1]:
        raise ValueError('open/unreconciled quantity blocks completed episode payoff')
    if not quantities[0]:
        if dividends:
            raise ValueError('dividends without position')
        return {'status':'ABSTENTION','gross':0.0,'C':0.0,'net':0.0}
    gross=(fsum(reference)+dividends)/A
    C=(fsum(concessions)+fsum(fees))/A
    net=(fsum(actual)+dividends-fsum(fees))/A
    if not np.isclose(net,gross-C,rtol=1e-12,atol=1e-14):
        raise AssertionError('gross-cost-net identity failed')
    return {'status':'CLOSED_EPISODE','gross':gross,'C':C,'net':net}


CRG_REQUIRED=(
    'issuer_id','security_id','fiscal_period','units','first_public_at','provider_receipt_at',
    'ingested_at','content_hash','revision_id','sec_acceptance_at','document_kind',
    'event_date','event_version','schedule_first_observed_at','schedule_primary_confirmed',
    'event_distance_sessions','calendar_hash','model_manifest','quarter_ids',
    'quarter_forecasts','joint_residual_vectors','prior_annual_forecast','ttm_revenue',
    'ttm_cfo','ttm_cash_capex','ttm_cash_interest','reported_tax','accounting_US_GAAP',
    'lease_classification_known','finance_lease_debt','finance_lease_investment_matched',
    'full_finance_lease_reconciliation','financial_debt_excluding_convertible',
    'unrestricted_cash','current_share_equivalents','shares_reconciled','price',
    'convertible_mode','convertible_debt','converted_shares','unresolved_claim_usd',
    'claim_materiality_known','ordinary_us_common_stock','industry',
    'median_dollar_volume60','market_cap','operating_observations',
    'peer_multiples','peer_known_at','peer_plausibility_bounds',
    'lower_mean_return','lower_excess_qqq','lower_excess_spy','cost_C','ES',
    'return_bootstrap_fits','return_policy_labels_exact','quarter_labels_matured',
    'training_only_transforms','return_features_no_future_benchmarks','cancel_fields_observed',
    'cash_flow_features_oof','residual_calibration_oof',
)


def evaluate_crg(record: Mapping, decision_at: str, entry_recheck=False) -> Gate:
    # Non-SEC primary releases explicitly have sec_acceptance_at=None. Field omission
    # is different from a declared nonapplicable field.
    errors=[f'MISSING:{k}' for k in CRG_REQUIRED if k not in record or
            (record[k] is None and k!='sec_acceptance_at')]
    if errors:
        return Gate('NO_TRADE',tuple(errors))
    try:
        decision=stamp(decision_at)
        if not entry_recheck and (decision.astimezone(NY).hour,decision.astimezone(NY).minute,decision.astimezone(NY).second)!=(18,0,0):
            errors.append('COHORT_CLOCK')
        pub,receipt,ingestion=map(stamp,(record['first_public_at'],record['provider_receipt_at'],record['ingested_at']))
        if not pub<=receipt<=ingestion<=decision:
            errors.append('SOURCE_AVAILABILITY')
        if record['document_kind']=='SEC':
            if stamp(record['sec_acceptance_at'])>pub:
                errors.append('SEC_ACCEPTANCE_AFTER_PUBLICATION')
        elif record['document_kind']!='ISSUER_PRIMARY':
            errors.append('PRIMARY_SOURCE_REQUIRED')
        if not record['issuer_id'] or not record['security_id'] or not record['fiscal_period'] or not record['revision_id']:
            errors.append('IDENTITY_OR_PERIOD')
        if record['units']!='USD' or not hash64(record['content_hash']) or not hash64(record['calendar_hash']):
            errors.append('UNITS_OR_HASH')
        errors.extend(model_errors(record['model_manifest'],decision))
        if record['schedule_primary_confirmed'] is not True or stamp(record['schedule_first_observed_at'])>=decision:
            errors.append('EVENT_CLOCK_NOT_PRECONFIRMED')
        if not 3<=number(record['event_distance_sessions'])<=15:
            errors.append('EVENT_DISTANCE')
        if stamp(record['event_date'])<=decision or not record['event_version']:
            errors.append('EVENT_CALENDAR_IDENTITY')
        if record['ordinary_us_common_stock'] is not True or record['industry'] not in ('industrial equipment','semiconductors','enterprise software'):
            errors.append('UNIVERSE')
        if number(record['price'])<10 or number(record['median_dollar_volume60'])<3e7 or number(record['market_cap'])<2e9:
            errors.append('UNIVERSE_FLOORS')
        if record['accounting_US_GAAP'] is not True or record['lease_classification_known'] is not True or record['shares_reconciled'] is not True or record['claim_materiality_known'] is not True:
            errors.append('ACCOUNTING_RECONCILIATION')
        qttm=unlevered_cash_flow(record['ttm_cfo'],record['ttm_cash_capex'],record['ttm_cash_interest'],record['reported_tax'])
        if qttm<=0 or number(record['ttm_revenue'])<=0:
            errors.append('POSITIVE_KNOWN_FINANCIAL_GATE')
        bridge_price = record['entry_price'] if entry_recheck else record['price']
        bridge=capital_bridge(bridge_price,record['current_share_equivalents'],record['financial_debt_excluding_convertible'],record['unrestricted_cash'],
            convertible_debt=record['convertible_debt'],converted_shares=record['converted_shares'],convertible_mode=record['convertible_mode'])
        fl=number(record['finance_lease_debt']); claim=number(record['unresolved_claim_usd'])
        if fl<0 or claim<0:
            errors.append('INVALID_CLAIM_MAGNITUDE')
        if fl>0 and record['finance_lease_investment_matched'] is not True or fl>.005*bridge['E'] and record['full_finance_lease_reconciliation'] is not True:
            errors.append('FINANCE_LEASE_RECONCILIATION')
        if claim>.01*bridge['E']:
            errors.append('MATERIAL_UNRESOLVED_CLAIM')
        observations=record['operating_observations']
        if not isinstance(observations,Sequence) or isinstance(observations,str):
            raise ValueError('typed operating observations required')
        families=set(); ids={}
        allowed={'backlog','shipment','independent_demand'}
        for o in observations:
            family=o['family']; obs_id=o['economic_observation_id']
            if not obs_id or family not in allowed or o.get('typed_definition_frozen') is not True:
                errors.append('OPERATING_DRIVER_IDENTITY')
            opub,oreceipt,oingest = (stamp(o[k]) for k in ('first_public_at','provider_receipt_at','ingested_at'))
            if not opub<=oreceipt<=oingest<=decision:
                errors.append('FUTURE_OPERATING_EVIDENCE')
            if obs_id in ids and ids[obs_id]!=family:
                errors.append('DUPLICATE_RELABELED_DRIVER')
            ids[obs_id]=family
            if o.get('status') not in ('observed','cancelled','adverse'):
                errors.append('OPERATING_OUTCOME_STATUS')
            if o.get('known_numeric_value') is None:
                errors.append('OPERATING_VALUE_MISSING')
            else:
                number(o['known_numeric_value'])
            families.add(family)
        if len(families)<2 or len(families)>3:
            errors.append('DISTINCT_DRIVER_FAMILIES')
        peers=record['peer_multiples']; known=record['peer_known_at']
        if len(peers)!=len(known) or any(stamp(t)>=decision for t in known):
            errors.append('PEER_VINTAGE')
        multiple=capitalization_set(peers,*record['peer_plausibility_bounds'])
        if len(record['quarter_ids'])!=4 or len(set(record['quarter_ids']))!=4 or any(not isinstance(q,str) or not q for q in record['quarter_ids']):
            errors.append('FROZEN_QUARTER_IDENTITY')
        annual=annual_joint_draws(record['quarter_forecasts'],record['joint_residual_vectors'],record['ttm_revenue'])
        stats=valuation_stats(annual,multiple,bridge['E'],record['ttm_revenue'],record['prior_annual_forecast'])
        if stats['p']<.8 or stats['G']<.05 or stats['Delta']<=0:
            errors.append('OPERATING_GATE')
        cost=number(record['cost_C']); ES=number(record['ES'])
        L,Lq,Ls=map(number,(record['lower_mean_return'],record['lower_excess_qqq'],record['lower_excess_spy']))
        if cost<0 or ES<0:
            errors.append('COST_OR_TAIL_MAGNITUDE')
        if min(L,Lq,Ls)<=2*cost+.005:
            errors.append('DUAL_BENCHMARK_RETURN_BRIDGE')
        if number(record['return_bootstrap_fits'])!=200:
            errors.append('BOOTSTRAP_MODEL_COUNT')
        for k in ('return_policy_labels_exact','quarter_labels_matured','training_only_transforms','return_features_no_future_benchmarks','cancel_fields_observed','cash_flow_features_oof','residual_calibration_oof'):
            if record[k] is not True:
                errors.append(k.upper())
        if entry_recheck:
            session_open,session_close=stamp(record['session_open_at']),stamp(record['session_close_at'])
            if not session_open<=decision<session_close or session_open.astimezone(NY).date()!=decision.astimezone(NY).date():
                errors.append('ENTRY_OUTSIDE_REGULAR_SESSION')
            if not decision.astimezone(NY).time()>=datetime.min.replace(hour=10).time():
                errors.append('ENTRY_BEFORE_1000')
            max_age=number(record['quote_max_age_seconds'])
            if max_age<=0:
                errors.append('QUOTE_POLICY')
            errors.extend(quote_errors(record.get('quote'),decision,max_age))
            q=record['quote']; mid=(number(q['ask'])+number(q['bid']))/2
            if number(record['entry_price'])<number(q['ask']):
                errors.append('BUY_PRICE_BELOW_EXECUTABLE_ASK')
            if (number(q['ask'])-number(q['bid']))/mid>.002:
                errors.append('SPREAD_ABOVE_20BP')
            if abs(number(record['entry_price'])-number(record['prior_close']))>number(record['lagged_ATR']):
                errors.append('GAP_ABOVE_ATR')
            if record.get('halted') is not False or record.get('corporate_action_resolved') is not True:
                errors.append('HALT_OR_CORPORATE_ACTION')
            order_shares, adv_shares=number(record['order_shares']),number(record['ADV60_shares'])
            if order_shares<=0 or adv_shares<=0:
                errors.append('ENTRY_QUANTITY_OR_ADV_NONPOSITIVE')
            elif order_shares>.0025*adv_shares:
                errors.append('ENTRY_PARTICIPATION')
        values={**bridge,**stats,'weight':crg_weight(ES),'rank':min(Lq-2*cost,Ls-2*cost)/(ES+.01)}
    except (ValueError,TypeError,KeyError,IndexError,OverflowError):
        return Gate('NO_TRADE',tuple(errors+['INVALID_REQUIRED_INPUT']))
    return Gate('NO_TRADE' if errors else 'QUALIFIED_RESEARCH_CANDIDATE',tuple(errors),values)


class CatalystEpisode:
    """One first-eligible decision, immutable four-quarter target and entry deadline."""
    def __init__(self, episode_id, quarters, original_prior, decision_at, outcome):
        if not episode_id or len(quarters)!=4 or len(set(quarters))!=4:
            raise ValueError('episode identity')
        if outcome not in ('QUALIFIED','REJECTED','NO_TRADE'):
            raise ValueError('initial outcome')
        self.episode_id=episode_id; self.quarters=tuple(quarters)
        self.prior=number(original_prior); self.decision=stamp(decision_at)
        self.initial_outcome=outcome; self.log=[{'action':'INITIAL_DECISION','outcome':outcome}]
        self.original_entry_index=None; self.first_full_release_index=None
        self.actuals={}; self.state=outcome

    def retry(self):
        self.log.append({'action':'NO_RETRY'})
        return 'NO_RETRY'

    def fill(self, entry_index):
        if self.initial_outcome!='QUALIFIED' or self.original_entry_index is not None:
            raise ValueError('unqualified or repeated entry')
        if isinstance(entry_index,bool) or not isinstance(entry_index,int) or entry_index<0:
            raise ValueError('entry index')
        self.original_entry_index=entry_index; self.state='HELD'

    def deadline_index(self):
        if self.original_entry_index is None:
            raise ValueError('no filled episode')
        deadline=self.original_entry_index+28
        if self.first_full_release_index is not None:
            deadline=min(deadline,self.first_full_release_index+10)
        return deadline

    def release(self, first_full_index, actuals: Mapping, remaining_forecasts: Mapping, reported_quarter_ids):
        if self.state!='HELD' or self.first_full_release_index is not None:
            raise ValueError('invalid release transition')
        if first_full_index<self.original_entry_index:
            raise ValueError('release before entry')
        self.first_full_release_index=first_full_index
        if not reported_quarter_ids or not set(reported_quarter_ids)<=set(self.quarters) or set(actuals)!=set(reported_quarter_ids) or set(actuals)&set(remaining_forecasts) or set(actuals)|set(remaining_forecasts)!=set(self.quarters):
            self.state='EXIT_MISSING_REQUIRED_RELEASE'
            self.log.append({'action':self.state})
            return None
        try:
            components={q:number(actuals[q] if q in actuals else remaining_forecasts[q]) for q in self.quarters}
        except ValueError:
            self.state='EXIT_MISSING_REQUIRED_RELEASE'
            return None
        self.actuals=dict(actuals)
        self.log.append({'action':'RECONCILED_ORIGINAL_TARGET','quarter_ids':self.quarters})
        return fsum(components.values())

    def reconciliation_exit(self,p,G,Delta,hard_falsifier=False):
        p,G,Delta=map(number,(p,G,Delta))
        if self.state=='EXIT_MISSING_REQUIRED_RELEASE' or hard_falsifier or G<.02 or p<.60 or Delta<=0:
            self.state='EXIT_NEXT_1000'
            return True
        return False

    def missed_date_exit_index(self,scheduled_index):
        return min(scheduled_index+2,self.original_entry_index+28)


class CatalystRegistry:
    def __init__(self):
        self.episodes={}; self.log=[]

    def register_first_decision(self,episode_id,quarters,prior,decision_at,outcome,first_eligible_at):
        if episode_id in self.episodes:
            self.log.append({'episode':episode_id,'action':'NO_RETRY'})
            return None
        if stamp(first_eligible_at)!=stamp(decision_at):
            raise ValueError('not original first-eligible cohort')
        episode=CatalystEpisode(episode_id,quarters,prior,decision_at,outcome)
        self.episodes[episode_id]=episode
        self.log.append({'episode':episode_id,'action':'INITIAL_DECISION','outcome':outcome})
        return episode


def liquidation_fill(trigger_price,quote_bid,halted):
    trigger,bid=number(trigger_price),number(quote_bid)
    if trigger<=0 or bid<=0 or not isinstance(halted,bool):
        raise ValueError('obtainable executable bid required')
    if halted:
        return {'action':'WAIT_HALT','fill':None}
    return {'action':'SELL_OBTAINABLE_BID','fill':bid,'trigger':trigger}


def uir_order_capacity(order_dollars,daily_dollar_ADV,eligible_minute_dollars):
    q,adv,minute=map(number,(order_dollars,daily_dollar_ADV,eligible_minute_dollars))
    if q<0 or adv<=0 or minute<0:
        raise ValueError('liquidity units')
    return min(q,.01*adv,.05*minute)


def uir_side_cost(fees,spread_fraction,daily_volatility,order_dollars,daily_dollar_ADV):
    fees,spread,sigma,q,adv=map(number,(fees,spread_fraction,daily_volatility,order_dollars,daily_dollar_ADV))
    if min(fees,spread,sigma,q)<0 or adv<=0:
        raise ValueError('matched dollar-notional cost units required')
    return fees+spread/2+.5*sigma*sqrt(q/adv)


@dataclass(frozen=True)
class RidgeModel:
    means: np.ndarray
    scales: np.ndarray
    coefficients: np.ndarray
    intercept: np.ndarray
    manifest: Mapping

    def predict(self,X):
        X=numeric_array(X,2)
        if X.shape[1]!=len(self.means):
            raise ValueError('feature identity/shape')
        return ((X-self.means)/self.scales)@self.coefficients+self.intercept


def asof_snapshot(revisions,cutoff_at):
    """Latest available immutable observation version; future rows have no effect."""
    cutoff=stamp(cutoff_at); selected={}
    for r in revisions:
        pub=stamp(r['first_public_at'])
        if pub>cutoff:
            continue
        receipt,ingestion=map(stamp,(r['provider_receipt_at'],r['ingested_at']))
        available=max(pub,receipt,ingestion)
        if available>cutoff:
            continue
        identity=r['observation_id']
        if not identity or not r['revision_id'] or not hash64(r['content_hash']):
            raise ValueError('observation/version identity')
        if not pub<=receipt<=ingestion:
            raise ValueError('invalid revision source chronology')
        current=selected.get(identity)
        if current is None or available>current[0]:
            selected[identity]=(available,dict(r))
        elif available==current[0] and r['content_hash']!=current[1]['content_hash']:
            raise ValueError('conflicting identical-time versions need source adjudication')
    return {key:value[1] for key,value in sorted(selected.items())}


def require_chronological_stacking(origin_at,artifacts):
    """Generated return features must come from historical as-of first-stage fits."""
    origin=stamp(origin_at)
    if set(artifacts)!={'cash_flow_model','residual_calibration','peer_scenarios'}:
        raise ValueError('complete generated-feature artifact lineage required')
    for name,a in artifacts.items():
        created=stamp(a['created_at']); label=stamp(a['latest_label_received_at'])
        available=stamp(a['maximum_input_available_at'])
        if not label<=created<origin or available>created or not hash64(a['sha256']):
            raise ValueError(f'{name}: future/self-label generated feature')


def lower_mean_forecasts(bootstrap_predictions):
    forecasts=numeric_array(bootstrap_predictions,2)
    if forecasts.shape!=(200,3):
        raise ValueError('200 joint mean fits, stock/QQQ/SPY heads required')
    return tuple(map(float,np.quantile(forecasts,.1,axis=0,method='linear')))


def fit_ridge(X,Y,manifest,fit_at, *,penalty=10,robust=False):
    """Training-only scaler; unpenalized intercept; mature labels mandatory.

    Caller must supply purged training folds and authenticated feature lineage.
    This routine does not invent OOF splits, cash-flow labels, or event history.
    """
    X=numeric_array(X,2); Y=numeric_array(Y,2); p=number(penalty)
    if not len(X) or len(X)!=len(Y) or p<=0:
        raise ValueError('paired training arrays and positive ridge penalty required')
    at=stamp(fit_at)
    if stamp(manifest['latest_label_received_at'])>at or stamp(manifest['maximum_feature_available_at'])>at:
        raise ValueError('future training feature/label')
    if not hash64(manifest['sha256']) or manifest.get('purged_folds') is not True:
        raise ValueError('training lineage and purge declaration required')
    means=np.median(X,axis=0) if robust else X.mean(axis=0)
    scales=np.median(np.abs(X-means),axis=0) if robust else X.std(axis=0,ddof=0)
    scales=np.where(scales>0,scales,1.0)
    Z=(X-means)/scales
    # Robust centering need not make columns mean-zero: center the design again
    # algebraically so the fitted intercept is truly unpenalized.
    zbar=Z.mean(axis=0); ybar=Y.mean(axis=0)
    Zc=Z-zbar; Yc=Y-ybar
    beta=np.linalg.solve(Zc.T@Zc+p*np.eye(X.shape[1]),Zc.T@Yc)
    intercept=ybar-zbar@beta
    return RidgeModel(means,scales,beta,intercept,dict(manifest))
