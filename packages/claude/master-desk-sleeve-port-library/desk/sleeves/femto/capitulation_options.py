"""Capitulation Reversal — options (0-7 DTE long calls) — lean-desk port (Wave B).

master-desk: the old desk's capitulation_options.py restored on the engine. The equity sleeve's 5-part 1H
capitulation signature (its functions in desk/sleeves/femto/capitulation.py: the old file mirrored
capitulation_sleeve.py verbatim) bought as one slightly out-of-the-money weekly call, 5-10x leverage on the
violent bounce: the premium paid is the max loss (no disaster stop); out at +75%, at 1 day to expiry, or when
the underlying breaks 3% under the entry.

  signal ... >= 200 completed daily bars and >= 36 closed 1H RTH-grid bars; daily ATR(14) / close > 5% first;
             then on the last closed 1H bar: the bar before it (the climax) has RSI(14) < 20, volume > 2x the
             mean of the 20 bars before it and a low within 2% of the daily EMA200; the last bar is green with
             RSI turning up.
  fear ..... the fear-based sleeves' own entry rule (User 2026-10-10, ported from the equity sleeve): an entry
             defers unless the desk sentiment composite reads FEAR+; unreadable = fail-open, as the old.
  entry .... the basket in order, at most 5 calls held, closing or in flight: the nearest expiry 0-7 DTE, its
             first strike >= the last 1H close x 1.02 (desk/options_exec.select_long_call), ask > 0 and
             (ask - bid) / mid <= 15% when bid > 0; floor(0.10% of equity / (ask x 100)) contracts (0: skip);
             buy to open, a day limit at the ask.
  exits .... (never gated; every pass, every held call whose buy has finished) in the old order: the quote's
             mid ((bid + ask) / 2 to 4 places, two-sided) >= 1.75 x the premium paid; <= 1 day to expiry (a call
             bought that close to expiry is sold at the next pass, the reconcile echo); the last closed 1H close
             <= the entry's (the signal bar's close, to the cent) x 0.97; sell to close, a day limit at the bid
             (no quote or no bid: no close, the exit fires again next pass).

Gone under the cutover doctrine: the risk gate (kill switch, the desk-wide -3% daily halt, Decisions #4/#14), the
drawdown brake (block / halve), the Decision #75 pre_buy (red-day gate, its context gate, the chart-gate staging,
the 72h pending TTL and the release replay with its re-checks and re-quote), the Decision #8 earnings blackout
(desk/earnings.py, fail-closed on a stale or missing calendar: a desk-wide rail per the sleeve's own SPEC), the
150% desk cap (its intra-pass accumulator and exposure ledger) and the post-wipe double-buy guard (the broker's
option positions across every sleeve).
Named divergences: passes hourly at :31 in the session (09:31-15:31 ET on trading days) and the old cron's
reconcile run as an exits-only echo pass minutes later (anchored at :36) — the old cron ran scan then reconcile
hourly at :31: the scan quit outside 09:30-16:00 ET and at weekends (not on holidays or after an early close), the
reconcile (fills, close verification and the exits again) ran around the clock on weekdays, so an exit that comes
due overnight is decided at the session's first pass; the desk's option chain snapshot carries the candidate's
and the held call's quotes (the old called the latest-quote endpoint per contract); orders are day limits resting
to the session's close, as the old's DAY orders, but a close that dies unfilled is decided again at the next pass
(the old's verify_closes re-fired a dead close once at the then-bid, whatever its exit rules then said); a call
frees its slot and its symbol once its close fills (the old's verify_closes ran after its entry loop, so a close
filled since its last run still held them through the next scan's entries).

Inputs via context.extra:
  "universe"      the basket, in scan order (+ held names)
  "bars_1h"       {SYM: closed 1H bars on the RTH grid (09..15 ET starts), since (today - 15d)}
  "chains"        {SYM: call rows 0-7 DTE {"symbol","strike","expiration","type","bid","ask"}} (fetched on demand)
  "option_quotes" {OCC: {"bid","ask"}} — the held calls
  "fear_ok"       bool (absent == fail-open pass)
  "session_close" epoch of the session's close (the day orders' deadline)
  "scan"          False on the reconcile echo pass (exits only); absent == a scan
  "entering"      the symbols whose buy is still working (a partly filled call is not a position yet)
  "sleeve_state"  {SYM: {"position": {"qty","entry_px","occ","expiry","entry_stock_px",...} | None,
                  "pending_entry": ...}}
Bars (arg): {SYM: completed daily bars (SIP, adjustment=all), 260}."""
import math
from datetime import date

from . import capitulation as cap
from .compat import BaseSleeve, Intent, SleeveConfig

RISK_FRACTION = 0.001        # 0.10% — smaller due to variance
MAX_POSITIONS = 5
DTE_MIN, DTE_MAX = 0, 7
OTM_PCT = 0.02
PROFIT_TAKE_MULT = 1.75      # +75% premium profit-take
EXIT_DTE = 1                 # time exit: close at the latest with 1 DTE (never hold into expiry)
THESIS_BREAK_PCT = 0.03      # underlying -3% from entry = thesis broken
QUOTE_GATE_FRAC = 0.15       # desk/options_exec.select_long_call: (ask - bid) / mid
DAILY_MIN_BARS = cap.EMA200_PERIOD                      # 200: the old scan's daily floor
H1_MIN_BARS = cap.VOL_LOOKBACK + cap.RSI_PERIOD + 2     # 36: the old scan's 1H floor

CONFIG = SleeveConfig(
    sleeve_id="capitulation_options", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def capitulation_signal(h1_bars, daily_bars):
    """the old maybe_enter's signal: part 5 (daily ATR(14) / close > 5%) first, then parts 1-4 on the last
    closed 1H bar — the equity sleeve's functions; its shadow-band telemetry is never an entry."""
    if not cap.atr_filter_ok(daily_bars):
        return None
    sig = cap.detect_capitulation(h1_bars, daily_bars)
    return None if not sig or sig.get("shadow_beyond_ema_band") else sig


def _px(q, key):
    """a quote side as the old quote CLI read it: a finite float, else 0."""
    try:
        v = float((q or {}).get(key) or 0)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


def quote_mid(q):
    """the old quote CLI's mid: (bid + ask) / 2 to 4 places when both sides are quoted, else 0."""
    bid, ask = _px(q, "bid"), _px(q, "ask")
    return round((bid + ask) / 2.0, 4) if bid > 0 and ask > 0 else 0.0


def _strike(c):
    try:
        return float(c.get("strike") or 0)
    except (TypeError, ValueError):
        return 0.0


def select_long_call(chain, quotes, spot, session_iso):
    """desk/options_exec.select_long_call(ticker, spot, 0, 7, 0.02) over the chain snapshot: the nearest expiry
    0-7 DTE, its first strike >= spot x 1.02 in strike order, then that contract's quote: ask > 0 and, when
    bid > 0, (ask - bid) / mid <= 15%. None = no liquid call."""
    try:
        ref = date.fromisoformat(session_iso)
    except (TypeError, ValueError):
        return None
    by_exp = {}
    for c in chain or []:
        if c.get("type") not in (None, "call") or not c.get("symbol"):
            continue
        exp = str(c.get("expiration") or "")
        try:
            dte = (date.fromisoformat(exp[:10]) - ref).days
        except ValueError:
            continue
        if DTE_MIN <= dte <= DTE_MAX:
            by_exp.setdefault(exp, []).append(c)
    if not by_exp:
        return None
    expiry = sorted(by_exp)[0]
    target = spot * (1 + OTM_PCT)
    sel = next((c for c in sorted(by_exp[expiry], key=_strike) if _strike(c) >= target), None)
    if sel is None:
        return None
    q = (quotes or {}).get(sel["symbol"])
    if not q:
        return None
    ask, bid = _px(q, "ask"), _px(q, "bid")
    if ask <= 0:
        return None
    if bid > 0 and (ask - bid) / ((ask + bid) / 2) > QUOTE_GATE_FRAC:
        return None
    return {"occ": sel["symbol"], "strike": _strike(sel), "expiry": expiry[:10],
            "dte": (date.fromisoformat(expiry[:10]) - ref).days, "ask": ask, "bid": bid,
            "mid": round((ask + bid) / 2, 2) if bid > 0 else ask}


def qty_for_risk(ask, equity):
    """Contracts so the premium paid <= RISK_FRACTION of equity. Verbatim."""
    if not equity or equity <= 0 or not ask or ask <= 0:
        return 0
    return max(0, int((equity * RISK_FRACTION) // (ask * 100)))


def exit_due(pos, dte, mid, last_stock_close):
    """the old exit_due, first trigger wins: +75% on the quote's mid (mid None = no quote), the 1-DTE time stop,
    the underlying -3% from the entry. dte: days to expiry from the session."""
    entry_px = pos.get("entry_premium") or 0
    if mid is not None and entry_px > 0:
        if (mid or 0) >= PROFIT_TAKE_MULT * entry_px:
            return "profit_take_75pct"
    if dte is not None and dte <= EXIT_DTE:
        return "dte_time_stop"
    entry_stock = pos.get("entry_stock_px") or 0
    if last_stock_close and entry_stock > 0:
        if last_stock_close <= entry_stock * (1 - THESIS_BREAK_PCT):
            return "thesis_broken_-3pct"
    return None


def occ_expiry(occ):
    s = str(occ)[-15:]
    return "20%s-%s-%s" % (s[0:2], s[2:4], s[4:6])


def _dte(expiry, session_iso):
    try:
        return (date.fromisoformat(str(expiry)[:10]) - date.fromisoformat(session_iso)).days
    except (TypeError, ValueError):
        return None


def _day_limit(px, close_at):
    """a limit resting until filled or the session's close (the old's DAY orders)."""
    o = {"type": "limit", "limit_price": px}
    if close_at:
        o["not_after"] = float(close_at)
    return o


def decide(bars, context):
    """intents: the held calls' exits, then (on a scan pass) the basket's entries in order, at most MAX_POSITIONS
    calls live — held, closing or in flight (the old live_count: positions + awaiting fills + closing)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    h1map = extra.get("bars_1h") or {}
    oq = extra.get("option_quotes") or {}
    entering = set(extra.get("entering") or ())
    close_at = extra.get("session_close")
    today = context.session
    intents, live = [], 0
    for sym, st in state.items():
        st = st or {}
        pos = st.get("position")
        if pos or st.get("pending_entry"):
            live += 1
        if not pos or pos.get("exit_submitted") or sym in entering:
            continue                                  # closing (its close works) / its buy still works
        occ = pos.get("occ")
        qty = int(abs(float(pos.get("qty") or 0)))
        if not occ or qty <= 0:
            continue
        q = oq.get(occ)
        mid = None if q is None else quote_mid(q)
        h1 = h1map.get(sym) or []
        last = float(h1[-1]["c"]) if h1 else None
        held = {"entry_premium": round(float(pos.get("entry_px") or pos.get("ask") or 0), 2),
                "entry_stock_px": pos.get("entry_stock_px")}
        why = exit_due(held, _dte(pos.get("expiry") or occ_expiry(occ), today), mid, last)
        bid = _px(q, "bid")
        if not why or q is None or bid <= 0:
            continue                                  # the old close_call: no quote / no bid -> no close
        intents.append(Intent(
            "exit", sym, qty_hint=qty, order=_day_limit(round(bid, 2), close_at),
            signal_key="%s:%s:cap-exit" % (occ, today),
            reason="capitulation_options exit: %s occ=%s bid=%.2f mid=%s premium=%.2f last=%s"
                   % (why, occ, bid, mid, held["entry_premium"], last)))
    equity = float(context.equity or 0.0)
    if not extra.get("scan", True) or equity <= 0:
        return intents                                # the reconcile echo makes no entries
    chains = extra.get("chains") or {}
    fear_ok = extra.get("fear_ok", True)
    for sym in extra.get("universe") or sorted(bars):
        daily = bars.get(sym) or []
        h1 = h1map.get(sym) or []
        if len(daily) < DAILY_MIN_BARS or len(h1) < H1_MIN_BARS:
            continue
        st = state.get(sym) or {}
        if st.get("position") or st.get("pending_entry") or sym in entering or live >= MAX_POSITIONS:
            continue
        sig = capitulation_signal(h1, daily)
        if not sig or not fear_ok:
            continue                                  # fear gate closed: DEFER, the signal stays eligible
        spot = float(h1[-1]["c"])
        rows = chains.get(sym) or []
        call = select_long_call(rows, {r["symbol"]: r for r in rows if r.get("symbol")}, spot, today)
        if not call:
            continue
        qty = qty_for_risk(call["ask"], equity)
        if qty <= 0:
            continue
        intents.append(Intent(
            "enter", sym, qty_hint=qty, asset="option",
            legs=({"symbol": call["occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},),
            order=_day_limit(call["ask"], close_at),
            signal_key="%s:%s:cap-call" % (sym, h1[-1].get("t")),
            position_meta={"occ": call["occ"], "strike": call["strike"], "expiry": call["expiry"],
                           "dte_at_entry": call["dte"], "ask": call["ask"], "bid": call["bid"],
                           "entry_stock_px": round(spot, 2), "signal_bar": h1[-1].get("t"), "rsi": sig["rsi"],
                           "rsi_now": sig["rsi_now"], "climax_vol_mult": sig["climax_vol_mult"],
                           "ema200": sig["ema200"], "climax_low": sig["climax_low"]},
            reason="capitulation_options long call: %s strike %.2f expiry %s dte %d ask %.2f x%d; rsi %.1f -> %.1f "
                   "vol %.2fx ema200 %.2f climax low %.2f; spot %.2f"
                   % (call["occ"], call["strike"], call["expiry"], call["dte"], call["ask"], qty, sig["rsi"],
                      sig["rsi_now"], sig["climax_vol_mult"], sig["ema200"], sig["climax_low"], spot)))
        live += 1
    return intents


class CapitulationOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(decide(bars, context))


def signal(bars, slice_state, context):
    return CapitulationOptions().signal(bars, slice_state, context)
