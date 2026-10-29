"""Tensor Red Dip — lean-desk port.

master-desk: the old desk's tensor_red_dip_sleeve.py restored on the
engine. User's rule: "Buy on red fear days, sell into strength."

  signals .. the flagship's fresh signals of the day: the latest
             tensor_swing pass of this ET session whose decisions held
             any TRADE / WATCH (read_fresh_signals: the latest journal
             entry with fresh_signals wins; signals are day-scoped),
             confidence >= 7, the first listed wins per symbol (the
             flagship's basket order).
  fear ..... QQQ day-so-far <= -1.5% vs the prior close (red_day_gate
             day_return: the day's price over the prior session's
             close); unknown -> no entries this pass.
  entry .... per signal, in order: 5 positions at most (held names and
             working entries — the old counted every state record), not
             held or working, the symbol itself strictly red on the day
             (unknown -> deferred, the signal stays eligible while
             fresh), a price, floor(0.25% x equity / (price x 8%))
             shares (at least 1, else skipped); a market buy.
  exits .... (never gated) price >= entry x 1.03: strength_target;
             price <= entry x 0.92: stop_loss; the 3rd trading day after
             the entry day (entry day = 0; weekdays minus NYSE
             holidays): time_stop_3d — in that precedence, a market
             sell. The engine carries the same law measured from the
             actual fill (target_pct 3 / stop_pct 8 / time_sessions 3)
             at its tick; the pass checks it on its own quotes.

Gone under the cutover doctrine: the desk kill switch, the Decision #75
chart gate (pre_buy staging, its release pass and staged TTL), the
earnings blackout (Decision #8, desk-wide) and the 150% desk cap.
Named divergences: the fresh signals arrive as the flagship's
structured decisions (the old parsed the journal's "SYM DEC conf=N
PHENO" strings); the day's price is the live quote, mid when two-sided
(the old read the latest 1H IEX bar's running close); the prior close
is the prior session's split-adjusted daily close, required to be that
session (the old read the IEX daily bar before today); passes run every
5 minutes of the session (the old cron ran at :05 / :35 around the
clock, its off-hours market orders queued for the open); positions are
the sleeve's own book. Same-day re-entry after an exit stays possible,
as in the old (each round trip its own order key).

Inputs via context.extra:
  "fresh"         {"session", "at", "signals": [{"symbol","decision","confidence","phenotype"}]}
  "quotes"        {SYM: {"bid","ask","last","t"}} — QQQ, the basket, held names
  "prev_session"  "YYYY-MM-DD" — the session whose close is the prior close
  "nyse_holidays" ["YYYY-MM-DD", ...]
  "closed_trades" the sleeve's own closed trades (re-entry order keys)
  "sleeve_state"  {SYM: {"position": {"entry_px","entry_date","qty"} | None, "pending_entry": ...}}
Bars: completed daily bars (the prior close)."""
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
FEAR_QQQ_PCT = -1.5
MIN_CONF = 7
RISK_FRACTION = 0.0025
STOP_LOSS_PCT = 0.08
STRENGTH_TARGET_PCT = 0.03
HOLD_DAYS = 3
MAX_POSITIONS = 5
FEAR_SYMBOL = "QQQ"

CONFIG = SleeveConfig(
    sleeve_id="tensor_red_dip", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def filter_signals(signals):
    """read_fresh_signals' filter+dedupe, verbatim in behavior:
    confidence >= MIN_CONF only; de-dupe by symbol, first wins."""
    seen, out = set(), []
    for s in signals or []:
        if not isinstance(s, dict):
            continue
        sym = str(s.get("symbol") or "").upper()
        if not sym:
            continue
        try:
            conf = int(s.get("confidence"))
        except (TypeError, ValueError):
            continue
        if conf < MIN_CONF:
            continue
        if sym in seen:
            continue
        seen.add(sym)
        out.append({"symbol": sym, "decision": s.get("decision"),
                    "confidence": conf,
                    "phenotype": (str(s.get("phenotype") or "").upper() or None)})
    return out


def size_qty(equity, price):
    """Verbatim old size_qty: floor(risk$ / (price x 8%)); 0 when the
    inputs are unusable (caller skips), else at least 1."""
    if not equity or not price or price <= 0:
        return 0
    qty = math.floor((equity * RISK_FRACTION) / (price * STOP_LOSS_PCT))
    return max(1, qty) if qty >= 1 else 0


def trading_days_held(entry_date_iso, today_iso, holidays=()):
    """Verbatim old _trading_days_held with the holiday set injected
    (weekdays minus NYSE holidays; entry day = 0)."""
    try:
        d0 = date.fromisoformat(str(entry_date_iso)[:10])
        d1 = date.fromisoformat(str(today_iso)[:10])
    except (ValueError, TypeError):
        return 0
    if d1 <= d0:
        return 0
    hols = set(holidays or ())
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in hols:
            n += 1
    return n


def exit_reason(pos, last_px, today_iso, holidays=()):
    """Verbatim old manage_exits precedence: strength target, then the
    stop, then the 3-trading-day time stop. None = hold."""
    entry_px = float(pos.get("entry_px") or 0)
    if not entry_px or not last_px:
        return None
    if last_px >= entry_px * (1.0 + STRENGTH_TARGET_PCT):
        return "strength_target"
    if last_px <= entry_px * (1.0 - STOP_LOSS_PCT):
        return "stop_loss"
    if trading_days_held(pos.get("entry_date"), today_iso, holidays) >= HOLD_DAYS:
        return "time_stop_3d"
    return None


def _et_date(t):
    return datetime.fromtimestamp(float(t), tz=ET).date().isoformat()


def live_price(q, session):
    """the day's price from a quote stamped in this session: the mid when two-sided, else the last trade.
    None when unknown (the old: no intraday bar today yet -> defer)."""
    if not q:
        return None
    try:
        if q.get("t") is None or _et_date(q["t"]) != session:
            return None
        bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
        if bid and ask and float(ask) >= float(bid) > 0:
            return (float(bid) + float(ask)) / 2
        return float(last) if last and float(last) > 0 else None
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def prior_close(daily, prev_session):
    """the close of the prior session's completed daily bar (None unless the newest bar not after it IS that
    session — a gap in the series never stands in for the prior close)."""
    if not prev_session:
        return None
    for b in reversed(daily or []):
        try:
            d = _et_date(b["t"])
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            return None
        if d > prev_session:
            continue
        if d != prev_session:
            return None
        try:
            c = float(b["c"])
        except (KeyError, TypeError, ValueError):
            return None
        return c if c > 0 else None
    return None


def day_return(daily, q, session, prev_session):
    """(ret | None, detail): the day-so-far return vs the prior close (red_day_gate.day_return)."""
    pc = prior_close(daily, prev_session)
    if pc is None:
        return None, "no prior close (%s) (deferring)" % prev_session
    px = live_price(q, session)
    if px is None:
        return None, "no price on %s yet (deferring)" % session
    ret = px / pc - 1.0
    return ret, "day-so-far %.2f%% vs prior close %.2f" % (ret * 100.0, pc)


def _book(state):
    return {s: st["position"] for s, st in (state or {}).items() if (st or {}).get("position")}


def _working(state):
    return {s for s, st in (state or {}).items() if (st or {}).get("pending_entry") and not (st or {}).get("position")}


def entry_key(sym, session, closed=()):
    """one order key per round trip: the old minted a fresh client order id per submit, so a name exited
    today can be bought again today."""
    n = 0
    for t in closed or ():
        try:
            if str(t.get("symbol") or "").upper() == sym and _et_date(t["closed_at"]) == session:
                n += 1
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            continue
    return "%s:%s:enter" % (sym, session) + (":%d" % n if n else "")


class TensorRedDip(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        holidays = extra.get("nyse_holidays") or ()
        quotes = extra.get("quotes") or {}
        today = context.session
        prev = extra.get("prev_session")
        equity = float(context.equity or 0.0)
        intents = []
        book = _book(state)
        working = _working(state)
        # exits first (never gated)
        for sym, p in book.items():
            if p.get("exit_submitted"):
                continue
            px = live_price(quotes.get(sym), today)
            if px is None:
                continue                                  # exit_price_unknown: deferred
            why = exit_reason(p, px, today, holidays)
            qty = int(float(p.get("qty") or 0))
            if why and qty > 0:                           # one exit key per position (its open)
                opened = p.get("opened_at")
                intents.append(Intent(
                    "exit", sym, qty_hint=qty, price_hint=round(px, 2),
                    signal_key="%s:%s:exit" % (sym, int(float(opened)) if opened is not None else today),
                    reason="tensor_red_dip exit: %s" % why))
        # entries: a fear day (QQQ day-so-far <= -1.5%), fail closed on an unknown QQQ return
        fresh = extra.get("fresh") or {}
        if fresh.get("session") != today or equity <= 0 or prev is None:
            return intents
        qret, _qd = day_return((bars or {}).get(FEAR_SYMBOL), quotes.get(FEAR_SYMBOL), today, prev)
        if qret is None or qret * 100.0 > FEAR_QQQ_PCT:
            return intents
        n_open = len(book) + len(working)
        closed = extra.get("closed_trades") or ()
        for s in filter_signals(fresh.get("signals")):
            sym = s["symbol"]
            if n_open >= MAX_POSITIONS:
                break
            if sym in book or sym in working:
                continue
            r, _rd = day_return((bars or {}).get(sym), quotes.get(sym), today, prev)
            if r is None or not r < 0.0:
                continue                                  # deferred_symbol_not_red: stays eligible while fresh
            px = live_price(quotes.get(sym), today)
            qty = size_qty(equity, px)
            if qty <= 0:
                continue
            stop_px = round(px * (1 - STOP_LOSS_PCT), 2)
            target_px = round(px * (1 + STRENGTH_TARGET_PCT), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2), stop=stop_px, target=target_px,
                exit_rules=(ExitRule("stop", stop_px), ExitRule("target", target_px),
                            ExitRule("time_bars", float(HOLD_DAYS))),
                order={"type": "market"}, signal_key=entry_key(sym, today, closed),
                position_meta={"signal_phenotype": s["phenotype"], "signal_conf": s["confidence"],
                               "tensor_decision": s["decision"], "qqq_day_pct": round(qret * 100.0, 2),
                               "sym_day_pct": round(r * 100.0, 2)},
                reason="tensor_red_dip: fear day QQQ %.2f%%, %s conf=%d pheno=%s, sym red %.2f%%"
                       % (qret * 100.0, s["decision"], s["confidence"], s["phenotype"], r * 100.0)))
            n_open += 1
        return intents


def signal(bars, slice_state, context):
    return TensorRedDip().signal(bars, slice_state, context)
