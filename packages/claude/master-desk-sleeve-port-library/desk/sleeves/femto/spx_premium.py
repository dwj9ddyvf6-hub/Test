"""SPX Premium — ATR index premium selling (XSP weeklies) — lean port.

master-desk: the old desk's spx_premium.py (the Milkman Trades author's spec) restored on the engine.

  entry .... the week's first trading session (Monday; Tuesday after a Monday holiday) from 10:00 ET, once per
             ISO week, flat, outside the cooldown, book equity >= $37,000: the last completed week's close and
             Wilder ATR14 on weekly bars of the XSP level (S&P 500 / 10; at least 15 completed weeks);
             short put = round1(close - 1 x ATR14), long put 5 points below; expiry = this week's latest XSP
             expiration (its last session); skip unless the natural credit (short bid - wing ask) is > 0;
             1 lot, both legs as one spread at the natural credit.
  exit ..... none — held to settlement (the author's rule): XSP is PM-settled in cash; the engine settles each
             leg at intrinsic on the expiry session's S&P 500 close / 10.
  cooldown . a settlement losing >= 90% of the 5-wide wing (<= -$450) arms a 4-ISO-week entry cooldown (Monty
             Carlo): no entry while this week <= the settlement day's week + 4.

Gone under the cutover doctrine: the risk gate, drawdown brake, circuit breaker, context gate and 150% desk cap
(the chart gate never applied: Decision #85 / #96, a net-credit sale). Named divergences: the weekly levels are
the S&P 500 index's daily sessions / 10 over two years (the old resampled ~1500 SPY 1H SIP bars, extended hours
included: its weekly close was the last after-hours print and its ATR seeded ~19 weeks back); held to the cash
settlement (the old bought both legs back at the touch at 15:55 on the last session, a paper adaptation of the
author's hold-to-settlement); the entry is evaluated in the 10:00 hour (the old cron ran once at 10:07): a
decision (an entry, no positive credit, missing contracts) closes the week, a data failure retries in the hour;
the first session comes from the desk calendar (the old read which dates had SPY 1H bars).

Inputs via context.extra:
  "spx"           {"^GSPC": daily bars} (Yahoo, completed sessions)
  "chain"         {"XSP": chain rows {"symbol","strike","expiration","type","bid","ask",...}} (puts, 0-7 DTE)
  "traded_dates"  ["YYYY-MM-DD", ...] trading sessions of this week (the desk calendar)
  "meta"          {"last_entry_week", "cooldown_until", "open", "closed"}
  "closed_trades" the sleeve's closed trades (the settlement P&L)
  "sleeve_state"  {"XSP": {"position": spread | None, "pending_entry": ...}}"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

WING_WIDTH = 5
ATR_PERIOD = 14
SPX_EQUIV = 1.0
LOT_QTY = 1
EQUITY_GATE = 37000.0
ENTRY_HOUR_ET = 10
FULL_WIDTH_LOSS_USD = -(WING_WIDTH * 100.0 * 0.9)
COOLDOWN_WEEKS = 4
UNDERLYING = "XSP"
INDEX = "^GSPC"
INDEX_DIV = 10.0
ENTRY_WINDOW_S = 300
GATE_EXEMPT_DECISION75 = True  # Decision #85 extended by #96

CONFIG = SleeveConfig(
    sleeve_id="spx_premium", cadence_s=300, universe=(UNDERLYING,),
    state_schema={"position": "dict|None", "cooldown_until": "list|None",
                  "last_entry_week": "list|None"},
    risk_pct=None)


# ------------------------------------------------------- verbatim math
def round5(x):
    """Round to the nearest 5 (author's strike rule, SPX scale)."""
    return int(5 * round(float(x) / 5.0))


def round1(x):
    """Round to the nearest 1 (XSP scale: $1 strikes)."""
    return int(round(float(x)))


def wilder_atr(weekly, period=ATR_PERIOD):
    """Wilder ATR over weekly bars; SMA-seeded at index period-1,
    None before. Verbatim (numpy -> lists)."""
    n = len(weekly)
    trs = []
    for i, b in enumerate(weekly):
        pc = float(weekly[i - 1]["c"]) if i > 0 else float(b["c"])
        trs.append(max(float(b["h"]) - float(b["l"]),
                       abs(float(b["h"]) - pc), abs(float(b["l"]) - pc)))
    atr = [None] * n
    if n >= period:
        atr[period - 1] = sum(trs[:period]) / period
        for i in range(period, n):
            atr[i] = atr[i - 1] + (trs[i] - atr[i - 1]) / period
    return atr


def atr_level_strikes(prior_close, atr14):
    """Author's strike rule: (short, long) on the XSP scale."""
    short = round1(prior_close - 1.0 * atr14)
    return short, short - WING_WIDTH


def natural_credit(bid_short, ask_long):
    return float(bid_short) - float(ask_long)


def settle_pnl(credit_pts, k_short, k_long, settle):
    """Settlement P&L in USD for the put credit spread. Verbatim."""
    width = k_short - k_long
    intrinsic_owed = max(0.0, min(k_short - settle, width))
    return credit_pts * 100.0 - intrinsic_owed * 100.0


def is_full_width_loss(pnl_usd):
    return pnl_usd <= FULL_WIDTH_LOSS_USD


def iso_week_tuple(dt):
    iso = dt.isocalendar()
    return [iso[0], iso[1]]


def week_leq(a, b):
    return (a[0], a[1]) <= (b[0], b[1])


def cooldown_until_week(today, weeks=COOLDOWN_WEEKS):
    return iso_week_tuple(today + timedelta(weeks=weeks))


def entry_day_ok(now_et, traded_dates):
    """(ok, reason): now_et (a datetime) is the week's first trading
    day and >= 10:00 ET. Verbatim logic; traded_dates = set of dates."""
    today = now_et.date()
    if today not in traded_dates:
        return False, "market_closed"
    wd = now_et.weekday()
    if wd == 0:
        ok_day, reason = True, "monday"
    elif wd == 1:
        monday = today - timedelta(days=1)
        if monday in traded_dates:
            return False, "not_first_trading_day"
        ok_day, reason = True, "tuesday_after_monday_holiday"
    else:
        return False, "not_first_trading_day"
    if (now_et.hour, now_et.minute) < (ENTRY_HOUR_ET, 0):
        return False, "too_early"
    return ok_day, reason


def _session(t):
    return datetime.fromtimestamp(float(t), tz=ET).date()


def weekly_bars(daily, div=INDEX_DIV):
    """daily index sessions -> weekly bars (the old resample('W-FRI'): open first, high max, low min, close last),
    scaled to the XSP level, oldest first; each carries its ISO week."""
    out = []
    for b in daily or []:
        d = _session(b["t"])
        wk = iso_week_tuple(d)
        o, h, l, c = (float(b[k]) / div for k in ("o", "h", "l", "c"))
        if out and out[-1]["week"] == wk:
            w = out[-1]
            w["h"], w["l"], w["c"], w["last"] = max(w["h"], h), min(w["l"], l), c, d.isoformat()
        else:
            out.append({"week": wk, "o": o, "h": h, "l": l, "c": c, "last": d.isoformat()})
    return out


def prior_week_level(weekly, this_week):
    """the old prior_week_level: (close, Wilder ATR14) of the last week fully completed before this one; (None,
    None) with fewer than ATR_PERIOD + 1 completed weeks."""
    done = [w for w in weekly if (w["week"][0], w["week"][1]) < (this_week[0], this_week[1])]
    if len(done) < ATR_PERIOD + 1:
        return None, None
    atr = wilder_atr(done)
    return float(done[-1]["c"]), float(atr[-1])


def pick_spread(chain, k_short, k_long, monday, friday):
    """this week's latest put expiration (Monday..Friday) and its two contracts, or a skip reason."""
    rows = [r for r in chain or [] if r.get("type", "put") == "put"
            and monday <= str(r.get("expiration") or "")[:10] <= friday]
    exps = sorted({str(r["expiration"])[:10] for r in rows})
    if not exps:
        return None, "no_weekly_expiry"
    expiry = exps[-1]

    def occ_for(k):
        for r in rows:
            try:
                if str(r["expiration"])[:10] == expiry and abs(float(r["strike"]) - k) < 0.01:
                    return r
            except (KeyError, TypeError, ValueError):
                continue
        return None
    s, w = occ_for(k_short), occ_for(k_long)
    if not s or not w:
        return None, "contracts_unavailable"
    return (expiry, s, w), None


def decide(context):
    """the old run_entry decision: (intent | None, reason, decided) — decided = the week is spent."""
    extra = context.extra or {}
    meta = extra.get("meta") or {}
    st = (extra.get("sleeve_state") or {}).get(UNDERLYING) or {}
    now_et = datetime.fromtimestamp(float(context.now), tz=timezone.utc).astimezone(ET)
    traded = set()
    for d in extra.get("traded_dates") or []:
        try:
            traded.add(date.fromisoformat(str(d)[:10]))
        except ValueError:
            continue
    ok, reason = entry_day_ok(now_et, traded)
    if not ok:
        return None, reason, False
    wk = iso_week_tuple(now_et)
    cd = meta.get("cooldown_until")
    if cd and week_leq(wk, cd):
        return None, "cooldown_active", False
    if meta.get("last_entry_week") == wk:
        return None, "already_entered_this_week", False
    if st.get("position") or st.get("pending_entry") or meta.get("open"):
        return None, "position_already_open", False
    if float(context.equity or 0.0) < EQUITY_GATE:
        return None, "equity_below_live_gate", False
    weekly = weekly_bars((extra.get("spx") or {}).get(INDEX))
    prior_close, atr14 = prior_week_level(weekly, wk)
    if prior_close is None:
        return None, "insufficient_history", False
    k_short, k_long = atr_level_strikes(prior_close, atr14)
    monday = (now_et - timedelta(days=now_et.weekday())).date()
    friday = monday + timedelta(days=4)
    chain = (extra.get("chain") or {}).get(UNDERLYING)
    if chain is None:
        return None, "chain_error", False
    picked, why = pick_spread(chain, k_short, k_long, monday.isoformat(), friday.isoformat())
    if picked is None:
        return None, why, True
    expiry, s, w = picked
    if s.get("bid") is None or w.get("ask") is None:
        return None, "quote_error", False
    bid_short, ask_long = float(s.get("bid") or 0), float(w.get("ask") or 0)
    credit = natural_credit(bid_short, ask_long)
    if credit <= 0:
        return None, "no_positive_credit", True
    pm = {"short_occ": s["symbol"], "long_occ": w["symbol"], "short_strike": k_short, "long_strike": k_long,
          "expiry": expiry, "prior_weekly_close": round(prior_close, 2), "prior_week_atr14": round(atr14, 2),
          "bid_short": bid_short, "ask_long": ask_long, "credit_pts": round(credit, 2), "week": wk,
          "max_loss_usd": round((WING_WIDTH - credit) * 100, 2), "entry_day": reason}
    intent = Intent(
        "enter", UNDERLYING, qty_hint=LOT_QTY, asset="mleg",
        legs=({"symbol": s["symbol"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},
              {"symbol": w["symbol"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"}),
        net_price=-round(credit, 2), order={"window_s": ENTRY_WINDOW_S},
        signal_key="XSP:%d-W%02d:spread" % tuple(wk), position_meta=pm,
        reason="spx_premium put credit spread: short %s @%d long %s @%d expiry %s credit %.2f (prior close %.2f, "
               "ATR14 %.2f); held to settlement; Decision #85/#96 net-credit sale"
               % (s["symbol"], k_short, w["symbol"], k_long, expiry, credit, prior_close, atr14))
    return intent, "entry", True


class SpxPremium(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        intent, _why, _decided = _decide(context)
        return [intent] if intent else []


def _decide(context):
    """one decision per pass (signal and next_meta read the same one), keyed on the pass's context."""
    extra = context.extra
    memo = extra.get("_spx_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:            # one decision per pass's context (identity, not id())
        memo = (context, decide(context))
        if isinstance(extra, dict):
            extra["_spx_pass"] = memo
    return memo[1]


def signal(bars, slice_state, context):
    return SpxPremium().signal(bars, slice_state, context)


def settled(meta, state, closed, now):
    """the open spread's settlement once the book no longer holds it: (pnl | None, done). The P&L is the sum of
    the legs' closed trades since the entry (the realized credit less the intrinsic paid) — settle_pnl on the
    actual fills."""
    op = meta.get("open")
    if not op:
        return None, False
    st = state.get(UNDERLYING) or {}
    if st.get("position") or st.get("pending_entry"):
        return None, False
    legs = [t for t in closed or [] if str(t.get("symbol") or "") == UNDERLYING
            and float(t.get("closed_at") or 0) >= float(op.get("at") or 0)]
    if legs:
        return sum(float(t.get("pnl") or 0.0) for t in legs), True
    if float(now) - float(op.get("at") or 0) > ENTRY_WINDOW_S + 3600:
        return None, True                         # the spread never filled: nothing to settle
    return None, False


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    pnl, done = settled(meta, extra.get("sleeve_state") or {}, extra.get("closed_trades"), context.now)
    if done:
        op = meta.pop("open")
        if pnl is not None:
            exp = date.fromisoformat(str(op.get("expiry"))[:10])
            full = is_full_width_loss(pnl)
            if full:
                meta["cooldown_until"] = cooldown_until_week(exp)
            meta["closed"] = (list(meta.get("closed") or []) + [{"expiry": op.get("expiry"), "pnl_usd": round(pnl, 2),
                                                                 "full_width_loss": full}])[-20:]
    intent, _why, decided = _decide(context)
    now_et = datetime.fromtimestamp(float(context.now), tz=timezone.utc).astimezone(ET)
    if decided:
        meta["last_entry_week"] = iso_week_tuple(now_et)
    if intent is not None:
        pm = intent.position_meta or {}
        meta["open"] = {"at": float(context.now), "expiry": pm.get("expiry"), "short_occ": pm.get("short_occ"),
                        "long_occ": pm.get("long_occ"), "credit_pts": pm.get("credit_pts"), "week": pm.get("week")}
    return meta
