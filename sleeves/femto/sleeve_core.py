"""master-desk: the old desk's sleeve_core fill law (rank -> pending -> run_fill), as pure functions.

The old core sleeves (snapback, daily_cyan_gbm, leader_d/sc, gate_1h, the rule_* family, ...) staged a rank's
buys/sells/exit dates into `pending` and executed them at a fill pass (sleeve_core.Sleeve.run_fill). The
femto ports kept each rank but replaced the fill with a flat 1%-of-equity size; this module restores the old
fill law. Desk-wide gates the old run_fill also applied — risk gate, circuit breaker, context gate, drawdown
brake, red/green-day gates, Decision #75 buy-delay and chart gate, the 150% desk cap — are out of scope by
the cutover doctrine; the market-condition bundle (VIX/SPY/FOMC/year-end) was already log-only there
(Decision #90). What stays, verbatim:

  sells   the rank's staged sells + every position whose exit_due_date <= today, unless an exit is already
          working; a fresh quote; the whole position
  buys    budget = 30% x equity - booked notional (qty x fill) - working-entry notional (qty x ref), once per
          pass; per name = budget / len(target or buys); qty = max(1, floor(per_name / (mid x (1 + cost))));
          a buy is skipped and STAYS pending when the budget is 0, the name is already held or working, 10
          positions are held + working, or there is no fresh quote (entries: quoted 10:00-16:00 ET and at
          most 15 minutes old; exits: at most 15 minutes old)
  due     pos_exit_date(today, pending, sym): the rank's per-symbol override, else fill + 91 days"""
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from ...venues.sim import iex_near

ET = ZoneInfo("America/New_York")
MAX_POSITIONS = 10
SLEEVE_CAP = 0.30
QUOTE_MAX_AGE_S = 15 * 60


def merge_pending_buys(old_buys, new_buys, n_book):
    """verbatim (Row 43 F1): union surviving pending buys with a fresh rank selection, old first, truncated to
    the room the book leaves."""
    try:
        room = max(0, MAX_POSITIONS - int(n_book or 0))
    except (TypeError, ValueError):
        room = 0
    merged = []
    for s in list(old_buys or []) + list(new_buys or []):
        if s not in merged:
            merged.append(s)
    return merged[:room]


def pos_exit_date(today, pending, sym):
    """verbatim: the exit due date of a new position — the rank's per-symbol override (a tagged
    {"anchor": "fill+91"} re-anchors on the fill; an untagged ~85-95-day override is a stale +91 backstop and
    re-anchors too), else fill + 91 days."""
    over = (pending.get("exit_dates") or {}).get(sym)
    if over:
        if isinstance(over, dict):
            if over.get("anchor") == "fill+91":
                return (date.fromisoformat(today) + timedelta(days=91)).isoformat()
            return over.get("date")
        try:
            _over_d = date.fromisoformat(over)
            _today_d = date.fromisoformat(today)
            if 85 <= (_over_d - _today_d).days <= 95:
                return (_today_d + timedelta(days=91)).isoformat()
        except (ValueError, TypeError):
            pass
        return over
    return (date.fromisoformat(today) + timedelta(days=91)).isoformat()


def _in_entry_window(t):
    qt = datetime.fromtimestamp(t, tz=ET)
    return (10, 0) <= (qt.hour, qt.minute) and (qt.hour, qt.minute, qt.second) <= (16, 0, 0)


def fresh_mid(q, now, for_exit=False):
    """old fresh_quote_ok: (bid + ask) / 2 of a quote at most 15 minutes old; an ENTRY also needs the quote
    stamped 10:00-16:00 ET (never priced off pre/post-market quotes). None when not fresh.

    Named divergence (F5, the owner's call 3, measured 2026-10-19): an ENTRY prices on the reference the sim fills
    on. When IEX's book is not near the NBBO (desk.venues.sim.iex_near) its mid is not the market: the last print,
    under the same age and window rules; without one, None (the buy waits, as the sim would not fill it). The source
    sized on its quote's mid; on the desk's free IEX book femto_leader_sc sized PAHC on 36.40 (bid 33.38, a stale
    quote) and filled at 39.35, 8.1% over its slot."""
    if not q:
        return None
    try:
        bid, ask = float(q.get("bid") or q.get("bp") or 0), float(q.get("ask") or q.get("ap") or 0)
    except (TypeError, ValueError):
        return None
    t = q.get("t") if q.get("t") is not None else q.get("as_of")
    try:
        t = float(t)
    except (TypeError, ValueError):
        return None
    if not for_exit and not _in_entry_window(t):
        return None
    if float(now) - t > QUOTE_MAX_AGE_S:
        return None
    if bid <= 0 or ask <= 0:
        return None
    if for_exit or iex_near(bid, ask):
        return (bid + ask) / 2
    try:                                         # a quote with no print time of its own (Yahoo's): its stamp
        last, lt = float(q.get("last")), float(q.get("last_t") if q.get("last_t") is not None else t)
    except (TypeError, ValueError):
        return None
    if last <= 0 or not _in_entry_window(lt) or float(now) - lt > QUOTE_MAX_AGE_S:
        return None
    return last


def book_of(state):
    return {s: st["position"] for s, st in (state or {}).items() if isinstance(st, dict) and st.get("position")}


def working_of(state):
    return {s: st["pending_entry"] for s, st in (state or {}).items()
            if isinstance(st, dict) and st.get("pending_entry") and not st.get("position")}


def fill(state, pending, equity, quotes, cost_bps_side, today, now, name="core"):
    """one old run_fill pass. state: the adapter's sleeve_state; pending: {"buys", "sells", "exit_dates",
    "target"}; quotes: {SYM: quote row}. Returns (sells, buys, leftover) with
    sells = [(sym, qty, mid, why)], buys = [(sym, qty, mid, exit_due_date)], leftover = the pending dict after
    the pass (buys/sells not done stay)."""
    pending = dict(pending or {})
    book = book_of(state)
    working = working_of(state)
    buys = list(pending.get("buys") or [])
    sells = list(pending.get("sells") or [])
    for s, p in book.items():
        due = p.get("exit_due_date")
        if due and str(due) <= today and s not in sells and not p.get("exit_submitted"):
            sells.append(s)
    out_sells, done_sells = [], []
    for sym in sells:
        p = book.get(sym)
        if p and p.get("exit_submitted"):
            done_sells.append(sym)                       # a sell is already working (adopted)
            continue
        mid = fresh_mid((quotes or {}).get(sym), now, for_exit=True)
        if mid is None:
            continue                                     # stale quote: the sell waits
        qty = abs(float((p or {}).get("qty") or 0))
        if qty <= 0:
            done_sells.append(sym)                       # nothing held: dropped from pending
            continue
        out_sells.append((sym, qty, mid, (p or {}).get("exit_reason") or "time_exit"))
        done_sells.append(sym)
    out_buys, done_buys = [], []
    if buys and equity > 0:
        book_not = sum(abs(float(p.get("qty") or 0)) * float(p.get("entry_px") or 0) for p in book.values())
        pend_not = sum(float(w.get("qty") or 0) * float(w.get("ref_px") or 0) for w in working.values())
        budget = max(0.0, SLEEVE_CAP * equity - book_not - pend_not)
        tgt = pending.get("target") or buys
        n_target = max(1, len(tgt) if isinstance(tgt, (list, tuple, dict, set)) else len(buys))
        held = set(book) | set(working)
        for sym in buys:
            if budget == 0:
                continue
            if sym in held:
                continue                                 # duplicate: stays pending (old behaviour)
            if len(held) >= MAX_POSITIONS:
                continue
            mid = fresh_mid((quotes or {}).get(sym), now)
            if mid is None:
                continue
            per_name = budget / n_target
            all_in = mid * (1.0 + (cost_bps_side or 0.0))
            qty = max(1, math.floor(per_name / all_in)) if all_in > 0 else 1
            out_buys.append((sym, qty, mid, pos_exit_date(today, pending, sym)))
            done_buys.append(sym)
            held.add(sym)
    leftover = dict(pending, buys=[s for s in buys if s not in done_buys],
                    sells=[s for s in sells if s not in done_sells])
    return out_sells, out_buys, leftover


def fill_intents(Intent, state, pending, equity, quotes, cost_bps_side, today, now, name="core", close_ts=None,
                 extra_meta=None, disaster_stop=None):
    """fill() as femto intents (market orders, the day's session); returns (intents, leftover). disaster_stop:
    the old Sleeve.disaster_stop_pct (a GTC stop at fill x (1 - pct)); the reference stop travels on the
    intent and the spec's stop_pct re-measures it from the actual fill."""
    sells, buys, leftover = fill(state, pending, equity, quotes, cost_bps_side, today, now, name)
    out = []
    for sym, qty, mid, why in sells:
        out.append(Intent("exit", sym, qty=qty, price_hint=round(mid, 4), signal_key="%s:%s:core_sell" % (sym, today),
                          reason="%s %s" % (name, why)))
    for sym, qty, mid, due in buys:
        pm = {"exit_due_date": due}
        pm.update((extra_meta or {}).get(sym) or {})
        out.append(Intent("enter", sym, qty_hint=int(qty), price_hint=round(mid, 4),
                          stop=round(mid * (1 - disaster_stop), 4) if disaster_stop else None,
                          order={"not_after": close_ts} if close_ts else None,
                          signal_key="%s:%s:core_buy" % (sym, today), position_meta=pm,
                          reason="%s buy (exit due %s)" % (name, due)))
    return out, leftover
