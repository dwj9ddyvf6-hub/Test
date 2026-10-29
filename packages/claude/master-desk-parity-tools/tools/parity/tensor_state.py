"""tensor_state parity: the two ported pieces of the Ausar Tensor state-repair books against the source itself.

  * book — N_BOOK randomized operation sequences on one strategy-owned local book (quotes fresh / stale / future /
    historical, strategy buys and sells with frozen max debits, opening windows and expiries, fill passes across
    sessions, settlement releases, split / dividend events through TensorActions, verified payments, account and
    settled-cash reads): source backend/trading.py TradingDesk (+ store.py, settlement_calendar.py,
    providers.exchange_calendar on exchange_calendars XNYS) vs desk/feedlib/ts_bridge.py TradingBridge (+ DeskXNYS).
    Compared after every operation: its result or error text, the book's cash / realized / fees, every intent
    (status, fills, reservations, windows, errors), fill (price, notional, realized, clocks, quote provenance),
    position, debit limit, settlement claim, corporate action, receivable, fractional claim and payment, and on
    reads the account (equity, marks, settled / available cash, coverage) and strategy_cash.
  * provider — N_PROVIDER randomized Yahoo v8 chart responses (weekly / hourly bars with missing, invalid,
    inconsistent, Boolean, duplicate, unordered and future rows, identity / interval changes, regular-session and
    market-time metadata, quote metadata) through bars(), native_bars_since() and refresh(): source
    backend/providers.py Providers (kind yahoo, its clock pinned) vs desk/feedlib/ts_yahoo.py YahooNative; compared:
    the returned payload (revision id, content hash, bars, omissions, request window, provenance) or the error, and
    stored quotes.
TensorRuntime, TensorActions, the policy and the engine are the vendored source bytes and run on both sides.
Record ids are drawn in creation order on both sides (the source's uuid4 ids order same-clock intents at random:
both serve active intents ORDER BY created_at, id), and the book id is left out of the compared rows.

The source files are read from TS_SOURCE_TREE (a directory holding the artifacts commit's backend/ files; each is
verified against its pinned git blob before use); exchange_calendars (the source's calendar) from XCALS_SITE:

    TS_SOURCE_TREE=/path/to/tree XCALS_SITE=/path/to/site python3 -m tools.parity.run tensor_state"""
import hashlib
import json
import os
import random
import sys
import tempfile
import types
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from tools.parity import ROOT, write_receipt

UTC = timezone.utc
N_BOOK = int(os.environ.get("TS_BOOK_CASES", "1200"))
N_PROVIDER = int(os.environ.get("TS_PROVIDER_CASES", "1200"))
SOURCE_BLOBS = {"__init__.py": "75190783b9987fad367766435f23743cbe72c11c",
                "store.py": "0c240db423da39ff1181d535669d9fa88ed83c11",
                "strategy_contract.py": "e1cbd9bf9330b78aa3097a5e1fefc07ba538f3ed",
                "trading.py": "2fd1fe56648e4b0bc9d4efafb41a1e43269cf3bc",
                "tensor_actions.py": "e2c4f543bfb0fb4e764f76160db329e8b8cbd5d5",
                "providers.py": "f61d414e4cbab2d04f9692787b6402375fd5e0c3",
                "http_transport.py": "2f2a35f90402309e63ce976127aa147bc8fa6d5a",
                "bar_revision_codec.py": "e398b24baa4a0c36d70af131eabe993bc1c72555",
                "settlement_calendar.py": "5241b3a7a2933ad6969b10b780f773517330e5ee"}
START, END = date(2024, 6, 3), date(2026, 9, 18)          # T+1 sales inside the frozen settlement calendar
SYMS = ("AAA", "BBB", "CCC")
GOOD = "Yahoo Finance quote (provider timestamp; may be delayed)"

# ------------------------------------------------------------------------------------------------ the driver
DRIVER = r'''
import hashlib, itertools, json
from datetime import datetime, timezone
UTC = timezone.utc
INSTALL = "tensor_state_repair_1wk_r12"
_IDS = itertools.count(1)


def ident():
    """record ids in creation order (uuid4 order is random on both sides: same-clock intents are served
    ORDER BY created_at,id)"""
    return "%032x" % next(_IDS)


def _t(s):
    return datetime.fromisoformat(s)


def _err(exc):
    return ["error", type(exc).__name__, getattr(exc, "detail", None) or str(exc)[:300]]


def events_transport(method, url, payload, headers):
    """Yahoo chart events for TensorActions probes: the listing identity and no events (events are explicit ops)."""
    from urllib.parse import unquote, urlsplit
    sym = unquote(urlsplit(url).path.rsplit("/", 1)[1])
    return {"chart": {"result": [{"meta": {"symbol": sym, "currency": "USD"}, "events": {}}], "error": None}}


def snapshot(A):
    with A.store.connect() as con:
        q = lambda sql, *a: [dict(r) for r in con.execute(sql, a)]
        out = {
            "book": q("SELECT cash_cents,realized_cents,fees_cents FROM p_books WHERE id=?", A.book),
            "intents": q("SELECT symbol,side,quantity,order_type,time_in_force,status,filled_quantity,filled_notional_cents,fees_cents,reserved_cents,reserved_quantity,error,not_before,expires_at,session_open,session_close,session_date,completed_at,created_at,updated_at,sleeve,source FROM p_intents WHERE book_id=? ORDER BY rowid", A.book),
            "fills": q("SELECT symbol,side,quantity,price,notional_cents,fee_cents,realized_cents,timestamp,observed_at,source,quote_as_of,quote_source FROM p_fills WHERE book_id=? ORDER BY rowid", A.book),
            "positions": q("SELECT symbol,quantity,cost_cents,realized_cents,sleeve,source,locked,updated_at FROM p_positions WHERE book_id=? ORDER BY symbol", A.book),
            "limits": q("SELECT l.installation_id,l.max_debit_cents,l.reference_price,l.quote_as_of,l.created_at FROM a_strategy_intent_limits l JOIN p_intents i ON i.id=l.intent_id WHERE i.book_id=? ORDER BY i.rowid", A.book),
            "settlements": q("SELECT amount_cents,release_at,created_at,released_at FROM a_strategy_settlements WHERE book_id=? ORDER BY rowid", A.book),
            "receipts": q("SELECT r.policy_version,r.definition,r.created_at FROM a_strategy_settlement_policy_receipts r JOIN a_strategy_settlements s ON s.fill_id=r.fill_id WHERE s.book_id=? ORDER BY s.rowid", A.book),
            "actions": q("SELECT symbol,kind,effective_at,definition,source,observed_at,status,payload,applied_at FROM a_strategy_actions WHERE book_id=? ORDER BY rowid", A.book),
            "receivables": q("SELECT symbol,entitled_quantity,amount_cents,status FROM a_strategy_receivables WHERE book_id=? ORDER BY rowid", A.book),
            "claims": q("SELECT symbol,quantity,basis_cents,status FROM a_strategy_fractional_claims WHERE book_id=? ORDER BY rowid", A.book),
            "payments": q("SELECT amount_cents,payment_at,source,evidence_sha256 FROM a_strategy_action_payments WHERE book_id=? ORDER BY rowid", A.book),
        }
    for a in out["actions"]:
        p = json.loads(a["payload"])
        p["cancelled_intent_ids"] = len(p.get("cancelled_intent_ids", []))
        a["payload"] = p
    return out


ACCOUNT_KEYS = ("cash", "equity", "market_value", "missing_marks", "stale_marks", "unsettled_cash", "settled_cash",
                "available_cash", "dividend_receivable", "fractional_claim_market_value", "exact_market_value_cents",
                "exact_equity_cents", "corporate_action_coverage", "reserved_cash", "gross_exposure")


def account(A, t, release):
    if release:
        with A.store.transaction() as con:
            cash = A.trading.strategy_cash(con, A.book, t, release=True)
    with A.store.connect() as con:
        book = A.trading._book(con, A.book)
        acct, positions = A.trading._account(con, book, t)
        if not release:
            cash = A.trading.strategy_cash(con, A.book, t, release=False)
    return {"account": {k: acct.get(k) for k in ACCOUNT_KEYS},
            "positions": [{k: p.get(k) for k in ("symbol", "quantity", "market_value", "quote_fresh", "mark_price")} for p in positions],
            "cash": cash}


def step(A, op):
    t, kind = _t(op["t"]), op["op"]
    try:
        if kind == "quote":
            with A.store.transaction() as con:
                con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)", (op["symbol"], op["price"], op["as_of"], op["source"]))
            return ["ok"]
        if kind == "submit":
            payload = dict(op["payload"], book_id=A.book)
            row = A.trading.submit_strategy_intent(payload, op["install"], clock=t)
            return ["ok", row["status"]]
        if kind == "process":
            res = A.process(t)
            return ["ok", res["processed"], res["fills"], [e["detail"] if isinstance(e, dict) else e for e in res["errors"]]]
        if kind == "account":
            return ["ok", account(A, t, op.get("release", False))]
        if kind == "probe":
            res = A.actions.probe_symbols([op["symbol"]], clock=t)
            return ["ok", res["checked"], len(res["errors"])]
        if kind == "action":
            res = A.actions.apply_event(A.book, op["symbol"], op["event"], "parity event source", t)
            return ["ok", res.get("status"), bool(res.get("idempotent"))]
        if kind == "pay":
            with A.store.connect() as con:
                ids = [r[0] for r in con.execute("SELECT id FROM a_strategy_actions WHERE book_id=? ORDER BY rowid", (A.book,))]
            if not ids:
                return ["no-action"]
            evidence = hashlib.sha256(op["evidence"].encode()).hexdigest()
            res = A.actions.record_verified_payment(ids[op["index"] % len(ids)], _t(op["payment_at"]), "parity payment source",
                                                    evidence, amount_cents=op["amount_cents"], clock=t)
            return ["ok", res["amount_cents"], res["payment_at"]]
        raise AssertionError(kind)
    except Exception as exc:
        return _err(exc)


def drive(A, ops):
    out = []
    for op in ops:                       # quotes / probes write tables whose effects the next snapshot reveals
        r = step(A, op)
        out.append({"result": r, "state": None if op["op"] in ("quote", "probe") else snapshot(A)})
    return out
'''

SOURCE_BOOK = r'''
import os, sys, tempfile, types
sys.path.insert(0, PAYLOAD["xcals"])
httpx = types.ModuleType("httpx")
httpx.HTTPError = type("HTTPError", (Exception,), {})
httpx.AsyncClient = None
sys.modules["httpx"] = httpx
from backend.store import Store
from backend.trading import TradingDesk
from backend import providers as P
from backend.tensor_actions import TensorActions
import backend.trading as TR
exec(PAYLOAD["driver"])
TR.identifier = ident


class Prov:
    @staticmethod
    def calendar(clock=None):
        return P.exchange_calendar(clock)


def make(path):
    store = Store(path)
    trading = TradingDesk(store)
    book = trading.create_book({"name": "Tensor weekly state repair", "kind": "forward", "broker": "local",
                                "description": "R12 frozen independent strategy; virtual paper capital only"})["id"]
    with store.transaction() as con:                      # TensorRuntime.install claims inside its writer
        trading.claim_strategy_book(book, INSTALL, con=con)
    trading.set_book(book, {"policy": {"allow_short": False, "fees_per_order": 0, "slippage_bps": 10}})
    trading.fund_book(book, 100000, "r12-opening-capital-WSTATE")
    actions = TensorActions(store, trading, None, transport=events_transport)
    return types.SimpleNamespace(store=store, trading=trading, actions=actions, book=book,
                                 process=lambda t: trading.process(Prov, t))


import shutil
out, BATCH_TMP = [], tempfile.mkdtemp(prefix="parity-tensor-state-")
try:
    for case in PAYLOAD["cases"]:
        out.append(drive(make(os.path.join(tempfile.mkdtemp(dir=BATCH_TMP), "s.sqlite3")), case["ops"]))
finally:
    shutil.rmtree(BATCH_TMP, ignore_errors=True)
print(json.dumps(out, default=str))
'''


def desk_book(path, transport, ident=None):
    from desk.feedlib import ts_source as TS
    from desk.feedlib import ts_bridge as TB
    from desk.feedlib.ts_bridge import Store, TradingBridge
    TS.install_shims()
    if ident is not None:
        TB.identifier = ident
    ta = TS.vendored()["tensor_actions"]
    store = Store(path)
    trading = TradingBridge(store)
    book = trading.create_book("Tensor weekly state repair", 10000000, "r12-opening-capital-WSTATE")
    trading.claim_strategy_book(book, "tensor_state_repair_1wk_r12")
    actions = ta.TensorActions(store, trading, None, transport=transport)
    return types.SimpleNamespace(store=store, trading=trading, actions=actions, book=book, process=lambda t: trading.process(t))


def book_case(seed):
    """session episodes: entries queued for an opening window (or immediate), fresh / stale / historical quotes and
    action probes, fill passes inside, at the edge of and after the window, sales of held (and unheld) units,
    split / dividend events, verified payments, account and settled-cash reads, and settlement across sessions."""
    from desk.feedlib.r19_source import DeskXNYS
    rnd = random.Random(seed)
    cal = DeskXNYS()
    s = cal.date_to_session((START + timedelta(days=rnd.randrange((END - START).days))).isoformat(), direction="next")
    sessions = [s]
    while len(sessions) < 6:
        sessions.append(cal.next_session(sessions[-1]))
    opens = [cal.session_open(x).to_pydatetime().astimezone(UTC) for x in sessions]
    closes = [cal.session_close(x).to_pydatetime().astimezone(UTC) for x in sessions]
    syms = rnd.sample(SYMS, rnd.randint(1, 3))
    px = {x: Decimal(str(round(rnd.uniform(3, 260), 2))) for x in syms}
    bought = {x: 0 for x in syms}
    ops, cids, k = [], [], [0]

    def quote(t, sym, age=0, src=GOOD):
        px[sym] = max(Decimal("0.5"), (px[sym] * Decimal(str(1 + rnd.gauss(0, 0.01)))).quantize(Decimal(rnd.choice(("0.01", "0.01", "0.0001")))))
        ops.append({"op": "quote", "t": t.isoformat(), "symbol": sym, "price": str(px[sym]),
                    "as_of": (t - timedelta(seconds=age)).isoformat(), "source": src})

    def submit(t, sym, side, window):
        k[0] += 1
        if side == "buy":
            budget = Decimal(rnd.choice((2500, 10000, 10000, 30000, 200000)))
            qty = int(budget / (px[sym] * Decimal("1.001")))
            qty = rnd.choices((qty, max(1, qty // 3), "2.5", 0), (70, 22, 4, 4))[0] if qty > 0 else 1
        else:
            held = bought[sym]
            qty = rnd.choices((held, max(1, held // 2), held + 1, 3), (55, 25, 10, 10))[0] or 1
        payload = {"symbol": sym, "side": side, "quantity": qty, "order_type": "market", "time_in_force": "day",
                   "sleeve": "WSTATE", "reason": "Frozen deterministic Tensor research rule; local observed quote simulation"}
        if window is not None:
            payload.update(not_before=window[0].isoformat(), expires_at=window[1].isoformat())
        if side == "buy" and isinstance(qty, int) and qty > 0:
            if rnd.random() < 0.85:
                est = Decimal(qty) * px[sym] * Decimal("1.001") * 100
                payload["max_debit_cents"] = max(1, int(est * Decimal(str(rnd.choice((0.995, 1.0, 1.0001, 1.0005, 1.01, 1.2))))))
            bought[sym] += qty
        if cids and rnd.random() < 0.08:
            payload["client_id"] = rnd.choice(cids)
        else:
            payload["client_id"] = "tensor-%d-%d" % (seed, k[0])
            cids.append(payload["client_id"])
        ops.append({"op": "submit", "t": t.isoformat(), "payload": payload,
                    "install": "tensor_state_repair_1wk_r12" if rnd.random() < 0.98 else "tensor_state_repair_1h_r12"})

    for si in range(len(sessions)):
        if rnd.random() < 0.25:
            continue                                                     # a quiet session
        o, c = opens[si], closes[si]
        window = (o, o + timedelta(seconds=300))
        pre = o - timedelta(seconds=rnd.choice((60, 1)))
        for sym in rnd.sample(syms, rnd.randint(1, len(syms))):
            if rnd.random() < 0.85:
                ops.append({"op": "probe", "t": pre.isoformat(), "symbol": sym})
            quote(pre, sym, age=rnd.choice((0, 0, 0, 2, 400)), src=GOOD if rnd.random() < 0.95 else "historical daily bar")
            side = "buy" if bought[sym] == 0 or rnd.random() < 0.35 else "sell"
            submit(pre, sym, side, window if rnd.random() < 0.8 else None)
        for _ in range(rnd.randint(1, 4)):
            t = o + timedelta(seconds=rnd.choice((0, 1, 31, 120, 299, 300, 301, 3600)))
            for sym in syms:
                if rnd.random() < 0.85:
                    ops.append({"op": "probe", "t": t.isoformat(), "symbol": sym})
                if rnd.random() < 0.8:
                    quote(t, sym, age=rnd.choice((0, 0, 0, 1, 301, -3)) if t >= o else 0)
            if rnd.random() < 0.15:
                sym = rnd.choice(syms)
                submit(t, sym, rnd.choice(("buy", "sell")), (t, t + timedelta(seconds=300)) if rnd.random() < 0.7 else None)
            ops.append({"op": "process", "t": t.isoformat()})
            if rnd.random() < 0.3:
                ops.append({"op": "account", "t": t.isoformat(), "release": rnd.random() < 0.5})
        if rnd.random() < 0.25:
            t = c + timedelta(seconds=rnd.choice((-61, -1, 0, 1, 600)))
            for sym in syms:
                ops.append({"op": "probe", "t": t.isoformat(), "symbol": sym})
                quote(t, sym)
            ops.append({"op": "process", "t": t.isoformat()})
        if rnd.random() < 0.3:
            sym = rnd.choice(syms)
            day = sessions[si] if rnd.random() < 0.8 else sessions[min(si + 1, len(sessions) - 1)]
            t = o + timedelta(seconds=rnd.choice((3600, 7200)))
            if rnd.random() < 0.5:
                a, b = rnd.choice(((2, 1), (3, 2), (1, 2), (1, 3), (3, 1), (5, 4)))
                event = {"kind": "split", "date": str(day.date()), "numerator": a, "denominator": b}
            else:
                event = {"kind": "dividend", "date": str(day.date()), "amount": str(rnd.choice((Decimal("0.05"), Decimal("0.37"), Decimal("1.2"))))}
            ops.append({"op": "action", "t": t.isoformat(), "symbol": sym, "event": event})
            if event["kind"] == "split" and rnd.random() < 0.6:
                quote(t, sym)
                if rnd.random() < 0.5:
                    ops.append({"op": "pay", "t": t.isoformat(), "index": rnd.randrange(4), "evidence": "e%d" % len(ops),
                                "payment_at": t.isoformat(), "amount_cents": rnd.randint(0, 5000)})
        if rnd.random() < 0.3:
            t = o + timedelta(seconds=rnd.choice((7200, 10800)))
            ops.append({"op": "pay", "t": t.isoformat(), "index": rnd.randrange(4), "evidence": "e%d" % len(ops),
                        "payment_at": (t - timedelta(seconds=rnd.choice((0, 60, 86400, -60)))).isoformat(),
                        "amount_cents": rnd.choice((None, None, 0, rnd.randint(1, 5000)))})
        if rnd.random() < 0.4:
            ops.append({"op": "account", "t": (c + timedelta(seconds=rnd.choice((1, 3600)))).isoformat(), "release": rnd.random() < 0.5})
    ops.append({"op": "account", "t": (opens[-1] + timedelta(days=3)).isoformat(), "release": True})
    return {"seed": seed, "ops": ops}


# ------------------------------------------------------------------------------------------------ provider
PROVIDER_DRIVER = r'''
import json
from datetime import datetime, timezone
from decimal import Decimal
UTC = timezone.utc


def pdrive(P, case):
    out = []
    for call in case["calls"]:
        P.responses[:] = [call["response"]]
        P.now[0] = call["now"]
        try:
            if call["kind"] == "bars":
                res = P.provider.bars(call["symbol"], call["range"], call["interval"])
            elif call["kind"] == "since":
                res = P.provider.native_bars_since(call["symbol"], datetime.fromtimestamp(call["anchor"], UTC), "60m")
            else:
                res = P.provider.refresh(call["symbols"])
            out.append(["ok", json.loads(json.dumps(res, sort_keys=True, default=str)), P.urls[-1] if P.urls else None])
        except Exception as exc:
            out.append(["error", type(exc).__name__, getattr(exc, "detail", None) or str(exc)[:200]])
        with P.store.connect() as con:
            out.append(["quotes", [dict(r) for r in con.execute("SELECT * FROM quotes ORDER BY symbol")]])
    return out
'''

SOURCE_PROVIDER = r'''
import os, sys, tempfile, types
sys.path.insert(0, PAYLOAD["xcals"])
httpx = types.ModuleType("httpx")
httpx.HTTPError = type("HTTPError", (Exception,), {})
httpx.AsyncClient = None
sys.modules["httpx"] = httpx
os.environ["ASTER_MARKET_DATA"] = "yahoo"
os.environ["ASTER_BAR_FALLBACK"] = "none"
from datetime import datetime as _dt, timezone as _tz
from backend.store import Store
from backend import providers as PR
exec(PAYLOAD["driver"])
NOW = [0.0]


class Clock(_dt):
    @classmethod
    def now(cls, tz=None):
        return _dt.fromtimestamp(NOW[0], tz or _tz.utc)


PR.datetime = Clock                                   # the provider's (and its store's) wall clock, pinned per call
import backend.store as ST
ST.datetime = Clock


def make(path):
    store = Store(path)
    responses, urls = [], []

    def transport(method, url, payload, headers):
        urls.append(url)
        r = responses[0]
        if r.get("raise"):
            raise PR.ProviderError("Provider request failed or returned invalid data")
        return r["body"]
    return types.SimpleNamespace(store=store, provider=PR.Providers(store, transport=transport), responses=responses,
                                 urls=urls, now=NOW)


import shutil
out, BATCH_TMP = [], tempfile.mkdtemp(prefix="parity-tensor-state-")
try:
    for case in PAYLOAD["cases"]:
        out.append(pdrive(make(os.path.join(tempfile.mkdtemp(dir=BATCH_TMP), "p.sqlite3")), case))
finally:
    shutil.rmtree(BATCH_TMP, ignore_errors=True)
print(json.dumps(out, default=str))
'''


def desk_provider(path):
    from desk.feedlib.ts_bridge import Store
    from desk.feedlib.ts_yahoo import ProviderError, YahooNative
    store = Store(path)
    responses, urls, now = [], [], [0.0]

    def transport(method, url, payload, headers):
        urls.append(url)
        r = responses[0]
        if r.get("raise"):
            raise ProviderError("Provider request failed or returned invalid data")
        return r["body"]
    return types.SimpleNamespace(store=store, provider=YahooNative(store, lambda: now[0], transport=transport),
                                 responses=responses, urls=urls, now=now)


def _chart(rnd, sym, interval, now, n):
    """a Yahoo v8 chart body with randomized defects."""
    step = 7 * 86400 if interval == "1wk" else 3600
    if interval == "1wk":
        last = datetime.fromtimestamp(now, UTC)
        from desk.util import ET
        local = last.astimezone(ET).date()
        monday = local - timedelta(days=local.weekday())
        t0 = int(datetime(monday.year, monday.month, monday.day, tzinfo=ET).timestamp()) - (n - 1) * step
    else:
        t0 = int(now) - (int(now) - 1800) % 3600 - (n - 1) * step         # half-hour stamps, the last <= now
    ts = [t0 + i * step for i in range(n)]
    q = {k: [] for k in ("open", "high", "low", "close", "volume")}
    px = rnd.uniform(5, 200)
    for _ in ts:
        o = px
        c = px * (1 + rnd.gauss(0, 0.02))
        h, l = max(o, c) * 1.01, min(o, c) * 0.99
        for k, v in zip(("open", "high", "low", "close", "volume"), (o, h, l, c, rnd.randint(10**5, 10**7))):
            q[k].append(round(v, 4) if k != "volume" else v)
        px = c
    for _ in range(rnd.choice((0, 0, 0, 1, 2)) if n else 0):            # defects
        i, kind = rnd.randrange(n), rnd.choice(("none", "zero", "inverted", "bool", "neg_volume", "nan"))
        if kind == "none":
            q[rnd.choice(("open", "close"))][i] = None
        elif kind == "zero":
            q["low"][i] = 0
        elif kind == "inverted":
            q["high"][i] = q["low"][i] * 0.9
        elif kind == "bool":
            q["close"][i] = True
        elif kind == "neg_volume":
            q["volume"][i] = -5
        else:
            q["open"][i] = float("nan")
    if rnd.random() < 0.05 and n > 2:
        ts[1] = ts[0]                                        # duplicate timestamp
    if rnd.random() < 0.04 and n:
        ts[-1] = int(now) + 3600                             # a future row
    meta = {"symbol": sym, "currency": "USD", "instrumentType": rnd.choice(("EQUITY", "EQUITY", "ETF")),
            "dataGranularity": interval if rnd.random() > 0.03 else "1d", "exchangeTimezoneName": "America/New_York",
            "regularMarketTime": int(now) - rnd.choice((1, 30, 400)), "regularMarketPrice": round(px, 4)}
    if rnd.random() < 0.03:
        meta["currency"] = "CAD"
    if rnd.random() < 0.03:
        meta["symbol"] = sym + "X"
    if interval == "60m" and rnd.random() < 0.8:
        meta["currentTradingPeriod"] = {"regular": {"start": int(now) - 3600, "end": int(now) + 3600, "timezone": "EDT", "gmtoffset": -14400}}
    body = {"chart": {"result": [{"meta": meta, "timestamp": ts, "indicators": {"quote": [q], "adjclose": [{"adjclose": list(q["close"])}]}}], "error": None}}
    if rnd.random() < 0.03:
        body = {"chart": {"result": [], "error": {"code": "Not Found"}}}
    return body


def provider_case(seed):
    rnd = random.Random(10_000 + seed)
    now = datetime(2025, 3, 3, 15, tzinfo=UTC).timestamp() + rnd.randrange(0, 500 * 86400)
    sym = rnd.choice(("AAA", "BRK.B", "MSFT"))
    calls = []
    for _ in range(rnd.randint(1, 4)):
        now += rnd.choice((0, 30, 59, 61, 3600))
        kind = rnd.choices(("bars", "since", "refresh"), (5, 2, 2))[0]
        if kind == "refresh":
            body = _chart(rnd, sym.replace(".", "-"), "1m", now, 0)
            calls.append({"kind": "refresh", "symbols": [sym], "now": now,
                          "response": {"raise": rnd.random() < 0.05, "body": body}})
            continue
        interval = "1wk" if kind == "bars" and rnd.random() < 0.6 else "60m"
        rng = "max" if interval == "1wk" and rnd.random() < 0.5 else rnd.choice(("1mo", "6mo", "2y"))
        body = _chart(rnd, sym.replace(".", "-"), interval, now, rnd.randint(1, 40))
        call = {"kind": kind, "symbol": sym, "range": rng, "interval": interval, "now": now,
                "response": {"raise": rnd.random() < 0.04, "body": body}}
        if kind == "since":
            call["anchor"] = int(now) - rnd.choice((3600, 86400, 10 * 86400, 800 * 86400))
        calls.append(call)
    return {"seed": seed, "calls": calls}


# ------------------------------------------------------------------------------------------------ run
def _tree():
    tree = os.environ.get("TS_SOURCE_TREE")
    site = os.environ.get("XCALS_SITE")
    if not tree or not os.path.isdir(os.path.join(tree, "backend")):
        raise SystemExit("set TS_SOURCE_TREE to a directory holding the source backend/ files")
    if not site or not os.path.isdir(site):
        raise SystemExit("set XCALS_SITE to a directory holding exchange_calendars")
    for name, blob in SOURCE_BLOBS.items():
        data = open(os.path.join(tree, "backend", name), "rb").read()
        if hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() != blob:
            raise SystemExit(f"source file {name} differs from its pinned blob {blob}")
    return tree, site


def _norm(x):
    return json.loads(json.dumps(x, sort_keys=True, default=str))


def _book_chunk(seeds):
    from tools.parity import old_run
    tree, site = _tree()
    ns = {}
    exec(DRIVER, ns)
    cases = [book_case(x) for x in seeds]
    from tools.parity.batch_tmp import batch_tmp
    with batch_tmp("parity-tensor-state-"):   # removed here even when the child fails, times out or is killed
        src = old_run(SOURCE_BOOK, {"xcals": site, "driver": DRIVER, "cases": cases}, timeout=7200, tree=tree)
    rows = []
    for c, s in zip(cases, src):
        with tempfile.TemporaryDirectory() as d:
            port = _norm(ns["drive"](desk_book(os.path.join(d, "b.sqlite3"), ns["events_transport"], ns["ident"]), c["ops"]))
        s = _norm(s)
        diff = None
        if s != port:
            k = next(i for i, (a, b) in enumerate(zip(s, port)) if a != b) if len(s) == len(port) else -1
            diff = {"part": "book", "seed": c["seed"], "op_index": k, "op": c["ops"][k] if k >= 0 else None,
                    "source": s[k] if k >= 0 else len(s), "port": port[k] if k >= 0 else len(port)}
        last = s[-1]["state"]
        rows.append({"seed": c["seed"], "diff": diff, "stats": {
            "ops": len(c["ops"]), "fills": len(last["fills"]), "buys": sum(f["side"] == "buy" for f in last["fills"]),
            "sells": sum(f["side"] == "sell" for f in last["fills"]), "errors": sum(r["result"][0] == "error" for r in s),
            "actions_applied": sum(a["status"] == "applied" for a in last["actions"]), "payments": len(last["payments"]),
            "fractional_claims": len(last["claims"]), "receivables": len(last["receivables"]),
            "settlements": len(last["settlements"]), "released": sum(x["released_at"] is not None for x in last["settlements"]),
            "expired": sum(i["status"] == "expired" for i in last["intents"]),
            "blocked": sum(i["status"] == "blocked" for i in last["intents"])}})
    return rows


def _provider_chunk(seeds):
    from tools.parity import old_run
    tree, site = _tree()
    ns = {}
    exec(PROVIDER_DRIVER, ns)
    cases = [provider_case(x) for x in seeds]
    from tools.parity.batch_tmp import batch_tmp
    with batch_tmp("parity-tensor-state-"):   # removed here even when the child fails, times out or is killed
        src = old_run(SOURCE_PROVIDER, {"xcals": site, "driver": PROVIDER_DRIVER, "cases": cases}, timeout=7200,
                      tree=tree)
    rows = []
    for c, s in zip(cases, src):
        with tempfile.TemporaryDirectory() as d:
            port = _norm(ns["pdrive"](desk_provider(os.path.join(d, "p.sqlite3")), c))
        s = _norm(s)
        diff = None
        if s != port:
            k = next((i for i, (a, b) in enumerate(zip(s, port)) if a != b), -1)
            diff = {"part": "provider", "seed": c["seed"], "index": k, "source": s[k] if k >= 0 else None,
                    "port": port[k] if k >= 0 else None}
        st = {"calls": 0, "ok": 0, "errors": 0, "omitted_rows": 0}
        for call, r in zip(c["calls"], s[::2]):
            st["calls"] += 1
            st["ok" if r[0] == "ok" else "errors"] += 1
            key = call["kind"] + ("_" + call["interval"] if call["kind"] == "bars" else "") + ("_ok" if r[0] == "ok" else "_error")
            st[key] = st.get(key, 0) + 1
            if r[0] == "ok" and isinstance(r[1], dict):
                st["omitted_rows"] += r[1].get("omitted_rows", 0) or 0
        rows.append({"seed": c["seed"], "diff": diff, "stats": st})
    return rows


def _chunked(name, fn, chunks):
    """run chunks one at a time (one source process alive at a time); PARITY_CKPT=<dir> keeps each finished
    chunk's rows so an interrupted run resumes where it stopped."""
    import json as _json
    ckpt = os.environ.get("PARITY_CKPT")
    if ckpt:
        os.makedirs(os.path.join(ckpt, name), exist_ok=True)
    rows = []
    for i, chunk in enumerate(chunks):
        path = os.path.join(ckpt, name, "%03d-%d.json" % (i, len(chunks))) if ckpt else None
        if path and os.path.exists(path):
            rows += _json.load(open(path))
            continue
        part = fn(chunk)
        if path:
            with open(path + ".tmp", "w") as f:
                _json.dump(part, f)
            os.replace(path + ".tmp", path)
        rows += part
    return rows


def run():
    _tree()
    n_chunks = int(os.environ.get("PARITY_CHUNKS", "24"))
    seeds = list(range(1, N_BOOK + 1))
    pseeds = list(range(1, N_PROVIDER + 1))
    book = _chunked("tensor_state_book", _book_chunk, [seeds[i::n_chunks] for i in range(n_chunks)])
    prov = _chunked("tensor_state_provider", _provider_chunk, [pseeds[i::8] for i in range(8)])
    diffs = [r["diff"] for r in sorted(book, key=lambda r: r["seed"]) + sorted(prov, key=lambda r: r["seed"]) if r["diff"]]
    stats, pstats = {}, {}
    for r in book:
        for k, v in r["stats"].items():
            stats[k] = stats.get(k, 0) + v
    for r in prov:
        for k, v in r["stats"].items():
            pstats[k] = pstats.get(k, 0) + v
    res = {"sleeve": "tensor_state", "cases": len(book) + len(prov), "identical": len(book) + len(prov) - len(diffs),
           "diffs": diffs[:20], "n_diffs": len(diffs),
           "parts": {"book": {"cases": len(book), "stats": stats}, "provider": {"cases": len(prov), "stats": pstats}},
           "sleeves": ["ausar_h1state", "ausar_wstate"],
           "source": {"tree": "codex-complete-archive 9de7747 digitalocean-pilot/2026-10-11/context/source/backend",
                      "blobs": SOURCE_BLOBS, "calendar": "exchange_calendars XNYS (XCALS_SITE)"},
           "port": "desk/feedlib/ts_bridge.py TradingBridge + desk/feedlib/ts_yahoo.py YahooNative",
           "named_divergences": {}}
    write_receipt("tensor_state", res)
    return res
