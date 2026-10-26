"""Sable / Autopilot desk (autopilot-desk @48e8f90f, the "Cassius" paper desk) — its two screens, each a sleeve on
the desk's own unattended paper runtime (desk/sleeves/sable/runtime.py, a line-by-line port of ledger-core.mjs +
unattended-core.mjs):

  sable_location_first_repair_v210 (manifest family location_first)
      Location-first Repair v2.1.0 (src/lib/scanner/location-first-repair.mjs, ported in
      desk/sleeves/sable/location_first.py): daily location under the 50-day after a wash, on a support shelf
      (EMA21 / 12-day low / 60-day drop Fibonacci), MACD recently lifting, RSI 28-52 -> S_COIL / A_WASHOUT;
      BUY_NOW (priority S / A) is a SETUP hand. The scan is the worker's runLocationFirstUniverse(): a close-only
      prelim over the Yahoo spark (6 months of daily closes) for every stock, a deep-OHLC shortlist (48 best
      under-50 reads + 48 best leaders-rest reads + SPY / QQQ) evaluated on the daily OHLC with today's forming bar
      and the live session price, ETFs close-only (context, never SETUP); buildLocationFirstScan() ranks it and
      hands the first fill-cap (mandate.maxPositions = 6) SETUP stocks to the paper pass.
  sable_support_scanner (manifest family sable)
      the legacy desk-native completed-bar support scanner (src/lib/scanner/desk-core.mjs scoreDeskQuote /
      buildDeskScan, ported in desk/sleeves/sable/desk_scanner.py) over quotes built from completed 5-minute bars.

The paper pass (both sleeves, every 5 minutes in the session — the worker's 5-minute tick):
  * held names: the swing stop / target floors from the fill and the daily ATR (stop = fill - 1.6 x max(ATR, 1.5%
    of fill), target = fill + 2.8 x ATR), breakeven once last >= fill + 1R; exit at the quote through the stop or
    target; the 15-day time stop when the rest never paid; the thesis exit on the scan's leaders-rest reasons;
  * entries: each SETUP hand, in the research pass's order (the eligible universe's order) and then the hand
    order, through deskDiscretionAllowsBuy (location-first: SETUP, anti-chase clear, a completed daily bar) and
    canEnter (no same-session round trip — 8 hours after a sell, not already held, position cap 6 incl. working
    buys, size >= 1 share, regular session, the mandate's own entry rules incl. its earnings window); one buy per
    name per daily bar (the event key buy:<ticker>:<daily bar>); size = min(0.5% of equity / (1.6 x daily ATR),
    15% of equity, 98% of cash) whole shares; market orders.

Removed under the cutover doctrine (not the strategy's own rules): the desk run state (pause / park), the 2%
daily-loss park, the stale-tape park, the Edge overlay (blockNewEntries / parked names / sizeDown quarter-risk),
the Tensor SELL veto on entries (a 5-minute chart gate on a daily location entry — the Sable law: "Tensor is a
badge"). The broker bracket the Alpaca path could attach is not carried: the pass's own stop / target govern.

Named divergences (plumbing / timing of the source runtime -> the strategy's intent on this engine):
  1. cadence: the cron worker ran every 5 minutes around the clock; here a pass every 5 minutes in the regular
     session (entries were regular-session only; exits it decided off-hours could not route before the open).
  2. data: the spark series are the source's own read (Yahoo v7 spark, 6mo/1d, open bar dropped, cached 5 min:
     desk/feedlib/yahoo_spark.py); the deep OHLC is the desk's split-adjusted daily bars (Alpaca SIP when keyed,
     else Yahoo) since now - 400 days plus today's forming bar from the quote's daily bar (the source: Alpaca IEX
     daily bars incl. today's bar); the session price is the quote's daily close, else last, else previous close
     (regularSessionPriceFromSnapshot). A shortlisted name without a quote this pass (it entered the shortlist this
     pass) is evaluated without the forming bar at its last known price, as the source did on a snapshot miss
     (counted in the pass's observation).
  3. earnings: the earnings-window flags are stamped at the source's broad windows (08 10 12 14 18 ET and the first
     run of a day) for the top 6 hands, from the desk's Nasdaq earnings calendar (desk/feedlib/earnings.py) instead
     of the source's Yahoo quote-page scrape: the same date, next report within [now - 12 h, now + 48 h].
  4. fills: the desk simulator filled at the quote inside the pass; here the pass decides on the same simulated
     state (so the cap, cash and same-pass sizing match) and its buys / exits become marketable engine orders;
     the next pass rebuilds the state from the sleeve's book (fill price, open time), the stop / target initialised
     from the fill and the ATR recorded at the decision.
  5. lens fallback: when the location-first scan has no candidate at all the worker switched the hands to the
     leaders-rest lens (a different screen); here the sleeve stays with its own scan (no new hands that pass).
  6. a failed spark read: the source kept its last scanner bundle and quotes; here too (state), with the held and
     handed names' prices refreshed from the live quote."""
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...util import ET, et_date
from ..jsport import gt, js_round, number
from ..sable import desk_scanner as ds
from ..sable import location_first as lf
from ..sable import runtime as rt

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "..", "..", "vendor", "sable")
COMMIT = "48e8f90f5d9def28363eb4013dac4dd8d78f74bf"
LF_SOURCE = {"repo": "autopilot-desk", "ref": "main", "commit": COMMIT,
             "path": "src/lib/scanner/location-first-repair.mjs", "blob": "5377c97f7c0d48b1045fdc9f754b9b3555ae638c",
             "runtime": ["src/lib/desk/ledger-core.mjs@6342ddc8", "src/lib/desk/unattended-core.mjs@8fb33e59",
                         "src/lib/scanner/location-first-desk.mjs@0b1c5417", "src/lib/scanner/leaders-rest-core.mjs@5df6186e"]}
BROAD_HOURS = (8, 10, 12, 14, 18)


def _vendored_lists():
    """the Sable universe, byte-exact from the vendored catalog.mjs + universe.ts: SEED rows, then the catalog
    tickers not in SEED (kind etf when in ETF_TICKERS)."""
    cat = open(os.path.join(VENDOR, "catalog.mjs")).read()
    uni = open(os.path.join(VENDOR, "universe.ts")).read()

    def block(name):
        m = re.search(name + r"\s*=\s*(?:new Set|Object\.freeze)\(\[(.*?)\]\)", cat, re.S)
        return re.findall(r'"([^"]+)"', m.group(1))

    etfs = set(block("ETF_TICKERS"))
    catalog = block("CATALOG_TICKERS")
    seed_src = re.search(r"const SEED: SymbolMeta\[\] = \[(.*?)\n\];", uni, re.S).group(1)
    seed = [(t, k) for t, k in re.findall(r'ticker: "([^"]+)".*?kind: "(stock|etf)"', seed_src)]
    avg = {t: float(v.replace("_", "")) for t, v in re.findall(r'ticker: "([^"]+)".*?avgVolume: ([0-9_]+)', seed_src)}
    seed_set = {t for t, _ in seed}
    universe = seed + [(t, "etf" if t in etfs else "stock") for t in catalog if t not in seed_set]
    avg.update({t: 1_000_000.0 for t in catalog if t not in seed_set})          # universe.ts catalog rows
    return universe, etfs, avg


UNIVERSE, ETF_TICKERS, AVG_VOLUME = _vendored_lists()
KIND = dict(UNIVERSE)
TICKERS = tuple(t for t, _ in UNIVERSE)
ORDER = {t: i for i, t in enumerate(TICKERS)}


def broad_window_key(now):
    d = datetime.fromtimestamp(now, tz=ET)
    if d.hour in BROAD_HOURS:
        return f"{d.date().isoformat()}-{d.hour:02d}"
    return None


def should_run_broad_window(last_key, now):
    key = broad_window_key(now)
    if key:
        return last_key != key
    return last_key is None or last_key == ""


def first_window_key(now):
    return f"first-{datetime.fromtimestamp(now, tz=ET).date().isoformat()}"


def session_price(q):
    """regularSessionPriceFromSnapshot: the daily bar's close, else the last trade, else the previous close."""
    q = q or {}
    for k in ("day_close", "last", "prev_close"):
        v = number(q.get(k))
        if v > 0:
            return v
    return None


def ms(t):
    """location-first-desk msOf(): seconds -> ms."""
    n = number(t)
    if not math.isfinite(n) or n <= 0:
        return None
    return n * 1000 if n < 10_000_000_000 else n


def ohlc_bars(completed, quote, now):
    """the deep OHLC tape: completed daily bars since now - 400 days plus today's forming bar (the quote's daily
    bar of today's session) — the source read Alpaca daily bars (start = now - 400 days), today's included."""
    start = datetime.fromtimestamp(now - 400 * 86400, tz=timezone.utc).date().isoformat()
    today = et_date(now)
    out = []
    for b in completed or []:
        d = cal._as_date(float(b["t"])).isoformat()
        if d >= start and d < today:
            out.append({"time": float(b["t"]), "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"],
                        "volume": b.get("v") or 0})
    q = quote or {}
    forming = False
    if q.get("day_date") == today and all(gt(number(q.get(k)), 0) for k in ("day_open", "day_high", "day_low", "day_close")):
        t0 = datetime.combine(datetime.fromisoformat(today).date(), datetime.min.time(), ET).timestamp()
        out.append({"time": t0, "open": q["day_open"], "high": q["day_high"], "low": q["day_low"],
                    "close": q["day_close"], "volume": q.get("day_volume") or 0})
        forming = True
    return out, forming


class LocationFirstRepair(Sleeve):
    """sable_location_first_repair_v210."""

    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="sable_location_first_repair_v210", family="location_first", cadence_s=300, schedule="rth",
            universe=TICKERS, capital=float(rt.DEFAULT_MANDATE["startingCapital"]),
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": 300, "symbols_for": "ohlc"}],
                   "quotes": {"source": "equity"}, "feeds": ["sable_spark", "sable_earnings"]},
            params={"mandate": dict(rt.DEFAULT_MANDATE), "fill_cap": lf.fill_cap(rt.DEFAULT_MANDATE),
                    "version": lf.LOCATION_FIRST_VERSION},
            source=LF_SOURCE)
        # the desk's daily earnings job refreshes the calendar of every sleeve whose spec reads it
        self.spec = {"extra": {"earnings": "feed:sable_earnings"}}
        self.engine = None
        self._funnel_at = None
        self._funnel = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    # -- data the engine fetches for this sleeve -------------------------------------------------------------------
    def spark_symbols(self, now):
        return list(TICKERS)

    def earnings_symbols(self, now):
        st = self._state()
        return list(dict.fromkeys((st.get("hands") or []) + (st.get("shortlist") or [])))

    def universe_now(self, now, book=None):
        return list(TICKERS)

    def _state(self):
        if self.engine is None:
            return {}
        return self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}

    def _held(self, book):
        return [i.split(":", 1)[1] for i in ((book.positions if book is not None else {}) or {}) if i.startswith("EQ:")]

    def _shortlist_now(self, now):
        """the funnel's deep-OHLC shortlist for this pass (spark prelim + leaders shortlist), memoised per pass."""
        if self._funnel_at == now and self._funnel is not None:
            return self._funnel
        spark = None
        if self.engine is not None and self.engine.feeds is not None:
            spark = self.engine.feeds.get("sable_spark", self, now)
        st = self._state()
        prelim, leaders = self._prelim(spark or {}, st.get("quotes") or {})
        self._funnel = sorted(lf.shortlist(prelim, leaders))
        self._funnel_at = now
        return self._funnel

    def bar_symbols(self, need, now, book=None):
        return sorted(set(self._shortlist_now(now)) | set(self._held(book)) | set(self._state().get("hands") or []))

    def quote_universe(self, now, book=None):
        return self.bar_symbols(None, now, book)

    # -- the scan ----------------------------------------------------------------------------------------------------
    def _prelim(self, spark, quotes):
        prelim, leaders = [], []
        for t in TICKERS:
            if KIND[t] == "etf":
                continue
            series = spark.get(t)
            bars = lf.bars_from_daily_closes((series or {}).get("times"), (series or {}).get("closes"))
            if len(bars) < 70:
                continue
            q = quotes.get(t) or {"ticker": t, "kind": "stock", "price": (series or {}).get("price")}
            px = number(q.get("price"))
            res = lf.evaluate({"symbol": t, "bars": bars,
                               "regularSessionPrice": px if px > 0 else (series or {}).get("price"),
                               "marketContext": {"eventBlocked": q.get("earningsImminent") is True}})
            prelim.append({"ticker": t, "result": res, "quote": q, "bars": bars})
            ld = lf.evaluate_leaders({"symbol": t, "bars": bars,
                                      "regularSessionPrice": px if px > 0 else (series or {}).get("price"),
                                      "eventBlocked": q.get("earningsImminent") is True})
            leaders.append({"ticker": t, "leaders": ld})
        return prelim, leaders

    def scan(self, view, spark, prev_quotes):
        """runLocationFirstUniverse() on this pass's data: (results, quotes, scan bundle, counters)."""
        now = view.now
        quotes = {t: dict(q) for t, q in (prev_quotes or {}).items()}
        prelim, leaders = self._prelim(spark, quotes)
        want = lf.shortlist(prelim, leaders)
        daily = (view.bars or {}).get("1d") or {}
        results, counts = [], {"prelim": len(prelim), "shortlist": len(want), "ohlc": 0, "no_quote": 0}
        for row in prelim:
            t = row["ticker"]
            series = spark.get(t) or {}
            bar_at = ms(row["bars"][-1]["time"]) if row["bars"] else None
            if t in quotes and bar_at:
                quotes[t] = dict(quotes[t], locationFirstAt=bar_at)
            elif t not in quotes and (bar_at or gt(number(series.get("price")), 0)):
                quotes[t] = {"ticker": t, "kind": "stock", "price": series.get("price"), "locationFirstAt": bar_at}
            if t not in want:
                results.append(row["result"])
                continue
            vq = view.quotes.get(t)
            tape, forming = ohlc_bars(daily.get(t), vq, now)
            if len(tape) < 70:
                results.append(row["result"])
                continue
            counts["ohlc"] += 1
            live = session_price(vq) if vq else None
            if not vq:
                counts["no_quote"] += 1                     # no snapshot this pass: the source's liveBy miss
            qpx = number((quotes.get(t) or {}).get("price"))
            spx = live if gt(live, 0) else (qpx if qpx > 0 else None)
            res = lf.evaluate({"symbol": t, "bars": tape, "regularSessionPrice": spx,
                               "marketContext": {"eventBlocked": (quotes.get(t) or {}).get("earningsImminent") is True}})
            results.append(res)
            bat = ms(tape[-1]["time"])
            if t in quotes and bat:
                upd = {"locationFirstAt": bat, "ema21": res["metrics"].get("ema21"), "ema50": res["metrics"].get("ema50")}
                if gt(live, 0):
                    upd.update(price=live, source="live-read-quote")
                quotes[t] = dict(quotes[t], **upd)
        for t in TICKERS:
            if KIND[t] != "etf":
                continue
            series = spark.get(t) or {}
            bars = lf.bars_from_daily_closes(series.get("times"), series.get("closes"))
            if len(bars) < 70:
                continue
            q = quotes.get(t) or {"ticker": t, "kind": "etf"}
            px = number(q.get("price"))
            results.append(lf.evaluate({"symbol": t, "bars": bars,
                                        "regularSessionPrice": px if px > 0 else series.get("price")}))
        for res in results:
            t = res["symbol"]
            ex = dict(quotes.get(t) or {}, ticker=t, kind="etf" if lf.is_etf_ticker(t, (quotes.get(t) or {}).get("kind"),
                                                                                   ETF_TICKERS) else "stock")
            series = spark.get(t) or {}
            h = lf.hydrate_quote(ex, res, series)
            bar_at = ms(ex.get("locationFirstAt")) or ms((series.get("times") or [None])[-1])
            h["locationFirstAt"] = bar_at
            h["origin"] = lf.LOCATION_FIRST_SOURCE
            quotes[t] = h
        bundle = lf.build_location_first_scan(results, quotes, rt.DEFAULT_MANDATE, ETF_TICKERS)
        return results, quotes, bundle, counts, sorted(want)

    # -- the pass -------------------------------------------------------------------------------------------------------
    def signal(self, view):
        now = view.now
        st = dict(view.state or {})
        spark = (view.extra or {}).get("sable_spark") or {}
        prev_quotes = st.get("quotes") or {}
        if spark:
            _, quotes, bundle, counts, want = self.scan(view, spark, prev_quotes)
        else:                                               # divergence 6: keep the last bundle, refresh prices
            quotes = {t: dict(q) for t, q in prev_quotes.items()}
            bundle = st.get("scan") or lf.build_location_first_scan([], {}, rt.DEFAULT_MANDATE, ETF_TICKERS)
            for t, vq in (view.quotes or {}).items():
                px = session_price(vq)
                if t in quotes and gt(px, 0):
                    quotes[t]["price"] = px
            counts, want = {"spark": "unavailable"}, st.get("shortlist") or []
        # lens: location-first while it has candidates (the leaders-rest fallback is divergence 5)
        if not bundle.get("candidates"):
            bundle = dict(bundle, hands=[])
        # earnings window flags at the broad windows (divergence 3)
        if should_run_broad_window(st.get("broad_key"), now):
            st["broad_key"] = broad_window_key(now) or first_window_key(now)
            calendar = (view.extra or {}).get("sable_earnings") or {}
            for h in (bundle.get("hands") or [])[:6]:
                t = str(h.get("ticker") or "")
                d = calendar.get(t)
                at = datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000 if d else None
                imminent = at is not None and now * 1000 - 12 * 3600 * 1000 <= at <= now * 1000 + 48 * 3600 * 1000
                if t in quotes:
                    quotes[t] = dict(quotes[t], earningsImminent=bool(imminent), earningsAt=at if imminent else None)
        state, positions = self._desk_state(view, st, quotes, bundle)
        actions = self._run(state, view)
        intents = self._intents(actions, state, view)
        st.update(quotes=_slim_quotes(quotes, set(positions) | {str(h.get("ticker")) for h in bundle.get("hands") or []}),
                  scan=_slim_bundle(bundle), hands=[str(h.get("ticker")) for h in bundle.get("hands") or []],
                  shortlist=want, events=state["events"][:400],
                  pos={p["ticker"]: {"stop": p["stop"], "target": p["target"], "opened_at": p["_opened"]}
                       for p in state["positions"] if p["ticker"] in positions})
        self._st = st
        hands = [h["ticker"] for h in bundle.get("hands") or []]
        intents.append(Intent("signal", "SABLE", reason=f"location-first pass: hands {hands}",
                              meta={"counts": counts, "hands": hands, "actions": [list(a[:3]) for a in actions]},
                              signal_key=f"lf:{et_date(now)}:{','.join(hands)}"))
        return intents

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})

    # -- engine book -> Sable desk state ---------------------------------------------------------------------------------
    def _desk_state(self, view, st, quotes, bundle):
        working_exit = {p["inst"].split(":", 1)[1] for p in (view.extra or {}).get("pending_orders", [])
                        if p["action"] == "exit"}
        saved = st.get("pos") or {}
        positions, held = [], []
        for inst, p in view.positions.items():
            if not inst.startswith("EQ:") or float(p["qty"]) <= 0:
                continue
            t = inst.split(":", 1)[1]
            if t in working_exit:
                continue                                    # the exit is working: the source decremented it
            avg = float(p["avg"])
            opened = float(p.get("opened_at") or view.now)
            sv = saved.get(t) if (saved.get(t) or {}).get("opened_at") == opened else None
            if sv is None:                                  # first sight of the fill: applySimulatorFill's levels
                pm = (p.get("meta") or {}).get("position_meta") or {}
                q = quotes.get(t) or {}
                atr = max(number(pm.get("atr_entry")) if gt(number(pm.get("atr_entry")), 0) else
                          (number(q.get("atr")) if gt(number(q.get("atr")), 0) else 0), avg * 0.015)
                sv = {"stop": rt.round2(avg - atr * 1.6), "target": rt.round2(avg + atr * 2.8), "opened_at": opened}
            positions.append({"id": f"pos_{t}_{int(opened)}", "ticker": t, "side": "long", "qty": float(p["qty"]),
                              "avgPrice": avg, "openedAt": opened * 1000, "stop": sv["stop"], "target": sv["target"],
                              "_opened": opened})
            held.append(t)
        orders = [{"id": f"ord_{i}", "ticker": p["inst"].split(":", 1)[1], "side": "buy", "qty": p["vqty"],
                   "status": "accepted"}
                  for i, p in enumerate((view.extra or {}).get("pending_orders", []))
                  if p["action"] == "enter" and p["side"] == "buy"]
        state = {"positions": positions, "orders": orders, "events": list(st.get("events") or []), "quotes": quotes,
                 "scanner": bundle, "mandate": dict(rt.DEFAULT_MANDATE), "runState": "running",
                 "cash": float(view.cash), "broker": {"cash": float(view.cash), "equity": float(view.equity)},
                 "market": {"session": rt.equity_session(view.now * 1000)}, "freshness": {}}
        return state, held

    def _run(self, state, view):
        now_ms = view.now * 1000
        reads = {p["ticker"]: {"paperBuy": False, "paperSell": False, "state": "NEUTRAL"}
                 for p in state["positions"] if p["ticker"] in state["quotes"]}
        ps = rt.Pass(state, reads, now_ms, now_ms)
        # the worker's research pass (researchPassAsync) before the unattended pass: held names, then the hands in
        # the eligible universe's order
        for pos in list(state["positions"]):
            q = state["quotes"].get(pos["ticker"])
            if q:
                ps.consider_held(pos, q, reads[pos["ticker"]])
        hands = {str(r.get("ticker") or "").upper() for r in (state["scanner"].get("hands") or [])
                 if str(r.get("action") or "").upper() == "SETUP"}
        pins = {r["ticker"] for r in state["scanner"].get("candidates") or [] if lf.is_buy_side_candidate(r)}
        for t in sorted(hands & pins, key=lambda x: ORDER.get(x, 1 << 30)):
            if any(p["ticker"] == t for p in state["positions"]):
                continue
            q = state["quotes"].get(t)
            if q:
                ps.consider_watch(dict(q, ticker=t), {"paperBuy": False, "paperSell": False, "state": "NEUTRAL",
                                                      "completedBarAt": q.get("locationFirstAt")})
        ps.run()
        for pos in state["positions"]:
            pos.setdefault("_opened", view.now)
        return ps.actions

    def _intents(self, actions, state, view):
        out = []
        for a in actions:
            if a[0] == "buy":
                _, t, qty, px, why, key = a
                q = state["quotes"].get(t) or {}
                out.append(Intent("enter", t, qty=float(qty), price_hint=float(px), signal_key=key,
                                  reason=f"{self.CONFIG.sleeve_id}: {why}"[:300], order=OrderSpec(window_s=3600),
                                  meta={"position_meta": {"atr_entry": q.get("atr"), "sable_key": key}}))
            elif a[0] == "sell":
                _, t, qty, px, why, key = a
                out.append(Intent("exit", t, price_hint=float(px), signal_key=key, reason=why[:300],
                                  order=OrderSpec(window_s=3600)))
            elif a[0] == "cancel":
                out.append(Intent("cancel", a[1], reason=a[2]))
        return out


class SupportScanner(LocationFirstRepair):
    """sable_support_scanner: the legacy desk-native completed-bar support scanner on the two-pass tape — the spark
    screen (Yahoo v7 spark 1d / 5m: price, day range, 52-week range, today's 5-minute closes) quotes every catalog
    name; pickDeep keeps the held names, the last scan's buy-side pins, SPY / QQQ / IWM and the best screenScore
    names up to 36; those get a quote from their completed regular-session 5-minute bars of the last 5 sessions
    (quote-core quoteFromCompletedBars: swing support over 64 bars, 5-minute ATR, VWAP, RSI, MACD) carrying the
    spark's 52-week range and daily previous close; buildDeskScan scores every quote (scoreDeskQuote: SETUP only on
    completed OHLC, near support or the lower 30% of the 52-week range, not lost / roof / chase / deteriorating, no
    earnings inside 48 h, ETFs context); the paper pass trades the SETUP hands (deskDiscretionAllowsBuy's desk branch:
    RSI 38-68, extension <= 1.6 ATR, MACD >= -0.15, location not extended) with the swing exits on the quote's ATR.

    Divergences beyond the location-first sleeve's 1, 4: (a) Tensor reads are not supplied — the desk's 5-minute
    vector-replica engine fed a SELL veto (removed: chart gate) and score badges (+6 on a BUY, +3 in a reversal
    window), which go with it; (b) a deep 5-minute quote is rebuilt each pass for that pass's deep names — the
    source kept a name's last 5-minute quote (with its old price) after it left the deep list; (c) earnings: the
    legacy flow never carried an earnings flag onto a 5-minute quote (it rebuilt the quote without one), so none."""

    def __init__(self):
        super().__init__()
        self.CONFIG = SleeveConfig(
            sleeve_id="sable_support_scanner", family="sable", cadence_s=300, schedule="rth", universe=TICKERS,
            capital=float(rt.DEFAULT_MANDATE["startingCapital"]),
            needs={"bars": [{"source": "yahoo", "interval": "5m", "n": 400, "symbols_for": "deep"}],
                   "feeds": ["sable_spark5m"]},
            params={"mandate": dict(rt.DEFAULT_MANDATE), "fill_cap": lf.fill_cap(rt.DEFAULT_MANDATE),
                    "deep_cap": ds.DEEP_CAP},
            source={"repo": "autopilot-desk", "ref": "main", "commit": COMMIT, "path": "src/lib/scanner/desk-core.mjs",
                    "blob": "1b5f90418acae9d53d3bf25caa251f86843351b2", "lines": [42, 240],
                    "runtime": ["src/lib/desk/ledger-core.mjs@6342ddc8", "src/lib/desk/unattended-core.mjs@8fb33e59",
                                "src/lib/market/quote-core.mjs@7b2bac12", "src/lib/desk/screen-core.mjs@4a94dc93"]})
        self.spec = {}
        self._deep_at = None
        self._deep = None

    def earnings_symbols(self, now):
        return []

    def _screen(self, metas):
        quotes = {}
        for t in TICKERS:
            m = (metas or {}).get(t)
            if not m:
                continue
            q = ds.quote_from_spark_meta(m, t, {"kind": KIND[t], "avgVolume": AVG_VOLUME.get(t, 0)})
            if q:
                quotes[t] = q
        return quotes

    def _deep_now(self, now, book):
        if self._deep_at == now and self._deep is not None:
            return self._deep
        metas = self.engine.feeds.get("sable_spark5m", self, now) if (self.engine and self.engine.feeds) else None
        quotes = self._screen(metas or {})
        st = self._state()
        self._deep = ds.pick_deep(list(quotes.values()), self._held(book), st.get("pins") or [])
        self._deep_at = now
        return self._deep

    def bar_symbols(self, need, now, book=None):
        return self._deep_now(now, book)

    def quote_universe(self, now, book=None):
        return []

    def signal(self, view):
        now = view.now
        st = dict(view.state or {})
        metas = (view.extra or {}).get("sable_spark5m") or {}
        quotes = self._screen(metas)
        held = [i.split(":", 1)[1] for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"]) > 0]
        deep = ds.pick_deep(list(quotes.values()), held, st.get("pins") or [])
        five = (view.bars or {}).get("5m") or {}
        last_bar, n_deep = None, 0
        for t in deep:
            rows = _last_sessions(five.get(t) or [], 5)
            if not rows:
                continue
            d = ds.quote_from_completed_bars({"ticker": t, "kind": KIND.get(t, "stock")}, rows, "live-read")
            if not d:
                continue
            prior = quotes.get(t)
            if prior:
                if number(prior.get("low52")) > 0:
                    d["low52"] = prior["low52"]
                if number(prior.get("high52")) > 0:
                    d["high52"] = prior["high52"]
                dp = number(prior.get("dayPrevClose")) if number(prior.get("dayPrevClose")) > 0 else \
                    (number(prior.get("prevClose")) if prior.get("source") == "live-read-quote" else float("nan"))
                if math.isfinite(dp) and dp > 0:
                    d["dayPrevClose"] = dp
            quotes[t] = d
            n_deep += 1
            last_bar = rows[-1]["time"] * 1000
        scan = ds.build_desk_scan(quotes, [], rt.DEFAULT_MANDATE, completed_bar_at=last_bar)
        bundle = ds.desk_scan_to_bundle(scan)
        state, positions = self._desk_state(view, st, quotes, bundle)
        actions = self._run(state, view)
        intents = self._intents(actions, state, view)
        hands = [h["ticker"] for h in bundle.get("hands") or [] if str(h.get("action")) == "SETUP"]
        st.update(pins=[r["ticker"] for r in bundle["candidates"] if lf.is_buy_side_candidate(r)], deep=deep,
                  events=state["events"][:400], hands=hands,
                  pos={p["ticker"]: {"stop": p["stop"], "target": p["target"], "opened_at": p["_opened"]}
                       for p in state["positions"] if p["ticker"] in positions})
        self._st = st
        intents.append(Intent("signal", "SABLE", reason=f"desk support scan: SETUP hands {hands}",
                              meta={"screened": len(quotes), "deep": len(deep), "deep_quotes": n_deep, "hands": hands,
                                    "actions": [list(a[:3]) for a in actions]},
                              signal_key=f"ds:{et_date(now)}:{','.join(hands)}"))
        return intents


def _last_sessions(bars, k):
    """completed regular-session 5-minute bars of the last k sessions (the source's Yahoo range=5d read)."""
    rows = []
    for b in bars:
        d = datetime.fromtimestamp(float(b["t"]), tz=ET)
        m = d.hour * 60 + d.minute
        if d.weekday() < 5 and 9 * 60 + 30 <= m < 16 * 60:
            rows.append({"time": float(b["t"]), "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"],
                         "volume": b.get("v") or 0, "_d": d.date()})
    days = sorted({r["_d"] for r in rows})[-k:]
    keep = set(days)
    return [{k2: v for k2, v in r.items() if k2 != "_d"} for r in rows if r["_d"] in keep]


def _slim_quotes(quotes, keep):
    """what the next pass reads back (desk.quotes persisted): price, atr, flags."""
    out = {}
    for t, q in quotes.items():
        row = {k: q.get(k) for k in ("price", "atr", "kind", "locationFirstAt", "earningsImminent", "earningsAt",
                                    "ema21", "ema50") if q.get(k) is not None}
        if row:
            out[t] = row
    return out


def _slim_bundle(b):
    return {"status": b.get("status"), "candidates": b.get("candidates") or [], "hands": b.get("hands") or [],
            "fillCap": b.get("fillCap"), "radarCap": b.get("radarCap"), "origin": b.get("origin")}


def _feed_spark(feeds, sleeve, now, arg):
    from ...feedlib import yahoo_spark
    return yahoo_spark.feed(feeds, sleeve, now, arg)


def _feed_spark5m(feeds, sleeve, now, arg):
    from ...feedlib import yahoo_spark
    return yahoo_spark.feed_metas(feeds, sleeve, now, arg)


def _feed_earnings(feeds, sleeve, now, arg):
    from .femto_specs import _earnings_book
    syms = sleeve.earnings_symbols(now) if hasattr(sleeve, "earnings_symbols") else []
    return _earnings_book(feeds).calendar(syms) if syms else {}


FEEDS = {"sable_spark": (_feed_spark, {"per_sleeve": True}),
         "sable_spark5m": (_feed_spark5m, {"per_sleeve": True}),
         "sable_earnings": (_feed_earnings, {"per_sleeve": True})}


def sleeves():
    return [LocationFirstRepair(), SupportScanner()]
