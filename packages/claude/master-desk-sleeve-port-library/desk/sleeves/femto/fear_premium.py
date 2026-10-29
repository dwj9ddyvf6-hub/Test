"""Fear Premium — put credit spreads on red days — lean port (Wave B).

master-desk: the old desk's fear_premium_sleeve.py (SPEC adapted from Matt Giannino's guide) restored on the
engine: after a >=5% red day with RSI(14) < 50 on a high-beta name, sell a ~30-DTE put credit spread for >= 3%
on the capital at risk; out at 50% of max profit, after 8 days, or at 21 DTE.

  universe . SOXL and TQQQ always, then the basket's top 10 by 60-day beta vs QQQ (cov / var of daily returns,
             >= 20 aligned pairs), re-ranked when the ranking is 7 days old (kept in meta between ranks).
  signal ... the last completed daily bar down >= 5% with Wilder RSI(14) < 50; no earnings within 3 days and a
             confirmed calendar entry, on a calendar refreshed within 8 days (SOXL / TQQQ / QQQ have none) — the
             sleeve's own signal step 3, fail closed.
  spread ... puts 25-35 DTE: short strike nearest 7% under the red-day close, long nearest one width (10% of the
             price snapped to the strike grid) lower, same expiry; both legs two-sided with (ask - bid) / mid <=
             10% (Decision #103); credit = short bid - long ask >= 3% of the capital at risk ((width - credit) x
             100); floor(0.5% of equity / risk) spreads, at most 25% of equity in short-strike notional; at most
             5 spreads held or in flight; one spread, both legs at once, at that natural credit.
  exits .... (never gated, every pass) credit - (short ask - long bid) >= 50% of the credit received; 8 days
             since the fill; <= 21 days to expiry; both legs closed at their mids (the package at the mid net).

Gone under the cutover doctrine: the risk gate (kill switch), the Decision #75 chart gate (staging, its 24h
pending TTL, the release replay) and the 150% desk cap; the cross-sleeve check was a log line. Named
divergences: one atomic spread order at the natural credit (the old sent two single-leg orders, short first, at
the short bid and the long ask — the same prices, without its legging risk) and one at the mid net to close (the
old: each leg at its own mid); passes hourly at :55 in the session (the old cron ran hourly around the clock);
the chain snapshot carries the legs' quotes (the old made a separate latest-quote call).

Inputs via context.extra:
  "chains"        {SYM: put rows 25-35 DTE {"symbol","strike","expiration","bid","ask",...}} (fetched on demand)
  "option_quotes" {OCC: {"bid","ask"}} — the held legs
  "earnings"      {SYM: "YYYY-MM-DD" | None}; "earnings_fresh": bool
  "basket"        the basket's names in file order (the beta ranking's candidates)
  "meta"          {"universe": {"ranked", "as_of", "betas"}}
  "sleeve_state"  {SYM: {"position": spread group | None, "pending_entry": ...}}
Bars (arg): daily bars (90 completed sessions) for the basket, SOXL, TQQQ and QQQ."""
import math
from datetime import date, datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

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
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


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
        frac = round((a - b) / mid, 4) if mid > 0 else None       # the old rounds the leg fraction first
        if frac is None or frac > SPREAD_GATE_FRAC:
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
    """Conservative cost to close: buy short at ask, sell long at bid."""
    q = quotes or {}
    sq, lq = q.get(spread["short_occ"], {}), q.get(spread["long_occ"], {})
    try:
        sa, lb = float(sq.get("ask") or 0), float(lq.get("bid") or 0)
    except (TypeError, ValueError):
        return None
    if sa <= 0 or lb <= 0:
        return None
    return sa - lb


def exit_due(pos, session_iso, dates, close_cost):
    """Verbatim old order: 50% profit, 8-session time exit (old counted
    calendar days from entry_ts; sessions on the bar calendar are the
    contract's equivalent — named in the port report), 21-DTE floor."""
    if close_cost is not None and pos["entry_credit"] > 0:
        if pos["entry_credit"] - close_cost \
                >= PROFIT_TARGET_FRAC * pos["entry_credit"]:
            return "profit_target_50pct"
    if pos.get("entry_date") and pos["entry_date"] in dates:
        if len(dates) - 1 - dates.index(pos["entry_date"]) >= TIME_EXIT_DAYS:
            return "time_exit_8d"
    try:
        from datetime import date as _date
        dte = (_date.fromisoformat(str(pos["spread"]["expiry"])[:10])
               - _date.fromisoformat(session_iso)).days
        if dte <= DTE_FLOOR:
            return "dte_floor_21"
    except (ValueError, TypeError, KeyError):
        pass
    return None


NO_EARNINGS_ETFS = {"SOXL", "TQQQ", "QQQ"}
BLACKOUT_DAYS = 3
EXIT_WINDOW_S = 3600


def earnings_ok(sym, calendar, fresh, today):
    """the old earnings_ok: ETFs by construction clear; else a fresh calendar, a confirmed entry, and no report
    today or in the next 3 days. Fail closed."""
    s = (sym or "").upper()
    if s in NO_EARNINGS_ETFS:
        return True
    if not fresh or s not in (calendar or {}):
        return False
    d = calendar[s]
    if d is None:
        return True
    try:
        delta = (date.fromisoformat(str(d)[:10]) - date.fromisoformat(today)).days
    except ValueError:
        return True
    return not (0 <= delta <= BLACKOUT_DAYS)


def ranked_universe(meta, bars, basket, now):
    """(universe, new_rank | None): the cached ranking while under 7 days old, else a fresh one (the old
    rank_universe: no QQQ bars -> the last ranking)."""
    uni = meta.get("universe") or {}
    if uni.get("ranked") and uni.get("as_of") is not None and int((float(now) - float(uni["as_of"])) // 86400) \
            < BETA_RERANK_DAYS:
        return list(uni["ranked"]), None
    bench = bars.get("QQQ") or []
    if not bench:
        return list(uni.get("ranked") or []), None
    scored = []
    for sym in basket or []:
        if sym in ALWAYS_INCLUDE or sym == "QQQ":
            continue
        bl = bars.get(sym)
        if not bl:
            continue
        beta = compute_beta(bl, bench)
        if beta is not None:
            scored.append((beta, sym))
    scored.sort(reverse=True)
    ranked = [s for _, s in scored[:UNIVERSE_BETA_COUNT]]
    universe = list(dict.fromkeys(list(ALWAYS_INCLUDE) + ranked))
    return universe, {"ranked": universe, "as_of": float(now),
                      "betas": {s: round(b, 3) for b, s in scored[:UNIVERSE_BETA_COUNT]}}


def held_spread(pos):
    """the spread's short / long OCC from its group legs, its credit received and its open time."""
    legs = pos.get("legs") or {}
    short = [o for o, q in legs.items() if float(q) < 0]
    long = [o for o, q in legs.items() if float(q) > 0]
    if len(short) != 1 or len(long) != 1:
        return None
    return {"short_occ": short[0], "long_occ": long[0], "entry_credit": -float(pos.get("net_entry") or 0.0),
            "opened_at": pos.get("opened_at"), "expiry": pos.get("expiry")}


def exit_reason(spread, now, session_iso, close_cost):
    """the old exit_due: 50% of max profit, 8 days since the fill (timestamp days), the 21-DTE floor."""
    if close_cost is not None and spread["entry_credit"] > 0:
        if spread["entry_credit"] - close_cost >= PROFIT_TARGET_FRAC * spread["entry_credit"]:
            return "profit_target_50pct"
    if spread.get("opened_at") is not None and int((float(now) - float(spread["opened_at"])) // 86400) \
            >= TIME_EXIT_DAYS:
        return "time_exit_8d"
    try:
        exp = spread.get("expiry") or _occ_expiry(spread["short_occ"])
        if (date.fromisoformat(str(exp)[:10]) - date.fromisoformat(session_iso)).days <= DTE_FLOOR:
            return "dte_floor_21"
    except (ValueError, TypeError):
        pass
    return None


def _occ_expiry(occ):
    t = str(occ)[-15:]
    return "20%s-%s-%s" % (t[0:2], t[2:4], t[4:6])


def _mid(q):
    try:
        m = (float(q["bid"]) + float(q["ask"])) / 2
    except (KeyError, TypeError, ValueError):
        return None
    return m if m > 0 else None


def decide(bars, context):
    """(intents, new_rank): exits first, then the universe's entries in order, at most MAX_POSITIONS slots."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    meta = extra.get("meta") or {}
    oq = extra.get("option_quotes") or {}
    chains = extra.get("chains") or {}
    equity = float(context.equity or 0.0)
    now = float(context.now)
    universe, new_rank = ranked_universe(meta, bars, extra.get("basket"), now)
    intents = []
    slots = 0
    for sym, st in state.items():
        pos = (st or {}).get("position")
        if (st or {}).get("pending_entry") and not pos:
            slots += 1
        if not pos:
            continue
        sp = held_spread(pos)
        if sp is None:
            continue
        slots += 1
        if pos.get("exit_submitted"):
            continue
        cost = spread_close_cost(oq, sp)
        why = exit_reason(sp, now, context.session, cost)
        if not why:
            continue
        ms, ml = _mid(oq.get(sp["short_occ"]) or {}), _mid(oq.get(sp["long_occ"]) or {})
        if ms is None or ml is None:
            continue                                  # the old close_spread: no two-sided quotes, no close
        net = max(round(ms - ml, 2), 0.01)
        intents.append(Intent(
            "exit", sym, qty_hint=int(abs(float(pos.get("qty") or 0))) or None, net_price=net,
            order={"window_s": EXIT_WINDOW_S}, signal_key="%s:%s:fp-exit" % (sym, context.session),
            reason="fear_premium exit: %s close_cost=%s credit=%.2f legs=%s/%s mid_net=%.2f"
                   % (why, None if cost is None else round(cost, 2), sp["entry_credit"], sp["short_occ"],
                      sp["long_occ"], net)))
    if equity <= 0:
        return intents, new_rank
    today = context.session
    for sym in universe:
        st = state.get(sym) or {}
        if st.get("position") or st.get("pending_entry"):
            continue
        if slots >= MAX_POSITIONS:
            break
        bl = bars.get(sym) or []
        is_sig, day_pct, rsi = detect_red_day(bl)
        if not is_sig:
            continue
        if not earnings_ok(sym, extra.get("earnings"), extra.get("earnings_fresh"), today):
            continue
        ref_px = float(bl[-1]["c"])
        chain = chains.get(sym)
        if not chain:
            continue
        legs = select_spread_legs(ref_px, chain, today)
        if not legs:
            continue
        q = {r["symbol"]: r for r in chain if r.get("symbol") in (legs["short_occ"], legs["long_occ"])}
        sp = validate_spread_quotes(legs, q)
        if not sp:
            continue
        n = size_contracts(equity, sp["capital_at_risk"], sp["short_strike"])
        if n <= 0:
            continue
        intents.append(Intent(
            "enter", sym, qty_hint=n, asset="mleg",
            legs=({"symbol": sp["short_occ"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},
                  {"symbol": sp["long_occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"}),
            net_price=-sp["credit"], order={"window_s": EXIT_WINDOW_S},
            signal_key="%s:%s:fear-premium" % (sym, today),
            position_meta={k: sp[k] for k in ("short_occ", "long_occ", "short_strike", "long_strike", "expiry",
                                              "width_pts", "capital_at_risk")} |
                          {"credit_nat": sp["credit"], "day_pct": round(day_pct, 4), "rsi": round(rsi, 1),
                           "ref_px": round(ref_px, 2)},
            reason="fear_premium put credit spread: short %s @%.2f long %s @%.2f expiry %s dte %d width %.2f "
                   "credit %.2f risk %.2f x%d; red day %.2f%% rsi %.1f"
                   % (sp["short_occ"], sp["short_strike"], sp["long_occ"], sp["long_strike"], sp["expiry"],
                      sp["dte"], sp["width_pts"], sp["credit"], sp["capital_at_risk"], n, day_pct * 100, rsi)))
        slots += 1
    return intents, new_rank


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_fp_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:            # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_fp_pass"] = memo
    return memo[1]


class FearPremium(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)[0])


def signal(bars, slice_state, context):
    return FearPremium().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    _intents, new_rank = _pass(bars, context)
    if new_rank is not None:
        meta["universe"] = new_rank
    return meta
