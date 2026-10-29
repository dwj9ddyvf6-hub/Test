"""master-desk: the old daily-cyan GBM and GBM-rule sleeves' rank (daily_cyan_gbm_sleeve / rule_1d_* / rule_1w_*
mode_rank over rule_sleeve_base) on the nightly DCG scoring file, and their fill through the old sleeve_core law
— market-on-close, the spec's order (tif "cls"): entry at the next session's close, exit at the close.

Rank (weekdays >= 16:30 ET, once per session, once the scoring file for the session exists): the sleeve's
candidates on their signal bar (the session's last bar) in the sleeve's order (the GBM: score descending; the
rules: the scorer's symbol order), deduped, staged into the free capacity (book + surviving buys + new buys <
10); positions with >= HOLD - 1 of their own bars after the entry date staged to sell (the MOC lands on the
HOLD-th close); exit backstop today + int(HOLD x 1.45) + 3; merged into the surviving pending (old buys first).
Fill (the next trading day 10:30-16:00 ET): sleeve_core.fill_intents."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import sleeve_core as core

ET = ZoneInfo("America/New_York")


def now_et(context):
    return datetime.fromtimestamp(float(context.now), tz=ET)


def phase(context, rank_hm, fill_hm):
    """rank: weekdays from the sleeve's rank minute; fill: weekdays from its fill minute to the close."""
    t = now_et(context)
    if t.weekday() >= 5:
        return None
    hm = (t.hour, t.minute)
    if hm >= rank_hm:
        return "rank"
    if fill_hm <= hm < (16, 0):
        return "fill"
    return None


def bar_dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat() for b in bars]


def rank(context, meta, signals, hold_bars, bars):
    """signals: [symbol] in the sleeve's order (already filtered on the signal bar). Returns the merged pending."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    today = context.session
    book = core.book_of(state)
    old = dict(meta.get("pending") or {})
    surv = list(old.get("buys") or [])
    buys, seen = [], set()
    for s in signals:
        if s in book or s in seen:
            continue
        if len(buys) + len(surv) + len(book) >= core.MAX_POSITIONS:
            break
        seen.add(s)
        buys.append(s)
    sells = []
    for s, p in book.items():
        entry = p.get("entry_date")
        bl = bars.get(s) or []
        if not entry or not bl:
            continue
        n = sum(1 for d in bar_dates(bl) if entry < d <= today)
        if n >= hold_bars - 1:
            sells.append(s)
    exit_dates = dict(old.get("exit_dates") or {})
    exit_dates.update({s: (date.fromisoformat(today) + timedelta(days=int(hold_bars * 1.45) + 3)).isoformat()
                       for s in buys})
    old_sells = list(old.get("sells") or [])
    return {"buys": core.merge_pending_buys(surv, buys, len(book)),
            "sells": old_sells + [s for s in sells if s not in old_sells], "exit_dates": exit_dates}


def fill(Intent, context, meta, cost, name, disaster_stop=None):
    extra = context.extra or {}
    close_ts = now_et(context).replace(hour=16, minute=0, second=0, microsecond=0).timestamp()
    intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                       float(context.equity or 0.0), extra.get("quotes") or {}, cost,
                                       context.session, float(context.now), name, close_ts,
                                       disaster_stop=disaster_stop)
    return intents


def next_meta(context, meta, signals_fn, hold_bars, bars, cost, name, rank_hm, fill_hm):
    """rank once per session (when the scoring file exists); after a fill pass, the fill law's leftovers."""
    extra = context.extra or {}
    meta = dict(meta or {})
    ph = phase(context, rank_hm, fill_hm)
    if ph == "rank" and meta.get("last_rank_date") != context.session:
        scores = extra.get("dcg")                       # sells never wait on the scoring file; buys rank once
        sig = signals_fn(scores, context) if scores is not None else []
        meta["pending"] = rank(context, meta, [s for s, _why in sig], hold_bars, bars)
        if scores is not None:
            meta["last_rank_date"] = context.session
            meta["last_signals"] = sig[:50]
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, cost, context.session,
                                 float(context.now), name)
        meta["pending"] = left
    return meta
