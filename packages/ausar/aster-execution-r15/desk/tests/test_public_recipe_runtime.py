from pathlib import Path
from datetime import datetime,timezone,timedelta
import tempfile,unittest,json,sqlite3,math,random,sys
from backend.public_recipe_runtime import PublicRecipeDesk,IndicatorStream,load_core,read_status,iso,MARKETS,BinancePublicSpotFeed,sha,canonical,worker_status,process_birth

class Clock:
 def __init__(self,at):self.at=at
 def __call__(self):self.at+=timedelta(microseconds=10);return self.at

def fixture(strategy='iu_body',big=True,at=None,n=25):
 symbol,interval,step=MARKETS[strategy];end=at or datetime(2026,10,9,20,tzinfo=timezone.utc);delta=timedelta(milliseconds=step);bars=[]
 for i in range(n):
  op=100.+i*.01;cl=op+.01
  if i==n-1 and big:cl=op+5
  bars.append({'open_at':iso(end-(n-i)*delta),'close_at':iso(end-(n-1-i)*delta),'available_at':iso(end+timedelta(seconds=1)),'open':op,'high':max(op,cl)+.1,'low':min(op,cl)-.1,'close':cl,'volume':1000.})
 br={'id':'bars-'+iso(end),'received_at':iso(end+timedelta(seconds=1)),'url':'synthetic://native-bars'};qr={'id':'quote-'+iso(end),'received_at':iso(end+timedelta(seconds=2)),'url':'synthetic://quote'};mr={'id':'metadata-'+iso(end),'received_at':iso(end),'url':'synthetic://production-contract-shape'}
 contract={'id':mr['id'],'source':mr['url'],'available_at':mr['received_at'],'valid_until':iso(end+timedelta(minutes=5)),'symbol':symbol,'paper_only':True,'market_kind':'spot','price_tick':.01,'qty_step':.001,'max_leverage':1,'minimum_qty':.001,'maximum_qty':10000000,'minimum_notional':1,'quote_asset':'USDT'}
 return {'bars':bars,'quote':{'asof':qr['received_at'],'bid':105.2,'ask':105.3,'bid_qty':10000000.,'ask_qty':10000000.},'contract':contract,'receipts':{'bars':br,'quote':qr,'metadata':mr},'entry_acquisition_errors':[],'fixture_identity':'synthetic-only'}

class TestPublicRecipeRuntime(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'paper.sqlite'
 def tearDown(self):self.tmp.cleanup()
 def installed(self,strategy='iu_body',capture=None,enable=True):
  cap=capture or fixture(strategy);clock=Clock(datetime.fromisoformat(cap['quote']['asof']));d=PublicRecipeDesk(self.path,clock=clock);d.install(enable);return d,cap,'PUBLIC_'+strategy.upper()+'_SPOT100'
 def state(self,book):
  with sqlite3.connect(self.path) as db:return json.loads(db.execute('SELECT state FROM books WHERE id=?',(book,)).fetchone()[0])
 def test_constructor_and_read_status_do_not_create_or_fund(self):
  d=PublicRecipeDesk(self.path);self.assertFalse(self.path.exists());self.assertFalse(read_status(self.path)['installed']);self.assertFalse(self.path.exists())
 def test_explicit_install_idempotent_separate_virtual_principal(self):
  d=PublicRecipeDesk(self.path);a=d.install(True);b=d.install(True);self.assertEqual(len(a['installed_now']),3);self.assertEqual(b['installed_now'],[]);s=read_status(self.path);self.assertEqual(s['event_count'],3);self.assertEqual([x['cash'] for x in s['books']],[100000]*3)
 def test_source_hash_binding(self):self.assertEqual(load_core().SOURCE_FILES['iu_body'],'IU_BIG_BODY_BAR.pine')
 def test_stream_matches_all_three_frozen_prefixes(self):
  core=load_core();rng=random.Random(715);checks=0
  for strategy in MARKETS:
   config=core.make_config(strategy,{'params':{'window_end':'2030-12-30T00:00:00+00:00'} if strategy=='tomazetti_rsi2' else {}});stream=IndicatorStream();bars=[];px=100
   for i in range(600):
    op=px;px*=math.exp(rng.uniform(-.04,.04));t=datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(hours=i);b={'open_at':iso(t),'open':op,'high':max(op,px)*1.001,'low':min(op,px)*.999,'close':px,'volume':rng.uniform(50,5000)};bars.append(b)
    actual=stream.push(strategy,config['params'],b);expected=core.source_features(strategy,bars,config['params']);self.assertEqual(set(actual),set(expected))
    for k,v in expected.items():
     if isinstance(v,(int,float)) and not isinstance(v,bool):self.assertAlmostEqual(actual[k],v,places=10)
     else:self.assertEqual(actual[k],v)
     checks+=1
  self.assertGreater(checks,10000)
 def test_actual_quote_fill_buy_and_cash_fee_conservation(self):
  d,cap,b=self.installed();r=d.process_capture(b,cap);s=self.state(b);self.assertIsNotNone(s['position']);self.assertGreater(s['position']['qty'],0);self.assertGreaterEqual(s['book']['cash'],-1e-7);fill=s['fill_ledger'][-1];self.assertEqual(fill['price'],cap['quote']['ask']);self.assertAlmostEqual(s['book']['cash']+fill['qty']*fill['price']+fill['fees'],100000,places=7)
 def test_min_notional_filter_cancels_owned_order_no_fake_fill(self):
  cap=fixture();cap['contract']['minimum_notional']=1000000;d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertEqual(self.state(b)['fill_ledger'],[])
 def test_disable_blocks_entry_but_preserves_source_decision(self):
  d,cap,b=self.installed(enable=False);d.process_capture(b,cap);s=self.state(b);self.assertIsNone(s['position']);self.assertTrue(any(x['features']['long_signal'] for x in s['source_decisions']))
 def test_disabled_owned_stop_still_closes_at_real_bid(self):
  d,cap,b=self.installed();d.process_capture(b,cap);d.set_enabled(False);end=datetime.fromisoformat(cap['bars'][-1]['close_at']);new=fixture(at=end+timedelta(minutes=5),big=False,n=1);new['bars'][0].update(open=105,close=105,high=105.1,low=104.9);d.clock=Clock(datetime.fromisoformat(new['quote']['asof']));d.process_capture(b,new)
  stop=self.state(b)['position']['stop'];self.assertIsNotNone(stop);new['bars']=[];at=datetime.fromisoformat(new['quote']['asof'])+timedelta(seconds=1);new['quote']={'asof':iso(at),'bid':stop-1,'ask':stop-.9,'bid_qty':10000000.,'ask_qty':10000000.};new['receipts']['quote']={'id':'fresh-stop','received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,new);self.assertIsNone(self.state(b)['position'])
 def test_entry_deadline_exact300seconds_blocks_buy(self):
  cap=fixture();end=datetime.fromisoformat(cap['bars'][-1]['close_at']);late=end+timedelta(seconds=300);cap['quote']['asof']=iso(late);cap['receipts']['quote']['received_at']=iso(late);cap['contract']['valid_until']=iso(late+timedelta(seconds=60));d,cap,b=self.installed(capture=cap);r=d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertIn('missed_native_opening_window',r['diagnostics'])
 def test_stale_quote_at_processing_rejected_atomic_no_bars(self):
  d,cap,b=self.installed();d.clock=Clock(datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=11));self.assertRaises(ValueError,d.process_capture,b,cap);self.assertEqual(self.state(b)['bars'],[])
 def test_unsupported_short_decision_visible(self):
  cap=fixture();bar=cap['bars'][-1];bar.update(open=105,close=100,high=105.1,low=99.9);d,cap,b=self.installed(capture=cap);r=d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertIn('short_not_explicitly_supported',r['diagnostics']);self.assertTrue(self.state(b)['source_decisions'][-1]['features']['short_signal'])
 def test_same_bar_reread_no_duplicate_feature_or_trade(self):
  d,cap,b=self.installed();d.process_capture(b,cap);n=self.state(b)['position']['qty'];next_time=datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=1);cap['quote']['asof']=iso(next_time);cap['receipts']['quote']={'id':'reread','received_at':iso(next_time)};d.clock=Clock(next_time);d.process_capture(b,cap);s=self.state(b);self.assertEqual(s['position']['qty'],n);self.assertEqual(len(s['fill_ledger']),1)
 def test_changed_prefix_blocks_new_entries_and_preserves_original(self):
  d,cap,b=self.installed(enable=False);d.process_capture(b,cap);d.set_enabled(True);cap['bars'][-1]['volume']+=1;at=datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=1);cap['quote']['asof']=iso(at);cap['receipts']['quote']={'id':'corrected','received_at':iso(at)};d.clock=Clock(at);r=d.process_capture(b,cap);self.assertTrue(r['source_prefix_entry_blocked']);self.assertIsNone(self.state(b)['position'])
 def test_acquisition_failure_does_not_block_owned_quote_stop(self):
  d,cap,b=self.installed();d.process_capture(b,cap);end=datetime.fromisoformat(cap['bars'][-1]['close_at']);new=fixture(at=end+timedelta(minutes=5),big=False,n=1);new['bars'][0].update(open=105,close=105,high=105.1,low=104.9);d.clock=Clock(datetime.fromisoformat(new['quote']['asof']));d.process_capture(b,new);stop=self.state(b)['position']['stop'];new['bars']=[];new['entry_acquisition_errors']=['bars_unavailable'];new['contract']=None;at=datetime.fromisoformat(new['quote']['asof'])+timedelta(seconds=1);new['quote']={'asof':iso(at),'bid':stop-1,'ask':stop-.9,'bid_qty':10000000.,'ask_qty':10000000.};new['receipts']['quote']={'id':'owned-exit-no-metadata','received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,new);self.assertIsNone(self.state(b)['position'])
 def test_missing_native_bar_blocks_entry(self):
  d,cap,b=self.installed(enable=False);d.process_capture(b,cap);d.set_enabled(True);end=datetime.fromisoformat(cap['bars'][-1]['close_at']);new=fixture(at=end+timedelta(minutes=15),n=1);d.clock=Clock(datetime.fromisoformat(new['quote']['asof']));r=d.process_capture(b,new);self.assertTrue(r['source_prefix_entry_blocked']);self.assertIsNone(self.state(b)['position'])
 def test_new_runtime_recovers_owned_book_without_funding(self):
  d,cap,b=self.installed();d.process_capture(b,cap);s=self.state(b);fresh=PublicRecipeDesk(self.path);fresh.install(True);self.assertEqual(self.state(b)['book'],s['book']);self.assertEqual(self.state(b)['position'],s['position']);self.assertEqual(read_status(self.path)['event_count'],3+len(cap['bars'])+2)
 def test_default_current_source_window_extension_is_explicit(self):
  d=PublicRecipeDesk(self.path);d.install(True)
  with sqlite3.connect(self.path) as db:c=json.loads(db.execute("SELECT config FROM books WHERE strategy='tomazetti_rsi2'").fetchone()[0])
  self.assertEqual(c['params']['window_end'],'2030-12-30T00:00:00+00:00');self.assertEqual(c['quantity_value'],100)
 def test_feed_failure_durable_status_and_other_books_continue(self):
  class BadFeed:
   def capture(self,*args):raise ValueError('fixture outage')
  d=PublicRecipeDesk(self.path,feed=BadFeed());d.install(True);r=d.cycle_once();self.assertEqual(len(r['cycles']),3);self.assertTrue(all('error' in x for x in r['cycles']));self.assertTrue(all('error' in x['last_receipt'] for x in read_status(self.path)['books']))
 def test_processing_clock305_despite_quote299_vetoes(self):
  cap=fixture();end=datetime.fromisoformat(cap['bars'][-1]['close_at']);cap['bars'][-1]['available_at']=iso(end+timedelta(seconds=298));cap['receipts']['bars']['received_at']=cap['bars'][-1]['available_at'];cap['quote']['asof']=iso(end+timedelta(seconds=299));cap['receipts']['quote']['received_at']=cap['quote']['asof'];cap['contract']['valid_until']=iso(end+timedelta(minutes=10));d,cap,b=self.installed(capture=cap);d.clock=Clock(end+timedelta(seconds=305));r=d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertIsNone(self.state(b)['pending_target']);self.assertIn('missed_native_opening_window',r['diagnostics'])
 def test_actual_acknowledgement_crossing300_cancels_unfilled_open(self):
  cap=fixture();end=datetime.fromisoformat(cap['bars'][-1]['close_at']);cap['receipts']['bars']['received_at']=iso(end+timedelta(seconds=298));cap['bars'][-1]['available_at']=cap['receipts']['bars']['received_at'];cap['quote']['asof']=iso(end+timedelta(seconds=299));cap['receipts']['quote']['received_at']=cap['quote']['asof'];cap['contract']['valid_until']=iso(end+timedelta(minutes=10));d,cap,b=self.installed(capture=cap);ticks=iter([end+timedelta(seconds=299),end+timedelta(seconds=300)]);d.clock=lambda:next(ticks);d.process_capture(b,cap);s=self.state(b);self.assertIsNone(s['position']);self.assertEqual(s['orders'],{});self.assertEqual(s['fill_ledger'],[])
 def test_depth_partial_open_cancels_remainder(self):
  cap=fixture();cap['quote']['ask_qty']=5;d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);s=self.state(b);self.assertEqual(s['position']['qty'],5);self.assertEqual(s['orders'],{});self.assertEqual(len(s['fill_ledger']),1);self.assertAlmostEqual(s['book']['cash'],100000-5*105.3*1.001,places=8)
 def test_zero_depth_open_retries_fresh_quote_within_origin_window(self):
  cap=fixture();cap['quote']['ask_qty']=0;d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertEqual(len(self.state(b)['orders']),1);at=datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=1);cap['bars']=[];cap['quote']['asof']=iso(at);cap['quote']['ask_qty']=5;cap['receipts']['quote']={'id':'depth-now-available','received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,cap);self.assertEqual(self.state(b)['position']['qty'],5);self.assertEqual(self.state(b)['orders'],{})
 def test_origin_unfilled_order_expiry_cancels_without_new_bar(self):
  cap=fixture();cap['quote']['ask_qty']=0;d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);end=datetime.fromisoformat(cap['bars'][-1]['close_at']);at=end+timedelta(seconds=300);cap['bars']=[];cap['quote']['asof']=iso(at);cap['receipts']['quote']={'id':'expired-opening','received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertEqual(self.state(b)['orders'],{})
 def test_active_opening_is_cancelled_on_acquisition_block_or_disable(self):
  for gate in ('blocked','disabled'):
   with self.subTest(gate=gate):
    p=self.path.parent/(gate+'.sqlite');cap=fixture();cap['quote']['ask_qty']=0;clock=Clock(datetime.fromisoformat(cap['quote']['asof']));d=PublicRecipeDesk(p,clock=clock);d.install(True);b='PUBLIC_IU_BODY_SPOT100';d.process_capture(b,cap)
    at=datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=1);cap['bars']=[];cap['quote'].update(asof=iso(at),ask_qty=10000000);cap['receipts']['quote']={'id':'newdepth-'+gate,'received_at':iso(at)};d.clock=Clock(at)
    if gate=='blocked':cap['entry_acquisition_errors']=['last_trade_stale_or_future']
    else:d.set_enabled(False)
    d.process_capture(b,cap)
    with sqlite3.connect(p) as db:s=json.loads(db.execute('SELECT state FROM books WHERE id=?',(b,)).fetchone()[0])
    self.assertIsNone(s['position']);self.assertEqual(s['orders'],{});d.close()
 def test_pending_origin_cannot_roll_into_next_native_bar_window(self):
  cap=fixture();end=datetime.fromisoformat(cap['bars'][-1]['close_at']);cap['receipts']['bars']['received_at']=iso(end+timedelta(seconds=298));cap['bars'][-1]['available_at']=cap['receipts']['bars']['received_at'];cap['quote'].update(asof=iso(end+timedelta(seconds=299)),ask_qty=0);cap['receipts']['quote']['received_at']=cap['quote']['asof'];cap['contract']['valid_until']=iso(end+timedelta(minutes=10));d,cap,b=self.installed(capture=cap);d.process_capture(b,cap)
  newer=fixture(at=end+timedelta(minutes=5),big=False,n=1);d.clock=Clock(datetime.fromisoformat(newer['quote']['asof']));d.process_capture(b,newer);s=self.state(b);self.assertIsNone(s['position']);self.assertIsNone(s['pending_target']);self.assertEqual(s['orders'],{})
 def test_partial_owned_close_remainder_uses_later_bid_and_no_duplicate_order(self):
  cap=fixture();cap['quote']['ask_qty']=5;d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);end=datetime.fromisoformat(cap['bars'][-1]['close_at']);new=fixture(at=end+timedelta(minutes=5),big=False,n=1);new['bars'][0].update(open=105,close=105,high=105.1,low=104.9);d.clock=Clock(datetime.fromisoformat(new['quote']['asof']));d.process_capture(b,new);stop=self.state(b)['position']['stop'];new['bars']=[];at=datetime.fromisoformat(new['quote']['asof'])+timedelta(seconds=1);new['quote']={'asof':iso(at),'bid':stop-1,'ask':stop-.9,'bid_qty':2.,'ask_qty':10000};new['receipts']['quote']={'id':'partialclose1','received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,new);self.assertEqual(self.state(b)['position']['qty'],3);oid=next(iter(self.state(b)['orders']))
  for i in (2,3):
   at+=timedelta(seconds=1);new['quote']['asof']=iso(at);new['receipts']['quote']={'id':'partialclose'+str(i),'received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,new)
  self.assertIsNone(self.state(b)['position']);fills=self.state(b)['fill_ledger'];self.assertEqual([f['order_id'] for f in fills if f['action']=='CLOSE_LONG'],[oid]*3)
 def test_foreign_schema_and_empty_foreign_brand_refused(self):
  with sqlite3.connect(self.path) as db:db.execute('CREATE TABLE foreign_money(cash REAL)');db.execute('INSERT INTO foreign_money VALUES(17)')
  self.assertRaises(ValueError,PublicRecipeDesk(self.path).install,True)
  with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT cash FROM foreign_money').fetchone()[0],17)
  self.path.unlink()
  with sqlite3.connect(self.path) as db:db.execute('PRAGMA application_id=1234')
  self.assertRaises(ValueError,PublicRecipeDesk(self.path).install,True)
 def test_main_database_filename_refused_even_uncreated(self):
  p=self.path.parent/'aster.sqlite';self.assertRaises(ValueError,PublicRecipeDesk(p).install,True);self.assertFalse(p.exists())
 def test_restart_state_hash_and_full_money_replay_reject_forged_cash(self):
  d,cap,b=self.installed();d.process_capture(b,cap)
  with sqlite3.connect(self.path) as db:
   s=json.loads(db.execute('SELECT state FROM books WHERE id=?',(b,)).fetchone()[0]);s['book']['cash']+=1000;db.execute('UPDATE books SET state=? WHERE id=?',(canonical(s),b));db.execute('UPDATE checkpoints SET state_sha=? WHERE book_id=?',(sha(s),b))
  fresh=PublicRecipeDesk(self.path);self.assertRaises(ValueError,fresh.process_capture,b,cap)
 def test_old_journal_edit_detected_in_same_process_after_external_commit(self):
  d,cap,b=self.installed();d.process_capture(b,cap)
  with sqlite3.connect(self.path) as db:
   r=db.execute('SELECT id,payload FROM events WHERE book_id=? AND id LIKE ? LIMIT1',(b,'bar:%')).fetchone() if False else db.execute('SELECT id,payload FROM events WHERE book_id=? AND id LIKE ? LIMIT 1',(b,'bar:%')).fetchone();event=json.loads(r[1]);event['bar']['volume']+=1;db.execute('UPDATE events SET payload=?,payload_sha=? WHERE book_id=? AND id=?',(canonical(event),sha(event),b,r[0]))
  self.assertRaises(ValueError,d.process_capture,b,cap)
 def test_idle_quotes_do_not_grow_immutable_event_journal(self):
  cap=fixture(big=False);d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);count=read_status(self.path)['event_count'];cap['bars']=[]
  for i in range(50):
   at=datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=1);cap['quote']['asof']=iso(at);cap['receipts']['quote']={'id':'idle'+str(i),'received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,cap)
  self.assertEqual(read_status(self.path)['event_count'],count)
 def test_worker_pid_birth_and_stale_status(self):
  import os
  now=datetime.now(timezone.utc);p=Path(str(self.path)+'.worker.json');p.write_text(canonical({'pid':os.getpid(),'pid_birth_tick':process_birth(os.getpid()),'heartbeat_at':iso(now),'phase':'running','interval_seconds':20}));self.assertTrue(worker_status(self.path)['running']);r=json.loads(p.read_text());r['pid_birth_tick']='wrong';p.write_text(canonical(r));self.assertFalse(worker_status(self.path)['running']);r['pid_birth_tick']=process_birth(os.getpid());r['heartbeat_at']=iso(now-timedelta(seconds=181));p.write_text(canonical(r));self.assertTrue(worker_status(self.path)['stale'])
 def test_http_default_transport_absolute_deadline_and_size_contract(self):
  calls=[]
  def transport(method,url,**kwargs):calls.append((method,url,kwargs));return 200,b'{"ok":true}'
  result,receipt=BinancePublicSpotFeed(transport=transport).fetch('fixture');self.assertTrue(result['ok']);self.assertEqual(calls[0][2]['timeout_seconds'],8);self.assertEqual(calls[0][2]['maximum_bytes'],256000);self.assertFalse(calls[0][2]['follow_redirects'])
 def test_enj_full_target_above900k_can_execute_legal11880_depth_chunk(self):
  cap=fixture();cap['quote'].update(bid=.03097,ask=.03098,ask_qty=11880,bid_qty=11880);cap['contract'].update(price_tick=.00001,qty_step=1,minimum_qty=1,maximum_qty=900000,minimum_notional=5);d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);s=self.state(b);self.assertEqual(s['position']['qty'],11880);self.assertEqual(s['orders'],{})
  with sqlite3.connect(self.path) as db:records=[json.loads(x[0]) for x in db.execute('SELECT intents FROM events WHERE book_id=?',(b,))]
  order=next(x for rs in records for x in rs if x['kind']=='PAPER_ORDER');self.assertEqual(order['qty'],900000);self.assertGreater(order['source_allocation_intended_qty'],900000)
 def test_venue_max_below_display_depth_fills_maximum_without_extra_additions(self):
  cap=fixture();cap['contract']['maximum_qty']=10;cap['quote']['ask_qty']=100;d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);self.assertEqual(self.state(b)['position']['qty'],10);self.assertEqual(len(self.state(b)['fill_ledger']),1)
 def test_legal_chunk_below_minimum_notional_has_no_fill(self):
  cap=fixture();cap['quote'].update(bid=.03097,ask=.03098,ask_qty=100,bid_qty=100);cap['contract'].update(price_tick=.00001,qty_step=1,minimum_qty=1,maximum_qty=900000,minimum_notional=5);d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);self.assertIsNone(self.state(b)['position']);self.assertEqual(self.state(b)['fill_ledger'],[])
 def test_strict_bool_install_and_control_before_mutation(self):
  for value in (None,0,1,2,'false','true',[],{}):
   with self.subTest(value=value):
    p=self.path.parent/('bad'+str(type(value).__name__)+str(value)+'.sqlite');d=PublicRecipeDesk(p);self.assertRaises(ValueError,d.install,value);self.assertFalse(p.exists())
  d=PublicRecipeDesk(self.path);d.install(False);count=read_status(self.path)['event_count']
  for value in (None,0,1,2,'false','true',[],{}):self.assertRaises(ValueError,d.set_enabled,value)
  self.assertEqual(read_status(self.path)['event_count'],count);self.assertTrue(all(not b['enabled'] for b in read_status(self.path)['books']))
 def test_external_sql_enabled_flip_refused_even_with_rehashed_checkpoint(self):
  cap=fixture();d,cap,b=self.installed(capture=cap,enable=False)
  with sqlite3.connect(self.path) as db:db.execute('UPDATE books SET enabled=1 WHERE id=?',(b,));db.execute('UPDATE checkpoints SET enabled_sha=? WHERE book_id=?',(sha({'enabled':True}),b))
  self.assertRaises(ValueError,d.process_capture,b,cap);self.assertRaises(ValueError,read_status,self.path);self.assertIsNone(self.state(b)['position'])
 def test_legitimate_control_history_replays_across_restart(self):
  d=PublicRecipeDesk(self.path);d.install(False);d.set_enabled(True);d.set_enabled(False);fresh=PublicRecipeDesk(self.path);fresh.set_enabled(True);s=read_status(self.path);self.assertTrue(all(b['enabled'] for b in s['books']));self.assertEqual(s['event_count'],12)
 def test_warm_cache_control_flag_flip_after_disable_refused(self):
  d,cap,b=self.installed();d.process_capture(b,cap);d.set_enabled(False)
  with sqlite3.connect(self.path) as db:db.execute('UPDATE books SET enabled=1 WHERE id=?',(b,))
  self.assertRaises(ValueError,d.process_capture,b,cap)
 def test_malformed_sql_control_flag_refused(self):
  d=PublicRecipeDesk(self.path);d.install(False)
  for flag in (2,'true'):
   with sqlite3.connect(self.path) as db:db.execute('UPDATE books SET enabled=? WHERE id=?',(flag,'PUBLIC_IU_BODY_SPOT100'))
   self.assertRaises(ValueError,read_status,self.path)
 def test_disable_clears_unsubmitted_old_pending_entry_before_fresh_quote(self):
  cap=fixture();cap['contract']=None;cap['entry_acquisition_errors']=[];d,cap,b=self.installed(capture=cap);d.process_capture(b,cap);self.assertIsNotNone(self.state(b)['pending_target']);d.set_enabled(False);new=fixture();new['bars']=[];at=datetime.fromisoformat(cap['quote']['asof'])+timedelta(seconds=1);new['quote']['asof']=iso(at);new['receipts']['quote']={'id':'valid-after-disable','received_at':iso(at)};d.clock=Clock(at);d.process_capture(b,new);self.assertIsNone(self.state(b)['position']);self.assertIsNone(self.state(b)['pending_target'])

if __name__=='__main__':unittest.main()
