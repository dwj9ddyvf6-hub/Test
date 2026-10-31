import json, math, sys

payload=json.load(sys.stdin)
cohort=payload['cohort']; closes=payload['closes']; n=505
weight=sum(group['weight_percent'] for group in cohort['issuers'])
issuer_returns=[]; issuer_indexes=[]
for group in cohort['issuers']:
    mass=sum(line['weight_percent'] for line in group['securities'])
    returns=[]
    for t in range(1,n):
        returns.append(sum(line['weight_percent']*math.log(closes[line['symbol']][t]/closes[line['symbol']][t-1]) for line in group['securities'])/mass)
    index=[1.0]
    for r in returns:index.append(index[-1]*math.exp(r))
    issuer_returns.append(returns);issuer_indexes.append(index)
breadth=[None]*n
for t in range(1,n):breadth[t]=sum(group['weight_percent']*(1 if issuer_returns[j][t-1]>0 else -1 if issuer_returns[j][t-1]<0 else 0) for j,group in enumerate(cohort['issuers']))/weight
hl=[None]*n
for t in range(252,n):
    value=0.0
    for j,group in enumerate(cohort['issuers']):
        prior=issuer_indexes[j][t-252:t];current=issuer_indexes[j][t]
        value+=group['weight_percent']*(1 if current>max(prior) else -1 if current<min(prior) else 0)
    hl[t]=value/weight
spy=closes['SPY'];trend=[math.log(spy[t]/spy[t-20]) for t in range(20,n)]
def z(value, prior):
    m=sum(prior)/len(prior);sd=math.sqrt(sum((x-m)**2 for x in prior)/len(prior))
    if sd<=1e-12:raise ValueError('degenerate_normalizer')
    return (value-m)/sd
t=n-1
features={'breadth_delta':breadth[t],'advance_decline_z':z(breadth[t],breadth[t-252:t]),
          'new_high_low_z':z(hl[t],hl[t-252:t]),'index_trend_z':z(trend[-1],trend[-253:-1])}
print(json.dumps(features,separators=(',',':')))
