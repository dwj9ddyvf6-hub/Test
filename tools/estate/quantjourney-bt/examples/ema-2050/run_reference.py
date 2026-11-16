"""Reference engine: OUR headline, computed BEFORE touching quantjourney-bt.
Strategy (from research_notes/ema-trend-system-evidence-20261008-0229/report.md Investigation 2):
 EMA20/50 trend rule, mechanised minimally: long at close-t signal if EMA20>EMA50 and close>EMA50, else flat.
 Fill at open t+1. Per-name independent $20,000 sub-account, fractional shares, all-in when long.
 Cost 5 bps per side on notional. Window: signals/fills 2020-01-01..2024-12-31, EMA warmup from 2019.
 Data: DEEP panel (Alpaca SIP split-adjusted daily), panel_5.json extracted by streaming mmap.
"""
import json
panel=json.load(open("panel_5.json"))
COST=0.0005; START="2020-01-01"; END="2024-12-31"
def ema(vals,n):
    k=2/(n+1); out=[None]*len(vals); e=None
    for i,v in enumerate(vals):
        e=v if e is None else v*k+e*(1-k); out[i]=e
    return out
total_start=100000.0; total_end=0.0; all_trades=[]
per={}
for sym,rows in panel.items():
    rows=[r for r in rows if r[0]<="2024-12-31"]
    closes=[r[4] for r in rows]; opens=[r[1] for r in rows]; dates=[r[0] for r in rows]
    e20=ema(closes,20); e50=ema(closes,50)
    cash=20000.0; shares=0.0; entry=None; trades=[]
    for t in range(len(rows)-1):
        if dates[t]<START: 
            desired=False
        else:
            desired=(e20[t]>e50[t] and closes[t]>e50[t])
        # fill at open t+1
        price=opens[t+1]
        if desired and shares==0:
            cost=cash*COST; shares=(cash-cost)/price; entry=(dates[t+1],price,cash); cash=0.0
        elif not desired and shares>0:
            proceeds=shares*price; cost=proceeds*COST; cash=proceeds-cost
            pnl=cash-entry[2]; trades.append({"sym":sym,"entry_date":entry[0],"entry_px":entry[1],"exit_date":dates[t+1],"exit_px":price,"pnl":round(pnl,2),"ret_pct":round(pnl/entry[2]*100,4)})
            shares=0.0; entry=None
    # force close at last close 2024-12-31
    if shares>0:
        proceeds=shares*closes[-1]; cost=proceeds*COST; cash=proceeds-cost
        pnl=cash-entry[2]; trades.append({"sym":sym,"entry_date":entry[0],"entry_px":entry[1],"exit_date":dates[-1],"exit_px":closes[-1],"pnl":round(pnl,2),"ret_pct":round(pnl/entry[2]*100,4),"forced_eow":True})
    per[sym]={"end_cash":round(cash,2),"trades":len(trades)}
    total_end+=cash; all_trades.extend(trades)
wins=sum(1 for t in all_trades if t["pnl"]>0)
res={"strategy":"EMA20/50 trend long-only, close>EMA50 filter, next-open fill","universe":sorted(panel),"window":[START,END],"cost_bps_per_side":5,"initial_capital":total_start,
"final_equity":round(total_end,2),"total_return_pct":round((total_end/total_start-1)*100,4),
"trades_round_trips":len(all_trades),"win_rate_pct":round(wins/len(all_trades)*100,2) if all_trades else 0,"wins":wins,"per_symbol":per}
json.dump(res,open("reference_results.json","w"),indent=1)
json.dump(all_trades,open("reference_trades.json","w"),indent=1)
print(json.dumps(res,indent=1))
