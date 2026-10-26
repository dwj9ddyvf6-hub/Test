#!/usr/bin/env python3
"""Recover actual numeric events and real call texts, without invented events.

Original publisher datasets differ from unreleased EarningsInOne. Derived
metadata retains row/source hashes and explicit availability assumptions.
"""
from pathlib import Path
import argparse, hashlib, json, re
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
NEGATIONS={'no','not','never','neither','without','hardly'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lexicon_score(text,positive,negative):
    tokens=re.findall(r"[A-Za-z]+",text.lower());pos=neg=negated=0
    for i,w in enumerate(tokens):
        val=1 if w in positive else -1 if w in negative else 0
        if not val:continue
        if any(t in NEGATIONS for t in tokens[max(0,i-3):i]):val=-val;negated+=1
        if val>0:pos+=1
        else:neg+=1
    return {'score':(pos-neg)/(pos+neg+1.),'positive_count':pos,'negative_count':neg,'negated_hits':negated,'token_count':len(tokens)}

def historical_sue(events,denominator='absolute_error'):
    """Paper8quarter/min4/shift1 setting on retained ticker earnings records.

    Yahoo source lacks fiscal-quarter IDs. Eight retained releases are not
    proven eight distinct fiscal quarters; revisions/backlogged releases are
    flagged separately instead of guessed or silently removed.

    Appendix C.2 numerator is percentage surprise but describes denominator as
    historical forecast errors; literal absolute-error SD is the primary here.
    A consistent-unit percentage-error-SD sensitivity is separate.
    """
    x=events.sort_values(['symbol','available_at']).copy();error=x['actual_eps']-x['estimate_eps']
    x['eps_surprise']=(error/x['estimate_eps'].replace(0,np.nan));x['eps_surprise_abs_estimate']=error/x['estimate_eps'].abs().replace(0,np.nan)
    x['forecast_error']=error
    feature='forecast_error' if denominator=='absolute_error' else 'eps_surprise'
    x['historical_error_std']=x.groupby('symbol')[feature].transform(lambda a:a.shift(1).rolling(8,min_periods=4).std(ddof=1))
    x['sue']=x['eps_surprise']/x['historical_error_std'].replace(0,np.nan)
    x['prior_error_count']=x.groupby('symbol')[feature].transform(lambda a:a.shift(1).rolling(8,min_periods=1).count()).fillna(0).astype(int)
    return x

def prepare_numeric():
    source=ROOT/'data/earnings_dates_all.csv';x=pd.read_csv(source)
    x=x.rename(columns={'ticker':'symbol','EPS Estimate':'estimate_eps','Reported EPS':'actual_eps','Surprise(%)':'vendor_surprise_pct'})
    x['available_at']=pd.to_datetime(x['earnings_datetime_utc'],utc=True)
    x['source_row']=np.arange(len(x));x['source_sha256']=sha(source);x['source']='Yahoo Finance retrospective EPS dataset in vivek-v-rao/Earnings-Dates pinned7ed98a0'
    x=x[(x['available_at']>=pd.Timestamp('2016-01-01',tz='UTC')) & (x['available_at']<=pd.Timestamp('2026-10-07',tz='UTC')) & x['estimate_eps'].notna() & x['actual_eps'].notna()].copy()
    # Duplicates/restatements do not get interpreted as extra quarterly events.
    x=x.sort_values(['symbol','available_at']).drop_duplicates(['symbol','available_at'],keep='first')
    x['source_knowledge']='Retrospective Yahoo dataset; pre-release estimate vintage and precise actuals availability not independently verified.'
    x['event_id']=x['symbol']+'|'+x['available_at'].astype(str)
    primary=historical_sue(x,'absolute_error');unit=historical_sue(x,'percentage_error')
    primary['sue_percentage_error_sd']=unit['sue'];primary.to_csv(ROOT/'data/numeric-events.csv.gz',index=False)
    return primary

MONEY=r'\$?\(?-?\d[\d,]*(?:\.\d+)?\)?[BMK]?'
def amount(s):
    s=s.strip().replace('$','').replace(',','');sign=-1 if s.startswith('(') or s.startswith('-') else 1;s=s.strip('()-');unit=s[-1] if s[-1] in 'BMK' else '';scale={'B':1e9,'M':1e6,'K':1e3}.get(unit,1.);return sign*float(s[:-1] if unit else s)*scale

def prepare_news(news_root):
    rows=[];seen=set();rejected=[]
    for path in sorted(Path(news_root).rglob('news_by_symbol/*.json')):
        source=json.loads(path.read_text());source=source if isinstance(source,list) else source.get('news',source.get('data',[]))
        for row in source:
            rid=str(row.get('id'));headline=str(row.get('headline',''))
            if rid in seen:continue
            seen.add(rid)
            if not re.search(r'\bReports?\b.*\bQ[1-4]\b|\bQ[1-4]\b.*\bEPS\b',headline,re.I) or re.search(r'\bSees\b|May Not Compare|In Q[1-4] 20\d\d',headline,re.I):continue
            m=re.search(r'\bEPS\s+('+MONEY+r')\s+vs\.?\s+('+MONEY+r')\s+(?:Est\.?|Eset\.?|Expected)',headline,re.I)
            if not m:continue
            symbols=[s.replace('/','.') for s in row.get('symbols',[])];selected=path.stem
            if 'GOOGL' in symbols or selected in ('GOOG','GOOGL'):selected='GOOGL'
            available=max(pd.Timestamp(row['created_at']),pd.Timestamp(row.get('updated_at') or row['created_at']))
            actual,estimate=amount(m.group(1)),amount(m.group(2))
            if estimate==0:continue
            rev=re.search(r'(?:Sales|Revenue)\s+('+MONEY+r')\s+vs\.?\s+('+MONEY+r')\s+(?:Est\.?|Eset\.?)',headline,re.I)
            out={'event_id':'benzinga-'+rid,'symbol':selected,'available_at':str(available),'created_at':row['created_at'],'updated_at':row.get('updated_at'),'actual_eps':actual,'estimate_eps':estimate,'eps_surprise':(actual-estimate)/estimate,'eps_surprise_abs_estimate':(actual-estimate)/abs(estimate),'source':'Original Midna cached Benzinga headline','source_file':str(path),'source_sha256':sha(path),'source_id':rid,'url':row.get('url'),'headline':headline,'adjusted_eps':'Adj.' in headline,'publication_time_policy':'max(created_at,updated_at); cached revisions cannot be read before their update','actual_revenue':amount(rev.group(1)) if rev else None,'estimate_revenue':amount(rev.group(2)) if rev else None}
            rows.append(out)
    out=pd.DataFrame(rows).sort_values('available_at').drop_duplicates(['symbol','available_at']);out.to_csv(ROOT/'data/news-numeric-events.csv',index=False)
    return out

def prepare_calls():
    p=ROOT/'data/2024-earnings-call-transcripts.jsonl';datefile=ROOT/'data/fioneer-earnings_dates.json';dates=json.loads(datefile.read_text());lm=pd.read_csv(ROOT/'data/lm-2018.csv')
    cols={c.lower():c for c in lm};positive=set(lm.loc[lm[cols['positive']]>0,cols['word']].str.lower());negative=set(lm.loc[lm[cols['negative']]>0,cols['word']].str.lower())
    rows=[];missing=[];call_source_sha=sha(p);date_source_sha=sha(datefile);lexicon_sha=sha(ROOT/'data/lm-2018.csv')
    for i,line in enumerate(p.open()):
        r=json.loads(line);key=f'{r["ticker"]}_{r["year"]}_Q{r["q"]}';call_date=dates.get(key)
        if not call_date:missing.append(key);continue
        segments=r['conversations'];text='\n'.join(str(s['content']) for s in segments if s.get('speaker','').lower()!='operator')
        scores=lexicon_score(text,positive,negative)
        row={'event_id':key,'symbol':r['ticker'].upper().replace('-','.'),'call_date':call_date,'source_row':i,'source_sha256':call_source_sha,'call_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'date_map_sha256':date_source_sha,'score_type':'deterministic_LoughranMcDonald_2018_negation_adjusted; NOT GPT-5-mini','score_model_sha256':lexicon_sha,'availability_assumption':'Actual call date retained; historical transcript publication timestamp is unavailable. Primary allows24h after call-date23:59:59ET; sensitivity48h.'}
        row.update(scores)
        # End-of-date already overstates typical call completion and deliberately
        # shifts entry later than the paper. It is an assumption, not proof.
        row['available_at_0h']=str(pd.Timestamp(call_date+' 23:59:59',tz='America/New_York').tz_convert('UTC'))
        row['available_at_24h']=str(pd.Timestamp(call_date+' 23:59:59',tz='America/New_York').tz_convert('UTC')+pd.Timedelta(hours=24))
        row['available_at_48h']=str(pd.Timestamp(call_date+' 23:59:59',tz='America/New_York').tz_convert('UTC')+pd.Timedelta(hours=48))
        rows.append(row)
    out=pd.DataFrame(rows).sort_values('call_date');out.to_csv(ROOT/'data/call-score-events.csv',index=False)
    return out,missing,len(positive),len(negative)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--news-root',type=Path,default=ROOT.parent/'research/repository-assets/recovered/Midna');args=a.parse_args();ROOT.joinpath('data').mkdir(exist_ok=True)
    n=prepare_numeric();news=prepare_news(args.news_root);calls,missing,pos,neg=prepare_calls()
    report={'actual_retrospective_numeric_events':len(n),'numeric_symbols':int(n.symbol.nunique()),'native_sue_valid':int(np.isfinite(n.sue).sum()),'actual_timestamped_numeric_news':len(news),'actual_call_texts_with_source_dates':len(calls),'call_date_missing':missing,'lexicon_positive_words':pos,'lexicon_negative_words':neg,'invented_events':0,'paid_model_calls':0,'paper_profit_exactly_reproduced':False}
    (ROOT/'data/preparation-receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
