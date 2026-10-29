"""Momentum — lean-desk port.

EXTRACTED from the old desk's momentum_sleeve.py. compute_rank and
new_buy_gates ported verbatim in behavior (the desk-halt leg is core
Risk's job now and is dropped here — named in ports/momentum.md);
plumbing is core-owned.

Strategy (old module): rank the universe by 126-session return on last
COMPLETED bars; eligibility = price >= $5, 20d avg dollar volume >=
$1M, SOXL skipped; take the top tenth (capped at 10 positions) when at
least 10 names are eligible. Review every 63 sessions. Sleeve cap 30%
of equity. Circuit breaker: close a position down 40% from entry.
New-buy gates (old, verbatim): Friday after 14:00 ET, last 5 December
weekdays, FOMC blackout (prior session + both days), VIX unavailable/
stale (>4 calendar days) fail-closed, VIX > 32, VIX +25% day spike,
SPY -8%/20d with VIX rising.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {...} | None}}
  "vix": (close, prev_close, asof_iso, source) — absent = vix_unknown
  "universe": optional override (default: bars keys)
Bars: daily dicts {"t","o","h","l","c","v"} ascending; the last bar is
treated as completed iff its date < context.session (old last_completed).
"""
import math
from datetime import date, datetime, timedelta, timezone

from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

LOOKBACK = 126
REVIEW_EVERY = 63
TOP_FRAC = 0.10
MAX_POSITIONS = 10
SLEEVE_CAP = 0.30
MIN_PRICE = 5.0
MIN_DOLLAR_VOL = 1_000_000
SKIP_SYMBOLS = {"SOXL"}
BREAKER_DROP = 0.40
VIX_HIGH = 32.0
VIX_SPIKE = 0.25
SPY_DROP = -0.08
FOMC_2026 = [("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"),
             ("2026-04-28", "2026-04-29"), ("2026-06-16", "2026-06-17"),
             ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"),
             ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09")]
# master-desk: SPEC §7 ("2027 FOMC dates must be added here in January 2027") — the Fed's 2027 schedule
FOMC_2026 = FOMC_2026 + [("2027-01-26", "2027-01-27"), ("2027-03-16", "2027-03-17"),
                         ("2027-04-27", "2027-04-28"), ("2027-06-15", "2027-06-16"),
                         ("2027-07-27", "2027-07-28"), ("2027-09-21", "2027-09-22"),
                         ("2027-11-02", "2027-11-03"), ("2027-12-14", "2027-12-15")]

CONFIG = SleeveConfig(
    sleeve_id="momentum", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def last_completed(bars, today):
    """Bars strictly before today's session (old last_completed shape)."""
    ds = _dates(bars)
    return [b for b, d in zip(bars, ds) if d < today]


def compute_rank(bars_by_sym, today):
    """Verbatim port of the old compute_rank (corrupt-bar guards incl.)."""
    comp = {}
    for sym, bars in bars_by_sym.items():
        cb = last_completed(bars, today)
        if len(cb) >= LOOKBACK + 1:
            comp[sym] = cb
    spy_all = sorted(set(_dates(last_completed(bars_by_sym["SPY"], today)))) \
        if "SPY" in bars_by_sym else []
    eligible = []
    for sym, cb in comp.items():
        if sym in SKIP_SYMBOLS:
            continue
        c = cb[-1].get("c")
        if not isinstance(c, (int, float)) or isinstance(c, bool):
            continue
        if c < MIN_PRICE:
            continue
        dv20 = sum(b["c"] * b["v"] for b in cb[-20:]
                   if isinstance(b.get("c"), (int, float))
                   and isinstance(b.get("v"), (int, float))) / 20.0
        if dv20 < MIN_DOLLAR_VOL:
            continue
        dc = cb[-LOOKBACK - 1].get("c")
        if not dc:
            continue
        eligible.append({"symbol": sym, "ret126": c / dc - 1, "price": c,
                         "dollar_vol_20d": dv20, "bars": len(cb)})
    eligible.sort(key=lambda r: r["ret126"], reverse=True)
    k = max(1, int(len(eligible) * TOP_FRAC))
    k = min(k, MAX_POSITIONS)
    top = eligible[:k] if len(eligible) >= 10 else []
    flagged = set()
    scored = []
    for sym, cb in comp.items():
        if len(cb) >= 252 + 21 + 1:
            n22, d274 = cb[-22].get("c"), cb[-274].get("c")
            if not n22 or not d274:
                continue
            scored.append((sym, n22 / d274 - 1))
    if scored:
        scored.sort(key=lambda t: t[1], reverse=True)
        kf = max(1, int(len(scored) * 0.20))
        flagged = {s for s, _ in scored[:kf]}
    for r in eligible:
        r["overlap_252_21_flag"] = r["symbol"] in flagged
    return {"eligible": eligible, "top": [t["symbol"] for t in top],
            "top_detail": top, "n_eligible": len(eligible),
            "spy_sessions": spy_all,
            "session_idx": (spy_all.index(spy_all[-1]) if spy_all else None)}


def new_buy_gates(now_date, now_hm, vix, spy_bars, today):
    """Old new_buy_gates minus the risk_gate desk-halt leg (core Risk).
    now_date: date; now_hm: (hour, minute) ET; vix: tuple or None."""
    blocks = []
    if now_date.weekday() == 4 and now_hm[0] >= 14:
        blocks.append(("friday_pm", "Friday after 14:00 ET"))
    dec_weekdays = []
    d = date(now_date.year, 12, 1)
    while d.month == 12:
        if d.weekday() < 5:
            dec_weekdays.append(d.isoformat())
        d += timedelta(days=1)
    if today in dec_weekdays[-5:]:
        blocks.append(("year_end", "last 5 sessions of the year"))
    for d1s, d2s in FOMC_2026:
        d1 = date.fromisoformat(d1s)
        prev = d1 - timedelta(days=1)
        while prev.weekday() >= 5:
            prev -= timedelta(days=1)
        if today in (prev.isoformat(), d1s, d2s):
            blocks.append(("fomc", "FOMC blackout %s/%s/%s"
                           % (prev.isoformat(), d1s, d2s)))
            break
    if not vix:
        blocks.append(("vix_unknown", "VIX unavailable; buys wait"))
        return blocks
    vclose, vprev, vasof, vsrc = vix
    if vclose is None:
        blocks.append(("vix_unknown", "VIX unavailable (%s); buys wait" % vsrc))
    else:
        stale = False
        try:
            asof = date.fromisoformat(str(vasof)[:10])
            if (now_date - asof).days > 4:
                stale = True
        except (TypeError, ValueError):
            stale = True
        if stale:
            blocks.append(("vix_stale", "VIX as-of %s is stale (%s); buys wait"
                           % (vasof, vsrc)))
        if vclose > VIX_HIGH:
            blocks.append(("vix_high", "VIX %.1f > %.1f" % (vclose, VIX_HIGH)))
        if vprev and (vclose / vprev - 1) > VIX_SPIKE:
            blocks.append(("vix_spike", "VIX +%0.0f%% on the day"
                           % ((vclose / vprev - 1) * 100)))
        sc = last_completed(spy_bars or [], today)
        if len(sc) >= 21:
            try:
                c1, c21 = float(sc[-1]["c"]), float(sc[-21]["c"])
                if not (c1 > 0 and c21 > 0):
                    raise ValueError("non-positive SPY close")
                r20 = c1 / c21 - 1
            except (TypeError, ValueError, KeyError):
                r20 = None
            if r20 is not None and r20 <= SPY_DROP and vprev and vclose > vprev:
                blocks.append(("spy_drop_vix_up",
                               "SPY %.1f%%/20d and VIX rising" % (r20 * 100)))
    return blocks


def cost_bps(price):
    """Verbatim old cost_bps tiers (paper calibration reference)."""
    if price >= 20:
        return 0.0010
    if price >= 5:
        return 0.0025
    return 0.0050


def review_plan(bars, state, meta, today):
    """master-desk: the old mode_rank decision verbatim in behaviour — rank on completed bars, a review
    every 63 SPY sessions (or on the first rank), target = top tenth on review else the current book,
    sells = book - target (minus working exits), buys = target - book - pending entries.
    Returns None when the rank waits (SPY missing/stale), else a dict."""
    rank = compute_rank(bars, today)
    spy = rank["spy_sessions"]
    if not spy:
        return None
    prev = date.fromisoformat(today) - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    if spy[-1] < prev.isoformat():
        return None                                   # old: SPY bars stale -> rank waits
    book = {s: (st or {}).get("position") for s, st in state.items() if (st or {}).get("position")}
    pend_entry = {s for s, st in state.items() if (st or {}).get("pending_entry")}
    pend_exit = {s for s, p in book.items() if p.get("exit_submitted")}
    last_rev = meta.get("last_review_spy_date")
    is_first = not book and not meta.get("ranked")
    due = is_first or last_rev is None or sum(1 for d in spy if d > last_rev) >= REVIEW_EVERY \
        or review_lost(meta, state, book, pend_entry)
    target = list(rank["top"]) if due else sorted(book)
    sells = [s for s in book if s not in target and s not in pend_exit]
    buys = [s for s in target if s not in book and s not in pend_entry]
    return {"rank": rank, "review": due, "target": target, "sells": sells, "buys": buys,
            "spy_last": spy[-1], "book": book, "pend_entry": pend_entry, "pend_exit": pend_exit}


def review_lost(meta, state, book, pend_entry):
    """master-desk (roll call 2026-10-26): a review stamped before reviews recorded their sends ("review_sent")
    whose book never held a name since — its buys were never sent, so the review is still due. femto_momentum's
    only review ran at the 2026-10-16 14:07Z pass in the Alpaca credentials outage, sent no buy and stamped itself."""
    last_rev = meta.get("last_review_spy_date")
    if not last_rev or "review_sent" in meta or book or pend_entry:
        return False
    return not any(str((st or {}).get("last_exit_date") or "") >= last_rev for st in state.values())


def next_meta(bars, slice_state, context, out=()):
    """master-desk: the old rank's state stamps (persisted sleeve meta): ranked; review date on a review — once
    its buys are sent (or it needed none). A review whose buys all wait (a buy gate, no fresh quote, no budget) stays
    due, as the old gates' "buys wait" says: stamped regardless, it emptied the book until the next review."""
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    plan = review_plan(bars, extra.get("sleeve_state") or {}, meta, context.session)
    if plan is None:
        return meta
    meta["ranked"] = True
    if plan["review"]:
        sent = sum(1 for i in out or () if i.kind == "enter")
        if sent or not plan["buys"]:
            meta["last_review_spy_date"] = plan["spy_last"]
            meta["review_sent"] = sent
    return meta


def _mid(q):
    try:
        bid, ask = float(q.get("bid") or q.get("bp") or 0), float(q.get("ask") or q.get("ap") or 0)
    except (TypeError, ValueError, AttributeError):
        return None
    return (bid + ask) / 2 if bid > 0 and ask > 0 else None


class Momentum(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old rank (16:05) + fill (10:05) pair as one 10:05 pass on the same completed
        bars: review plan -> rank sells -> 40% breaker on a fresh mid -> gated buys sized from the 30%
        sleeve budget left after book + pending notional, split over the review target, all-in price
        mid x (1 + cost_bps), 1-share minimum (Decision #20), book capped at 10."""
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        meta = extra.get("meta") or {}
        quotes = extra.get("quotes") or {}
        equity = float(context.equity or 0.0)
        today = context.session
        now_et = datetime.fromtimestamp(float(context.now), tz=ET)
        if (now_et.hour, now_et.minute) < (10, 0):
            return []                                  # old fill clock: never before 10:00 ET
        intents = []
        plan = review_plan(bars, state, meta, today)
        book = {s: (st or {}).get("position") for s, st in state.items() if (st or {}).get("position")}
        done_sells = set()
        for sym in (plan or {}).get("sells", []):
            mid = _mid(quotes.get(sym) or {})
            p = book.get(sym) or {}
            qty = int(float(p.get("qty") or 0))
            if mid is None or qty <= 0:
                continue                               # old: sell_quote_stale -> not sold this pass
            intents.append(Intent("exit", sym, qty_hint=qty, price_hint=round(mid, 2),
                                  reason="momentum rank_exit (review target %s)" % ",".join(plan["target"])))
            done_sells.add(sym)
        for sym, p in book.items():                    # 40% circuit breaker on a fresh regular-hours mid
            if sym in done_sells or p.get("exit_submitted"):
                continue
            qty = int(float(p.get("qty") or 0))
            entry = float(p.get("entry_px") or 0)
            mid = _mid(quotes.get(sym) or {})
            if qty <= 0 or entry <= 0 or mid is None:
                continue
            if mid <= (1 - BREAKER_DROP) * entry:
                intents.append(Intent("exit", sym, qty_hint=qty, price_hint=round(mid, 2),
                                      reason="momentum breaker_40pct: mid %.2f <= 0.60 x entry %.2f" % (mid, entry)))
                done_sells.add(sym)
        if plan is None or not plan["buys"] or equity <= 0:
            return intents
        blocks = new_buy_gates(now_et.date(), (now_et.hour, now_et.minute), extra.get("vix"), bars.get("SPY"), today)
        if blocks:
            return intents
        pend = {s: (st or {}).get("pending_entry") for s, st in state.items() if (st or {}).get("pending_entry")}
        book_not = sum(float(p.get("qty") or 0) * float(p.get("entry_px") or p.get("ref_px") or 0)
                       for p in book.values())
        pend_not = sum(float(pe.get("qty") or 0) * float(pe.get("ref_px") or pe.get("entry_px") or 0)
                       for pe in pend.values())
        budget = max(0.0, SLEEVE_CAP * equity - book_not - pend_not)
        if budget == 0:
            return intents
        n_target = max(1, len(plan["target"] or plan["buys"]))
        n_open = len(book) + len(pend)
        for sym in plan["buys"]:
            if n_open - len(done_sells) >= MAX_POSITIONS:
                continue
            mid = _mid(quotes.get(sym) or {})
            if mid is None:
                continue                               # old: buy_quote_stale
            all_in = mid * (1.0 + cost_bps(mid))
            qty = max(1, math.floor((budget / n_target) / all_in)) if all_in > 0 else 1
            row = next((r for r in plan["rank"]["top_detail"] if r["symbol"] == sym), {})
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(mid, 2),
                reason="momentum review buy: ret126=%s cost_bps=%.4f"
                       % (round(row.get("ret126", 0.0), 4), cost_bps(mid)),
                position_meta={"ref_px": round(mid, 2), "cost_bps": cost_bps(mid) * 1e4}))
            n_open += 1
        return intents


def signal(bars, slice_state, context):
    return Momentum().signal(bars, slice_state, context)
