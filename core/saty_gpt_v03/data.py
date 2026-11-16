"""Explicit exchange calendars, session-aligned resampling and read-only data adapters.

Historical availability is a declared replay assumption, never an observed live latency.
Minute bars can arrive revised; finalized input is required and revision conflicts halt.
"""
from __future__ import annotations
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
from typing import Iterable
from core.saty_gpt_v03.reference import Bar,Session,Config,Indicators
from .models import Observation,Reference,aware

NY=ZoneInfo('America/New_York')

def timeframe_minutes(tf:str)->int:
    if tf.endswith('m'): n=int(tf[:-1])
    elif tf.endswith('H'): n=int(tf[:-1])*60
    else: raise ValueError('intraday timeframe required, e.g.10m or1H')
    if n<=0:raise ValueError('positive timeframe required')
    return n

class Calendar:
    def __init__(self,sessions:Iterable[Session]):
        self.sessions=tuple(sorted(sessions,key=lambda s:s.open))
        if len({s.session_id for s in self.sessions})!=len(self.sessions): raise ValueError('duplicate calendar sessions')
        for i,s in enumerate(self.sessions):
            s.validate()
            if i and self.sessions[i-1].close>=s.open:raise ValueError('overlapping sessions')
    @classmethod
    def from_alpaca(cls,rows:list[dict],entry_delay_minutes:int=0,cutoff_minutes:int=20,flat_minutes:int=10):
        if min(entry_delay_minutes,cutoff_minutes,flat_minutes)<0 or cutoff_minutes<flat_minutes:raise ValueError('invalid trading windows')
        out=[]
        for r in rows:
            day=r['date'];o=datetime.fromisoformat(day+'T'+r['open']).replace(tzinfo=NY);c=datetime.fromisoformat(day+'T'+r['close']).replace(tzinfo=NY)
            out.append(Session(day,o,o+timedelta(minutes=entry_delay_minutes),c-timedelta(minutes=cutoff_minutes),c-timedelta(minutes=flat_minutes),c))
        return cls(out)
    def session_at(self,t:datetime)->Session|None:
        aware(t)
        return next((s for s in self.sessions if s.open<=t<s.close),None)
    def previous(self,s:Session)->Session:
        i=self.sessions.index(s)
        if not i:raise ValueError('previous eligible session missing from calendar')
        return self.sessions[i-1]

def normalize_alpaca_intraday(symbol:str,rows:list[dict],timeframe:str,calendar:Calendar,
                              feed:str='iex',adjustment:str='raw',finalization_delay:timedelta=timedelta(seconds=1),
                              observed_at:datetime|None=None)->list[Observation]:
    """Drop extended/cross-session bars. Never relabel a partial clock-hour as session-hour."""
    delta=timedelta(minutes=timeframe_minutes(timeframe))
    if finalization_delay<timedelta(0):raise ValueError('negative finalization delay')
    out=[]
    for r in rows:
        t=datetime.fromisoformat(r['t'].replace('Z','+00:00'));s=calendar.session_at(t)
        if not s or t+delta>s.close:continue
        end=t+delta;available=max(end+finalization_delay,observed_at) if observed_at else end+finalization_delay
        if observed_at and end+finalization_delay>observed_at:continue
        out.append(Observation(symbol,timeframe,Bar(t,end,float(r['o']),float(r['h']),float(r['l']),float(r['c']),float(r['v'])),available,
                               'alpaca:'+feed,'US','regular',adjustment,'0'))
    out.sort(key=lambda o:(o.available_at,o.bar.end))
    return out

def resample_intraday(observations:Iterable[Observation],timeframe:str,calendar:Calendar)->list[Observation]:
    """Session-open-aligned complete buckets only; missing child bars are never filled.

    The last short session bucket is intentionally dropped. No current-hour preview.
    """
    target=timedelta(minutes=timeframe_minutes(timeframe));groups=defaultdict(list)
    for o in observations:
        o.validate();s=calendar.session_at(o.bar.start)
        if not s:continue
        step=o.bar.end-o.bar.start
        if target<step or target%step:raise ValueError('target must be an integer multiple of input bar')
        offset=(o.bar.start-s.open)//target;start=s.open+offset*target;end=start+target
        if end>s.close or o.bar.end>end:continue
        groups[(o.symbol,o.provider,o.session_policy,o.adjustment,start,end)].append(o)
    out=[]
    for key,items in sorted(groups.items(),key=lambda x:x[0][-1]):
        items.sort(key=lambda o:o.bar.start);symbol,provider,policy,adj,start,end=key
        if items[0].bar.start!=start or items[-1].bar.end!=end:continue
        if any(a.bar.end!=b.bar.start for a,b in zip(items,items[1:])):continue
        if len({o.bar.start for o in items})!=len(items):raise ValueError('duplicate resample input')
        if len({o.revision for o in items})>1:raise ValueError('mixed revision lineage')
        b=Bar(start,end,items[0].bar.open,max(o.bar.high for o in items),min(o.bar.low for o in items),items[-1].bar.close,sum(o.bar.volume for o in items))
        out.append(Observation(symbol,timeframe,b,max(o.available_at for o in items),provider,'US',policy,adj,items[-1].revision))
    return out

def normalize_alpaca_daily(symbol:str,rows:list[dict],calendar:Calendar,feed:str='iex',adjustment:str='raw',
                           finalization_delay:timedelta=timedelta(minutes=1),observed_at:datetime|None=None)->list[Observation]:
    sessions={s.session_id:s for s in calendar.sessions};out=[]
    for r in rows:
        day=datetime.fromisoformat(r['t'].replace('Z','+00:00')).astimezone(NY).date().isoformat()
        if day not in sessions:continue
        s=sessions[day]
        if observed_at and s.close+finalization_delay>observed_at:continue
        available=max(s.close+finalization_delay,observed_at) if observed_at else s.close+finalization_delay
        out.append(Observation(symbol,'1D',Bar(s.open,s.close,float(r['o']),float(r['h']),float(r['l']),float(r['c']),float(r['v'])),available,'alpaca:'+feed,'US','regular',adjustment))
    return sorted(out,key=lambda o:o.bar.end)

def build_daily_references(daily:Iterable[Observation],calendar:Calendar)->list[tuple[str,Reference]]:
    """WilderATR14 daily map valid only in the next known exchange session."""
    states={};out=[];byclose={s.close:i for i,s in enumerate(calendar.sessions)};last={}
    for o in sorted(daily,key=lambda o:o.bar.end):
        o.validate()
        if o.timeframe!='1D' or o.bar.end not in byclose:raise ValueError('daily bar not matched to exchange close')
        i=byclose[o.bar.end]
        if o.symbol in last and i!=last[o.symbol]+1:states.pop(o.symbol,None)
        last[o.symbol]=i
        ind=states.setdefault(o.symbol,Indicators(Config(warmup_bars=14)));f=ind.update(o.bar)
        if f.atr is None or f.atr<=0 or i+1==len(calendar.sessions):continue
        nxt=calendar.sessions[i+1]
        if o.available_at>nxt.open:continue
        out.append((o.symbol,Reference('day',o.bar.end,o.available_at,o.bar.close,f.atr,nxt.open,nxt.close,calendar.sessions[i].session_id)))
    return out
