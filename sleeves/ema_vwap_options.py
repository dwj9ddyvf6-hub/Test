"""EMA-VWAP Options — call debit spreads — lean-desk port (Wave B).

EXTRACTED from the old desk's ema_vwap_options.py. Signal identical to
the equity sleeve (the old file imported ema_vwap_sleeve's helpers so
the two could never drift; the VWAP helpers are mirrored here for the
same reason). Execution: call debit spread on the nearest 14-30 DTE
expiry — long leg ~2% OTM, width 6% (short ~8% OTM) — via the pure
form of desk/options_exec.select_debit_spread over a chain snapshot
the core Data door provides. See ports/ema_vwap_options.md.

Risk 0.25%/trade sized on debit paid; max 5. Long options are
defined-risk: no disaster stop; time exits instead.
Exits (first trigger): 50% of max profit (conservative live value =
long bid - short ask), 7-DTE time stop, underlying reverted to/above
VWAP (mean reversion complete), 21-day max hold.

Inputs via context.extra:
  "chains":       {SYM: [{"symbol","strike","expiration"}]} (calls)
  "quotes":       {OCC: {"bid","ask"}}
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars (arg): daily dicts ascending (same series as the equity sleeve).

ENH (IMPROVE-ema_vwap_options, Edge program 2026-10-24): the VWAP
reversion exit fires only when the spread's conservative live value
(long bid - short ask) is at or above the entry debit; a below-debit
reversion print does not exit — the position continues under the
50%-of-max-profit, 7-DTE and 21-day max-hold exits. Switched by
context.extra["ema_vwap_options_improve"]["reversion_value_gate"]
(default ON; OFF restores the pre-change rule exactly). Divergent
decisions record a paired control/treatment record on
self.last_evaluation["enhance_exp"].
"""
import math
import re
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

RISK_FRACTION = 0.0025
MAX_POSITIONS = 5
DTE_MIN, DTE_MAX = 14, 30
WIDTH_PCT = 0.06
LONG_OTM_PCT = 0.02
EXIT_DTE = 7
PROFIT_TARGET_PCT = 0.50
MAX_HOLD_DAYS = 21
WARMUP_BARS = 30
VWAP_WINDOW = 20
DEV_PCT = 0.02
LIQ_GATE_FRAC = 0.10  # select_debit_spread's long-leg liquidity gate

CONFIG = SleeveConfig(
    sleeve_id="ema_vwap_options", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


# --- signal helpers mirrored from ema_vwap_sleeve (via sleeves/ema_vwap)
def rolling_vwap(bars, window=VWAP_WINDOW):
    """Mirror of the parent sleeves/ema_vwap.py rolling_vwap, INCLUDING
    its P3 D4 cure (2026-10-15): old-desk pandas semantics are
    (tp*vol).rolling(20).sum()/vol.rolling(20).sum() with
    vol.replace(0, NaN) and min_periods=window — ANY zero/missing-
    volume bar inside the window makes the VWAP None (no anchor, no
    signal). The exclusion form this copy carried averaged the
    remaining bars and traded on an anchor the old desk did not have
    (coordinator cross-family consistency cure D4-X)."""
    if len(bars) < window:
        return None
    num = den = 0.0
    for b in bars[-window:]:
        v = b.get("v")
        if v is None or float(v) == 0:
            return None
        v = float(v)
        tp = (float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0
        num += tp * v
        den += v
    return num / den if den > 0 else None


def deviation_below(bars, pct=DEV_PCT):
    if len(bars) < 21:
        return False
    v = rolling_vwap(bars)
    c = float(bars[-1]["c"])
    if v is None or not math.isfinite(v) or v <= 0:
        return False
    return bool(c < v * (1.0 - pct))


def reverted_to_vwap(bars):
    if len(bars) < 21:
        return False
    v = rolling_vwap(bars)
    c = float(bars[-1]["c"])
    if v is None or not math.isfinite(v) or v <= 0:
        return False
    return bool(c >= v)


# --- options selection (pure select_debit_spread) -------------------
def select_debit_spread(chain, quotes, target_price, session_iso,
                        dte_min=DTE_MIN, dte_max=DTE_MAX,
                        width_pct=WIDTH_PCT, debit_range=None):
    """Pure form of desk/options_exec.select_debit_spread: nearest
    expiry in the DTE window; long = highest strike <= target_price
    (chain[0] if none); short = first strike >= long*(1+width_pct);
    long-leg (ask-bid)/mid <= 10% when bid > 0; debit = long ask -
    short bid must be > 0; optional debit/width ratio band veto."""
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
    if debit_range is not None and width > 0:
        ratio = debit / width
        if not (debit_range[0] <= ratio <= debit_range[1]):
            return None
    return {"expiry": expiry,
            "long_leg": dict(long_leg, ask=long_ask, bid=long_bid),
            "short_leg": dict(short_leg, bid=short_bid),
            "width": round(width, 2), "debit": round(debit, 2),
            "max_profit": round(width - debit, 2),
            "breakeven": round(long_leg["strike"] + debit, 2)}


def pick_spread(chain, quotes, spot, session_iso):
    """Old pick_spread: target = spot*(1+LONG_OTM_PCT); debit_range=None
    explicitly (2026-10-13 fragment 098: no SPEC'd ratio band here)."""
    return select_debit_spread(chain, quotes, spot * (1.0 + LONG_OTM_PCT),
                               session_iso, debit_range=None)


def spread_qty_for_risk(debit, equity, risk_fraction=RISK_FRACTION):
    """desk/options_exec.spread_qty_for_risk, verbatim."""
    if not equity or equity <= 0 or debit <= 0:
        return 0
    return max(0, int((equity * risk_fraction) / (debit * 100)))


def spread_value(spread, quotes):
    """Conservative live value: long bid - short ask. None unquotable."""
    lq = (quotes or {}).get(spread["long_leg"]["occ"]) or {}
    sq = (quotes or {}).get(spread["short_leg"]["occ"]) or {}
    try:
        lb, sa = float(lq.get("bid") or 0), float(sq.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if lb <= 0 or sa <= 0:
        return None
    return lb - sa


def _occ_strike(occ):
    m = re.search(r"(\d{8})$", str(occ or ""))
    return int(m.group(1)) / 1000.0 if m else None


def _spread_view(pos):
    """The spread dict exit math reads, in EITHER recorded shape.

    Sleeve-native records carry spread={long_leg:{occ}, short_leg:{occ},
    expiry, max_profit, ...} (the select_debit_spread result). A
    core-recorded position (core/dispatch derived fields +
    state_store.normalize_position) instead carries legs[] plus
    spread={long_occ, short_occ}, a top-level expiry and entry_debit —
    the old exit path indexed spread["long_leg"] and raised KeyError,
    killing the sleeve's signal (and the dispatch tick) on every held
    spread. Rebuild the identical view from the core shape: width from
    the OCC strikes, max_profit = width - entry debit (the same
    arithmetic select_debit_spread returns)."""
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


def _dte(expiry, session_iso):
    try:
        from datetime import date as _date
        return (_date.fromisoformat(str(expiry)[:10])
                - _date.fromisoformat(session_iso)).days
    except (ValueError, TypeError):
        return None


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


# ------------------------------------------------------------ ENH experiment
EXP_ID = "ENH-EMA-VWAP-OPTIONS-20261024"

def reversion_value_gate_enabled(extra):
    ov = (extra or {}).get("ema_vwap_options_improve")
    if isinstance(ov, dict) and "reversion_value_gate" in ov:
        return bool(ov["reversion_value_gate"])
    return True

def reversion_pays(value, entry_debit):
    """True when the spread's live value covers the entry debit."""
    return value is not None and entry_debit is not None \
        and float(value) >= float(entry_debit)

def exit_due(pos, bars, quotes, session_iso, reversion_gate=True):
    """(reason, value) — verbatim old order: 50% max profit, 7-DTE,
    VWAP reversion, 21-day max hold (sessions since entry date).
    ENH: with reversion_gate ON, the reversion exit additionally
    requires reversion_pays(value, entry_debit)."""
    spread = _spread_view(pos)
    entry_debit = pos.get("entry_debit") or pos.get("debit") \
        or spread.get("debit") or 0
    value = spread_value(spread, quotes)
    if value is not None and spread["max_profit"] > 0:
        if value - entry_debit >= PROFIT_TARGET_PCT * spread["max_profit"]:
            return "profit_target_50pct", value
    dte = _dte(spread.get("expiry"), session_iso)
    if dte is not None and dte <= EXIT_DTE:
        return "dte_time_stop_7", value
    if bars and reverted_to_vwap(bars) and \
            (not reversion_gate or reversion_pays(value, entry_debit)):
        return "vwap_reversion", value
    dates = _dates(bars) if bars else []
    if pos.get("entry_date") and pos["entry_date"] in dates:
        if len(dates) - 1 - dates.index(pos["entry_date"]) >= MAX_HOLD_DAYS:
            return "max_hold_21d", value
    return None, value


class EmaVwapOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        equity = float(context.equity or 0.0)
        universe = extra.get("universe") or sorted(bars.keys())
        gate_on = reversion_value_gate_enabled(extra)
        exp_records = []
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                reason_c, _v = exit_due(pos, bl, quotes, context.session,
                                        reversion_gate=False)
                reason, value = exit_due(pos, bl, quotes, context.session,
                                         reversion_gate=gate_on)
                if reason_c != reason:
                    exp_records.append({
                        "symbol": sym, "value": value,
                        "control_exit": reason_c,
                        "treatment_exit": reason, "switch_on": gate_on})
                if reason:
                    view = _spread_view(pos)
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bl[-1]["c"]), 2) if bl else None,
                        reason="ema_vwap_options exit: %s value=%s legs=%s/%s"
                               % (reason, value, view["long_leg"]["occ"],
                                  view["short_leg"]["occ"])))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0 or len(bl) < WARMUP_BARS:
                continue
            if not deviation_below(bl):
                continue
            spot = float(bl[-1]["c"])
            sp = pick_spread(chains.get(sym), quotes, spot, context.session)
            if not sp:
                continue
            qty = spread_qty_for_risk(sp["debit"], equity)
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(spot, 2),
                reason="ema_vwap_options call_debit_spread: long=%s@%.2f "
                       "short=%s@%.2f expiry=%s width=%.2f debit=%.2f "
                       "structure=call_debit_spread dte_window=%d-%d "
                       "long_otm_pct=%.2f width_pct=%.2f"
                       % (sp["long_leg"]["occ"], sp["long_leg"]["strike"],
                          sp["short_leg"]["occ"], sp["short_leg"]["strike"],
                          sp["expiry"], sp["width"], sp["debit"],
                          DTE_MIN, DTE_MAX, LONG_OTM_PCT, WIDTH_PCT)))
            open_n += 1
        if exp_records:
            self.last_evaluation = {"enhance_exp": {
                "exp_id": EXP_ID, "switch_on": gate_on,
                "records": exp_records}}
        return intents


def signal(bars, slice_state, context):
    return EmaVwapOptions().signal(bars, slice_state, context)
