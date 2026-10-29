"""Causal, independently clocked feature and structure book.

Fractals, clustering and trendlines are ORIGINAL research choices, not recovered
Saty constants. Indicator math is reused unchanged from ``saty_reference``.
Calendar schedules are supplied explicitly; this module never guesses holidays,
missing bars, session closes, or the previous eligible reference period.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from itertools import islice
from math import isfinite
import json
import re

from core.saty_gpt_v03.reference import Bar, Config, Features, Indicators, MULTIPLIERS, Session
from .models import Context, Frame, Level, Observation, Pivot, Reference, aware, jsonable


def _duration(tf: str) -> timedelta | None:
    """Only fixed intraday clocks are inferred; calendar periods are not seconds."""
    m = re.fullmatch(r'(\d+)(s|m|h|H)', tf)
    if m:
        n = int(m.group(1))
        if n <= 0: raise ValueError('positive timeframe required')
        return timedelta(seconds=n * {'s': 1, 'm': 60, 'h': 3600, 'H': 3600}[m.group(2)])
    return None


@dataclass(frozen=True)
class StructureConfig:
    required_timeframes: tuple[str, ...] = ('10m', '1H')
    max_ages: dict[str, timedelta] = field(default_factory=dict)
    warmup_bars: int = 1000
    warmup_by_timeframe: dict[str, int] = field(default_factory=dict)
    ribbon_version: str = 'pro'
    pivot_left: int = 2
    pivot_right: int = 2
    zone_tolerance_atr: float = .10
    range_lookback: int = 12
    max_history: int = 2048
    max_pivots: int = 256
    max_streams: int = 128
    max_calendar_entries: int = 4096
    require_session: bool = False
    require_same_provider: bool = True
    carry_previous_session_timeframes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.ribbon_version not in ('pro', 'legacy'): raise ValueError('invalid ribbon version')
        if self.warmup_bars < 21 or any(v < 21 for v in self.warmup_by_timeframe.values()):
            raise ValueError('warmup must include at least 21 actual bars')
        if min(self.pivot_left, self.pivot_right, self.range_lookback) < 1:
            raise ValueError('positive structure lengths required')
        if self.max_history < max(self.pivot_left + self.pivot_right + 1, self.range_lookback + 1):
            raise ValueError('history too short for structure')
        if min(self.max_pivots, self.max_streams, self.max_calendar_entries) < 2:
            raise ValueError('invalid retention bounds')
        if not isfinite(self.zone_tolerance_atr) or self.zone_tolerance_atr < 0:
            raise ValueError('invalid clustering tolerance')
        if any(v <= timedelta(0) for v in self.max_ages.values()): raise ValueError('positive max ages required')
        if any(not tf for tf in self.required_timeframes): raise ValueError('empty required timeframe')
        if any(_duration(tf) is None for tf in self.carry_previous_session_timeframes):
            raise ValueError('session carry requires fixed intraday timeframes')

    def warmup(self, tf: str) -> int:
        return self.warmup_by_timeframe.get(tf, self.warmup_bars)

    def max_age(self, tf: str) -> timedelta:
        if tf in self.max_ages: return self.max_ages[tf]
        return 2 * (_duration(tf) or timedelta(days=1))


@dataclass(frozen=True)
class _Record:
    frame: Frame
    segment: int


@dataclass(frozen=True)
class _Confirmed:
    pivot: Pivot
    segment: int


@dataclass(frozen=True)
class _ReferenceWindow:
    symbol: str
    horizon: str
    valid_from: datetime
    valid_until: datetime
    previous_period_end: datetime
    known_at: datetime


class _Stream:
    def __init__(self, symbol: str, cfg: StructureConfig):
        self.ind = Indicators(Config(symbol=symbol, ribbon_version=cfg.ribbon_version,
                                     warmup_bars=max(14, cfg.warmup_bars)))
        self.records: deque[_Record] = deque(maxlen=cfg.max_history)
        self.pivots: deque[_Confirmed] = deque(maxlen=cfg.max_pivots)
        self.segment = 0
        self.retention_truncated = False
        self.lineage: tuple[str, ...] | None = None


class FeatureBook:
    """No implicit resampling: each timeframe must arrive as its own Observation.

    ``update`` is idempotent for an identical retained observation. Revisions,
    overlapping bars, out-of-order delivery and lineage changes raise ValueError
    without modifying state; corrected data require an explicit replay.

    ``context`` returns blockers rather than guessing missing/stale inputs. No
    execution frame available at as_of raises ValueError, since Context requires
    an actual execution Frame. Querying an evicted historical prefix is unsupported.
    """
    def __init__(self, config: StructureConfig | None = None):
        self.config = config or StructureConfig()
        self._streams: dict[tuple[str, str], _Stream] = {}
        self._sessions: list[Session] = []
        self._reference_windows: list[_ReferenceWindow] = []

    def register_session(self, session: Session) -> None:
        session.validate()
        for old in self._sessions:
            if old == session: return
            if old.session_id == session.session_id or max(old.open, session.open) < min(old.close, session.close):
                raise ValueError('conflicting/overlapping calendar session')
        self._sessions.append(session)
        self._sessions.sort(key=lambda x: x.open)
        self._sessions = self._sessions[-self.config.max_calendar_entries:]

    def register_reference_period(self, symbol: str, horizon: str, valid_from: datetime,
                                  valid_until: datetime, previous_period_end: datetime,
                                  known_at: datetime | None = None) -> None:
        """Register previous-eligible-period metadata from an independent calendar.

        The caller must obtain this schedule from the relevant exchange/horizon
        calendar, separately from the Reference being checked. No synthetic
        weekday rule or a merely user-declared Reference expiry passes this gate.
        """
        known_at = known_at or valid_from
        for t in (valid_from, valid_until, previous_period_end, known_at): aware(t)
        if not symbol or not horizon or not previous_period_end <= valid_from < valid_until or known_at > valid_from:
            raise ValueError('invalid eligible-period schedule')
        item = _ReferenceWindow(symbol, horizon, valid_from, valid_until, previous_period_end, known_at)
        for old in self._reference_windows:
            if old == item: return
            if old.symbol == symbol and old.horizon == horizon and max(old.valid_from, valid_from) < min(old.valid_until, valid_until):
                raise ValueError('conflicting reference calendar window')
        self._reference_windows.append(item)
        self._reference_windows.sort(key=lambda x: x.valid_from)
        self._reference_windows = self._reference_windows[-self.config.max_calendar_entries:]

    def _calendar_bridge(self, previous: Bar, current: Bar, policy: str, timeframe: str) -> bool:
        if policy != 'regular': return False
        # Only a complete known closure is skipped. Missing open-session bars are
        # never disguised as an overnight/weekend gap.
        for a, b in zip(self._sessions, self._sessions[1:]):
            if current.start != b.open: continue
            if previous.end == a.close: return True
            d = _duration(timeframe)
            # A resampler may omit the final incomplete bucket, e.g. the last
            # 30 minutes of a 6.5-hour session on a 1H clock. This is permitted
            # only at the exact final full-bucket boundary, never for a missing
            # whole tradable bucket. No synthetic bar is created.
            if (d is not None and previous.end - previous.start == d
                    and a.open <= previous.start < previous.end < a.close
                    and a.close - previous.end < d
                    and (previous.end - a.open) % d == timedelta(0)):
                return True
        return False

    @staticmethod
    def _lineage(o: Observation) -> tuple[str, ...]:
        return (o.provider, o.venue, o.session_policy, o.adjustment)

    def update(self, observation: Observation) -> Frame:
        o = observation
        o.validate()
        if not o.venue or not o.session_policy or not o.adjustment or not o.revision:
            raise ValueError('missing observation lineage')
        cfg = self.config
        key = (o.symbol, o.timeframe)
        stream = self._streams.get(key)
        if stream is None and len(self._streams) >= cfg.max_streams: raise ValueError('stream capacity exceeded')
        if stream is not None:
            # Accepted bar ends are strictly increasing. Only an older/equal
            # end can be a retained duplicate; the normal append path is O(1).
            if o.bar.end <= stream.records[-1].frame.bar.end:
                for r in reversed(stream.records):
                    if r.frame.bar.end == o.bar.end:
                        if r.frame.observation == o: return r.frame
                        raise ValueError('revision/conflicting duplicate requires replay')
            if stream.lineage != self._lineage(o): raise ValueError('stream lineage changed; replay required')
            previous = stream.records[-1].frame
            if o.bar.start < previous.bar.end: raise ValueError('overlapping/out-of-order bars')
            if o.available_at < previous.available_at: raise ValueError('out-of-order availability; replay required')
        d = _duration(o.timeframe)
        if d is not None and o.bar.end - o.bar.start != d:
            truncated = (o.bar.end - o.bar.start < d and o.session_policy == 'regular'
                         and any(o.bar.end == s.close and s.open <= o.bar.start for s in self._sessions))
            if not truncated: raise ValueError('bar duration does not match timeframe/calendar close')
        if d is not None and self._sessions and o.session_policy == 'regular':
            if not any(s.open <= o.bar.start < o.bar.end <= s.close for s in self._sessions):
                raise ValueError('regular-session bar outside registered calendar')
        if stream is None:
            stream = _Stream(o.symbol, cfg)
            stream.lineage = self._lineage(o)
            self._streams[key] = stream
        elif o.bar.start > stream.records[-1].frame.bar.end and not self._calendar_bridge(stream.records[-1].frame.bar, o.bar, o.session_policy, o.timeframe):
            stream.segment += 1
            stream.ind = Indicators(stream.ind.cfg)
        f = Frame(o, stream.ind.update(o.bar), stream.ind.count)
        if len(stream.records) == cfg.max_history: stream.retention_truncated = True
        stream.records.append(_Record(f, stream.segment))
        width = cfg.pivot_left + cfg.pivot_right + 1
        recent = list(islice(reversed(stream.records), width))
        recent.reverse()
        if len(recent) == width and all(r.segment == stream.segment for r in recent):
            center = recent[cfg.pivot_left].frame
            neighbors = [r.frame for i, r in enumerate(recent) if i != cfg.pivot_left]
            confirmation = max(r.frame.available_at for r in recent)
            for kind, price, confirmed in (
                ('high', center.bar.high, all(center.bar.high > x.bar.high for x in neighbors)),
                ('low', center.bar.low, all(center.bar.low < x.bar.low for x in neighbors)),
            ):
                if confirmed:
                    if len(stream.pivots) == cfg.max_pivots: stream.retention_truncated = True
                    stream.pivots.append(_Confirmed(Pivot(kind, price, center.bar.end, confirmation,
                                                         center.features.phase, o.timeframe), stream.segment))
        return f

    def _reference_ok(self, reference: Reference, symbol: str, at: datetime, blockers: list[str]) -> bool:
        try: reference.validate(at)
        except (ValueError, TypeError):
            blockers.append('REFERENCE_INVALID_OR_STALE'); return False
        windows = [w for w in self._reference_windows if w.symbol == symbol and w.horizon == reference.horizon
                   and w.known_at <= at and w.valid_from <= at < w.valid_until]
        if not windows:
            blockers.append('REFERENCE_PREVIOUS_PERIOD_UNVERIFIED'); return False
        w = windows[-1]
        if (reference.period_end != w.previous_period_end or reference.valid_from != w.valid_from
                or reference.valid_until != w.valid_until):
            blockers.append('REFERENCE_WRONG_PREVIOUS_PERIOD'); return False
        return True

    def _previous_session_carry(self, frame: Frame, execution_timeframe: str, as_of: datetime,
                                reference: Reference, session: Session | None) -> dict | None:
        """Explicit v0.3 policy, not an inferred author trading rule.

        Carry only the previous session's final complete clock bucket until the
        current session's first complete bucket is due. The independently
        registered daily reference calendar anchors previous-session adjacency.
        Closed-market elapsed time is excluded only for this narrow case.
        """
        tf = frame.timeframe
        if (session is None or tf == execution_timeframe
                or tf not in self.config.carry_previous_session_timeframes
                or frame.observation.session_policy != 'regular' or reference.horizon not in ('D', 'day')):
            return None
        d = _duration(tf)
        if d is None or not session.open <= as_of < session.open + d <= session.close:
            return None
        if frame.available_at > as_of or not self._reference_ok(reference, frame.symbol, as_of, []):
            return None
        for previous, current in zip(self._sessions, self._sessions[1:]):
            if current != session or reference.period_end != previous.close:
                continue
            expected_end = previous.open + ((previous.close - previous.open) // d) * d
            if (expected_end <= previous.open or frame.bar.end != expected_end
                    or frame.bar.start != expected_end - d):
                return None
            trading_age = previous.close - frame.bar.end + as_of - current.open
            return {'policy': 'previous_session_final_full_bucket_v03',
                    'previous_session_id': previous.session_id,
                    'current_session_id': current.session_id,
                    'bar_end': frame.bar.end.isoformat(),
                    'first_current_bucket_due': (current.open + d).isoformat(),
                    'trading_age_seconds': trading_age.total_seconds()}
        return None

    def context(self, symbol: str, execution_timeframe: str, as_of: datetime,
                reference: Reference, session: Session | None = None) -> Context:
        aware(as_of)
        selected: dict[str, _Record] = {}
        for (sym, tf), st in self._streams.items():
            if sym != symbol: continue
            if st.retention_truncated and as_of < st.records[-1].frame.available_at:
                raise ValueError('historical context beyond retained prefix; replay required')
            r = next((r for r in reversed(st.records) if r.frame.available_at <= as_of and r.frame.bar.end <= as_of), None)
            if r is not None: selected[tf] = r
        if execution_timeframe not in selected: raise ValueError('no available execution frame at as_of')
        execution = selected[execution_timeframe].frame
        blockers: list[str] = []
        required = set(self.config.required_timeframes) | {execution_timeframe}
        frames: dict[str, Frame] = {}
        valid_records: dict[str, _Record] = {}
        carried: dict[str, dict] = {}
        for tf in sorted(required - selected.keys()): blockers.append('MISSING_TIMEFRAME:' + tf)
        for tf, rec in selected.items():
            f = rec.frame
            problems = []
            carry = self._previous_session_carry(f, execution_timeframe, as_of, reference, session)
            age = timedelta(seconds=carry['trading_age_seconds']) if carry is not None else as_of - f.bar.end
            if age > self.config.max_age(tf): problems.append('STALE_TIMEFRAME:' + tf)
            if f.count < self.config.warmup(tf):
                problems.append(('GAP_REWARM:' if rec.segment else 'WARMUP:') + tf)
            if f.features.atr is None or f.features.atr <= 0 or f.features.phase is None or f.features.compression is None:
                problems.append('INCOMPLETE_FEATURES:' + tf)
            a, b = f.observation, execution.observation
            if (a.venue, a.session_policy, a.adjustment) != (b.venue, b.session_policy, b.adjustment) or (self.config.require_same_provider and a.provider != b.provider):
                problems.append('LINEAGE_MISMATCH:' + tf)
            if tf in required:
                blockers.extend(problems)
                frames[tf] = f
                valid_records[tf] = rec
            elif not problems:
                frames[tf] = f
                valid_records[tf] = rec
            if carry is not None and tf in frames:
                carried[tf] = carry
        if session is None:
            if self.config.require_session: blockers.append('SESSION_REQUIRED')
        else:
            session.validate()
            if not session.open <= execution.bar.start < execution.bar.end <= as_of <= session.close:
                blockers.append('EXECUTION_SESSION_MISMATCH')
            for tf, f in frames.items():
                if tf not in carried and _duration(tf) is not None and f.observation.session_policy == 'regular' and not session.open <= f.bar.start < f.bar.end <= session.close:
                    blockers.append('FRAME_SESSION_MISMATCH:' + tf)
        reference_ok = self._reference_ok(reference, symbol, as_of, blockers)
        pivots: list[Pivot] = []
        raw_levels: list[Level] = []
        trendlines: list[Level] = []
        for tf, rec in valid_records.items():
            f = rec.frame
            # A blocked required frame is visible for diagnostics but supplies no
            # tradable structure until its own freshness and warmup are valid.
            if any(x.endswith(':' + tf) for x in blockers): continue
            st = self._streams[(symbol, tf)]
            ps = [p.pivot for p in st.pivots if p.segment == rec.segment and p.pivot.confirmed_at <= as_of
                  and p.pivot.bar_end <= f.bar.end]
            pivots.extend(ps)
            raw_levels.extend(Level(p.price, 'pivot_' + p.kind, tf, p.confirmed_at) for p in ps)
            raw_levels.extend(Level(price, 'ema_' + str(n), tf, f.available_at, 'completed_frame_ema')
                              for n, price in f.features.ema.items())
            if tf != execution_timeframe:
                raw_levels.extend((Level(f.bar.high, 'completed_high', tf, f.available_at),
                                   Level(f.bar.low, 'completed_low', tf, f.available_at)))
            # Take the same final K eligible records without materializing H
            # retained frames. Historical queries still skip future records.
            window = list(islice((r.frame for r in reversed(st.records)
                                  if r.segment == rec.segment and r.frame.available_at <= as_of
                                  and r.frame.bar.end < f.bar.end), self.config.range_lookback))
            window.reverse()
            if len(window) == self.config.range_lookback:
                known = max(x.available_at for x in window)
                raw_levels.extend((Level(max(x.bar.high for x in window), 'range_high', tf, known),
                                   Level(min(x.bar.low for x in window), 'range_low', tf, known)))
            for kind in ('high', 'low'):
                same = [p for p in ps if p.kind == kind]
                if len(same) < 2: continue
                a, b = same[-2:]
                seconds = (b.bar_end - a.bar_end).total_seconds()
                if seconds <= 0: continue
                price = b.price + (b.price - a.price) * (as_of - b.bar_end).total_seconds() / seconds
                if isfinite(price) and price > 0:
                    trendlines.append(Level(price, 'trendline_' + kind, tf, max(a.confirmed_at, b.confirmed_at),
                                            'confirmed_pivots:' + a.bar_end.isoformat() + '/' + b.bar_end.isoformat()))
        if reference_ok:
            for m in sorted({d * m for d in (-1, 1) for m in MULTIPLIERS}):
                price = reference.price(m)
                if price > 0: raw_levels.append(Level(price, 'reference_' + str(m), reference.horizon,
                                                       reference.available_at, 'previous_eligible_period'))
        atr = execution.features.atr or 0.
        levels = self._cluster(raw_levels, self.config.zone_tolerance_atr * atr) + trendlines
        return Context(as_of, execution, frames, reference, tuple(sorted(levels, key=lambda x: (x.price, x.kind))),
                       tuple(sorted(pivots, key=lambda x: (x.confirmed_at, x.timeframe, x.kind))), session,
                       tuple(dict.fromkeys(blockers)),
                       metadata={'carried_timeframes': carried} if carried else {})

    @staticmethod
    def _cluster(levels: list[Level], tolerance: float) -> list[Level]:
        """Bounded-diameter clusters, not single-link chains or confidence votes."""
        groups: list[list[Level]] = []
        for level in sorted(levels, key=lambda x: (x.price, x.timeframe, x.kind)):
            if not groups or level.price - groups[-1][0].price > tolerance: groups.append([level])
            else: groups[-1].append(level)
        out = []
        for group in groups:
            if len(group) == 1: out.append(group[0]); continue
            prices = [x.price for x in group]
            out.append(Level(sum(prices) / len(prices), 'zone', '+'.join(sorted({x.timeframe for x in group})),
                             max(x.known_at for x in group),
                             'cluster:' + ';'.join(sorted({x.kind + '@' + x.timeframe for x in group})),
                             min(prices), max(prices)))
        return out

    def dump_state(self) -> dict:
        streams = []
        for (symbol, tf), st in sorted(self._streams.items()):
            ind = st.ind
            streams.append({'symbol': symbol, 'timeframe': tf, 'segment': st.segment, 'lineage': st.lineage, 'retention_truncated': st.retention_truncated,
                            'records': list(st.records), 'pivots': list(st.pivots),
                            'indicator': {'ema': ind.ema, 'previous_close': ind.previous_close,
                                          'tr_seed': ind.tr_seed, 'atr': ind.atr, 'count': ind.count,
                                          'closes': list(ind.closes), 'phase': ind.phase,
                                          'previous_bb_kc_delta': ind.previous_bb_kc_delta}})
        payload = jsonable({'format': 'saty_structure_v1', 'config': self.config, 'streams': streams,
                            'sessions': self._sessions, 'reference_windows': self._reference_windows})
        payload['checksum'] = sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return payload

    def load_state(self, state: dict) -> None:
        """Restore an exact checkpoint; configuration must match this book."""
        payload = json.loads(json.dumps(state))
        checksum = payload.pop('checksum', None)
        if checksum != sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest():
            raise ValueError('checkpoint checksum mismatch')
        if payload.get('format') != 'saty_structure_v1' or payload.get('config') != jsonable(self.config):
            raise ValueError('checkpoint format/config mismatch')
        rebuilt = FeatureBook(self.config)
        dt = datetime.fromisoformat
        for s in payload['sessions']:
            rebuilt.register_session(Session(**{k: dt(v) if k != 'session_id' else v for k, v in s.items()}))
        for w in payload['reference_windows']:
            rebuilt.register_reference_period(w['symbol'], w['horizon'], dt(w['valid_from']), dt(w['valid_until']),
                                              dt(w['previous_period_end']), dt(w['known_at']))
        for item in payload['streams']:
            st = _Stream(item['symbol'], self.config)
            st.segment = item['segment']; st.retention_truncated = item['retention_truncated']; st.lineage = tuple(item['lineage'])
            for r in item['records']:
                d = r['frame']; od = d['observation']; bd = od.pop('bar')
                b = Bar(**{k: dt(v) if k in ('start', 'end') else v for k, v in bd.items()})
                od['available_at'] = dt(od['available_at'])
                o = Observation(bar=b, **od); o.validate()
                fd = d['features']; fd['ema'] = {int(k): v for k, v in fd['ema'].items()}
                st.records.append(_Record(Frame(o, Features(**fd), d['count']), r['segment']))
            for p in item['pivots']:
                pd = p['pivot']; pd['bar_end'] = dt(pd['bar_end']); pd['confirmed_at'] = dt(pd['confirmed_at'])
                st.pivots.append(_Confirmed(Pivot(**pd), p['segment']))
            ind = item['indicator']
            for k, value in ind.items():
                if k == 'ema': value = {int(n): v for n, v in value.items()}
                if k == 'closes': value = deque(value, maxlen=21)
                setattr(st.ind, k, value)
            if not st.records or st.ind.count != st.records[-1].frame.count:
                raise ValueError('invalid checkpoint stream')
            rebuilt._streams[(item['symbol'], item['timeframe'])] = st
        if len(rebuilt._streams) > self.config.max_streams: raise ValueError('checkpoint exceeds capacity')
        self._streams, self._sessions, self._reference_windows = rebuilt._streams, rebuilt._sessions, rebuilt._reference_windows
