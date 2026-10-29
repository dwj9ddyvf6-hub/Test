"""Dedicated installed-strategy authority, atomic reservations and T+1 cash."""
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from backend.providers import exchange_calendar
from backend.store import DeskError, Store
from backend.trading import TradingDesk

UTC = timezone.utc


class FixtureProviders:
    broker = None

    def calendar(self, clock=None):
        return exchange_calendar(clock)


class TensorStrategyTradingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'desk.sqlite'
        self.store = Store(self.path)
        self.trading = TradingDesk(self.store)
        self.book_id = self.trading.create_book({'name': 'Tensor hourly fixture', 'kind': 'forward', 'broker': 'local'})['id']
        self.installation = 'tensor-hourly-fixture-v1'
        self.clock = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)
        self.providers = FixtureProviders()

    def tearDown(self):
        self.temp.cleanup()

    def own(self, amount=1000):
        self.trading.fund_book(self.book_id, amount, 'fixture-funding')
        return self.trading.claim_strategy_book(self.book_id, self.installation)

    def quote(self, clock=None, price='10', symbol='AAPL'):
        # Explicit deterministic synthetic quotes, with their actual fixture
        # clock; no data-provider call or production database is involved.
        with self.store.transaction() as con:
            con.execute('INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)', (symbol, str(price), (clock or self.clock).isoformat(), 'Synthetic execution quote fixture'))

    def payload(self, key='entry', side='buy', qty=10, symbol='AAPL', **kwargs):
        return {'book_id': self.book_id, 'symbol': symbol, 'side': side, 'quantity': qty, 'client_id': key, 'order_type': 'market', 'time_in_force': 'gtc', **kwargs}

    def submit(self, **kwargs):
        return self.trading.submit_strategy_intent(self.payload(**kwargs), self.installation, clock=self.clock)

    def cash(self, clock=None):
        with self.store.transaction() as con:
            return self.trading.strategy_cash(con, self.book_id, clock or self.clock)

    def rows(self, table):
        with self.store.connect() as con:
            return [dict(row) for row in con.execute('SELECT * FROM ' + table)]

    def test_claim_is_durable_exclusive_empty_local_and_funding_is_independent(self):
        ownership = self.own()
        self.assertEqual(self.trading.claim_strategy_book(self.book_id, self.installation), ownership)
        self.assertEqual(TradingDesk(Store(self.path)).claim_strategy_book(self.book_id, self.installation), ownership)
        another = self.trading.create_book({'name': 'Other fixture', 'kind': 'forward', 'broker': 'local'})['id']
        broker = self.trading.create_book({'name': 'Broker fixture', 'kind': 'forward', 'broker': 'alpaca'})['id']
        for book, identity in ((self.book_id, 'foreign'), (another, self.installation), (broker, 'connected')):
            with self.subTest(book=book, identity=identity), self.assertRaises(DeskError):
                self.trading.claim_strategy_book(book, identity)
        self.trading.fund_book(self.book_id, 20, 'additional-funding')
        self.assertEqual(self.cash()['available_cents'], 102000)
        snapshot = self.trading.snapshot()
        self.assertEqual(snapshot['strategy_count'], 1)
        self.assertTrue(snapshot['strategy_extension']['enabled'])
        self.assertEqual(next(book for book in snapshot['books'] if book['id'] == 'main')['account']['cash'], 0)
        for bad in (None, '', 'bad\nidentity'):
            with self.assertRaises(DeskError):
                self.trading.claim_strategy_book(another, bad)
        with self.store.connect() as con, self.assertRaises(DeskError):
            self.trading.claim_strategy_book(another, 'other-valid', con=con)

    def test_pending_or_previously_traded_book_cannot_be_claimed(self):
        self.trading.fund_book(self.book_id, 1000, 'fixture-funding')
        self.quote()
        payload = self.payload(qty=2)
        # Preserve operator API clock behavior while this synthetic timestamp
        # is exercised through its internal unchanged operator boundary.
        with self.store.transaction() as con:
            order = self.trading._submit_normalized_intent(con, self.trading._normalize_intent(payload), clock=self.clock)
        with self.assertRaises(DeskError):
            self.trading.claim_strategy_book(self.book_id, self.installation)
        self.trading.process(self.providers, self.clock)
        self.assertEqual(self.rows('p_fills')[0]['intent_id'], order['id'])
        with self.assertRaises(DeskError):
            self.trading.claim_strategy_book(self.book_id, self.installation)

    def test_decision_and_intent_share_one_atomic_guarded_transaction(self):
        self.own()
        self.quote()
        with self.store.transaction() as con:
            con.execute('CREATE TABLE fixture_decisions(id TEXT PRIMARY KEY)')
        def stale_guard(con):
            raise DeskError('Installation was disabled while work was running')
        with self.assertRaises(DeskError):
            with self.store.transaction() as con:
                con.execute("INSERT INTO fixture_decisions VALUES('failed')")
                self.trading.submit_strategy_intent(self.payload(), self.installation, con=con, clock=self.clock, transaction_guard=stale_guard)
        self.assertEqual(self.rows('fixture_decisions'), [])
        self.assertEqual(self.rows('p_intents'), [])
        guards = []
        with self.store.transaction() as con:
            con.execute("INSERT INTO fixture_decisions VALUES('committed')")
            receipt = self.trading.submit_strategy_intent(self.payload(), self.installation, con=con, clock=self.clock, transaction_guard=lambda writer: guards.append(writer is con))
        self.assertEqual(guards, [True])
        self.assertEqual(self.rows('fixture_decisions'), [{'id': 'committed'}])
        self.assertEqual(receipt['source'], 'strategy')
        self.assertEqual(self.submit()['id'], receipt['id'])
        self.assertEqual(len(self.rows('p_intents')), 1)
        authorization = [row for row in self.rows('events') if row['event_type'] == 'strategy_intent_authorized']
        self.assertEqual(len(authorization), 1)
        self.assertEqual(authorization[0]['actor'], 'strategy')
        self.assertEqual(json.loads(authorization[0]['payload'])['installation_id'], self.installation)
        with self.assertRaises(DeskError):
            self.submit(qty=11)
        with self.store.connect() as con, self.assertRaises(DeskError):
            self.trading.submit_strategy_intent(self.payload(key='no-transaction'), self.installation, con=con, clock=self.clock)

    def test_manual_entry_and_foreign_authority_isolation_with_emergency_sell(self):
        self.own()
        self.quote()
        for identity in ('foreign', None):
            with self.assertRaises(DeskError):
                self.trading.submit_strategy_intent(self.payload(), identity, clock=self.clock)
        with self.assertRaises(DeskError):
            self.trading.submit_intent(self.payload(key='operator-entry'))
        with self.assertRaises(DeskError):
            self.trading.submit_intent(self.payload(key='operator-short', side='sell'))
        with self.assertRaises(DeskError):
            self.submit(qty='0.5')
        self.submit(qty=10)
        self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 1)
        self.trading.set_book(self.book_id, {'halted': True, 'allow_short': True})
        with self.assertRaises(DeskError):
            self.submit(key='new-entry', qty=1)
        with self.assertRaises(DeskError):
            self.submit(key='short', side='sell', qty=11)
        # The public operator API uses the actual current clock, so patch only
        # that parsing helper for this deterministic emergency exit fixture.
        with patch('backend.trading.clock_time', return_value=self.clock):
            emergency = self.trading.submit_intent(self.payload(key='emergency', side='sell', qty=10))
        self.assertEqual(emergency['source'], 'operator')
        self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 1)
        with patch('backend.trading.clock_time', return_value=self.clock):
            self.assertEqual(self.trading.submit_intent(self.payload(key='emergency', side='sell', qty=10))['id'], emergency['id'])
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '0')
        self.assertEqual(self.cash()['unsettled_cents'], 10000)

    def test_concurrent_installation_reservations_cannot_spend_same_cash(self):
        self.own()
        self.quote()
        def reserve(key):
            try:
                return self.submit(key=key, qty=75)['id']
            except DeskError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, ['one', 'two']))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(self.cash()['available_cents'], 25000)
        self.assertEqual(self.cash()['reserved_cents'], 75000)
        original = next(result for result in results if result)
        self.trading.cancel_intent(original)
        self.assertEqual(self.cash()['available_cents'], 100000)

    def test_fill_rounding_fee_and_slippage_are_reserved_before_admission(self):
        self.own(amount=100)
        self.trading.set_book(self.book_id, {'slippage_bps': 10, 'fees_per_order': '.03'})
        self.quote()
        with self.assertRaises(DeskError):
            self.submit(qty=10)
        accepted = self.submit(qty=9)
        self.assertEqual(accepted['reserved'], 90.12)
        self.assertEqual(self.cash()['available_cents'], 988)
        self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 1)
        self.assertEqual(self.rows('p_fills')[0]['notional_cents'], 9009)
        self.assertEqual(self.rows('p_fills')[0]['fee_cents'], 3)
        self.assertEqual(self.cash()['cash_cents'], 988)

    def test_price_gap_cannot_exceed_frozen_strategy_debit_budget(self):
        self.own(amount=100000)
        self.trading.set_book(self.book_id, {'slippage_bps': 10})
        self.quote(price='50')
        intent = self.submit(qty=199, max_debit_cents=1000000)
        limits = self.rows('a_strategy_intent_limits')
        self.assertEqual(limits[0]['intent_id'], intent['id'])
        self.assertEqual(limits[0]['max_debit_cents'], 1000000)
        self.quote(self.clock + timedelta(seconds=1), price='100')
        result = self.trading.process(self.providers, self.clock + timedelta(seconds=1))
        self.assertEqual(result['fills'], 0)
        self.assertTrue(result['errors'])
        self.assertIn('debit budget', result['errors'][0]['detail'])
        self.assertEqual(self.cash()['cash_cents'], 10000000)
        self.assertEqual(self.rows('p_fills'), [])
        self.assertEqual(self.rows('p_positions'), [])
        self.assertEqual(self.rows('p_intents')[0]['status'], 'blocked')
        with self.assertRaises(DeskError):
            self.submit(qty=199, max_debit_cents=2000000)
        with self.assertRaises(DeskError):
            self.trading.submit_intent(self.payload(key='operator-budget', max_debit_cents=1000000))

    def test_partial_gap_budget_includes_prior_debits_and_actual_fee(self):
        self.own(amount=1000)
        self.trading.set_book(self.book_id, {'slippage_bps': 10, 'fees_per_order': '.25'})
        self.quote()
        self.submit(qty=10, max_fill_quantity=2, max_debit_cents=11000)
        self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 1)
        self.assertEqual(self.rows('p_fills')[0]['notional_cents'], 2002)
        self.assertEqual(self.rows('p_fills')[0]['fee_cents'], 25)
        later = self.clock + timedelta(seconds=1)
        self.quote(later, price='30')
        self.assertEqual(self.trading.process(self.providers, later)['fills'], 1)
        before = self.cash(later)['cash_cents']
        result = self.trading.process(self.providers, later)
        self.assertEqual(result['fills'], 0)
        self.assertTrue(result['errors'])
        self.assertEqual(len(self.rows('p_fills')), 2)
        self.assertEqual(self.cash(later)['cash_cents'], before)
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '4')
        order = self.rows('p_intents')[0]
        self.assertEqual(order['filled_notional_cents'], 8008)
        self.assertEqual(order['fees_cents'], 25)
        self.assertEqual(order['status'], 'blocked')
        self.assertEqual(TradingDesk(Store(self.path)).snapshot()['strategy_intent_limits'][0]['max_debit_cents'], 11000)

    def test_strategy_budget_admission_is_integral_bounded_and_not_undersized(self):
        self.own()
        self.quote()
        for bad in (True, 0, -1, 10000.0, '10000', 10 ** 30):
            with self.subTest(budget=bad), self.assertRaises(DeskError):
                self.submit(max_debit_cents=bad)
        with self.assertRaises(DeskError):
            self.submit(max_debit_cents=9999)
        self.assertEqual(self.rows('p_intents'), [])
        self.assertEqual(self.rows('a_strategy_intent_limits'), [])

    def test_installed_strategy_keeps_book_caps_and_whole_share_constraints(self):
        self.own()
        self.quote()
        self.quote(symbol='MSFT')
        self.trading.set_book(self.book_id, {'gross_exposure_cap': 100, 'symbol_exposure_cap': 75, 'allow_short': True})
        with self.assertRaises(DeskError):
            self.submit(qty=8)
        self.submit(qty=7)
        with self.assertRaises(DeskError):
            self.submit(key='aggregate-over-cap', qty=4, symbol='MSFT')
        with self.assertRaises(DeskError):
            self.submit(key='fractional-fill', qty=1, symbol='MSFT', max_fill_quantity='.5')
        self.assertEqual(len(self.rows('p_intents')), 1)
        self.trading.process(self.providers, self.clock)
        with self.assertRaises(DeskError):
            self.submit(key='short-even-when-enabled', side='sell', qty=8)
        with self.assertRaises(DeskError):
            self.trading.submit_intent(self.payload(key='fractional-manual-exit', side='sell', qty='.5'))

    def test_partial_fills_settle_each_actual_net_sale_and_survive_restart(self):
        self.own(amount=100)
        self.trading.set_book(self.book_id, {'slippage_bps': 10, 'fees_per_order': '.03'})
        self.quote()
        self.submit(qty=5, max_fill_quantity=2)
        for _ in range(3):
            self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 1)
        self.assertEqual(self.cash()['cash_cents'], 4992)
        self.submit(key='exit', side='sell', qty=2, max_fill_quantity=1)
        for _ in range(2):
            self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 1)
        settlements = self.rows('a_strategy_settlements')
        self.assertEqual(sorted(row['amount_cents'] for row in settlements), [996, 999])
        self.assertEqual({row['release_at'] for row in settlements}, {'2026-07-06T13:30:00+00:00'})
        self.assertEqual(self.cash()['cash_cents'], 6987)
        self.assertEqual(self.cash()['unsettled_cents'], 1995)
        self.assertEqual(self.cash()['available_cents'], 4992)
        self.trading = TradingDesk(Store(self.path))
        self.assertEqual(self.cash()['unsettled_cents'], 1995)
        result = self.trading.reconcile(self.providers, self.clock)
        self.assertEqual(result['errors'], [])
        self.assertEqual(self.trading.process(self.providers, self.clock)['fills'], 0)
        self.assertEqual(len(self.rows('a_strategy_settlements')), 2)

    def test_t_plus_one_skips_holiday_and_blocks_entry_until_next_open(self):
        self.own(amount=100)
        self.quote()
        self.submit(qty=10)
        self.trading.process(self.providers, self.clock)
        self.submit(key='exit', side='sell', qty=10)
        self.trading.process(self.providers, self.clock)
        before = datetime(2026, 7, 6, 13, 29, 59, tzinfo=UTC)
        self.quote(before)
        with self.assertRaises(DeskError):
            self.trading.submit_strategy_intent(self.payload(key='premature', qty=10), self.installation, clock=before)
        self.assertEqual(self.cash(before)['available_cents'], 0)
        self.assertEqual(self.rows('a_strategy_settlements')[0]['released_at'], None)
        opened = before + timedelta(seconds=1)
        self.quote(opened)
        new = self.trading.submit_strategy_intent(self.payload(key='next-session', qty=10), self.installation, clock=opened)
        self.assertEqual(new['reserved'], 100)
        self.assertEqual(self.rows('a_strategy_settlements')[0]['released_at'], opened.isoformat())
        self.assertEqual(self.trading.process(self.providers, opened)['fills'], 1)
        self.assertEqual(self.cash(opened)['cash_cents'], 0)

    def test_calendar_handles_early_close_holiday_and_dst(self):
        cases = [('2026-11-25T16:00:00+00:00', '2026-11-27T14:30:00+00:00'),
                 ('2026-11-27T17:30:00+00:00', '2026-11-30T14:30:00+00:00'),
                 ('2026-01-16T16:00:00+00:00', '2026-01-20T14:30:00+00:00'),
                 ('2026-03-06T16:00:00+00:00', '2026-03-09T13:30:00+00:00')]
        for trade, settled in cases:
            with self.subTest(trade=trade):
                self.assertEqual(self.trading._strategy_settlement_release_at(datetime.fromisoformat(trade)), settled)
        self.assertTrue(exchange_calendar(datetime.fromisoformat(cases[1][0]))['early_close'])

    def test_missing_settlement_calendar_cannot_half_commit_a_fill(self):
        self.own()
        self.quote()
        self.submit(qty=10)
        self.trading.process(self.providers, self.clock)
        self.submit(key='exit', side='sell', qty=10)
        prior_cash = self.cash()['cash_cents']
        with patch.object(self.trading, '_strategy_settlement_release_at', side_effect=DeskError('Calendar unavailable')):
            result = self.trading.process(self.providers, self.clock)
        self.assertEqual(result['fills'], 0)
        self.assertTrue(result['errors'])
        self.assertEqual(self.cash()['cash_cents'], prior_cash)
        self.assertEqual(self.rows('p_positions')[0]['quantity'], '10')
        self.assertEqual(len(self.rows('p_fills')), 1)
        self.assertEqual(self.rows('a_strategy_settlements'), [])

    def test_settlement_corruption_is_detected_by_independent_reconciliation(self):
        self.own()
        self.quote()
        self.submit(qty=10)
        self.trading.process(self.providers, self.clock)
        self.submit(key='exit', side='sell', qty=10)
        self.trading.process(self.providers, self.clock)
        with self.store.transaction() as con:
            con.execute('UPDATE a_strategy_settlements SET amount_cents=amount_cents+1')
        result = self.trading.reconcile(self.providers, self.clock)
        self.assertTrue(result['errors'])
        with self.store.connect() as con:
            state = json.loads(con.execute("SELECT value FROM p_state WHERE key=?", ('reconcile:' + self.book_id,)).fetchone()[0])
        self.assertEqual(state['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
