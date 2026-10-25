"""Fear Premium — put credit spreads on red days — lean port (Wave B).

EXTRACTED from the old desk's fear_premium_sleeve.py (SPEC adapted
from Matt Giannino's guide): after a >=5% red day with RSI(14) < 50
on a high-beta name, sell a ~30-DTE put credit spread. Universe =
top-10 by 60d beta vs QQQ (re-ranked weekly) + SOXL/TQQQ always —
the ranking is a pure function here; the weekly cache is core state.
Leg selection and quote validation are the old file's PURE functions
(select_spread_legs / validate_spread_quotes) verbatim in behavior,
including the 2026-10-11 determinism fixes. See ports/fear_premium.md.

Spread: short put nearest 7% below the red-day close, long one width
(~10% of underlying, snapped to the strike grid) lower, same expiry,
25-35 DTE (legs accepted within +-4 days by the old selector). Gates:
two-sided quotes, per-leg (ask-bid)/mid <= 10% (Decision #103),
credit (short bid - long ask) >= 3% of capital at risk. Risk 0.5%/
spread, sleeve notional cap 25%, max 5.
Exits: 50% of max profit, 8-day time exit, 21-DTE floor.

Inputs via context.extra:
  "chains":  {SYM: [{"symbol","strike","expiration"}]} (puts)
  "quotes":  {OCC: {"bid","ask"}}
  "sleeve_state": {SYM: {"position": {...} | None}}
  "universe": ranked universe override (default: bars keys)
Bars (arg): daily dicts ascending; QQQ must be present for beta.

ENH (IMPROVE-fear_premium, Edge program 2026-10-24): the 8-session
time exit is conditioned on profitability — at 8 sessions it fires
only when the spread's conservative close cost is at or above the
entry credit (flat-to-losing); a decayed winner lives under the
50%-of-credit target and the 21-DTE floor alone (re-tested every
pass). Switched by context.extra["fear_premium_improve"]
["time_exit_profit_gate"] (default ON; OFF restores the pre-change
rule exactly). Divergent decisions record a paired control/treatment
record on self.last_evaluation["enhance_exp"].
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

UNIVERSE_BETA_COUNT = 10
ALWAYS_INCLUDE = ("SOXL", "TQQQ")
BETA_LOOKBACK_DAYS = 60
BETA_RERANK_DAYS = 7
RED_DAY_THRESHOLD = -0.05
RSI_PERIOD = 14
RSI_CEILING = 50.0
DTE_MIN, DTE_MAX = 25, 35
DTE_FLOOR = 21
SHORT_OTM_PCT = 0.07
WIDTH_PCT = 0.10
MIN_CREDIT_FRAC = 0.03
SPREAD_GATE_FRAC = 0.10   # Decision #103
RISK_FRACTION = 0.005
MAX_POSITIONS = 5
SLEEVE_NOTIONAL_CAP = 0.25
PROFIT_TARGET_FRAC = 0.50
TIME_EXIT_DAYS = 8

CONFIG = SleeveConfig(
    sleeve_id="fear_premium", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    out = []
    for b in bars or []:
        try:
            out.append(datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                              tz=timezone.utc).date().isoformat())
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            continue  # a bar without a usable timestamp has no session date
    return out


def wilder_rsi(closes, period=RSI_PERIOD):
    """Wilder RSI (SMA seed, then smoothing). Verbatim; None if short."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        chg = closes[i] - closes[i - 1]
        gains.append(max(chg, 0.0))
        losses.append(max(-chg, 0.0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
    if avg_l == 0:
        return 100.0
    return 100.0 - (100.0 / (1.0 + avg_g / avg_l))


def compute_beta(sym_bars, bench_bars, lookback=BETA_LOOKBACK_DAYS):
    """60d beta vs benchmark from daily closes. Verbatim incl. the
    2026-10-11 aligned-pairs fix. None on bad data."""
    try:
        sc = [float(b["c"]) for b in sym_bars[-lookback - 1:]]
        bc = [float(b["c"]) for b in bench_bars[-lookback - 1:]]
    except (KeyError, TypeError, ValueError):
        return None
    n = min(len(sc), len(bc))
    if n < lookback:
        return None
    sc, bc = sc[-n:], bc[-n:]
    pairs = [(sc[i] / sc[i - 1] - 1, bc[i] / bc[i - 1] - 1)
             for i in range(1, n) if sc[i - 1] and bc[i - 1]]
    if len(pairs) < 20:
        return None
    sr = [p[0] for p in pairs]
    br = [p[1] for p in pairs]
    m = len(pairs)
    mb = sum(br) / m
    var_b = sum((x - mb) ** 2 for x in br) / m
    if var_b <= 0:
        return None
    ms = sum(sr) / m
    cov = sum((s - ms) * (b - mb) for s, b in zip(sr, br)) / m
    return cov / var_b


def rank_universe(bars, bench_sym="QQQ"):
    """Top-N beta names + ALWAYS_INCLUDE (deduped, ordered). Pure
    form of the old rank_universe minus its weekly cache (core state)."""
    bench = bars.get(bench_sym) or []
    scored = []
    for sym, bl in bars.items():
        if sym in ALWAYS_INCLUDE or sym == bench_sym:
            continue
        beta = compute_beta(bl, bench)
        if beta is not None:
            scored.append((beta, sym))
    scored.sort(reverse=True)
    ranked = [s for _, s in scored[:UNIVERSE_BETA_COUNT]]
    return list(dict.fromkeys(list(ALWAYS_INCLUDE) + ranked))


def detect_red_day(bars):
    """(is_signal, red_day_pct, rsi). Last completed daily bar. Verbatim."""
    if len(bars) < RSI_PERIOD + 2:
        return False, None, None
    closes = [float(b["c"]) for b in bars]
    last, prev = closes[-1], closes[-2]
    if prev <= 0:
        return False, None, None
    day_pct = last / prev - 1.0
    rsi = wilder_rsi(closes)
    if rsi is None:
        return False, day_pct, None
    return (day_pct <= RED_DAY_THRESHOLD and rsi < RSI_CEILING), day_pct, rsi


def select_spread_legs(ref_px, chain, session_iso):
    """Pure chain math, verbatim old select_spread_legs (its wall-clock
    DTE read becomes context.session): short strike nearest 7% below
    ref_px, width = max(grid, round(ref*10%/grid)*grid), long nearest
    short-width, same-expiry vertical only, deterministic tie-breaks,
    DTE accepted within (DTE_MIN-4)..(DTE_MAX+4)."""
    from datetime import date as _date
    puts = []
    for c in chain or []:
        try:
            strike = float(c["strike"])
            occ = c["symbol"]
            exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
            puts.append({"strike": strike, "occ": occ, "exp": exp})
        except (KeyError, TypeError, ValueError):
            continue
    if len(puts) < 2:
        return None
    strikes = sorted({p["strike"] for p in puts})
    if len(strikes) < 2:
        return None
    grid = min(b - a for a, b in zip(strikes, strikes[1:]) if b > a)
    target_short = ref_px * (1 - SHORT_OTM_PCT)
    short_strike = min(strikes, key=lambda s: abs(s - target_short))
    width = max(grid, round(ref_px * WIDTH_PCT / grid) * grid)
    target_long = short_strike - width
    long_strike = min(strikes, key=lambda s: abs(s - target_long))
    if long_strike >= short_strike:
        return None
    short_c = min((p for p in puts if p["strike"] == short_strike),
                  key=lambda p: (p["exp"], p["occ"]))
    long_c = min((p for p in puts if p["strike"] == long_strike),
                 key=lambda p: (p["exp"], p["occ"]))
    if short_c["exp"] != long_c["exp"]:
        same = [p for p in puts if p["exp"] == short_c["exp"]
                and p["strike"] < short_strike]
        if not same:
            return None
        long_c = min(same, key=lambda p: (abs(p["strike"] - target_long),
                                          p["exp"], p["occ"]))
        long_strike = long_c["strike"]
    try:
        dte = (_date.fromisoformat(short_c["exp"])
               - _date.fromisoformat(session_iso)).days
    except ValueError:
        return None
    if not (DTE_MIN - 4 <= dte <= DTE_MAX + 4):
        return None
    return {"short_occ": short_c["occ"], "long_occ": long_c["occ"],
            "short_strike": short_strike, "long_strike": long_strike,
            "expiry": short_c["exp"], "dte": dte,
            "width_pts": short_strike - long_strike}


def validate_spread_quotes(legs, quotes):
    """Quote/economic gates, verbatim: two-sided both legs, per-leg
    frac <= 10%, credit = short bid - long ask >= 3% of capital at
    risk (capital = (width - credit) x 100)."""
    if not legs:
        return None
    q = quotes or {}
    sq, lq = q.get(legs["short_occ"], {}), q.get(legs["long_occ"], {})
    try:
        sb, sa = float(sq.get("bid") or 0), float(sq.get("ask") or 0)
        lb, la = float(lq.get("bid") or 0), float(lq.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if not (sb > 0 and sa >= sb and lb > 0 and la >= lb):
        return None
    for b, a in ((sb, sa), (lb, la)):
        mid = (b + a) / 2
        if mid <= 0 or (a - b) / mid > SPREAD_GATE_FRAC:
            return None
    credit = sb - la
    width_pts = legs.get("width_pts") or 0
    capital_at_risk = (width_pts - credit) * 100
    if capital_at_risk <= 0 or credit <= 0:
        return None
    if credit / (capital_at_risk / 100) < MIN_CREDIT_FRAC:
        return None
    return dict(legs, credit=round(credit, 2),
                capital_at_risk=round(capital_at_risk, 2),
                short_bid=sb, short_ask=sa, long_bid=lb, long_ask=la)


def pick_spread(ref_px, chain, quotes, session_iso):
    legs = select_spread_legs(ref_px, chain, session_iso)
    if not legs:
        return None
    return validate_spread_quotes(legs, quotes)


def size_contracts(equity, capital_at_risk, short_strike):
    """Contracts fitting 0.5% risk and the 25% notional cap. Verbatim."""
    if equity <= 0 or capital_at_risk <= 0:
        return 0
    n = math.floor((equity * RISK_FRACTION) / capital_at_risk)
    if short_strike > 0:
        n = min(n, math.floor((equity * SLEEVE_NOTIONAL_CAP)
                              / (short_strike * 100)))
    return max(0, int(n))


def spread_close_cost(quotes, spread):
    """Conservative cost to close: buy short at ask, sell long at bid.
    AUDIT3-C (2026-10-16): a long leg quoting bid 0 is a WORTHLESS
    leg, not missing data — it is the winning credit spread's
    normal state near expiry, and the pre-cure `lb <= 0` guard
    made the close cost uncomputable exactly then, killing the
    profit/stop exits. Missing quotes (occ absent) or an
    unpriceable short leg still fail closed."""
    q = quotes or {}
    if not spread or not spread.get("short_occ") or not spread.get("long_occ"):
        return None
    if spread["short_occ"] not in q or spread["long_occ"] not in q:
        return None
    sq, lq = q.get(spread["short_occ"], {}), q.get(spread["long_occ"], {})
    try:
        sa, lb = float(sq.get("ask") or 0), float(lq.get("bid") or 0)
    except (TypeError, ValueError):
        return None
    if sa <= 0 or lb < 0:
        return None
    return sa - lb


# ------------------------------------------------------------ ENH experiment
EXP_ID = "ENH-FEAR-PREMIUM-20261024"

def time_exit_profit_gate_enabled(extra):
    ov = (extra or {}).get("fear_premium_improve")
    if isinstance(ov, dict) and "time_exit_profit_gate" in ov:
        return bool(ov["time_exit_profit_gate"])
    return True

def time_exit_fires(close_cost, entry_credit, gate_on=True):
    """8-session time-exit decision once due: with the ENH gate ON a
    profitable spread (close cost below entry credit) does not fire;
    an unpriceable spread (close_cost None) keeps the control rule."""
    if gate_on and close_cost is not None and entry_credit \
            and float(entry_credit) > 0 and close_cost < entry_credit:
        return False
    return True

def exit_due(pos, session_iso, dates, close_cost, time_gate=True):
    """Verbatim old order: 50% profit, 8-session time exit (old counted
    calendar days from entry_ts; sessions on the bar calendar are the
    contract's equivalent — named in the port report), 21-DTE floor.
    ENH: with time_gate ON, the time exit additionally requires
    time_exit_fires(close_cost, entry_credit)."""
    if close_cost is not None and (pos.get("entry_credit") or 0) > 0:
        if pos["entry_credit"] - close_cost \
                >= PROFIT_TARGET_FRAC * pos["entry_credit"]:
            return "profit_target_50pct"
    if pos.get("entry_date") and pos["entry_date"] in dates:
        if len(dates) - 1 - dates.index(pos["entry_date"]) >= TIME_EXIT_DAYS \
                and time_exit_fires(close_cost, pos.get("entry_credit"),
                                    gate_on=time_gate):
            return "time_exit_8d"
    try:
        from datetime import date as _date
        # AUDIT3-C-01 (2026-10-16): core records carry expiry at
        # the TOP level of the position (the spread sub-dict is
        # {short_occ, long_occ} only) — the pre-cure read of
        # pos["spread"]["expiry"] raised KeyError on every pass,
        # swallowed by the except below, so the 21-DTE floor
        # NEVER fired (live proof: the held IREN record's shape).
        exp = pos.get("expiry") or (pos.get("spread") or {}).get("expiry")
        dte = (_date.fromisoformat(str(exp)[:10])
               - _date.fromisoformat(session_iso)).days
        if dte <= DTE_FLOOR:
            return "dte_floor_21"
    except (ValueError, TypeError, KeyError, AttributeError):
        pass
    return None


class FearPremium(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        equity = float(context.equity or 0.0)
        gate_on = time_exit_profit_gate_enabled(extra)
        exp_records = []
        universe = extra.get("universe") or rank_universe(bars)
        uni_set = set(universe)
        intents = []
        # Exits are never gated on the entry universe: a held name that
        # rotates out of the beta ranking still gets its exit rules
        # evaluated (the ranking re-ranks weekly; a position the loop
        # never visits can never exit). Entries stay universe-only.
        open_n = sum(1 for s in state if (state.get(s) or {}).get("position"))
        syms = list(universe) + [s for s in sorted(state) if s not in uni_set]
        for sym in syms:
            bl = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                spread = pos.get("spread") or {}
                cost = spread_close_cost(quotes, spread)
                reason_c = exit_due(pos, context.session, _dates(bl), cost,
                                    time_gate=False)
                reason = exit_due(pos, context.session, _dates(bl), cost,
                                  time_gate=gate_on)
                if reason_c != reason:
                    exp_records.append({
                        "symbol": sym, "close_cost": cost,
                        "entry_credit": pos.get("entry_credit"),
                        "control_exit": reason_c,
                        "treatment_exit": reason, "switch_on": gate_on})
                if reason:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bl[-1]["c"]), 2) if bl else None,
                        reason="fear_premium exit: %s close_cost=%s legs=%s/%s"
                               % (reason, cost, spread.get("short_occ"),
                                  spread.get("long_occ"))))
                continue
            if sym not in uni_set:
                continue  # held-name visit was for exits only; no entries
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            is_sig, day_pct, rsi = detect_red_day(bl)
            if not is_sig:
                continue
            ref_px = float(bl[-1]["c"])
            sp = pick_spread(ref_px, chains.get(sym), quotes, context.session)
            if not sp:
                continue
            qty = size_contracts(equity, sp["capital_at_risk"], sp["short_strike"])
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(ref_px, 2),
                reason="fear_premium put_credit_spread: short=%s@%.2f "
                       "long=%s@%.2f expiry=%s dte=%d width=%.2f credit=%.2f "
                       "day_pct=%.4f rsi=%.1f structure=put_credit_spread "
                       "dte_window=%d-%d short_otm_pct=%.2f width_pct=%.2f"
                       % (sp["short_occ"], sp["short_strike"], sp["long_occ"],
                          sp["long_strike"], sp["expiry"], sp["dte"],
                          sp["width_pts"], sp["credit"], day_pct, rsi,
                          DTE_MIN, DTE_MAX, SHORT_OTM_PCT, WIDTH_PCT)))
            open_n += 1
        if exp_records:
            self.last_evaluation = {"enhance_exp": {
                "exp_id": EXP_ID, "switch_on": gate_on,
                "records": exp_records}}
        return intents


def signal(bars, slice_state, context):
    return FearPremium().signal(bars, slice_state, context)
