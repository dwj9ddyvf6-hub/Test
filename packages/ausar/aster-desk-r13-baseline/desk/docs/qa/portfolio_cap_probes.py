"""Independent QA probes; temporary SQLite state, fake broker, no networking."""
import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.store import Store, DeskError
from backend.trading import TradingDesk

UTC = timezone.utc

class FakeBroker:
    def __init__(self):
        self.cash = '1000'
        self.remote_positions = []
        self.remote_orders = []
        self.fail_read = False
        self.submits = self.cancels = 0
    def account(self):
        if self.fail_read:
            raise RuntimeError('Fixture read failure')
        return {'cash': self.cash, 'equity': self.cash, 'account_number': 'ISOLATED-PAPER-QA'}
    def positions(self):
        return list(self.remote_positions)
    def orders(self):
        return list(self.remote_orders)
    def get_order(self, client_id):
        return next((x for x in self.remote_orders if x['client_order_id'] == client_id), None)
    def submit(self, intent):
        self.submits += 1
        row = {'id': f'fake-{self.submits}', 'client_order_id': intent['client_id'], 'symbol': intent['symbol'], 'side': intent['side'], 'qty': str(intent['quantity']), 'type': intent['order_type'], 'time_in_force': intent['time_in_force'], 'status': 'accepted', 'filled_qty': '0', 'filled_avg_price': None, 'submitted_at': datetime.now(UTC).isoformat(), 'legs': []}
        self.remote_orders.append(row)
        return row
    def cancel(self, order_id):
        self.cancels += 1
        next(x for x in self.remote_orders if x['id'] == order_id)['status'] = 'canceled'

class FakeProviders:
    def __init__(self, broker):
        self.broker = broker
    def calendar(self, clock=None):
        clock = clock or datetime.now(UTC)
        return {'is_session': True, 'is_open': True, 'session_date': clock.date().isoformat(), 'open_at': (clock-timedelta(hours=1)).isoformat(), 'close_at': (clock+timedelta(hours=5)).isoformat()}

@contextmanager
def fixture(broker=False):
    with tempfile.TemporaryDirectory(prefix='aster-portfolio-review-') as temp:
        store = Store(Path(temp)/'isolated.sqlite')
        trading = TradingDesk(store)
        fake = FakeBroker()
        providers = FakeProviders(fake)
        store.ingest_quote('AAPL', Decimal('10'), datetime.now(UTC), 'Isolated manual QA fixture')
        if broker:
            book = trading.create_book({'name':'Fake broker book', 'broker':'alpaca'})['id']
            assert trading.reconcile(providers)['errors'] == []
        else:
            book = 'main'
            trading.fund_book(book, 1000, 'fixture-fund')
        yield store, trading, providers, fake, book

def authorize(t, book, client='probe', **fields):
    return t.submit_intent({'book_id':book, 'symbol':'AAPL', 'side':'buy', 'quantity':10, 'client_id':client, 'time_in_force':'gtc', **fields})

def error_for(fn):
    try:
        fn()
    except DeskError as exc:
        return exc.detail
    return None

def order(t, intent):
    return next(x for x in t.snapshot()['intents'] if x['id']==intent['id'])

results=[]
def record(probe, expected, observed, passed):
    results.append({'probe':probe,'expected':expected,'observed':observed,'passed':passed})

with fixture() as (s,t,p,b,book):
    books=[book]
    for i in range(7):
        bid=t.create_book({'name':f'Concurrent independent book {i}'})['id']
        t.fund_book(bid,1000,'fund')
        books.append(bid)
    t.set_portfolio_policy({'gross_exposure_cap':100})
    def concurrent(i):
        td=TradingDesk(Store(s.path))
        try:
            authorize(td,books[i%8],f'concurrent-{i}')
            return True
        except DeskError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        accepted=sum(pool.map(concurrent,range(16)))
    exposure=t.snapshot()['global_exposure']
    record('cross_instance_atomic_reservations', 'Exactly one $100 intent across 16 concurrent submissions and 8 books', {'accepted':accepted,'projected':exposure['projected_gross_exposure']},accepted==1 and exposure['projected_gross_exposure']==100)

with fixture() as (s,t,p,b,book):
    t.set_portfolio_policy({'gross_exposure_cap':20})
    err=error_for(lambda:authorize(t,book,quantity=1,order_type='stop_limit',limit_price=25,stop_price=30))
    t.set_portfolio_policy({'gross_exposure_cap':30})
    authorize(t,book,quantity=1,order_type='stop_limit',limit_price=25,stop_price=30)
    projected=t.snapshot()['global_exposure']['projected_gross_exposure']
    record('explicit_price_envelope', 'Reject at $20 and reserve $30 for quote=$10, limit=$25, stop=$30', {'error':err,'projected':projected},bool(err and 'gross exposure cap' in err) and projected==30)

with fixture() as (s,t,p,b,book):
    authorize(t,book,quantity=5)
    t.process(p)
    other=t.create_book({'name':'Known empty book'})['id']
    t.fund_book(other,1000,'fund')
    s.ingest_quote('MSFT',Decimal('10'),datetime.now(UTC),'Isolated manual QA fixture')
    with s.transaction() as con:
        con.execute("DELETE FROM quotes WHERE symbol='AAPL'")
    t.set_portfolio_policy({'gross_exposure_cap':1000})
    exposure=t.snapshot()['global_exposure']
    err=error_for(lambda:authorize(t,other,symbol='MSFT',quantity=1))
    views={x['book_id']:x for x in exposure['books']}
    record('missing_mark_truthful_view_and_gate', 'Global/affected-book values null, unaffected empty book zero, fresh unrelated entry rejected', {'valuation':exposure['valuation_status'],'global':exposure['gross_exposure'],'affected':views[book]['gross_exposure'],'unaffected':views[other]['gross_exposure'],'error':err}, exposure['valuation_status']=='incomplete' and exposure['gross_exposure'] is None and views[book]['gross_exposure'] is None and views[other]['gross_exposure']==0 and bool(err))

with fixture(broker=True) as (s,t,p,b,book):
    t.set_portfolio_policy({'gross_exposure_cap':100})
    intent=authorize(t,book)
    t.process(p)
    remote=b.remote_orders[0]
    remote.update(status='partially_filled',filled_qty='3',filled_avg_price='10',filled_at=datetime.now(UTC).isoformat())
    b.remote_positions=[{'symbol':'AAPL','qty':'3','avg_entry_price':'10','side':'long'}]
    b.cash='970'
    assert t.reconcile(p)['errors']==[]
    exposure=t.snapshot()['global_exposure']
    record('partial_fill_not_double_counted', 'Observed $30 plus remaining $70 gives projected $100', {'gross':exposure['gross_exposure'],'projected':exposure['projected_gross_exposure']}, exposure['gross_exposure']==30 and exposure['projected_gross_exposure']==100)
    t.cancel_intent(intent['id'])
    before=t.snapshot()['global_exposure']['projected_gross_exposure']
    t.process(p)
    during=t.snapshot()['global_exposure']['projected_gross_exposure']
    t.reconcile(p)
    after=t.snapshot()['global_exposure']['projected_gross_exposure']
    record('cancellation_retains_capacity_until_confirmed', 'Project $100 until actual terminal cancellation, then $30', {'before':before,'pending_cancel':during,'after_terminal':after},before==100 and during==100 and after==30)

with fixture(broker=True) as (s,t,p,b,book):
    intent=authorize(t,book)
    t.process(p)
    with s.transaction() as con:
        con.execute("DELETE FROM quotes WHERE symbol='AAPL'")
    t.set_portfolio_policy({'gross_exposure_cap':50})
    t.process(p)
    exposed=t.snapshot()['global_exposure']
    observed={'cancel_calls':b.cancels,'intent_status':order(t,intent)['status'],'valuation':exposed['valuation_status'],'projected':exposed['projected_gross_exposure']}
    record('accepted_entry_missing_quote', 'Existing entry cancellation requested when enabled cap cannot value missing mark', observed,b.cancels==1 and order(t,intent)['status']=='cancel_requested')

with fixture(broker=True) as (s,t,p,b,book):
    intent=authorize(t,book)
    t.process(p)
    b.fail_read=True
    t.reconcile(p)
    t.set_portfolio_policy({'gross_exposure_cap':50})
    t.process(p)
    observed={'cancel_calls':b.cancels,'intent_status':order(t,intent)['status'],'error':order(t,intent)['error'],'remote_status':b.remote_orders[0]['status']}
    record('accepted_entry_failed_reconciliation', 'Existing accepted entry remains cancellable after cap reduction despite failed account read',observed,b.cancels==1 and order(t,intent)['status']=='cancel_requested')

with fixture(broker=True) as (s,t,p,b,book):
    b.remote_positions=[{'symbol':'AAPL','qty':'10','avg_entry_price':'10','side':'long'}]
    b.remote_orders=[{'id':'foreign-parent','client_order_id':'foreign-bracket','symbol':'AAPL','side':'buy','qty':'10','type':'market','time_in_force':'gtc','status':'filled','filled_qty':'10','filled_avg_price':'10','order_class':'bracket','legs':[{'id':'foreign-live-leg','client_order_id':'foreign-protection','symbol':'AAPL','side':'sell','qty':'10','type':'stop','stop_price':'9','time_in_force':'gtc','status':'new','filled_qty':'0'}]}]
    assert t.reconcile(p)['errors']==[]
    t.set_portfolio_policy({'gross_exposure_cap':500})
    t.fund_book('main',1000,'fund')
    exposure=t.snapshot()['global_exposure']
    err=error_for(lambda:authorize(t,'main',quantity=1))
    observed={'valuation':exposure['valuation_status'],'projected':exposure['projected_gross_exposure'],'reasons':exposure['incomplete_reasons'],'entry_error':err}
    record('foreign_live_nested_order', 'Unattributed active nested broker order makes pending exposure unknown and gates entries',observed,exposure['valuation_status']=='incomplete' and bool(err))

with fixture(broker=True) as (s,t,p,b,book):
    intent=authorize(t,book,take_profit=12,stop_loss=9)
    t.process(p)
    parent=b.remote_orders[0]
    parent.update(status='filled',filled_qty='10',filled_avg_price='10',filled_at=datetime.now(UTC).isoformat())
    parent['legs']=[{'id':'owned-stop','client_order_id':'generated-native-stop','symbol':'AAPL','side':'sell','qty':'10','type':'stop','stop_price':'9','time_in_force':'gtc','status':'new','filled_qty':'0'}]
    # Position was closed externally; the still-working native leg can open a short.
    b.remote_positions=[]
    b.cash='1000'
    assert t.reconcile(p)['errors']==[]
    t.set_portfolio_policy({'gross_exposure_cap':500})
    t.fund_book('main',1000,'fund')
    exposure=t.snapshot()['global_exposure']
    err=error_for(lambda:authorize(t,'main',quantity=1))
    observed={'valuation':exposure['valuation_status'],'projected':exposure['projected_gross_exposure'],'reasons':exposure['incomplete_reasons'],'entry_error':err}
    record('owned_protection_against_flat_position', 'Active protective sell with flat broker position makes pending exposure unknown and gates entries',observed,exposure['valuation_status']=='incomplete' and bool(err))

with fixture(broker=True) as (s,t,p,b,book):
    intent=authorize(t,book,take_profit=12,stop_loss=9)
    t.process(p)
    parent=b.remote_orders[0]
    parent.update(status='filled',filled_qty='10',filled_avg_price='10',filled_at=datetime.now(UTC).isoformat())
    parent['legs']=[{'id':'owned-stop','client_order_id':'generated-native-stop','symbol':'AAPL','side':'sell','qty':'10','type':'stop','stop_price':'9','time_in_force':'gtc','status':'new','filled_qty':'0'}]
    b.remote_positions=[{'symbol':'AAPL','qty':'5','avg_entry_price':'10','side':'long'}]
    b.cash='950'
    assert t.reconcile(p)['errors']==[]
    t.set_portfolio_policy({'gross_exposure_cap':500})
    exposure=t.snapshot()['global_exposure']
    observed={'valuation':exposure['valuation_status'],'projected':exposure['projected_gross_exposure'],'reasons':exposure['incomplete_reasons']}
    record('owned_protection_exceeds_remaining_position', 'Protective quantity 10 against actual held 5 makes pending exposure unknown',observed,exposure['valuation_status']=='incomplete')

with fixture(broker=True) as (s,t,p,b,book):
    intent=authorize(t,book,take_profit=12,stop_loss=9)
    t.process(p)
    parent=b.remote_orders[0]
    parent.update(status='filled',filled_qty='10',filled_avg_price='10',filled_at=datetime.now(UTC).isoformat())
    parent['legs']=[{'id':'owned-stop','client_order_id':'generated-native-stop','symbol':'AAPL','side':'sell','qty':'10','type':'stop','stop_price':'9','time_in_force':'gtc','status':'new','filled_qty':'0'}, {'id':'owned-target','client_order_id':'generated-native-target','symbol':'AAPL','side':'sell','qty':'10','type':'limit','limit_price':'12','time_in_force':'gtc','status':'new','filled_qty':'0'}]
    b.remote_positions=[{'symbol':'AAPL','qty':'10','avg_entry_price':'10','side':'long'}]
    b.cash='900'
    assert t.reconcile(p)['errors']==[]
    t.set_portfolio_policy({'gross_exposure_cap':500})
    exposure=t.snapshot()['global_exposure']
    record('matched_native_oco_not_double_counted', 'Correctly matched OCO exits produce complete $100 observed/projected exposure', {'valuation':exposure['valuation_status'],'gross':exposure['gross_exposure'],'projected':exposure['projected_gross_exposure'],'reasons':exposure['incomplete_reasons']}, exposure['valuation_status']=='complete' and exposure['gross_exposure']==100 and exposure['projected_gross_exposure']==100)

with fixture() as (s,t,p,b,book):
    t.set_book(book,{'allow_short':True})
    authorize(t,book,side='sell',quantity=5)
    assert t.process(p)['fills']==1
    t.create_book({'name':'Unknown unrelated broker account','broker':'alpaca'})
    t.set_book(book,{'halted':True,'halt_reason':'QA halt'})
    t.set_portfolio_policy({'gross_exposure_cap':1})
    exit_intent=authorize(t,book,client='short-cover',quantity=5)
    completed=t.process(p)
    record('halted_short_cover_survives_global_unknown', 'Explicit reducing cover fills under halt, exceeded cap and unrelated unknown broker state', {'fills':completed['fills'],'status':order(t,exit_intent)['status'],'positions':t.snapshot()['positions']},completed['fills']==1 and order(t,exit_intent)['status']=='filled' and not t.snapshot()['positions'])

out=Path(__file__).with_name('portfolio_cap_probe_results.json')
out.write_text(json.dumps({'generated_at':datetime.now(UTC).isoformat(),'safety':'Temporary SQLite files and fake providers only. No network or real broker calls.','results':results},indent=2)+'\n')
print(json.dumps({'result_file':str(out),'results':results},indent=2))
