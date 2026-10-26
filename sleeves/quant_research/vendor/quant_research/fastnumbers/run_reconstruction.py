#!/usr/bin/env python3
"""Event-based financial reconstructions on genuine numeric and language inputs.

Native Appendix weight formula and lagged quarterly standardization retained;
original unreleased data/GPT outputs are replaced only with labelled adapters.
"""
from pathlib import Path
import argparse,hashlib,json,sys
from functools import lru_cache
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'finrlx'))
from load_arrays import load_union

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cdf_scores(events,signal='sue',available='available_at',mode='expanding',history_start='2022-01-01',min_history=30):
    """Monthly frozen market CDF; no event in current month changes its own rank."""
    x=events.copy();x['available_at_used']=pd.to_datetime(x[available],utc=True);x['cdf_percentile']=np.nan;x['cdf_count']=0
    month_labels=x.available_at_used.dt.strftime('%Y-%m')
    for month in sorted(month_labels.unique()):
        cutoff=pd.Timestamp(month+'-01',tz='UTC');lower=cutoff-pd.DateOffset(months=12) if mode=='trailing12m' else pd.Timestamp(history_start,tz='UTC')
        h=x.loc[(x.available_at_used>=lower)&(x.available_at_used<cutoff),signal].to_numpy(float);h=np.sort(h[np.isfinite(h)])
        mask=month_labels==month;v=x.loc[mask,signal].to_numpy(float)
        x.loc[mask,'cdf_count']=len(h)
        if len(h)>=min_history:
            p=(np.searchsorted(h,v,side='left')+np.searchsorted(h,v,side='right'))/(2*len(h));p[~np.isfinite(v)]=np.nan;x.loc[mask,'cdf_percentile']=p
    return x

@lru_cache(maxsize=8)
def session_closes(first,last):
    schedule=mcal.get_calendar('NYSE').schedule(start_date=first,end_date=last)
    return {str(d.date()):str(t) for d,t in schedule.market_close.items()}

def actual_session(x,dates,availability='available_at_used'):
    """Actual calendar, UTC->ET; next RTHopen after availability plus1min."""
    opens=pd.DatetimeIndex([pd.Timestamp(str(d.date())+' 09:30:00',tz='America/New_York').tz_convert('UTC') for d in dates])
    closes=session_closes(str(dates[0].date()),str(dates[-1].date()))
    t=pd.DatetimeIndex(pd.to_datetime(x[availability],utc=True))+pd.Timedelta(minutes=1);ix=opens.searchsorted(t,side='left');valid=ix<len(dates);out=x.loc[valid].copy();out['session_date']=[str(dates[i].date()) for i in ix[valid]];out['session_index']=ix[valid];out['entry_time']=[str(opens[i]) for i in ix[valid]];out['exit_time']=[closes[str(dates[i].date())] for i in ix[valid]];out['holding_minutes']=[(pd.Timestamp(closes[str(dates[i].date())])-opens[i]).total_seconds()/60. for i in ix[valid]];return out

def load_event_price_extension(path,needed_keys=None):
    """Read explicitly raw same-session prices without changing signal cohorts."""
    if Path(path).suffix=='.parquet':
        import pyarrow.parquet as pq
        fields=set(pq.read_schema(path).names);columns=['symbol','date','open','close','volume','valid','provider_symbol','asset_uuid','format_mapping_receipt'];frame=pd.read_parquet(path,columns=[c for c in columns if c in fields])
    else:frame=pd.read_csv(path,float_precision='round_trip')
    required={'symbol','date','open','close','volume','valid'}
    if not required.issubset(frame):raise ValueError(f'Missing extension fields: {required-set(frame)}')
    if frame.duplicated(['symbol','date']).any():raise ValueError('Duplicate execution-price rows')
    if needed_keys is not None:
        frame=frame[pd.MultiIndex.from_frame(frame[['symbol','date']]).isin(needed_keys)]
    result={(str(row.symbol),str(row.date)[:10]):row.to_dict() for _,row in frame.iterrows()}
    supplement=Path(path).parent/'daily-symbol-format.parquet'
    if Path(path).name=='daily.parquet' and supplement.exists():
        more=load_event_price_extension(supplement,needed_keys)
        if set(result)&set(more):raise ValueError('Ambiguous raw price/symbol-format overlap')
        result.update(more)
    return result

def price_events(events,panel,extension=None):
    dates=pd.DatetimeIndex(panel['dates']);symbols=list(panel['symbols'].astype(str));lookup={s:j for j,s in enumerate(symbols)}
    x=actual_session(events,dates);kept=[];rejected=[]
    for _,r in x.iterrows():
        s=r['symbol'];i=int(r.session_index)
        source='original all-adjusted daily price proxy';provider_symbol=s;asset_uuid=None;format_mapping=None
        if extension is not None and '2024-01-01'<=r.session_date<='2025-12-31':
            quote=extension.get((s,r.session_date))
            if quote is None:rejected.append({'event_id':r.event_id,'symbol':s,'reason':'raw_extension_same_session_quote_absent'});continue
            if quote.get('valid')!=True or not float(quote['volume'])>0:rejected.append({'event_id':r.event_id,'symbol':s,'reason':'raw_extension_quote_invalid_or_zero_volume'});continue
            op=float(quote['open']);cl=float(quote['close']);source='explicit Alpaca raw1Day historical-asof2025-12-31 price extension';provider_symbol=quote.get('provider_symbol',s);asset_uuid=quote.get('asset_uuid');format_mapping=quote.get('format_mapping_receipt')
        else:
            if s not in lookup:rejected.append({'event_id':r.event_id,'symbol':s,'reason':'symbol_absent_genuine_price_panel'});continue
            j=lookup[s];op=float(panel['all_open'][i,j]);cl=float(panel['all_close'][i,j])
        if not(np.isfinite(op) and np.isfinite(cl) and op>0 and cl>0):rejected.append({'event_id':r.event_id,'symbol':s,'reason':'actual_session_price_missing'});continue
        d=r.to_dict();d.update({'entry_price':op,'exit_price':cl,'forward_log_return':np.log(cl/op),'forward_simple_return':cl/op-1.,'execution_price_source':source,'execution_provider_symbol':provider_symbol,'execution_asset_uuid':asset_uuid,'execution_format_mapping_receipt':format_mapping});kept.append(d)
    return pd.DataFrame(kept),rejected

def weights(events,signal):
    x=events[np.isfinite(events[signal])&np.isfinite(events.cdf_percentile)].copy();
    if 'session_N' not in x:x['session_N']=x.groupby('session_date')['event_id'].transform('count')
    p=x.cdf_percentile.to_numpy();x['weight']=np.where(np.abs(p-.5)>=.4,(2./x.session_N.to_numpy())*2*(p-.5),0.)
    return x

def metric(returns,dates,trades=0):
    dates=list(dates);r=np.array(returns,float);nv=np.r_[1,np.cumprod(1+r)]
    return {'sessions':len(r),'start':str(dates[0]) if len(dates) else None,'end':str(dates[-1]) if len(dates) else None,'total_return':float(nv[-1]-1),'cagr':float(nv[-1]**(252/len(r))-1) if len(r) and nv[-1]>0 else None,'sharpe':float(r.mean()/r.std(ddof=1)*np.sqrt(252)) if len(r)>1 and r.std(ddof=1)>0 else None,'max_drawdown':float(np.min(nv/np.maximum.accumulate(nv)-1)),'trades':trades}

def pnl(events,all_dates,start,end,cost=15.,native_log=False):
    """Intraday round-trip cash ledger, actual notional charges and borrow.

    Native comparator multiplies Appendix weights by paper log returns.
    Economic uses actual signed shares, simple cash PnL, full two-sided fees,
    3% annual short borrow and5%annual positive debit financing pro rata hours.
    """
    dates=[str(d.date()) for d in all_dates if start<=str(d.date())<=end];nav=100000.;led=[];tr=[]
    groups={d:g for d,g in events.groupby('session_date')}
    for date in dates:
        g=groups.get(date);prior=nav;gain=charges=borrow=financing=short_value=gross=0.;native=0.;IC=None;count=0;opening_cash=prior;entry_fees=0.;signed_entry_notional=0.
        if g is not None:
            valid=g[g.weight!=0];count=len(valid);gross=float(valid.weight.abs().sum());short_value=float(-valid.loc[valid.weight<0,'weight'].sum());net_exposure=float(valid.weight.sum());signed_entry_notional=prior*net_exposure;entry_fees=prior*gross*cost/10000.;opening_cash=prior-signed_entry_notional-entry_fees;debit=max(0.,-opening_cash/prior)
            if len(g)>=3 and g['signal_for_ic'].nunique()>1 and g.forward_log_return.nunique()>1:IC=float(spearmanr(g.signal_for_ic,g.forward_log_return).statistic)
            for _,r in valid.iterrows():
                hours=(pd.Timestamp(r.exit_time)-pd.Timestamp(r.entry_time)).total_seconds()/3600.;qty=prior*r.weight/r.entry_price;gross_pnl=qty*(r.exit_price-r.entry_price);fee=(abs(qty)*r.entry_price+abs(qty)*r.exit_price)*cost/10000.;bf=abs(min(qty,0))*r.entry_price*.03*hours/(365*24);native_contrib=float(r.weight*r.forward_log_return)
                gain+=gross_pnl;charges+=fee;borrow+=bf;native+=native_contrib
                tr.append({'date':date,'event_id':r.event_id,'symbol':r.symbol,'available_at':str(r.available_at_used),'entry_time':r.entry_time,'exit_time':r.exit_time,'entry_price':r.entry_price,'exit_price':r.exit_price,'weight':r.weight,'shares':qty,'side':'LONG' if qty>0 else 'SHORT','entry_notional':abs(qty)*r.entry_price,'exit_notional':abs(qty)*r.exit_price,'gross_pnl':gross_pnl,'commission_slippage_cost':fee,'short_borrow_cost':bf,'net_pnl_before_financing':gross_pnl-fee-bf,'cdf_percentile':r.cdf_percentile,'cdf_history_count':r.cdf_count,'session_N':r.session_N})
            holding_hours=max((pd.Timestamp(row.exit_time)-pd.Timestamp(row.entry_time)).total_seconds()/3600. for _,row in valid.iterrows()) if len(valid) else 0.
            financing=prior*debit*.05*holding_hours/(365*24)
        net=(native*prior-charges-borrow-financing) if native_log else gain-charges-borrow-financing;nav+=net
        if nav<=0:raise RuntimeError('Portfolio insolvency; do not clamp or hide')
        led.append({'date':date,'nav':nav,'net_return':net/prior,'opening_cash_after_trades':opening_cash,'signed_entry_notional':signed_entry_notional,'entry_transaction_cost':entry_fees,'closing_cash_after_roundtrip':nav,'gross_pnl':gain,'transaction_cost':charges,'short_borrow':borrow,'leverage_financing':financing,'gross_exposure':gross,'short_exposure':short_value,'trades':count,'session_ic':IC,'native_log_weight_pnl':native})
    out=pd.DataFrame(led);metrics=metric(out.net_return,out.date,len(tr));ics=out.session_ic.dropna();metrics.update({'active_sessions':int((out.trades>0).sum()),'mean_gross_exposure_all_sessions':float(out.gross_exposure.mean()),'mean_gross_exposure_active_sessions':float(out.loc[out.trades>0,'gross_exposure'].mean()) if (out.trades>0).any() else 0.,'total_cost_dollars':float(out.transaction_cost.sum()),'mean_session_spearman_ic':float(ics.mean()) if len(ics) else None,'ic_session_count':len(ics)})
    return out,pd.DataFrame(tr),metrics

def matched_benchmark(panel,ledger,symbol,cost=15.):
    syms=list(panel['symbols'].astype(str));dates=list(panel['dates'].astype(str));j=syms.index(symbol);i0=dates.index(ledger.date.iloc[0]);i1=dates.index(ledger.date.iloc[-1]);op=float(panel['all_open'][i0,j]);cl=panel['all_close'][i0:i1+1,j];nv=np.r_[1,cl/op/(1+cost/10000)*(1-cost/10000)];rr=nv[1:]/nv[:-1]-1
    return metric(rr,ledger.date)

def main(panel_path,outdir=None,price_extension=None):
    outdir=Path(outdir) if outdir else ROOT/'results';outdir.mkdir(parents=True,exist_ok=True);panel=load_union(panel_path);dates=pd.DatetimeIndex(panel['dates']);extension=None
    numeric=pd.read_csv(ROOT/'data/numeric-events.csv.gz');numeric['sue_canonical_raw_error']=numeric['forecast_error']/numeric['historical_error_std'].replace(0,np.nan);calls=pd.read_csv(ROOT/'data/call-score-events.csv');summary={'paper_profit_exactly_reproduced':False,'real_numeric_events':len(numeric),'real_call_text_events':len(calls),'actual_numeric_news_events':len(pd.read_csv(ROOT/'data/news-numeric-events.csv')),'paid_model_calls':0,'broker_orders':0,'principal':'Canonical source-body SUE with full-cohort weights; literal Appendix formulation is a separate ambiguity diagnostic. Priceable-only prior results retained under priced-subset-diagnostics are not principal.','protocol_sha256':sha(ROOT/'protocol.json'),'panel_sha256':sha(panel_path),'augmentation_sha256':sha(Path(panel_path).parent/'finrlx-augmentation/panel.npz'),'variants':{},'execution_scope':'Alpaca daily open/close proxy for regular-session holding period:390minutes on normal days,210 on early closes. Calendar timestamps are intended execution times, not individual auction print timestamps. No5minute/one-minute fidelity is asserted for this ledger.'}
    if price_extension:
        needed=set()
        for source,availability in [(numeric,'available_at')]+[(calls,f'available_at_{lag}h') for lag in [0,24,48]]:
            sessions=actual_session(source,dates,availability);sessions=sessions[sessions.session_date.between('2024-01-01','2025-12-31')];needed.update(zip(sessions.symbol,sessions.session_date))
        extension=load_event_price_extension(price_extension,needed)
    variants=[('numeric_sue_canonical_raw_error','sue_canonical_raw_error','expanding'),('numeric_sue_literal_expanding','sue','expanding'),('numeric_sue_pct_sd_expanding','sue_percentage_error_sd','expanding'),('numeric_sue_literal_trailing12m','sue','trailing12m')]
    if price_extension:
        summary['expanded_execution_price_coverage']={'path':str(price_extension),'sha256':sha(price_extension),'registered_after_original_diagnostic_returns':True,'parameters_changed':False,'N_changed':False,'price_policy':'Raw1Day, asof2025-12-31, valid positiveOHLC/volume only; missing remains unexecuted. Original all-adjusted proxy retained outside2024–2025.','benchmark_policy':'Matched QQQ/SPY benchmark retains original all-adjusted total-return proxy.'}
        supplement=Path(price_extension).parent/'daily-symbol-format.parquet'
        if Path(price_extension).name=='daily.parquet' and supplement.exists():
            summary['expanded_execution_price_coverage']['verified_format_supplement']={'path':str(supplement),'sha256':sha(supplement),'identity_proofs':str(supplement.parent/'symbol-format-mappings.json'),'receipt':str(supplement.parent/'symbol-format-price-manifest.json'),'original_event_identifiers_retained':True}
    for name,signal,mode in variants:
        x=cdf_scores(numeric,signal,mode=mode,min_history=30);x=x[np.isfinite(x[signal])&np.isfinite(x.cdf_percentile)].copy();cohort=actual_session(x,dates);x=cohort.copy();x['session_N']=x.groupby('session_date')['event_id'].transform('count');x[['event_id','symbol','session_date','session_N','cdf_count','cdf_percentile',signal]].to_csv(outdir/(name+'-full-cohort-N.csv.gz'),index=False);priced,rejected=price_events(x,panel,extension);priced['signal_for_ic']=priced[signal];priced=weights(priced,signal);priced.to_csv(outdir/(name+'-events.csv.gz'),index=False)
        (outdir/(name+'-missing-price-events.json')).write_text(json.dumps(rejected,indent=2));summary['variants'][name]={'full_signal_cohort_events':len(x),'full_cohort_symbols':int(x.symbol.nunique()),'priceable_events':len(priced),'rejected_events':len(rejected),'unexecuted_missing_capital_policy':'Full-cohort session_N assigned before missing-price filter; missing events remain unexecuted, never reallocated.','source':'Retrospective Yahoo actual/consensus estimates; availability/revision vintage unresolved.','costs':{}}
        for c in [0.,1.,10.,15.,30.,60.]:
            for period,start,end in [('paper_test','2024-01-01','2025-12-31'),('extended_test','2024-01-01','2026-10-07')]:
                label=f'{name}-{period}-{c:g}bps';nav,tr,stats=pnl(priced,dates,start,end,c);nav.to_csv(outdir/(label+'-nav.csv'),index=False);tr.to_csv(outdir/(label+'-trades.csv'),index=False);stats['QQQ_same_dates']=matched_benchmark(panel,nav,'QQQ',c);stats['SPY_same_dates']=matched_benchmark(panel,nav,'SPY',c);summary['variants'][name]['costs'][f'{period}_{c:g}']=stats
        native_nav,_,native_stats=pnl(priced,dates,'2024-01-01','2025-12-31',1.,native_log=True);native_nav.to_csv(outdir/(name+'-native-log-1bps-nav.csv'),index=False);summary['variants'][name]['native_log_weight_comparator']=native_stats
        print(name,'executed',len(priced),'events',flush=True)
    for lag in [0,24,48]:
        name=f'language_lm2018_delay{lag}h';x=cdf_scores(calls,signal='score',available=f'available_at_{lag}h',history_start='2023-01-01',min_history=30);x=x[np.isfinite(x.score)&np.isfinite(x.cdf_percentile)].copy();cohort=actual_session(x,dates);x=cohort.copy();x['session_N']=x.groupby('session_date')['event_id'].transform('count');x[['event_id','symbol','session_date','session_N','cdf_count','cdf_percentile','score']].to_csv(outdir/(name+'-full-cohort-N.csv.gz'),index=False);priced,rejected=price_events(x,panel,extension);priced['signal_for_ic']=priced.score;priced=weights(priced,'score');priced.to_csv(outdir/(name+'-events.csv.gz'),index=False)
        summary['variants'][name]={'full_signal_cohort_events':len(x),'full_cohort_symbols':int(x.symbol.nunique()),'priceable_events':len(priced),'rejected_events':len(rejected),'unexecuted_missing_capital_policy':'Full-cohort session_N assigned before missing-price filter; missing events remain unexecuted, never reallocated.','score_type':'Actual transcript text, deterministic Loughran-McDonald2018negation-adjusted counts; not GPT-5-mini','assumed_availability_hours_after_call_date_end':lag,'primary':lag==24,'costs':{}}
        for c in [0.,1.,10.,15.,30.,60.]:
            label=f'{name}-{c:g}bps';nav,tr,stats=pnl(priced,dates,'2024-07-01','2025-03-31',c);nav.to_csv(outdir/(label+'-nav.csv'),index=False);tr.to_csv(outdir/(label+'-trades.csv'),index=False);stats['QQQ_same_dates']=matched_benchmark(panel,nav,'QQQ',c);stats['SPY_same_dates']=matched_benchmark(panel,nav,'SPY',c);summary['variants'][name]['costs'][str(c)]=stats
        print(name,'executed',len(priced),'events',flush=True)
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--panel',type=Path,default=ROOT.parent/'data/panel.npz');a.add_argument('--out',type=Path);a.add_argument('--price-extension',type=Path);args=a.parse_args();main(args.panel,args.out,args.price_extension)
