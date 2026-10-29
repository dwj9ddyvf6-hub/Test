"""Isolated synthetic execution fixtures; these tests are not profit/market samples."""
import copy
import datetime as dt
from email.utils import format_datetime
from decimal import Decimal
import json
import hashlib
import itertools
import random
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend.prospective_native import (NativeProspectiveDesk,CoinbasePublicFeed,read_status,
    validate_capture,funded_targets,sha,SYMBOLS,RULES,FEE,MONEY_QUANTUM,UTC)
from backend.prospective_native_math import rebalance

OPEN=dt.datetime(2026,10,10,0,0,4,tzinfo=UTC)


def fixture(now=OPEN, gates=(True,True), specials=None, bids=(199.99,199.99),asks=(200.01,200.01)):
    """Fresh observed receipts and 200 native bars, explicitly synthetic market values."""
    now=now.astimezone(UTC);opening=now.replace(hour=0,minute=0,second=0,microsecond=0)
    specials=specials or {}
    candles={};products={};quotes={};receipts=[]
    def receipt(path,stamp):
        out={'url':'https://api.exchange.coinbase.com/'+path,'request_started_at':(stamp-dt.timedelta(milliseconds=10)).isoformat(),
             'received_at':stamp.isoformat(),'http_status':200,'server_date':format_datetime(stamp.replace(microsecond=0),usegmt=True),'raw_sha256':sha({'synthetic':path,'at':stamp.isoformat()}),'raw_bytes':100}
        receipts.append(out);return out
    for index,s in enumerate(SYMBOLS):
        observed=now-dt.timedelta(seconds=2-index*.2)
        r=receipt('products/'+s,observed-dt.timedelta(milliseconds=100))
        products[s]={'id':s,'base_currency':s.split('-')[0],'quote_currency':'USD','status':'online',
                     'base_increment':'0.00000001','quote_increment':'0.01','min_market_funds':'1',
                     'received_at':r['received_at'],'receipt_sha256':sha(r),
                     'trading_disabled':False,'cancel_only':False,'auction_mode':False,'post_only':False,'limit_only':False}
        r=receipt('products/'+s+'/candles?granularity=86400',observed)
        bars=[]
        for n in range(200):
            start=opening-dt.timedelta(days=200-n)
            price=specials.get((s,start.date().isoformat()),100)
            if n==199:price=specials.get((s,start.date().isoformat()),200 if gates[index] else 50)
            bars.append({'date':start.date().isoformat(),'start_at':start.isoformat(),'complete_at':(start+dt.timedelta(days=1)).isoformat(),
                         'open':price,'high':price+1,'low':price-1,'close':price,'volume':1000000,
                         'received_at':r['received_at'],'source_receipt_sha256':sha(r)})
        candles[s]=bars
    for index,s in enumerate(SYMBOLS):
        stamp=now-dt.timedelta(milliseconds=200-index*50)
        r=receipt('products/'+s+'/ticker',stamp)
        quotes[s]={'bid':str(bids[index]),'ask':str(asks[index]),'as_of':r['received_at'],'received_at':r['received_at'],
                   'market_trade_at':(stamp-dt.timedelta(milliseconds=10)).isoformat(),'source_receipt_sha256':sha(r),'clock_scope':'Synthetic fixture'}
    result={'venue':RULES['venue'],'paper_only':True,'requested_at':(now-dt.timedelta(seconds=3)).isoformat(),
            'received_at':(now-dt.timedelta(milliseconds=50)).isoformat(),'products':products,'bars':candles,'quotes':quotes,
            'receipts':receipts,'synthetic_fixture':True}
    return bind_raw(result)


def bind_raw(capture):
    for receipt in capture['receipts']:
        symbol=next(s for s in SYMBOLS if s in receipt['url'])
        if '/candles?'in receipt['url']:
            data=[[int(dt.datetime.fromisoformat(r['start_at']).timestamp()),r['low'],r['high'],r['open'],r['close'],r['volume']]for r in capture['bars'][symbol]]
        elif '/ticker'in receipt['url']:
            quote=capture['quotes'][symbol];data={'bid':quote['bid'],'ask':quote['ask'],'time':quote['market_trade_at']}
        else:data={k:v for k,v in capture['products'][symbol].items()if k not in ['received_at','receipt_sha256']}
        raw=json.dumps(data,separators=(',',':'));receipt.update(raw_body_utf8=raw,raw_bytes=len(raw.encode()),raw_sha256=hashlib.sha256(raw.encode()).hexdigest())
        digest=sha(receipt)
        if '/candles?'in receipt['url']:
            for row in capture['bars'][symbol]:row['source_receipt_sha256']=digest
        elif '/ticker'in receipt['url']:capture['quotes'][symbol]['source_receipt_sha256']=digest
        else:capture['products'][symbol]['receipt_sha256']=digest
    return capture


class NativeProspectiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'native.sqlite'
        self.desk=NativeProspectiveDesk(self.path)
    def tearDown(self):self.temp.cleanup()
    def financial(self):
        with self.desk.connect()as c:
            return {name:[dict(r)for r in c.execute('SELECT * FROM '+name+' ORDER BY rowid')]for name in ['native_books','native_positions','native_orders','native_fills','native_cycles']}
    def counts(self):
        with self.desk.connect()as c:return c.execute('SELECT count(*)FROM native_fills').fetchone()[0]
    def audit(self):
        with self.desk.connect()as c:return self.desk.verify_ledger(c)
    def test_empty_and_missing_read_status_does_not_create(self):
        missing=Path(self.temp.name)/'missing/anything.sqlite'
        self.assertEqual(read_status(missing)['status'],'not_installed');self.assertFalse(missing.parent.exists())
        self.assertEqual(read_status(self.path)['installed_count'],0)
        before={p.name:p.read_bytes()for p in self.path.parent.iterdir()if p.is_file()}
        read_status(self.path)
        self.assertEqual(before,{p.name:p.read_bytes()for p in self.path.parent.iterdir()if p.is_file()})
        self.assertEqual(self.audit()['fills'],0)
    def test_isolated_main_or_unrelated_database_rejected(self):
        with self.assertRaises(ValueError):NativeProspectiveDesk(Path(self.temp.name)/'aster.sqlite')
        self.assertFalse((Path(self.temp.name)/'aster.sqlite').exists())
        other=Path(self.temp.name)/'other.sqlite'
        with sqlite3.connect(other)as c:c.execute('CREATE TABLE strategy_books(x)')
        with self.assertRaises(ValueError):NativeProspectiveDesk(other)
        with sqlite3.connect(other)as c:self.assertEqual(c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[('strategy_books',)])
    def test_explicit_install_is_idempotent_and_books_separate(self):
        a=self.desk.install(True,OPEN);before=self.financial();self.desk.install(False,OPEN+dt.timedelta(seconds=1))
        self.assertEqual(before,self.financial());self.assertEqual(a['installed_count'],2)
        self.assertEqual([x['cash']for x in a['books']],['100000','100000'])
        with self.desk.connect()as c:self.assertEqual(c.execute("SELECT count(*)FROM native_events WHERE kind='virtual_funding'").fetchone()[0],2)
    def test_quote_funded_lot_entry_and_conservation(self):
        self.desk.install(True,OPEN);result=self.desk.run_once(fixture(),OPEN)
        self.assertEqual(result['fills'],3);self.assertEqual(self.audit()['fills'],3)
        for book in read_status(self.path)['books']:
            self.assertLess(Decimal(book['cash']),Decimal('.01'));self.assertGreaterEqual(Decimal(book['cash']),0)
            self.assertEqual(set(book['positions']),{'ETH-USD'} if book['sleeve']=='ETH_SMA200'else set(SYMBOLS))
        with self.desk.connect()as c:
            for f in c.execute('SELECT *FROM native_fills'):
                q=Decimal(f['quantity']);p=Decimal(f['price']);fee=Decimal(f['fee'])
                self.assertEqual(p,Decimal('200.01'));self.assertEqual(q%Decimal('0.00000001'),0)
                self.assertEqual(fee,(q*p*FEE).quantize(MONEY_QUANTUM,rounding='ROUND_UP'))
    def test_same_day_restart_and_concurrent_workers_no_duplicate_fills(self):
        self.desk.install(True,OPEN)
        errors=[]
        def go():
            try:NativeProspectiveDesk(self.path).run_once(fixture(),OPEN)
            except Exception as exc:errors.append(exc)
        threads=[threading.Thread(target=go)for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(errors,[]);self.assertEqual(self.counts(),3)
        self.assertEqual(NativeProspectiveDesk(self.path).run_once(fixture(),OPEN)['fills'],0)
        self.audit()
    def test_genuine_next_day_exit_no_new_entries_after_window(self):
        self.desk.install(True,OPEN);self.desk.run_once(fixture(),OPEN)
        later=OPEN+dt.timedelta(days=1,hours=3)
        specials={(s,'2026-10-09'):200 for s in SYMBOLS}
        result=self.desk.run_once(fixture(later,(False,False),specials,bids=(149.99,149.99),asks=(150.01,150.01)),later)
        self.assertEqual(result['fills'],3)
        for b in read_status(self.path)['books']:self.assertEqual(b['positions'],{})
        with self.desk.connect()as c:self.assertEqual([r[0]for r in c.execute('SELECT side FROM native_fills ORDER BY rowid')],['buy','buy','buy','sell','sell','sell'])
        self.audit()
    def test_disabled_entries_preserve_owned_exit(self):
        self.desk.install(True,OPEN);self.desk.run_once(fixture(),OPEN)
        self.desk.set_enabled('ETH_SMA200',False,OPEN)
        later=OPEN+dt.timedelta(days=1)
        result=self.desk.run_once(fixture(later,(False,False),{(s,'2026-10-09'):200 for s in SYMBOLS}),later)
        self.assertEqual(result['fills'],3);self.assertEqual(read_status(self.path)['enabled_count'],1)
        self.audit()
    def test_missed_window_and_paused_install_make_no_entries(self):
        self.desk.install(True,OPEN);later=OPEN+dt.timedelta(minutes=5)
        self.assertEqual(self.desk.run_once(fixture(later),later)['fills'],0)
        self.assertEqual(self.counts(),0)
        second=NativeProspectiveDesk(Path(self.temp.name)/'paused.sqlite');second.install(False,OPEN)
        self.assertEqual(second.run_once(fixture(),OPEN)['fills'],0)
    def test_signal_gate_is_strict_and_parity_with_r14(self):
        payload=fixture(gates=(False,False))
        # A flat completed history equals its SMA and must stay in cash.
        for s in SYMBOLS:
            for r in payload['bars'][s]:r.update(open=100,high=101,low=99,close=100)
        payload=bind_raw(payload)
        market=validate_capture(payload,OPEN);self.assertEqual([m['gate']for m in market.values()],[False,False])
        self.desk.install(True,OPEN);self.assertEqual(self.desk.run_once(payload,OPEN)['fills'],0)
    def test_bad_receipts_stale_quotes_and_native_causality_fail_closed(self):
        self.desk.install(True,OPEN);baseline=self.financial()
        cases=[]
        x=fixture();x['quotes']['BTC-USD']['market_trade_at']=(OPEN-dt.timedelta(seconds=31)).isoformat();cases.append(x)
        x=fixture();x['quotes']['BTC-USD']['as_of']=(OPEN+dt.timedelta(seconds=1)).isoformat();cases.append(x)
        x=fixture();x['quotes']['BTC-USD']['bid']='200.005';cases.append(x)
        x=fixture();x['bars']['BTC-USD'][-1]['complete_at']=(OPEN+dt.timedelta(days=1)).isoformat();cases.append(x)
        x=fixture();x['bars']['BTC-USD'][10]['source_receipt_sha256']='0'*64;cases.append(x)
        x=fixture();x['products']['ETH-USD']['quote_currency']='USDT';cases.append(x)
        x=fixture();x['products']['BTC-USD']['trading_disabled']=True;cases.append(x)
        x=fixture();x['quotes']['BTC-USD']['market_trade_at']=None;cases.append(x)
        x=fixture();x['bars']['BTC-USD']=x['bars']['BTC-USD'][1:];cases.append(x)
        for case in cases:
            with self.subTest(case=cases.index(case)):
                self.assertEqual(self.desk.run_once(case,OPEN)['status'],'blocked');self.assertEqual(self.financial(),baseline)
        self.audit()
    def test_daily_vendor_revision_is_audited_without_trades(self):
        self.desk.install(True,OPEN);self.desk.run_once(fixture(),OPEN)
        before=self.financial();changed=fixture();changed['bars']['BTC-USD'][10]['volume']=1000001;bind_raw(changed)
        self.assertEqual(self.desk.run_once(changed,OPEN)['status'],'source_revision_block')
        self.assertEqual(before,self.financial());self.audit()
    def test_actual_raw_economic_bindings_and_missing_metadata_fail_closed(self):
        self.desk.install(True,OPEN);before=self.financial();cases=[]
        x=fixture();x['quotes']['BTC-USD']['bid']='199.98';cases.append(x)
        x=fixture();x['bars']['ETH-USD'][-1].update(close=199,open=199);cases.append(x)
        x=fixture();x['products']['BTC-USD']['base_increment']='0.1';cases.append(x)
        x=fixture();x['receipts'][0].pop('raw_body_utf8');cases.append(x)
        x=fixture();x['products']['BTC-USD'].pop('min_market_funds');bind_raw(x);cases.append(x)
        x=fixture();x['products']['BTC-USD'].pop('limit_only');bind_raw(x);cases.append(x)
        for index,capture in enumerate(cases):
            with self.subTest(case=index):
                self.assertEqual(self.desk.run_once(capture,OPEN)['status'],'blocked');self.assertEqual(before,self.financial())
    def test_raw_sources_are_retained_and_deduplicated(self):
        self.desk.install(True,OPEN);self.desk.run_once(fixture(),OPEN);self.desk.run_once(fixture(),OPEN)
        with self.desk.connect()as c:
            sources=c.execute('SELECT *FROM native_raw_sources').fetchall()
            # This fixture's BTC/ETH candle bodies are byte-identical, so six receipts use five payloads.
            self.assertEqual(len(sources),5)
            for source in sources:self.assertEqual(hashlib.sha256(source['body'].encode()).hexdigest(),source['sha256'])
            event=json.loads(c.execute("SELECT payload FROM native_events WHERE kind='market_capture'LIMIT 1").fetchone()[0])
            self.assertTrue(all('raw_body_utf8'not in r for r in event['receipts']))
            self.assertTrue(all(any(s['sha256']==r['raw_sha256']for s in sources)for r in event['receipts']))
    def test_previous_acquisition_product_cannot_be_reused_as_current_metadata(self):
        self.desk.install(True,OPEN);capture=fixture()
        receipt=capture['receipts'][0];receipt['request_started_at']=(OPEN-dt.timedelta(days=2)).isoformat()
        receipt['received_at']=(OPEN-dt.timedelta(days=2)+dt.timedelta(milliseconds=1)).isoformat()
        receipt['server_date']=format_datetime((OPEN-dt.timedelta(days=2)).replace(microsecond=0),usegmt=True)
        capture['products']['BTC-USD']['received_at']=receipt['received_at'];bind_raw(capture)
        self.assertEqual(self.desk.run_once(capture,OPEN)['status'],'blocked');self.assertEqual(self.counts(),0)
    def test_partial_financial_failure_rolls_back_atomically(self):
        self.desk.install(True,OPEN);before=self.financial();original=self.desk._fill;calls=[]
        def failing(*args,**kwargs):
            calls.append(True)
            if len(calls)==2:raise ValueError('Injected interruption after first local fill')
            return original(*args,**kwargs)
        with patch.object(self.desk,'_fill',side_effect=failing):
            with self.assertRaises(ValueError):self.desk.run_once(fixture(),OPEN)
        self.assertEqual(before,self.financial());self.assertEqual(self.desk.run_once(fixture(),OPEN)['fills'],3)
        self.audit()
    def test_tampered_cash_blocks_new_financial_decisions(self):
        self.desk.install(True,OPEN)
        with self.desk.connect()as c:c.execute("UPDATE native_books SET cash='100001'WHERE book='ETH_SMA200'")
        with self.assertRaises(ValueError):self.desk.run_once(fixture(),OPEN)
        self.assertEqual(self.counts(),0)
    def test_unjournaled_entry_enable_is_rejected_before_fills(self):
        self.desk.install(False,OPEN)
        with self.desk.connect()as c:c.execute("UPDATE native_books SET enabled=1")
        with self.assertRaisesRegex(ValueError,'authorization'):self.desk.run_once(fixture(),OPEN)
        self.assertEqual(self.counts(),0)
    def test_unfunded_enable_does_not_install_and_explicit_enable_is_journaled(self):
        with self.assertRaisesRegex(ValueError,'not installed'):self.desk.set_enabled('ETH_SMA200',True,OPEN)
        self.assertEqual(read_status(self.path)['installed_count'],0)
        self.desk.install(False,OPEN);self.desk.set_enabled('ETH_SMA200',True,OPEN)
        self.assertEqual(self.desk.run_once(fixture(),OPEN)['fills'],1)
        self.audit()
    def test_order_receipt_quote_and_ownership_corruption_are_rejected(self):
        self.desk.install(True,OPEN);self.desk.run_once(fixture(),OPEN)
        with self.desk.connect()as c:
            order=dict(c.execute('SELECT *FROM native_orders LIMIT 1').fetchone())
        quote=json.loads(order['quote']);quote['ask']='999999.00'
        for field,value in [('quote',json.dumps(quote)),('day','2026-10-01'),('book','ETH_SMA200'),('quantity','1'),('created_at','2026-10-01T00:00:04+00:00'),('filled_at','2026-10-01T00:00:04+00:00')]:
            with self.subTest(field=field):
                if value==order[field]:continue
                with self.desk.connect()as c:c.execute('UPDATE native_orders SET '+field+'=?WHERE id=?',(value,order['id']))
                with self.assertRaisesRegex(ValueError,'receipts disagree'):self.audit()
                with self.desk.connect()as c:c.execute('UPDATE native_orders SET '+field+'=?WHERE id=?',(order[field],order['id']))
        self.audit()
    def test_sells_precede_buys_and_reconcile_actual_cash(self):
        self.desk.install(True,OPEN);self.desk.run_once(fixture(gates=(True,False)),OPEN)
        later=OPEN+dt.timedelta(days=1)
        specials={('BTC-USD','2026-10-09'):200,('ETH-USD','2026-10-09'):50}
        before=self.counts();result=self.desk.run_once(fixture(later,(False,True),specials),later)
        self.assertEqual(result['fills'],3)
        with self.desk.connect()as c:
            rows=[dict(r)for r in c.execute('SELECT *FROM native_fills ORDER BY rowid')][before:]
            self.assertEqual([(r['book'],r['side'])for r in rows],[('BTC_ETH_SMA200','sell'),('BTC_ETH_SMA200','buy'),('ETH_SMA200','buy')])
        self.audit()
    def test_symmetric_zero_spread_targets_match_unchanged_r14(self):
        market=validate_capture(fixture(bids=(200,200),asks=(200,200)),OPEN)
        for cash,q,weights in [(100000,[0,0],[0,1]),(5000,[300,100],[.5,.5]),(0,[0,500],[.5,.5]),(1,[200,100],[0,0])]:
            result=funded_targets(str(cash),dict(zip(SYMBOLS,map(str,q))),market,weights)
            _,expected,_=rebalance(cash,q,[200,200],weights,.002)
            for symbol,v in zip(SYMBOLS,expected):self.assertLessEqual(abs(float(result[symbol])-v),1.1e-8)
    def test_independent_closed_form_funding_across_500_books(self):
        rng=random.Random(12092026)
        for trial in range(500):
            cash=Decimal(rng.randrange(0,10000000))/100
            quantities={s:Decimal(rng.randrange(0,100000))/100 for s in SYMBOLS}
            weights=rng.choice([(0,0),(0,1),(.5,.5),(.5,0),(0,.5)])
            market={}
            for s in SYMBOLS:
                bid=Decimal(rng.randrange(100,10000000))/100
                ask=bid+Decimal(rng.randrange(0,100))/100
                market[s]={'bid':bid,'ask':ask,'mid':(bid+ask)/2,'lot':Decimal('0.00000001')}
            pre=cash+sum(quantities[s]*market[s]['mid']for s in SYMBOLS)
            feasible=[]
            for signs in itertools.product([False,True],repeat=2):
                coefficient=Decimal(0);constant=Decimal(0)
                for s,w,buy in zip(SYMBOLS,weights,signs):
                    m=market[s];w=Decimal(str(w));q=quantities[s]
                    if buy:
                        cost=m['ask']-m['mid']+FEE*m['ask'];coefficient+=cost*w/m['mid'];constant-=cost*q
                    else:
                        cost=m['mid']-m['bid']+FEE*m['bid'];coefficient-=cost*w/m['mid'];constant+=cost*q
                candidate=(pre-constant)/(1+coefficient)
                if all((Decimal(str(w))*candidate/market[s]['mid']>=quantities[s])==buy for s,w,buy in zip(SYMBOLS,weights,signs)):
                    feasible.append(candidate)
            self.assertEqual(len(feasible),1,msg=str(trial));nav=feasible[0]
            actual=funded_targets(cash,quantities,market,weights)
            for s,w in zip(SYMBOLS,weights):
                ideal=Decimal(str(w))*nav/market[s]['mid']
                self.assertLessEqual(actual[s],ideal+Decimal('1e-18'))
                self.assertLess(ideal-actual[s],market[s]['lot']+Decimal('1e-18'))
    def test_status_does_not_claim_inactive_worker_running(self):
        self.desk.install(True,OPEN);self.assertFalse(read_status(self.path)['worker']['running'])
        self.desk.heartbeat();self.assertTrue(read_status(self.path)['worker']['running'])
        self.desk.heartbeat(False);self.assertFalse(read_status(self.path)['worker']['running'])
    def test_serve_records_failure_and_stays_restartable(self):
        stop=threading.Event()
        def failing():stop.set();raise ValueError('Injected source/ledger failure')
        with patch.object(self.desk,'run_once',side_effect=failing):self.desk.serve(5,stop)
        status=read_status(self.path);self.assertFalse(status['worker']['running']);self.assertIn('Injected',status['last_error'])
    def test_capture_uses_only_public_get_and_quotes_after_all_signals(self):
        calls=[];feed=CoinbasePublicFeed()
        def fake_get(tail):
            calls.append(tail)
            base=fixture();symbol=next(s for s in SYMBOLS if s in tail)
            if '/candles?'in tail:
                data=[[int(dt.datetime.fromisoformat(r['start_at']).timestamp()),r['low'],r['high'],r['open'],r['close'],r['volume']]for r in base['bars'][symbol]]
            elif '/ticker?'in tail:data={'bid':'200.00','ask':'200.01','time':OPEN.isoformat()}
            else:data=base['products'][symbol]
            received=OPEN+dt.timedelta(milliseconds=len(calls))
            receipt={'url':feed.BASE+tail,'request_started_at':OPEN.isoformat(),'received_at':received.isoformat(),'http_status':200,
                     'raw_sha256':sha(data),'raw_bytes':len(json.dumps(data)),'server_date':format_datetime(received.replace(microsecond=0),usegmt=True)}
            return data,receipt
        with patch.object(feed,'_get_json',side_effect=fake_get),patch('backend.prospective_native.clock',side_effect=lambda value=None:OPEN+dt.timedelta(seconds=1)if value is None else dt.datetime.fromisoformat(value)if isinstance(value,str)else value):
            capture=feed.capture(OPEN)
        self.assertTrue(all('/ticker?'in x for x in calls[-2:]));self.assertEqual(len(capture['bars']['BTC-USD']),200)
        self.assertEqual(len(capture['receipts']),6)


if __name__=='__main__':unittest.main()
