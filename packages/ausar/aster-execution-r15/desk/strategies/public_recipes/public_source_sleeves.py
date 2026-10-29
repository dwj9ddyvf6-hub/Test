"""Source-grounded local paper candidate reducers. No broker/network imports.

Source signal logic and execution/accounting policy are separate layers. No Pine
compiler parity or TraderDev original-source/return equivalence is claimed.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo
from copy import deepcopy
from pathlib import Path
import argparse, hashlib, json, math

STRATEGIES = ('ai_volume', 'iu_body', 'tomazetti_rsi2')
DEFAULTS = {
 'ai_volume': {'volume_ema_length':20,'volume_multiplier':2.,'price_ema_length':50,'exit_bars':5},
 'iu_body': {'big_body_threshold':4.,'atr_length':14,'atr_factor':2.,'body_baseline':'source_inclusive21_div20'},
 'tomazetti_rsi2': {'rsi_length':2,'rsi_threshold':10.,'short_ma_length':5,'long_ma_length':200,'rsi_ma_filter':True,'rsi_ma_length':4,'rsi_ma_threshold':30.,'stop_enabled':False,'stop_percent':10.,'window_start':'2009-01-02T00:00:00+00:00','window_end':'2020-12-30T00:00:00+00:00','source_timezone':'UTC'}
}
SOURCE_FILES = {'ai_volume':'AI_Volume_Strategy.pine','iu_body':'IU_BIG_BODY_BAR.pine','tomazetti_rsi2':'TOMAZETTI_RSI2.pine'}

def stamp(value):
 if not isinstance(value,str): raise ValueError('timestamp must be explicit ISO string')
 d=datetime.fromisoformat(value.replace('Z','+00:00'))
 if d.tzinfo is None or d.utcoffset() is None: raise ValueError('timestamp needs timezone')
 return d.astimezone(timezone.utc)
def finite(value, name='number', minimum=None):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError(name+' must be finite number')
 if minimum is not None and value<minimum: raise ValueError(name+' below minimum')
 return float(value)
def positive_integer(value,name):
 if isinstance(value,bool) or not isinstance(value,int) or value<1:raise ValueError(name+' must be positive integer')
 return value
def fhash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sma(xs,n):
 out=[]
 for i in range(len(xs)):
  w=xs[max(0,i-n+1):i+1]
  out.append(sum(w)/n if len(w)==n and all(x is not None for x in w) else None)
 return out
def ema(xs,n):
 out=[];old=None;a=2/(n+1)
 for x in xs:
  old=x if old is None else a*x+(1-a)*old
  out.append(old)
 return out
def rma(xs,n):
 out=[];seed=[];old=None
 for x in xs:
  if x is None:out.append(None);continue
  if old is None:
   seed.append(x)
   if len(seed)<n:out.append(None);continue
   old=sum(seed[-n:])/n
  else:old=(old*(n-1)+x)/n
  out.append(old)
 return out
def rsi(xs,n):
 gains=[None]+[max(xs[i]-xs[i-1],0) for i in range(1,len(xs))]
 losses=[None]+[max(xs[i-1]-xs[i],0) for i in range(1,len(xs))]
 g,l=rma(gains,n),rma(losses,n);out=[]
 for a,b in zip(g,l):
  if a is None or b is None or (a==0 and b==0):out.append(None)
  elif b==0:out.append(100.)
  elif a==0:out.append(0.)
  else:out.append(100-100/(1+a/b))
 return out
def atr(bars,n):
 tr=[]
 for i,b in enumerate(bars):
  tr.append(b['high']-b['low'] if i==0 else max(b['high']-b['low'],abs(b['high']-bars[i-1]['close']),abs(b['low']-bars[i-1]['close'])))
 return rma(tr,n)
def source_features(strategy,bars,params):
 if not bars:return {}
 close=[b['close'] for b in bars];b=bars[-1]
 if strategy=='ai_volume':
  v=ema([b['volume'] for b in bars],params['volume_ema_length'])[-1];m=ema(close,params['price_ema_length'])[-1]
  spike=b['volume']>v*params['volume_multiplier']
  return {'volume_ema':v,'price_ema':m,'volume_spike':spike,'long_signal':spike and b['close']>m and b['close']>b['open'],'short_signal':spike and b['close']<m and b['close']<b['open']}
 if strategy=='iu_body':
  bodies=[abs(b['close']-b['open']) for b in bars]
  if params['body_baseline']=='source_inclusive21_div20':base=sum(bodies[-21:])/20 if len(bodies)>=21 else None
  elif params['body_baseline']=='declared_corrected_prior20':base=sum(bodies[-21:-1])/20 if len(bodies)>=21 else None
  else:raise ValueError('unknown declared body baseline')
  strong=base is not None and bodies[-1]>base*params['big_body_threshold']
  return {'body':bodies[-1],'body_baseline':base,'atr':atr(bars,params['atr_length'])[-1],'long_signal':strong and b['close']>b['open'],'short_signal':strong and b['close']<b['open']}
 rs=rsi(close,params['rsi_length']);short=sma(close,params['short_ma_length'])[-1];long=sma(close,params['long_ma_length'])[-1];mr=sma(rs,params['rsi_ma_length'])[-1]
 in_window=stamp(params['window_start'])<=stamp(b['open_at'])<=stamp(params['window_end'])
 enter=in_window and rs[-1] is not None and long is not None and rs[-1]<params['rsi_threshold'] and b['close']>long and (not params['rsi_ma_filter'] or (mr is not None and mr<params['rsi_ma_threshold']))
 return {'rsi':rs[-1],'rsi_average':mr,'short_ma':short,'long_ma':long,'source_window_allows_all_strategy_block':in_window,'long_signal':enter,'short_signal':False,'long_close_signal':in_window and rs[-1] is not None and short is not None and b['close']>short}

def make_config(strategy, config=None):
 if strategy not in STRATEGIES:raise ValueError('unknown strategy')
 c=deepcopy(config or {})
 if c.get('paper_only',True) is not True:raise ValueError('this reducer refuses live mode')
 c['paper_only']=True;c.setdefault('symbol','BTCUSD');c.setdefault('market_kind','spot')
 if c['market_kind'] not in ('spot','perpetual','equity'):raise ValueError('market_kind must be explicit supported type')
 c.setdefault('initial_cash',100000.);finite(c['initial_cash'],'initial_cash',0)
 c.setdefault('quote_max_age_seconds',10.);finite(c['quote_max_age_seconds'],'quote_max_age_seconds',0)
 c.setdefault('entry_ttl_seconds',300.);finite(c['entry_ttl_seconds'],'entry_ttl_seconds',0)
 c.setdefault('bar_max_decision_lag_seconds',300.);finite(c['bar_max_decision_lag_seconds'],'bar_max_decision_lag_seconds',0)
 c.setdefault('quantity_mode','equity_percent' if strategy=='tomazetti_rsi2' else 'fixed')
 c.setdefault('quantity_value',100. if c['quantity_mode']=='equity_percent' else 1.)
 if c['quantity_mode'] not in ('fixed','equity_percent'):raise ValueError('quantity mode')
 finite(c['quantity_value'],'quantity_value',0)
 c.setdefault('params',{});unknown=set(c['params'])-set(DEFAULTS[strategy])
 if unknown:raise ValueError('unknown source params '+str(sorted(unknown)))
 c['params']={**DEFAULTS[strategy],**c['params']}
 for k,v in c['params'].items():
  if k.endswith('_length') or k=='exit_bars':positive_integer(v,k)
  if k in ('volume_multiplier','big_body_threshold','atr_factor'):finite(v,k,0)
 if strategy=='tomazetti_rsi2':
  zone=ZoneInfo(c['params']['source_timezone']);start,end=stamp(c['params']['window_start']),stamp(c['params']['window_end'])
  if any((d.astimezone(zone).hour,d.astimezone(zone).minute,d.astimezone(zone).second,d.astimezone(zone).microsecond)!=(0,0,0,0) for d in (start,end)):raise ValueError('source date input boundaries must be midnight in explicitly declared source_timezone')
  if start>end:raise ValueError('source window order')
  if not isinstance(c['params']['rsi_ma_filter'],bool) or not isinstance(c['params']['stop_enabled'],bool):raise ValueError('source switches must be bool')
  for k in ('rsi_threshold','rsi_ma_threshold','stop_percent'):finite(c['params'][k],k,0)
  if c['params']['stop_percent']>=100:raise ValueError('source stop percent must be under100')
 return c

def journal_digest(state):
 return fhash({'fills':state.get('fill_ledger',[]),'cashflows':state.get('cashflow_ledger',[])})

def initial_state(strategy,c):
 return {'schema':1,'strategy':strategy,'config_sha256':fhash(c),'book':{'cash':float(c['initial_cash'])},'bars':[],'position':None,'source_counter':0,'pending_target':None,'orders':{},'seen_events':[],'event_fingerprints':{},'last_received_at':None,'next_order':1,'fill_ledger':[],'cashflow_ledger':[],'source_decisions':[],'accounting_obligations':[]}

def valid_receipt(receipt,at,kind):
 if not isinstance(receipt,dict):return False,kind+'_receipt_missing'
 try:
  if not receipt.get('source') or not receipt.get('id'):return False,kind+'_source_identity_missing'
  if stamp(receipt['available_at'])>at:return False,kind+'_not_yet_available'
  if stamp(receipt['valid_until'])<at:return False,kind+'_expired'
 except (KeyError,ValueError,TypeError):return False,kind+'_clock_invalid'
 return True,None

def step(strategy,config,state,event):
 """Return {state, intents, diagnostics}. State transitions only on real events.

BAR appends a completed/received candle and emits preserved source decisions.
QUOTE can propose a paper order. FILL must acknowledge our own order id; this is
not an OHLC fill simulator. CANCEL acknowledges cancellation. CASHFLOW applies
an externally received paper funding/borrow/dividend/settlement cash receipt.
"""
 c=make_config(strategy,config);s=deepcopy(state) if state else initial_state(strategy,c)
 if s.get('schema')!=1 or s.get('strategy')!=strategy or s.get('config_sha256')!=fhash(c):raise ValueError('state/config identity mismatch')
 if not isinstance(event,dict) or not isinstance(event.get('id'),str) or not event['id']:raise ValueError('nonempty string event id required')
 intents=[];diagnostics=[];eid=event['id']
 if eid in s['seen_events']:
  if s.get('event_fingerprints',{}).get(eid)!=fhash(event):raise ValueError('event id payload conflict')
  return {'state':s,'intents':[],'diagnostics':['duplicate_event_ignored']}
 at=stamp(event['received_at'])
 if s['last_received_at'] and at<stamp(s['last_received_at']):raise ValueError('event receipt chronology moves backwards')
 if event.get('symbol',c['symbol'])!=c['symbol']:raise ValueError('event symbol identity mismatch')
 s['last_received_at']=at.isoformat();s['seen_events'].append(eid);s.setdefault('event_fingerprints',{})[eid]=fhash(event)
 def emit(kind,**fields):intents.append({'kind':kind,'paper_only':True,'strategy':strategy,'symbol':c['symbol'],'created_at':at.isoformat(),**fields})
 def cancel_entries(reason):
  for oid,o in s['orders'].items():
   if o['action'].startswith('OPEN_') and o['status']=='open':o['status']='cancel_requested';emit('CANCEL_ORDER',order_id=oid,reason=reason)
 def target(side,reason):
  if side!='flat' and s['bars'] and (at-stamp(s['bars'][-1]['close_at'])).total_seconds()>c['bar_max_decision_lag_seconds']:
   diagnostics.append('stale_bar_entry_veto');emit('ENTRY_VETO',source_side=side,reasons=['stale_bar_entry_veto']);return
  old=s.get('pending_target')
  if old and old['side']!=side:cancel_entries('source_target_changed')
  s['pending_target']={'side':side,'reason':reason,'created_at':at.isoformat(),'source_bar_open_at':s['bars'][-1]['open_at'] if s['bars'] else None}
 def expire_entries():
  t=s.get('pending_target')
  if t and t['side']!='flat' and (at-stamp(t['created_at'])).total_seconds()>=c['entry_ttl_seconds']:
   cancel_entries('entry_deadline_expired');s['pending_target']=None;diagnostics.append('entry_deadline_expired')
 def register_funding_due(pos,through):
  due=pos.get('funding_next_due_at')
  if not due or through<stamp(due):return
  obid='funding:'+pos['opened_at']+':'+due
  existing=next((x for x in s['accounting_obligations'] if x['id']==obid),None)
  if existing:
   if stamp(existing['through_at'])<through:existing['through_at']=through.isoformat()
  elif not any(x.get('covers_obligation_id')==obid for x in s['cashflow_ledger']):
   s['accounting_obligations'].append({'id':obid,'kind':'funding','due_at':due,'opened_at':pos['opened_at'],'through_at':through.isoformat(),'qty_at_detection':pos['qty']})
  diagnostics.append('funding_cashflow_receipt_due')
 kind=event.get('type')
 expire_entries()
 if kind=='BAR':
  b=event.get('bar')
  if not isinstance(b,dict):raise ValueError('bar required')
  b=deepcopy(b);o,cl,avail=stamp(b['open_at']),stamp(b['close_at']),stamp(b['available_at'])
  if not o<cl<=avail<=at:raise ValueError('forming/future/not received bar')
  if s['bars'] and o<stamp(s['bars'][-1]['close_at']):raise ValueError('overlapping or out-of-order bar')
  for k in ('open','high','low','close'):b[k]=finite(b[k],k,0)
  if not 0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high']:raise ValueError('invalid OHLC')
  b['volume']=finite(b['volume'],'volume',0);b['received_at']=at.isoformat();s['bars'].append(b)
  f=source_features(strategy,s['bars'],c['params']);pos=s['position'];decision={'event_id':eid,'bar_open_at':b['open_at'],'bar_close_at':b['close_at'],'received_at':at.isoformat(),'features':f,'position_side_before':pos['side'] if pos else None}
  s['source_decisions'].append(decision)
  if strategy=='ai_volume':
   side='long' if f['long_signal'] else 'short' if f['short_signal'] else None
   if side:
    s['source_counter']=0
    # Pine same-side entries are suppressed by no-pyramid behavior, but counter reset remains.
    if pos is None or pos['side']!=side:target(side,'source_entry_or_reversal')
   s['source_counter']+=1;decision['source_counter_after']=s['source_counter']
   if s['source_counter']>=c['params']['exit_bars'] and (pos or s['pending_target']):
    if pos and stamp(b['close_at'])<=stamp(pos['opened_at']):diagnostics.append('prefill_completed_bar_owned_exit_skipped')
    else:target('flat','source_signal_reset_counter_exit')
  elif strategy=='iu_body':
   if pos is None:
    if f['long_signal']:target('long','source_body_impulse')
    elif f['short_signal']:target('short','source_body_impulse')
   elif f['atr'] is not None and stamp(b['close_at'])>stamp(pos['opened_at']):
    dist=f['atr']*c['params']['atr_factor'];old=pos.get('stop')
    new=pos['avg_price']-dist if pos['side']=='long' else pos['avg_price']+dist
    if old is not None:new=max(old,b['close']-dist) if pos['side']=='long' else min(old,b['close']+dist)
    if new<=0:diagnostics.append('source_stop_nonpositive_not_submitted')
    else:
     if old is None or new!=old:pos['stop_active_from']=at.isoformat()
     pos['stop']=new;emit('STOP_PLAN',side=pos['side'],qty=pos['qty'],source_stop_price=new,active_from=pos['stop_active_from'],rounding='execution quote tick rounding supplied later')
   elif pos:diagnostics.append('prefill_completed_bar_stop_update_skipped')
  else:
   if f['long_signal']:
    if pos is None:target('long','source_rsi2_filtered')
    # Exact optional source exit is inside entry branch. A flat prefill average is unavailable.
    if c['params']['stop_enabled']:
     if pos:
      pos['stop']=pos['avg_price']*(1-c['params']['stop_percent']/100);pos['stop_active_from']=at.isoformat();emit('STOP_PLAN',side='long',qty=pos['qty'],source_stop_price=pos['stop'],active_from=at.isoformat())
     else:diagnostics.append('source_optional_stop_prefill_average_unavailable')
   if f['long_close_signal'] and (pos or s['pending_target']):
    if pos and stamp(b['close_at'])<=stamp(pos['opened_at']):diagnostics.append('prefill_completed_bar_owned_exit_skipped')
    else:target('flat','source_close_above_sma5')
  emit('SOURCE_DECISION',**decision)
 elif kind=='QUOTE':
  q=event.get('quote',{});qa=stamp(q['asof']);bid=finite(q['bid'],'bid',0);ask=finite(q['ask'],'ask',0)
  if not 0<bid<=ask or qa>at or (at-qa).total_seconds()>c['quote_max_age_seconds']:raise ValueError('invalid/stale/future quote')
  pos=s['position']
  if pos and c['market_kind']=='perpetual':register_funding_due(pos,qa)
  if pos and pos.get('stop') is not None and qa>stamp(pos['stop_active_from']):
   triggered=bid<=pos['stop'] if pos['side']=='long' else ask>=pos['stop']
   if triggered:target('flat','observed_quote_stop_trigger')
  t=s.get('pending_target')
  if not t:return {'state':s,'intents':intents,'diagnostics':diagnostics}
  if (pos is None or t['side']==pos['side']) and qa<=stamp(t['created_at']):diagnostics.append('entry_quote_not_strictly_after_source_decision');return {'state':s,'intents':intents,'diagnostics':diagnostics}
  # Close/reversal flatten leg is never vetoed by entry capability/cash/funding data.
  action=None;qty=None
  if pos and (t['side']=='flat' or t['side']!=pos['side']):action='CLOSE_'+pos['side'].upper();qty=pos['qty']
  elif pos and t['side']==pos['side']:s['pending_target']=None
  elif t['side']=='flat':cancel_entries('flat_source_target');s['pending_target']=None
  else:
   receipts=event.get('receipts',{});checks=[]
   if s.get('accounting_obligations'):checks.append((False,'unreconciled_funding_or_borrow_cashflow'))
   contract=receipts.get('contract');ok,why=valid_receipt(contract,qa,'contract');checks.append((ok,why))
   fee=receipts.get('fees');ok,why=valid_receipt(fee,qa,'fees');checks.append((ok,why))
   if contract and contract.get('market_kind')!=c['market_kind']:checks.append((False,'market_kind_receipt_mismatch'))
   if contract and contract.get('symbol')!=c['symbol']:checks.append((False,'contract_symbol_mismatch'))
   if c['market_kind']=='perpetual':
    checks.append(valid_receipt(receipts.get('funding'),qa,'funding'))
    funding=receipts.get('funding')
    if not funding or not isinstance(funding.get('rate'),(int,float)) or isinstance(funding.get('rate'),bool) or not math.isfinite(funding['rate']) or not funding.get('effective_at') or not funding.get('next_due_at'):checks.append((False,'funding_rate_and_schedule_missing'))
    elif stamp(funding['effective_at'])>qa or stamp(funding['next_due_at'])<=qa:checks.append((False,'funding_schedule_not_current'))
    if contract and contract.get('pnl_model')!='linear_quote_per_unit':checks.append((False,'unsupported_derivative_pnl_model'))
    if contract and contract.get('contract_multiplier')!=1:checks.append((False,'unsupported_derivative_contract_multiplier'))
   if t['side']=='short':
    short=receipts.get('short_capability');checks.append(valid_receipt(short,qa,'short_capability'))
    if not short or short.get('allowed') is not True:checks.append((False,'short_not_explicitly_supported'))
    if c['market_kind']!='perpetual':
     checks.append(valid_receipt(receipts.get('borrow'),qa,'borrow'))
     borrow=receipts.get('borrow')
     if not borrow or not isinstance(borrow.get('available_qty'),(int,float)) or isinstance(borrow.get('available_qty'),bool) or not isinstance(borrow.get('annual_rate'),(int,float)) or isinstance(borrow.get('annual_rate'),bool):checks.append((False,'borrow_quantity_and_rate_missing'))
     elif not math.isfinite(borrow['available_qty']) or borrow['available_qty']<=0 or not math.isfinite(borrow['annual_rate']) or borrow['annual_rate']<0:checks.append((False,'borrow_quantity_or_rate_invalid'))
   if c['market_kind']=='equity':
    checks.append(valid_receipt(receipts.get('settled_cash'),qa,'settled_cash'))
    if not receipts.get('settled_cash') or receipts['settled_cash'].get('journal_sha256')!=journal_digest(s):checks.append((False,'settled_cash_journal_binding_mismatch'))
   fails=[why for ok,why in checks if not ok]
   if fails:diagnostics.extend(fails);emit('ENTRY_VETO',source_side=t['side'],reasons=fails);return {'state':s,'intents':intents,'diagnostics':diagnostics}
   if contract.get('paper_only') is not True:raise ValueError('contract receipt must be paper-only')
   tick=finite(contract['price_tick'],'price_tick',0);lot=finite(contract['qty_step'],'qty_step',0);maxlev=finite(contract['max_leverage'],'max_leverage',1)
   if tick<=0 or lot<=0:raise ValueError('positive tick/lot required')
   fb=finite(fee['taker_bps'],'fee_bps',0)/10000;px=ask if t['side']=='long' else bid
   nav=finite(s['book']['cash'],'book cash',0)
   wanted=c['quantity_value'] if c['quantity_mode']=='fixed' else (nav*c['quantity_value']/100)/(px*(1+fb))
   maximum=(nav*maxlev)/(px*(1+fb))
   if c['market_kind']=='spot' and t['side']=='long':maximum=nav/(px*(1+fb))
   if c['market_kind']=='equity' and t['side']=='long':maximum=min(maximum,finite(receipts['settled_cash']['amount'],'settled cash',0)/(px*(1+fb)))
   desired=min(wanted,maximum)
   if t['side']=='short' and c['market_kind']!='perpetual':desired=min(desired,float(receipts['borrow']['available_qty']))
   qty=float((Decimal(str(desired))/Decimal(str(lot))).to_integral_value(rounding=ROUND_DOWN)*Decimal(str(lot)))
   if qty<=0:diagnostics.append('size_rounds_to_zero');return {'state':s,'intents':intents,'diagnostics':diagnostics}
   action='OPEN_'+t['side'].upper()
  if action:
   active=[o for o in s['orders'].values() if o['status'] in ('open','cancel_requested')]
   if active:diagnostics.append('await_existing_order_acknowledgement');return {'state':s,'intents':intents,'diagnostics':diagnostics}
   oid=f'{strategy}:{c["symbol"]}:{s["next_order"]}';s['next_order']+=1
   o={'id':oid,'action':action,'qty':qty,'remaining':qty,'status':'open','submitted_at':at.isoformat(),'quote_asof':qa.isoformat(),'source_target_created_at':t['created_at'],'quote_price':ask if action in ('OPEN_LONG','CLOSE_SHORT') else bid,'quote_id':eid,'quote_receipts':event.get('receipts',{})}
   s['orders'][oid]=o;emit('PAPER_ORDER',**o)
 elif kind=='FILL':
  oid=event.get('order_id');o=s['orders'].get(oid)
  if not o or o['status'] not in ('open','cancel_requested'):raise ValueError('fill must acknowledge own outstanding order')
  if event.get('paper_only') is not True:raise ValueError('fill must be paper-only')
  ft=stamp(event['filled_at']);q=finite(event['qty'],'fill_qty',0);px=finite(event['price'],'fill_price',0);fees=finite(event['fees'],'fill fees',0)
  if q<=0 or px<=0 or q>o['remaining']+1e-10 or not stamp(o['submitted_at'])<=ft<=at:raise ValueError('invalid fill quantity/clock/price')
  action=o['action'];side='long' if action.endswith('LONG') else 'short';d=1 if side=='long' else -1;pos=s['position'];cash=finite(s['book']['cash'],'cash')
  if action.startswith('OPEN_'):
   if pos and pos['side']!=side:raise ValueError('open fill cannot silently cross old position')
   if pos is None:
    pos={'side':side,'qty':q,'avg_price':px,'opened_at':ft.isoformat(),'stop':None,'stop_active_from':None};s['position']=pos
    if c['market_kind']=='perpetual':pos['funding_next_due_at']=o.get('quote_receipts',{}).get('funding',{}).get('next_due_at')
   else:pos['avg_price']=(pos['avg_price']*pos['qty']+px*q)/(pos['qty']+q);pos['qty']+=q
   cash-=fees
   if c['market_kind']!='perpetual':cash-=d*q*px
   # Partial fill stays protected/owned; requests cancel of opening remainder rather than duplicate entries.
   if q<o['remaining']-1e-10:o['status']='cancel_requested';emit('CANCEL_ORDER',order_id=oid,reason='partial_fill_remainder_policy')
  else:
   if not pos or pos['side']!=side or q>pos['qty']+1e-10:raise ValueError('exit fill exceeds owned position')
   if c['market_kind']=='perpetual':register_funding_due(pos,ft)
   if side=='short' and c['market_kind']!='perpetual':
    obid='borrow:'+pos['opened_at']+':'+ft.isoformat()
    s['accounting_obligations'].append({'id':obid,'kind':'borrow','opened_at':pos['opened_at'],'through_at':ft.isoformat(),'closed_qty':q})
   cash+=(d*q*(px-pos['avg_price']) if c['market_kind']=='perpetual' else d*q*px)-fees
   pos['qty']-=q
   if pos['qty']<=1e-10:
    s['position']=None
    if s['pending_target'] and s['pending_target']['side']=='flat':s['pending_target']=None
  s['book']['cash']=cash;o['remaining']=max(0,o['remaining']-q)
  if o['remaining']<=1e-10:o['status']='filled'
  s['fill_ledger'].append({'event_id':eid,'order_id':oid,'action':action,'qty':q,'price':px,'fees':fees,'filled_at':ft.isoformat(),'received_at':at.isoformat(),'cash_after':cash})
  if action.startswith('OPEN_') and o['status']=='filled' and s['pending_target'] and s['pending_target']['side']==side:s['pending_target']=None
 elif kind=='CANCEL':
  oid=event.get('order_id');o=s['orders'].get(oid)
  if not o or o['status'] not in ('open','cancel_requested'):raise ValueError('cancel must acknowledge own outstanding order')
  o['status']='cancelled';emit('ORDER_CANCELLED',order_id=oid,remaining_unfilled=o['remaining'])
 elif kind=='CASHFLOW':
  if event.get('paper_only') is not True:raise ValueError('cashflow must be paper-only')
  delta=finite(event['amount'],'cashflow amount');eff=stamp(event['effective_at'])
  if eff>at or not event.get('source_receipt_id') or not event.get('source'):raise ValueError('cashflow actual receipt required')
  covering=event.get('covers_obligation_id');obligation=next((x for x in s['accounting_obligations'] if x['id']==covering),None)
  if covering and obligation is None:raise ValueError('cashflow must cover known outstanding obligation')
  nextdue=None
  if obligation:
   if event.get('cashflow_kind')!=obligation['kind']:raise ValueError('cashflow kind must match obligation')
   if obligation['kind']=='funding':
    if eff<stamp(obligation['due_at']):raise ValueError('funding cashflow cannot precede scheduled due')
    nextdue=stamp(event['next_due_at'])
    if nextdue<=stamp(obligation['due_at']):raise ValueError('authoritative funding schedule must advance')
  s['book']['cash']=finite(s['book']['cash'],'cash')+delta;s['cashflow_ledger'].append({**event,'cash_after':s['book']['cash']})
  if covering:
   s['accounting_obligations']=[x for x in s['accounting_obligations'] if x['id']!=covering]
   if nextdue:
    pos=s['position']
    if pos and pos['opened_at']==obligation['opened_at']:pos['funding_next_due_at']=nextdue.isoformat()
    # Closed or still-held position may have crossed additional due periods.
    if nextdue<=stamp(obligation['through_at']):
     nid='funding:'+obligation['opened_at']+':'+nextdue.isoformat()
     s['accounting_obligations'].append({**obligation,'id':nid,'due_at':nextdue.isoformat()})
 else:raise ValueError('unknown event type')
 return {'state':s,'intents':intents,'diagnostics':diagnostics}

def run_payload(payload):
 strategy=payload['strategy'];config=make_config(strategy,payload.get('config'));state=payload.get('state');output=[]
 for event in payload.get('events',[]):
  result=step(strategy,config,state,event);state=result['state'];output.append({'event_id':event['id'],'intents':result['intents'],'diagnostics':result['diagnostics']})
 result={'strategy':strategy,'paper_only':True,'config':config,'config_sha256':fhash(config),'state':state or initial_state(strategy,config),'events':output,'source_identity':'Distinct public recipe, not original gated TraderDev source; source compiler parity not verified','execution_identity':'Own quote/fill events and local-paper cash accounting; no external orders'}
 if payload.get('fixture_identity') is not None:result['fixture_identity']=payload['fixture_identity']
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',required=True);parser.add_argument('--output');args=parser.parse_args()
 input_path=Path(args.input).resolve()
 if args.output and Path(args.output).resolve()==input_path:raise ValueError('output cannot overwrite input')
 payload=json.loads(input_path.read_text());result=run_payload(payload);text=json.dumps(result,indent=2,allow_nan=False)+'\n'
 if args.output:Path(args.output).write_text(text)
 else:print(text,end='')
if __name__=='__main__':main()
