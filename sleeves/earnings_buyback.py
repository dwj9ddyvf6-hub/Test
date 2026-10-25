"""Earnings Buyback — lean-desk port (Wave B).

EXTRACTED from the old desk's earnings_buyback_sleeve.py. Event-driven:
buyback >= 5% announced 15-30 calendar days before earnings (SPEC
Step 1 timing), entry T-15..T-8 before earnings, DEFINED-RISK debit
spread (30-45 DTE, expiry strictly AFTER earnings) or long-call
fallback, exit T+15 trading days after earnings. See
ports/earnings_buyback.md.

DECISION #100 (2026-10-13) — carried as strategy, not plumbing: this
sleeve's defined-risk structures (max loss = debit paid) are EXEMPT
from the desk's no-holding-through-earnings rule / Decision #8
blackout; the position is HELD THROUGH the event toward the T+15
exit. Decision #8 still binds every other sleeve. Scan-freshness:
the old SCAN_MAX_AGE_DAYS=8 (a scan older than 8 days is stale) is
core Data's duty; scan rows arrive via extra["scan_signals"] already
parsed from the latest buyback_scan_*.json, and extra["scan_age_days"]
gates freshness here fail-closed.

Structure rules (pure forms of desk/options_exec selectors): debit
spread = nearest 30-45 DTE expiry, long highest strike <= spot, short
first strike >= long x 1.10, long-leg quote gate 10%, debit/width
ratio inside DEBIT_RANGE (0.30, 0.45) — this sleeve HAS a SPEC'd band
(fragment 098). Long-call fallback: first strike >= spot x 1.02,
quote gate 15%. Stock price >= $10 (SPEC universe filter). Risk
0.5%/trade, max 4, max 2 per sector (unknown sector never blocked).
Exits: T+15 time stop, 50% profit target, -50% stop on debit, 5-DTE
floor. Spread exits compare the live VALUE (=-close cost) to debit —
the 2026-10-11 inverted-comparison fix is preserved.

Inputs via context.extra:
  "scan_signals": [{"symbol","buyback_pct","filing_date"}]
  "earnings":     {SYM: "YYYY-MM-DD"}, "scan_age_days": float
  "chains"/"quotes": as the other options sleeves
  "sectors":      {SYM: sector} (old desk/risk SECTORS map, core Data)
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars (arg): daily dicts (spot = last close; bar dates drive T+15).

ENH (IMPROVE-earnings_buyback, Edge program 2026-10-24): one added
qualification on structure selection — accept a spread or call only
if its expiry is at least 26 calendar days after the earnings date
(21 calendar days for the T+15-trading-day hold + the 5-DTE floor);
among qualifying expiries keep the nearest; if none in the 30-45 DTE
window qualifies, refuse the entry. Switched by
context.extra["earnings_buyback_improve"]["expiry_gap_gate"]
(default ON; OFF restores the pre-change nearest-expiry rule
exactly). Decisions record a paired control/treatment record on
self.last_evaluation["enhance_exp"].
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

BUYBACK_MIN_PCT = 5.0
EARN_DAYS_MIN, EARN_DAYS_MAX = 8, 15      # entry window T-15..T-8
ANNOUNCE_DAYS_MIN, ANNOUNCE_DAYS_MAX = 15, 30  # SPEC Step 1 filing window
DTE_MIN, DTE_MAX = 30, 45
DTE_FLOOR = 5
MIN_STOCK_PRICE = 10.0
EXIT_TRADING_DAYS_AFTER_EARNINGS = 15
SPREAD_WIDTH_PCT = 0.10
DEBIT_RANGE = (0.30, 0.45)
RISK_FRACTION = 0.005
MAX_POSITIONS = 4
MAX_SAME_SECTOR = 2
PROFIT_TARGET_FRAC = 0.50
STOP_FRAC = 0.50
SCAN_MAX_AGE_DAYS = 8
LONG_CALL_OTM_PCT = 0.02
MIN_DAYS_EXPIRY_AFTER_EARNINGS = 26  # ENH: 21 cal days (T+15 td) + 5-DTE floor

# ------------------------------------------------------------ ENH experiment
EXP_ID = "ENH-EARNINGS-BUYBACK-20261024"

def expiry_gap_gate_enabled(extra):
    ov = (extra or {}).get("earnings_buyback_improve")
    if isinstance(ov, dict) and "expiry_gap_gate" in ov:
        return bool(ov["expiry_gap_gate"])
    return True

def expiry_gap_ok(expiry_str, earnings_date_str):
    """True when expiry is >= 26 calendar days after earnings."""
    exp_d, earn_d = _parse_date(expiry_str), _parse_date(earnings_date_str)
    if exp_d is None or earn_d is None:
        return False
    return (exp_d - earn_d).days >= MIN_DAYS_EXPIRY_AFTER_EARNINGS

CONFIG = SleeveConfig(
    sleeve_id="earnings_buyback", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _parse_date(s):
    try:
        from datetime import date as _date
        return _date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def qualify_signal(row, earnings):
    """Pure form of the old scan_signals filter: buyback >= 5%,
    filing 15-30 calendar days before a KNOWN earnings date;
    unparseable filing or unknown earnings fails closed.
    Returns the normalized signal dict or None."""
    try:
        sym = str(row.get("ticker") or row.get("symbol") or "").upper()
        pct = float(row.get("buyback_pct") or 0)
    except (TypeError, ValueError):
        return None
    if not sym or pct < BUYBACK_MIN_PCT:
        return None
    filing_d = _parse_date(row.get("filing_date"))
    earn_d = _parse_date((earnings or {}).get(sym))
    if filing_d is None or earn_d is None:
        return None
    dd = (earn_d - filing_d).days
    if not (ANNOUNCE_DAYS_MIN <= dd <= ANNOUNCE_DAYS_MAX):
        return None
    return {"symbol": sym, "buyback_pct": pct,
            "filing_date": row.get("filing_date"),
            "earnings_date": earn_d.isoformat()}


def expiry_after_earnings(expiry_str, earnings_date_str):
    """Decision #100: structure must expire strictly AFTER earnings."""
    exp_d, earn_d = _parse_date(expiry_str), _parse_date(earnings_date_str)
    if exp_d is None or earn_d is None:
        return False
    return exp_d > earn_d


def _filter_expiries(by_exp, earnings_date, min_gap_days):
    if min_gap_days is None:
        return by_exp
    return {e: legs for e, legs in by_exp.items()
            if expiry_gap_ok(e, earnings_date)}


def select_debit_spread(chain, quotes, spot, session_iso,
                        earnings_date=None, min_gap_days=None):
    """Pure select_debit_spread with THIS sleeve's SPEC'd DEBIT_RANGE
    ratio veto (fragment 098: callers with a band pass it explicitly)."""
    from datetime import date as _date
    ref = _parse_date(session_iso)
    if ref is None:
        return None
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
        try:
            strike = float(c["strike"])
            dte = (_date.fromisoformat(exp) - ref).days
        except (TypeError, ValueError, KeyError):
            continue
        if DTE_MIN <= dte <= DTE_MAX:
            by_exp.setdefault(exp, []).append(
                {"occ": c["symbol"], "strike": strike})
    by_exp = _filter_expiries(by_exp, earnings_date, min_gap_days)
    if not by_exp:
        return None
    expiry = sorted(by_exp.keys())[0]
    legs = sorted(by_exp[expiry], key=lambda c: c["strike"])
    long_leg = None
    for c in legs:
        if c["strike"] <= spot:
            long_leg = c
    if long_leg is None:
        long_leg = legs[0]
    short_leg = next((c for c in legs
                      if c["strike"] >= long_leg["strike"] * (1 + SPREAD_WIDTH_PCT)),
                     None)
    if short_leg is None:
        return None
    lq = (quotes or {}).get(long_leg["occ"]) or {}
    sq = (quotes or {}).get(short_leg["occ"]) or {}
    try:
        long_ask, long_bid = float(lq.get("ask") or 0), float(lq.get("bid") or 0)
        short_bid = float(sq.get("bid") or 0)
    except (TypeError, ValueError):
        return None
    if long_ask <= 0:
        return None
    mid = (long_ask + long_bid) / 2 if long_bid > 0 else long_ask
    if long_bid > 0 and (long_ask - long_bid) / mid > 0.10:
        return None
    debit = long_ask - short_bid
    if debit <= 0:
        return None
    width = short_leg["strike"] - long_leg["strike"]
    if width <= 0 or not (DEBIT_RANGE[0] <= debit / width <= DEBIT_RANGE[1]):
        return None
    return {"expiry": expiry,
            "long_leg": dict(long_leg, ask=long_ask, bid=long_bid),
            "short_leg": dict(short_leg, bid=short_bid),
            "width": round(width, 2), "debit": round(debit, 2),
            "max_profit": round(width - debit, 2)}


def select_long_call(chain, quotes, spot, session_iso,
                     earnings_date=None, min_gap_days=None):
    """Pure select_long_call (otm 2%, quote gate 15%)."""
    ref = _parse_date(session_iso)
    if ref is None:
        return None
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
        try:
            strike = float(c["strike"])
            dte = (_parse_date(exp) - ref).days
        except (TypeError, ValueError, KeyError):
            continue
        if DTE_MIN <= dte <= DTE_MAX:
            by_exp.setdefault(exp, []).append(
                {"occ": c["symbol"], "strike": strike})
    by_exp = _filter_expiries(by_exp, earnings_date, min_gap_days)
    if not by_exp:
        return None
    expiry = sorted(by_exp.keys())[0]
    legs = sorted(by_exp[expiry], key=lambda c: c["strike"])
    target = spot * (1 + LONG_CALL_OTM_PCT)
    sel = next((c for c in legs if c["strike"] >= target), None)
    if sel is None:
        return None
    q = (quotes or {}).get(sel["occ"]) or {}
    try:
        ask, bid = float(q.get("ask") or 0), float(q.get("bid") or 0)
    except (TypeError, ValueError):
        return None
    if ask <= 0:
        return None
    if bid > 0 and (ask - bid) / ((ask + bid) / 2) > 0.15:
        return None
    return {"expiry": expiry, "occ": sel["occ"], "strike": sel["strike"],
            "ask": ask, "bid": bid}


def build_trade(chain, quotes, spot, earnings_date, equity, session_iso,
                expiry_gap_gate=True):
    """Spread first, long-call fallback; both must expire AFTER
    earnings (Decision #100) and size > 0 at 0.5% risk. Verbatim
    decision order from the old build_trade. ENH: with
    expiry_gap_gate ON (default), structures must also expire
    >= 26 calendar days after earnings (nearest qualifying kept)."""
    if not spot or spot < MIN_STOCK_PRICE:
        return None
    gap = MIN_DAYS_EXPIRY_AFTER_EARNINGS if expiry_gap_gate else None
    sp = select_debit_spread(chain, quotes, spot, session_iso,
                             earnings_date=earnings_date, min_gap_days=gap)
    if sp and expiry_after_earnings(sp["expiry"], earnings_date):
        n = max(0, int((equity * RISK_FRACTION) / (sp["debit"] * 100))) \
            if sp["debit"] > 0 else 0
        if n > 0:
            return {"kind": "debit_spread", "spread": sp, "contracts": n,
                    "stock_px": spot}
        return None  # old: zero contracts on the spread ends the attempt
    call = select_long_call(chain, quotes, spot, session_iso,
                            earnings_date=earnings_date, min_gap_days=gap)
    if call and expiry_after_earnings(call["expiry"], earnings_date):
        n = max(0, int((equity * RISK_FRACTION) / (call["ask"] * 100))) \
            if call["ask"] > 0 else 0
        if n > 0:
            return {"kind": "long_call", "call": call, "contracts": n,
                    "stock_px": spot}
    return None


def trading_days_since_earnings(earnings_date, dates):
    """Trading days from the earnings date to the last bar date, on
    the bar calendar (old counted NYSE sessions; bars ARE sessions)."""
    if not earnings_date or not dates:
        return None
    after = [d for d in dates if d > str(earnings_date)[:10]]
    return len(after)


def exit_due(pos, dates, session_iso, spread_value=None, call_bid=None):
    """Verbatim old order: T+15, +50%, -50%, 5-DTE floor. The spread
    branch compares live VALUE to debit (2026-10-11 fix)."""
    t_since = trading_days_since_earnings(pos.get("earnings_date"), dates)
    if t_since is not None and t_since >= EXIT_TRADING_DAYS_AFTER_EARNINGS:
        return "time_stop_t_plus_15"
    debit = pos.get("debit") or 0
    if pos.get("kind") == "debit_spread":
        if spread_value is not None and debit > 0:
            if spread_value >= debit * (1 + PROFIT_TARGET_FRAC):
                return "profit_target_50pct"
            if spread_value <= debit * (1 - STOP_FRAC):
                return "stop_minus50pct"
    else:
        if call_bid and call_bid > 0 and debit > 0:
            if call_bid >= debit * (1 + PROFIT_TARGET_FRAC):
                return "profit_target_50pct"
            if call_bid <= debit * (1 - STOP_FRAC):
                return "stop_minus50pct"
    exp_d = _parse_date(pos.get("expiry"))
    ref = _parse_date(session_iso)
    if exp_d is not None and ref is not None \
            and (exp_d - ref).days <= DTE_FLOOR:
        return "dte_floor_5"
    return None


class EarningsBuyback(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        earnings = extra.get("earnings") or {}
        sectors = extra.get("sectors") or {}
        equity = float(context.equity or 0.0)
        gate_on = expiry_gap_gate_enabled(extra)
        exp_records = []
        intents = []
        # exits first (never gated)
        for sym, st in sorted(state.items()):
            pos = (st or {}).get("position")
            if not pos:
                continue
            qty = int(float(pos.get("qty") or 0))
            if qty <= 0:
                continue
            bl = bars.get(sym) or []
            value, bid = None, None
            if pos.get("kind") == "debit_spread" and pos.get("spread"):
                sp = pos["spread"]
                lq = quotes.get(sp["long_leg"]["occ"]) or {}
                sq = quotes.get(sp["short_leg"]["occ"]) or {}
                try:
                    lb, sa = float(lq.get("bid") or 0), float(sq.get("ask") or 0)
                    value = lb - sa if lb > 0 and sa > 0 else None
                except (TypeError, ValueError):
                    value = None
            elif pos.get("occ"):
                q = quotes.get(pos["occ"]) or {}
                try:
                    bid = float(q.get("bid") or 0)
                except (TypeError, ValueError):
                    bid = None
            reason = exit_due(pos, _dates(bl), context.session, value, bid)
            if reason:
                intents.append(Intent(
                    "exit", sym, qty_hint=qty,
                    price_hint=round(float(bl[-1]["c"]), 2) if bl else None,
                    reason="earnings_buyback exit: %s kind=%s" % (reason, pos.get("kind"))))
        # entries
        age = extra.get("scan_age_days")
        try:
            age_f = float(age) if age is not None else None
        except (TypeError, ValueError):
            age_f = None  # unparseable age fails closed, never raises
        if age_f is None or not math.isfinite(age_f) \
                or age_f > SCAN_MAX_AGE_DAYS:
            return intents  # stale/absent scan: fail closed (old SCAN_MAX_AGE)
        open_syms = [s for s, st in state.items() if (st or {}).get("position")]
        if len(open_syms) >= MAX_POSITIONS or equity <= 0:
            return intents
        today = _parse_date(context.session)
        for row in extra.get("scan_signals") or []:
            sig = qualify_signal(row, earnings)
            if not sig:
                continue
            sym = sig["symbol"]
            if sym in open_syms:
                continue
            earn_d = _parse_date(sig["earnings_date"])
            days_to = (earn_d - today).days if earn_d and today else None
            if days_to is None or not (EARN_DAYS_MIN <= days_to <= EARN_DAYS_MAX):
                continue  # entry window T-15..T-8 only
            sector = sectors.get(sym)
            if sector is not None:
                same = sum(1 for s in open_syms if sectors.get(s) == sector)
                if same >= MAX_SAME_SECTOR:
                    continue
            bl = bars.get(sym) or []
            if not bl:
                continue
            spot = float(bl[-1]["c"])
            trade_c = build_trade(chains.get(sym), quotes, spot,
                                  sig["earnings_date"], equity,
                                  context.session, expiry_gap_gate=False)
            trade = build_trade(chains.get(sym), quotes, spot,
                                sig["earnings_date"], equity, context.session,
                                expiry_gap_gate=gate_on)
            exp_records.append({
                "symbol": sym, "earnings_date": sig["earnings_date"],
                "control_trade": None if not trade_c else trade_c["kind"],
                "control_expiry": None if not trade_c else
                (trade_c.get("spread") or trade_c.get("call"))["expiry"],
                "treatment_trade": None if not trade else trade["kind"],
                "treatment_expiry": None if not trade else
                (trade.get("spread") or trade.get("call"))["expiry"],
                "switch_on": gate_on})
            if not trade:
                continue
            if trade["kind"] == "debit_spread":
                sp = trade["spread"]
                desc = ("long=%s@%.2f short=%s@%.2f expiry=%s debit=%.2f"
                        % (sp["long_leg"]["occ"], sp["long_leg"]["strike"],
                           sp["short_leg"]["occ"], sp["short_leg"]["strike"],
                           sp["expiry"], sp["debit"]))
                expiry = sp["expiry"]
            else:
                call = trade["call"]
                desc = "occ=%s strike=%.2f expiry=%s ask=%.2f" % (
                    call["occ"], call["strike"], call["expiry"], call["ask"])
                expiry = call["expiry"]
            intents.append(Intent(
                "enter", sym, qty_hint=trade["contracts"],
                price_hint=round(spot, 2),
                reason="earnings_buyback %s: %s buyback_pct=%.1f "
                       "earnings=%s days_to=%d structure=%s dte_window=%d-%d "
                       "decision100=hold_through_earnings(defined-risk)"
                       % (trade["kind"], desc, sig["buyback_pct"],
                          sig["earnings_date"], days_to, trade["kind"],
                          DTE_MIN, DTE_MAX)))
            open_syms.append(sym)
            if len(open_syms) >= MAX_POSITIONS:
                break
        if exp_records:
            self.last_evaluation = {"enhance_exp": {
                "exp_id": EXP_ID, "switch_on": gate_on,
                "records": exp_records}}
        return intents


def signal(bars, slice_state, context):
    return EarningsBuyback().signal(bars, slice_state, context)
