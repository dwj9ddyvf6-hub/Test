"""EMA20/50 trend strategy in quantjourney-bt order-mode idiom.
Drives the engine's own ExecutionSimulator + FillEngine (fill_at='open',
FixedBpsCommission 5 bps, NoSlippage) + PortfolioLedger offline on local bars.
Signals precomputed with pandas ewm(adjust=False), identical recursion to reference.
Sizing: per-name tracked sub-account cash (starts $20,000), quantity floored to whole
shares (engine equity quantity_step=1.0), sized on close-t as next open is unknowable
at submission: qty = floor(sub_cash*0.9995 / close_t). Orders submitted in the bar-t
callback fill at open t+1 per the simulator phase order.
"""
import json, math
import pandas as pd
from backtester.execution.fill_engine import FillEngine
from backtester.execution.simulator import ExecutionSimulator
from backtester.execution.commission import FixedBpsCommission
from backtester.execution.slippage import NoSlippage
from backtester.execution.order_types import Order, OrderSide, OrderType
from backtester.execution.contract_spec import ContractSpec
from backtester.portfolio.accounting.ledger import PortfolioLedger

panel=json.load(open("panel_5.json"))
syms=sorted(panel)
def frame(idx):
    return pd.DataFrame({s:{r[0]:r[idx] for r in panel[s]} for s in syms})
dates=pd.DatetimeIndex(sorted({r[0] for s in syms for r in panel[s] if r[0]<="2024-12-31"}))
def aligned(idx):
    df=frame(idx).reindex([d.strftime("%Y-%m-%d") for d in dates]); df.index=dates; return df.astype(float)
close, open_, high, low, vol = aligned(4), aligned(1), aligned(2), aligned(3), aligned(5)
e20=close.ewm(span=20,adjust=False).mean(); e50=close.ewm(span=50,adjust=False).mean()
desired=(e20>e50)&(close>e50)
START=pd.Timestamp("2020-01-01")
sub_cash={s:20000.0 for s in syms}; fills_log=[]; entry_info={}
trades=[]
fe=FillEngine(slippage=NoSlippage(), commission=FixedBpsCommission(bps=5.0), fill_at="open")
ledger=PortfolioLedger(initial_cash=100000.0, instruments=syms, contract_spec_resolver=lambda i: ContractSpec.equity(i))
sim=ExecutionSimulator(fill_engine=fe, ledger=ledger)
def on_fill(fill, nav):
    fills_log.append({"sym":fill.instrument,"side":str(fill.side),"qty":fill.quantity,"price":fill.fill_price,"commission":fill.commission,"ts":str(fill.timestamp)})
    if fill.side==OrderSide.BUY:
        sub_cash[fill.instrument]-=fill.quantity*fill.fill_price+fill.commission
        entry_info[fill.instrument]=(fill.quantity*fill.fill_price+fill.commission, str(fill.timestamp))
    else:
        proceeds=fill.quantity*fill.fill_price-fill.commission
        sub_cash[fill.instrument]+=proceeds
        if fill.instrument in entry_info:
            cost_basis,_=entry_info.pop(fill.instrument)
            trades.append({"sym":fill.instrument,"pnl":round(proceeds-cost_basis,2),"exit_ts":str(fill.timestamp)})
def on_bar(date, bars, positions, nav, avg_entry):
    if date<START: return
    for s in syms:
        if date not in desired.index: continue
        want=bool(desired.loc[date,s]); pos=positions.get(s,0.0)
        pending=any(o.instrument==s and o.is_active for o in fe.pending_orders)
        if want and pos==0 and not pending:
            qty=math.floor(sub_cash[s]*0.9995/float(close.loc[date,s]))
            if qty>0: fe.submit(Order(s, OrderSide.BUY, float(qty), OrderType.MARKET))
        elif not want and pos>0 and not pending:
            fe.submit(Order(s, OrderSide.SELL, float(pos), OrderType.MARKET))
result=sim.run(close=close, open_=open_, high=high, low=low, volume=vol, on_bar=on_bar, on_fill=on_fill)
nav_series=result.nav if hasattr(result,"nav") else None
print(type(result), [a for a in dir(result) if not a.startswith("_")])
# final equity: last NAV mark, less 5bps hypothetical exit cost on open positions (matches reference forced close)
last_nav=float(nav_series.iloc[-1]) if nav_series is not None else float(ledger.cash)
open_pos_value=0.0; open_pos={}
for s in syms:
    p=float(result.positions.iloc[-1][s]) if hasattr(result,"positions") else 0.0
    if p: open_pos[s]=p; open_pos_value+=p*float(close.iloc[-1][s])
final_equity=last_nav-0.0005*open_pos_value
wins=sum(1 for t in trades if t["pnl"]>0)
# round trips: closed trades + positions still open at end (reference counts its forced close)
rt=len(trades)+len(open_pos)
res={"engine":"quantjourney-bt 16fe1ac6 order mode: ExecutionSimulator+FillEngine(fill_at=open)+PortfolioLedger","cost":"FixedBpsCommission 5 bps per side, NoSlippage",
"final_nav_marked":round(last_nav,2),"open_positions_at_end":open_pos,"open_position_value":round(open_pos_value,2),
"final_equity_after_forced_exit_cost":round(final_equity,2),"total_return_pct":round((final_equity/100000-1)*100,4),
"closed_trades":len(trades),"round_trips_incl_forced":rt,"closed_win_rate_pct":round(wins/len(trades)*100,2) if trades else 0,"wins_closed":wins,"fills":len(fills_log)}
json.dump(res,open("qj_results.json","w"),indent=1)
json.dump(trades,open("qj_trades.json","w"),indent=1)
json.dump(fills_log,open("qj_fills.json","w"),indent=1)
print(json.dumps(res,indent=1))
