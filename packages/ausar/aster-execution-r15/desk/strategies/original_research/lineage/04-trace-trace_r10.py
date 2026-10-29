"""TRACE research mathematics and receipt-driven account primitives.

No broker API, download, desk installation or inferred historical fills. Canonical
Tensor B and point-in-time bar/fill evidence must be supplied externally. The
sealed design is underdetermined; bindings are registered in VARIANT_LEDGER.json.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import floor, sqrt
from typing import Sequence
from zoneinfo import ZoneInfo

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import logsumexp

ENGINE_SHA = '42fc461ef0327a3a7394f0a7cc37fadcc88816b0'
NY = ZoneInfo('America/New_York')
CLASSES = ('CONTINUE', 'FAIL', 'EXPIRE')


class ContractError(ValueError):
    pass


def finite(x, name='values'):
    out = np.asarray(x, dtype=float)
    if not np.isfinite(out).all():
        raise ContractError(name + ' contains unavailable/nonfinite data')
    return out


def aware(t):
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
        raise ContractError('explicit timezone required')
    return t


@dataclass(frozen=True)
class Bar:
    end: datetime
    available_at: datetime
    received_at: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    duration: float = 1.0
    session: str = ''
    slot: str = 'daily'
    final: bool = True
    origin: datetime | None = None

    def check(self, cutoff):
        for stamp in (self.end, self.available_at, self.received_at, cutoff): aware(stamp)
        if self.origin is not None and aware(self.origin) >= self.end:
            raise ContractError('bar origin must precede its end')
        if not self.end<=self.received_at<=self.available_at:
            raise ContractError('completed final bar requires end <= receipt <= usable time')
        if not self.final or max(self.end, self.available_at, self.received_at) > cutoff:
            raise ContractError('bar not final/available/received at cutoff')
        finite([self.open, self.high, self.low, self.close, self.volume, self.duration])
        if min(self.open,self.close,self.low) <= 0 or self.high < max(self.open,self.close,self.low):
            raise ContractError('invalid OHLC')
        if self.low > min(self.open,self.close) or self.volume < 0 or self.duration <= 0:
            raise ContractError('invalid bar volume/range/duration')


def prefix(bars: Sequence[Bar], cutoff):
    """Select historical end times first; future suffix cannot change old features."""
    aware(cutoff)
    selected = [bar for bar in bars if aware(bar.end) <= cutoff]
    if any(a.end >= b.end for a,b in zip(selected,selected[1:])):
        raise ContractError('duplicate or out-of-order completed bars')
    for bar in selected: bar.check(cutoff)
    return selected


def signed_area(q, p):
    """Centered open-path Levy area, straight segments; independently oracle-tested."""
    q,p = finite(q), finite(p)
    if q.ndim != 1 or q.shape != p.shape or len(q)<2:
        raise ContractError('two aligned 1D paths required')
    q,p = q-q[0],p-p[0]
    return float(0.5*np.sum(q[:-1]*np.diff(p)-p[:-1]*np.diff(q)))


def pressure(bars, denominators):
    den = finite(denominators, 'pre-window volume medians')
    if len(bars)!=len(den) or np.any(den<=0):
        raise ContractError('positive frozen volume median for every slot required')
    result=[]; zero=[]
    for bar,v in zip(bars,den):
        if bar.high == bar.low: result.append(0.0); zero.append(True)
        else:
            result.append(np.clip((2*bar.close-bar.high-bar.low)/(bar.high-bar.low)*bar.volume/v,-5,5))
            zero.append(False)
    return np.asarray(result), tuple(zero)


def volume_medians(prebars, window, count=20):
    """All samples strictly before window origin, per exact clock-slot identity."""
    if not window: raise ContractError('empty window')
    if window[0].origin is None: raise ContractError('explicit feature-window origin required')
    origin = aware(window[0].origin)
    if any(max(aware(bar.end),aware(bar.available_at),aware(bar.received_at)) >= origin for bar in prebars):
        raise ContractError('volume scale sees window/future data')
    values=[]
    for bar in window:
        matches=[b.volume for b in prebars if b.slot==bar.slot]
        if len(matches)<count: raise ContractError('insufficient exact same-slot prior volume')
        values.append(float(np.median(matches[-count:])))
    return finite(values)


@dataclass(frozen=True)
class FactorFit:
    coef: np.ndarray
    sigma: float
    alpha: float
    known_at: datetime
    maximum_input_end: datetime | None = None
    maximum_received_at: datetime | None = None


def fit_factors(stock, spy, sector, durations, known_at, alpha=1.0, sigma_floor=1e-6, *, maximum_input_end=None, maximum_received_at=None):
    """Ridge slopes, unpenalized duration-scaled intercept, pre-window only.

    Factor return scales are computed on the same pre-window fitting history.
    No centering of d_j: its coefficient has per-session/per-week return units.
    """
    y,m,s,d = map(finite,(stock,spy,sector,durations))
    if y.ndim!=1 or not (y.shape==m.shape==s.shape==d.shape) or len(y)<4 or np.any(d<=0):
        raise ContractError('aligned factor-fit returns and durations required')
    finite([alpha,sigma_floor])
    if alpha<0 or sigma_floor<=0: raise ContractError('invalid regularization/floor')
    if maximum_input_end is None or maximum_received_at is None:
        raise ContractError('factor input-end and last-receipt provenance required')
    if not aware(maximum_input_end)<=aware(maximum_received_at)<=aware(known_at):
        raise ContractError('factor fit precedes supplied input availability')
    x=np.column_stack((d,m,s)); scales=np.array([1.0,max(np.std(m),1e-8),max(np.std(s),1e-8)])
    z=x/scales; penalty=np.diag([0.,alpha,alpha])
    beta=np.linalg.lstsq(z.T@z+penalty,z.T@y,rcond=None)[0]/scales
    residual=y-x@beta
    sigma=max(float(np.std(residual/np.sqrt(d),ddof=1)),sigma_floor)
    return FactorFit(beta,sigma,float(alpha),aware(known_at),aware(maximum_input_end),aware(maximum_received_at))


def residual_path(bars, stock, spy, sector, medians, fit: FactorFit):
    if not bars or bars[0].origin is None or fit.maximum_input_end is None or fit.maximum_received_at is None:
        raise ContractError('explicit window origin and factor input/receipt clocks required')
    origin=aware(bars[0].origin)
    if max(aware(fit.known_at),aware(fit.maximum_input_end),aware(fit.maximum_received_at)) >= origin:
        raise ContractError('factor fit and inputs must predate window origin')
    finite(fit.coef)
    if np.asarray(fit.coef).shape!=(3,) or not np.isfinite(fit.sigma) or fit.sigma<=0:
        raise ContractError('invalid fitted factor dimensions/scale')
    y,m,s = map(finite,(stock,spy,sector))
    if not (len(bars)==len(y)==len(m)==len(s)):
        raise ContractError('unaligned window')
    d=finite([bar.duration for bar in bars]); e=y-np.column_stack((d,m,s))@fit.coef
    u,zero=pressure(bars,medians)
    p=np.r_[0,np.cumsum(e)/(fit.sigma*sqrt(float(np.sum(d))))]
    q=np.r_[0,np.cumsum(u)/sqrt(len(bars))]
    clock=np.r_[0,np.cumsum(d)/np.sum(d)]
    middle=len(bars)//2
    if not middle: raise ContractError('phase contrast requires >=2 bars')
    a=signed_area(q,p)
    contrast=signed_area(q[middle:],p[middle:])-signed_area(q[:middle+1],p[:middle+1])
    return {'p':p,'q':q,'u':u,'clock':clock,'area':a,'contrast':contrast,
            'clock_price_area':signed_area(clock,p),'clock_pressure_area':signed_area(clock,q),
            'zero_range':zero,'residual':e}


@dataclass(frozen=True)
class Phase:
    pressure_index: int | None
    acceptance_index: int | None
    state: str
    entry_gate: bool
    invalidated: bool


def phase_transition(closes,q,p,low,high):
    """First pressure and first two-close acceptance; invalidation through cutoff."""
    closes,q,p=map(finite,(closes,q,p))
    n=len(closes)
    if closes.ndim!=1 or n<2 or np.any(closes<=0) or low<=0:raise ContractError('positive completed phase-price series and box required')
    if q.shape!=(n+1,) or p.shape!=(n+1,) or not np.isfinite([low,high]).all() or high<low:
        raise ContractError('phase dimensions/frozen box invalid')
    established=next((i for i,c in enumerate(closes,1) if q[i]>=1 and abs(p[i])<=.5 and low<=c<=high),None)
    accepted=next((i for i in range(2,n+1) if closes[i-2]>high and closes[i-1]>high),None)
    invalid = established is not None and bool(np.any(closes[established-1:]<low))
    gate=established is not None and accepted is not None and established<accepted and accepted>=n-2 and not invalid
    if invalid: state='INVALIDATED'
    elif accepted is not None and (established is None or accepted<established): state='CHASE'
    elif gate: state='PRICE_ACCEPTED'
    elif established is not None: state='PRESSURE_ESTABLISHED'
    else: state='QUIET'
    return Phase(established,accepted,state,bool(gate),invalid)


def renewal_failure(closes, previous_closing_high, hourly_contrast, last_three_pressure):
    closes=finite(closes)
    finite([previous_closing_high,hourly_contrast])
    if len(closes)!=3 or len(last_three_pressure)!=3 or previous_closing_high<=0:
        raise ContractError('three completed sessions required')
    return bool(np.max(closes)<=previous_closing_high and float(hourly_contrast)<0 and np.sum(finite(last_three_pressure))<0)


@dataclass(frozen=True)
class Episode:
    id: str
    symbol: str
    start_session: int
    end_session: int
    week: str
    label: int | None
    net_return: float | None
    label_received_at: datetime
    fill_policy: str = 'TRACE_v1_receipt_policy'


def eligible_training(episodes, boundary_session, fit_at, gap=21):
    """Strict interval purge, full maturity gap, received outcomes, no-fill exclusion."""
    aware(fit_at)
    if type(boundary_session) is not int or type(gap) is not int or boundary_session<0 or gap<0:
        raise ContractError('training boundary/gap require nonnegative integer sessions')
    selected=[]
    for e in episodes:
        if e.end_session < e.start_session or e.label not in (None,0,1,2): raise ContractError('invalid episode interval/class')
        if e.fill_policy!='TRACE_v1_receipt_policy': raise ContractError('different fill-policy target population')
        if e.label is not None and e.end_session < boundary_session-gap and aware(e.label_received_at)<=fit_at:
            if e.net_return is None or not np.isfinite(e.net_return): raise ContractError('mature label missing net payoff')
            selected.append(e)
    return selected


class Standardizer:
    def fit(self,x):
        x=finite(x)
        if x.ndim!=2 or not len(x) or not x.shape[1]: raise ContractError('nonempty training matrix required')
        self.mean=x.mean(axis=0); self.scale=np.maximum(x.std(axis=0),1e-8); return self
    def transform(self,x):
        x=finite(x)
        if x.ndim!=2 or x.shape[1]!=len(self.mean):raise ContractError('training feature schema mismatch')
        return (x-self.mean)/self.scale


def ridge_fit(x,y,alpha):
    x,y=finite(x),finite(y)
    if x.ndim!=2 or y.ndim not in (1,2) or not len(x) or len(x)!=len(y) or not np.isfinite(alpha) or alpha<0:
        raise ContractError('aligned nonempty ridge training and finite penalty required')
    z=np.column_stack((np.ones(len(x)),x)); p=np.eye(z.shape[1])*alpha;p[0,0]=0
    return np.linalg.lstsq(z.T@z+p,z.T@y,rcond=None)[0]


class OrderProjection:
    """Train-only six ridge/MAD residuals plus exact two fixed scale products."""
    def fit(self,b,areas,alpha=1.,mad_floor=1e-6):
        b,areas=finite(b),finite(areas)
        if b.ndim!=2 or areas.shape!=(len(b),6) or not np.isfinite(alpha) or not np.isfinite(mad_floor) or alpha<0 or mad_floor<=0:
            raise ContractError('B plus exactly6 raw area/contrast terms required')
        self.standard=Standardizer().fit(b); z=self.standard.transform(b)
        self.coef=ridge_fit(z,areas,alpha)
        r=areas-np.column_stack((np.ones(len(z)),z))@self.coef
        self.mad=np.maximum(np.median(np.abs(r-np.median(r,axis=0)),axis=0),mad_floor)
        return self
    def transform(self,b,areas):
        b,areas=finite(b),finite(areas); z=self.standard.transform(b)
        if areas.shape!=(len(b),6): raise ContractError('six area/contrast columns required')
        h=(areas-np.column_stack((np.ones(len(z)),z))@self.coef)/self.mad
        return np.column_stack((h,h[:,0]*h[:,1],h[:,1]*h[:,2]))


class SoftmaxRidge:
    """Mean cross entropy +lambda/2 sum(W^2), intercept unpenalized."""
    def fit(self,x,y,alpha=1.):
        x=finite(x); raw_y=np.asarray(y)
        if raw_y.ndim!=1 or not np.issubdtype(raw_y.dtype,np.integer):raise ContractError('integer class labels required')
        y=raw_y.astype(int)
        if x.ndim!=2 or len(x)!=len(y) or set(y)!={0,1,2} or not np.isfinite(alpha) or alpha<0:
            raise ContractError('all3 class labels and aligned training rows required')
        self.scaler=Standardizer().fit(x); z=np.column_stack((np.ones(len(x)),self.scaler.transform(x)))
        def objective(flat):
            w=flat.reshape(z.shape[1],3); logits=z@w; logp=logits-logsumexp(logits,axis=1)[:,None]
            loss=-np.mean(logp[np.arange(len(y)),y])+alpha/2*np.sum(w[1:]**2)
            prob=np.exp(logp); prob[np.arange(len(y)),y]-=1
            grad=z.T@prob/len(y); grad[1:]+=alpha*w[1:]
            return loss,grad.ravel()
        fit=minimize(objective,np.zeros(z.shape[1]*3),jac=True,method='L-BFGS-B',options={'maxiter':2000,'ftol':1e-12,'gtol':1e-9})
        if not fit.success: raise ContractError('logistic optimizer did not converge')
        self.coef=fit.x.reshape(z.shape[1],3); self.alpha=alpha; self.temperature=1.; return self
    def logits(self,x):
        z=np.column_stack((np.ones(len(x)),self.scaler.transform(x))); return z@self.coef
    def scores(self,x):
        logit=self.logits(x)/self.temperature; return np.exp(logit-logsumexp(logit,axis=1)[:,None])
    def calibrate(self,x,y):
        raw_y=np.asarray(y)
        if raw_y.ndim!=1 or not len(raw_y) or not np.issubdtype(raw_y.dtype,np.integer):raise ContractError('nonempty integer calibration labels required')
        y=raw_y.astype(int); logits=self.logits(x)
        if len(y)!=len(x) or any(k not in (0,1,2) for k in y): raise ContractError('invalid calibration labels')
        def loss(logt):
            value=logits/np.exp(logt); return float(np.mean(logsumexp(value,axis=1)-value[np.arange(len(y)),y]))
        fit=minimize_scalar(loss,bounds=(np.log(.05),np.log(20.)),method='bounded')
        if not fit.success: raise ContractError('temperature calibration failed')
        self.temperature=float(np.exp(fit.x)); return self


class TraceModel:
    def fit(self,b,areas,episodes,fit_at,boundary_session,alpha=1.):
        selected=eligible_training(episodes,boundary_session,fit_at)
        if len(selected)!=len(episodes): raise ContractError('caller supplied unpurged/unmatured/no-fill training rows')
        if len(episodes)!=len(b): raise ContractError('episode feature alignment mismatch')
        self.projection=OrderProjection().fit(b,areas,alpha)
        x=np.column_stack((b,self.projection.transform(b,areas)))
        self.classifier=SoftmaxRidge().fit(x,[e.label for e in episodes],alpha)
        self.payoff=np.array([np.mean([e.net_return for e in episodes if e.label==k]) for k in range(3)])
        self.known_at=aware(fit_at);self.feature_width=np.asarray(b).shape[1];return self
    def expected_value(self,b,areas,decision_at):
        if aware(decision_at)<=self.known_at: raise ContractError('checkpoint not known before decision')
        x=np.column_stack((b,self.projection.transform(b,areas)))
        score=self.classifier.scores(x);return score@self.payoff,score


def week_bootstrap_expected(b,areas,episodes,query_b,query_areas,fit_at,boundary_session,alpha=1.,draws=200,seed=20261008):
    """Jointly refit train-only projection/logistic/payoffs by whole calendar week.

    This primitive uses temperature1 unless separate matured calibration is
    explicitly supplied to an external pipeline. It returns uncalibrated scores,
    not canonical entry probabilities or guaranteed profit.
    """
    groups={week:np.array([i for i,e in enumerate(episodes) if e.week==week]) for week in sorted({e.week for e in episodes})}
    if len(groups)<5 or draws<20: raise ContractError('bootstrap requires >=5weeks and20draws')
    rng=np.random.default_rng(seed); weeks=list(groups); estimates=[]; omitted=0
    for _ in range(draws):
        sampled=rng.choice(weeks,len(weeks),replace=True); idx=np.concatenate([groups[w] for w in sampled])
        if set(episodes[i].label for i in idx)!={0,1,2}: omitted+=1;continue
        model=TraceModel().fit(np.asarray(b)[idx],np.asarray(areas)[idx],[episodes[i] for i in idx],fit_at,boundary_session,alpha)
        estimates.append(model.expected_value(query_b,query_areas,fit_at+timedelta(microseconds=1))[0])
    if len(estimates)<.9*draws: raise ContractError('bootstrap class support collapsed')
    return np.quantile(np.asarray(estimates),.1,axis=0),{'accepted_draws':len(estimates),'omitted_draws':omitted,'temperature':'uncalibrated1'}


def arm(phase: Phase, lower_value, scores, calibrated=False):
    scores=finite(scores)
    if not np.isfinite(lower_value):raise ContractError('finite conservative value required')
    if scores.shape!=(3,) or not np.isclose(scores.sum(),1) or np.any(scores<0): raise ContractError('invalid class score simplex')
    if not calibrated: raise ContractError('scores lack separate out-of-sample calibration support')
    return bool(phase.entry_gate and lower_value>.0025 and scores[0]-scores[1]>=.15)


@dataclass(frozen=True)
class Quote:
    timestamp: datetime
    received_at: datetime
    bid: float
    ask: float
    ask_size: int
    minute_observed_volume: int
    halted: bool=False
    event_timestamp: datetime | None=None

    def check(self):
        aware(self.timestamp);aware(self.received_at)
        if self.received_at>self.timestamp or self.bid<=0 or self.ask<self.bid or not np.isfinite([self.bid,self.ask]).all():
            raise ContractError('quote unavailable/stale/crossed')
        if self.event_timestamp is not None:
            if aware(self.event_timestamp)>self.received_at or (self.timestamp-self.event_timestamp).total_seconds()>2:
                raise ContractError('quote event is future or stale beyond registered2seconds')
        if type(self.ask_size) is not int or type(self.minute_observed_volume) is not int or self.ask_size<0 or self.minute_observed_volume<0:
            raise ContractError('displayed size/observed volume require nonnegative integer shares')


@dataclass(frozen=True)
class Fill:
    id: str
    side: str
    shares: int
    price: float
    timestamp: datetime
    fee: float=0.
    evidence: str='SYNTHETIC_TEST_FIXTURE'


@dataclass
class Position:
    symbol: str
    first_price: float
    atr: float
    shares: int
    total_cost: float
    stop: float
    target: float
    entry_session: int = 0
    opened_at: datetime | None=None
    negative_value_cutoffs: int=0
    pending_exit: str | None=None
    pending_exit_at: datetime | None=None
    closed: bool=False
    last_value_cutoff: datetime | None=None
    last_value_lower: float | None=None
    @property
    def average_cost(self): return self.total_cost/self.shares if self.shares else 0.


class ReceiptAccount:
    """State/ledger books only supplied receipts; never infers a limit-touch fill."""
    def __init__(self,capital=1_000_000.,mode='SYNTHETIC_TEST_FIXTURE',calendar=()):
        if not np.isfinite(capital) or capital<=0: raise ContractError('finite positive capital required')
        self.initial=self.cash=float(capital);self.mode=mode;self.position=None;self.fills={};self.ledger=[]
        self.attempt=None;self.minute_used={};self.last_volume={};self.closed_episodes=[]
        self.calendar={day:index for index,day in enumerate(calendar)};self.last_exit_session=None
        if len(self.calendar)!=len(calendar) or list(calendar)!=sorted(calendar): raise ContractError('unique ordered exchange calendar required')
        self.last_fill_at=None;self.last_quote_at=None;self.sell_request=None;self.action_receipts={};self.latest_quote=None
    def plan(self,symbol,close,atr,nav,adv_shares,capacity_shares,sector_remaining_usd,session_date):
        if self.position or self.attempt: raise ContractError('no pyramiding/concurrent single-name attempt')
        finite([close,atr,nav,adv_shares,capacity_shares,sector_remaining_usd])
        if min(close,atr,nav,adv_shares)<=0 or min(capacity_shares,sector_remaining_usd)<0: raise ContractError('positive sizing inputs required')
        if session_date not in self.calendar: raise ContractError('explicit exchange-session calendar required')
        if self.last_exit_session is not None and self.calendar[session_date]<=self.last_exit_session+20:
            raise ContractError('twenty completed post-exit cooldown sessions required')
        shares=floor(min(.0025*nav/(1.5*atr),.08*nav/close,.005*adv_shares,capacity_shares,sector_remaining_usd/close,self.cash/close))
        if shares*close<1000: return 0
        self.attempt={'symbol':symbol,'shares':shares,'remaining':shares,'limit':close+.5*atr,'atr':atr,'date':session_date,'first':None,'next_request':0}
        return shares
    def quote(self,q:Quote):
        q.check();local=q.timestamp.astimezone(NY); minute=local.replace(second=0,microsecond=0)
        if self.last_quote_at is not None and q.timestamp<self.last_quote_at: raise ContractError('out-of-order quote processing')
        if self.last_fill_at is not None and q.timestamp<self.last_fill_at: raise ContractError('quote precedes already received fill')
        if self.latest_quote is not None and q.timestamp==self.latest_quote.timestamp and q!=self.latest_quote:
            raise ContractError('immutable same-time supporting quote revised')
        previous=self.last_volume.get(minute,0)
        if q.minute_observed_volume<previous: raise ContractError('observed minute volume decreased')
        if local.date().isoformat() not in self.calendar: raise ContractError('quote missing declared exchange session')
        if self.mode!='SYNTHETIC_TEST_FIXTURE' and q.event_timestamp is None:
            raise ContractError('nonfixture quote requires separate event/receipt provenance')
        self.last_quote_at=q.timestamp;self.latest_quote=q
        self.last_volume[minute]=q.minute_observed_volume
        if q.halted:
            self.attempt=None
            return {'action':'HALT_ABSTAIN','partial_preserved':self.position is not None}
        if self.position and not self.position.closed:
            if q.bid<=self.position.stop: self.position.pending_exit='STOP'
            elif q.bid>=self.position.target: self.position.pending_exit='TARGET'
            due=self.position.pending_exit in {'STOP','TARGET'} or (
                self.position.pending_exit_at is not None and q.timestamp>=self.position.pending_exit_at)
            if due:
                self.attempt=None;self.sell_request={'at':q.timestamp,'shares':self.position.shares,'reason':self.position.pending_exit};return {'action':'SELL_REQUEST','shares':self.position.shares,'reason':self.position.pending_exit,'observed_bid':q.bid}
        if not self.attempt: return {'action':'NONE'}
        if local.date().isoformat()!=self.attempt['date'] or local.time().hour!=9 or not 35<=local.minute<45:
            if local.date().isoformat()>=self.attempt['date'] and (local.hour>9 or local.minute>=45): self.attempt=None
            return {'action':'NONE'}
        spread=(q.ask-q.bid)/((q.ask+q.bid)/2)*10000
        if q.halted or spread>15 or q.ask>self.attempt['limit']:
            self.attempt=None;return {'action':'CANCEL_REMAINDER','partial_preserved':self.position is not None}
        shares=min(self.attempt['remaining'],q.ask_size,max(0,floor(.01*q.minute_observed_volume)-self.minute_used.get(minute,0)),floor(self.cash/q.ask))
        self.attempt['next_request']=shares
        return {'action':'BUY_REQUEST' if shares else 'NONE','shares':shares,'limit':self.attempt['limit'],'observed_ask':q.ask,'minute':minute}
    def book(self,fill:Fill,q:Quote):
        q.check()
        if fill.id in self.fills:
            if self.fills[fill.id]!=fill: raise ContractError('immutable fill receipt revised')
            return False
        if fill.evidence!=self.mode or not fill.id or type(fill.shares) is not int or fill.shares<=0 or fill.price<=0 or fill.fee<0 or not np.isfinite([fill.price,fill.fee]).all():
            raise ContractError('invalid receipt/evidence')
        if self.latest_quote is None or q!=self.latest_quote:
            raise ContractError('fill must reference the latest processed supporting quote')
        if q.halted: raise ContractError('supporting halted quote cannot establish executable fill')
        if self.mode!='SYNTHETIC_TEST_FIXTURE' and q.event_timestamp is None:
            raise ContractError('nonfixture fill requires separate supporting quote event provenance')
        if aware(fill.timestamp)<q.timestamp: raise ContractError('fill precedes supporting quote')
        if self.last_fill_at is not None and fill.timestamp<self.last_fill_at: raise ContractError('out-of-order fill receipt')
        if self.last_quote_at is not None and fill.timestamp<self.last_quote_at: raise ContractError('fill precedes latest processed quote; delayed receipt unsupported')
        if fill.timestamp.astimezone(NY).replace(second=0,microsecond=0)!=q.timestamp.astimezone(NY).replace(second=0,microsecond=0):
            raise ContractError('quote/fill minute mismatch: participation evidence absent')
        if fill.side=='BUY':
            if not self.attempt or fill.shares>self.attempt['next_request'] or fill.price>self.attempt['limit']:
                raise ContractError('receipt violates requested size/limit')
            local=fill.timestamp.astimezone(NY)
            if local.date().isoformat()!=self.attempt['date'] or local.hour!=9 or not 35<=local.minute<45:
                raise ContractError('buy receipt outside acquisition window')
            minute=local.replace(second=0,microsecond=0)
            if q.minute_observed_volume<self.last_volume.get(minute,0):
                raise ContractError('fill support revises observed minute volume downward')
            supported=min(q.ask_size,max(0,floor(.01*q.minute_observed_volume)-self.minute_used.get(minute,0)))
            if fill.shares>supported:
                raise ContractError('receipt exceeds supporting observed participation/displayed size')
            debit=fill.shares*fill.price+fill.fee
            if debit>self.cash+1e-9: raise ContractError('cash violation')
            self.cash-=debit; local=q.timestamp.astimezone(NY); minute=local.replace(second=0,microsecond=0)
            self.minute_used[minute]=self.minute_used.get(minute,0)+fill.shares
            if self.position is None:
                atr=self.attempt['atr'];self.position=Position(self.attempt['symbol'],fill.price,atr,fill.shares,fill.shares*fill.price,fill.price-1.5*atr,fill.price+3*atr,self.calendar[self.attempt['date']])
                self.position.opened_at=fill.timestamp
                self.attempt['first']=fill.price;self.attempt['limit']=fill.price
            else:
                self.position.shares+=fill.shares;self.position.total_cost+=fill.shares*fill.price
            self.attempt['remaining']-=fill.shares;self.attempt['next_request']=0
            if self.attempt['remaining']==0: self.attempt=None
        elif fill.side=='SELL':
            if self.sell_request is None or self.sell_request['at']!=q.timestamp or fill.shares>self.sell_request['shares']:
                raise ContractError('sell receipt requires matching outstanding exit request')
            if self.cash+fill.shares*fill.price-fill.fee < -1e-9:
                raise ContractError('sell fee exceeds funded proceeds and cash')
            if self.position is None or fill.shares>self.position.shares: raise ContractError('sell absent/excess shares')
            day=fill.timestamp.astimezone(NY).date().isoformat()
            if day not in self.calendar: raise ContractError('exit receipt missing calendar session')
            self.cash+=fill.shares*fill.price-fill.fee
            self.sell_request['shares']-=fill.shares
            average=self.position.average_cost;self.position.total_cost-=average*fill.shares;self.position.shares-=fill.shares
            if self.position.shares==0:
                self.last_exit_session=self.calendar[day]
                self.position.closed=True;self.closed_episodes.append(self.position);self.position=None;self.attempt=None
        else: raise ContractError('invalid receipt side')
        self.fills[fill.id]=fill;self.ledger.append(fill);self.last_fill_at=fill.timestamp;return True
    def daily_value(self,lower_bound,cutoff_at,next_window_at):
        if not self.position: return
        if not np.isfinite(lower_bound): raise ContractError('missing retention estimate')
        cutoff_at,next_window_at=aware(cutoff_at),aware(next_window_at)
        cutoff_local=cutoff_at.astimezone(NY)
        if cutoff_local!=cutoff_local.replace(hour=16,minute=10,second=0,microsecond=0):
            raise ContractError('one fixed16:10 economic cutoff per exchange date required')
        local=next_window_at.astimezone(NY)
        if next_window_at<=cutoff_at or local.hour!=9 or local.minute!=35:
            raise ContractError('next actual exchange morning window required')
        day=cutoff_at.astimezone(NY).date().isoformat()
        if day not in self.calendar: raise ContractError('cutoff missing exchange session')
        next_day=local.date().isoformat()
        if next_day not in self.calendar or self.calendar[next_day]!=self.calendar[day]+1 or local.weekday()>4:
            raise ContractError('exit must use actual immediately next exchange session')
        if self.position.opened_at is not None and cutoff_at<=self.position.opened_at: raise ContractError('cutoff precedes position opening')
        previous=self.position.last_value_cutoff
        if previous is not None:
            if cutoff_at<previous: raise ContractError('out-of-order completed daily cutoff')
            if cutoff_at==previous:
                if self.position.last_value_lower!=lower_bound: raise ContractError('immutable completed cutoff revised')
                return False
        if self.position.pending_exit in {'STOP','TARGET'}: return
        consecutive=previous is not None and self.calendar[previous.astimezone(NY).date().isoformat()]+1==self.calendar[day]
        self.position.negative_value_cutoffs=(self.position.negative_value_cutoffs+1 if consecutive else 1) if lower_bound<0 else 0
        self.position.last_value_cutoff=cutoff_at;self.position.last_value_lower=lower_bound
        if self.calendar[day]-self.position.entry_session+1>=20:
            self.position.pending_exit='AGE_NEXT_WINDOW';self.position.pending_exit_at=next_window_at
        elif self.position.negative_value_cutoffs>=2:
            self.position.pending_exit='VALUE_NEXT_WINDOW';self.position.pending_exit_at=next_window_at
        return True
    def mark(self,bid):
        if bid<=0 or not np.isfinite(bid): raise ContractError('invalid executable mark')
        return self.cash+(self.position.shares*bid if self.position else 0.)
    def _action(self,action_id,payload,effective_at,known_at,applied_at):
        if not isinstance(action_id,str) or not action_id:raise ContractError('corporate action immutable identity required')
        effective_at,known_at,applied_at=map(aware,(effective_at,known_at,applied_at))
        if max(effective_at,known_at)>applied_at:raise ContractError('corporate action applied before effect or receipt')
        record=(payload,effective_at.isoformat(),known_at.isoformat())
        if action_id in self.action_receipts:
            if self.action_receipts[action_id]!=record:raise ContractError('corporate action receipt revised')
            return None
        return record
    def dividend(self,per_share,*,action_id,effective_at,known_at,applied_at,entitlement_shares):
        if per_share<0 or not np.isfinite(per_share) or type(entitlement_shares) is not int or entitlement_shares<0:
            raise ContractError('explicit nonnegative frozen dividend entitlement required')
        record=self._action(action_id,('DIVIDEND',float(per_share),entitlement_shares),effective_at,known_at,applied_at)
        if record is None:return False
        self.cash+=entitlement_shares*per_share;self.action_receipts[action_id]=record;return True
    def split(self,ratio,*,action_id,effective_at,known_at,applied_at):
        if ratio<=0 or not np.isfinite(ratio):raise ContractError('invalid split')
        record=self._action(action_id,('SPLIT',float(ratio)),effective_at,known_at,applied_at)
        if record is None:return False
        if self.attempt:raise ContractError('split during acquisition requires cancel/replan receipt')
        if self.position:
            qty=self.position.shares*ratio
            if not np.isclose(qty,round(qty),atol=1e-12,rtol=0):raise ContractError('fractional cash-in-lieu receipt required')
            self.position.shares=int(round(qty));self.position.first_price/=ratio;self.position.atr/=ratio
            self.position.stop/=ratio;self.position.target/=ratio
            self.sell_request=None
        self.action_receipts[action_id]=record;return True


class RemainingValueModel:
    """Fixed ridge original-barrier minus next-window-liquidation payoffs.

    Labels must be measured on the original fixed policy, never optimized exits.
    Episode grouping is mandatory for subsequent resampling, not random rows.
    """
    def fit(self,x,hold_net,sell_next_net,episodes,fit_at,boundary_session,alpha=1.):
        if len(eligible_training(episodes,boundary_session,fit_at))!=len(episodes):
            raise ContractError('unmatured/overlapping retention observations')
        x,hold,sell=map(finite,(x,hold_net,sell_next_net))
        if x.ndim!=2 or len(x)!=len(hold) or hold.shape!=sell.shape or len(x)!=len(episodes):
            raise ContractError('retention labels/features not aligned')
        self.standard=Standardizer().fit(x);self.coef=ridge_fit(self.standard.transform(x),hold-sell,alpha)
        self.known_at=aware(fit_at);return self
    def predict(self,x,decision_at):
        if aware(decision_at)<=self.known_at: raise ContractError('future retention checkpoint')
        z=self.standard.transform(x);return np.column_stack((np.ones(len(z)),z))@self.coef


def require_exact_tensor_input(engine_sha,profile_sha,names,values):
    if engine_sha!=ENGINE_SHA or not isinstance(profile_sha,str) or len(profile_sha)!=64:
        raise ContractError('exact v690 source/profile provenance required')
    if len(set(names))!=len(names) or len(names)!=len(values) or not names:
        raise ContractError('fixed numeric B schema required')
    # This verifies identifiers/shape only. External parity/recipe evidence must
    # establish formula correctness; a caller cannot turn an approximation into
    # Tensor merely by providing matching hashes.
    return finite(values)


def portfolio_order_shares(nav,cash,price,atr,adv_shares,capacity_shares,
                           existing_names,sector_value,gross_value):
    """Shared-account cap gate; caller supplies then-known held/reserved values."""
    finite([nav,cash,price,atr,adv_shares,capacity_shares,existing_names,sector_value,gross_value])
    if min(nav,price,atr,adv_shares)<=0 or min(cash,capacity_shares,sector_value,gross_value,existing_names)<0:
        raise ContractError('invalid account/capacity inputs')
    if existing_names>=15: return 0
    quantity=min(.0025*nav/(1.5*atr),.08*nav/price,.005*adv_shares,capacity_shares,
                 max(0,.25*nav-sector_value)/price,max(0,nav-gross_value)/price,cash/price)
    shares=max(0,floor(quantity))
    return shares if shares*price>=1000 else 0


def covariance_scale(weights,covariance_daily,limit=.20):
    """Scale ALL holdings, not only proposed trade; reduction receipts still needed."""
    w,c=finite(weights),finite(covariance_daily)
    if c.shape!=(len(w),len(w)) or np.any(w<0) or w.sum()>1+1e-12 or limit<=0:
        raise ContractError('invalid long-only covariance/exposure')
    if not np.allclose(c,c.T,atol=1e-12) or np.min(np.linalg.eigvalsh(c)) < -1e-12:
        raise ContractError('covariance must be symmetric positive semidefinite')
    sigma=sqrt(max(0,float(w@c@w))*252)
    scale=min(1,limit/sigma) if sigma else 1.
    return w*scale,{'predicted_vol_before':sigma,'scale':scale,'reductions_are_requests_not_fills':True}


def modeled_side_cost(notional,quoted_spread_bp,sigma_day,shares,adv_shares,fee=0.,eta=None,floor_bp=15.):
    finite([notional,quoted_spread_bp,sigma_day,shares,adv_shares,fee,floor_bp]+([] if eta is None else [eta]))
    if min(notional,adv_shares)<=0 or min(quoted_spread_bp,sigma_day,shares,fee,floor_bp)<0:
        raise ContractError('invalid cost/capacity units')
    impact=0. if eta is None else eta*sigma_day*sqrt(shares/adv_shares)
    if impact<0: raise ContractError('negative calibrated impact')
    cost=fee+notional*(quoted_spread_bp/20000+impact)
    return max(cost,notional*floor_bp/10000)


def conservative_ohlc_label(open_price,high,low,stop,target):
    """NONCANONICAL sensitivity only: no receipt, queue or intrabar chronology."""
    if low>high or stop>=target: raise ContractError('invalid barrier/bar')
    if open_price<=stop: return 'FAIL',open_price,False
    if low<=stop: return 'FAIL',stop,high>=target
    if high>=target: return 'CONTINUE',target,False
    return None,None,False

R10_VERSION="r10-trace-necessary-repairs-v1"
CANONICAL_FINANCIAL_QUALIFICATION=False
DEPLOYMENT_APPROVED=False
