"""Autonomous, isolated public-recipe spot paper books; no broker order client.

The vendored reducer/source are immutable R14 public counterparts. Market/side,
allocation and execution overlays below are explicit R15 transfer variants.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from decimal import Decimal, ROUND_DOWN
import argparse, hashlib, importlib.util, json, math, sqlite3, threading, time, os, fcntl, signal, uuid
import urllib.request

SOURCE_PATH=Path(__file__).resolve().parents[1]/'strategies/public_recipes/public_source_sleeves.py'
SOURCE_SHA='e64c995dd451ac0fd0a32f8a1bcc22624a76362c58d607ee9edecc2d99722e6b'
MARKETS={'tomazetti_rsi2':('ADAUSDT','1h',3600000),'iu_body':('ENJUSDT','5m',300000),'ai_volume':('LINKUSDT','4h',14400000)}
APPLICATION_ID=0x41535250
OWN_TABLES={'books','events','bars','checkpoints','receipts'}
def utcnow():return datetime.now(timezone.utc)
def iso(d):return d.astimezone(timezone.utc).isoformat()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def process_birth(pid):
 try:return Path('/proc/'+str(pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
 except (OSError,IndexError):return None
def worker_status(db_path):
 p=Path(str(db_path)+'.worker.json')
 if not p.exists():return {'running':False,'status':'not_started'}
 try:
  record=json.loads(p.read_text());birth=process_birth(record.get('pid'));alive=birth is not None and birth==record.get('pid_birth_tick');age=(utcnow()-datetime.fromisoformat(record['heartbeat_at'])).total_seconds();stale=age<0 or age>max(180,2*record.get('interval_seconds',20)+30)
  return {**record,'process_alive_with_matching_birth':alive,'stale':stale,'heartbeat_age_seconds':age,'running':alive and not stale and record.get('phase')=='running'}
 except (ValueError,KeyError,TypeError):return {'running':False,'status':'invalid_worker_receipt'}
def verify_identity(db):
 brand=db.execute('PRAGMA application_id').fetchone()[0];tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
 if brand!=APPLICATION_ID or tables!=OWN_TABLES:raise ValueError('foreign or unexpected database schema refused')
 if 'enabled_sha' not in {r[1] for r in db.execute('PRAGMA table_info(checkpoints)')}:raise ValueError('legacy prototype lacks bound entry authorization; explicit reviewed migration required')
def journal_record(book_id,event,intents,diagnostics):return {'book_id':book_id,'id':event['id'],'payload':event,'intents':intents,'diagnostics':diagnostics,'received_at':event['received_at']}
def load_core():
 if hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('public source reducer hash mismatch')
 spec=importlib.util.spec_from_file_location('aster_public_source_core',SOURCE_PATH);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class IndicatorStream:
 """Exact chronological recurrence; bounded windows, no EMA reseeding on trim."""
 def __init__(self,state=None):self.state=deepcopy(state or {'count':0,'closes':[],'bodies':[],'rsis':[],'tr_seed':[],'gain_seed':[],'loss_seed':[]})
 def push(self,strategy,params,b):
  s=self.state;c=b['close'];prev=s.get('prev_close');s['count']+=1
  s['closes']=(s['closes']+[c])[-max(200,params.get('long_ma_length',200),params.get('short_ma_length',5)):]
  body=abs(c-b['open']);s['bodies']=(s['bodies']+[body])[-21:]
  def exponential(key,x,n):
   a=2/(n+1);s[key]=x if key not in s else a*x+(1-a)*s[key];return s[key]
  def wilder(key,seedkey,x,n):
   if x is None:return None
   if key not in s:
    s[seedkey].append(x)
    if len(s[seedkey])<n:return None
    s[key]=sum(s[seedkey][-n:])/n;s[seedkey]=[]
   else:s[key]=(s[key]*(n-1)+x)/n
   return s[key]
  if strategy=='ai_volume':
   v=exponential('volume_ema',b['volume'],params['volume_ema_length']);m=exponential('price_ema',c,params['price_ema_length']);spike=b['volume']>v*params['volume_multiplier']
   f={'volume_ema':v,'price_ema':m,'volume_spike':spike,'long_signal':spike and c>m and c>b['open'],'short_signal':spike and c<m and c<b['open']}
  elif strategy=='iu_body':
   tr=b['high']-b['low'] if prev is None else max(b['high']-b['low'],abs(b['high']-prev),abs(b['low']-prev))
   a=wilder('atr','tr_seed',tr,params['atr_length'])
   baseline=sum(s['bodies'])/20 if len(s['bodies'])>=21 else None
   if params['body_baseline']=='declared_corrected_prior20':baseline=sum(s['bodies'][:-1])/20 if len(s['bodies'])>=21 else None
   strong=baseline is not None and body>baseline*params['big_body_threshold']
   f={'body':body,'body_baseline':baseline,'atr':a,'long_signal':strong and c>b['open'],'short_signal':strong and c<b['open']}
  else:
   n=params['rsi_length'];g=wilder('gain','gain_seed',None if prev is None else max(c-prev,0),n);l=wilder('loss','loss_seed',None if prev is None else max(prev-c,0),n)
   r=None if g is None or l is None or (g==0 and l==0) else 100. if l==0 else 0. if g==0 else 100-100/(1+g/l)
   s['rsis']=(s['rsis']+[r])[-params['rsi_ma_length']:]
   def average(xs,n):return sum(xs[-n:])/n if len(xs)>=n and all(x is not None for x in xs[-n:]) else None
   short=average(s['closes'],params['short_ma_length']);long=average(s['closes'],params['long_ma_length']);mr=average(s['rsis'],params['rsi_ma_length'])
   stamp=datetime.fromisoformat(b['open_at']);window=datetime.fromisoformat(params['window_start'])<=stamp<=datetime.fromisoformat(params['window_end'])
   f={'rsi':r,'rsi_average':mr,'short_ma':short,'long_ma':long,'source_window_allows_all_strategy_block':window,'long_signal':window and r is not None and long is not None and r<params['rsi_threshold'] and c>long and (not params['rsi_ma_filter'] or (mr is not None and mr<params['rsi_ma_threshold'])),'short_signal':False,'long_close_signal':window and r is not None and short is not None and c>short}
  s['prev_close']=c;return f

def spot_market_constraints(item):
 """Intersect native LOT_SIZE and MARKET_LOT_SIZE; zero market fields disable only themselves.

 Decimal strings preserve source precision. Frozen historical contracts without
 this policy marker keep their original replay interpretation.
 """
 filters={x['filterType']:x for x in item['filters']}
 if len(filters)!=len(item['filters']):raise ValueError('duplicate native filter')
 def operand(value):
  if isinstance(value,bool):raise ValueError('boolean native filter')
  d=Decimal(str(value))
  if not d.is_finite() or d<0 or d and not -18<=d.adjusted()<=30:raise ValueError('invalid native filter')
  return d
 lot=filters['LOT_SIZE'];market=filters.get('MARKET_LOT_SIZE',{})
 steps=[operand(x.get('stepSize','0')) for x in (lot,market)]
 steps=[x for x in steps if x>0]
 if not steps:raise ValueError('native quantity step unavailable')
 # A quantity must be on BOTH grids, including non-power-of-ten increments.
 scale=10**max(0,max(-x.as_tuple().exponent for x in steps))
 if scale>10**18:raise ValueError('unsupported native step precision')
 quantum=Decimal(math.lcm(*(int(x*scale) for x in steps)))/scale
 minimum=max(operand(x.get('minQty','0')) for x in (lot,market))
 maxima=[operand(x.get('maxQty','0')) for x in (lot,market)]
 maxima=[x for x in maxima if x>0]
 if not maxima or min(maxima)<minimum:raise ValueError('native quantity range invalid')
 tick=operand(filters['PRICE_FILTER']['tickSize'])
 if tick<=0:raise ValueError('native tick unavailable')
 minimum_notional=max(operand(filters.get('NOTIONAL',{}).get('minNotional','0')),
                      operand(filters.get('MIN_NOTIONAL',{}).get('minNotional','0')))
 return {'price_tick':str(tick),'qty_step':str(quantum),'minimum_qty':str(minimum),
         'maximum_qty':str(min(maxima)),'minimum_notional':str(minimum_notional)}

class BinancePublicSpotFeed:
 """Production read-only endpoints; quote observation clock is HTTP receipt."""
 origin='https://data-api.binance.vision/api/v3/'
 def __init__(self,opener=None,transport=None,heartbeat=None,completed_limit=None):
  if completed_limit is not None and (type(completed_limit) is not int or not 1<=completed_limit<=999):raise ValueError('bounded completed-bar limit required')
  self.opener=opener;self.transport=transport;self.heartbeat=heartbeat;self.completed_limit=completed_limit
 def fetch(self,path):
  if self.heartbeat:self.heartbeat(phase='crypto_public_get',path=path)
  started=utcnow();req=urllib.request.Request(self.origin+path,headers={'User-Agent':'Aster-public-paper/15'})
  if self.opener is None:
   if self.transport is None:
    from backend.http_transport import bounded_http
    transport=bounded_http
   else:transport=self.transport
   status,body=transport('GET',self.origin+path,headers={'User-Agent':'Aster-public-paper/15'},timeout_seconds=8,maximum_bytes=256000,follow_redirects=False);headers={}
  else:
   # Injectable in-memory fixture opener; production uses absolute-deadline IO.
   with self.opener(req,timeout=8) as r:
    body=r.read(256001);status=getattr(r,'status',200);headers=dict(r.headers)
   if len(body)>256000:raise ValueError('fixture response exceeds byte cap')
  received=utcnow()
  if status!=200:raise ValueError('public feed HTTP '+str(status))
  value=json.loads(body)
  return value,{'id':hashlib.sha256(body).hexdigest(),'url':self.origin+path,'request_started_at':iso(started),'received_at':iso(received),'http_status':status,'body_sha256':hashlib.sha256(body).hexdigest(),'headers':headers,'raw':value}
 def capture(self,symbol,interval,step_ms):
  errors=[]
  def failed(path,e):return {'id':'failed:'+str(type(e).__name__),'url':self.origin+path,'received_at':iso(utcnow()),'error':str(e),'raw':None}
  try:metadata,mr=self.fetch('exchangeInfo?symbol='+symbol)
  except Exception as e:metadata={'symbols':[]};mr=failed('exchangeInfo?symbol='+symbol,e);errors.append('metadata_unavailable')
  try:rows,br=self.fetch('klines?symbol='+symbol+'&interval='+interval+'&limit='+str(300 if self.completed_limit is None else self.completed_limit+1))
  except Exception as e:rows=[];br=failed('klines?symbol='+symbol,e);errors.append('bars_unavailable')
  received=datetime.fromisoformat(br['received_at']);completed=[];forming=0
  try:
   previous=None
   for row in rows:
    if not isinstance(row,list) or len(row)<7 or isinstance(row[0],bool) or isinstance(row[6],bool):raise ValueError('malformed native bar')
    op=int(row[0]);cl=int(row[6])+1
    if op!=row[0] or cl-1!=row[6] or op%step_ms or cl-op!=step_ms or (previous is not None and op!=previous):raise ValueError('nonnative bar clock')
    previous=cl
    if datetime.fromtimestamp(cl/1000,timezone.utc)>received:forming+=1;continue
    completed.append({'open_at':iso(datetime.fromtimestamp(op/1000,timezone.utc)),'close_at':iso(datetime.fromtimestamp(cl/1000,timezone.utc)),'available_at':br['received_at'],'open':float(row[1]),'high':float(row[2]),'low':float(row[3]),'close':float(row[4]),'volume':float(row[5])})
  except (ValueError,KeyError,TypeError,IndexError,OverflowError):
   # Parsing a bad signal batch must not prevent acquiring a fresh observed
   # quote for existing protective exits. Never admit its partial prefix.
   completed=[];errors.append('bars_invalid_native_batch')
  if self.completed_limit is not None:completed=completed[-self.completed_limit:]
  trade_receipt=None;last_trade=None
  try:
   trades,trade_receipt=self.fetch('trades?symbol='+symbol+'&limit=1')
   if trades:last_trade=iso(datetime.fromtimestamp(int(trades[-1]['time'])/1000,timezone.utc))
  except Exception as e:trade_receipt=failed('trades?symbol='+symbol,e);errors.append('last_trade_unavailable')
  # Quote fetch is after bar receipt/source availability, never a historical open.
  ticker,qr=self.fetch('ticker/bookTicker?symbol='+symbol)
  quote={'asof':qr['received_at'],'bid':float(ticker['bidPrice']),'ask':float(ticker['askPrice']),'bid_qty':float(ticker['bidQty']),'ask_qty':float(ticker['askQty'])}
  contract=None
  try:
   item=next((s for s in metadata.get('symbols',[]) if s.get('symbol')==symbol),None)
   if not item or item.get('status')!='TRADING' or item.get('isSpotTradingAllowed') is not True or item.get('quoteAsset')!='USDT' or item.get('baseAsset')!=symbol[:-4]:errors.append('production_spot_contract_unavailable')
   else:
    native=spot_market_constraints(item)
    contract={'id':mr['id'],'source':mr['url'],'available_at':mr['received_at'],'valid_until':iso(datetime.fromisoformat(mr['received_at'])+timedelta(minutes=5)),'symbol':symbol,'paper_only':True,'market_kind':'spot','max_leverage':1,'quote_asset':item['quoteAsset'],
              **{k:float(v) for k,v in native.items()},'native_filter_values':native,'filter_policy':'lot_and_market_intersection_v1'}
  except (ValueError,KeyError,TypeError,IndexError,ArithmeticError):
   contract=None;errors.append('metadata_invalid_contract')
  if last_trade:
   trade_age=(datetime.fromisoformat(qr['received_at'])-datetime.fromisoformat(last_trade)).total_seconds()
   if not 0<=trade_age<=60:errors.append('last_trade_stale_or_future')
  else:errors.append('last_trade_missing')
  return {'bars':completed,'quote':quote,'contract':contract,'receipts':{'metadata':mr,'bars':br,'quote':qr,'last_trade':trade_receipt},'last_trade_at':last_trade,'entry_acquisition_errors':errors,'forming_rows_ignored':forming,'quote_clock_identity':'Actual public HTTP snapshot observation; endpoint provides no exchange quote timestamp; last trade separately bounded60seconds for entries','trade_identity':'Binance production USDT spot, long-only transfer of distinct public recipe'}

def read_status(db_path):
 """Read-only UI entry: never create a file/schema, install or fund."""
 p=Path(db_path)
 if not p.exists():return {'installed':False,'paper_only':True,'books':[],'runtime_identity':'Distinct public recipes / Binance spot long-only transfer','worker':worker_status(p)}
 db=sqlite3.connect('file:'+str(p.resolve())+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 verifier=None
 try:
  db.execute("BEGIN")  # One journal/book/quote projection, even during a fill.
  verify_identity(db)
  verifier=PublicRecipeDesk(p)
  books=[]
  for row in db.execute('SELECT * FROM books ORDER BY id'):
   verifier._verify_book(db,dict(row))
   state=json.loads(row['state']);receipt=json.loads(row['last_receipt']) if row['last_receipt'] else None
   quote=(receipt or {}).get('capture',{}).get('quote',{});marked=state['book']['cash']+(state['position']['qty']*quote['bid'] if state['position'] and quote.get('bid') else 0)
   books.append({'id':row['id'],'strategy':row['strategy'],'enabled':bool(row['enabled']),'symbol':MARKETS[row['strategy']][0],'timeframe':MARKETS[row['strategy']][1],'quote_currency':'USDT','virtual_principal':100000,'cash':state['book']['cash'],'position':state['position'],'marked_equity':marked if not state['position'] or quote.get('bid') else None,'pending_target':state['pending_target'],'last_received_at':state['last_received_at'],'last_receipt':receipt,'source_recipe_identity':'Recovered public Pine counterpart; original TraderDev parity unverified','allocation':'100percent equity intent explicit overlay; actual displayed-depth partial fills may lower exposure','direction':'spot long only; short research decisions visible but opening unsupported'})
  return {'installed':bool(books),'paper_only':True,'books':books,'worker':worker_status(p),'runtime_identity':'Independent Binance production-spot paper books; no broker orders','event_count':db.execute('SELECT COUNT(*) FROM events').fetchone()[0]}
 finally:
  if verifier:verifier.close()
  db.close()

class PublicRecipeDesk:
 """Constructor has no filesystem/financial effects. Install is explicit."""
 def __init__(self,db_path,feed=None,clock=None):self.path=Path(db_path);self.feed=feed or BinancePublicSpotFeed();self.core=load_core();self.lock=threading.RLock();self.clock=clock or utcnow;self.verified={};self.monitor=None;self.data_version=None
 def _connect(self):
  if not self.path.exists():raise ValueError('uninstalled public recipe desk')
  db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row
  try:verify_identity(db)
  except Exception:db.close();raise
  return db
 def install(self,enable=False):
  if type(enable) is not bool:raise ValueError('installation enabled policy must be an explicit bool')
  if self.path.name.lower() in ('aster.sqlite','aster.db','aster.sqlite3','desk.sqlite'):raise ValueError('main desk database filename refused')
  self.path.parent.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(self.path)
  try:
   tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
   brand=db.execute('PRAGMA application_id').fetchone()[0]
   if brand not in (0,APPLICATION_ID):raise ValueError('foreign database application identity refused')
   if tables:verify_identity(db)
   db.executescript('PRAGMA application_id='+str(APPLICATION_ID)+'; CREATE TABLE IF NOT EXISTS books(id TEXT PRIMARY KEY,strategy TEXT NOT NULL,enabled INTEGER NOT NULL,config TEXT NOT NULL,state TEXT NOT NULL,indicators TEXT NOT NULL,last_receipt TEXT); CREATE TABLE IF NOT EXISTS events(book_id TEXT,id TEXT,payload TEXT NOT NULL,payload_sha TEXT NOT NULL,intents TEXT NOT NULL,diagnostics TEXT NOT NULL,received_at TEXT NOT NULL,PRIMARY KEY(book_id,id)); CREATE TABLE IF NOT EXISTS bars(book_id TEXT,open_at TEXT,content_sha TEXT NOT NULL,first_seen_at TEXT NOT NULL,PRIMARY KEY(book_id,open_at)); CREATE TABLE IF NOT EXISTS checkpoints(book_id TEXT PRIMARY KEY,state_sha TEXT NOT NULL,indicator_sha TEXT NOT NULL,config_sha TEXT NOT NULL,journal_sha TEXT NOT NULL,enabled_sha TEXT NOT NULL); CREATE TABLE IF NOT EXISTS receipts(body_sha TEXT PRIMARY KEY,body TEXT NOT NULL,first_received_at TEXT NOT NULL,source TEXT NOT NULL);')
   db.execute('BEGIN IMMEDIATE')
   installed=[]
   for strategy,(symbol,interval,_) in MARKETS.items():
    book='PUBLIC_'+strategy.upper()+'_SPOT100';old=db.execute('SELECT id FROM books WHERE id=?',(book,)).fetchone()
    if old:continue
    config=self.core.make_config(strategy,{'symbol':symbol,'market_kind':'spot','initial_cash':100000.,'quantity_mode':'equity_percent','quantity_value':100.,'params':{'window_end':'2030-12-30T00:00:00+00:00'} if strategy=='tomazetti_rsi2' else {}})
    state=self.core.initial_state(strategy,config);at=iso(utcnow());fund={'type':'FUND','id':'installation:'+book,'amount':100000,'currency':'USDT','virtual_only':True,'explicit_operator_installation':True,'entries_enabled_at_install':enable,'received_at':at}
    db.execute('INSERT INTO books VALUES(?,?,?,?,?,?,?)',(book,strategy,int(enable),canonical(config),canonical(state),canonical(IndicatorStream().state),None))
    db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(book,fund['id'],canonical(fund),sha(fund),'[]','[]',at));head=sha({'previous':'','record':journal_record(book,fund,[],[])})
    db.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?,?)',(book,sha(state),sha(IndicatorStream().state),sha(config),head,sha({'enabled':enable})));installed.append(book)
   db.commit();return {'installed_now':installed,'paper_only':True,'status':read_status(self.path)}
  except Exception:db.rollback();raise
  finally:db.close()
 def set_enabled(self,enabled):
  if type(enabled) is not bool:raise ValueError('entry policy must be an explicit bool')
  with self.lock:
   db=self._connect();db.execute('BEGIN IMMEDIATE')
   try:
    changed=[]
    for got in db.execute('SELECT * FROM books ORDER BY id').fetchall():
     row=dict(got);self._verify_book(db,row)
     if bool(row['enabled'])==enabled:continue
     event={'type':'ENTRY_POLICY','id':'entry-policy:'+uuid.uuid4().hex,'enabled':enabled,'authority':'explicit_operator_command','received_at':iso(self.clock()),'paper_only':True};row['enabled']=int(enabled)
     db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(row['id'],event['id'],canonical(event),sha(event),'[]','[]',event['received_at']));db.execute('UPDATE books SET enabled=? WHERE id=?',(int(enabled),row['id']));self._seal_event(db,row,event,[],[]);changed.append(row['id'])
    db.commit()
    self.verified.clear()
    if self.monitor:self.data_version=self.monitor.execute('PRAGMA data_version').fetchone()[0]
    return {'enabled':enabled,'changed_books':changed,'explicit_operator_control_recorded':True}
   except Exception:db.rollback();self.verified.clear();raise
   finally:db.close()
 def _verify_book(self,db,row):
  if self.monitor is None:self.monitor=sqlite3.connect('file:'+str(self.path.resolve())+'?mode=ro',uri=True)
  version=self.monitor.execute('PRAGMA data_version').fetchone()[0]
  if self.data_version is not None and version!=self.data_version:self.verified.clear()
  cp=db.execute('SELECT * FROM checkpoints WHERE book_id=?',(row['id'],)).fetchone()
  if type(row['enabled']) is not int or row['enabled'] not in (0,1) or not cp or cp['enabled_sha']!=sha({'enabled':bool(row['enabled'])}) or cp['state_sha']!=sha(json.loads(row['state'])) or cp['indicator_sha']!=sha(json.loads(row['indicators'])) or cp['config_sha']!=sha(json.loads(row['config'])):raise ValueError('owned checkpoint/policy hash mismatch')
  if self.verified.get(row['id'])==cp['journal_sha']:return
  cash=0.;pos=None;orders={};head='';policy=None;funded=False
  for record in db.execute('SELECT * FROM events WHERE book_id=? ORDER BY rowid',(row['id'],)):
   ev=json.loads(record['payload']);intents=json.loads(record['intents']);diags=json.loads(record['diagnostics'])
   if record['payload_sha']!=sha(ev) or ev['received_at']!=record['received_at']:raise ValueError('owned event payload hash/clock mismatch')
   head=sha({'previous':head,'record':journal_record(row['id'],ev,intents,diags)})
   for intent in intents:
    if intent.get('kind')=='PAPER_ORDER':
     if intent['id'] in orders:raise ValueError('duplicate owned order journal')
     orders[intent['id']]={**intent,'filled':0.,'cancelled':False}
   if ev['type']=='FUND':
    if funded or ev['id']!='installation:'+row['id'] or cash!=0 or pos or ev.get('amount')!=100000 or ev.get('currency')!='USDT' or ev.get('virtual_only') is not True or ev.get('explicit_operator_installation') is not True or type(ev.get('entries_enabled_at_install')) is not bool:raise ValueError('invalid own principal/authorization event')
    cash=ev['amount'];policy=ev['entries_enabled_at_install'];funded=True
   elif ev['type']=='ENTRY_POLICY':
    if not funded or type(ev.get('enabled')) is not bool or ev.get('authority')!='explicit_operator_command' or ev.get('paper_only') is not True:raise ValueError('invalid explicit entry policy event')
    policy=ev['enabled']
   elif ev['type']=='CANCEL':
    if ev['order_id'] not in orders:raise ValueError('cancel outside owned journal')
    orders[ev['order_id']]['cancelled']=True
   elif ev['type']=='FILL':
    o=orders.get(ev['order_id']);q=ev['qty'];px=ev['price'];fee=ev['fees']
    if not o or o['cancelled'] or ev.get('paper_only') is not True or not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in (q,px,fee)) or q<=0 or px<=0 or fee<0 or o['filled']+q>o['qty']+1e-8:raise ValueError('unowned/invalid fill journal')
    if not datetime.fromisoformat(o['submitted_at'])<=datetime.fromisoformat(ev['filled_at'])<=datetime.fromisoformat(ev['received_at']):raise ValueError('fill journal chronology mismatch')
    o['filled']+=q
    if o['action']=='OPEN_LONG':
     if policy is not True:raise ValueError('opening fill without contemporaneous explicit entry authorization')
     cash-=q*px+fee
     if pos:pos['avg_price']=(pos['avg_price']*pos['qty']+px*q)/(pos['qty']+q);pos['qty']+=q
     else:pos={'side':'long','qty':q,'avg_price':px,'opened_at':ev['filled_at']}
    elif o['action']=='CLOSE_LONG':
     if not pos or q>pos['qty']+1e-8:raise ValueError('close exceeds owned journal position')
     cash+=q*px-fee;pos['qty']-=q
     if pos['qty']<=1e-10:pos=None
    else:raise ValueError('unsupported spot direction in funding journal')
  state=json.loads(row['state']);actual=state['position']
  if not funded or policy!=bool(row['enabled']) or head!=cp['journal_sha'] or not math.isclose(cash,state['book']['cash'],rel_tol=1e-12,abs_tol=1e-6) or bool(pos)!=bool(actual):raise ValueError('entire owned money/entry-authorization journal replay mismatch')
  if pos and (actual['side']!='long' or not math.isclose(pos['qty'],actual['qty'],rel_tol=1e-12,abs_tol=1e-8) or not math.isclose(pos['avg_price'],actual['avg_price'],rel_tol=1e-12,abs_tol=1e-8) or pos['opened_at']!=actual['opened_at']):raise ValueError('owned position journal replay mismatch')
  self.verified[row['id']]=head
 def _seal_event(self,db,row,event,intents,diagnostics):
  cp=db.execute('SELECT journal_sha FROM checkpoints WHERE book_id=?',(row['id'],)).fetchone();head=sha({'previous':cp[0],'record':journal_record(row['id'],event,intents,diagnostics)})
  db.execute('UPDATE checkpoints SET state_sha=?,indicator_sha=?,config_sha=?,journal_sha=?,enabled_sha=? WHERE book_id=?',(sha(json.loads(row['state'])),sha(json.loads(row['indicators'])),sha(json.loads(row['config'])),head,sha({'enabled':bool(row['enabled'])}),row['id']));self.verified[row['id']]=head
 def _event(self,db,row,event,stream=None):
  old=db.execute('SELECT payload_sha FROM events WHERE book_id=? AND id=?',(row['id'],event['id'])).fetchone()
  if old:
   if old[0]!=sha(event):raise ValueError('durable event payload conflict')
   return {'intents':[],'diagnostics':['durable_duplicate_ignored']}
  state=json.loads(row['state']);config=json.loads(row['config']);original=self.core.source_features
  if event['type']=='BAR':
   stream=stream or IndicatorStream(json.loads(row['indicators']));feature=stream.push(row['strategy'],config['params'],event['bar']);self.core.source_features=lambda strategy,bars,params:feature
  try:result=self.core.step(row['strategy'],config,state,event)
  finally:self.core.source_features=original
  state=result['state']
  t=state.get('pending_target')
  if t and t['side']!='flat' and not t.get('origin_completed_at'):
   origin=next((b for b in state['bars'] if b['open_at']==t.get('source_bar_open_at')),None)
   if not origin:raise ValueError('source target lacks its own origin completion')
   t['origin_completed_at']=origin['close_at']
  for intent in result['intents']:
   if intent['kind']=='PAPER_ORDER':
    owned=state['orders'][intent['id']];contract=owned['quote_receipts'].get('contract') or (state.get('position') or {}).get('accepted_contract')
    if contract:
     cap=contract['maximum_qty'];lot=contract['qty_step']
     legal=float((Decimal(str(min(owned['qty'],cap)))/Decimal(str(lot))).to_integral_value(rounding=ROUND_DOWN)*Decimal(str(lot)))
     owned['source_allocation_intended_qty']=owned['qty'];owned['qty']=legal;owned['remaining']=legal
     intent.update(source_allocation_intended_qty=owned['source_allocation_intended_qty'],qty=legal,remaining=legal,execution_overlay='Venue maximum order quantity cap; actual displayed-depth partial acknowledgement')
    if intent['action'].startswith('OPEN_'):
     if not t or not t.get('origin_completed_at'):raise ValueError('opening order missing origin completion')
     owned['origin_completed_at']=t['origin_completed_at'];intent['origin_completed_at']=t['origin_completed_at']
  if event['type']=='FILL' and state.get('position'):
   order=state['orders'][event['order_id']]
   if order['action']=='OPEN_LONG':state['position']['accepted_contract']=deepcopy(order['quote_receipts']['contract']);state['position']['accepted_entry_order_id']=order['id']
  # All raw events, source decisions and fills remain append-only in events.
  # The reducer checkpoint keeps bounded tails plus exact recurrence state.
  state['bars']=state['bars'][-200:];state['source_decisions']=state['source_decisions'][-5:];state['seen_events']=state['seen_events'][-32:];state['event_fingerprints']={k:state['event_fingerprints'][k] for k in state['seen_events']};state['fill_ledger']=state['fill_ledger'][-32:];state['cashflow_ledger']=state['cashflow_ledger'][-32:]
  state['orders']={k:v for k,v in state['orders'].items() if v['status'] in ('open','cancel_requested')}
  if not row['enabled'] and state.get('pending_target') and state['pending_target']['side']!='flat':
   if state.get('position') and state['position']['side']!=state['pending_target']['side']:state['pending_target']={**state['pending_target'],'side':'flat','reason':'disabled_entry_preserve_owned_flatten'}
   else:state['pending_target']=None
   result['diagnostics'].append('operator_entry_disabled')
  row['state']=canonical(state)
  if stream:row['indicators']=canonical(stream.state)
  db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(row['id'],event['id'],canonical(event),sha(event),canonical(result['intents']),canonical(result['diagnostics']),event['received_at']))
  db.execute('UPDATE books SET state=?,indicators=? WHERE id=?',(row['state'],row['indicators'],row['id']))
  self._seal_event(db,row,event,result['intents'],result['diagnostics'])
  return result
 def process_capture(self,book_id,capture):
  """Consume actual captured bars then later quote; atomic owned paper fills."""
  with self.lock:
   db=self._connect();db.execute('BEGIN IMMEDIATE')
   try:
    got=db.execute('SELECT * FROM books WHERE id=?',(book_id,)).fetchone()
    if not got:raise ValueError('unknown independent book')
    row=dict(got);self._verify_book(db,row);stream=IndicatorStream(json.loads(row['indicators']));outputs=[];new_bar_opens=[];bar_receipt=capture['receipts']['bars'];blocked=bool(capture.get('entry_acquisition_errors'))
    last=json.loads(row['state'])['bars'];last_open=last[-1]['open_at'] if last else None
    offered=capture['bars']
    try:
     # The frozen public reducer accepts arbitrary bar spans; this adapter
     # owns the instrument's actual native grid and validates the WHOLE batch
     # before advancing recurrence. A failed signal batch leaves quote stops.
     previous_end=None;step=MARKETS[row['strategy']][2]/1000
     received=self.core.stamp(bar_receipt['received_at'])
     if received>self.core.stamp(capture['receipts']['quote']['received_at']):raise ValueError('source receipt follows observed quote')
     for bar in offered:
      op=self.core.stamp(bar['open_at']);end=self.core.stamp(bar['close_at']);available=self.core.stamp(bar['available_at'])
      if op.microsecond or int(op.timestamp())%int(step) or (end-op).total_seconds()!=step or not end<=available<=received or (previous_end is not None and op!=previous_end):raise ValueError('invalid native completed bar clock')
      values={k:self.core.finite(bar[k],k,0)for k in ('open','high','low','close','volume')}
      if not 0<values['low']<=min(values['open'],values['close'])<=max(values['open'],values['close'])<=values['high']:raise ValueError('invalid native OHLC')
      previous_end=end
    except (ValueError,KeyError,TypeError,ArithmeticError):
     offered=[];blocked=True
     outputs.append({'intents':[],'diagnostics':['invalid_native_bar_batch_entries_blocked_owned_quote_exits_preserved']})
    for bar in offered:
     contents={k:bar[k] for k in ('open_at','close_at','open','high','low','close','volume')};existing=db.execute('SELECT content_sha FROM bars WHERE book_id=? AND open_at=?',(book_id,bar['open_at'])).fetchone()
     if existing:
      if existing[0]!=sha(contents):blocked=True
      continue
     if last_open and bar['open_at']<last_open:blocked=True;continue
     if last_open:
      step=MARKETS[row['strategy']][2]/1000
      if (datetime.fromisoformat(bar['open_at'])-datetime.fromisoformat(last_open)).total_seconds()!=step:blocked=True;break
     raw_row=next((r for r in bar_receipt.get('raw',[]) if int(r[0])==int(datetime.fromisoformat(bar['open_at']).timestamp()*1000)),None)
     ev={'type':'BAR','id':'bar:'+bar['open_at'],'received_at':bar_receipt['received_at'],'symbol':MARKETS[row['strategy']][0],'bar':bar,'source_receipt':{'url':bar_receipt.get('url'),'http_body_sha256':bar_receipt.get('body_sha256'),'native_raw_row':raw_row}}
     outputs.append(self._event(db,row,ev,stream));db.execute('INSERT INTO bars VALUES(?,?,?,?)',(book_id,bar['open_at'],sha(contents),bar_receipt['received_at']));last_open=bar['open_at'];new_bar_opens.append(bar['open_at'])
    q=capture['quote'];qr=capture['receipts']['quote'];at=datetime.fromisoformat(qr['received_at']);observed=self.clock();symbol=MARKETS[row['strategy']][0]
    if q['asof']!=qr['received_at'] or not all(isinstance(q[k],(int,float)) and not isinstance(q[k],bool) and math.isfinite(q[k]) for k in ('bid','ask')) or not 0<q['bid']<=q['ask']:raise ValueError('quote values/actual observation identity invalid')
    if observed<at or (observed-at).total_seconds()>10:raise ValueError('capture quote stale/future at actual processing clock')
    fee={'id':'paper-cost-model-v1','source':'Explicit hypothetical10bps each-side fee debit plus actual bid/ask spread; account-specific fee unavailable','available_at':capture['receipts']['metadata']['received_at'],'valid_until':iso(at+timedelta(minutes=5)),'taker_bps':10.}
    if blocked or not row['enabled']:
     s=json.loads(row['state']);t=s.get('pending_target')
     if t and t['side']!='flat':
      if s.get('position') and s['position']['side']!=t['side']:s['pending_target']={**t,'side':'flat','reason':'acquisition_entry_block_preserve_owned_flatten'}
      else:s['pending_target']=None
      row['state']=canonical(s)
    s=json.loads(row['state']);t=s.get('pending_target');window_veto=False
    if t and t['side']!='flat' and (not t.get('origin_completed_at') or max(at,observed)>=datetime.fromisoformat(t['origin_completed_at'])+timedelta(seconds=300)):
     window_veto=True
     if s.get('position') and s['position']['side']!=t['side']:s['pending_target']={**t,'side':'flat','reason':'missed_opening_preserve_owned_flatten'}
     else:s['pending_target']=None
     row['state']=canonical(s)
    for order in list(json.loads(row['state'])['orders'].values()):
     if order['action'].startswith('OPEN_') and order['status'] in ('open','cancel_requested') and (blocked or not row['enabled'] or not order.get('origin_completed_at') or observed>=datetime.fromisoformat(order['origin_completed_at'])+timedelta(seconds=300)):
      reason='acquisition_or_operator_entry_block' if blocked or not row['enabled'] else 'original_native_signal_completion_window_expired'
      cancel={'type':'CANCEL','id':'opening-guard-cancel:'+order['id'],'order_id':order['id'],'received_at':iso(self.clock()),'reason':reason};outputs.append(self._event(db,row,cancel));window_veto=True;observed=self.clock()
    ev={'type':'QUOTE','id':'quote:'+qr['received_at']+':'+qr['id'],'received_at':iso(observed),'symbol':symbol,'quote':q,'receipts':{'contract':capture['contract'],'fees':fee}}
    s=json.loads(row['state']);p=s.get('position');stop_trigger=bool(p and p.get('stop') is not None and datetime.fromisoformat(q['asof'])>datetime.fromisoformat(p['stop_active_from']) and q['bid']<=p['stop'])
    active=any(o['status'] in ('open','cancel_requested') for o in s['orders'].values())
    local_state_changed=sha(s)!=db.execute('SELECT state_sha FROM checkpoints WHERE book_id=?',(book_id,)).fetchone()[0]
    if s.get('pending_target') or stop_trigger or active or local_state_changed:out=self._event(db,row,ev);outputs.append(out)
    else:out={'intents':[],'diagnostics':['observed_quote_no_financial_obligation']};outputs.append(out)
    # Outstanding close remainder uses each genuinely fresh quote until filled.
    existing_close=[o for o in json.loads(row['state'])['orders'].values() if o['status']=='open']
    new_ids={i.get('id') for i in out['intents'] if i['kind']=='PAPER_ORDER'}
    executable=out['intents']+[{'kind':'PAPER_ORDER',**o} for o in existing_close if o['id'] not in new_ids]
    for intent in executable:
     if intent['kind']=='CANCEL_ORDER':
      cancel={'type':'CANCEL','id':'cancel:'+intent['order_id']+':'+qr['received_at'],'order_id':intent['order_id'],'received_at':iso(self.clock())};outputs.append(self._event(db,row,cancel));continue
     if intent['kind']!='PAPER_ORDER':continue
     order=intent;position=json.loads(row['state']).get('position');contract=capture['contract'] or (position or {}).get('accepted_contract');opening=order['action'].startswith('OPEN_')
     if contract is None:raise ValueError('owned order lacks accepted contract identity')
     if opening and (order['qty']<contract['minimum_qty'] or order['qty']>contract['maximum_qty'] or order['qty']*order['quote_price']<contract['minimum_notional']):
      cancel={'type':'CANCEL','id':'filter-veto:'+order['id'],'order_id':order['id'],'received_at':iso(self.clock())};outputs.append(self._event(db,row,cancel));continue
     buy=order['action'] in ('OPEN_LONG','CLOSE_SHORT');px=q['ask'] if buy else q['bid'];display=q.get('ask_qty' if buy else 'bid_qty')
     if not isinstance(display,(int,float)) or isinstance(display,bool) or not math.isfinite(display) or display<0:raise ValueError('actual displayed quote quantity required for paper fill')
     # The HTTP receive time is not evidence of replenished displayed size.
     # Account for every prior fill against the same actual bookTicker body,
     # including prior processes/orders and an intervening different quote.
     depth_identity=sha({k:q[k] for k in ('bid','ask','bid_qty','ask_qty')})
     used=Decimal(0)
     for prior in db.execute("SELECT payload FROM events WHERE book_id=? AND json_extract(payload,'$.type')='FILL'",(book_id,)):
      fill=json.loads(prior[0])
      if (fill.get('displayed_depth_identity')==depth_identity or fill.get('actual_quote_receipt_id')==qr['id']) and fill.get('liquidity_side') in (None,'buy' if buy else 'sell'):
       used+=Decimal(str(fill['qty']))
     display=max(Decimal(0),Decimal(str(display))-used)
     lot=contract['qty_step']
     qty=float((min(Decimal(str(order.get('remaining',order['qty']))),display)/Decimal(str(lot))).to_integral_value(rounding=ROUND_DOWN)*Decimal(str(lot)))
     if qty<=0:continue
     if qty<contract['minimum_qty'] or qty*px<contract['minimum_notional']:
      if opening:
       cancel={'type':'CANCEL','id':'depth-filter-veto:'+order['id'],'order_id':order['id'],'received_at':iso(self.clock())};outputs.append(self._event(db,row,cancel))
      else:
       # A triggered stop cannot manufacture sub-minimum venue execution.
       # Preserve its outstanding reduction for later sufficient depth.
       outputs.append({'intents':[],'diagnostics':['owned_exit_depth_below_accepted_venue_minimum_unfilled']})
      continue
     # Local acknowledgement uses actual observed bid/ask and displayed size.
     fill_at=iso(self.clock())
     if datetime.fromisoformat(fill_at)<observed:raise ValueError('actual paper acknowledgement clock moved backwards')
     fill_clock=datetime.fromisoformat(fill_at)
     if fill_clock-datetime.fromisoformat(q['asof'])>timedelta(seconds=10):
      if opening:
       cancel={'type':'CANCEL','id':'quote-expired:'+order['id'],'order_id':order['id'],'received_at':fill_at,'reason':'observed_quote_expired_before_actual_acknowledgement'};outputs.append(self._event(db,row,cancel))
      continue
     if opening:
      origin=datetime.fromisoformat(order['origin_completed_at']);valid_clock=all(datetime.fromisoformat(r['available_at'])<=fill_clock<=datetime.fromisoformat(r['valid_until']) for r in (capture['contract'],fee))
      if fill_clock>=origin+timedelta(seconds=300) or not valid_clock or qty*px*1.001>json.loads(row['state'])['book']['cash']+1e-8:
       cancel={'type':'CANCEL','id':'actual-fill-veto:'+order['id'],'order_id':order['id'],'received_at':fill_at,'reason':'actual_acknowledgement_origin_receipt_or_cash_guard'};outputs.append(self._event(db,row,cancel));window_veto=True;continue
     fill={'type':'FILL','id':'fill:'+order['id']+':'+qr['received_at'],'order_id':order['id'],'qty':qty,'price':px,'fees':qty*px*.001,'filled_at':fill_at,'received_at':fill_at,'paper_only':True,'actual_quote_receipt_id':qr['id'],'displayed_depth_identity':depth_identity,'liquidity_side':'buy' if buy else 'sell','fill_identity':'Local paper acknowledgement bounded by actual observed displayed quantity; repeated identical depth is not replenishment evidence'}
     filled=self._event(db,row,fill);outputs.append(filled)
     for follow in filled['intents']:
      if follow['kind']=='CANCEL_ORDER':
       cancel={'type':'CANCEL','id':'partial-remainder-cancel:'+follow['order_id']+':'+qr['received_at'],'order_id':follow['order_id'],'received_at':iso(self.clock())};outputs.append(self._event(db,row,cancel))
    receipt={'at':qr['received_at'],'capture':capture,'source_prefix_entry_blocked':blocked,'diagnostics':[d for o in outputs for d in o['diagnostics']]+capture.get('entry_acquisition_errors',[])+(['missed_native_opening_window'] if window_veto else []),'intent_count':sum(len(o['intents']) for o in outputs),'local_paper_only':True,'no_external_broker_orders':True}
    # Raw body deduplication: immutable decision receipts stay in event journal;
    # idle quotes replace latest observation instead of growing without bound.
    decision_quote=any(x.get('kind')=='PAPER_ORDER' for o in outputs for x in o['intents'])
    for kind,raw in capture['receipts'].items():
     if raw and raw.get('raw') is not None:
      if kind=='bars':
       if not new_bar_opens:continue
       times={int(datetime.fromisoformat(x).timestamp()*1000) for x in new_bar_opens};value=[r for r in raw['raw'] if int(r[0]) in times]
      elif decision_quote:value=raw['raw']
      else:continue
      body=canonical(value);db.execute('INSERT OR IGNORE INTO receipts VALUES(?,?,?,?)',(hashlib.sha256(body.encode()).hexdigest(),body,raw['received_at'],raw.get('url','unknown')))
    db.execute('UPDATE books SET last_receipt=? WHERE id=?',(canonical(receipt),book_id));db.commit()
    # Do not let a second writer between commit and this data_version read
    # bless our cached replay result for a subsequently modified journal.
    self.verified.clear()
    self.data_version=self.monitor.execute('PRAGMA data_version').fetchone()[0]
    return receipt
   except Exception:db.rollback();self.verified.pop(book_id,None);raise
   finally:db.close()
 def cycle_once(self):
  with self._connect() as db:books=[dict(r) for r in db.execute('SELECT id,strategy FROM books ORDER BY id')]
  result=[]
  for book in books:
   try:
    symbol,interval,step=MARKETS[book['strategy']];capture=self.feed.capture(symbol,interval,step);result.append({'book':book['id'],'receipt':self.process_capture(book['id'],capture)})
   except Exception as e:
    error={'book':book['id'],'at':iso(utcnow()),'error':type(e).__name__+': '+str(e),'paper_only':True};result.append(error)
    with self._connect() as db:db.execute('UPDATE books SET last_receipt=? WHERE id=?',(canonical(error),book['id']))
  return {'at':iso(utcnow()),'cycles':result,'paper_only':True}
 def close(self):
  if self.monitor:self.monitor.close();self.monitor=None

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['install','status','once','serve','disable','enable']);p.add_argument('--db',required=True);p.add_argument('--enable',action='store_true');p.add_argument('--interval',type=float,default=20);args=p.parse_args()
 if args.command=='status':print(json.dumps(read_status(args.db),indent=2));return
 d=PublicRecipeDesk(args.db)
 if args.command=='install':print(json.dumps(d.install(args.enable),indent=2));return
 if args.command in ('enable','disable'):d.set_enabled(args.command=='enable');print(json.dumps(read_status(args.db),indent=2));return
 if args.command=='once':print(json.dumps(d.cycle_once(),indent=2));return
 if not math.isfinite(args.interval) or not 1<=args.interval<=60:raise ValueError('serve interval1..60seconds')
 lock=open(str(d.path)+'.worker.lock','a+')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('another public-recipe worker owns this database')
 stop=threading.Event();signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
 def heartbeat(phase,summary=None):
  record={'pid':os.getpid(),'pid_birth_tick':process_birth(os.getpid()),'heartbeat_at':iso(utcnow()),'phase':phase,'interval_seconds':args.interval,'paper_only':True,'lease':'fcntl exclusive companion-database worker lock','summary':summary};p=Path(str(d.path)+'.worker.json');tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(canonical(record));os.replace(tmp,p)
 try:
  while not stop.is_set():
   heartbeat('running');r=d.cycle_once();summary={'at':r['at'],'books':[{ 'book':x['book'],'error':x.get('error'),'intents':x.get('receipt',{}).get('intent_count',0),'diagnostics':x.get('receipt',{}).get('diagnostics',[])[-8:]} for x in r['cycles']]};heartbeat('running',summary);print(canonical(summary),flush=True);stop.wait(args.interval)
 finally:heartbeat('stopped');fcntl.flock(lock,fcntl.LOCK_UN);lock.close();d.close()
if __name__=='__main__':main()
