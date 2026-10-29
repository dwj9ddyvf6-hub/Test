"""Causal, bounded market-context measurements; no orders, forecasts or risk uplift.

Definitions and primary sources are documented in research/enhancement_v03/
awareness_research.md. All inference thresholds are research hypotheses. Quote
sizes must already be normalized executable units. Alpaca's dated changelog
specifies CTA/UTP share units from 2025-11-03; older/generic schemas can differ.
The adapter must declare feed/date-appropriate units and any per-symbol lot
conversion explicitly, never assume a universal multiplier of 100. No
minimum historical quote date is assumed: only explicit event/receipt timestamps
and the requested as_of determine availability/freshness.

Only the configured intraday timeframe is consumed. Bars must be complete,
nonoverlapping, regular-session observations from a consistent lineage. Later
revisions require replay. HLC3 volume weighting is explicitly a bar VWAP proxy.
Missing optional data stays unknown; this module never vetoes or sizes a trade.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from bisect import bisect_right
from datetime import datetime, timedelta
from math import log, sqrt
from statistics import median
import json
import re

from .models import (Observation, Quote, Reference, Session, aware, number,
                     jsonable, stable_id, observation_from_dict, quote_from_dict,
                     session_from_dict)

METHOD_VERSION = 'causal-awareness-1'


class FrozenDict(dict):
    """JSON-compatible read-only mapping for detached snapshot values."""
    def _immutable(self, *args, **kwargs): raise TypeError('immutable awareness snapshot')
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable
    def __deepcopy__(self, memo): return self


def _freeze(value):
    if isinstance(value, dict): return FrozenDict((k,_freeze(v)) for k,v in value.items())
    if isinstance(value,(tuple,list)): return tuple(_freeze(v) for v in value)
    return value


def _seconds(timeframe: str) -> int:
    match = re.fullmatch(r'([1-9][0-9]*)(s|m|H)',timeframe)
    if not match: raise ValueError('awareness requires an explicit intraday timeframe')
    return int(match[1])*{'s':1,'m':60,'H':3600}[match[2]]


@dataclass(frozen=True)
class AwarenessConfig:
    execution_timeframe: str = '10m'
    rolling_bars: int = 20
    min_returns: int = 12
    opening_minutes: int = 30
    baseline_sessions: int = 20
    min_baseline_sessions: int = 5
    max_symbols: int = 128
    max_sessions: int = 24
    max_calendar_entries: int = 4096
    max_bars_per_session: int = 512
    max_quotes_per_symbol: int = 64
    max_event_calendars: int = 4096
    max_events_per_calendar: int = 256
    max_bar_age_seconds: float = 1200.
    max_quote_age_seconds: float = 5.
    max_calendar_age_seconds: float = 86400.
    wide_spread_bps: float = 25.
    directional_efficiency: float = .6
    choppy_efficiency: float = .25
    elevated_rvol: float = 1.5
    quiet_rvol: float = .7

    def __post_init__(self):
        _seconds(self.execution_timeframe)
        integers = (self.rolling_bars,self.min_returns,self.opening_minutes,self.baseline_sessions,
                    self.min_baseline_sessions,self.max_symbols,self.max_sessions,self.max_calendar_entries,self.max_bars_per_session,
                    self.max_quotes_per_symbol,self.max_event_calendars,self.max_events_per_calendar)
        if any(isinstance(v,bool) or not isinstance(v,int) or v<1 for v in integers):
            raise ValueError('positive integer awareness bounds required')
        if not 2 <= self.min_returns <= self.rolling_bars < self.max_bars_per_session:
            raise ValueError('invalid awareness rolling window')
        if not self.min_baseline_sessions <= self.baseline_sessions < self.max_sessions:
            raise ValueError('insufficient baseline retention')
        if self.max_calendar_entries<self.max_sessions: raise ValueError('insufficient calendar capacity')
        values = (self.max_bar_age_seconds,self.max_quote_age_seconds,self.max_calendar_age_seconds,
                  self.wide_spread_bps,self.directional_efficiency,self.choppy_efficiency,
                  self.elevated_rvol,self.quiet_rvol)
        number(*values)
        if min(self.max_bar_age_seconds,self.max_quote_age_seconds,self.max_calendar_age_seconds,self.wide_spread_bps)<=0:
            raise ValueError('positive awareness ages/spread required')
        if not 0 <= self.choppy_efficiency < self.directional_efficiency <= 1:
            raise ValueError('invalid efficiency labels')
        if not 0 < self.quiet_rvol < 1 < self.elevated_rvol:
            raise ValueError('invalid participation labels')

    @property
    def fingerprint(self):
        return stable_id(METHOD_VERSION,json.dumps(asdict(self),sort_keys=True))


@dataclass(frozen=True)
class ScheduledEvent:
    event_id: str
    category: str
    scheduled_at: datetime
    available_at: datetime
    blackout_before_seconds: float = 300.
    blackout_after_seconds: float = 300.
    symbols: tuple[str,...] = ()  # Empty means the calendar's declared scope.
    source: str = 'caller'

    def __post_init__(self):
        object.__setattr__(self,'symbols',tuple(self.symbols))

    def validate(self):
        aware(self.scheduled_at); aware(self.available_at)
        number(self.blackout_before_seconds,self.blackout_after_seconds)
        if not self.event_id or not self.category or not self.source or min(self.blackout_before_seconds,self.blackout_after_seconds)<0:
            raise ValueError('invalid scheduled event')
        try:
            self.scheduled_at-timedelta(seconds=self.blackout_before_seconds)
            self.scheduled_at+timedelta(seconds=self.blackout_after_seconds)
        except OverflowError as exc:
            raise ValueError('scheduled blackout exceeds datetime range') from exc
        if len(set(self.symbols)) != len(self.symbols) or any(not isinstance(x,str) or not x for x in self.symbols):
            raise ValueError('invalid event symbol scope')


@dataclass(frozen=True)
class EventCalendar:
    calendar_id: str
    available_at: datetime
    coverage_start: datetime
    coverage_end: datetime
    events: tuple[ScheduledEvent,...] = ()
    symbols: tuple[str,...] = ()  # Empty is an explicitly global calendar.
    source: str = 'caller'
    max_blackout_seconds: float = 300.

    def __post_init__(self):
        object.__setattr__(self,'symbols',tuple(self.symbols))
        object.__setattr__(self,'events',tuple(self.events))

    def validate(self):
        for at in (self.available_at,self.coverage_start,self.coverage_end): aware(at)
        if not self.calendar_id or not self.source or self.coverage_start>=self.coverage_end:
            raise ValueError('invalid event calendar')
        number(self.max_blackout_seconds)
        if self.max_blackout_seconds<0: raise ValueError('invalid calendar blackout bound')
        try:
            self.coverage_start+timedelta(seconds=self.max_blackout_seconds)
            self.coverage_end-timedelta(seconds=self.max_blackout_seconds)
        except OverflowError as exc:
            raise ValueError('calendar blackout bound exceeds datetime range') from exc
        if len(set(self.symbols)) != len(self.symbols) or any(not isinstance(x,str) or not x for x in self.symbols):
            raise ValueError('invalid calendar symbol scope')
        if len({e.event_id for e in self.events}) != len(self.events): raise ValueError('duplicate calendar event')
        for event in self.events:
            event.validate()
            if event.available_at>self.available_at: raise ValueError('event unavailable to calendar version')
            if self.symbols and not set(event.symbols).issubset(self.symbols):
                raise ValueError('event scope outside parent calendar')
            if max(event.blackout_before_seconds,event.blackout_after_seconds)>self.max_blackout_seconds:
                raise ValueError('event exceeds declared calendar blackout bound')
            if not self.coverage_start <= event.scheduled_at <= self.coverage_end:
                raise ValueError('event outside declared calendar coverage')


def event_calendar_from_dict(data: dict) -> EventCalendar:
    """Strict JSON decoder; ISO8601 timestamps, second-valued blackout durations."""
    values = dict(data)
    values['events'] = tuple(ScheduledEvent(**{**event,
        'scheduled_at':datetime.fromisoformat(event['scheduled_at']),
        'available_at':datetime.fromisoformat(event['available_at']),
        'symbols':tuple(event.get('symbols',()))}) for event in values.get('events',()))
    for name in ('available_at','coverage_start','coverage_end'):
        values[name] = datetime.fromisoformat(values[name])
    values['symbols'] = tuple(values.get('symbols',()))
    result = EventCalendar(**values); result.validate()
    return result


def event_calendar_to_dict(calendar: EventCalendar) -> dict:
    calendar.validate()
    return jsonable(calendar)


@dataclass(frozen=True)
class AwarenessSnapshot:
    symbol: str
    as_of: datetime
    latest_bar_end: datetime | None
    latest_available_at: datetime | None
    observed: FrozenDict
    inferred: FrozenDict
    quality: FrozenDict
    issues: tuple[str,...]
    version: str = METHOD_VERSION

    def to_dict(self) -> dict:
        return jsonable(self)


class AwarenessBook:
    def __init__(self, config: AwarenessConfig | None = None):
        self.config = config or AwarenessConfig()
        self._sessions: list[Session] = []
        self._session_opens: list[datetime] = []
        self._bars: dict[str,list[Observation]] = {}
        self._quotes: dict[str,list[Quote]] = {}
        self._calendars: list[EventCalendar] = []

    def register_session(self, session: Session) -> bool:
        session.validate()
        for old in self._sessions:
            if old==session: return False
            if old.session_id==session.session_id or max(old.open,session.open)<min(old.close,session.close):
                raise ValueError('conflicting awareness session')
        if len(self._sessions)>=self.config.max_calendar_entries:
            raise ValueError('awareness calendar capacity exceeded')
        # Future schedules must not evict observations used by an earlier replay.
        self._sessions = sorted((*self._sessions,session),key=lambda s:s.open)
        self._session_opens = [s.open for s in self._sessions]
        return True

    def _capacity(self, symbol):
        if symbol not in set(self._bars)|set(self._quotes) and len(set(self._bars)|set(self._quotes))>=self.config.max_symbols:
            raise ValueError('awareness symbol capacity exceeded')

    @staticmethod
    def _lineage(observation):
        return (observation.provider,observation.venue,observation.session_policy,observation.adjustment)

    def update(self, observation: Observation) -> bool:
        observation.validate()
        if observation.timeframe!=self.config.execution_timeframe: return False
        self._capacity(observation.symbol)
        b = observation.bar
        index = bisect_right(self._session_opens,b.start)-1
        session = self._sessions[index] if index>=0 else None
        if session is None or not session.open<=b.start<b.end<=session.close:
            raise ValueError('awareness bar needs a registered containing session')
        if observation.session_policy!='regular': raise ValueError('awareness requires regular-session bars')
        if (b.end-b.start).total_seconds()!=_seconds(self.config.execution_timeframe):
            raise ValueError('awareness bar duration mismatch')
        rows = self._bars.get(observation.symbol,[])
        if rows and b.start<rows[-1].bar.end:
            for old in rows:
                if old.bar.start==b.start or old.bar.end==b.end:
                    if old==observation: return False
                    raise ValueError('awareness revision/conflict requires replay')
        if rows:
            if b.start<rows[-1].bar.end or observation.available_at<rows[-1].available_at:
                raise ValueError('out-of-order awareness observation')
            if self._lineage(rows[-1])!=self._lineage(observation):
                raise ValueError('awareness lineage changed; replay separately')
        if sum(session.open<=o.bar.start<session.close for o in rows)>=self.config.max_bars_per_session:
            raise ValueError('awareness session capacity exceeded')
        floor = self._sessions[max(0,index-self.config.max_sessions+1)].open
        self._bars[observation.symbol] = [o for o in rows if o.bar.start>=floor]+[observation]
        return True

    def update_quote(self, quote: Quote) -> bool:
        # Validate chronology and values without declaring an old received quote
        # fresh today. Freshness is evaluated independently at each snapshot.
        quote.validate(quote.received_at,timedelta.max)
        if not quote.symbol or any(isinstance(v,bool) or not isinstance(v,int) for v in (quote.bid_size,quote.ask_size)):
            raise ValueError('normalized integer quote depth required')
        self._capacity(quote.symbol)
        rows = self._quotes.get(quote.symbol,[])
        if quote in rows: return False
        if rows and (quote.at<rows[-1].at or quote.received_at<rows[-1].received_at):
            raise ValueError('out-of-order awareness quote')
        self._quotes[quote.symbol] = (rows+[quote])[-self.config.max_quotes_per_symbol:]
        return True

    def update_event_calendar(self, calendar: EventCalendar) -> bool:
        calendar.validate()
        if len(calendar.events)>self.config.max_events_per_calendar: raise ValueError('calendar event capacity exceeded')
        for old in self._calendars:
            if old.calendar_id==calendar.calendar_id and old.available_at==calendar.available_at:
                if old==calendar: return False
                raise ValueError('conflicting calendar version')
        if len(self._calendars)>=self.config.max_event_calendars:
            # Never let a future version silently erase prior decision knowledge.
            raise ValueError('awareness event-calendar history capacity exceeded')
        self._calendars = sorted((*self._calendars,calendar),key=lambda c:(c.available_at,c.calendar_id))
        return True

    def _session(self, as_of):
        index = bisect_right(self._session_opens,as_of)-1
        return self._sessions[index] if index>=0 else None

    def _rows(self, symbol, session, as_of):
        return [o for o in self._bars.get(symbol,())
                if session.open<=o.bar.start<o.bar.end<=session.close and o.available_at<=as_of]

    @staticmethod
    def _complete_prefix(rows, session):
        return bool(rows) and rows[0].bar.start==session.open and all(a.bar.end==b.bar.start for a,b in zip(rows,rows[1:]))

    def _cross_return(self, symbol, session, end, as_of, lineage):
        rows = [o for o in self._rows(symbol,session,as_of) if o.bar.end<=end]
        if not rows: return None,'missing'
        if rows[-1].bar.end!=end: return None,'unsynchronized'
        if (as_of-rows[-1].bar.end).total_seconds()>self.config.max_bar_age_seconds: return None,'stale'
        if not self._complete_prefix(rows,session): return None,'incomplete_session'
        if self._lineage(rows[-1])!=lineage: return None,'lineage_mismatch'
        return log(rows[-1].bar.close/rows[0].bar.open),None

    def _event_state(self,symbol,as_of):
        latest = {}
        for calendar in self._calendars:
            if calendar.available_at<=as_of:
                latest[calendar.calendar_id] = calendar
        relevant = [c for c in latest.values() if not c.symbols or symbol in c.symbols]
        covered, blocked, unavailable = [],[],[]
        for cal in relevant:
            if (as_of-cal.available_at).total_seconds()>self.config.max_calendar_age_seconds:
                unavailable.append(cal.calendar_id); continue
            padding=timedelta(seconds=cal.max_blackout_seconds)
            if cal.coverage_start+padding<=as_of<=cal.coverage_end-padding: covered.append(cal.calendar_id)
            else: unavailable.append(cal.calendar_id)
            for event in cal.events:
                if event.symbols and symbol not in event.symbols: continue
                start = event.scheduled_at-timedelta(seconds=event.blackout_before_seconds)
                end = event.scheduled_at+timedelta(seconds=event.blackout_after_seconds)
                if start<=as_of<=end: blocked.append(event.event_id)
        state = 'known_blackout' if blocked else ('clear_covered_schedule' if covered and not unavailable else 'unknown')
        return state,tuple(sorted(blocked)),{'covered_calendars':tuple(sorted(covered)),
            'unknown_calendars':tuple(sorted(unavailable)),'scope':'supplied_scheduled_events_only'}

    def event_state(self, symbol: str, as_of: datetime):
        """Pure cheap lookup: state, immutable event IDs, detached scope metadata."""
        aware(as_of)
        if not symbol: raise ValueError('event lookup symbol required')
        return self._event_state(symbol,as_of)

    def snapshot(self, symbol: str, as_of: datetime, *, benchmark: str | None = None,
                 universe=(), reference: Reference | None = None) -> AwarenessSnapshot:
        aware(as_of)
        if not symbol: raise ValueError('snapshot symbol required')
        universe = tuple(universe)
        if len(set(universe))!=len(universe) or any(not isinstance(x,str) or not x for x in universe):
            raise ValueError('explicit unique breadth universe required')
        if len(universe)>self.config.max_symbols: raise ValueError('breadth universe exceeds capacity')
        observed = dict.fromkeys(('realized_variance','realized_volatility','rms_log_return','efficiency_ratio',
            'session_vwap_proxy','session_open','session_log_return','opening_gap_atr','opening_range_high',
            'opening_range_low','rvol_bucket','rvol_cumulative','relative_strength_log_return',
            'breadth_signed_fraction','quote_spread','quote_spread_bps','quote_age_seconds','quote_delay_seconds',
            'quote_bid_size','quote_ask_size'))
        inferred = {k:'unknown' for k in ('path_regime','participation','vwap_location','opening_location','relative_strength','quote_health')}
        quality = {'confidence_kind':'data_sufficiency_only_not_predictive_probability',
                   'rolling_return_count':0,'rolling_target_count':self.config.rolling_bars,
                   'baseline_bucket_samples':0,'baseline_cumulative_samples':0,
                   'baseline_target_sessions':self.config.baseline_sessions,'session_prefix_complete':False,
                   'universe_size':len(universe),'universe_id':stable_id('caller-universe',*sorted(universe)),
                   'universe_members':tuple(sorted(universe)), 'breadth_eligible':0,'breadth_coverage':None,
                   'bar_vwap_price_source':'HLC3_bar_proxy','annualized':False}
        issues = []
        session = self._session(as_of)
        rows = self._rows(symbol,session,as_of) if session else []
        last = rows[-1] if rows else None
        if not session: issues.append('no_retained_session')
        elif not rows: issues.append('no_available_session_bars')
        if session:
            quality.update(session_id=session.session_id,session_open=session.open.isoformat(),
                           session_close=session.close.isoformat(),session_phase='closed' if as_of>session.close else 'open')
        fresh = last is not None and (as_of-last.bar.end).total_seconds()<=self.config.max_bar_age_seconds
        if last and not fresh: issues.append('stale_bar')
        quality['bar_state'] = 'fresh' if fresh else ('stale' if last else 'unknown')
        if fresh:
            complete = self._complete_prefix(rows,session)
            quality['session_prefix_complete'] = complete
            if not complete: issues.append('incomplete_session_prefix')
            # A gap starts a new contiguous return window; never bridge it.
            contiguous = [last]
            for previous in reversed(rows[:-1]):
                if previous.bar.end!=contiguous[0].bar.start: break
                contiguous.insert(0,previous)
                if len(contiguous)>=self.config.rolling_bars+1: break
            returns = [log(b.bar.close/a.bar.close) for a,b in zip(contiguous,contiguous[1:])]
            n = len(returns); quality['rolling_return_count'] = n
            quality['rolling_state'] = 'full' if n==self.config.rolling_bars else ('partial' if n>=self.config.min_returns else 'warming')
            if n>=self.config.min_returns:
                variance = sum(r*r for r in returns)
                observed.update(realized_variance=variance,realized_volatility=sqrt(variance),rms_log_return=sqrt(variance/n))
                path = sum(abs(b.bar.close-a.bar.close) for a,b in zip(contiguous,contiguous[1:]))
                quality['rolling_start'] = contiguous[0].bar.end.isoformat()
                quality['rolling_end'] = last.bar.end.isoformat()
                if path==0: inferred['path_regime']='flat'
                else:
                    efficiency = min(1.,abs(last.bar.close-contiguous[0].bar.close)/path)
                    observed['efficiency_ratio'] = efficiency
                    inferred['path_regime'] = 'directional' if efficiency>=self.config.directional_efficiency else ('choppy' if efficiency<=self.config.choppy_efficiency else 'mixed')
            else: issues.append('rolling_warmup')
            if complete:
                opening = rows[0].bar.open
                observed.update(session_open=opening,session_log_return=log(last.bar.close/opening))
                volume = sum(o.bar.volume for o in rows)
                observed['session_volume'] = volume
                if volume>0:
                    vwap = sum((o.bar.high+o.bar.low+o.bar.close)/3*o.bar.volume for o in rows)/volume
                    observed['session_vwap_proxy'] = vwap
                    inferred['vwap_location'] = 'above' if last.bar.close>vwap else ('below' if last.bar.close<vwap else 'at')
                else: issues.append('zero_session_volume')
                if reference is not None:
                    try:
                        reference.validate(as_of)
                        previous_index=bisect_right(self._session_opens,session.open)-2
                        previous=self._sessions[previous_index] if previous_index>=0 else None
                        if (reference.horizon!='day' or reference.valid_from!=session.open or previous is None
                                or reference.period_end!=previous.close):
                            raise ValueError('not a prior daily session reference')
                        observed['opening_gap_atr'] = (opening-reference.close)/reference.atr
                    except ValueError: issues.append('invalid_opening_reference')
            cutoff = session.open+timedelta(minutes=self.config.opening_minutes)
            opening_rows = [o for o in rows if o.bar.end<=cutoff]
            if (cutoff<=session.close and as_of>=cutoff and self._complete_prefix(opening_rows,session)
                    and opening_rows[-1].bar.end==cutoff):
                high,low = max(o.bar.high for o in opening_rows),min(o.bar.low for o in opening_rows)
                observed.update(opening_range_high=high,opening_range_low=low)
                inferred['opening_location'] = 'above' if last.bar.close>high else ('below' if last.bar.close<low else 'inside')
            else: issues.append('opening_range_incomplete_or_unaligned')
            # Exact offsets and durations; current session is never its baseline.
            offset = last.bar.start-session.open
            prior = [s for s in self._sessions if s.close<=session.open][-self.config.baseline_sessions:]
            buckets,cumulative = [],[]
            for past in prior:
                hist = self._rows(symbol,past,as_of)
                matches = [o for o in hist if o.bar.start-past.open==offset and o.bar.end-o.bar.start==last.bar.end-last.bar.start]
                if not matches: continue
                match = matches[0]
                if self._lineage(match)!=self._lineage(last): continue
                buckets.append(match.bar.volume)
                prefix = [o for o in hist if o.bar.end<=match.bar.end]
                if self._complete_prefix(prefix,past): cumulative.append(sum(o.bar.volume for o in prefix))
            quality.update(baseline_bucket_samples=len(buckets),baseline_cumulative_samples=len(cumulative))
            if len(buckets)>=self.config.min_baseline_sessions and median(buckets)>0:
                observed['rvol_bucket'] = last.bar.volume/median(buckets)
            else: issues.append('bucket_rvol_insufficient_baseline')
            if complete and len(cumulative)>=self.config.min_baseline_sessions and median(cumulative)>0:
                ratio = sum(o.bar.volume for o in rows)/median(cumulative)
                observed['rvol_cumulative'] = ratio
                inferred['participation'] = 'elevated' if ratio>=self.config.elevated_rvol else ('quiet' if ratio<=self.config.quiet_rvol else 'typical')
            else: issues.append('cumulative_rvol_insufficient_baseline')
            if benchmark:
                other,reason = self._cross_return(benchmark,session,last.bar.end,as_of,self._lineage(last))
                if other is not None and observed['session_log_return'] is not None:
                    relative = observed['session_log_return']-other
                    observed['relative_strength_log_return'] = relative
                    inferred['relative_strength'] = 'outperforming' if relative>0 else ('underperforming' if relative<0 else 'flat')
                else: issues.append('benchmark_'+(reason or 'incomplete_target_session'))
            positive=negative=unchanged=0; missing=[]
            for member in universe:
                change,reason = self._cross_return(member,session,last.bar.end,as_of,self._lineage(last))
                if change is None: missing.append((member,reason)); continue
                positive += change>0; negative += change<0; unchanged += change==0
            eligible = positive+negative+unchanged
            quality.update(breadth_eligible=eligible,breadth_missing=tuple(missing),
                           breadth_coverage=eligible/len(universe) if universe else None)
            observed.update(breadth_positive=positive,breadth_negative=negative,breadth_unchanged=unchanged,
                            breadth_baseline='observed_session_open_equal_weight')
            if eligible: observed['breadth_signed_fraction']=(positive-negative)/eligible
        quotes = [q for q in self._quotes.get(symbol,()) if q.received_at<=as_of]
        if quotes:
            quote = quotes[-1]; age=(as_of-quote.at).total_seconds(); spread=quote.ask-quote.bid
            observed.update(quote_age_seconds=age,quote_delay_seconds=(quote.received_at-quote.at).total_seconds(),
                            quote_spread=spread,quote_spread_bps=spread/((quote.ask+quote.bid)/2)*10000,
                            quote_bid_size=quote.bid_size,quote_ask_size=quote.ask_size)
            inferred['quote_health'] = ('stale' if age>self.config.max_quote_age_seconds else
                'no_two_sided_liquidity' if min(quote.bid_size,quote.ask_size)<=0 or quote.bid<=0 else
                'wide' if observed['quote_spread_bps']>self.config.wide_spread_bps else 'observed_usable')
        else: issues.append('quote_unknown')
        state,event_ids,event_quality = self._event_state(symbol,as_of)
        observed.update(event_state=state,event_ids=event_ids)
        quality['events'] = event_quality
        if state=='unknown': issues.append('event_coverage_unknown')
        return AwarenessSnapshot(symbol,as_of,last.bar.end if last else None,last.available_at if last else None,
                                 _freeze(observed),_freeze(inferred),_freeze(quality),tuple(sorted(set(issues))))

    def dump_state(self) -> dict:
        return {'version':METHOD_VERSION,'config':self.config.fingerprint,
                'sessions':jsonable(self._sessions),'bars':{s:jsonable(v) for s,v in sorted(self._bars.items())},
                'quotes':{s:jsonable(v) for s,v in sorted(self._quotes.items())},
                'calendars':jsonable(self._calendars)}

    def load_state(self, payload: dict) -> None:
        if set(payload)!={'version','config','sessions','bars','quotes','calendars'} or payload['version']!=METHOD_VERSION or payload['config']!=self.config.fingerprint:
            raise ValueError('awareness checkpoint version/config mismatch')
        cfg=self.config
        if len(payload['sessions'])>cfg.max_calendar_entries or len(payload['calendars'])>cfg.max_event_calendars:
            raise ValueError('oversize awareness checkpoint')
        candidate = AwarenessBook(cfg)
        for row in payload['sessions']: candidate.register_session(session_from_dict(row))
        for symbol,rows in payload['bars'].items():
            if len(rows)>cfg.max_sessions*cfg.max_bars_per_session: raise ValueError('oversize bar checkpoint')
            for row in rows:
                observation=observation_from_dict(row)
                if observation.symbol!=symbol or not candidate.update(observation): raise ValueError('invalid checkpoint observation')
        for symbol,rows in payload['quotes'].items():
            if len(rows)>cfg.max_quotes_per_symbol: raise ValueError('oversize quote checkpoint')
            for row in rows:
                quote=quote_from_dict(row)
                if quote.symbol!=symbol or not candidate.update_quote(quote): raise ValueError('invalid checkpoint quote')
        for row in payload['calendars']:
            if not candidate.update_event_calendar(event_calendar_from_dict(row)): raise ValueError('duplicate checkpoint calendar')
        self._sessions,self._bars,self._quotes,self._calendars = candidate._sessions,candidate._bars,candidate._quotes,candidate._calendars
        self._session_opens = candidate._session_opens
