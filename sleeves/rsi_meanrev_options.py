"""RSI Mean Reversion — Options (call debit spreads) — lean port.

EXTRACTED from the old desk's rsi_meanrev_options.py. Signal EXACTLY
the stock sleeve's (the old file imported rsi_meanrev_sleeve): RSI(2)
< 10 with close > SMA200 (fail-closed under 200 bars), using the stock
sleeve's pandas-ewm-seeded Wilder RSI (see sleeves/rsi_meanrev.py).
Execution: 14-30 DTE call debit spread via the pure form of
desk/options_exec.select_debit_spread — long leg highest strike <=
spot (ATM or 1 ITM, never OTM), short first strike >= long x 1.08.
Risk 0.25%/trade on the debit; max 5.
Exits: 50% of max profit, 7-DTE time stop, RSI(2) > 70 (snapback done).

Inputs via context.extra:
  "chains":       {SYM: [{"symbol","strike","expiration"}]} (calls)
  "quotes":       {OCC: {"bid","ask"}}
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars (arg): daily dicts ascending.

ENH (IMPROVE-rsi_meanrev_options, Edge program 2026-10-24): refuse a
spread whose debit exceeds half its width (max profit < amount risked).
Switched by context.extra["rsi_meanrev_options_enhance"]
["debit_cap"] (default ON; OFF restores the pre-change rule exactly —
any debit below the AUDIT3 identity bound). Every signal that reaches
selection records a paired control/treatment decision in the
rsi_meanrev_options_enh_journal (adopted from context.extra, filed on
self.last_evaluation); the pre-change rule is the shadow control and
never emits intents.
"""
import math
import re

from core.sleeve import BaseSleeve, Intent, SleeveConfig

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

CONFIG = SleeveConfig(
    sleeve_id="rsi_meanrev_options", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)

# ------------------------------------------------------------ ENH
ENH_EXP_ID = "ENH-RSI-MEANREV-OPTIONS-20261024"
DEBIT_CAP_FRAC = 0.5  # refuse when debit > DEBIT_CAP_FRAC * width


def debit_cap_enabled(extra):
    """ctx.extra['rsi_meanrev_options_enhance']['debit_cap'],
    default ON; non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("rsi_meanrev_options_enhance")
    if isinstance(ov, dict) and "debit_cap" in ov:
        return bool(ov["debit_cap"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("rsi_meanrev_options_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == ENH_EXP_ID \
            and isinstance(raw.get("records"), list):
        return raw
    return {"exp_id": ENH_EXP_ID, "records": []}


def debit_cap_refuses(debit, width):
    """The enhancement's one comparison: debit > width / 2 means the
    spread's maximum profit (width - debit) is less than the amount
    risked. Equality is TAKEN (max profit == risk)."""
    return width > 0 and debit > DEBIT_CAP_FRAC * width


def rsi_wilder_last(closes, period=RSI_PERIOD):
    """Identical to sleeves/rsi_meanrev.py (the stock sleeve's
    rsi_wilder: pandas ewm alpha=1/period, adjust=False)."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    alpha = 1.0 / period
    ag = al = None
    last = None
    for i, d in enumerate(deltas):
        g, l = max(d, 0.0), max(-d, 0.0)
        if ag is None:
            ag, al = g, l
        else:
            ag = ag + alpha * (g - ag)
            al = al + alpha * (l - al)
        if i + 1 < period:
            last = None
            continue
        if al == 0 and ag > 0:
            last = 100.0
        elif ag == 0 and al == 0:
            last = 50.0
        elif al == 0:
            last = 100.0
        else:
            last = 100.0 - 100.0 / (1.0 + ag / al)
    return last


def rsi_signal(closes):
    """(bool, info) — verbatim old rsi_signal over closes (the old
    fetched bars itself; here bars arrive via the core Data door)."""
    if len(closes) < MA200_PERIOD:
        return False, {"note": "ma200_warmup", "bars": len(closes)}
    rsi = rsi_wilder_last(closes)
    if rsi is None or (isinstance(rsi, float) and math.isnan(rsi)) \
            or rsi >= RSI_OVERSOLD:
        return False, {"rsi2": None if rsi is None else round(float(rsi), 2)}
    sma200 = sum(closes[-MA200_PERIOD:]) / MA200_PERIOD
    last_close = closes[-1]
    if last_close <= sma200:
        return False, {"rsi2": round(float(rsi), 2),
                       "close": round(last_close, 2),
                       "sma200": round(sma200, 2), "note": "below_ma200"}
    return True, {"rsi2": round(float(rsi), 2), "close": round(last_close, 2),
                  "sma200": round(sma200, 2)}


def select_debit_spread(chain, quotes, target_price, session_iso,
                        dte_min=DTE_MIN, dte_max=DTE_MAX,
                        width_pct=SPREAD_WIDTH_PCT):
    """Pure form of desk/options_exec.select_debit_spread (see
    sleeves/ema_vwap_options.py for the shared rule text); this sleeve
    passes target = spot and debit_range=None (fragment 098)."""
    from datetime import date as _date
    try:
        ref = _date.fromisoformat(session_iso)
    except ValueError:
        return None
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
        try:
            strike = float(c["strike"])
            dte = (_date.fromisoformat(exp) - ref).days
        except (TypeError, ValueError, KeyError):
            continue
        if dte_min <= dte <= dte_max:
            by_exp.setdefault(exp, []).append(
                {"occ": c["symbol"], "strike": strike})
    if not by_exp:
        return None
    expiry = sorted(by_exp.keys())[0]
    legs = sorted(by_exp[expiry], key=lambda c: c["strike"])
    long_leg = None
    for c in legs:
        if c["strike"] <= target_price:
            long_leg = c
    if long_leg is None:
        long_leg = legs[0]
    target_short = long_leg["strike"] * (1 + width_pct)
    short_leg = next((c for c in legs if c["strike"] >= target_short), None)
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
    if long_bid > 0 and (long_ask - long_bid) / mid > LIQ_GATE_FRAC:
        return None
    debit = long_ask - short_bid
    if debit <= 0:
        return None
    width = short_leg["strike"] - long_leg["strike"]
    # AUDIT3-C-05 (2026-10-16): a debit at or above the width is a
    # guaranteed-loss structure (max profit = width - debit <= 0)
    # under ANY parameterization — it arises only from crossed or
    # stale leg quotes. The debit_range band is a strategy
    # parameter and stays the caller's; this identity bound is
    # not. (pick_spread passes debit_range=None, so without it
    # the sleeve sized and bought negative-max-profit spreads.)
    if width > 0 and debit >= width:
        return None
    return {"expiry": expiry,
            "long_leg": dict(long_leg, ask=long_ask, bid=long_bid),
            "short_leg": dict(short_leg, bid=short_bid),
            "width": round(width, 2), "debit": round(debit, 2),
            "max_profit": round(width - debit, 2),
            "breakeven": round(long_leg["strike"] + debit, 2)}


def size_spreads(equity, debit, halve=False):
    """Old _size_spreads: spread_qty_for_risk, optionally halved."""
    if not equity or equity <= 0 or debit <= 0:
        qty = 0
    else:
        qty = max(0, int((equity * RISK_FRACTION) / (debit * 100)))
    if halve:
        qty = int(qty / 2)
    return qty


def _occ_strike(occ):
    m = re.search(r"(\d{8})$", str(occ or ""))
    return int(m.group(1)) / 1000.0 if m else None


def _spread_view(pos):
    """The spread dict exit math reads, in EITHER recorded shape —
    sleeve-native {long_leg:{occ}, short_leg:{occ}, expiry, max_profit}
    or the core-recorded shape (legs[] + spread={long_occ, short_occ},
    top-level expiry, entry_debit). The old exit path indexed
    spread["long_leg"] on the core shape and raised KeyError, killing
    the sleeve's signal on every held spread. Width/max_profit are
    rebuilt with select_debit_spread's own arithmetic (width from the
    OCC strikes; max_profit = width - entry debit)."""
    spread = pos.get("spread")
    if isinstance(spread, dict) and isinstance(spread.get("long_leg"), dict):
        return spread
    long_occ = short_occ = None
    expiry = pos.get("expiry")
    if isinstance(spread, dict):
        long_occ = spread.get("long_occ")
        short_occ = spread.get("short_occ")
        expiry = spread.get("expiry") or expiry
    for leg in pos.get("legs") or []:
        if not isinstance(leg, dict):
            continue
        pi, side = leg.get("position_intent"), leg.get("side")
        if pi == "buy_to_open" or (pi is None and side == "buy"):
            long_occ = long_occ or leg.get("symbol")
        if pi == "sell_to_open" or (pi is None and side == "sell"):
            short_occ = short_occ or leg.get("symbol")
    long_occ = pos.get("long_occ") or long_occ
    short_occ = pos.get("short_occ") or short_occ
    debit = pos.get("entry_debit") or pos.get("debit") or 0
    ls, ss = _occ_strike(long_occ), _occ_strike(short_occ)
    width = (ss - ls) if (ls is not None and ss is not None) else 0.0
    return {"expiry": expiry,
            "long_leg": {"occ": long_occ}, "short_leg": {"occ": short_occ},
            "width": round(width, 2), "debit": debit,
            "max_profit": round(width - debit, 2) if width and debit else 0}


def spread_close_value(spread, quotes):
    """Long bid - short ask. None when either leg is unquotable."""
    lq = (quotes or {}).get((spread.get("long_leg") or {}).get("occ")) or {}
    sq = (quotes or {}).get((spread.get("short_leg") or {}).get("occ")) or {}
    try:
        lb, sa = float(lq.get("bid") or 0), float(sq.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if lb <= 0 or sa <= 0:
        return None
    return round(lb - sa, 2)


def _dte(spread, session_iso):
    try:
        from datetime import date as _date
        return (_date.fromisoformat(str(spread["expiry"])[:10])
                - _date.fromisoformat(session_iso)).days
    except (ValueError, TypeError, KeyError):
        return None


def exit_due(pos, session_iso, close_value, rsi2):
    """Verbatim old order: 50% of max profit, 7-DTE, RSI(2) > 70."""
    entry_debit = pos.get("entry_debit") or pos.get("debit") or 0
    max_profit = _spread_view(pos).get("max_profit") or 0
    if close_value is not None and entry_debit > 0 and max_profit > 0:
        if close_value - entry_debit >= PROFIT_TARGET_FRAC * max_profit:
            return "profit_target_50pct"
    dte = _dte(pos.get("spread") or {}, session_iso)
    if dte is not None and dte <= EXIT_DTE:
        return "dte_time_stop_%d" % dte
    if rsi2 is not None and rsi2 > RSI_OVERBOUGHT:
        return "rsi2_overbought_%.1f" % rsi2
    return None


class RsiMeanrevOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        equity = float(context.equity or 0.0)
        enh_on = debit_cap_enabled(extra)
        journal = _enh_journal(extra)
        universe = extra.get("universe") or sorted(bars.keys())
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            closes = [float(b["c"]) for b in bl]
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                pos = dict(pos, spread=_spread_view(pos))
                value = spread_close_value(pos["spread"], quotes)
                rsi2 = rsi_wilder_last(closes) if len(closes) >= 5 else None
                reason = exit_due(pos, context.session, value, rsi2)
                if reason:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(closes[-1], 2) if closes else None,
                        reason="rsi_meanrev_options exit: %s value=%s"
                               % (reason, value)))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            ok, info = rsi_signal(closes)
            if not ok:
                continue
            spot = closes[-1]
            sp = select_debit_spread(chains.get(sym), quotes, spot,
                                     context.session)
            if not sp:
                continue
            # ENH paired record: control (pre-change) takes any spread
            # select_debit_spread returns; treatment refuses
            # debit > width/2. Switch OFF => treatment == control.
            refused = debit_cap_refuses(sp["debit"], sp["width"])
            journal["records"].append({
                "symbol": sym, "session": context.session,
                "debit": sp["debit"], "width": sp["width"],
                "control": "enter",
                "treatment": "refuse_debit_cap" if refused else "enter",
                "enhance_switch": enh_on})
            if enh_on and refused:
                continue
            qty = size_spreads(equity, sp["debit"])
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(spot, 2),
                reason="rsi_meanrev_options call_debit_spread: long=%s@%.2f "
                       "short=%s@%.2f expiry=%s width=%.2f debit=%.2f "
                       "rsi2=%.2f sma200=%.2f structure=call_debit_spread "
                       "dte_window=%d-%d width_pct=%.2f"
                       % (sp["long_leg"]["occ"], sp["long_leg"]["strike"],
                          sp["short_leg"]["occ"], sp["short_leg"]["strike"],
                          sp["expiry"], sp["width"], sp["debit"],
                          info["rsi2"], info["sma200"],
                          DTE_MIN, DTE_MAX, SPREAD_WIDTH_PCT)))
            open_n += 1
        self.last_evaluation = {
            "rsi_meanrev_options_enh_journal": journal}
        return intents


def signal(bars, slice_state, context):
    return RsiMeanrevOptions().signal(bars, slice_state, context)
