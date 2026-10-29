"""master-desk: the beatendown / confluence weekly runtime — the old twins' mode_rank + mode_fill minus the desk
gates (risk_gate desk halt, Decision #75 chart gate, context gate, drawdown brake, 150% cap: the cutover
doctrine). Each twin keeps its own selection, clocks and the rules its own fill carried.

Rank (Friday after the close, once the weekly M2 job has written this Friday's qualifier file): every
qualifier scored on the frozen HOLD9 confluences (count desc, symbol asc), the twin's selection; positions
due for their 13-week exit staged to sell; buys = the first selected names not held / not working, into
10 - (book - sells) - working entries free slots; target = every selected name (the budget divisor).

Fill (Monday, one pass at the twin's clock): sells — the staged ones plus any due position — at a fresh
quote (regular-hours stamp 10:00-16:00 ET, <= 15 min old), market, day; buys only when the twin's buy gates
are clear (last 5 December weekdays, FOMC blackout = session before + both days, VIX unknown or > 4 days
stale) — budget = 30% of equity - book notional at entry - working-entry notional, per name =
budget / len(target), qty = max(1, floor(per_name / (mid x 1.00255))); a 10-position cap over book +
working entries + this pass's buys (confluence also frees the slots it sells this pass); beatendown defers
every buy while the desk fear composite is below FEAR (User's fear gate, 2026-10-10). Exit due = the fill
date + 91 days."""
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MAX_POSITIONS = 10
HOLD_DAYS = 91
SLEEVE_CAP = 0.30
COST_BPS_SIDE = 0.00255          # 51bp round-trip, split per side (study §5)
FOMC = [("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"),
        ("2026-04-28", "2026-04-29"), ("2026-06-16", "2026-06-17"),
        ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"),
        ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09"),
        # SPEC §7 ("2027 FOMC dates must be added in January 2027") — the Fed's 2027 schedule
        ("2027-01-26", "2027-01-27"), ("2027-03-16", "2027-03-17"),
        ("2027-04-27", "2027-04-28"), ("2027-06-15", "2027-06-16"),
        ("2027-07-27", "2027-07-28"), ("2027-09-21", "2027-09-22"),
        ("2027-11-02", "2027-11-03"), ("2027-12-14", "2027-12-15")]


def now_et(context):
    return datetime.fromtimestamp(float(context.now), tz=ET)


def phase(context, rank_hm, fill_hm):
    t = now_et(context)
    hm = (t.hour, t.minute)
    if t.weekday() == 4 and hm >= rank_hm:
        return "rank"
    if t.weekday() == 0 and fill_hm <= hm < (16, 0):
        return "fill"
    return None


def book_of(state):
    return {s: v["position"] for s, v in (state or {}).items() if isinstance(v, dict) and v.get("position")}


def working_of(state):
    return {s: v["pending_entry"] for s, v in (state or {}).items()
            if isinstance(v, dict) and v.get("pending_entry") and not v.get("position")}


def valid(q):
    return isinstance(q, dict) and q.get("symbol") and isinstance(q.get("bar"), dict) and q.get("friday") \
        and "m2" in q


def rank(context, qfile, row_fn, exit_due):
    """old mode_rank on the weekly qualifier file. row_fn(q) -> {"count", "rules", "selected", ...}.
    None when the file is missing or failed closed (the rank waits)."""
    if not qfile or qfile.get("wait") or not isinstance(qfile.get("qualifiers"), list):
        return None
    today = context.session
    state = (context.extra or {}).get("sleeve_state") or {}
    table = []
    for q in qfile["qualifiers"]:
        if valid(q):
            table.append(dict(row_fn(q), symbol=q["symbol"], m2=q["m2"]))
    table.sort(key=lambda r: (-r["count"], r["symbol"]))
    selected = [r for r in table if r["selected"]]
    book = book_of(state)
    working = working_of(state)
    sells = [s for s, p in book.items() if exit_due(p, today)]
    free = MAX_POSITIONS - (len(book) - len(sells)) - len(working)
    buys, skipped = [], []
    for r in selected:
        if r["symbol"] in book or r["symbol"] in working:
            continue
        if len(buys) < max(0, free):
            buys.append(r["symbol"])
        else:
            skipped.append(r["symbol"])
    return {"buys": buys, "sells": sells, "asof": today, "monday": qfile.get("asof_monday"),
            "target": [r["symbol"] for r in selected], "selected_detail": selected, "skipped_capacity": skipped}


def fresh_quote_ok(q, now):
    """old fresh_quote_ok: (ok, mid) — a regular-hours quote (stamped 10:00-16:00 ET), <= 15 min old."""
    q = q or {}
    try:
        bid, ask, qt = float(q.get("bid") or 0), float(q.get("ask") or 0), q.get("t")
    except (TypeError, ValueError):
        return False, None
    if qt is None:
        return False, None
    t = datetime.fromtimestamp(float(qt), tz=ET)
    if not ((10, 0, 0) <= (t.hour, t.minute, t.second) and (t.hour, t.minute, t.second, t.microsecond) <= (16, 0, 0, 0)):
        return False, None
    if now - float(qt) > 15 * 60:
        return False, None
    if bid <= 0 or ask <= 0:
        return False, None
    return True, (bid + ask) / 2


def fill(context, meta, exit_due, buy_gates, fear_gate=False, free_sold_slots=False):
    """old mode_fill -> (sell_orders [(sym, qty, mid)], buy_orders [(sym, qty, mid)], done_sells, done_buys)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    quotes = extra.get("quotes") or {}
    today = context.session
    now = float(context.now)
    pend = meta.get("pending") or {}
    book = book_of(state)
    working = working_of(state)
    sells = list(pend.get("sells") or [])
    for s, p in book.items():                                       # the safety net: any position past due
        if exit_due(p, today) and s not in sells and not p.get("exit_submitted"):
            sells.append(s)
    sell_orders, done_sells = [], []
    for sym in sells:
        pos = book.get(sym)
        if pos is not None and pos.get("exit_submitted"):
            done_sells.append(sym)                                  # already working: never a duplicate sell
            continue
        ok, mid = fresh_quote_ok(quotes.get(sym), now)
        if not ok:
            continue
        qty = float((pos or {}).get("qty") or 0)
        if qty <= 0:
            done_sells.append(sym)
            continue
        sell_orders.append((sym, qty, mid))
        done_sells.append(sym)
    buys = list(pend.get("buys") or [])
    buy_orders, done_buys = [], []
    blocks = buy_gates(today, extra.get("vix"), FOMC)
    if buys and not blocks and now_et(context).weekday() == 0:
        equity = float(context.equity or 0.0)
        book_not = sum(float(p.get("qty") or 0) * float(p.get("entry_px") or p.get("ref_px") or 0)
                       for p in book.values())
        pend_not = sum(float(w.get("qty") or 0) * float(w.get("ref_px") or 0) for w in working.values())
        budget = max(0.0, SLEEVE_CAP * equity - book_not - pend_not)
        n_target = max(1, len(pend.get("target") or buys))
        fear_ok = extra.get("fear_ok", True) if fear_gate else True
        for sym in buys:
            n_held = len(book) + len(working) + len(done_buys) - (len(done_sells) if free_sold_slots else 0)
            if n_held >= MAX_POSITIONS:
                continue
            if sym in book or sym in working:
                continue
            ok, mid = fresh_quote_ok(quotes.get(sym), now)
            if not ok:
                continue
            per_name = budget / n_target
            all_in = mid * (1.0 + COST_BPS_SIDE)
            qty = max(1, math.floor(per_name / all_in)) if all_in > 0 else 1
            if fear_ok is False:
                continue                                            # deferred: the market is not scared
            buy_orders.append((sym, qty, mid))
            done_buys.append(sym)
    return sell_orders, buy_orders, done_sells, done_buys


def intents(Intent, context, meta, exit_due, buy_gates, tag, fear_gate=False, free_sold_slots=False):
    sell_orders, buy_orders, _ds, _db = fill(context, meta, exit_due, buy_gates, fear_gate, free_sold_slots)
    close_ts = now_et(context).replace(hour=16, minute=0, second=0, microsecond=0).timestamp()
    order = {"type": "market", "tif": "day", "not_after": close_ts}
    detail = {r["symbol"]: r for r in ((meta.get("pending") or {}).get("selected_detail") or [])}
    due = (date.fromisoformat(context.session) + timedelta(days=HOLD_DAYS)).isoformat()
    out = []
    for sym, qty, mid in sell_orders:
        out.append(Intent("exit", sym, qty=qty, price_hint=round(mid, 2), order=dict(order),
                          signal_key="%s:%s:%s_sell" % (sym, context.session, tag),
                          reason="%s 13-week time exit" % tag))
    for sym, qty, mid in buy_orders:
        r = detail.get(sym) or {}
        out.append(Intent("enter", sym, qty=float(qty), price_hint=round(mid, 2), order=dict(order),
                          position_meta={"exit_due_date": due, "rule_count": r.get("count"),
                                         "rules_fired": r.get("rules")},
                          signal_key="%s:%s:%s_buy" % (sym, context.session, tag),
                          reason="%s: rules=%s count=%s" % (tag, ",".join(r.get("rules") or []) or "-",
                                                            r.get("count"))))
    return out


def next_meta(context, meta, rank_hm, fill_hm, row_fn, exit_due, buy_gates, fear_gate=False,
              free_sold_slots=False):
    extra = context.extra or {}
    meta = dict(meta or {})
    ph = phase(context, rank_hm, fill_hm)
    today = context.session
    if ph == "rank" and meta.get("last_rank_date") != today:
        p = rank(context, extra.get("m2"), row_fn, exit_due)
        if p is not None:
            meta.update(pending=p, last_rank_date=today)
    elif ph == "fill" and meta.get("last_fill_date") != today:
        _so, _bo, done_sells, done_buys = fill(context, meta, exit_due, buy_gates, fear_gate, free_sold_slots)
        pend = dict(meta.get("pending") or {})
        pend["buys"] = [s for s in pend.get("buys") or [] if s not in done_buys]
        pend["sells"] = [s for s in pend.get("sells") or [] if s not in done_sells]
        meta.update(pending=pend, last_fill_date=today,
                    last_fill={"date": today, "buys": done_buys, "sells": done_sells})
    return meta
