"""Finite R17 ETF opportunity experiment. No production imports or writes."""
import csv,gzip,hashlib,json,math,datetime
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'EXPERIMENT_PROTOCOL.json').read_text())
SYMS=P['universe']; RULES=list(P['rules'])

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(provider):
    path=P['inputs'][0 if provider=='ALPACA' else 2]
    frame=pd.read_csv(path);frame=frame[frame.symbol.isin(SYMS)].copy()
    assert not frame.duplicated(['date','symbol']).any()
    dates=sorted(frame.loc[frame.symbol=='QQQ','date'].tolist())
    values={k:frame.pivot(index='date',columns='symbol',values=k).reindex(index=dates,columns=SYMS).astype(float).to_numpy() for k in ['open','close','volume']}
    if provider=='ALPACA':
        raw=pd.read_csv(P['inputs'][1]);raw=raw[raw.symbol.isin(SYMS)]
        values['dollar_volume']=(raw.pivot(index='date',columns='symbol',values='close')*raw.pivot(index='date',columns='symbol',values='volume')).reindex(index=dates,columns=SYMS).to_numpy()
    else:values['dollar_volume']=values['close']*values['volume']
    return dates,values

def weights(rule,c,i):
    """Read only observations through completed close i. Scale gross elsewhere."""
    z=np.zeros(len(SYMS));q=SYMS.index('QQQ')
    if rule.endswith('_HOLD'):z[SYMS.index(rule.split('_')[0])]=1.;return z
    if i<251:z[q]=1.;return z
    hist=c[i-251:i+1]; eligible=np.all(np.isfinite(hist)&(hist>0),axis=0)
    m126=np.log(c[i]/c[i-126]);m21=np.log(c[i]/c[i-21]);m3=np.log(c[i]/c[i-3]);rel=m126-m126[q]
    vol=np.std(np.diff(np.log(c[i-63:i+1]),axis=0),axis=0,ddof=1)
    ma=np.mean(c[i-199:i+1],axis=0);peak=np.max(c[i-19:i+1],axis=0);dd=c[i]/peak-1
    score=m126.copy();n=1 if rule in ('LEADER1','ESCAPE1') else 3
    if rule in ('RELATIVE3','VOLADJ3','ACCEL3','REPAIR3'):
        eligible&=(rel>0);eligible[q]=False;score=rel.copy()
    if rule=='VOLADJ3':score=rel/np.maximum(vol,1e-8)
    if rule=='ACCEL3':
        score=(m21-m126/6)/np.maximum(vol,1e-8);eligible&=(score>0)&(c[i]>ma)
    if rule=='REPAIR3':eligible&=(dd<=-.02)&(dd>=-.10)&(m3>0)&(c[i]>ma)
    if rule=='ESCAPE1':eligible&=(m126>0)&(c[i]>ma)
    order=sorted(np.where(eligible&np.isfinite(score))[0],key=lambda j:(-score[j],SYMS[j]))[:n]
    for j in order:z[j]=1/n
    if rule!='ESCAPE1':z[q]+=(n-len(order))/n
    return z

def value_held(units,marks):
    active=units>1e-12
    if not np.all(np.isfinite(units)) or np.any(units < -1e-8):raise ValueError('Invalid holdings')
    if not np.all(np.isfinite(marks[active]) & (marks[active]>0)):raise ValueError('Missing held valuation')
    return float(units[active]@marks[active])

def settlement_lag(date):return 3 if date<'2017-09-05' else 2 if date<'2024-05-28' else 1

def run_account(dates,v,provider,start,end,rule,gross,bps,save=True):
    op=v['open'];cl=v['close'];dv=v['dollar_volume'];cost=bps/10000
    ids=[i for i,d in enumerate(dates) if start<=d<=end];assert ids
    a,b=ids[0],ids[-1]; margin=gross>1
    units=np.zeros(len(SYMS));desired=units.copy();cash=100000.;receivables=[]
    total_fees=0.;interest=0.;fills=[];navs=[];targets=[];pending_weights=None;settlement_block_days=0;capacity_hits=0;maintenance_count=0
    # Previous month-end only, or zero-information static index.
    origins=[i for i in range(a) if i+1<len(dates) and dates[i][:7]!=dates[i+1][:7]]
    origin=origins[-1] if origins else a-1
    pending_weights=weights(rule,cl,origin)*gross
    targets.append({'decision_date':dates[origin],'execution_start':dates[a],'weights':dict(zip(SYMS,pending_weights)),'reason':'initial'})
    lastclose=cl[a-1].copy();previous_day=datetime.date.fromisoformat(dates[a-1]);bankrupt=False
    for i in ids:
        day=datetime.date.fromisoformat(dates[i]);elapsed=(day-previous_day).days
        debt=max(0.,-(cash+sum(x[1] for x in receivables))) if margin else 0.
        charge=debt*.10*elapsed/365;cash-=charge;interest+=charge
        matured=sum(vv for due,vv in receivables if due<=i);cash+=matured;receivables=[(due,vv)for due,vv in receivables if due>i]
        marks=np.where(np.isfinite(op[i])&(op[i]>0),op[i],lastclose)
        nav=cash+sum(x[1]for x in receivables)+value_held(units,marks)
        if not math.isfinite(nav):raise ValueError('Nonfinite account NAV')
        if nav<=0:bankrupt=True;break
        if pending_weights is not None:
            desired=np.divide(pending_weights*nav,marks,out=units.copy(),where=np.isfinite(marks)&(marks>0));pending_weights=None
        cap=np.maximum(0,np.nan_to_num(dv[i-1],nan=0.))*0.001
        for j in range(len(SYMS)):
            if not np.isfinite(op[i,j]) or op[i,j]<=0:continue
            qty=min(max(0.,units[j]-desired[j]),cap[j]/op[i,j]);capacity_hits+=int(units[j]-desired[j]>cap[j]/op[i,j]+1e-8)
            if qty>1e-10:
                notional=qty*op[i,j];fee=notional*cost;units[j]-=qty;cap[j]-=notional;total_fees+=fee
                receivables.append((i+settlement_lag(dates[i]),notional-fee))
                fills.append({'date':dates[i],'symbol':SYMS[j],'side':'sell','units':qty,'price':float(op[i,j]),'fee':fee,'settlement_index':i+settlement_lag(dates[i])})
        needed=np.maximum(0,desired-units);valid=np.isfinite(op[i])&(op[i]>0);needed[~valid]=0.
        capacity=np.divide(cap,op[i],out=np.zeros(len(SYMS)),where=valid);capacity_hits+=int(np.any(needed>capacity+1e-8));needed=np.minimum(needed,capacity)
        # Gross target is a decision target, not forced rebalancing each day. Entry budget prevents new fills exceeding target.
        nav=cash+sum(x[1]for x in receivables)+value_held(units,marks)
        if margin:
            available=max(0.,gross*nav-value_held(units,marks));denom=1+gross*cost
        else:available=max(0.,cash);denom=1+cost
        requested=float(needed@np.where(valid,op[i],0.));scale=min(1.,available/(requested*denom))if requested>0 else 0.
        if not margin and requested>cash+1e-6 and receivables:settlement_block_days+=1
        for j in range(len(SYMS)):
            qty=needed[j]*scale
            if qty>1e-10:
                notional=qty*op[i,j];fee=notional*cost;units[j]+=qty;cash-=notional+fee;total_fees+=fee
                fills.append({'date':dates[i],'symbol':SYMS[j],'side':'buy','units':qty,'price':float(op[i,j]),'fee':fee,'settlement_index':None})
        lastclose=np.where(np.isfinite(cl[i])&(cl[i]>0),cl[i],lastclose)
        held=value_held(units,lastclose);receivable=sum(x[1]for x in receivables);nav=cash+receivable+held
        assert margin or cash>=-1e-6
        if not math.isfinite(nav):raise ValueError('Nonfinite account NAV')
        if nav<=0:bankrupt=True;break
        navs.append({'date':dates[i],'nav':nav,'cash':cash,'receivables':receivable,'net_debit':max(0,-cash-receivable),'gross':held/nav,'holdings':dict((SYMS[j],float(units[j]))for j in np.where(units>1e-10)[0])})
        if i<b:
            if margin and held/nav>2.:
                pending_weights=np.zeros(len(SYMS));active=units>1e-12;pending_weights[active]=(units[active]*lastclose[active]/held)*gross;maintenance_count+=1;reason='maintenance'
            elif not rule.endswith('_HOLD') and dates[i][:7]!=dates[i+1][:7]:pending_weights=weights(rule,cl,i)*gross;reason='month_end'
            else:reason=None
            if reason:targets.append({'decision_date':dates[i],'execution_start':dates[i+1],'weights':dict(zip(SYMS,pending_weights)),'reason':reason})
        previous_day=day
    net=0. if bankrupt else navs[-1]['nav']-value_held(units,lastclose)*cost
    series=np.array([100000.]+[n['nav']for n in navs]);series[-1]=net
    years=(datetime.date.fromisoformat(dates[b])-datetime.date.fromisoformat(dates[a])).days/365.25
    result={'provider':provider,'start':dates[a],'end':dates[b],'rule':rule,'gross_target':gross,'cost_bps':bps,'net_terminal':net,'return':net/100000-1,'cagr':(net/100000)**(1/years)-1 if net>0 else -1.,'max_drawdown':float(np.min(series/np.maximum.accumulate(series)-1)),'fees':total_fees,'terminal_fee_reserve':value_held(units,lastclose)*cost,'interest':interest,'fills':len(fills),'decisions':len(targets),'settlement_block_days':settlement_block_days,'capacity_hits':capacity_hits,'maintenance_events':maintenance_count,'max_actual_gross':max(n['gross']for n in navs),'bankrupt':bankrupt,'initial_nav':100000.,'all_history_reused_discovery':True}
    if save:
        name=f'{provider}_{start}_{end}_{rule}_G{gross}_C{bps}'
        with gzip.open(ROOT/'accounts'/f'{name}.json.gz','wt')as f:json.dump({'summary':result,'targets':targets,'nav':navs,'fills':fills},f,separators=(',',':'),allow_nan=False)
    return result

def main():
    (ROOT/'accounts').mkdir(exist_ok=True)
    receipt={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':sha(ROOT/'EXPERIMENT_PROTOCOL.json'),'producer_sha256':sha(__file__),'input_sha256':{p:sha(p)for p in P['inputs']}}
    (ROOT/'RUN_START.json').write_text(json.dumps(receipt,indent=2)+'\n')
    results=[]
    for provider,windows in P['windows'].items():
        dates,v=load(provider)
        for window in windows:
            start,end=window.split('/')
            for gross in P['risk_and_cost_cells']['gross_targets']:
                for bps in P['risk_and_cost_cells']['per_side_basis_points']:
                    for rule in RULES:results.append(run_account(dates,v,provider,start,end,rule,gross,bps))
            print(provider,window,len(results),flush=True)
    by={(x['provider'],x['start'],x['end'],x['gross_target'],x['cost_bps'],x['rule']):x for x in results}
    for x in results:
        base=(x['provider'],x['start'],x['end'])
        q=by[base+(x['gross_target'],x['cost_bps'],'QQQ_HOLD')];cashq=by[base+(.98,x['cost_bps'],'QQQ_HOLD')]
        x['excess_same_gross_qqq_return_pp']=(x['return']-q['return'])*100;x['excess_cash_qqq_return_pp']=(x['return']-cashq['return'])*100
    (ROOT/'RESULTS.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    with (ROOT/'RESULTS.csv').open('w')as f:w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    receipt['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();receipt['accounts']=len(results);receipt['inputs_unchanged']=all(sha(p)==h for p,h in receipt['input_sha256'].items());receipt['run_results_sha256']=sha(ROOT/'RESULTS.json')
    (ROOT/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
