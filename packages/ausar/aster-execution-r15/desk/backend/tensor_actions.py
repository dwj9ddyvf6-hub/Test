"""Observed corporate actions for dedicated local paper books.

Yahoo ex-date events establish dividend receivables, never payment dates. A
separate GET-only Alpaca source can verify declared payment dates for local-paper
simulation; this does not attest to actual broker cash receipt. Split quantities
and cost basis are ledger events. Ambiguous late splits fail closed.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import gzip
import hashlib
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from math import gcd
from urllib.parse import quote, urlencode

from .providers import NY, _nyse, utc_clock
from .store import DeskError, cents, checked_cents, now, symbol

UTC = timezone.utc
ACTIVE_SQL = "'queued','open','partially_filled','blocked','submitting','cancel_requested'"


def _dump(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def initialize_action_tables(con):
    con.executescript("""
      CREATE TABLE IF NOT EXISTS a_strategy_actions(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,symbol TEXT NOT NULL,
        kind TEXT NOT NULL,effective_at TEXT NOT NULL,definition TEXT NOT NULL,definition_sha256 TEXT NOT NULL,
        source TEXT NOT NULL,observed_at TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,applied_at TEXT,
        UNIQUE(book_id,symbol,kind,effective_at));
      CREATE TABLE IF NOT EXISTS a_strategy_action_revisions(id TEXT PRIMARY KEY,action_id TEXT NOT NULL,
        definition TEXT NOT NULL,source TEXT NOT NULL,observed_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_receivables(action_id TEXT PRIMARY KEY,book_id TEXT NOT NULL,symbol TEXT NOT NULL,
        entitled_quantity TEXT NOT NULL,amount_cents INTEGER NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_fractional_claims(action_id TEXT PRIMARY KEY,book_id TEXT NOT NULL,symbol TEXT NOT NULL,
        quantity TEXT NOT NULL,basis_cents INTEGER NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_action_payments(action_id TEXT PRIMARY KEY,book_id TEXT NOT NULL,
        amount_cents INTEGER NOT NULL,payment_at TEXT NOT NULL,source TEXT NOT NULL,evidence_sha256 TEXT NOT NULL,observed_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_action_receipts(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,
        observed_at TEXT NOT NULL,source TEXT NOT NULL,data BLOB NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_action_probes(symbol TEXT PRIMARY KEY,checked_at TEXT NOT NULL,
        status TEXT NOT NULL,error TEXT,receipt_id TEXT);
      CREATE TABLE IF NOT EXISTS a_strategy_action_ranges(symbol TEXT PRIMARY KEY,start_at TEXT NOT NULL,
        end_at TEXT NOT NULL,receipt_id TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_payment_probes(symbol TEXT PRIMARY KEY,checked_at TEXT NOT NULL,
        status TEXT NOT NULL,error TEXT,receipt_ids TEXT NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS a_strategy_action_control(id INTEGER PRIMARY KEY CHECK(id=1),enabled INTEGER NOT NULL,cursor INTEGER NOT NULL);
    """)


def split_mark_price(con, book_id, sym, price, quote_at):
    """Value an old source quote in current share units without editing it."""
    value = Decimal(str(price))
    rows = con.execute("SELECT definition FROM a_strategy_actions WHERE book_id=? AND symbol=? AND kind='split' AND applied_at IS NOT NULL AND effective_at>? ORDER BY effective_at,id", (book_id, sym, quote_at))
    for row in rows:
        definition = json.loads(row['definition'])
        value *= Decimal(definition['denominator']) / Decimal(definition['numerator'])
    return value


def _required_probe_at(clock):
    cal = _nyse()
    day = clock.astimezone(NY).date().isoformat()
    session = cal.date_to_session(day, direction='previous')
    if cal.session_open(session).to_pydatetime() > clock:
        session = cal.previous_session(session)
    return cal.session_open(session).to_pydatetime().astimezone(UTC).isoformat()


def action_coverage(con, book_id, clock, target_symbol=None):
    critical = list(con.execute("SELECT symbol,status FROM a_strategy_actions WHERE book_id=? AND status IN ('conflict','late_requires_review')", (book_id,)))
    unresolved = {row['symbol'] for row in critical}
    control = con.execute('SELECT enabled FROM a_strategy_action_control WHERE id=1').fetchone()
    missing = set()
    if control and control['enabled']:
        needed = {row['symbol'] for row in con.execute("SELECT symbol,quantity FROM p_positions WHERE book_id=?", (book_id,)) if Decimal(row['quantity']) != 0}
        needed.update(row['symbol'] for row in con.execute("SELECT symbol FROM a_strategy_fractional_claims WHERE book_id=? AND status='awaiting_cash_in_lieu'", (book_id,)))
        if target_symbol:
            needed.add(target_symbol)
        cutoff = _required_probe_at(clock)
        for sym in needed:
            receipt = con.execute('SELECT * FROM a_strategy_action_probes WHERE symbol=?', (sym,)).fetchone()
            if not receipt or receipt['status'] != 'ok' or receipt['checked_at'] < cutoff or utc_clock(receipt['checked_at']) > clock:
                missing.add(sym)
    fractions = con.execute("SELECT COUNT(*) FROM a_strategy_fractional_claims WHERE book_id=? AND status='awaiting_cash_in_lieu'", (book_id,)).fetchone()[0]
    return {'unresolved_symbols': sorted(unresolved), 'unchecked_symbols': sorted(missing),
            'fractional_claims_pending': fractions, 'entry_blocked': bool(unresolved or missing or fractions),
            'target_blocked': bool(target_symbol and target_symbol in unresolved | missing)}


def action_totals(con, book_id, clock, max_quote_age=300):
    receivable = con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM a_strategy_receivables WHERE book_id=? AND status='receivable'", (book_id,)).fetchone()[0]
    fractional_value, fractional_basis, missing, stale = 0, 0, 0, 0
    for claim in con.execute("SELECT * FROM a_strategy_fractional_claims WHERE book_id=? AND status='awaiting_cash_in_lieu'", (book_id,)):
        fractional_basis += claim['basis_cents']
        mark = con.execute('SELECT * FROM quotes WHERE symbol=?', (claim['symbol'],)).fetchone()
        if mark:
            price = split_mark_price(con, book_id, claim['symbol'], mark['price'], mark['as_of'])
            fractional_value += cents(Decimal(claim['quantity']) * price)
            stale += int(not -5 <= (clock - utc_clock(mark['as_of'])).total_seconds() <= max_quote_age)
        else:
            missing += 1
            stale += 1
    coverage = action_coverage(con, book_id, clock)
    return {'receivable_cents': checked_cents(receivable, 'Dividend receivables'),
            'fractional_market_cents': checked_cents(fractional_value, 'Fractional claim valuation'),
            'fractional_basis_cents': checked_cents(fractional_basis, 'Fractional claim basis'),
            # A displayed fractional mark is provisional until measured
            # cash-in-lieu is known. It must not establish proven performance.
            'missing_marks': missing + len(coverage['unresolved_symbols']) + len(coverage['unchecked_symbols']) + coverage['fractional_claims_pending'],
            'stale_marks': stale, 'coverage': coverage}


def apply_replayed_split(rebuilt, action):
    """Independent append-order replay of one previously observed split."""
    data = json.loads(action['payload'])
    sym = action['symbol']
    quantity, basis, realized = rebuilt.setdefault(sym, [Decimal(0), 0, 0])
    definition = json.loads(action['definition'])
    transformed = quantity * Decimal(definition['numerator']) / Decimal(definition['denominator'])
    whole = transformed.to_integral_value(rounding=ROUND_FLOOR)
    whole_basis = basis if whole == transformed else int((Decimal(basis) * whole / transformed).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if (str(quantity), basis, str(whole), whole_basis) != (data['before_quantity'], data['before_basis_cents'], data['after_quantity'], data['after_basis_cents']):
        raise DeskError('Corporate split does not match independent quantity/basis replay')
    rebuilt[sym] = [whole, whole_basis, realized]
    return transformed - whole, basis - whole_basis



def owned_quantity_at(con, book_id, sym, cutoff):
    timeline = []
    for row in con.execute('SELECT rowid,* FROM p_fills WHERE book_id=? AND symbol=?', (book_id, sym)):
        stamp = utc_clock(row['timestamp'] or row['observed_at'])
        if stamp < utc_clock(cutoff):
            timeline.append((stamp, 1, row['rowid'], 'fill', dict(row)))
    for row in con.execute("SELECT rowid,* FROM a_strategy_actions WHERE book_id=? AND symbol=? AND kind='split' AND applied_at IS NOT NULL AND effective_at<=?", (book_id, sym, cutoff)):
        timeline.append((utc_clock(row['effective_at']), 0, row['rowid'], 'split', dict(row)))
    quantity = Decimal(0)
    for _, _, _, kind, row in sorted(timeline, key=lambda entry: entry[:3]):
        if kind == 'fill':
            quantity += Decimal(row['quantity']) * (1 if row['side'] == 'buy' else -1)
        else:
            ratio = json.loads(row['definition'])
            quantity = (quantity * Decimal(ratio['numerator']) / Decimal(ratio['denominator'])).to_integral_value(rounding=ROUND_FLOOR)
    if quantity < 0:
        raise DeskError('Negative historical owned quantity cannot establish an entitlement')
    return quantity

class TensorActions:
    def __init__(self, store, trading, providers, transport=None, *, payment_transport=None, credentials_file=None):
        self.store, self.trading, self.providers = store, trading, providers
        self.transport = transport or getattr(providers, '_transport', None)
        self.fixture_transport = transport is not None
        self.payment_transport = payment_transport or self.transport
        self.fixture_payment_transport = payment_transport is not None
        self.credentials_file = credentials_file or os.environ.get('ASTER_ACTIONS_CREDENTIALS_FILE')
        self._seed_manifests = {}
        with store.connect() as con:
            initialize_action_tables(con)
            con.execute('INSERT OR IGNORE INTO a_strategy_action_control VALUES(1,1,0)')

    @staticmethod
    def _canonical_event(sym, event):
        kind = event.get('kind')
        if kind not in {'split', 'dividend'}:
            raise DeskError('Unsupported equity corporate action', 422)
        value = event.get('date', event.get('effective_at'))
        if type(value) in (int, float):
            stamp = datetime.fromtimestamp(value, UTC)
            day = stamp.date() if stamp.time().replace(tzinfo=None) == datetime.min.time() else stamp.astimezone(NY).date()
        elif isinstance(value, str) and len(value) == 10:
            day = datetime.fromisoformat(value).date()
        else:
            stamp = utc_clock(value)
            day = stamp.date() if stamp.time().replace(tzinfo=None) == datetime.min.time() else stamp.astimezone(NY).date()
        cal = _nyse()
        if not cal.is_session(day.isoformat()):
            raise DeskError('Corporate action ex-date is not an XNYS session', 422)
        result = {'symbol': sym, 'kind': kind, 'effective_at': cal.session_open(day.isoformat()).to_pydatetime().astimezone(UTC).isoformat()}
        if kind == 'split':
            for field in ('numerator', 'denominator'):
                number = Decimal(str(event.get(field)))
                if not number.is_finite() or number != number.to_integral_value() or not 1 <= number <= 1000000:
                    raise DeskError('Split ratio requires positive bounded integers', 422)
                result[field] = int(number)
            divisor = gcd(result['numerator'], result['denominator'])
            result['numerator'] //= divisor
            result['denominator'] //= divisor
        else:
            amount = Decimal(str(event.get('amount')))
            if not amount.is_finite() or not 0 < amount <= 1000000:
                raise DeskError('Dividend requires a positive finite per-share USD amount', 422)
            result['amount'] = format(amount.normalize(), 'f')
        return result

    def _quantity_at(self, con, book_id, sym, cutoff):
        return owned_quantity_at(con, book_id, sym, cutoff)

    def apply_event(self, book_id, sym, event, source, observed_at, con=None, fence=None):
        sym, observed = symbol(sym), utc_clock(observed_at)
        if not isinstance(source, str) or not source.strip():
            raise DeskError('A corporate action requires explicit source provenance', 422)
        definition = self._canonical_event(sym, event)
        if utc_clock(definition['effective_at']) > observed:
            return {'status': 'future_not_applied'}
        if con is None:
            with self.store.transaction() as writer:
                return self.apply_event(book_id, sym, event, source, observed, con=writer, fence=fence)
        if not con.in_transaction:
            raise DeskError('Corporate actions require an existing writer transaction')
        if fence:
            fence(con)
        book = self.trading._book(con, book_id)
        if book['broker'] != 'local' or not self.trading._strategy_owner(con, book_id):
            raise DeskError('Corporate action accounting is limited to owned local paper books')
        identity = hashlib.sha256(_dump([book_id, sym, definition['kind'], definition['effective_at']]).encode()).hexdigest()
        serialized = _dump(definition)
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        old = con.execute('SELECT * FROM a_strategy_actions WHERE id=?', (identity,)).fetchone()
        if old:
            if old['definition_sha256'] != digest:
                revision = hashlib.sha256(_dump([identity, digest, source]).encode()).hexdigest()
                con.execute('INSERT OR IGNORE INTO a_strategy_action_revisions VALUES(?,?,?,?,?)', (revision, identity, serialized, source, observed.isoformat()))
                con.execute("UPDATE a_strategy_actions SET status='conflict' WHERE id=?", (identity,))
                self.store.event(con, 'corporate_action_conflict', 'data_steward', 'Conflicting corporate action source; affected execution withheld', {'action_id': identity, 'book_id': book_id, 'symbol': sym, 'revision_id': revision})
                return {'id': identity, 'status': 'conflict'}
            return {**dict(old), 'idempotent': True}
        entitled = self._quantity_at(con, book_id, sym, definition['effective_at'])
        payload = {'entitled_quantity': str(entitled), 'after_fill_rowid': con.execute('SELECT COALESCE(MAX(rowid),0) FROM p_fills WHERE book_id=?', (book_id,)).fetchone()[0]}
        status = 'not_entitled' if entitled == 0 else 'applied'
        if definition['kind'] == 'split' and entitled:
            post_fills = con.execute('SELECT 1 FROM p_fills WHERE book_id=? AND symbol=? AND COALESCE(timestamp,observed_at)>=? LIMIT 1', (book_id, sym, definition['effective_at'])).fetchone()
            fraction_pending = con.execute("SELECT 1 FROM a_strategy_fractional_claims WHERE book_id=? AND symbol=? AND status='awaiting_cash_in_lieu' LIMIT 1", (book_id, sym)).fetchone()
            if post_fills or fraction_pending:
                status = 'late_requires_review'
            else:
                held = self.trading._position(con, book_id, sym)
                if not held or Decimal(held['quantity']) != entitled:
                    raise DeskError('Split overnight quantity differs from the current owned holding')
                transformed = entitled * Decimal(definition['numerator']) / Decimal(definition['denominator'])
                whole = transformed.to_integral_value(rounding=ROUND_FLOOR)
                whole_basis = held['cost_cents'] if whole == transformed else int((Decimal(held['cost_cents']) * whole / transformed).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                payload.update(before_quantity=str(entitled), before_basis_cents=held['cost_cents'], after_quantity=str(whole), after_basis_cents=whole_basis, fractional_quantity=str(transformed - whole), fractional_basis_cents=held['cost_cents'] - whole_basis)
                con.execute('UPDATE p_positions SET quantity=?,cost_cents=?,updated_at=? WHERE book_id=? AND symbol=?', (str(whole), whole_basis, observed.isoformat(), book_id, sym))
                pending = list(con.execute(f'SELECT id FROM p_intents WHERE book_id=? AND symbol=? AND status IN ({ACTIVE_SQL})', (book_id, sym)))
                for intent in pending:
                    con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=?,error='Observed split invalidated old share-unit order' WHERE id=?", (observed.isoformat(), observed.isoformat(), intent['id']))
                payload['cancelled_intent_ids'] = [row['id'] for row in pending]
                if transformed != whole:
                    con.execute('INSERT INTO a_strategy_fractional_claims VALUES(?,?,?,?,?,?,?)', (identity, book_id, sym, str(transformed - whole), held['cost_cents'] - whole_basis, 'awaiting_cash_in_lieu', observed.isoformat()))
        if definition['kind'] == 'dividend' and entitled:
            amount = checked_cents(cents(entitled * Decimal(definition['amount'])), 'Accrued dividend')
            payload['amount_cents'] = amount
            con.execute('INSERT INTO a_strategy_receivables VALUES(?,?,?,?,?,?,?)', (identity, book_id, sym, str(entitled), amount, 'receivable', observed.isoformat()))
        con.execute('INSERT INTO a_strategy_actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (identity, book_id, sym, definition['kind'], definition['effective_at'], serialized, digest, source, observed.isoformat(), status, _dump(payload), observed.isoformat() if status == 'applied' else None))
        self.store.event(con, 'corporate_action_recorded', 'accountant', 'Recorded observed local paper corporate action without inventing a trade or payment', {'action_id': identity, 'book_id': book_id, 'symbol': sym, 'kind': definition['kind'], 'status': status, 'source': source, 'definition_sha256': digest, 'payload': payload})
        return dict(con.execute('SELECT * FROM a_strategy_actions WHERE id=?', (identity,)).fetchone())

    def record_verified_payment(self, action_id, payment_at, source, evidence_sha256, *, amount_cents=None, clock=None, fence=None):
        """Trusted dated-payment receipt, never a model or Yahoo payment route.

        Yahoo supplies no dividend pay date. The caller must independently verify
        independent payment evidence; the source and its hash are retained.
        The configured GET-only Alpaca caller explicitly uses declared-date
        local-paper simulation, not proof of actual broker cash receipt.
        Cash-in-lieu additionally requires its measured whole-cent payment.
        """
        observed, paid = utc_clock(clock), utc_clock(payment_at)
        if paid > observed or not source or not isinstance(evidence_sha256, str) or len(evidence_sha256) != 64 or any(c not in '0123456789abcdef' for c in evidence_sha256):
            raise DeskError('A past verified payment date, source and evidence SHA256 are required', 422)
        with self.store.transaction() as con:
            if fence:
                fence(con)
            action = con.execute('SELECT * FROM a_strategy_actions WHERE id=?', (action_id,)).fetchone()
            if not action or action['status'] != 'applied' or paid < utc_clock(action['effective_at']):
                raise DeskError('Payment requires an applied action and cannot predate its ex-date')
            if action['kind'] == 'dividend':
                receivable = con.execute('SELECT * FROM a_strategy_receivables WHERE action_id=?', (action_id,)).fetchone()
                amount = receivable['amount_cents'] if receivable else None
                if amount_cents is not None and amount_cents != amount:
                    raise DeskError('Verified dividend payment does not match the receivable')
            else:
                claim = con.execute('SELECT * FROM a_strategy_fractional_claims WHERE action_id=?', (action_id,)).fetchone()
                if not claim or type(amount_cents) is not int or amount_cents < 0:
                    raise DeskError('Cash-in-lieu requires an existing claim and measured nonnegative whole cents')
                amount = amount_cents
            if amount is None:
                raise DeskError('Action has no payable entitlement')
            prior = con.execute('SELECT * FROM a_strategy_action_payments WHERE action_id=?', (action_id,)).fetchone()
            identity = (amount, paid.isoformat(), source, evidence_sha256)
            if prior:
                if identity != (prior['amount_cents'], prior['payment_at'], prior['source'], prior['evidence_sha256']):
                    raise DeskError('Payment identity already binds a different measured receipt')
                return dict(prior)
            book = self.trading._book(con, action['book_id'])
            cash = checked_cents(book['cash_cents'] + amount, 'Paid local paper cash')
            con.execute('INSERT INTO a_strategy_action_payments VALUES(?,?,?,?,?,?,?)', (action_id, action['book_id'], amount, paid.isoformat(), source, evidence_sha256, observed.isoformat()))
            con.execute('UPDATE p_books SET cash_cents=?,updated_at=? WHERE id=?', (cash, observed.isoformat(), action['book_id']))
            if action['kind'] == 'dividend':
                con.execute("UPDATE a_strategy_receivables SET status='paid' WHERE action_id=?", (action_id,))
            else:
                con.execute("UPDATE a_strategy_fractional_claims SET status='paid' WHERE action_id=?", (action_id,))
                basis = claim['basis_cents']
                gain = amount - basis
                con.execute('UPDATE p_books SET realized_cents=? WHERE id=?', (checked_cents(book['realized_cents'] + gain, 'Cash-in-lieu realized cents'), action['book_id']))
                position = self.trading._position(con, action['book_id'], action['symbol'])
                con.execute('UPDATE p_positions SET realized_cents=? WHERE book_id=? AND symbol=?', (checked_cents(position['realized_cents'] + gain, 'Cash-in-lieu symbol realized cents'), action['book_id'], action['symbol']))
            self.store.event(con, 'verified_corporate_action_payment', 'accountant', 'Credited local paper cash using independent dated payment evidence under its declared source convention', {'action_id': action_id, 'book_id': action['book_id'], 'amount_cents': amount, 'payment_at': paid.isoformat(), 'source': source, 'evidence_sha256': evidence_sha256})
            return dict(con.execute('SELECT * FROM a_strategy_action_payments WHERE action_id=?', (action_id,)).fetchone())

    def _fetch(self, sym, start, clock):
        if not callable(self.transport):
            raise DeskError('No corporate action read transport is configured')
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + quote(sym.replace('.', '-'), safe='')
        params = {'interval': '1d', 'events': 'div,splits', 'includePrePost': 'false', 'period1': int(start.timestamp()), 'period2': int(clock.timestamp()) + 1}
        raw = self.transport('GET', url + '?' + urlencode(params), None, None)
        result = (raw.get('chart') or {}).get('result') if isinstance(raw, dict) else None
        if (raw.get('chart') or {}).get('error') or not isinstance(result, list) or len(result) != 1:
            raise DeskError('Yahoo corporate action response is incomplete')
        chart = result[0]
        meta = chart.get('meta') or {}
        if meta.get('symbol', '').upper() != sym.replace('.', '-') or meta.get('currency') != 'USD':
            raise DeskError('Corporate action symbol/currency identity is unavailable')
        events = chart.get('events') or {}
        if not isinstance(events, dict):
            raise DeskError('Corporate action event collection is malformed')
        values = []
        for vendor_kind, kind in (('splits', 'split'), ('dividends', 'dividend')):
            grouped = events.get(vendor_kind) or {}
            if not isinstance(grouped, dict):
                raise DeskError('Corporate action group is malformed')
            for event in grouped.values():
                definition = self._canonical_event(sym, {**event, 'kind': kind})
                if utc_clock(definition['effective_at']) <= clock:
                    values.append(definition)
        return raw, sorted(values, key=lambda event: (event['effective_at'], 0 if event['kind'] == 'split' else 1))

    def _payment_headers(self):
        """Credentials are read only here and are never stored in receipts."""
        if not self.credentials_file:
            return None
        path = Path(self.credentials_file)
        if not path.is_file() or path.stat().st_mode & 0o077:
            raise DeskError('Corporate-action credentials require a private local file')
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or any(not isinstance(raw.get(key), str) or not raw[key].strip() for key in ('key', 'secret')):
            raise DeskError('Corporate-action read credentials are unavailable')
        return {'APCA-API-KEY-ID': raw['key'], 'APCA-API-SECRET-KEY': raw['secret']}

    def _fetch_declared_payments(self, sym, start_date, end_date, headers):
        if not callable(self.payment_transport):
            raise DeskError('No declared-payment read transport is configured')
        pages, records, seen, token, size = [], [], set(), None, 0
        for _ in range(8):
            params = {'symbols': sym, 'start': start_date, 'end': end_date, 'types': 'cash_dividend', 'limit': 1000}
            if token:
                params['page_token'] = token
            raw = self.payment_transport('GET', 'https://data.alpaca.markets/v1/corporate-actions?' + urlencode(params), None, headers)
            if not isinstance(raw, dict) or not isinstance(raw.get('corporate_actions'), dict) or 'next_page_token' not in raw:
                raise DeskError('Declared-payment response completeness is unavailable')
            group = raw['corporate_actions'].get('cash_dividends', [])
            if not isinstance(group, list) or len(group) > 1000 or any(not isinstance(record, dict) for record in group):
                raise DeskError('Declared-payment record collection is malformed')
            size += len(_dump(raw).encode())
            if size > 8_000_000:
                raise DeskError('Declared-payment response exceeds the bounded receipt size')
            pages.append(raw)
            records.extend(group)
            token = raw['next_page_token']
            if token is None or token == '':
                return pages, records
            if not isinstance(token, str) or len(token) > 4096 or token in seen:
                raise DeskError('Declared-payment pagination is incomplete or cyclic')
            seen.add(token)
        raise DeskError('Declared-payment pagination exceeds its bounded page budget')

    def settle_declared_dividends(self, clock=None, fence=None, max_symbols=16):
        """Simulate local payment only after independent declared-date evidence.

        Yahoo established the USD listing and overnight receivable. Alpaca's
        record has no currency; USD is this desk's explicitly declared listing
        convention. The later payable/process date at 09:30 New York is the
        simulated payment clock, never an assertion of actual broker credit.
        """
        clock = utc_clock(clock)
        if type(max_symbols) is not int or not 1 <= max_symbols <= 64:
            raise DeskError('Declared-payment scan budget is outside its bounded range', 422)
        result = {'configured': bool(self.credentials_file), 'checked': 0, 'payments': 0, 'pending': 0, 'eligible_pending': 0, 'errors': [],
                  'scope': 'GET-only declared-paydate local-paper simulation; gross USD-listing convention, not actual broker receipt'}
        with self.store.connect() as con:
            pending = [dict(row) for row in con.execute("SELECT a.* FROM a_strategy_receivables r JOIN a_strategy_actions a ON a.id=r.action_id JOIN a_strategy_ownership o ON o.book_id=a.book_id WHERE r.status='receivable' AND a.status='applied' ORDER BY a.effective_at,a.id")]
            total = con.execute("SELECT COUNT(*) FROM a_strategy_receivables r JOIN a_strategy_ownership o ON o.book_id=r.book_id WHERE r.status='receivable'").fetchone()[0]
            probes = {row['symbol']: dict(row) for row in con.execute('SELECT * FROM a_strategy_payment_probes')}
        result['pending'], result['eligible_pending'] = total, len(pending)
        try:
            headers = self._payment_headers()
        except Exception:
            result['errors'].append({'detail': 'Declared-payment read credentials unavailable; receivables retained'})
            return result
        if not headers or not pending:
            return result
        grouped = {}
        for action in pending:
            grouped.setdefault(action['symbol'], []).append(action)
        def due(sym):
            prior = probes.get(sym)
            return not prior or (clock - utc_clock(prior['checked_at'])).total_seconds() >= (300 if prior['status'] == 'ok' else 30)
        names = [sym for sym in grouped if due(sym)][:max_symbols]
        def fetch(sym):
            if fence:
                fence()
            start = (utc_clock(grouped[sym][0]['effective_at']).astimezone(NY).date() - timedelta(days=30)).isoformat()
            end = clock.astimezone(NY).date().isoformat()
            pages, records = self._fetch_declared_payments(sym, start, end, headers)
            observed = clock if self.fixture_payment_transport else max(clock, datetime.now(UTC))
            return pages, records, start, end, observed
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(names)))) as pool:
            reads = {sym: pool.submit(fetch, sym) for sym in names}
            for sym, future in reads.items():
                try:
                    pages, records, start, end, observed = future.result()
                    evidence = {'pages': pages, 'pagination_complete': True, 'symbol': sym, 'start_date': start, 'end_date': end,
                                'source_currency': 'Raw currency retained when supplied; absent currency uses independently established Yahoo USD listing identity',
                                'payment_convention': 'Later payable/process date at 09:30 America/New_York; local paper only', 'observed_at': observed.isoformat()}
                    encoded = _dump(evidence).encode()
                    digest = hashlib.sha256(encoded).hexdigest()
                    source = 'Alpaca declared-paydate local-paper USD-listing simulation receipt:' + digest
                    with self.store.transaction() as con:
                        if fence:
                            fence(con)
                        con.execute('INSERT OR IGNORE INTO a_strategy_action_receipts VALUES(?,?,?,?,?)', (digest, sym, observed.isoformat(), 'Alpaca GET /v1/corporate-actions cash_dividend; complete pagination', gzip.compress(encoded, mtime=0)))
                        con.execute("INSERT INTO a_strategy_payment_probes VALUES(?,?,'ok',NULL,?,?,?) ON CONFLICT(symbol) DO UPDATE SET checked_at=excluded.checked_at,status='ok',error=NULL,receipt_ids=excluded.receipt_ids,start_date=excluded.start_date,end_date=excluded.end_date", (sym, observed.isoformat(), _dump([digest]), start, end))
                    for action in grouped[sym]:
                        definition = json.loads(action['definition'])
                        ex_date = utc_clock(action['effective_at']).astimezone(NY).date().isoformat()
                        matching = [record for record in records if record.get('symbol') == sym and record.get('ex_date') == ex_date]
                        if not matching:
                            continue
                        # Several records for one ex-date cannot safely bind
                        # this one aggregated Yahoo entitlement.
                        serialized = {_dump(record) for record in matching}
                        if len(serialized) != 1:
                            self._payment_conflict(action, matching, source, observed, 'Several distinct records share this ex-date', fence)
                            raise DeskError('Ambiguous declared-payment records; no simulated cash credit')
                        record = matching[0]
                        rate = Decimal(str(record.get('rate')))
                        if not rate.is_finite() or rate <= 0 or not record.get('id') or record.get('foreign') is not False:
                            raise DeskError('Declared-payment identity or domestic USD-listing convention is unavailable')
                        if rate != Decimal(definition['amount']):
                            self.apply_event(action['book_id'], sym, {'kind': 'dividend', 'date': ex_date, 'amount': str(rate)}, source, observed, fence=fence)
                            raise DeskError('Declared-payment rate contradicts the accrued entitlement')
                        if not action['source'].startswith('Yahoo chart event receipt:'):
                            continue
                        yahoo_digest = action['source'].split(':', 1)[1]
                        with self.store.connect() as con:
                            yahoo_receipt = con.execute('SELECT data FROM a_strategy_action_receipts WHERE id=? AND symbol=?', (yahoo_digest, sym)).fetchone()
                        if not yahoo_receipt:
                            raise DeskError('Original USD-listing source receipt is unavailable')
                        yahoo_bytes = gzip.decompress(yahoo_receipt['data'])
                        yahoo = json.loads(yahoo_bytes)
                        listing = yahoo['chart']['result'][0]['meta']
                        if record.get('currency', 'USD') != 'USD':
                            self._payment_conflict(action, matching, source, observed, 'Explicit payment currency contradicts the USD entitlement', fence)
                            raise DeskError('Declared-payment currency conflicts with the accrued entitlement')
                        if hashlib.sha256(yahoo_bytes).hexdigest() != yahoo_digest or listing.get('currency') != 'USD' or listing.get('symbol') != sym.replace('.', '-'):
                            raise DeskError('Independent domestic USD-listing identity is unavailable')
                        dates = []
                        for field in ('payable_date', 'process_date'):
                            date = datetime.strptime(record[field], '%Y-%m-%d').date()
                            if date.isoformat() != record[field]:
                                raise DeskError('Declared payment date is malformed')
                            dates.append(date)
                        pay_date = max(dates)
                        paid = datetime(pay_date.year, pay_date.month, pay_date.day, 9, 30, tzinfo=NY).astimezone(UTC)
                        if paid < utc_clock(action['effective_at']):
                            raise DeskError('Declared payment predates the ex-date')
                        if paid > observed:
                            continue
                        self.record_verified_payment(action['id'], paid, source, digest, clock=observed, fence=fence)
                        result['payments'] += 1
                    result['checked'] += 1
                except Exception:
                    with self.store.transaction() as con:
                        if fence:
                            fence(con)
                        prior = con.execute('SELECT * FROM a_strategy_payment_probes WHERE symbol=?', (sym,)).fetchone()
                        start = prior['start_date'] if prior else grouped[sym][0]['effective_at'][:10]
                        end = clock.astimezone(NY).date().isoformat()
                        con.execute("INSERT INTO a_strategy_payment_probes VALUES(?,?,'failed',?,'[]',?,?) ON CONFLICT(symbol) DO UPDATE SET checked_at=excluded.checked_at,status='failed',error=excluded.error", (sym, clock.isoformat(), 'Independent declared-payment verification failed; receivable retained', start, end))
                    result['errors'].append({'symbol': sym, 'detail': 'Independent declared-payment verification failed; no fabricated cash'})
        return result

    def _payment_conflict(self, action, records, source, observed, reason, fence):
        evidence = _dump({'accepted_definition': json.loads(action['definition']), 'declared_records': records, 'reason': reason})
        identity = hashlib.sha256(_dump([action['id'], evidence]).encode()).hexdigest()
        with self.store.transaction() as con:
            if fence:
                fence(con)
            con.execute('INSERT OR IGNORE INTO a_strategy_action_revisions VALUES(?,?,?,?,?)', (identity, action['id'], evidence, source, observed.isoformat()))
            con.execute("UPDATE a_strategy_actions SET status='conflict' WHERE id=?", (action['id'],))
            self.store.event(con, 'corporate_payment_source_conflict', 'accountant', 'Independent declared payment conflicts with entitlement; cash and return validation withheld', {'action_id': action['id'], 'book_id': action['book_id'], 'symbol': action['symbol'], 'revision_id': identity, 'reason': reason, 'source': source})

    def probe_symbols(self, symbols, clock=None, fence=None, max_symbols=16):
        """Bounded pre-entry read, called outside a manager writer transaction."""
        if not isinstance(symbols, (list, tuple)) or len(symbols) > max_symbols:
            raise DeskError('A bounded explicit corporate-action symbol list is required', 422)
        return self.run_once(clock, fence, max_symbols, explicit_symbols=symbols)

    def _candidate_source_endpoint(self, candidate):
        """Cover every forward split since the frozen source basis endpoint."""
        config = json.loads(candidate['config'])
        if not config.get('seed_manifest_file'):
            return None
        path = Path(config['seed_manifest_file'])
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path
        expected = config.get('seed_manifest_sha256')
        stat = path.stat()
        cache_key = (str(path), expected, stat.st_size, stat.st_mtime_ns)
        if cache_key not in self._seed_manifests:
            encoded = path.read_bytes()
            if not expected or hashlib.sha256(encoded).hexdigest() != expected:
                raise DeskError('Corporate-action source endpoint manifest differs from its frozen pin')
            manifest = json.loads(encoded)
            self._seed_manifests[cache_key] = {(group['interval'], group['symbol']): group for source in manifest['sources'] for group in source['groups']}
        group = self._seed_manifests[cache_key].get((config['frame'], candidate['symbol']))
        if not group or not group.get('last_completed_at'):
            raise DeskError('Corporate-action frozen source endpoint is unavailable')
        return datetime.fromtimestamp(int(group['last_completed_at']), UTC).isoformat()

    def run_once(self, clock=None, fence=None, max_symbols=16, explicit_symbols=None):
        clock = utc_clock(clock)
        if type(max_symbols) is not int or not 1 <= max_symbols <= 64:
            raise DeskError('Corporate action scan budget is outside its bounded range', 422)
        with self.store.connect() as con:
            symbols = list(con.execute(f"SELECT f.symbol,MIN(COALESCE(f.timestamp,f.observed_at)) AS start FROM p_fills f JOIN a_strategy_ownership o ON o.book_id=f.book_id GROUP BY f.symbol UNION SELECT i.symbol,MIN(i.created_at) AS start FROM p_intents i JOIN a_strategy_ownership o ON o.book_id=i.book_id WHERE i.status IN ({ACTIVE_SQL}) GROUP BY i.symbol ORDER BY symbol"))
            cursor = con.execute('SELECT cursor FROM a_strategy_action_control WHERE id=1').fetchone()[0]
            candidates = []
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='a_tensor_candidates'").fetchone():
                candidates = [dict(row) for row in con.execute("SELECT c.*,i.book_id,i.config FROM a_tensor_candidates c JOIN a_tensor_installations i ON i.id=c.installation_id JOIN a_tensor_cycles t ON t.origin_ms=c.origin_ms AND t.frame=json_extract(i.config,'$.frame') WHERE i.enabled=1 AND t.expires_ms>?", (int(clock.timestamp() * 1000),))]
            held_names = {row['symbol'] for row in con.execute('SELECT p.symbol,p.quantity FROM p_positions p JOIN a_strategy_ownership o ON o.book_id=p.book_id') if Decimal(row['quantity']) > 0}
            probes = {row['symbol']: dict(row) for row in con.execute('SELECT * FROM a_strategy_action_probes')}
            ranges = {row['symbol']: dict(row) for row in con.execute('SELECT * FROM a_strategy_action_ranges')}
        # UNION can contain two starts for one symbol; preserve the earliest.
        starts = {}
        for row in symbols:
            starts[row['symbol']] = min(starts.get(row['symbol'], row['start']), row['start'])
        for row in candidates:
            endpoint = self._candidate_source_endpoint(row) or clock.isoformat()
            starts[row['symbol']] = min(starts.get(row['symbol'], endpoint), endpoint)
        if explicit_symbols is not None:
            requested = list(dict.fromkeys(symbol(value) for value in explicit_symbols))
            starts = {value: starts.get(value, clock.isoformat()) for value in requested}
        else:
            requested = None
        names = sorted(starts)
        result = {'checked': 0, 'cached': 0, 'actions': 0, 'errors': [], 'scope': 'Observed Yahoo ex-date events; independent declared-date local-paper payment simulation'}
        if not names:
            result['declared_payments'] = self.settle_declared_dividends(clock, fence, max_symbols)
            return result
        order = names[cursor % len(names):] + names[:cursor % len(names)]
        if requested is not None:
            order = requested
        else:
            cutoff = _required_probe_at(clock)
            def unverified(sym):
                return sym not in probes or probes[sym]['status'] != 'ok' or probes[sym]['checked_at'] < cutoff or utc_clock(probes[sym]['checked_at']) > clock
            def score(row):
                value = json.loads(row['data'])
                return float(value.get('priority', value.get('score', 0)))
            candidate_order = [row['symbol'] for row in sorted(candidates, key=lambda row: (-score(row), row['symbol'])) if unverified(row['symbol'])]
            urgent = list(dict.fromkeys(candidate_order + [value for value in order if value in held_names and unverified(value)]))
            order = urgent + [value for value in order if value not in urgent]
        def due(sym):
            receipt = probes.get(sym)
            if not receipt:
                return True
            prior_range = ranges.get(sym)
            if receipt['status'] == 'ok' and (not prior_range or utc_clock(prior_range['start_at']) > utc_clock(starts[sym]) - timedelta(days=7)):
                return True
            age = (clock - utc_clock(receipt['checked_at'])).total_seconds()
            if age < 0:
                return True
            if receipt['status'] == 'ok' and receipt['checked_at'] < _required_probe_at(clock):
                return True
            return age >= (300 if receipt['status'] == 'ok' else 30)
        result['cached'] = sum(not due(sym) for sym in order)
        chosen = [sym for sym in order if due(sym)][:max_symbols]
        def fetch(sym):
            if fence:
                fence()
            raw, events = self._fetch(sym, utc_clock(starts[sym]) - timedelta(days=7), clock)
            observed = clock if self.fixture_transport else max(clock, datetime.now(UTC))
            return raw, events, observed
        # Source GETs can run independently; financial writes remain sequential
        # and recheck the worker fence within every writer transaction.
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(chosen)))) as pool:
            reads = {sym: pool.submit(fetch, sym) for sym in chosen}
            for sym, future in reads.items():
                try:
                    raw, events, observed = future.result()
                    encoded = _dump(raw).encode()
                    digest = hashlib.sha256(encoded).hexdigest()
                    with self.store.transaction() as con:
                        if fence:
                            fence(con)
                        con.execute('INSERT OR IGNORE INTO a_strategy_action_receipts VALUES(?,?,?,?,?)', (digest, sym, observed.isoformat(), 'Yahoo chart events=div,splits', gzip.compress(encoded, mtime=0)))
                        books = [row['book_id'] for row in con.execute('SELECT book_id FROM a_strategy_ownership') if con.execute('SELECT 1 FROM p_fills WHERE book_id=? AND symbol=? UNION SELECT 1 FROM p_intents WHERE book_id=? AND symbol=? LIMIT 1', (row['book_id'], sym, row['book_id'], sym)).fetchone()]
                        books = sorted(set(books) | {row['book_id'] for row in candidates if row['symbol'] == sym})
                        for event in events:
                            for book_id in books:
                                action = self.apply_event(book_id, sym, event, 'Yahoo chart event receipt:' + digest, observed, con=con, fence=fence)
                                result['actions'] += int(action.get('status') == 'applied' and not action.get('idempotent'))
                        con.execute("INSERT INTO a_strategy_action_probes VALUES(?,?,'ok',NULL,?) ON CONFLICT(symbol) DO UPDATE SET checked_at=excluded.checked_at,status=excluded.status,error=NULL,receipt_id=excluded.receipt_id", (sym, observed.isoformat(), digest))
                        con.execute('INSERT INTO a_strategy_action_ranges VALUES(?,?,?,?) ON CONFLICT(symbol) DO UPDATE SET start_at=excluded.start_at,end_at=excluded.end_at,receipt_id=excluded.receipt_id', (sym, (utc_clock(starts[sym]) - timedelta(days=7)).isoformat(), clock.isoformat(), digest))
                    result['checked'] += 1
                except Exception:
                    with self.store.transaction() as con:
                        if fence:
                            fence(con)
                        con.execute("INSERT INTO a_strategy_action_probes VALUES(?,?,'failed',?,NULL) ON CONFLICT(symbol) DO UPDATE SET checked_at=excluded.checked_at,status=excluded.status,error=excluded.error,receipt_id=NULL", (sym, clock.isoformat(), 'Corporate action read failed; owned execution withheld'))
                    result['errors'].append({'symbol': sym, 'detail': 'Corporate action read failed; no fabricated event or payment'})
        with self.store.transaction() as con:
            if fence:
                fence(con)
            con.execute('UPDATE a_strategy_action_control SET cursor=? WHERE id=1', ((cursor + len(chosen)) % len(names),))
        observed = clock if self.fixture_transport else max(clock, datetime.now(UTC))
        result['declared_payments'] = self.settle_declared_dividends(observed, fence, max_symbols)
        return result
