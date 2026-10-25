"""Capitulation Reversal — Options (0-7 DTE long calls) — lean port.

EXTRACTED from the old desk's capitulation_options.py. The 5-part
capitulation signal is MIRRORED verbatim from capitulation_sleeve.py
(as the old options file itself mirrored it); execution becomes a
pure strike/expiry selection over a chain snapshot the core Data
door provides. See ports/capitulation_options.md.

Strategy: same 5-part signal as the equity sleeve (1H RSI(14) < 20,
climax volume > 2x the 20 bars before it, climax low within 2% of
daily EMA200, first green bar with RSI turning up, daily ATR% > 5%).
Execution: ONE long call, 0-7 DTE, ~2% OTM (desk/options_exec
select_long_call rule: first strike >= spot x 1.02 on the nearest
expiry in window; quote gate (ask-bid)/mid <= 15%).
Risk 0.10%/trade sized on premium (premium paid IS the max loss — no
disaster stop); max 5. Fear gate defers entries exactly as the equity
sleeve (extra["fear_ok"], fail-closed when absent — LC-1, 2026-10-18).
Exits (first trigger): +75% premium profit-take, 1-DTE time stop
(never hold into expiry), underlying -3% from entry (thesis broken).

Inputs via context.extra:
  "bars_1h":      {SYM: [closed 1H bars]}
  "chains":       {SYM: [{"symbol","strike","expiration"}]} (calls)
  "quotes":       {OCC: {"bid","ask"}}
  "sleeve_state": {SYM: {"position": {...} | None}}
  "fear_ok", "earnings", "earnings_fresh": as the equity sleeve
Bars (arg): daily dicts ascending.
"""

from core.sleeve import BaseSleeve, Intent, SleeveConfig

RISK_FRACTION = 0.001  # 0.10% — smaller due to variance
MAX_POSITIONS = 5
DTE_MIN, DTE_MAX = 0, 7
OTM_PCT = 0.02
PROFIT_TAKE_MULT = 1.75    # +75% premium profit-take
EXIT_DTE = 1               # close at latest with 1 DTE
THESIS_BREAK_PCT = 0.03    # underlying -3% from entry
QUOTE_GATE_FRAC = 0.15     # select_long_call's spread gate

RSI_PERIOD = 14
RSI_OVERSOLD = 20
VOL_CLIMAX_MULT = 2.0
VOL_LOOKBACK = 20
EMA200_PERIOD = 200
EMA_TOLERANCE = 0.02
ATR_PCT_FILTER = 0.05
ATR_PERIOD = 14
BLACKOUT_DAYS_BEFORE = 3

CONFIG = SleeveConfig(
    sleeve_id="capitulation_options", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


# --- signal helpers: verbatim mirrors of capitulation_sleeve.py ------
def calc_rsi_1h(closes, period=RSI_PERIOD):
    n = len(closes)
    if n < period + 1:
        return [None] * n
    gains, losses = [], []
    for i in range(1, n):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    rsi = [None] * period
    for i in range(period, n):
        if i > period:
            avg_g = (avg_g * (period - 1) + gains[i - 1]) / period
            avg_l = (avg_l * (period - 1) + losses[i - 1]) / period
        if avg_l == 0:
            rsi.append(100.0 if avg_g > 0 else 50.0)
        else:
            rsi.append(100.0 - (100.0 / (1.0 + avg_g / avg_l)))
    return rsi


def calc_atr_pct(daily_bars, period=ATR_PERIOD):
    if len(daily_bars) < period + 1:
        return None
    trs = []
    for i in range(1, len(daily_bars)):
        h, l, pc = (daily_bars[i]["h"], daily_bars[i]["l"],
                    daily_bars[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    close = daily_bars[-1]["c"]
    return atr / close if close > 0 else None


def calc_ema200(daily_bars):
    if len(daily_bars) < EMA200_PERIOD:
        return None
    closes = [b["c"] for b in daily_bars]
    ema = sum(closes[:EMA200_PERIOD]) / EMA200_PERIOD
    k = 2.0 / (EMA200_PERIOD + 1)
    for c in closes[EMA200_PERIOD:]:
        ema = c * k + ema * (1 - k)
    return ema


def detect_capitulation(h1_bars, daily_bars):
    """Parts 1-4 verbatim (part 5 = atr filter, checked by caller)."""
    if len(h1_bars) < VOL_LOOKBACK + RSI_PERIOD + 2:
        return None
    if len(daily_bars) < EMA200_PERIOD:
        return None
    closes = [b["c"] for b in h1_bars]
    rsi = calc_rsi_1h(closes)
    last, prev = h1_bars[-1], h1_bars[-2]
    rsi_last, rsi_prev = rsi[-1], rsi[-2]
    if rsi_last is None or rsi_prev is None:
        return None
    if not (last["c"] > last["o"]):
        return None
    if not (rsi_last > rsi_prev):
        return None
    if not (rsi_prev < RSI_OVERSOLD):
        return None
    vols = [b.get("v") or 0 for b in h1_bars[-(VOL_LOOKBACK + 2):-2]]
    avg_vol = sum(vols) / len(vols) if vols else 0
    if avg_vol <= 0 or prev.get("v", 0) <= VOL_CLIMAX_MULT * avg_vol:
        return None
    ema200 = calc_ema200(daily_bars)
    if ema200 is None or ema200 <= 0:
        return None
    if abs(prev["l"] - ema200) / ema200 > EMA_TOLERANCE:
        return None
    return {"rsi": round(rsi_prev, 1), "rsi_now": round(rsi_last, 1),
            "climax_vol_mult": round(prev["v"] / avg_vol, 2),
            "ema200": round(ema200, 2), "climax_low": round(prev["l"], 2)}


# --- options selection (pure, over a core-supplied chain snapshot) --
ENH_DTE_MIN = 2  # ENH 2026-10-24: EXIT_DTE (1) + 1 — skip 0-1 DTE


def select_long_call(chain, quotes, spot, session_iso, min_dte=None):
    """desk/options_exec.select_long_call as a pure function: nearest
    expiry inside DTE_MIN..DTE_MAX (vs context.session), first strike
    >= spot*(1+OTM_PCT), ask > 0, (ask-bid)/mid <= 15% when bid > 0."""
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
        if (DTE_MIN if min_dte is None else min_dte) <= dte <= DTE_MAX:
            by_exp.setdefault(exp, []).append(
                {"occ": c["symbol"], "strike": strike, "expiry": exp})
    if not by_exp:
        return None
    expiry = sorted(by_exp.keys())[0]
    target = spot * (1 + OTM_PCT)
    cands = sorted(by_exp[expiry], key=lambda c: c["strike"])
    sel = next((c for c in cands if c["strike"] >= target), None)
    if sel is None:
        return None
    q = (quotes or {}).get(sel["occ"]) or {}
    try:
        ask, bid = float(q.get("ask") or 0), float(q.get("bid") or 0)
    except (TypeError, ValueError):
        return None
    if ask <= 0:
        return None
    if bid > 0 and (ask - bid) / ((ask + bid) / 2) > QUOTE_GATE_FRAC:
        return None
    return dict(sel, ask=ask, bid=bid,
                mid=round((ask + bid) / 2, 2) if bid > 0 else ask)


def qty_for_risk(ask, equity):
    """Contracts so premium paid <= RISK_FRACTION of equity. Verbatim."""
    if not equity or equity <= 0 or not ask or ask <= 0:
        return 0
    return max(0, int((equity * RISK_FRACTION) // (ask * 100)))


def exit_due(pos, dte, mid, last_stock_close):
    """Verbatim old exit_due (DTE computed vs context.session here)."""
    entry_px = pos.get("entry_premium") or 0
    if mid is not None and entry_px > 0:
        if mid >= PROFIT_TAKE_MULT * entry_px:
            return "profit_take_75pct"
    if dte is not None and dte <= EXIT_DTE:
        return "dte_time_stop"
    # Core-recorded positions (core/dispatch derived fields) carry the
    # entry stock price as entry_spot (from the intent's price_hint),
    # never entry_stock_px — reading only entry_stock_px left the
    # thesis break silently dead on every desk-originated fill.
    entry_stock = pos.get("entry_stock_px") or pos.get("entry_spot") or 0
    if last_stock_close and entry_stock > 0:
        if last_stock_close <= entry_stock * (1 - THESIS_BREAK_PCT):
            return "thesis_broken_-3pct"
    return None


def _earnings_veto(sym, session_iso, earnings, fresh):
    if not fresh:
        return "stale_calendar"
    if sym not in earnings:
        return "unknown_date"
    ed = earnings[sym]
    if ed is None:
        return None
    try:
        from datetime import date as _date
        delta = (_date.fromisoformat(str(ed)[:10])
                 - _date.fromisoformat(session_iso)).days
    except ValueError:
        return "unknown_date"
    return "blackout_window" if 0 <= delta <= BLACKOUT_DAYS_BEFORE else None


def _dte(expiry, session_iso):
    try:
        from datetime import date as _date
        return (_date.fromisoformat(str(expiry)[:10])
                - _date.fromisoformat(session_iso)).days
    except (ValueError, TypeError):
        return None


class CapitulationOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        h1map = extra.get("bars_1h") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        earnings = extra.get("earnings") or {}
        earnings_fresh = bool(extra.get("earnings_fresh"))
        fear_ok = extra.get("fear_ok", False)  # LC-1: fail-closed,
        # as the equity sleeve (see sleeves/capitulation.py)
        equity = float(context.equity or 0.0)
        universe = extra.get("universe") or sorted(bars.keys())
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            daily = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                q = quotes.get(pos.get("occ")) or {}
                try:
                    mid = (float(q["bid"]) + float(q["ask"])) / 2 \
                        if q.get("bid") and q.get("ask") else None
                except (TypeError, ValueError):
                    mid = None
                last_close = float(daily[-1]["c"]) if daily else None
                reason = exit_due(pos, _dte(pos.get("expiry"), context.session),
                                  mid, last_close)
                if reason:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        # READINESS-20261022 F-A2: missing
                        # entry_premium -> price_hint=None, never 0.0
                        price_hint=(round(float(pos["entry_premium"]), 2)
                                    if pos.get("entry_premium") else None),
                        reason="capitulation_options exit: %s occ=%s"
                               % (reason, pos.get("occ"))))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            h1 = h1map.get(sym) or []
            if len(daily) < EMA200_PERIOD or not h1:
                continue
            atr_pct = calc_atr_pct(daily)
            if atr_pct is None or atr_pct <= ATR_PCT_FILTER:
                continue
            sig = detect_capitulation(h1, daily)
            if not sig:
                continue
            if not fear_ok:
                continue  # DEFER, as the equity sleeve
            if _earnings_veto(sym, context.session, earnings, earnings_fresh):
                continue
            spot = float(h1[-1]["c"])
            _eff_min = ENH_DTE_MIN if _capopt_enh_enabled(extra) else DTE_MIN
            _shadow = select_long_call(chains.get(sym), quotes, spot,
                                       context.session, min_dte=DTE_MIN)
            call = select_long_call(chains.get(sym), quotes, spot,
                                    context.session, min_dte=_eff_min)
            _capopt_paired(extra, {
                "exp_id": EXP_ID_CAPOPT, "symbol": sym,
                "control_expiry": (_shadow or {}).get("expiry"),
                "treatment_expiry": (call or {}).get("expiry")})
            if not call:
                continue
            qty = qty_for_risk(call["ask"], equity)
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(spot, 2),
                reason="capitulation_options long_call: occ=%s strike=%.2f "
                       "expiry=%s ask=%.2f rsi=%.1f vol_mult=%.2f structure="
                       "long_call dte_window=%d-%d otm_pct=%.2f"
                       % (call["occ"], call["strike"], call["expiry"],
                          call["ask"], sig["rsi"], sig["climax_vol_mult"],
                          _eff_min, DTE_MAX, OTM_PCT)))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return CapitulationOptions().signal(bars, slice_state, context)


# --- ENH 2026-10-24 (Edge IMPROVE-capitulation_options, Group A) ------
# Select the nearest expiry with DTE >= 2 (skip 0-1 DTE, which are
# born due under the sleeve's EXIT_DTE=1 law). Switch:
# extra["capitulation_options_improve"] {"dte_min_2": bool}, default
# ON; OFF restores DTE_MIN=0 selection exactly. Paired records go to
# extra["capitulation_options_exp_journal"]["records"] when served.
EXP_ID_CAPOPT = "ENH-CAPOPT-20261024"


def _capopt_enh_enabled(extra):
    ov = (extra or {}).get("capitulation_options_improve")
    if isinstance(ov, dict) and "dte_min_2" in ov:
        return bool(ov["dte_min_2"])
    return True


def _capopt_paired(extra, record):
    j = (extra or {}).get("capitulation_options_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)
