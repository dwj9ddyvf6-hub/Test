"""Earnings Buyback — call debit spreads on large buybacks before earnings, held through the event — lean-desk port
(Wave B).

master-desk: the old desk's earnings_buyback_sleeve.py restored on the engine (Quantpedia #0271, Amini & Singal). A
company whose 8-K announces a buyback of >= 5% of its shares 15-30 days before its earnings is bought 8-15 days
before the report as a defined-risk call debit spread (a long call when no spread qualifies) expiring after it,
HELD THROUGH the event (Decision #100: max loss = the debit, so the desk's no-holding-through-earnings rule does not
bind this sleeve), and sold 15 trading days after it unless its +50% target, -50% stop or 5-DTE floor comes first.

  signal ... the newest EDGAR buyback scan (feed buyback_scan: desk/feedlib/edgar_buyback.py, the old
             edgar_buyback_scraper.py) unless more than 8 days old by its scan_date (its file's mtime when undated):
             its results in order — buyback_pct >= 5, the filing 15-30 calendar days before the name's calendar
             earnings date (an unparseable filing date or an unknown earnings date: skipped).
  entry .... while fewer than 4 positions are held, closing or in flight, each signal not held or in flight: at most
             2 held (a working close aside) or in flight in its sector (the old desk/risk.py SECTORS map; an unknown
             sector never blocks); a calendar refreshed within 8 days that carries the name, its earnings 8-15 days
             out; that earnings event never traded before (SYM|date); the spot >= $10. Calls 30-45 DTE, the nearest
             expiry: long = the highest strike <= spot (the lowest when none is), short = the first strike >= 1.10 x
             the long; both legs quoted, long ask > 0, its (ask - bid) / mid <= 10% when bid, debit = long ask -
             short bid > 0 and debit / width in [0.30, 0.45]; expiring after the earnings date; floor(0.5% of equity
             / (debit x 100)) spreads (0: no trade, no fallback). No spread: the long call — the first strike >=
             1.02 x spot on that expiry, quoted, ask > 0, (ask - bid) / mid <= 15% when bid, expiring after
             earnings, floor(0.5% of equity / (ask x 100)) calls. The spread as one package at its natural debit
             (long ask - short bid), the call at its ask.
  exits .... (never gated, every pass; the earnings date first re-anchored to the calendar's when that is earlier,
             and kept) in the old order: 15 weekdays after the earnings date (T+15; holidays not netted out, as the
             old); the value (long bid - short ask; the call's bid) >= 1.5 x the debit paid; <= 0.5 x it; <= 5 DTE.
             The spread closes at its natural (long at its bid, short at its ask), the call at its bid, never
             one-sided (the exit waits a pass). A closed position's earnings event is never traded again.

Gone under the cutover doctrine: the risk gate (kill switch, fail closed when unavailable), the Decision #75 chart
gate (pre_buy staging, the staged-intent release replay with its kill-switch / earnings-window / red-day re-checks,
its re-quote and debit-band re-verification, the 24h pending TTL), the 150% desk gross-exposure cap (its intra-pass
accumulator and the desk exposure ledger it fed), the cross-sleeve overlap check (a log line; fail closed on an
unreadable exposure ledger), the desk earnings blackout (desk/earnings.is_blackout, Decision #8: earnings today or
within 3 days — inside this sleeve's own 8-15 day window it can never bind, so its removal changes no decision).

Named divergences: one atomic two-leg package at the natural debit to open (the old sent two single-leg day limits,
long first, at the long ask and the short bid — the same prices — with naked-leg fail-safes and partial-fill
adoption) and one at the natural to close (the old: two single-leg limits, long at its bid, short at its ask);
hourly passes at :25 in the session (the old cron ran hourly at :25 around the clock); the legs' quotes come from
the chain snapshot (the old made a latest-quote call per leg, and re-fetched chain and quote for the long call);
the spot is the live quote — its mid when two-sided, else its last, else the last daily close (the old read the
newest SIP 1-hour bar's close); sized on the sleeve's own book equity (the old read the account's); an unfilled
order lapses after 55 minutes and the next pass decides again (the old's day orders rested until filled or the
session ended, and a dead close was re-fired from its closing book); the scan arrives as feed:buyback_scan (the
newest file with its mtime; the old globbed desk/hidden_state itself); fills, partial fills, dead orders, ghost
legs and assignment are the engine's (the old's promote_fills / reconcile_pass), so an event is marked traded when
the book is flat (the old: at the reconcile that saw the broker flat on every leg); the calendar's freshness is the
desk's earnings_fresh (the sleeve's names refreshed within 8 days; the old read earnings.json's updated_ts); a
single-leg limit lands on the OMS's option tick grid toward marketability.

Inputs via context.extra:
  "scan"           {"file", "mtime", "scan": the scan document {"scan_date", "results": [...], ...}} | None
  "earnings"       {SYM: "YYYY-MM-DD" | None}; "earnings_fresh": bool
  "chains"         {SYM: call rows 30-45 DTE {"symbol","strike","expiration","type","bid","ask"}} (fetched on demand)
  "option_quotes"  {OCC: {"bid","ask"}} — the held legs
  "quotes"         {SYM: {"bid","ask","last"}} — spots
  "sectors"        {SYM: sector} — the old desk/risk.py SECTORS
  "meta"           {"completed": ["SYM|YYYY-MM-DD", ...]} — earnings events traded
  "closed_trades"  the sleeve's closed trades (one order key per round trip)
  "sleeve_state"   {SYM: {"position": spread group {qty, net_entry, legs, ...} | long call {qty, entry_px, occ, ...}
                   (+ its position_meta: kind, earnings_date, expiry, ...) | None, "pending_entry": ...,
                   "ebb_event": the held event's earnings date}}
Bars (arg): daily bars (the spot when no quote)."""
from datetime import date, datetime, timedelta, timezone

from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig

_ET = ZoneInfo("America/New_York")

BUYBACK_MIN_PCT = 5.0
EARN_DAYS_MIN, EARN_DAYS_MAX = 8, 15          # entry window: T-15..T-8
ANNOUNCE_DAYS_MIN, ANNOUNCE_DAYS_MAX = 15, 30  # SPEC Step 1: announced 30-15 days before earnings
DTE_MIN, DTE_MAX = 30, 45                      # spread / call DTE window (SPEC), expiring after earnings
DTE_FLOOR = 5                                  # never hold below 5 DTE
MIN_STOCK_PRICE = 10.0                         # SPEC universe filter: price >= $10
EXIT_TRADING_DAYS_AFTER_EARNINGS = 15          # SPEC time stop: T+15 trading days
SPREAD_WIDTH_PCT = 0.10
DEBIT_RANGE = (0.30, 0.45)                     # this sleeve's SPEC'd debit / width band (fragment 098)
LIQ_GATE_FRAC = 0.10                           # select_debit_spread's long-leg quote gate
CALL_GATE_FRAC = 0.15                          # select_long_call's quote gate
LONG_CALL_OTM_PCT = 0.02
RISK_FRACTION = 0.005                          # 0.5% risk per trade
MAX_POSITIONS = 4
MAX_SAME_SECTOR = 2                            # SPEC: max 2 positions in one sector
PROFIT_TARGET_FRAC = 0.50
STOP_FRAC = 0.50
SCAN_MAX_AGE_DAYS = 8                          # a scan older than 8 days is not traded
COMPLETED_KEEP_DAYS = 120                      # the old pruned traded-event keys older than this
WINDOW_S = 3300                                # an unfilled order lapses before the next hourly pass

CONFIG = SleeveConfig(
    sleeve_id="earnings_buyback", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


# --------------------------------------------------------------------- dates
def _parse_date(date_str):
    """the old _parse_date: a "YYYY-MM-DD" string (stripped) -> date, else None."""
    if not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def expiry_after_earnings(expiry_str, earnings_date_str):
    """Decision #100: the structure must expire strictly AFTER the earnings date (held through the event). Verbatim."""
    try:
        exp_d = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        earn_d = datetime.strptime(earnings_date_str, "%Y-%m-%d").date()
        return exp_d > earn_d
    except (ValueError, TypeError):
        return False


def trading_days_since_earnings(earnings_date_str, today_iso):
    """the old _trading_days_since_earnings: weekdays (Mon-Fri) in (earnings date, today]; market holidays are not
    netted out (the old had no holiday calendar: the T+15 stop fires marginally early around a holiday). 0 on or
    before the earnings date; None on an unparseable date."""
    earn_d = _parse_date(earnings_date_str)
    if earn_d is None:
        return None
    today = date.fromisoformat(today_iso)
    if today <= earn_d:
        return 0
    n = 0
    d = earn_d
    while d < today:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def dte(expiry_str, today_iso):
    """the old _dte: days from today (ET) to the expiry; None on a bad expiry."""
    try:
        return (datetime.strptime(expiry_str, "%Y-%m-%d").date() - date.fromisoformat(today_iso)).days
    except (ValueError, TypeError):
        return None


def sync_earnings_date(current, calendar_date):
    """the old _sync_earnings_date: the calendar's date replaces the position's when it is earlier (or the position
    has none); a later or unknown calendar date changes nothing."""
    d = _parse_date(calendar_date)
    if d is None:
        return current
    cur = _parse_date(current)
    if cur is None or d < cur:
        return d.isoformat()
    return current


# ---------------------------------------------------------------------- scan
def scan_age_days(feed, now):
    """the old _scan_age_days: days since the scan's scan_date (naive = UTC), else since its file's mtime; None when
    neither is readable."""
    now_dt = datetime.fromtimestamp(float(now), tz=timezone.utc)
    try:
        sd = str((feed or {}).get("scan").get("scan_date") or "")
        dt = datetime.fromisoformat(sd.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now_dt - dt).total_seconds() / 86400.0
    except (ValueError, TypeError, AttributeError):
        pass
    try:
        return (now_dt.timestamp() - float(feed["mtime"])) / 86400.0
    except (KeyError, TypeError, ValueError):
        return None


def latest_scan(feed, now):
    """the old latest_scan: the newest scan, or None when there is none or it is older than SCAN_MAX_AGE_DAYS (or
    undated) — stale signals are not traded."""
    if not feed:
        return None
    age = scan_age_days(feed, now)
    if age is None or age > SCAN_MAX_AGE_DAYS:
        return None
    return feed.get("scan")


def scan_signals(scan, calendar):
    """the old scan_signals filter, in the scan's order: buyback_pct >= 5 and the filing 15-30 calendar days before
    the calendar's earnings date (SPEC Step 1); an unparseable filing date or an unknown earnings date fails
    closed."""
    out = []
    if not scan:
        return out
    for r in scan.get("results") or []:
        try:
            sym = str(r.get("ticker") or "").upper()
            pct = float(r.get("buyback_pct") or 0)
        except (TypeError, ValueError):
            continue
        if not sym or pct < BUYBACK_MIN_PCT:
            continue
        filing_d = _parse_date(r.get("filing_date"))
        earn_d = _parse_date((calendar or {}).get(sym)) if calendar is not None else None
        if filing_d is None or earn_d is None:
            continue
        dd = (earn_d - filing_d).days
        if not (ANNOUNCE_DAYS_MIN <= dd <= ANNOUNCE_DAYS_MAX):
            continue
        out.append({"symbol": sym, "buyback_pct": pct, "filing_date": r.get("filing_date"),
                    "dollar": r.get("dollar_formatted")})
    return out


def earnings_window(sym, calendar, fresh, today_iso):
    """the old earnings_window_ok (its desk-blackout step gone): (ok, earnings date) — a calendar refreshed within 8
    days that carries the name with a date 8-15 days out. Fail closed."""
    if not fresh:
        return False, None
    cal = calendar or {}
    if (sym or "").upper() not in cal:
        return False, None
    earn_d = _parse_date(cal.get(sym.upper()))
    if earn_d is None:
        return False, None
    delta = (earn_d - date.fromisoformat(today_iso)).days
    if not (EARN_DAYS_MIN <= delta <= EARN_DAYS_MAX):
        return False, None
    return True, earn_d.isoformat()


def sector_blocked(sym, sectors, counted):
    """the old _sector_blocked: MAX_SAME_SECTOR names of the sector already among `counted` (the positions held
    without a working close, and the entries in flight); an unknown sector never blocks."""
    sec = (sectors or {}).get((sym or "").upper())
    if not sec:
        return False
    return sum(1 for s in counted if (sectors or {}).get((s or "").upper()) == sec) >= MAX_SAME_SECTOR


# ---------------------------------------------------------------- structures
def _strike(c):
    return float(c.get("strike", 0))


def _quote(q):
    """an option quote as the old quote CLI served it, or None when the contract has none at all (a chain row
    whose bid and ask are both absent)."""
    if not q or (q.get("bid") is None and q.get("ask") is None):
        return None
    return q


def _calls_by_expiry(chain, session_iso, dte_min, dte_max):
    """the old get_option_chain(expiry today+dte_min .. today+dte_max, calls) grouped by expiration."""
    ref = date.fromisoformat(session_iso)
    by_exp = {}
    for c in chain or []:
        if c.get("type") not in (None, "call"):
            continue
        exp = c.get("expiration") or ""
        if not exp:
            continue
        try:
            d = (date.fromisoformat(str(exp)[:10]) - ref).days
        except ValueError:
            continue
        if dte_min <= d <= dte_max:
            by_exp.setdefault(exp, []).append(c)
    return by_exp


def select_debit_spread(chain, quotes, stock_price, session_iso, dte_min=DTE_MIN, dte_max=DTE_MAX,
                        width_pct=SPREAD_WIDTH_PCT, debit_range=DEBIT_RANGE):
    """Pure form of desk/options_exec.select_debit_spread with this sleeve's SPEC'd DEBIT_RANGE: the nearest
    expiry; long = the highest strike <= stock price (the lowest when none is); short = the first strike >= long x
    (1 + width_pct); both legs quoted; long ask > 0; (ask - bid) / mid <= 10% when the long has a bid; debit = long
    ask - short bid > 0; debit / width inside the band."""
    by_expiry = _calls_by_expiry(chain, session_iso, dte_min, dte_max)
    if not by_expiry:
        return None
    expiry = sorted(by_expiry.keys())[0]
    legs = sorted(by_expiry[expiry], key=_strike)
    long_leg = None
    for c in legs:
        if _strike(c) <= stock_price:
            long_leg = c
    if not long_leg:
        long_leg = legs[0]
    long_strike = _strike(long_leg)
    target_short = long_strike * (1 + width_pct)
    short_leg = None
    for c in legs:
        if _strike(c) >= target_short:
            short_leg = c
            break
    if not short_leg:
        return None
    short_strike = _strike(short_leg)
    width = short_strike - long_strike
    long_q = _quote((quotes or {}).get(long_leg["symbol"]))
    short_q = _quote((quotes or {}).get(short_leg["symbol"]))
    if not long_q or not short_q:
        return None
    long_ask = float(long_q.get("ask") or 0)
    long_bid = float(long_q.get("bid") or 0)
    short_bid = float(short_q.get("bid") or 0)
    if long_ask <= 0:
        return None
    mid = (long_ask + long_bid) / 2 if long_bid > 0 else long_ask
    if long_bid > 0 and (long_ask - long_bid) / mid > LIQ_GATE_FRAC:
        return None
    debit = long_ask - short_bid
    if debit <= 0:
        return None
    ratio = debit / width if width > 0 else 1
    if debit_range is not None and not (debit_range[0] <= ratio <= debit_range[1]):
        return None
    return {"expiry": expiry,
            "long_leg": {"occ": long_leg["symbol"], "strike": long_strike, "ask": long_ask, "bid": long_bid},
            "short_leg": {"occ": short_leg["symbol"], "strike": short_strike, "bid": short_bid},
            "width": round(width, 2), "debit": round(debit, 2), "max_profit": round(width - debit, 2),
            "max_return_pct": round((width - debit) / debit * 100, 1), "breakeven": round(long_strike + debit, 2)}


def select_long_call(chain, quotes, stock_price, session_iso, dte_min=DTE_MIN, dte_max=DTE_MAX,
                     otm_pct=LONG_CALL_OTM_PCT):
    """Pure form of desk/options_exec.select_long_call: the nearest expiry; the first strike >= stock price x
    (1 + otm_pct); quoted, ask > 0, (ask - bid) / mid <= 15% when bid."""
    by_expiry = _calls_by_expiry(chain, session_iso, dte_min, dte_max)
    if not by_expiry:
        return None
    expiry = sorted(by_expiry.keys())[0]
    legs = sorted(by_expiry[expiry], key=_strike)
    target = stock_price * (1 + otm_pct)
    selected = None
    for c in legs:
        if _strike(c) >= target:
            selected = c
            break
    if not selected:
        return None
    q = _quote((quotes or {}).get(selected["symbol"]))
    if not q:
        return None
    ask = float(q.get("ask") or 0)
    bid = float(q.get("bid") or 0)
    if ask <= 0:
        return None
    if bid > 0 and (ask - bid) / ((ask + bid) / 2) > CALL_GATE_FRAC:
        return None
    return {"expiry": expiry, "occ": selected["symbol"], "strike": _strike(selected), "ask": ask, "bid": bid,
            "mid": round((ask + bid) / 2, 2) if bid > 0 else ask}


def spread_qty_for_risk(debit, equity, risk_fraction=RISK_FRACTION):
    """desk/options_exec.spread_qty_for_risk, verbatim."""
    if not equity or equity <= 0 or debit <= 0:
        return 0
    budget = equity * risk_fraction
    return max(0, int(budget / (debit * 100)))


def build_trade(chain, quotes, stock_px, earnings_date, equity, session_iso):
    """the old build_trade, in its order: the $10 floor; the debit spread (expiring after earnings; zero contracts
    ends the attempt, no fallback); else the long call (expiring after earnings, 0.5% of equity at the ask)."""
    if not stock_px:
        return None
    if stock_px < MIN_STOCK_PRICE:
        return None
    sp = select_debit_spread(chain, quotes, stock_px, session_iso)
    if sp and expiry_after_earnings(sp["expiry"], earnings_date):
        n = spread_qty_for_risk(sp["debit"], equity, RISK_FRACTION)
        if n > 0:
            return {"kind": "debit_spread", "spread": sp, "contracts": n, "stock_px": stock_px}
        return None
    call = select_long_call(chain, quotes, stock_px, session_iso)
    if call and expiry_after_earnings(call["expiry"], earnings_date):
        n = max(0, int((equity * RISK_FRACTION) / (call["ask"] * 100))) if call["ask"] > 0 else 0
        if n > 0:
            return {"kind": "long_call", "call": call, "contracts": n, "stock_px": stock_px}
    return None


# --------------------------------------------------------------------- exits
def exit_due(kind, earnings_date, debit, expiry, today_iso, close_cost=None, call_bid=0.0):
    """the old exit_due, in its order: T+15 (15 trading days after earnings; Decision #100: no pre-earnings exit),
    the +50% target, the -50% stop on the debit paid, the 5-DTE floor. A spread's live value is -close_cost (the
    2026-10-11 fix: never the cost itself); a long call's is its bid."""
    t_since = trading_days_since_earnings(earnings_date, today_iso)
    if t_since is not None and t_since >= EXIT_TRADING_DAYS_AFTER_EARNINGS:
        return "time_stop_t_plus_15"
    debit = debit or 0
    if kind == "debit_spread":
        if close_cost is not None and debit > 0:
            value = -close_cost
            if value >= debit * (1 + PROFIT_TARGET_FRAC):
                return "profit_target_50pct"
            if value <= debit * (1 - STOP_FRAC):
                return "stop_minus50pct"
    else:
        bid = call_bid
        if bid > 0 and debit > 0:
            if bid >= debit * (1 + PROFIT_TARGET_FRAC):
                return "profit_target_50pct"
            if bid <= debit * (1 - STOP_FRAC):
                return "stop_minus50pct"
    d = dte(expiry, today_iso)
    if d is not None and d <= DTE_FLOOR:
        return "dte_floor_5"
    return None


def _side_px(oq, occ, side):
    """the old quote read: float(quote[side] or 0), 0 when unquoted."""
    q = (oq or {}).get(occ) if occ else None
    try:
        return float(q.get(side) or 0) if q else 0.0
    except (TypeError, ValueError):
        return 0.0


def held(pos):
    """the held structure: its kind, contracts, debit paid (the fill, to the cent as the old read its fills), and its
    live legs {"long": OCC | None, "short": OCC | None} (a spread) / {"call": OCC} (a long call)."""
    legs = pos.get("legs") or ({pos["occ"]: pos.get("qty")} if pos.get("occ") else {})
    longs = [o for o, q in legs.items() if float(q or 0) > 0]
    shorts = [o for o, q in legs.items() if float(q or 0) < 0]
    kind = pos.get("kind") or ("debit_spread" if shorts else "long_call")
    contracts = int(round(abs(float(pos.get("qty") or 0))))
    if kind == "debit_spread":
        net = pos.get("net_entry")
        debit = round(float(net), 2) if (net is not None and longs and shorts) else pos.get("debit")
        return {"kind": kind, "contracts": contracts, "debit": debit,
                "long": longs[0] if longs else None, "short": shorts[0] if shorts else None}
    px = pos.get("entry_px")
    return {"kind": kind, "contracts": contracts, "debit": round(float(px), 2) if px is not None else pos.get("debit"),
            "call": longs[0] if longs else pos.get("occ")}


def close_cost_of(h, oq):
    """the old spread_close_cost: short at its ask, long at its bid (sa - lb); None when either is not > 0 or a leg
    is gone."""
    if not h.get("long") or not h.get("short"):
        return None
    lb, sa = _side_px(oq, h["long"], "bid"), _side_px(oq, h["short"], "ask")
    if lb <= 0 or sa <= 0:
        return None
    return sa - lb


def close_order(h, oq):
    """the old close_trade's prices, all fetched before any leg goes out: (net or limit, detail) — the spread's
    natural net (short ask - long bid), a lone leg's own side, the call's bid; None when any leg is one-sided."""
    if h["kind"] == "debit_spread":
        lb = _side_px(oq, h["long"], "bid") if h.get("long") else None
        sa = _side_px(oq, h["short"], "ask") if h.get("short") else None
        if lb is None and sa is None:
            return None
        if (lb is not None and lb <= 0) or (sa is not None and sa <= 0):
            return None
        if lb is not None and sa is not None:
            return {"net": round(sa - lb, 2), "lb": lb, "sa": sa}
        return {"limit": lb if lb is not None else sa, "lb": lb, "sa": sa}
    bid = _side_px(oq, h.get("call"), "bid")
    if bid <= 0:
        return None
    return {"limit": bid, "bid": bid}


# ---------------------------------------------------------------------- spot
def spot_of(sym, quotes, bars):
    """the live price: the quote's mid when two-sided, else its last, else the last daily close."""
    q = (quotes or {}).get(sym) or {}
    try:
        bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
        if bid and ask and float(ask) >= float(bid) > 0:
            return (float(bid) + float(ask)) / 2
        if last and float(last) > 0:
            return float(last)
    except (TypeError, ValueError):
        pass
    bl = (bars or {}).get(sym) or []
    return float(bl[-1]["c"]) if bl else None


def _et_date(ts):
    return datetime.fromtimestamp(float(ts), tz=_ET).date().isoformat()


def entry_key(sym, session, closed=()):
    """one order key per round trip (the old minted a fresh client order id per submit): the session's closed
    round trips of the name number the key."""
    seen = set()
    for t in closed or ():
        try:
            if str(t.get("symbol") or "").upper() == sym and _et_date(t["closed_at"]) == session:
                seen.add(t.get("signal_key") or t["closed_at"])
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            continue
    return "%s:%s:earnings-buyback" % (sym, session) + (":%d" % len(seen) if seen else "")


# ---------------------------------------------------------------------- pass
def decide(bars, context):
    """one pass of the old scan_pass: the held positions' exits first (manage_positions), then the scan's signals in
    order while fewer than MAX_POSITIONS are held, closing or in flight (maybe_enter). Returns {"intents",
    "symbols": per-symbol state updates, "completed": the traded-event keys, "exits": every exit decision,
    "skips": why each signal did not enter}."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    oq = extra.get("option_quotes") or {}
    chains = extra.get("chains") or {}
    quotes = extra.get("quotes") or {}
    calendar = extra.get("earnings")
    fresh = extra.get("earnings_fresh")
    sectors = extra.get("sectors") or {}
    meta = extra.get("meta") or {}
    equity = float(context.equity or 0.0)
    now = float(context.now)
    today = context.session
    intents, updates, exits, skips = [], {}, {}, []

    # traded events: the kept keys, and the event of every position the book has since closed
    completed = list(meta.get("completed") or [])
    for sym, st in state.items():
        st = st or {}
        if st.get("ebb_event") and not st.get("position"):
            key = "%s|%s" % (sym, st["ebb_event"])
            if key not in completed:
                completed.append(key)
            updates[sym] = {"ebb_event": None, "pos": None}
    cut = (datetime.fromtimestamp(now, tz=timezone.utc) - timedelta(days=COMPLETED_KEEP_DAYS)).date().isoformat()
    completed = [k for k in completed if not isinstance(k, str) or k.rsplit("|", 1)[-1] >= cut]
    done = set(completed)

    held_syms = [s for s, st in state.items() if (st or {}).get("position")]
    in_flight = [s for s, st in state.items() if (st or {}).get("pending_entry") and not (st or {}).get("position")]
    closing = set()
    # manage_positions: exits first, never gated
    for sym in held_syms:
        pos = state[sym]["position"]
        if pos.get("exit_submitted"):
            closing.add(sym)                      # the old "closing" book: not re-managed until the close resolves
            updates[sym] = {"ebb_event": str(pos.get("earnings_date")),
                            "pos": {"earnings_date": pos.get("earnings_date")}}
            continue
        earn = sync_earnings_date(pos.get("earnings_date"), (calendar or {}).get(sym.upper()))
        updates[sym] = {"ebb_event": str(earn), "pos": {"earnings_date": earn}}
        h = held(pos)
        if h["contracts"] <= 0:
            continue
        cost = close_cost_of(h, oq) if h["kind"] == "debit_spread" else None
        bid = _side_px(oq, h.get("call"), "bid") if h["kind"] != "debit_spread" else 0.0
        why = exit_due(h["kind"], earn, h["debit"], pos.get("expiry"), today, cost, bid)
        if not why:
            continue
        exits[sym] = why
        px = close_order(h, oq)
        if px is None:
            continue                              # the old close_trade: one-sided quotes, the exit waits a pass
        key = "%s:%s:earnings-buyback-exit:%d" % (sym, today, int(float(pos.get("opened_at") or 0)))
        why_txt = ("earnings_buyback exit: %s kind=%s contracts=%d debit=%s earnings=%s expiry=%s"
                   % (why, h["kind"], h["contracts"], h["debit"], earn, pos.get("expiry")))
        if "net" in px:
            intents.append(Intent("exit", sym, qty_hint=h["contracts"], net_price=px["net"],
                                  order={"window_s": WINDOW_S}, signal_key=key,
                                  reason=why_txt + " legs=%s/%s natural=%.2f" % (h["long"], h["short"], -px["net"])))
        else:
            intents.append(Intent("exit", sym, qty_hint=h["contracts"],
                                  order={"type": "limit", "limit_price": px["limit"], "window_s": WINDOW_S},
                                  signal_key=key, reason=why_txt + " limit=%.2f" % px["limit"]))
        closing.add(sym)

    # entries: the scan's signals in order while slots remain
    slots = len(held_syms) + len(in_flight)
    counted = [s for s in held_syms if s not in closing] + list(in_flight)
    busy = set(held_syms) | set(in_flight)
    scan = latest_scan(extra.get("scan"), now)
    if slots < MAX_POSITIONS and scan and equity > 0:
        closed = extra.get("closed_trades") or ()
        for sig in scan_signals(scan, calendar):
            sym = sig["symbol"]
            if sym in busy:
                continue
            if slots >= MAX_POSITIONS:
                break
            if sector_blocked(sym, sectors, counted):
                skips.append((sym, "sector_cap"))
                continue
            ok, earn = earnings_window(sym, calendar, fresh, today)
            if not ok:
                skips.append((sym, "earnings_window"))
                continue
            if "%s|%s" % (sym, earn) in done:
                skips.append((sym, "event_traded"))
                continue
            spot = spot_of(sym, quotes, bars)
            if not spot or spot < MIN_STOCK_PRICE:
                skips.append((sym, "no_price" if not spot else "below_10"))
                continue
            rows = chains.get(sym) or []
            q = {r["symbol"]: r for r in rows if r.get("symbol")}
            trade = build_trade(rows, q, spot, earn, equity, today)
            if not trade:
                skips.append((sym, "no_structure"))
                continue
            n = trade["contracts"]
            days_to = (date.fromisoformat(earn) - date.fromisoformat(today)).days
            base = {"kind": trade["kind"], "earnings_date": earn, "buyback_pct": sig["buyback_pct"],
                    "filing_date": sig["filing_date"], "stock_px": round(spot, 4)}
            note = ("buyback %.1f%% filed %s earnings %s (T-%d) spot %.2f; decision100=hold_through_earnings"
                    % (sig["buyback_pct"], sig["filing_date"], earn, days_to, spot))
            if trade["kind"] == "debit_spread":
                sp = trade["spread"]
                intents.append(Intent(
                    "enter", sym, qty_hint=n, asset="mleg",
                    legs=({"symbol": sp["long_leg"]["occ"], "side": "buy", "ratio": 1,
                           "position_intent": "buy_to_open"},
                          {"symbol": sp["short_leg"]["occ"], "side": "sell", "ratio": 1,
                           "position_intent": "sell_to_open"}),
                    net_price=sp["debit"], order={"window_s": WINDOW_S}, signal_key=entry_key(sym, today, closed),
                    position_meta=dict(base, expiry=sp["expiry"], long_occ=sp["long_leg"]["occ"],
                                       short_occ=sp["short_leg"]["occ"], spread=sp),
                    reason="earnings_buyback debit_spread: long %s@%g short %s@%g expiry %s width %.2f debit %.2f "
                           "x%d; %s" % (sp["long_leg"]["occ"], sp["long_leg"]["strike"], sp["short_leg"]["occ"],
                                        sp["short_leg"]["strike"], sp["expiry"], sp["width"], sp["debit"], n, note)))
            else:
                c = trade["call"]
                intents.append(Intent(
                    "enter", sym, qty_hint=n, asset="option",
                    legs=({"symbol": c["occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},),
                    order={"type": "limit", "limit_price": c["ask"], "window_s": WINDOW_S},
                    signal_key=entry_key(sym, today, closed),
                    position_meta=dict(base, expiry=c["expiry"], strike=c["strike"], ask=c["ask"]),
                    reason="earnings_buyback long_call: %s strike %g expiry %s ask %.2f x%d; %s"
                           % (c["occ"], c["strike"], c["expiry"], c["ask"], n, note)))
            busy.add(sym)
            counted.append(sym)
            slots += 1
    return {"intents": intents, "symbols": updates, "completed": completed, "exits": exits, "skips": skips}


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_ebb_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:            # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_ebb_pass"] = memo
    return memo[1]


class EarningsBuyback(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return EarningsBuyback().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    """the old state's "completed" list: earnings events traded (SYM|date), pruned after 120 days."""
    meta = dict((context.extra or {}).get("meta") or {})
    meta["completed"] = list(_pass(bars, context)["completed"])
    return meta


def next_symbol_state(bars, slice_state, context, intents=()):
    """per held position: its (re-anchored) earnings date, kept on the position, and the event it trades; a flat
    name's event becomes a completed key and is cleared."""
    return dict(_pass(bars, context)["symbols"])
