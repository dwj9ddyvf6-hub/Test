"""Separate, autonomous local-paper Coinbase native trend companion.

No broker client, credentials, parent desk tables, or strategy refits are used.
Only an explicit install command funds the two independently owned books.
"""
from __future__ import annotations

import argparse
import datetime as dt
from email.utils import parsedate_to_datetime
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import signal
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
import uuid
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path
from backend.prospective_native_math import features as r14_features

UTC = dt.timezone.utc
SYMBOLS = ("BTC-USD", "ETH-USD")
BOOK_WEIGHTS = {"ETH_SMA200": (0, 1), "BTC_ETH_SMA200": (.5, .5)}
FEE = Decimal("0.002")
MONEY_QUANTUM = Decimal("0.00000001")
PAPER_FILL_SOURCE = "local Coinbase received-quote paper simulation"
RULES = {
    "version": "native-coinbase-prospective-r15/1",
    "venue": "Coinbase Exchange public USD spot; local paper execution only",
    "gate": "Latest completed UTC daily close strictly above inclusive SMA200",
    "maximum_weights": BOOK_WEIGHTS,
    "fee_per_side": "0.002",
    "entry_window_seconds": 300,
    "quote_max_age_seconds": 30,
    "initial_virtual_principal_per_book": "100000",
    "cash": "USD virtual cash, zero interest, immediate simulated spot sale proceeds",
    "execution": "Actual received bid/ask local paper fills, lot-floor, actual published minimum funds required, fee-funded targets; sales before increases",
    "owned_exit": "Bearish-gate reductions may execute at a genuinely received later quote after a missed opening; no retroactive opening fill",
    "history_identity": "R14 Yahoo composite historical results do not establish Coinbase venue parity or future returns",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


RULES_SHA = sha(RULES)


def clock(value=None):
    if value is None:
        return dt.datetime.now(UTC)
    if isinstance(value, dt.datetime):
        out = value
    elif isinstance(value, str) and value:
        out = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Timezone-aware timestamp required")
    if out.tzinfo is None:
        raise ValueError("Timezone-aware timestamp required")
    return out.astimezone(UTC)


def number(value, zero=False):
    if isinstance(value, bool) or not isinstance(value, (str, float, int, Decimal)):
        raise ValueError("Finite numeric value required")
    try:
        out = Decimal(str(value))
    except Exception as exc:
        raise ValueError("Invalid numeric value") from exc
    if not out.is_finite() or out < 0 or (not zero and out == 0):
        raise ValueError("Invalid nonnegative number")
    return out


def default_path():
    return Path(os.environ.get("ASTER_NATIVE_DB_PATH", str(Path(__file__).resolve().parents[1] / "data/native-prospective.sqlite")))


def isolated_path(path):
    path = Path(path).resolve()
    main = Path(os.environ.get("ASTER_DB_PATH", str(Path(__file__).resolve().parents[1] / "data/aster.sqlite"))).resolve()
    if path == main or path.name == "aster.sqlite":
        raise ValueError("Native companion must use its own database, never the operating Aster ledger")
    if path.exists():
        connection = sqlite3.connect("file:"+urllib.parse.quote(str(path))+"?mode=ro",uri=True)
        try:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if any(name not in {"sqlite_sequence"} and not name.startswith("native_") for name in tables):
                raise ValueError("Database contains another ledger; native companion requires an isolated database")
        finally:
            connection.close()
    return path


class CoinbasePublicFeed:
    """Public GET-only market feed. Receipt clocks are captured, never supplied by a market bar."""
    BASE = "https://api.exchange.coinbase.com/"

    def _get_json(self, tail):
        started = clock()
        url = self.BASE + tail
        req = urllib.request.Request(url, headers={"User-Agent": "AsterNativePaper/1.0", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read()
            received = clock()
            receipt = {"url": url, "request_started_at": started.isoformat(),
                       "received_at": received.isoformat(), "http_status": response.status,
                       "server_date": response.headers.get("Date"),
                       "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_bytes": len(raw),
                       "raw_body_utf8": raw.decode('utf-8')}
        return json.loads(raw), receipt

    def capture(self, now=None):
        start = clock(now)
        opening = start.replace(hour=0, minute=0, second=0, microsecond=0)
        candles, quotes, products, receipts = {}, {}, {}, []
        for symbol in SYMBOLS:
            product, receipt = self._get_json("products/" + symbol)
            receipts.append(receipt)
            products[symbol] = {**product, "received_at": receipt["received_at"], "receipt_sha256": sha(receipt)}
            query = urllib.parse.urlencode({"granularity": 86400,
                "start": (opening-dt.timedelta(days=210)).isoformat(), "end": opening.isoformat(),
                "aster_receipt_nonce": str(time.time_ns())})
            rows, receipt = self._get_json("products/" + symbol + "/candles?" + query)
            receipts.append(receipt)
            observed = clock(receipt["received_at"])
            normalized = []
            for row in sorted(rows, key=lambda r:r[0]):
                if not isinstance(row,list) or len(row)!=6:
                    raise ValueError("Malformed Coinbase candle")
                beginning = dt.datetime.fromtimestamp(row[0], UTC)
                complete = beginning + dt.timedelta(days=1)
                if complete > observed or complete > opening:
                    continue
                normalized.append({"date": beginning.date().isoformat(), "start_at": beginning.isoformat(),
                    "complete_at": complete.isoformat(), "open": row[3], "high": row[2], "low": row[1],
                    "close": row[4], "volume": row[5], "received_at": receipt["received_at"],
                    "source_receipt_sha256": sha(receipt)})
            candles[symbol] = normalized[-200:]
        # Acquire quotes after both signals are actually known, including the combined book.
        for symbol in SYMBOLS:
            tick, receipt = self._get_json("products/" + symbol + "/ticker?aster_receipt_nonce=" + str(time.time_ns()))
            receipts.append(receipt)
            quotes[symbol] = {"bid": tick.get("bid"), "ask": tick.get("ask"), "as_of": receipt["received_at"],
                "market_trade_at": tick.get("time"),
                "received_at": receipt["received_at"], "source_receipt_sha256": sha(receipt),
                "clock_scope": "Bid/ask snapshot observed at actual HTTP receipt; last-trade time separately guards freshness, not an exchange timestamp for the bid/ask"}
        return {"venue": RULES["venue"], "paper_only": True, "requested_at": start.isoformat(),
                "received_at": clock().isoformat(), "bars": candles, "quotes": quotes,
                "products": products, "receipts": receipts}


def validate_capture(capture, now):
    now = clock(now)
    opening = now.replace(hour=0,minute=0,second=0,microsecond=0)
    if capture.get("paper_only") is not True or capture.get("venue") != RULES["venue"]:
        raise ValueError("Wrong paper venue identity")
    received = clock(capture["received_at"])
    requested=clock(capture['requested_at'])
    if requested>received or received > now or now-requested > dt.timedelta(seconds=60):
        raise ValueError("Stale or future acquisition receipt")
    output = {}
    receipts = {sha(r):r for r in capture["receipts"]}
    decoded = {}
    for receipt in receipts.values():
        parsed = urllib.parse.urlparse(receipt["url"])
        server = parsedate_to_datetime(receipt['server_date'])
        observed = clock(receipt['received_at'])
        if (parsed.scheme != "https" or parsed.netloc != "api.exchange.coinbase.com" or
            receipt["http_status"] != 200 or receipt["raw_bytes"] <= 0 or
            len(receipt["raw_sha256"]) != 64 or
            not requested <= clock(receipt["request_started_at"]) <= observed <= received or
            server > observed+dt.timedelta(seconds=1) or observed-server > dt.timedelta(seconds=30)):
            raise ValueError("Invalid public Coinbase acquisition receipt")
        raw=receipt['raw_body_utf8'].encode('utf-8')
        if len(raw)!=receipt['raw_bytes'] or hashlib.sha256(raw).hexdigest()!=receipt['raw_sha256']:
            raise ValueError("Retained source payload does not match its receipt")
        decoded[sha(receipt)] = json.loads(receipt['raw_body_utf8'])
    def binding(payload, key, expected):
        receipt = receipts.get(payload[key])
        if receipt is None or urllib.parse.urlparse(receipt["url"]).path != expected or receipt["received_at"] != payload["received_at"]:
            raise ValueError("Source record is not bound to the actual acquisition receipt")
        if expected.endswith('/candles')and parsedate_to_datetime(receipt['server_date'])<clock(payload['complete_at']):
            raise ValueError("Vendor response predates the candle completion")
        return decoded[payload[key]]
    for symbol in SYMBOLS:
        rows = capture["bars"][symbol]
        product = capture["products"][symbol]
        quote = capture["quotes"][symbol]
        raw_product=binding(product,"receipt_sha256","/products/"+symbol)
        raw_quote=binding(quote,"source_receipt_sha256","/products/"+symbol+"/ticker")
        if (not isinstance(raw_product,dict)or set(product)-{'received_at','receipt_sha256'}!=set(raw_product)or
            any(product.get(k)!=v for k,v in raw_product.items())):
            raise ValueError("Normalized product differs from actual raw metadata")
        if (number(quote['bid'])!=number(raw_quote['bid'])or number(quote['ask'])!=number(raw_quote['ask'])or
            clock(quote['market_trade_at'])!=clock(raw_quote['time'])):
            raise ValueError("Normalized quote differs from actual raw ticker")
        if len(rows) != 200:
            raise ValueError("Exactly 200 completed daily bars required")
        if product.get("id") != symbol or product.get("quote_currency") != "USD" or product.get("base_currency") != symbol.split("-")[0]:
            raise ValueError("Wrong actual Coinbase product identity")
        if product.get("status") != "online" or any(product.get(k)is not False for k in ("trading_disabled", "cancel_only", "auction_mode", "post_only","limit_only")):
            raise ValueError("Product not executable for ordinary spot paper entries")
        if clock(product["received_at"]) > received:
            raise ValueError("Future product receipt")
        lot = number(product["base_increment"])
        tick = number(product["quote_increment"])
        minimum = number(product["min_market_funds"])
        previous = None
        closes, source_clocks = [], []
        source_identity=rows[0]['source_receipt_sha256']
        raw_rows=decoded[source_identity]
        receipt=receipts[source_identity]
        if urllib.parse.parse_qs(urllib.parse.urlparse(receipt['url']).query).get('granularity')!=['86400']:
            raise ValueError("Source receipt does not declare actual UTC daily granularity")
        raw_candles={}
        for raw_row in raw_rows:
            if not isinstance(raw_row,list)or len(raw_row)!=6 or isinstance(raw_row[0],bool):
                raise ValueError("Malformed raw daily source")
            stamp=dt.datetime.fromtimestamp(raw_row[0],UTC)
            if stamp.time()!=dt.time(0)or stamp.isoformat()in raw_candles:
                raise ValueError("Duplicate or nonnative raw daily source")
            raw_candles[stamp.isoformat()]=raw_row
        selected=[s for s in sorted(raw_candles)if clock(s)+dt.timedelta(days=1)<=opening and clock(s)+dt.timedelta(days=1)<=clock(receipt['received_at'])][-200:]
        if [r['start_at']for r in rows]!=selected:
            raise ValueError("Normalized daily selection differs from actual raw completed history")
        for row in rows:
            if row['source_receipt_sha256']!=source_identity:raise ValueError("Mixed daily source responses")
            binding(row,"source_receipt_sha256","/products/"+symbol+"/candles")
            start, complete, fetched = clock(row["start_at"]), clock(row["complete_at"]), clock(row["received_at"])
            if start.time() != dt.time(0) or complete != start+dt.timedelta(days=1) or complete > fetched or fetched > received:
                raise ValueError("Invalid completed-bar availability")
            if row["date"] != start.date().isoformat() or (previous is not None and start-previous != dt.timedelta(days=1)):
                raise ValueError("Missing/non-native daily period")
            o,h,l,c = [number(row[k]) for k in ("open","high","low","close")]
            number(row["volume"],True)
            raw_row=raw_candles[row['start_at']]
            if any(number(row[key],key=='volume')!=number(raw_row[index],key=='volume')for key,index in [('low',1),('high',2),('open',3),('close',4),('volume',5)]):
                raise ValueError("Normalized OHLCV differs from actual raw candle")
            if not l <= min(o,c) <= max(o,c) <= h:
                raise ValueError("Invalid OHLC")
            previous = start; closes.append(c); source_clocks.append(fetched)
        if clock(rows[-1]["complete_at"]) != opening:
            raise ValueError("Latest completed UTC day unavailable")
        bid, ask = number(quote["bid"]), number(quote["ask"])
        as_of, quote_received = clock(quote["as_of"]), clock(quote["received_at"])
        market_trade = clock(quote["market_trade_at"])
        if bid > ask or as_of != quote_received or quote_received > received or now-as_of > dt.timedelta(seconds=30):
            raise ValueError("Stale/future/inverted received quote")
        if market_trade > quote_received or now-market_trade > dt.timedelta(seconds=30):
            raise ValueError("Ticker last trade is stale/future; bid/ask freshness not established")
        if bid % tick or ask % tick:
            raise ValueError("Off-tick source quote")
        if as_of < max(source_clocks):
            raise ValueError("Quote predates observed signal availability")
        # Preserve the unchanged R14 inclusive SMA calculation and strict comparison.
        original = r14_features([{"close":float(c),"date":r["date"],"complete_at":r["complete_at"]} for c,r in zip(closes,rows)])[-1]
        output[symbol] = {"gate": original["SMA200"], "close": str(closes[-1]), "sma200": str(original["sma200"]),
            "source_completed_at": opening.isoformat(), "signal_received_at": max(source_clocks).isoformat(),
            "bid": bid, "ask": ask, "mid": (bid+ask)/2, "lot": lot, "tick": tick,
            "minimum": minimum, "quote": quote}
    latest_signal = max(clock(m["signal_received_at"]) for m in output.values())
    if any(clock(m["quote"]["as_of"]) < latest_signal for m in output.values()):
        raise ValueError("Combined-book quote predates one of its signal receipts")
    return output


def funded_targets(cash, quantities, market, weights):
    """R14 post-fee-NAV fixed point extended to observed bid/ask and venue lot floors."""
    cash = number(cash,True)
    q = [number(quantities.get(s,"0"),True) for s in SYMBOLS]
    mids = [market[s]["mid"] for s in SYMBOLS]
    weights = [Decimal(str(w)) for w in weights]
    if any(w<0 for w in weights) or sum(weights)>1:
        raise ValueError("Invalid gross weight")
    pre = cash + sum(v*p for v,p in zip(q,mids))
    def remaining(nav, round_lots=False):
        target = [w*nav/p for w,p in zip(weights,mids)]
        if round_lots:
            target = [(v/market[s]["lot"]).to_integral_value(rounding=ROUND_DOWN)*market[s]["lot"] for s,v in zip(SYMBOLS,target)]
        result = cash
        for s,old,new in zip(SYMBOLS,q,target):
            delta = new-old
            price = market[s]["ask"] if delta>=0 else market[s]["bid"]
            result -= delta*price + abs(delta)*price*FEE
        return result,target
    lo,hi = Decimal(0),pre
    for _ in range(100):
        mid = (lo+hi)/2
        cash_after,target = remaining(mid)
        actual = cash_after+sum(v*p for v,p in zip(target,mids))
        if mid>actual:hi=mid
        else:lo=mid
    remaining_cash,target = remaining((lo+hi)/2,True)
    if remaining_cash < -MONEY_QUANTUM*4:
        raise ValueError("Unfunded target")
    return dict(zip(SYMBOLS,target))


SCHEMA = """
CREATE TABLE IF NOT EXISTS native_books(book TEXT PRIMARY KEY, enabled INTEGER NOT NULL,
 cash TEXT NOT NULL, principal TEXT NOT NULL, rules_sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS native_positions(book TEXT NOT NULL,symbol TEXT NOT NULL,quantity TEXT NOT NULL,
 PRIMARY KEY(book,symbol));
CREATE TABLE IF NOT EXISTS native_cycles(book TEXT NOT NULL,day TEXT NOT NULL,status TEXT NOT NULL,
 signal_sha256 TEXT NOT NULL,features TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(book,day));
CREATE TABLE IF NOT EXISTS native_orders(id TEXT PRIMARY KEY,book TEXT NOT NULL,day TEXT NOT NULL,
 symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,status TEXT NOT NULL,quote TEXT NOT NULL,
 created_at TEXT NOT NULL,filled_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS native_fills(order_id TEXT PRIMARY KEY,book TEXT NOT NULL,symbol TEXT NOT NULL,
 side TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,fee TEXT NOT NULL,at TEXT NOT NULL,
 source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS native_bars(symbol TEXT NOT NULL,start_at TEXT NOT NULL,payload TEXT NOT NULL,
 first_received_at TEXT NOT NULL,PRIMARY KEY(symbol,start_at));
CREATE TABLE IF NOT EXISTS native_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,
 kind TEXT NOT NULL,book TEXT,at TEXT NOT NULL,payload TEXT NOT NULL,previous_sha256 TEXT NOT NULL,sha256 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS native_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS native_raw_sources(sha256 TEXT PRIMARY KEY,body TEXT NOT NULL,
 raw_bytes INTEGER NOT NULL,first_received_at TEXT NOT NULL);
"""


class NativeProspectiveDesk:
    def __init__(self,path=None):
        self.path = isolated_path(path or default_path())
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path,timeout=20,isolation_level=None)
        conn.row_factory = sqlite3.Row
        # This small ledger uses rollback journaling so a mode=ro status read
        # cannot create WAL shared-memory sidecars, even after a writer stops.
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            with conn:yield conn
        finally:conn.close()

    def _event(self,conn,kind,payload,at,book=None,event_id=None):
        identity = event_id or uuid.uuid4().hex
        existing = conn.execute("SELECT * FROM native_events WHERE event_id=?",(identity,)).fetchone()
        text = canonical(payload)
        if existing:
            if existing["kind"] != kind or existing["payload"] != text or existing["book"] != book:
                raise ValueError("Conflicting idempotent event")
            return existing["sha256"]
        last = conn.execute("SELECT sha256 FROM native_events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0"*64
        digest = sha({"previous":previous,"id":identity,"kind":kind,"book":book,"at":at,"payload":payload})
        conn.execute("INSERT INTO native_events(event_id,kind,book,at,payload,previous_sha256,sha256) VALUES(?,?,?,?,?,?,?)",
                     (identity,kind,book,at,text,previous,digest))
        return digest

    def verify_ledger(self,conn):
        """Replay owned monetary events before any new decision; fail closed on corruption."""
        previous="0"*64; cash={}; positions={}; fill_ids=set(); installed={}
        for row in conn.execute("SELECT * FROM native_events ORDER BY seq"):
            payload=json.loads(row['payload'])
            expected=sha({'previous':previous,'id':row['event_id'],'kind':row['kind'],
                          'book':row['book'],'at':row['at'],'payload':payload})
            if row['previous_sha256']!=previous or row['sha256']!=expected:
                raise ValueError("Native append-only journal hash chain is invalid")
            previous=expected; book=row['book']
            if row['kind']=='installation':
                if (book not in BOOK_WEIGHTS or book in installed or sha(payload.get('rules'))!=RULES_SHA or
                    not isinstance(payload.get('enabled'),bool)or payload.get('paper_only')is not True or row['event_id']!='install:'+book):
                    raise ValueError('Invalid installed authorization or rule identity')
                installed[book]={'enabled':payload['enabled'],'at':row['at']}
            elif row['kind']=='entry_enable_changed':
                if book not in installed or not isinstance(payload.get('enabled'),bool)or payload.get('owned_exits_preserved')is not True:
                    raise ValueError('Invalid entry authorization event')
                installed[book]['enabled']=payload['enabled']
            elif row['kind']=='virtual_funding':
                if book not in installed or book in cash or payload.get('amount')!='100000' or payload.get('real_money')is not False or row['event_id']!='fund:'+book:
                    raise ValueError("Duplicate or invalid virtual funding")
                cash[book]=Decimal('100000');positions[book]={s:Decimal(0)for s in SYMBOLS}
            elif row['kind']=='paper_fill':
                if book not in cash or payload.get('broker_submitted')is not False or payload.get('paper_only')is not True:
                    raise ValueError("Fill has no independent funded ownership")
                quantity=number(payload['quantity']);price=number(payload['price']);fee=number(payload['fee'],True)
                if fee!=(quantity*price*FEE).quantize(MONEY_QUANTUM,rounding=ROUND_UP):
                    raise ValueError("Journal fill fee does not match declared cost")
                sign=1 if payload['side']=='buy' else -1 if payload['side']=='sell' else 0
                if not sign:raise ValueError("Invalid journal fill side")
                cash[book]-=sign*quantity*price+fee;positions[book][payload['symbol']]+=sign*quantity
                if cash[book]<0 or positions[book][payload['symbol']]<0 or cash[book]!=number(payload['cash_after'],True) or positions[book][payload['symbol']]!=number(payload['quantity_after'],True):
                    raise ValueError("Journal fill conservation failed")
                saved=conn.execute("SELECT f.*,o.status,o.book AS order_book,o.day AS order_day,o.symbol AS order_symbol,"
                    "o.side AS order_side,o.quantity AS order_quantity,o.quote AS order_quote,o.created_at,o.filled_at "
                    "FROM native_fills f JOIN native_orders o ON o.id=f.order_id WHERE f.order_id=?",(payload['order_id'],)).fetchone()
                if (not saved or saved['status']!='filled' or any(saved[k]!=str(payload[k]) for k in ['quantity','price','fee','side','symbol'])or saved['book']!=book or
                    saved['order_book']!=book or saved['order_day']!=payload['day']or
                    any(saved['order_'+k]!=str(payload[k])for k in ['quantity','side','symbol'])or
                    saved['order_quote']!=canonical(payload['quote'])or
                    any(saved[k]!=row['at']for k in ['at','created_at','filled_at'])or saved['source']!=PAPER_FILL_SOURCE or
                    price!=number(payload['quote']['ask'if sign==1 else 'bid'])or
                    clock(payload['quote']['received_at'])>clock(row['at'])or
                    clock(row['at'])-clock(payload['quote']['as_of'])>dt.timedelta(seconds=30)):
                    raise ValueError("Fill/order/journal receipts disagree")
                fill_ids.add(payload['order_id'])
        accounts=conn.execute("SELECT * FROM native_books").fetchall()
        if set(cash)!=set(installed)or set(cash)!={r['book']for r in accounts}:raise ValueError("Funded book set differs from journal")
        for account in accounts:
            book=account['book']
            if account['rules_sha256']!=RULES_SHA or account['principal']!='100000' or number(account['cash'],True)!=cash[book]:
                raise ValueError("Book capital/rule state differs from journal")
            if account['enabled']not in (0,1)or bool(account['enabled'])!=installed[book]['enabled']or account['created_at']!=installed[book]['at']:
                raise ValueError('Book entry authorization differs from installation/enable journal')
            observed={r['symbol']:number(r['quantity'],True)for r in conn.execute("SELECT * FROM native_positions WHERE book=?",(book,))}
            if any(observed.get(s,Decimal(0))!=quantity for s,quantity in positions[book].items()) or set(observed)-set(SYMBOLS):
                raise ValueError("Owned positions differ from journal")
        if len(fill_ids)!=conn.execute("SELECT count(*)FROM native_fills").fetchone()[0] or len(fill_ids)!=conn.execute("SELECT count(*)FROM native_orders").fetchone()[0]:
            raise ValueError("Unjournaled fills or orders")
        return {'events':conn.execute("SELECT count(*)FROM native_events").fetchone()[0],'fills':len(fill_ids),'last_sha256':previous}

    def install(self,enable=False,now=None):
        at=clock(now).isoformat()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.verify_ledger(conn)
            for book in BOOK_WEIGHTS:
                old=conn.execute("SELECT * FROM native_books WHERE book=?",(book,)).fetchone()
                if old:
                    if old["rules_sha256"] != RULES_SHA:
                        raise ValueError("Installed rule identity differs")
                    continue
                conn.execute("INSERT INTO native_books VALUES(?,?,?,?,?,?)",(book,int(enable),"100000","100000",RULES_SHA,at))
                self._event(conn,"installation",{"rules":RULES,"enabled":bool(enable),"paper_only":True},at,book,"install:"+book)
                self._event(conn,"virtual_funding",{"amount":"100000","currency":"USD","real_money":False},at,book,"fund:"+book)
            conn.commit()
        return read_status(self.path)

    def set_enabled(self,book,enabled,now=None):
        if book not in BOOK_WEIGHTS or not isinstance(enabled,bool):raise ValueError("Named book and boolean enable state required")
        with self.connect()as conn:
            conn.execute('BEGIN IMMEDIATE');self.verify_ledger(conn)
            old=conn.execute('SELECT enabled FROM native_books WHERE book=?',(book,)).fetchone()
            if old is None:raise ValueError("Book is not installed; enable does not fund or install")
            if bool(old[0])!=enabled:
                conn.execute('UPDATE native_books SET enabled=? WHERE book=?',(int(enabled),book))
                self._event(conn,'entry_enable_changed',{'enabled':enabled,'owned_exits_preserved':True},clock(now).isoformat(),book)
            conn.commit()
        return read_status(self.path)

    def _fill(self,conn,book,day,symbol,side,quantity,market,at):
        quantity=number(quantity)
        quote=market[symbol]["quote"]
        if clock(at)-clock(quote["as_of"])>dt.timedelta(seconds=30) or clock(quote["received_at"])>clock(at):
            raise ValueError("Fill quote unavailable/stale")
        stamp=clock(at);opening=stamp.replace(hour=0,minute=0,second=0,microsecond=0)
        if side=='buy'and (day!=stamp.date().isoformat()or not opening<=stamp<opening+dt.timedelta(seconds=300)):
            raise ValueError("Entry opening window expired before local fill")
        lot=market[symbol]["lot"]
        if quantity%lot:
            raise ValueError("Off-lot quantity")
        price=market[symbol]["ask"] if side=="buy" else market[symbol]["bid"]
        notional=quantity*price
        if notional<market[symbol]["minimum"]:
            return False
        fee=(notional*FEE).quantize(MONEY_QUANTUM,rounding=ROUND_UP)
        row=conn.execute("SELECT cash FROM native_books WHERE book=?",(book,)).fetchone()
        old=conn.execute("SELECT quantity FROM native_positions WHERE book=? AND symbol=?",(book,symbol)).fetchone()
        held=number(old[0],True)if old else Decimal(0);cash=number(row[0],True)
        if side=="buy":
            if notional+fee>cash:
                raise ValueError("Buy not funded by reconciled actual paper cash")
            cash-=notional+fee;held+=quantity
        elif side=="sell":
            if quantity>held:
                raise ValueError("Sell exceeds owned position")
            cash+=notional-fee;held-=quantity
        else:raise ValueError("Invalid side")
        identity=sha({"book":book,"day":day,"symbol":symbol,"side":side,"held_after":str(held),
                      "quote_sha256":sha(quote),"prior_event":conn.execute("SELECT count(*) FROM native_events").fetchone()[0]})
        conn.execute("INSERT INTO native_orders VALUES(?,?,?,?,?,?,?,?,?,?)",(identity,book,day,symbol,side,str(quantity),"filled",canonical(quote),at,at))
        conn.execute("INSERT INTO native_fills VALUES(?,?,?,?,?,?,?,?,?)",(identity,book,symbol,side,str(quantity),str(price),str(fee),at,PAPER_FILL_SOURCE))
        conn.execute("UPDATE native_books SET cash=? WHERE book=?",(str(cash),book))
        conn.execute("INSERT INTO native_positions VALUES(?,?,?) ON CONFLICT(book,symbol)DO UPDATE SET quantity=excluded.quantity",(book,symbol,str(held)))
        self._event(conn,"paper_fill",{"order_id":identity,"day":day,"symbol":symbol,"side":side,"quantity":str(quantity),
            "price":str(price),"fee":str(fee),"cash_after":str(cash),"quantity_after":str(held),"quote":quote,
            "paper_only":True,"broker_submitted":False},at,book,"fill:"+identity)
        return True

    def run_once(self,capture=None,now=None):
        # Acquisition happens before the short financial transaction, so a slow feed cannot hold a book lock.
        try:
            capture=CoinbasePublicFeed().capture()if capture is None else capture
            at=clock(now)
            market=validate_capture(capture,at)
        except Exception as exc:
            at=clock(now)
            with self.connect()as conn:
                conn.execute("BEGIN IMMEDIATE")
                self._event(conn,"data_block",{"error":str(exc),"financial_mutations":False},at.isoformat())
                conn.execute("INSERT OR REPLACE INTO native_meta VALUES('last_error',?)",(str(exc),))
                conn.commit()
            return {"status":"blocked","error":str(exc),"fills":0,"paper_only":True}
        day=at.date().isoformat();opening=at.replace(hour=0,minute=0,second=0,microsecond=0)
        inside=opening<=at<opening+dt.timedelta(seconds=300)
        fills=0
        features={s:{k:v for k,v in m.items()if k in ['gate','close','sma200','source_completed_at','signal_received_at']}for s,m in market.items()}
        with self.connect()as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.verify_ledger(conn)
            # A database wait or journal replay cannot freeze the acquisition/entry clock.
            at=clock(now);market=validate_capture(capture,at)
            day=at.date().isoformat();opening=at.replace(hour=0,minute=0,second=0,microsecond=0)
            inside=opening<=at<opening+dt.timedelta(seconds=300)
            for receipt in capture['receipts']:
                old=conn.execute('SELECT body,raw_bytes FROM native_raw_sources WHERE sha256=?',(receipt['raw_sha256'],)).fetchone()
                if old and (old[0]!=receipt['raw_body_utf8']or old[1]!=receipt['raw_bytes']):
                    raise ValueError('Conflicting retained raw source hash')
                if not old:
                    conn.execute('INSERT INTO native_raw_sources VALUES(?,?,?,?)',
                        (receipt['raw_sha256'],receipt['raw_body_utf8'],receipt['raw_bytes'],receipt['received_at']))
            # Preserve first observed daily values. Ordinary provider revisions are explicit blocking evidence.
            for symbol,rows in capture["bars"].items():
                for row in rows:
                    pure={k:row[k]for k in ['date','start_at','complete_at','open','high','low','close','volume']}
                    old=conn.execute("SELECT payload FROM native_bars WHERE symbol=? AND start_at=?",(symbol,row['start_at'])).fetchone()
                    if old and old[0]!=canonical(pure):
                        self._event(conn,"source_revision_block",{"symbol":symbol,"start_at":row['start_at'],"original_sha256":hashlib.sha256(old[0].encode()).hexdigest(),"new_sha256":sha(pure)},at.isoformat())
                        conn.execute("INSERT OR REPLACE INTO native_meta VALUES('last_error','Completed daily source revised; financial decisions blocked')")
                        conn.commit();return {"status":"source_revision_block","fills":0,"paper_only":True}
                    if not old:
                        conn.execute("INSERT INTO native_bars VALUES(?,?,?,?)",(symbol,row['start_at'],canonical(pure),row['received_at']))
            conn.execute("INSERT OR REPLACE INTO native_meta VALUES('last_capture',?)",(canonical({"at":capture['received_at'],"sha256":sha(capture),"quotes":capture['quotes'],"features":features,"venue":RULES['venue']}),))
            conn.execute("INSERT OR REPLACE INTO native_meta VALUES('last_error','')")
            # Raw bodies are durably deduplicated above, not repeated in journal events.
            receipts=[{k:v for k,v in r.items()if k!='raw_body_utf8'}for r in capture['receipts']]
            self._event(conn,"market_capture",{"capture_sha256":sha(capture),"receipts":receipts,"features":features},at.isoformat())
            for account in conn.execute("SELECT * FROM native_books ORDER BY book").fetchall():
                book=account['book']
                if account['rules_sha256']!=RULES_SHA:raise ValueError("Installed rule mismatch")
                old_cycle=conn.execute("SELECT * FROM native_cycles WHERE book=? AND day=?",(book,day)).fetchone()
                if old_cycle and old_cycle['status']=='completed':continue
                if old_cycle and old_cycle['signal_sha256']!=sha(features):
                    # Receipt timestamps legitimately change on reread; financial operand identity is what binds the daily decision.
                    old_features=json.loads(old_cycle['features'])
                    semantic=lambda f:{s:{k:v for k,v in r.items()if k!='signal_received_at'}for s,r in f.items()}
                    if semantic(old_features)!=semantic(features):
                        self._event(conn,"cycle_signal_conflict",{"day":day},at.isoformat(),book);continue
                weights=[w if market[s]['gate']else 0 for s,w in zip(SYMBOLS,BOOK_WEIGHTS[book])]
                def state():
                    cash=conn.execute("SELECT cash FROM native_books WHERE book=?",(book,)).fetchone()[0]
                    quantities={r['symbol']:r['quantity']for r in conn.execute("SELECT * FROM native_positions WHERE book=?",(book,))}
                    return cash,quantities
                cash,quantities=state()
                targets=funded_targets(cash,quantities,market,weights)
                # Outside a valid entry window or when disabled, service only gate-off owned exits.
                for symbol in SYMBOLS:
                    held=number(quantities.get(symbol,'0'),True)
                    goal=targets[symbol]if inside and account['enabled']else (Decimal(0)if not market[symbol]['gate']else held)
                    if held>goal:
                        fills+=int(self._fill(conn,book,day,symbol,'sell',held-goal,market,clock(now).isoformat()))
                # Actual committed-in-transaction sale results are reread before increases.
                cash,quantities=state()
                if inside and account['enabled']:
                    targets=funded_targets(cash,quantities,market,weights)
                    for symbol in SYMBOLS:
                        held=number(quantities.get(symbol,'0'),True)
                        desired=targets[symbol]-held
                        if desired>0:
                            # Reconcile the precise rounded-up paper fee, never a projected sale credit.
                            cash=number(state()[0],True);price=market[symbol]['ask'];lot=market[symbol]['lot']
                            affordable=(cash/(price*(1+FEE))/lot).to_integral_value(rounding=ROUND_DOWN)*lot
                            quantity=min(desired,affordable)
                            while quantity>0 and quantity*price+(quantity*price*FEE).quantize(MONEY_QUANTUM,rounding=ROUND_UP)>cash:
                                quantity-=lot
                            if quantity>0:fills+=int(self._fill(conn,book,day,symbol,'buy',quantity,market,clock(now).isoformat()))
                    status='completed'
                else:status='expired_or_entries_disabled'
                conn.execute("INSERT INTO native_cycles VALUES(?,?,?,?,?,?) ON CONFLICT(book,day)DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at",
                    (book,day,status,sha(features),canonical(features),at.isoformat()))
                cash,quantities=state()
                nav=number(cash,True)+sum(number(quantities.get(s,'0'),True)*market[s]['mid']for s in SYMBOLS)
                observed_weights={s:str(number(quantities.get(s,'0'),True)*market[s]['mid']/nav if nav else 0)for s in SYMBOLS}
                self._event(conn,"daily_decision",{"day":day,"status":status,"weights":weights,"features":features,
                    "actual_cash":cash,"postfill_mid_nav":str(nav),"actual_weights":observed_weights,
                    "rounding_policy":"Venue lot floors, rounded-up declared fees and sub-minimum dust may leave small cash/weight tracking differences",
                    "opening_window_met":inside},at.isoformat(),book)
            self.verify_ledger(conn)
            conn.commit()
        return {"status":"completed"if inside else "observed_missed_entry_window","fills":fills,"paper_only":True,"at":at.isoformat()}

    def heartbeat(self,running=True):
        stamp=clock().isoformat()
        payload={"at":stamp,"pid":os.getpid(),"process_start":Path('/proc/self/stat').read_text().split()[21],
                 "running":bool(running),"scope":"This process; no host-boot persistence claimed"}
        with self.connect()as conn:
            conn.execute("INSERT OR REPLACE INTO native_meta VALUES('worker',?)",(canonical(payload),))

    def serve(self,interval=30,stop=None):
        if interval<5:raise ValueError("Worker interval must be at least5seconds")
        stop=stop or threading.Event()
        with self.path.with_suffix(self.path.suffix+'.worker.lock').open('a+')as lease:
            try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError("Another native prospective worker owns this database")
            try:
                while not stop.is_set():
                    self.heartbeat()
                    try:self.run_once()
                    except Exception as exc:
                        with self.connect()as conn:
                            conn.execute("BEGIN IMMEDIATE")
                            self._event(conn,'runtime_block',{'error':str(exc),'financial_mutations':False},clock().isoformat())
                            conn.execute("INSERT OR REPLACE INTO native_meta VALUES('last_error',?)",(str(exc),))
                            conn.commit()
                    self.heartbeat()
                    stop.wait(interval)
            finally:self.heartbeat(False)


def read_status(db_path=None):
    path=Path(db_path or default_path())
    base={"paper_only":True,"execution_scope":"Independent Coinbase USD spot local-paper companion",
          "database":str(path),"rules_sha256":RULES_SHA,"installed_count":0,"enabled_count":0,"books":[],
          "broker_orders":0,"future_profitability_proved":False}
    if not path.is_file():return {**base,"status":"not_installed","worker":{"running":False}}
    try:
        conn=sqlite3.connect("file:"+urllib.parse.quote(str(path.resolve()))+"?mode=ro",uri=True,timeout=5)
        conn.row_factory=sqlite3.Row
        with conn:
            accounts=conn.execute("SELECT * FROM native_books ORDER BY book").fetchall()
            meta={r['key']:r['value']for r in conn.execute("SELECT * FROM native_meta")}
            capture=json.loads(meta['last_capture'])if meta.get('last_capture')else None
            for account in accounts:
                positions={r['symbol']:r['quantity']for r in conn.execute("SELECT * FROM native_positions WHERE book=?",(account['book'],))if number(r['quantity'],True)>0}
                fills=conn.execute("SELECT count(*)FROM native_fills WHERE book=?",(account['book'],)).fetchone()[0]
                last=conn.execute("SELECT day,status,updated_at FROM native_cycles WHERE book=? ORDER BY day DESC LIMIT 1",(account['book'],)).fetchone()
                base['books'].append({"sleeve":account['book'],"enabled":bool(account['enabled']),"cash":account['cash'],
                    "virtual_principal":account['principal'],"positions":positions,"fills":fills,"pending_orders":0,
                    "latest_cycle":dict(last)if last else None,"rules_sha256":account['rules_sha256']})
                if capture:
                    marked=number(account['cash'],True)+sum(number(q,True)*(number(capture['quotes'][s]['bid'])+number(capture['quotes'][s]['ask']))/2 for s,q in positions.items())
                    base['books'][-1].update(last_observed_mid_nav=str(marked),mark_received_at=capture['at'],
                        mark_scope='Received bid/ask midpoint; excludes unfilled liquidation cost, not a broker account value')
            base['installed_count']=len(accounts);base['enabled_count']=sum(bool(r['enabled'])for r in accounts)
            worker=json.loads(meta['worker'])if meta.get('worker')else {'running':False}
            if worker.get('at'):
                worker['heartbeat_age_seconds']=(clock()-clock(worker['at'])).total_seconds()
                worker['stale']=worker['heartbeat_age_seconds']>120
                try:alive=Path('/proc/'+str(worker['pid'])+'/stat').read_text().split()[21]==worker['process_start']
                except (OSError,KeyError,IndexError):alive=False
                worker['process_alive']=alive
                worker['running']=bool(worker.get('running'))and not worker['stale']and alive
            return {**base,"status":"installed"if accounts else 'empty','worker':worker,
                "market_data":capture,"last_error":meta.get('last_error')or None,
                "journal_events":conn.execute("SELECT count(*)FROM native_events").fetchone()[0]}
    except (sqlite3.Error,ValueError,TypeError,KeyError,AttributeError)as exc:
        return {**base,"status":"unavailable","error":str(exc),"worker":{"running":False}}
    finally:
        if 'conn'in locals():conn.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=default_path())
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    install=sub.add_parser('install');install.add_argument('--enable',action='store_true')
    for action in ['enable','disable']:
        change=sub.add_parser(action);change.add_argument('--book',choices=list(BOOK_WEIGHTS),required=True)
    sub.add_parser('run')
    serve=sub.add_parser('serve');serve.add_argument('--interval',type=int,default=30)
    capture=sub.add_parser('capture');capture.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='status':result=read_status(args.db)
    elif args.command=='capture':
        result=CoinbasePublicFeed().capture();args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');result={'status':'captured','path':str(args.output),'sha256':sha(result),'paper_orders':0}
    else:
        desk=NativeProspectiveDesk(args.db)
        if args.command=='install':result=desk.install(args.enable)
        elif args.command in ['enable','disable']:result=desk.set_enabled(args.book,args.command=='enable')
        elif args.command=='run':result=desk.run_once()
        else:
            stop=threading.Event()
            for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,lambda *_:stop.set())
            desk.serve(args.interval,stop);result=read_status(args.db)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
