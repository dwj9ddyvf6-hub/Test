"""Ausar native Coinbase SMA200 books (family coinbase_sma200) — the two ORIGINAL Ausar companions of
prospective_native.py (agentic-trading-desk@1720157f, blob 39e02731), separate from the femto forward
fwd_coinbase_sma200 (femto-lean sleeves/fwd_coinbase_sma200.py: a fixed 0.01 BTC daily buy):

  ausar_eth_sma200_coinbase      ETH_SMA200      weights BTC-USD 0 / ETH-USD 1
  ausar_btc_eth_sma200_coinbase  BTC_ETH_SMA200  weights BTC-USD .5 / ETH-USD .5

The vendored, hash-pinned source decides the numbers: desk/vendor/ausar_native/prospective_native.py (funded_targets,
BOOK_WEIGHTS, FEE, RULES) and prospective_native_math.py (blob bc97b418: the R14 inclusive SMA200 gate). This wrapper
carries out its run_once() per book, every 30 s pass (the source worker's 30 s interval):
  * a symbol's market = exactly 200 contiguous completed native Coinbase UTC daily candles, the latest completing at
    today's 00:00 UTC opening; the gate is the latest close strictly above their inclusive SMA200; the product is
    online and unrestricted (Coinbase /products metadata: base_increment lot, quote_increment tick, min_market_funds);
    the bid/ask quote is no older than 30 s, on tick, uncrossed, and — for risk increases — the last trade no older
    than 30 s (an exit is serviced without the last-trade clock, as the source's degraded path does);
  * risk increases need every market qualified (the BTC market too for the ETH-only book);
  * inside 00:00:00-00:05:00 UTC with every market qualified: absolute targets from funded_targets (the post-fee NAV
    fixed point over mids, buys at the ask / sells at the bid, 0.2% fee, lot floors) frozen once per UTC day; owned
    amounts above target are sold first, then the shortfall is bought (affordable at the ask incl. fee, lot-floored);
    a day whose targets are met is completed and never repeats;
  * otherwise a symbol whose gate is off is sold in full at the bid, whatever the clock (the owned exit);
  * fills on the sim:coinbase book at the received bid / ask, the frozen 0.2% fee per side (cost_bps 20).

Removed (runtime plumbing / gates, not strategy rules): the book enable switch (always enabled), the raw-body /
receipt-hash / server-Date provenance checks, the provider-revision block (a revised completed candle blocked the
symbol), the same-day cycle_signal_conflict skip, the quote-after-signal-receipt clock.

Named divergences:
  C1 displayed depth: the source capped each paper fill at the received L1 size with same-sequence consumption (its
     R20 execution overlay); the desk's Coinbase quote carries no size, the sim venue fills the order at the touch.
  C2 same-pass sequencing: the source sold, re-read its cash and then bought inside one transaction; here the sells
     and the buys go out in the same pass, the buys sized on the cash after the sells' fill at the decision bid (the
     sim venue fills them at that same quote).
  C3 fees: 0.2% of the fill (cost_bps 20); the source rounded each fee up to $1e-8.
  C4 cycle status: the day's completion is observed on the next pass (positions at target), not inside the pass."""
import importlib.util
import os
import sys
import types
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_UP

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...data.http import get
from ...vendor.ausar_native import prospective_native_math as PNM

SOURCE = {"repo": "agentic-trading-desk", "ref": "aurelia-paper-desk", "commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
          "path": "ausar-archive/ausar-receiver/original-payload/desk-source/backend/prospective_native.py",
          "blob": "39e02731c47ffaee2e79c00ef2b13f9e66f7b59c", "math_blob": "bc97b4185fb25756c1ad2c0ecd9f42101b41f997"}
UTC = timezone.utc
VENUE = "sim:coinbase"


def _load_source():
    """the vendored prospective_native.py, whose `from backend.prospective_native_math import features` resolves to
    the vendored math module for the duration of the import only."""
    path = os.path.join(os.path.dirname(PNM.__file__), "prospective_native.py")
    saved = {k: sys.modules.get(k) for k in ("backend", "backend.prospective_native_math")}
    pkg = types.ModuleType("backend")
    pkg.__path__ = []
    sys.modules["backend"], sys.modules["backend.prospective_native_math"] = pkg, PNM
    try:
        spec = importlib.util.spec_from_file_location("desk.vendor.ausar_native.prospective_native", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return mod


PN = _load_source()
SYMBOLS = PN.SYMBOLS
FEE = PN.FEE
BOOKS = (("ausar_eth_sma200_coinbase", "ETH_SMA200"), ("ausar_btc_eth_sma200_coinbase", "BTC_ETH_SMA200"))

_PRODUCTS = {}


def products(feeds, sleeve, now, arg):
    """FEED coinbase_products: Coinbase public /products/<id> metadata, refreshed at most hourly."""
    out = {}
    for sym in SYMBOLS:
        got = _PRODUCTS.get(sym)
        if not got or now - got[0] > 3600:
            try:
                d = get(f"https://api.exchange.coinbase.com/products/{sym}", tries=2, timeout=10)
                if isinstance(d, dict) and d.get("id") == sym:
                    _PRODUCTS[sym] = got = (now, d)
            except Exception:
                pass
        if got:
            out[sym] = got[1]
    return out or None


FEEDS = {"coinbase_products": products}


def _d(x):
    return Decimal(str(x))


def market_of(sym, bars, quote, product, now, require_trade=True):
    """the source's validate_capture for one symbol on the desk's data (ValueError when not qualified)."""
    opening = int(now // 86400) * 86400
    if not product:
        raise ValueError("Coinbase product metadata unavailable")
    if product.get("id") != sym or product.get("quote_currency") != "USD" or product.get("base_currency") != sym.split("-")[0]:
        raise ValueError("Wrong actual Coinbase product identity")
    if product.get("status") != "online" or any(product.get(k) is not False for k in
                                                ("trading_disabled", "cancel_only", "auction_mode", "post_only", "limit_only")):
        raise ValueError("Product not executable for ordinary spot paper entries")
    lot, tick, minimum = PN.number(product["base_increment"]), PN.number(product["quote_increment"]), \
        PN.number(product["min_market_funds"])
    rows = [b for b in bars or [] if float(b["t"]) + 86400 <= opening][-200:]
    if len(rows) != 200:
        raise ValueError("Exactly 200 completed daily bars required")
    prev = None
    for b in rows:
        if prev is not None and float(b["t"]) - prev != 86400:
            raise ValueError("Missing/non-native daily period")
        o, h, l, c = (PN.number(b[k]) for k in ("o", "h", "l", "c"))
        if not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError("Invalid OHLC")
        prev = float(b["t"])
    if float(rows[-1]["t"]) + 86400 != opening:
        raise ValueError("Latest completed UTC day unavailable")
    if not quote or quote.get("bid") is None or quote.get("ask") is None:
        raise ValueError("quote unavailable")
    bid, ask = PN.number(quote["bid"]), PN.number(quote["ask"])
    as_of = float(quote.get("_at") or now)
    # the acknowledgement clock: the source took it after its acquisition (run_once: capture, then clock), the desk's
    # pass clock starts before the pass reads its quotes, so a quote received in this pass is current, not future
    at = max(now, as_of)
    if bid > ask or at - as_of > 30:
        raise ValueError("Stale/future/inverted received quote")
    if require_trade:
        t = quote.get("t")
        if t is None or float(t) > as_of + 1e-6 or at - float(t) > 30:
            raise ValueError("Ticker last trade is stale/future; bid/ask freshness not established")
    if bid % tick or ask % tick:
        raise ValueError("Off-tick source quote")
    dates = [datetime.fromtimestamp(float(b["t"]), tz=UTC) for b in rows]
    feat = PNM.features([{"close": float(PN.number(b["c"])), "date": d.date().isoformat(),
                          "complete_at": datetime.fromtimestamp(float(b["t"]) + 86400, tz=UTC).isoformat()}
                         for b, d in zip(rows, dates)])[-1]
    return {"gate": feat["SMA200"], "close": str(rows[-1]["c"]), "sma200": str(feat["sma200"]), "bid": bid, "ask": ask,
            "mid": (bid + ask) / 2, "lot": lot, "tick": tick, "minimum": minimum}


def _round_fee(notional):
    return (notional * FEE).quantize(PN.MONEY_QUANTUM, rounding=ROUND_UP)


class CoinbaseSMA200(Sleeve):
    def __init__(self, sid, book):
        self.book = book
        self.weights = PN.BOOK_WEIGHTS[book]
        self.CONFIG = SleeveConfig(
            sleeve_id=sid, family="coinbase_sma200", cadence_s=30, universe=tuple(SYMBOLS),
            capital=float(PN.RULES["initial_virtual_principal_per_book"]), schedule="always", venue_pref=VENUE,
            needs={"bars": [{"source": "coinbase", "interval": "1d", "n": 230, "symbols": list(SYMBOLS)}],
                   "quotes": {"source": "coinbase", "symbols": list(SYMBOLS)}, "feeds": ["coinbase_products"]},
            params={"cost_bps": float(FEE * 10000), "book": book, "weights": list(self.weights),
                    "rules_sha256": PN.RULES_SHA},
            source=dict(SOURCE, config_id=book), state_schema={"day": "str", "targets": "dict", "status": "str"})
        self._st = None

    def _held(self, view):
        out = {}
        for sym in SYMBOLS:
            p = view.positions.get(f"SPOT:COINBASE:{sym}")
            out[sym] = _d(p["qty"]) if p and float(p["qty"]) > 0 else Decimal(0)
        return out

    def signal(self, view):
        now = float(view.now)
        opening = int(now // 86400) * 86400
        day = datetime.fromtimestamp(opening, tz=UTC).date().isoformat()
        inside = opening <= now < opening + int(PN.RULES["entry_window_seconds"])
        st = dict(view.state or {})
        if st.get("day") != day:
            st = {"day": day, "targets": {}, "status": None}
        self._st = st
        if st.get("status") == "completed":
            return []
        bars = (view.bars or {}).get("1d") or {}
        prods = view.extra.get("coinbase_products") or {}
        market, failures = {}, {}
        for sym in SYMBOLS:
            try:
                market[sym] = market_of(sym, bars.get(sym), (view.quotes or {}).get(sym), prods.get(sym), now)
                market[sym]["entry_quote_qualified"] = True
            except (ValueError, KeyError, TypeError, ArithmeticError) as e:
                failures[sym] = str(e)
                try:                                  # the degraded path: exits without the last-trade clock
                    market[sym] = market_of(sym, bars.get(sym), (view.quotes or {}).get(sym), prods.get(sym), now,
                                            require_trade=False)
                except (ValueError, KeyError, TypeError, ArithmeticError):
                    pass
        cross_ready = not failures and len(market) == len(SYMBOLS)
        held = self._held(view)
        cash = _d(view.cash)
        pending = {p.get("signal_key") for p in view.extra.get("pending_orders") or []}
        weights = [w if s in market and market[s]["gate"] else 0 for s, w in zip(SYMBOLS, self.weights)]
        required = {s for s, w in zip(SYMBOLS, self.weights) if w or held[s] > 0}
        complete = required <= set(market) and (len(required) < 2 or cross_ready)
        entry_ready = complete and not failures and cross_ready
        book_market = {s: market[s] for s in required if s in market}
        trading = entry_ready and inside
        intents = []
        targets = {s: _d(q) for s, q in (st.get("targets") or {}).items()}
        if not targets and trading:
            targets = PN.funded_targets(cash, {s: str(q) for s, q in held.items()}, book_market, weights)
            st["targets"] = {s: str(q) for s, q in targets.items()}
        sold = {}
        for sym in SYMBOLS:
            if sym not in book_market:
                continue
            goal = targets[sym] if trading else (Decimal(0) if not market[sym]["gate"] else held[sym])
            if held[sym] > goal and (held[sym] - goal) * market[sym]["bid"] >= market[sym]["minimum"]:
                q = held[sym] - goal                          # (the source's fill refuses a sub-minimum notional)
                why = "rebalance to the frozen daily target" if trading else "SMA200 gate off: owned exit at the bid"
                key = f"{sym}:{day}:sell:{q}"
                intents.append(Intent("exit", sym, asset="spot", venue=VENUE, qty=float(q), signal_key=key,
                                      price_hint=float(market[sym]["bid"]), order=OrderSpec(window_s=120),
                                      reason=f"{self.book} {why} (close {market[sym]['close']} vs SMA200 "
                                             f"{market[sym]['sma200']})"))
                if key not in pending:
                    sold[sym] = q
        buying = any(p.get("action") == "enter" for p in view.extra.get("pending_orders") or [])
        if trading and buying:                                # a buy still working: wait for its fill (no re-sizing)
            st["status"] = "pending_fills"
        elif trading:
            cash_after = cash
            for sym, q in sold.items():                       # C2: the sells fill at the decision bid this pass
                notional = q * book_market[sym]["bid"]
                cash_after += notional - _round_fee(notional)
            after = {s: held[s] - sold.get(s, Decimal(0)) for s in SYMBOLS}
            incomplete = False
            for sym in SYMBOLS:
                if sym not in book_market:
                    continue
                m = book_market[sym]
                desired = targets[sym] - after[sym]
                if desired > 0:
                    price, lot = m["ask"], m["lot"]
                    affordable = (cash_after / (price * (1 + FEE)) / lot).to_integral_value(rounding=ROUND_DOWN) * lot
                    q = min(desired, affordable)
                    while q > 0 and q * price + _round_fee(q * price) > cash_after:
                        q -= lot
                    if q > 0 and q * price >= m["minimum"]:
                        cash_after -= q * price + _round_fee(q * price)
                        after[sym] += q
                        intents.append(Intent("enter", sym, asset="spot", venue=VENUE, qty=float(q),
                                              signal_key=f"{sym}:{day}:buy:{q}", price_hint=float(price),
                                              order=OrderSpec(window_s=120),
                                              reason=f"{self.book} gate on: buy toward the frozen daily target "
                                                     f"{targets[sym]} (close {m['close']} vs SMA200 {m['sma200']})"))
                if abs(targets[sym] - after[sym]) >= m["lot"] and abs(targets[sym] - after[sym]) * m["mid"] >= m["minimum"]:
                    incomplete = True
            if not intents and not pending and not incomplete:
                st["status"] = "completed"                    # C4: the day's targets are met
            else:
                st["status"] = "partial_depth_pending" if incomplete else "pending_fills"
        else:
            st["status"] = "partial_market_unavailable" if not complete else "expired_or_entries_disabled"
        self._st = st
        return intents

    def update_state(self, view, intents):
        return self._st


def sleeves():
    return [CoinbaseSMA200(sid, book) for sid, book in BOOKS]
