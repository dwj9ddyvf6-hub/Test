"""Deterministic context detectors; thresholds are research settings, not probabilities."""
from collections import defaultdict
import json
import math
from datetime import timedelta
from .core import utc, stamp, stable_mean


def history(store, as_of, entity, horizon, lookback_days=30):
    as_of=stamp(as_of)
    cutoff=(utc(as_of)-timedelta(days=lookback_days)).isoformat()
    rows=store.db.execute('''SELECT * FROM observations WHERE entity=? AND horizon=?
         AND first_seen<=? AND publication_time<=? AND event_time<=? AND available_at<=? AND event_time>=?
         ORDER BY publication_time,first_seen,ingest_time,id''',(entity,horizon,as_of,as_of,as_of,as_of,cutoff))
    latest={}
    for row in rows:
        r=dict(row);latest[(r['source'],r['item_id'],r['dimension'],r['units'])]=r
    selected=[];seen=set()
    for r in latest.values():
        key=(r['fingerprint'],r['dimension'],r['units'],r['entity'],r['horizon'])
        if r['access_status'] not in ('public','licensed','user_import','fixture') or r['value'] is None or not json.loads(r['provenance']).get('source_population') or key in seen:continue
        seen.add(key);selected.append(r)
    return selected


def process_id(row):
    p=json.loads(row['provenance'])
    return (row['config_version'],p.get('source_population'),p.get('measurement_model_version'),p.get('entity_mapping_version'))


def series(rows):
    groups=defaultdict(list)
    for r in rows: groups[(r['source'],r['dimension'],r['units'],process_id(r))].append(r)
    return {k:sorted(v,key=lambda r:utc(r['event_time'])) for k,v in groups.items()}


def usable(v,as_of,minimum,max_gap_hours=72):
    if len(v)<minimum:return False
    if (utc(as_of)-utc(v[-1]['event_time'])).total_seconds()/3600>v[-1]['max_age_hours']:return False
    return all(0<(utc(b['event_time'])-utc(a['event_time'])).total_seconds()/3600<=max_gap_hours for a,b in zip(v[-minimum:],v[-minimum+1:]))


def detect(store,as_of,entity,horizon):
    rows=history(store,as_of,entity,horizon);groups=series(rows);out=[]
    def emit(name,status,reason,evidence=(),measure=None):
        def finite(value):
            if isinstance(value,dict):return all(finite(v) for v in value.values())
            return value is None or not isinstance(value,(int,float)) or math.isfinite(value)
        if not finite(measure):status='abstain';reason='Numerical range exceeds supported finite calculation';measure=None
        out.append(dict(pattern=name,status=status,reason=reason,measure=measure,evidence_ids=[r['id'] for r in evidence]))
    attention=[v for k,v in groups.items() if k[1]=='attention' and k[2]=='article_daily_user_pageviews' and usable(v,as_of,6)]
    for v in attention:
        prev=stable_mean(r['value'] for r in v[-6:-3]);recent=stable_mean(r['value'] for r in v[-3:])
        if prev<=0:emit('attention_acceleration','abstain','Nonpositive comparison baseline',v[-6:]);continue
        change=recent/prev-1
        emit('attention_acceleration','watch' if change>=.5 else 'context','Latest three observations versus prior three; 50% research threshold',v[-6:],change)
    if not attention:emit('attention_acceleration','abstain','Need six fresh-ended, ordered article-count observations with gaps <=72h')
    stress=[v for k,v in groups.items() if k[1]=='stress' and k[2]=='VIX_index_points' and usable(v,as_of,3)]
    for v in stress:
        elevated=all(r['value']>=25 for r in v[-3:])
        emit('stress_persistence','watch' if elevated else 'context','Three consecutive observed VIX closes >=25; risk proxy only',v[-3:],min(r['value'] for r in v[-3:]))
    if not stress:emit('stress_persistence','abstain','Need three fresh-ended VIX closes with gaps <=72h')
    # Compare only matching units, near-contemporaneous latest observations by source family.
    families=defaultdict(dict)
    for r in sorted(rows,key=lambda r:utc(r['event_time'])):
        if r['dimension']=='sentiment' and (utc(as_of)-utc(r['event_time'])).total_seconds()/3600<=min(r['max_age_hours'],48):
            p=json.loads(r['provenance'])
            semantic=p.get('measurement_model_version')
            if semantic is None and r['units'] in ('balance','lexicon_score_v1','FRBSF_news_sentiment_index'):
                semantic='declared_unit:'+r['units']
            if semantic is not None:families[(r['units'],semantic)][r['source_family']]=r
    compared=False
    for unit,vs in families.items():
        v=list(vs.values())
        if len(v)<2:continue
        # Exact identical text is not independent evidence.
        if len({r['fingerprint'] for r in v})<2:continue
        compared=True;opposed=min(r['value'] for r in v)<0<max(r['value'] for r in v)
        emit('source_disagreement','watch' if opposed else 'context','Opposing signs across at least two declared source families; common units/model '+str(unit),v,max(r['value'] for r in v)-min(r['value'] for r in v))
    if not compared:emit('source_disagreement','abstain','Need two nonduplicated source families, common units and observations within 48h')
    # Divergence needs explicitly imported price returns aligned to sentiment dates.
    found=False
    for k,v in groups.items():
        if k[1]!='sentiment' or not usable(v,as_of,3):continue
        for pk,pv in groups.items():
            if pk[1]!='price_return' or pk[2]!='decimal_return' or not usable(pv,as_of,3):continue
            prices={stamp(r['event_time']):r for r in pv}
            aligned=[(r,prices[stamp(r['event_time'])]) for r in v if stamp(r['event_time']) in prices][-3:]
            if len(aligned)<3:continue
            if not usable([a for a,b in aligned],as_of,3) or not usable([b for a,b in aligned],as_of,3):continue
            found=True;delta=aligned[-1][0]['value']-aligned[0][0]['value'];ret=sum(p['value'] for _,p in aligned)
            emit('sentiment_price_divergence','watch' if (delta<0<ret or ret<0<delta) else 'context','Three aligned observations; sentiment change versus sum of decimal returns (not compounded)',[r for pair in aligned for r in pair],{'sentiment_change':delta,'summed_return':ret})
    if not found:emit('sentiment_price_divergence','abstain','Need three time-aligned sentiment and explicitly supplied decimal-return observations')
    emit('narrative_concentration','abstain','Not implemented: requires topic-share denominator, taxonomy version and complete topic coverage')
    return {'as_of':stamp(as_of),'entity':entity,'horizon':horizon,'mode':'context_only','orders_allowed':False,'patterns':out}


def forecast(store,as_of,entity,horizon,source,dimension,units):
    """Next observed proxy-value forecast; not a return forecast or belief probability."""
    def observations(cutoff):
        candidates=[v for k,v in series(history(store,cutoff,entity,horizon)).items() if k[:3]==(source,dimension,units)]
        return max(candidates,key=lambda v:utc(v[-1]['event_time'])) if candidates else []
    v=observations(as_of)
    base=dict(as_of=stamp(as_of),entity=entity,horizon='next_observation',input_horizon=horizon,
              source=source,target=dimension,units=units,method='persistence and mean of last four first differences',
              predictive_validation='not_established',orders_allowed=False)
    if not usable(v,as_of,5):return dict(base,status='abstain',reason='Need five ordered fresh-ended observations with gaps <=72h')
    def prediction(v):
        estimate=v[-1]['value']+(v[-1]['value']-v[-5]['value'])/4
        if units in ('article_daily_user_pageviews','VIX_index_points'):estimate=max(0,estimate)
        if units in ('balance','lexicon_score_v1'):estimate=max(-1,min(1,estimate))
        if units in ('fraction','uncertainty_token_fraction'):estimate=max(0,min(1,estimate))
        return estimate
    # Reconstruct vintages at actual knowledge times; never score historical archives
    # as though their values had been available at original event dates.
    cutoff=stamp(as_of)
    origins=[r[0] for r in store.db.execute('''SELECT DISTINCT available_at FROM observations
        WHERE entity=? AND horizon=? AND source=? AND dimension=? AND units=?
        AND available_at<=? AND publication_time<=? AND event_time<=? AND first_seen<=?
        ORDER BY available_at''',(entity,horizon,source,dimension,units,cutoff,cutoff,cutoff,cutoff))][-100:]
    pending=[];scores=[];incomparable=[]
    for origin in origins:
        ov=observations(origin)
        if not ov:continue
        current_process=process_id(ov[-1])
        for p in pending[:]:
            if p['process_id']!=current_process:
                incomparable.append({'origin':p['origin'],'boundary_available_at':origin,'reason':'config/model/population/mapping boundary','old_process':p['process_id'],'new_process':current_process})
                pending.remove(p);continue
            later=[r for r in ov if utc(r['event_time'])>utc(p['event_time'])]
            if later:
                target=later[0]
                scores.append(dict(origin=p['origin'],target_event=target['event_time'],target_available_at=origin,
                                   actual=target['value'],persistence=p['persistence'],drift=p['drift'],process_id=current_process))
                pending.remove(p)
        if usable(ov,origin,5):
            value=prediction(ov)
            if math.isfinite(value):pending.append(dict(origin=origin,event_time=ov[-1]['event_time'],persistence=ov[-1]['value'],drift=value,process_id=current_process))
    # Retain one forecast per target event to avoid repeated same-horizon scoring.
    unique={}
    for s in scores:unique.setdefault((s['target_event'],s['process_id']),s)
    scores=list(unique.values())
    mse={};metric_status={}
    for m in ('persistence','drift'):
        try:
            mse[m]=stable_mean((s[m]-s['actual'])**2 for s in scores) if scores else None
            metric_status[m]='observed' if scores else 'unavailable'
        except (OverflowError,ValueError):mse[m]=None;metric_status[m]='numerical_range_exceeded'
    estimate=prediction(v)
    if not math.isfinite(estimate):return dict(base,status='abstain',reason='Forecast exceeds finite numerical range')
    return dict(base,status='research_forecast',persistence=v[-1]['value'],drift=estimate,process_id=process_id(v[-1]),evidence_ids=[r['id'] for r in v[-5:]],
                walk_forward={'n':len(scores),'mse':mse,'metric_status':metric_status,'incomparable':incomparable,'origin_limit':100,'predictions':scores,'limitation':'First observed target vintages; no significance or calibration claim. Backfilled single-vintage archives produce no historical scores.'})
