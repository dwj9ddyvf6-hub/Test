"""Corporate-action accounting uses isolated books and explicit synthetic events."""
import base64
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backend.providers import exchange_calendar
from backend.store import DeskError, Store
from backend.tensor_actions import TensorActions
from backend.trading import TradingDesk

UTC = timezone.utc

class CalendarFixture:
    broker = None
    def calendar(self, clock=None):
        return exchange_calendar(clock)

class TensorActionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / 'fixture.sqlite'
        self.store = Store(self.path)
        self.trading = TradingDesk(self.store)
        self.book = self.trading.create_book({'name': 'Action fixture', 'kind': 'forward', 'broker': 'local'})['id']
        self.installation = 'action-fixture'
        self.trading.fund_book(self.book, 10000, 'synthetic-capital')
        self.trading.claim_strategy_book(self.book, self.installation)
        self.entry = datetime(2026, 7, 2, 15, tzinfo=UTC)
        self.ex = datetime(2026, 7, 6, 13, 30, 5, tzinfo=UTC)
        self.providers = CalendarFixture()
        self.requests = []
        self.events = {}

    def tearDown(self):
        self.temporary.cleanup()

    def quote(self, price=100, clock=None, sym='AAPL'):
        with self.store.transaction() as con:
            con.execute('INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)', (sym, str(price), (clock or self.entry).isoformat(), 'Synthetic execution observation'))

    def order(self, key, qty, clock, side='buy', sym='AAPL'):
        return self.trading.submit_strategy_intent({'book_id': self.book, 'client_id': key, 'symbol': sym, 'side': side, 'quantity': qty, 'order_type': 'market', 'time_in_force': 'gtc'}, self.installation, clock=clock)

    def buy(self, qty=10, clock=None, price=100, key='entry'):
        clock = clock or self.entry
        self.quote(price, clock)
        order = self.order(key, qty, clock)
        self.assertEqual(self.trading.process(self.providers, clock)['fills'], 1)
        return order

    def transport(self, method, url, payload, headers):
        self.requests.append((method, url))
        return {'chart': {'result': [{'meta': {'symbol': 'AAPL', 'currency': 'USD'}, 'events': self.events}], 'error': None}}

    def actions(self):
        return TensorActions(self.store, self.trading, self.providers, transport=self.transport)

    def probe(self, clock=None, sym='AAPL'):
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO a_strategy_action_probes VALUES(?,?,'ok',NULL,'synthetic-provenance')", (sym, (clock or self.ex).isoformat()))

    def rows(self, name):
        with self.store.connect() as con:
            return [dict(row) for row in con.execute('SELECT * FROM ' + name)]

    def account(self, clock=None):
        with self.store.connect() as con:
            return self.trading._account(con, self.trading._book(con, self.book), clock or self.ex)[0]

    def cash(self, clock=None):
        with self.store.transaction() as con:
            return self.trading.strategy_cash(con, self.book, clock or self.ex)

    def event(self, actions, kind='split', **kwargs):
        default = {'kind': kind, 'date': '2026-07-06'}
        default.update({'numerator': 2, 'denominator': 1} if kind == 'split' else {'amount': '.25'})
        default.update(kwargs)
        return actions.apply_event(self.book, 'AAPL', default, 'Synthetic dated issuer event', self.ex)

    def test_forward_split_preserves_basis_wealth_and_actual_entry_anchor(self):
        self.buy()
        old = self.order('old-exit', 5, self.entry, side='sell')
        with self.store.transaction() as con:
            con.execute('CREATE TABLE a_tensor_position_state(installation_id TEXT,symbol TEXT,entry_fill_id TEXT,entry_time TEXT,entry_open_ms INTEGER,status TEXT)')
            fill = self.rows('p_fills')[0]
            con.execute('INSERT INTO a_tensor_position_state VALUES(?,?,?,?,?,?)', (self.installation, 'AAPL', fill['id'], fill['timestamp'], 1783000800000, 'held'))
        anchor = self.rows('a_tensor_position_state')
        actions = self.actions()
        split = self.event(actions)
        self.assertEqual(split['status'], 'applied')
        held = self.rows('p_positions')[0]
        self.assertEqual((held['quantity'], held['cost_cents']), ('20', 100000))
        self.assertEqual(self.rows('a_tensor_position_state'), anchor)
        self.assertEqual(next(row for row in self.rows('p_intents') if row['id'] == old['id'])['status'], 'cancelled')
        # A pre-action quote is valued in new units, never overwritten or used
        # as a post-action execution quote. Wealth does not double.
        self.assertEqual(self.account()['equity'], 10000)
        self.assertEqual(self.rows('quotes')[0]['price'], '100')
        self.quote(50, self.ex)
        self.probe()
        self.assertEqual(self.account()['equity'], 10000)
        self.order('actual-new-unit-exit', 20, self.ex, side='sell')
        self.assertEqual(self.trading.process(self.providers, self.ex)['fills'], 1)
        self.assertEqual(self.trading.reconcile(self.providers, self.ex)['errors'], [])
        self.assertEqual(self.rows('p_books')[1]['realized_cents'], 0)
        self.assertEqual(self.cash()['cash_cents'], 1000000)
        self.assertEqual(self.cash()['unsettled_cents'], 100000)
        self.assertEqual(self.event(actions)['id'], split['id'])
        self.assertEqual(len(self.rows('a_strategy_actions')), 1)

    def test_dividend_receivable_is_overnight_income_and_not_spendable(self):
        self.buy()
        actions = self.actions()
        dividend = self.event(actions, 'dividend')
        self.quote('99.75', self.ex)
        self.probe()
        self.assertEqual(self.account()['dividend_receivable'], 2.5)
        self.assertEqual(self.account()['equity'], 10000)
        self.assertEqual(self.cash()['cash_cents'], 900000)
        self.assertEqual(self.cash()['available_cents'], 900000)
        paid = datetime(2026, 7, 15, 17, tzinfo=UTC)
        receipt = actions.record_verified_payment(dividend['id'], paid, 'Synthetic independently verified issuer payment', 'a' * 64, clock=paid)
        self.assertEqual(receipt['amount_cents'], 250)
        self.assertEqual(self.cash(paid)['cash_cents'], 900250)
        self.assertEqual(self.account(paid)['dividend_receivable'], 0)
        self.assertEqual(self.account(paid)['equity'], 10000)
        actions.record_verified_payment(dividend['id'], paid, 'Synthetic independently verified issuer payment', 'a' * 64, clock=paid)
        self.assertEqual(self.cash(paid)['cash_cents'], 900250)
        self.assertEqual(self.trading.reconcile(self.providers, paid)['errors'], [])
        with self.assertRaises(DeskError):
            actions.record_verified_payment(dividend['id'], paid, 'Different payment', 'b' * 64, clock=paid)

    def test_late_dividend_entitlement_excludes_ex_date_additional_buys(self):
        self.buy()
        self.buy(5, self.ex, price='99.75', key='ex-date-buy')
        actions = self.actions()
        self.event(actions, 'dividend')
        receivable = self.rows('a_strategy_receivables')[0]
        self.assertEqual((receivable['entitled_quantity'], receivable['amount_cents']), ('10', 250))
        self.assertEqual(self.trading.reconcile(self.providers, self.ex)['errors'], [])

    def test_first_ex_date_buyer_has_no_fabricated_dividend_entitlement(self):
        self.buy(10, self.ex, price='99.75')
        action = self.event(self.actions(), 'dividend')
        self.assertEqual(action['status'], 'not_entitled')
        self.assertEqual(self.rows('a_strategy_receivables'), [])

    def test_dividend_remains_due_after_entitled_stock_is_sold(self):
        self.buy()
        self.quote('99.75', self.ex)
        self.order('exit', 10, self.ex, side='sell')
        self.trading.process(self.providers, self.ex)
        self.event(self.actions(), 'dividend')
        self.probe()
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '0')
        self.assertEqual(self.account()['equity'], 10000)
        self.assertEqual(self.account()['dividend_receivable'], 2.5)
        self.assertEqual(self.trading.reconcile(self.providers, self.ex)['errors'], [])

    def test_fractional_reverse_split_is_marked_not_paid_and_blocks_new_risk(self):
        self.buy(7)
        actions = self.actions()
        split = self.event(actions, numerator=1, denominator=2)
        self.quote(200, self.ex)
        self.probe()
        self.probe(sym='MSFT')
        self.quote(100, self.ex, sym='MSFT')
        position, claim = self.rows('p_positions')[0], self.rows('a_strategy_fractional_claims')[0]
        self.assertEqual((position['quantity'], position['cost_cents']), ('3', 60000))
        self.assertEqual((claim['quantity'], claim['basis_cents'], claim['status']), ('0.5', 10000, 'awaiting_cash_in_lieu'))
        self.assertEqual(self.account()['fractional_claim_market_value'], 100)
        self.assertEqual(self.account()['equity'], 10000)
        self.assertGreater(self.account()['missing_marks'], 0)
        with self.store.connect() as con:
            book = {**dict(self.trading._book(con, self.book)), 'account': self.account()}
            self.assertIsNone(self.trading._performance(con, [book])[0]['net_profit'])
        with self.assertRaises(DeskError):
            self.order('blocked-entry', 1, self.ex, sym='MSFT')
        self.order('whole-share-exit', 3, self.ex, side='sell')
        self.assertEqual(self.trading.process(self.providers, self.ex)['fills'], 1)
        self.assertEqual(self.trading.reconcile(self.providers, self.ex)['errors'], [])
        paid = self.ex + timedelta(days=1)
        actions.record_verified_payment(split['id'], paid, 'Synthetic verified cash-in-lieu activity', 'c' * 64, amount_cents=11000, clock=paid)
        self.assertEqual(self.cash(paid)['cash_cents'], 1001000)
        self.assertEqual(self.account(paid)['fractional_claim_market_value'], 0)
        self.assertEqual(self.rows('p_positions')[0]['realized_cents'], 1000)
        self.assertEqual(self.trading.reconcile(self.providers, paid)['errors'], [])

    def test_split_discovered_after_new_unit_fills_withholds_unrepairable_history(self):
        self.buy()
        self.quote(50, self.ex)
        self.order('unadjusted-early-exit', 5, self.ex, side='sell')
        self.trading.process(self.providers, self.ex)
        actions = self.actions()
        split = self.event(actions)
        self.assertEqual(split['status'], 'late_requires_review')
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '5')
        self.probe()
        self.assertGreater(self.account()['missing_marks'], 0)
        self.assertIn('AAPL', self.account()['corporate_action_coverage']['unresolved_symbols'])
        with self.assertRaises(DeskError):
            self.order('ambiguous-units-exit', 5, self.ex, side='sell')
        self.assertEqual(len(self.rows('p_fills')), 2)

    def test_conflicting_revision_preserves_original_receivable_and_requires_review(self):
        self.buy()
        actions = self.actions()
        original = self.event(actions, 'dividend')
        conflict = self.event(actions, 'dividend', amount='.30')
        self.assertEqual(conflict['status'], 'conflict')
        self.assertEqual(self.rows('a_strategy_receivables')[0]['amount_cents'], 250)
        self.assertEqual(len(self.rows('a_strategy_action_revisions')), 1)
        self.assertEqual(self.rows('a_strategy_actions')[0]['definition'], original['definition'])
        self.assertTrue(self.account()['corporate_action_coverage']['entry_blocked'])

    def test_equivalent_definition_is_idempotent_and_future_dates_are_not_applied(self):
        self.buy()
        actions = self.actions()
        first = self.event(actions, 'dividend', amount='.2500')
        second = self.event(actions, 'dividend', amount='.25')
        self.assertEqual(first['id'], second['id'])
        self.assertTrue(second['idempotent'])
        future = actions.apply_event(self.book, 'AAPL', {'kind': 'split', 'date': '2026-07-07', 'numerator': 2, 'denominator': 1}, 'Synthetic future dated issuer event', self.ex)
        self.assertEqual(future['status'], 'future_not_applied')
        self.assertEqual(len(self.rows('a_strategy_actions')), 1)

    def test_observed_split_before_same_day_dividend_uses_new_share_units(self):
        self.buy()
        actions = self.actions()
        self.event(actions)
        self.event(actions, 'dividend')
        self.assertEqual(self.rows('a_strategy_receivables')[0]['amount_cents'], 500)
        self.quote('49.75', self.ex)
        self.probe()
        self.assertEqual(self.account()['equity'], 10000)
        self.assertEqual(self.trading.reconcile(self.providers, self.ex)['errors'], [])

    def test_action_fence_failure_rolls_back_quantity_cash_and_receipts(self):
        self.buy()
        actions = self.actions()
        def expired(con):
            raise DeskError('Worker lease was superseded')
        with self.assertRaises(DeskError):
            actions.apply_event(self.book, 'AAPL', {'kind': 'split', 'date': '2026-07-06', 'numerator': 2, 'denominator': 1}, 'Synthetic source', self.ex, fence=expired)
        self.assertEqual(self.rows('a_strategy_actions'), [])
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '10')
        self.assertEqual(self.cash()['cash_cents'], 900000)

    def test_bounded_preflight_enables_first_entry_without_inventing_events(self):
        actions = self.actions()
        self.quote(100, self.ex)
        with self.assertRaises(DeskError):
            self.order('entry', 10, self.ex)
        result = actions.probe_symbols(['AAPL'], self.ex)
        self.assertEqual(result['checked'], 1)
        self.assertEqual(result['actions'], 0)
        self.assertEqual(result['errors'], [])
        self.assertEqual(self.requests[0][0], 'GET')
        self.assertIn('events=div%2Csplits', self.requests[0][1])
        self.order('entry', 10, self.ex)
        self.assertEqual(self.trading.process(self.providers, self.ex)['fills'], 1)
        self.assertEqual(self.rows('a_strategy_receivables'), [])
        export = json.loads(json.dumps(self.store.export({})))
        record = export['tables']['a_strategy_action_receipts'][0]
        payload = record['data']
        raw = base64.b64decode(payload['data'], validate=True)
        self.assertEqual(len(raw), payload['bytes'])
        self.assertEqual(json.loads(gzip.decompress(raw))['chart']['result'][0]['meta']['symbol'], 'AAPL')

    def test_source_outage_withholds_execution_without_mutating_inventory(self):
        self.buy()
        actions = self.actions()
        def unavailable(*args):
            raise RuntimeError('Synthetic provider outage')
        actions.transport = unavailable
        result = actions.run_once(self.ex)
        self.assertEqual(result['checked'], 0)
        self.assertTrue(result['errors'])
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '10')
        self.assertEqual(self.cash()['cash_cents'], 900000)
        self.assertEqual(self.rows('a_strategy_actions'), [])
        self.quote(100, self.ex)
        with self.assertRaises(DeskError):
            self.order('unverified-exit', 10, self.ex, side='sell')

    def test_independent_reconciliation_detects_corrupted_split_or_dividend(self):
        self.buy()
        actions = self.actions()
        self.event(actions)
        self.event(actions, 'dividend')
        self.quote('49.75', self.ex)
        self.probe()
        self.assertEqual(self.trading.reconcile(self.providers, self.ex)['errors'], [])
        with self.store.transaction() as con:
            con.execute('UPDATE a_strategy_receivables SET amount_cents=amount_cents+1')
        self.assertTrue(self.trading.reconcile(self.providers, self.ex)['errors'])

    def payment_fixture(self, **changes):
        record = {'id': 'fixture-declared-payment', 'symbol': 'AAPL', 'ex_date': '2026-07-06',
                  'payable_date': '2026-07-15', 'process_date': '2026-07-15', 'rate': .25, 'foreign': False}
        record.update(changes)
        return {'corporate_actions': {'cash_dividends': [record]}, 'next_page_token': None}

    def payment_actions(self, response=None, transport=None):
        credentials = Path(self.temporary.name) / 'fixture-read-credentials.json'
        credentials.write_text(json.dumps({'key': 'synthetic-read-key', 'secret': 'synthetic-read-secret'}))
        credentials.chmod(0o600)
        self.payment_requests = []
        def payment_read(method, url, payload, headers):
            self.assertEqual(method, 'GET')
            self.assertTrue(url.startswith('https://data.alpaca.markets/v1/corporate-actions?'))
            self.assertIsNone(payload)
            self.assertEqual(headers['APCA-API-KEY-ID'], 'synthetic-read-key')
            self.payment_requests.append(url)
            return response or self.payment_fixture()
        actions = TensorActions(self.store, self.trading, self.providers, transport=self.transport,
                                payment_transport=transport or payment_read, credentials_file=str(credentials))
        self.events = {'dividends': {'event': {'date': int(self.ex.timestamp()), 'amount': .25}}}
        self.payment_initial_result = actions.run_once(self.ex)
        self.assertEqual(self.payment_initial_result['actions'], 1)
        return actions

    def test_automatic_declared_paydate_simulation_retains_future_cash_and_credits_once(self):
        self.buy()
        actions = self.payment_actions()
        self.assertEqual(self.cash()['cash_cents'], 900000)
        self.assertEqual(self.rows('a_strategy_receivables')[0]['status'], 'receivable')
        before = datetime(2026, 7, 15, 13, 29, 59, tzinfo=UTC)
        self.assertEqual(actions.settle_declared_dividends(before)['payments'], 0)
        self.assertEqual(self.cash(before)['cash_cents'], 900000)
        after = before + timedelta(minutes=6)
        result = actions.settle_declared_dividends(after)
        self.assertEqual((result['payments'], result['errors']), (1, []))
        self.assertEqual(self.cash(after)['cash_cents'], 900250)
        receipt = self.rows('a_strategy_action_payments')[0]
        self.assertEqual(receipt['payment_at'], '2026-07-15T13:30:00+00:00')
        self.assertEqual(receipt['observed_at'], after.isoformat())
        self.assertIn('local-paper USD-listing simulation', receipt['source'])
        self.assertEqual(actions.settle_declared_dividends(after)['payments'], 0)
        self.assertEqual(self.trading.reconcile(self.providers, after)['errors'], [])
        exported = json.dumps(self.store.export({}))
        self.assertNotIn('synthetic-read-key', exported)
        self.assertNotIn('synthetic-read-secret', exported)
        proof = next(row for row in self.rows('a_strategy_action_receipts') if row['id'] == receipt['evidence_sha256'])
        evidence = json.loads(gzip.decompress(proof['data']))
        self.assertTrue(evidence['pagination_complete'])
        self.assertIn('absent', evidence['source_currency'])

    def test_declared_process_date_later_than_payable_date_defers_simulated_credit(self):
        self.buy()
        actions = self.payment_actions(self.payment_fixture(process_date='2026-07-16'))
        earlier = datetime(2026, 7, 15, 15, tzinfo=UTC)
        self.assertEqual(actions.settle_declared_dividends(earlier)['payments'], 0)
        self.assertEqual(self.cash(earlier)['cash_cents'], 900000)
        later = datetime(2026, 7, 16, 14, tzinfo=UTC)
        self.assertEqual(actions.settle_declared_dividends(later)['payments'], 1)
        self.assertEqual(self.rows('a_strategy_action_payments')[0]['payment_at'], '2026-07-16T13:30:00+00:00')

    def test_conflicting_declared_rate_withholds_cash_and_preserves_receivable(self):
        self.buy()
        actions = self.payment_actions(self.payment_fixture(rate=.30))
        after = datetime(2026, 7, 16, 14, tzinfo=UTC)
        result = actions.settle_declared_dividends(after)
        self.assertEqual(result['payments'], 0)
        self.assertEqual(self.cash(after)['cash_cents'], 900000)
        self.assertEqual(self.rows('a_strategy_receivables')[0]['amount_cents'], 250)
        self.assertEqual(self.rows('a_strategy_actions')[0]['status'], 'conflict')
        self.assertTrue(self.account(after)['corporate_action_coverage']['entry_blocked'])

    def test_declared_payments_require_complete_bounded_pagination(self):
        self.buy()
        requests = []
        def paged(method, url, payload, headers):
            self.assertEqual(method, 'GET')
            requests.append(parse_qs(urlparse(url).query))
            if 'page_token' not in requests[-1]:
                return {'corporate_actions': {'cash_dividends': []}, 'next_page_token': 'fixture-next'}
            return self.payment_fixture()
        actions = self.payment_actions(transport=paged)
        after = datetime(2026, 7, 16, 14, tzinfo=UTC)
        self.assertEqual(actions.settle_declared_dividends(after)['payments'], 1)
        receipt = self.rows('a_strategy_action_payments')[0]
        proof = next(row for row in self.rows('a_strategy_action_receipts') if row['id'] == receipt['evidence_sha256'])
        self.assertEqual(len(json.loads(gzip.decompress(proof['data']))['pages']), 2)
        self.assertTrue(any(request.get('page_token') == ['fixture-next'] for request in requests))

    def test_cyclic_or_incomplete_payment_source_never_credits_cash(self):
        self.buy()
        response = self.payment_fixture()
        response['next_page_token'] = 'repeat'
        actions = self.payment_actions(response)
        after = datetime(2026, 7, 16, 14, tzinfo=UTC)
        result = actions.settle_declared_dividends(after)
        self.assertEqual(result['payments'], 0)
        self.assertTrue(result['errors'])
        self.assertEqual(self.cash(after)['cash_cents'], 900000)
        self.assertEqual(self.rows('a_strategy_action_payments'), [])
        self.assertLessEqual(len(self.payment_requests), 4)

    def test_foreign_or_nonusd_declared_record_cannot_fund_the_local_usd_book(self):
        self.buy()
        actions = self.payment_actions(self.payment_fixture(currency='EUR'))
        after = datetime(2026, 7, 16, 14, tzinfo=UTC)
        self.assertTrue(self.payment_initial_result['declared_payments']['errors'])
        result = actions.settle_declared_dividends(after)
        self.assertEqual((result['pending'], result['eligible_pending'], result['payments']), (1, 0, 0))
        self.assertEqual(self.cash(after)['cash_cents'], 900000)
        self.assertEqual(self.rows('a_strategy_action_payments'), [])
        self.assertEqual(self.rows('a_strategy_actions')[0]['status'], 'conflict')
        self.assertIn('AAPL', self.account(after)['corporate_action_coverage']['unresolved_symbols'])

    def test_action_success_cache_and_failure_retry_are_bounded(self):
        actions = self.actions()
        first = actions.probe_symbols(['AAPL'], self.ex)
        again = actions.probe_symbols(['AAPL'], self.ex + timedelta(seconds=5))
        self.assertEqual((first['checked'], again['checked'], again['cached']), (1, 0, 1))
        self.assertEqual(len(self.requests), 1)
        def failed(*args):
            self.requests.append(('GET', 'synthetic-failed-read'))
            raise RuntimeError('Synthetic outage')
        actions.transport = failed
        failed_at = self.ex + timedelta(seconds=301)
        self.assertTrue(actions.probe_symbols(['AAPL'], failed_at)['errors'])
        self.assertEqual(actions.probe_symbols(['AAPL'], failed_at + timedelta(seconds=5))['checked'], 0)
        self.assertEqual(len(self.requests), 2)
        self.assertTrue(actions.probe_symbols(['AAPL'], failed_at + timedelta(seconds=31))['errors'])
        self.assertEqual(len(self.requests), 3)

    def test_false_paid_status_without_a_payment_receipt_fails_reconciliation(self):
        self.buy()
        self.event(self.actions(), 'dividend')
        with self.store.transaction() as con:
            con.execute("UPDATE a_strategy_receivables SET status='paid'")
        self.assertTrue(self.trading.reconcile(self.providers, self.ex)['errors'])

    def test_first_candidate_probe_covers_old_seed_basis_and_extends_a_cached_short_read(self):
        actions = self.actions()
        self.assertEqual(actions.probe_symbols(['AAPL'], self.ex)['checked'], 1)
        seed_end = datetime(2026, 5, 1, 20, tzinfo=UTC)
        manifest = Path(self.temporary.name) / 'fixture-native-endpoint.json'
        manifest.write_text(json.dumps({'sources': [{'groups': [{'symbol': 'AAPL', 'interval': '1d', 'last_completed_at': int(seed_end.timestamp())}]}]}))
        config = json.dumps({'frame': '1d', 'seed_manifest_file': str(manifest), 'seed_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()})
        origin = int(self.ex.timestamp() * 1000)
        with self.store.transaction() as con:
            con.executescript('CREATE TABLE a_tensor_installations(id TEXT,book_id TEXT,enabled INTEGER,config TEXT); CREATE TABLE a_tensor_cycles(frame TEXT,origin_ms INTEGER,expires_ms INTEGER); CREATE TABLE a_tensor_candidates(installation_id TEXT,origin_ms INTEGER,symbol TEXT,data TEXT);')
            con.execute('INSERT INTO a_tensor_installations VALUES(?,?,1,?)', (self.installation, self.book, config))
            con.execute('INSERT INTO a_tensor_cycles VALUES(?,?,?)', ('1d', origin, origin + 300000))
            con.execute('INSERT INTO a_tensor_candidates VALUES(?,?,?,?)', (self.installation, origin, 'AAPL', '{"priority":5}'))
        split_day = datetime(2026, 6, 1, 13, 30, tzinfo=UTC)
        self.events = {'splits': {'old-split': {'date': int(split_day.timestamp()), 'numerator': 2, 'denominator': 1}}}
        result = actions.run_once(self.ex + timedelta(seconds=5))
        self.assertEqual((result['checked'], result['errors']), (1, []))
        query = parse_qs(urlparse(self.requests[-1][1]).query)
        self.assertEqual(int(query['period1'][0]), int((seed_end - timedelta(days=7)).timestamp()))
        self.assertEqual(self.rows('a_strategy_actions')[0]['status'], 'not_entitled')
        self.assertEqual(self.rows('a_strategy_actions')[0]['effective_at'], split_day.isoformat())
        self.assertEqual(self.rows('p_fills'), [])

    def test_no_payment_credentials_retains_verified_exdate_receivable(self):
        self.buy()
        actions = self.actions()
        self.events = {'dividends': {'event': {'date': int(self.ex.timestamp()), 'amount': .25}}}
        self.assertEqual(actions.run_once(self.ex)['actions'], 1)
        actions.credentials_file = None
        after = datetime(2026, 7, 16, 14, tzinfo=UTC)
        result = actions.settle_declared_dividends(after)
        self.assertEqual((result['configured'], result['pending'], result['payments']), (False, 1, 0))
        self.assertEqual(self.cash(after)['cash_cents'], 900000)
        self.assertEqual(self.rows('a_strategy_action_payments'), [])

    def test_payment_pagination_hard_cap_withholds_even_a_matching_first_page(self):
        self.buy()
        requests = []
        def never_finishes(method, url, payload, headers):
            requests.append(url)
            response = self.payment_fixture()
            response['next_page_token'] = 'unending-' + str(len(requests))
            return response
        actions = self.payment_actions(transport=never_finishes)
        self.assertEqual(len(requests), 8)
        after = datetime(2026, 7, 16, 14, tzinfo=UTC)
        result = actions.settle_declared_dividends(after)
        self.assertTrue(result['errors'])
        self.assertEqual(len(requests), 16)
        self.assertEqual(result['payments'], 0)
        self.assertEqual(self.cash(after)['cash_cents'], 900000)

if __name__ == '__main__':
    unittest.main()
