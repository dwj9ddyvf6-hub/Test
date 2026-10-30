"""Expanding-window ridge regression using only matured training labels.
This small reference evaluator is not evidence of market predictability.
"""
import math
from .core import utc


def fit_predict(train, test, fields, ridge=1.0):
    # Train-only standardization; missing sentiment is not imputed as neutral.
    means = [sum(r[f] for r in train)/len(train) for f in fields]
    scales = [max(1e-8,(sum((r[f]-m)**2 for r in train)/len(train))**.5) for f,m in zip(fields,means)]
    def design(r):
        return [1.0]+[(r[f]-m)/s for f,m,s in zip(fields,means,scales)]
    x = [design(r) for r in train]
    n = len(fields)+1
    a = [[sum(v[i]*v[j] for v in x)+(ridge if i==j and i>0 else 0) for j in range(n)] for i in range(n)]
    b = [sum(v[i]*r['target'] for v,r in zip(x,train)) for i in range(n)]
    for i in range(n):
        pivot = max(range(i,n),key=lambda k:abs(a[k][i]))
        a[i],a[pivot],b[i],b[pivot] = a[pivot],a[i],b[pivot],b[i]
        if abs(a[i][i])<1e-12:
            return sum(r['target'] for r in train)/len(train)
        div = a[i][i]
        a[i] = [v/div for v in a[i]]
        b[i] /= div
        for j in range(n):
            if j!=i:
                factor=a[j][i]
                a[j]=[v-factor*w for v,w in zip(a[j],a[i])]
                b[j]-=factor*b[i]
    return sum(v*w for v,w in zip(design(test),b))


def evaluate(rows, min_train=20, cost_bps=5):
    if isinstance(min_train,bool) or not isinstance(min_train,int) or min_train<3 or not math.isfinite(cost_bps) or not 0<=cost_bps<=10000:
        raise ValueError('invalid evaluation settings')
    for r in rows:
        for key in ('entity','horizon','as_of','feature_available_at','label_end','label_available_at'):
            if not isinstance(r.get(key),str) or not r[key].strip(): raise ValueError('missing typed evaluation field '+key)
    if len({(r['entity'],r['horizon']) for r in rows})>1: raise ValueError('mixed entity/horizon evaluation is unsupported')
    rows=sorted(rows,key=lambda r:utc(r['as_of']))
    if len({utc(r['as_of']) for r in rows}) != len(rows):
        raise ValueError('one entity/horizon and unique decision times required')
    for r in rows:
        if utc(r['feature_available_at'])>utc(r['as_of']):
            raise ValueError('feature leakage')
        if utc(r['label_available_at']) < utc(r['label_end']):
            raise ValueError('label availability before label end')
        if utc(r['label_end'])<=utc(r['as_of']):
            raise ValueError('label must end after decision')
        for f in ('target','price_momentum'):
            if isinstance(r[f],bool) or not math.isfinite(r[f]) or abs(r[f])>100: raise ValueError('nonfinite or out-of-range decimal return input')
        if r['sentiment'] is not None and (isinstance(r['sentiment'],bool) or not math.isfinite(r['sentiment']) or abs(r['sentiment'])>1):
            raise ValueError('nonfinite sentiment')
    predictions=[]
    last_end=None
    for i,test in enumerate(rows):
        # Non-overlapping test holding periods; no realized overlapping-label training.
        if last_end and utc(test['as_of'])<last_end: continue
        eligible=[r for r in rows[:i] if utc(r['label_available_at'])<utc(test['as_of']) and r['sentiment'] is not None]
        train=[]
        train_end=None
        for r in eligible:
            if train_end is None or utc(r['as_of'])>=train_end:
                train.append(r)
                train_end=utc(r['label_end'])
        if len(train)<min_train or test['sentiment'] is None: continue
        pred={'as_of':test['as_of'],'label_end':test['label_end'],'actual':test['target'],'n_train':len(train),
              'train_last_label_end':max((r['label_end'] for r in train),key=utc),
              'train_last_label_available_at':max((r['label_available_at'] for r in train),key=utc),
              'zero':0.0,'historical_mean':sum(r['target'] for r in train)/len(train),
              'price_only':fit_predict(train,test,['price_momentum']),
              'price_plus_sentiment':fit_predict(train,test,['price_momentum','sentiment'])}
        predictions.append(pred)
        last_end=utc(test['label_end'])
    metrics={}
    for model in ('zero','historical_mean','price_only','price_plus_sentiment'):
        pnls=[]; previous=0; previous_end=None
        for p in predictions:
            position=1 if p[model]>0 else -1 if p[model]<0 else 0
            continuous=previous_end is not None and utc(p['as_of'])==previous_end
            turnover=abs(position-previous) if continuous else abs(previous)+abs(position)
            pnls.append(position*p['actual']-turnover*cost_bps/10000)
            previous=position
            previous_end=utc(p['label_end'])
        if pnls: pnls[-1]-=abs(previous)*cost_bps/10000
        metrics[model]={'mse':sum((p[model]-p['actual'])**2 for p in predictions)/len(predictions) if predictions else None,
                        'sum_net_return':sum(pnls) if pnls else None,'n':len(predictions)}
    return {'method':'expanding-window fixed ridge; explicit label availability; common complete-case sample; nonoverlapping train and test windows',
            'execution_assumption':'flat between disjoint target windows; net turnover at contiguous boundaries; open/close each separated holding',
            'entity':rows[0]['entity'] if rows else None,'horizon':rows[0]['horizon'] if rows else None,
            'cost_bps':cost_bps,'metrics':metrics,'predictions':predictions,
            'limitation':'No statistical significance or market alpha established. Inputs require audited point-in-time vintages. Net returns omit funding, borrow, impact and nonlinear compounding.'}
