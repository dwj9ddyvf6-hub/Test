"""RSI Mean Reversion — Options (call debit spreads) — lean port (Wave B).

master-desk: the old desk's rsi_meanrev_options.py restored on the engine. The stock sleeve's exact signal (the old
imported rsi_meanrev_sleeve for it) — Connors' RSI(2) washout inside an uptrend — traded as a 14-30 DTE call debit
spread instead of stock; out at half the spread's max profit, at 7 DTE, or once RSI(2) is back above 70.

  universe . the basket (basket.json), in file order.
  signal ... the completed daily closes: at least 200 (fewer: no signal, fail closed), the stock sleeve's Wilder
             RSI(2) (pandas ewm alpha 1/2, seeded on the first change) < 10 and the close above its 200-day SMA.
  spread ... calls 14-30 DTE, the nearest expiry: long = the highest strike <= the signal close (to the cent; none at
             or below it: the lowest strike), short = the first strike >= long x 1.08 (none: no trade); both legs
             quoted; the long's ask > 0 and, when it is bid, (ask - bid) / mid <= 10%; debit = long ask - short bid
             > 0 (no debit / width band: fragment 098); floor(0.25% of equity / (debit x 100)) spreads (0: skip);
             at most 5 spreads held or in flight, the basket in order; the long bought and the short sold as one
             package at that natural debit, a day order.
  exits .... (never gated, every pass, the first that holds) the close value (long bid - short ask, both quoted)
             less the entry debit (the package fill) >= 50% of the max profit (width - debit at selection); <= 7
             days to expiry (the never-into-expiry rule); RSI(2) on the completed closes > 70 (the snapback is
             done); the package closes at its natural, a day order.

Gone under the cutover doctrine: the risk gate (the kill switch, consulted under the sleeve's own name), the
drawdown brake (its block and its halve-the-size verdicts), the Decision #75 chart gate (pre_buy's red-day gate and
chart read, the staging, its 72h pending TTL and the release replay with its re-checks), the 150% desk cap (with the
desk-exposure ledger that fed it) and the desk-wide Decision #8 earnings blackout (the stock sleeve's _earnings_ok,
borrowed: a desk rail in that sleeve's SPEC, as the restored equity sibling has it). Named divergences: one package
to open at the natural debit (the old sent the long at its ask, then the short at its bid, as two single-leg
orders: the same prices without the legging; a short leg bid at nothing, which the old's order CLI refused to
price, so the old bought the long alone and flattened it, now opens with the package) and one to close at its
natural (the old sent each leg at its own natural, and nothing while either leg was one-sided: a long leg bid at
zero now closes at zero instead of riding into expiry against the 7-DTE rule); hourly passes at :31 in the session
(the old cron ran hourly at :31 around the clock); the chain snapshot carries the legs' quotes (the old made a
separate latest-quote call for the two legs: a leg it got no quote for is a row with neither bid nor ask). The
old's fill promotion, partial-leg adoption, naked-leg flattening, dead-close retries and broker ghost-clears are
the OMS's and the book's.

Inputs via context.extra:
  "universe"      the basket in scan order (held names appended)
  "chains"        {SYM: call rows 14-30 DTE {"symbol","strike","expiration","bid","ask",...}} (fetched on demand)
  "option_quotes" {OCC: {"bid","ask"}} — the held legs
  "sleeve_state"  {SYM: {"position": spread group | None, "pending_entry": ...}}
Bars (arg): completed daily bars (260) of the basket and the held names."""
import math
from datetime import date, datetime

from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig
from .rsi_meanrev import rsi_wilder_last   # the stock sleeve's rsi_wilder, as the old imported it

_ET = ZoneInfo("America/New_York")

RSI_PERIOD = 2
RSI_OVERSOLD = 10.0
RSI_OVERBOUGHT = 70.0
MA200_PERIOD = 200
RISK_FRACTION = 0.0025
MAX_POSITIONS = 5
DTE_MIN, DTE_MAX = 14, 30
SPREAD_WIDTH_PCT = 0.08
PROFIT_TARGET_FRAC = 0.50
EXIT_DTE = 7
LIQ_GATE_FRAC = 0.10
RSI_EXIT_MIN_BARS = 5

CONFIG = SleeveConfig(
    sleeve_id="rsi_meanrev_options", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def rsi_signal(closes):
    """(bool, info): the old rsi_signal over the completed closes — fail closed under 200 bars, RSI(2) < 10, the
    close above its 200-day SMA. info carries rsi2 / close / sma200 rounded to the cent (the close, so rounded, is
    the stock price the spread is chosen on)."""
    if len(closes) < MA200_PERIOD:
        return False, {"note": "ma200_warmup", "bars": len(closes)}
    rsi = rsi_wilder_last(closes)
    if rsi is None or (isinstance(rsi, float) and math.isnan(rsi)) or rsi >= RSI_OVERSOLD:
        return False, {"rsi2": None if rsi is None else round(float(rsi), 2)}
    sma200 = sum(closes[-MA200_PERIOD:]) / MA200_PERIOD
    last_close = closes[-1]
    if last_close <= sma200:
        return False, {"rsi2": round(float(rsi), 2), "close": round(last_close, 2), "sma200": round(sma200, 2),
                       "note": "below_ma200"}
    return True, {"rsi2": round(float(rsi), 2), "close": round(last_close, 2), "sma200": round(sma200, 2)}


def current_rsi2(closes):
    """the old current_rsi2: the latest completed-bar RSI(2); None under 5 closes."""
    if len(closes) < RSI_EXIT_MIN_BARS:
        return None
    r = rsi_wilder_last(closes)
    return None if r is None or math.isnan(r) else float(r)


def _leg_quote(row):
    """the leg's latest quote as the old's quote CLI gave it ({bid, ask}, a missing side = 0), or None when the
    snapshot holds no quote at all (the old: no quote returned -> no spread)."""
    if row is None or (row.get("bid") is None and row.get("ask") is None):
        return None
    try:
        return {"bid": float(row.get("bid") or 0), "ask": float(row.get("ask") or 0)}
    except (TypeError, ValueError):
        return None


def pick_spread(chain, stock_price, session_iso, dte_min=DTE_MIN, dte_max=DTE_MAX, width_pct=SPREAD_WIDTH_PCT):
    """(spread | None, why): the old desk/options_exec.select_debit_spread on chain rows that carry their quotes,
    debit_range=None (fragment 098). The nearest expiry dte_min..dte_max days out; strikes in ascending order
    (stable): long = the last strike <= stock_price (none: the first), short = the first strike >= long x
    (1 + width_pct); the legs' quotes; the long ask > 0; the long's (ask - bid) / mid <= 10% when bid; debit =
    long ask - short bid > 0."""
    try:
        ref = date.fromisoformat(session_iso)
    except (TypeError, ValueError):
        return None, "bad_session"
    by_exp = {}
    for c in chain or []:
        if not c.get("tradable", True):                   # the old chain CLI's client-side tradable filter
            continue
        exp = str(c.get("expiration") or "")[:10]
        try:
            float(c["strike"])
            dte = (date.fromisoformat(exp) - ref).days
        except (KeyError, TypeError, ValueError):
            continue
        if dte_min <= dte <= dte_max:
            by_exp.setdefault(exp, []).append(c)
    if not by_exp:
        return None, "no_expiry_in_window"
    expiry = sorted(by_exp)[0]
    rows = sorted(by_exp[expiry], key=lambda c: float(c["strike"]))
    long_row = None
    for c in rows:
        if float(c["strike"]) <= stock_price:
            long_row = c
    if long_row is None:
        long_row = rows[0]
    long_strike = float(long_row["strike"])
    target_short = long_strike * (1 + width_pct)
    short_row = next((c for c in rows if float(c["strike"]) >= target_short), None)
    if short_row is None:
        return None, "no_short_strike"
    short_strike = float(short_row["strike"])
    width = short_strike - long_strike
    lq, sq = _leg_quote(long_row), _leg_quote(short_row)
    if lq is None or sq is None:
        return None, "leg_unquoted"
    long_ask, long_bid, short_bid = lq["ask"], lq["bid"], sq["bid"]
    if long_ask <= 0:
        return None, "long_no_ask"
    mid = (long_ask + long_bid) / 2 if long_bid > 0 else long_ask
    if long_bid > 0 and (long_ask - long_bid) / mid > LIQ_GATE_FRAC:
        return None, "long_illiquid"
    debit = long_ask - short_bid
    if debit <= 0:
        return None, "no_debit"
    return {"expiry": expiry,
            "long_leg": {"occ": long_row["symbol"], "strike": long_strike, "ask": long_ask, "bid": long_bid},
            "short_leg": {"occ": short_row["symbol"], "strike": short_strike, "bid": short_bid},
            "width": round(width, 2), "debit": round(debit, 2), "max_profit": round(width - debit, 2),
            "max_return_pct": round((width - debit) / debit * 100, 1),
            "breakeven": round(long_strike + debit, 2)}, "ok"


def select_debit_spread(chain, stock_price, session_iso, dte_min=DTE_MIN, dte_max=DTE_MAX,
                        width_pct=SPREAD_WIDTH_PCT):
    """the spread pick_spread chooses, or None."""
    return pick_spread(chain, stock_price, session_iso, dte_min, dte_max, width_pct)[0]


def size_spreads(equity, debit):
    """the old _size_spreads = options_exec.spread_qty_for_risk: int(equity x 0.25% / (debit x 100)), 0 on bad
    inputs (the drawdown brake's halving is gone with the brake)."""
    if not equity or equity <= 0 or debit <= 0:
        return 0
    budget = equity * RISK_FRACTION
    return max(0, int(budget / (debit * 100)))


def spread_close_value(spread, quotes):
    """the old spread_close_value: what closing pays now, long bid - short ask, to the cent; None unless both
    are > 0."""
    q = quotes or {}
    lq = q.get(spread["long_leg"]["occ"]) or {}
    sq = q.get(spread["short_leg"]["occ"]) or {}
    try:
        long_bid, short_ask = float(lq.get("bid") or 0), float(sq.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if long_bid <= 0 or short_ask <= 0:
        return None
    return round(long_bid - short_ask, 2)


def days_to_expiry(spread, session_iso):
    try:
        return (date.fromisoformat(str(spread["expiry"])[:10]) - date.fromisoformat(session_iso)).days
    except (KeyError, TypeError, ValueError):
        return None


def exit_due(spread, session_iso, close_value, closes):
    """the old exit_due, in its order: 50% of max profit, the 7-DTE time stop, RSI(2) > 70."""
    entry_debit = spread.get("entry_debit") or 0
    max_profit = spread.get("max_profit") or 0
    if close_value is not None and entry_debit > 0 and max_profit > 0:
        if close_value - entry_debit >= PROFIT_TARGET_FRAC * max_profit:
            return "profit_target_50pct"
    dte = days_to_expiry(spread, session_iso)
    if dte is not None and dte <= EXIT_DTE:
        return "dte_time_stop_%d" % dte
    rsi2 = current_rsi2(closes)
    if rsi2 is not None and rsi2 > RSI_OVERBOUGHT:
        return "rsi2_overbought_%.1f" % rsi2
    return None


def _occ_expiry(occ):
    t = str(occ)[-15:]
    return "20%s-%s-%s" % (t[0:2], t[2:4], t[4:6])


def held_spread(pos):
    """the held spread: its legs from the position's meta (both in the book's group), else the group's one long and
    one short leg (no max profit known); the entry debit is the package's net fill, to the cent."""
    legs = pos.get("legs") or {}
    sp = dict(pos.get("spread") or {})
    lo, so = (sp.get("long_leg") or {}).get("occ"), (sp.get("short_leg") or {}).get("occ")
    if not (lo and so and lo in legs and so in legs):
        longs = [o for o, q in legs.items() if float(q) > 0]
        shorts = [o for o, q in legs.items() if float(q) < 0]
        if len(longs) != 1 or len(shorts) != 1:
            return None
        sp = {"long_leg": {"occ": longs[0]}, "short_leg": {"occ": shorts[0]}, "expiry": _occ_expiry(shorts[0]),
              "max_profit": 0}
    sp["entry_debit"] = round(float(pos.get("net_entry") or 0.0), 2)
    return sp


def session_close_ts(session_iso):
    """16:00 ET of the session: a day order's end (the old's legs were day orders)."""
    d = date.fromisoformat(session_iso)
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=_ET).timestamp()


def _flight_symbol(key, pending):
    """the name an entry in flight belongs to: its signal key's symbol (a package in flight can be filed under the
    package's id)."""
    k = str((pending or {}).get("key") or "")
    return k.split(":", 1)[0] if ":" in k else key


def decide(bars, context):
    """intents: exits first (every held spread), then the basket's entries in order, at most MAX_POSITIONS spreads
    held or in flight."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    chains = extra.get("chains") or {}
    oq = extra.get("option_quotes") or {}
    equity = float(context.equity or 0.0)
    today = context.session
    day_end = session_close_ts(today)
    held, flight = set(), set()
    for key, st in state.items():
        st = st or {}
        if st.get("position"):
            held.add(key)
        elif st.get("pending_entry"):
            flight.add(_flight_symbol(key, st["pending_entry"]))
    intents = []
    for sym, st in state.items():
        pos = (st or {}).get("position")
        if not pos or pos.get("exit_submitted"):
            continue
        sp = held_spread(pos)
        n = int(abs(float(pos.get("qty") or 0)))
        if sp is None or n <= 0:
            continue
        cv = spread_close_value(sp, oq)
        closes = [float(b["c"]) for b in bars.get(sym) or []]
        why = exit_due(sp, today, cv, closes)
        if not why:
            continue
        intents.append(Intent(
            "exit", sym, qty_hint=n, order={"not_after": day_end}, signal_key="%s:%s:rmo-exit" % (sym, today),
            reason="rsi_meanrev_options exit: %s close_value=%s entry_debit=%.2f max_profit=%.2f legs=%s/%s"
                   % (why, cv, sp["entry_debit"], float(sp.get("max_profit") or 0), sp["long_leg"]["occ"],
                      sp["short_leg"]["occ"])))
    if equity <= 0:
        return intents
    live = len(held | flight)
    for sym in extra.get("universe") or sorted(bars):
        if sym in held or sym in flight:
            continue
        if live >= MAX_POSITIONS:
            break
        closes = [float(b["c"]) for b in bars.get(sym) or []]
        ok, info = rsi_signal(closes)
        if not ok:
            continue
        sp, _why = pick_spread(chains.get(sym), info["close"], today)
        if sp is None:
            continue
        qty = size_spreads(equity, sp["debit"])
        if qty <= 0:
            continue
        lo, so = sp["long_leg"], sp["short_leg"]
        intents.append(Intent(
            "enter", sym, qty_hint=qty, asset="mleg",
            legs=({"symbol": lo["occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},
                  {"symbol": so["occ"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"}),
            net_price=sp["debit"], order={"not_after": day_end}, signal_key="%s:%s:rmo" % (sym, today),
            position_meta={"spread": sp, "rsi2": info["rsi2"], "sma200": info["sma200"], "signal_close": info["close"]},
            reason="rsi_meanrev_options call debit spread: long %s @%.2f short %s @%.2f expiry %s width %.2f debit "
                   "%.2f max_profit %.2f x%d; rsi2 %.2f close %.2f sma200 %.2f"
                   % (lo["occ"], lo["strike"], so["occ"], so["strike"], sp["expiry"], sp["width"], sp["debit"],
                      sp["max_profit"], qty, info["rsi2"], info["close"], info["sma200"])))
        live += 1
    return intents


class RsiMeanrevOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(decide(bars, context))


def signal(bars, slice_state, context):
    return RsiMeanrevOptions().signal(bars, slice_state, context)
