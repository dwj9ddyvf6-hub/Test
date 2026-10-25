"""Iron Condor — lean-desk port (Wave B).

EXTRACTED from the old desk's iron_condor_sleeve.py. The Black-Scholes
machinery (price / delta / bisection IV), the TRUE IV-rank formula
(Decision #97), the delta-based leg selection from build_condor, the
quote gates and the exit rules are verbatim in behavior; chain/quote
fetching becomes pure selection over snapshots the core Data door
provides. See ports/iron_condor.md.

Entry: IV rank > 50 (TRUE rank vs the symbol's OWN stored IV history,
window 252; < 60 stored observations = cold start, entries pause
fail-closed), no earnings within 45 days (core-supplied earnings
distance), VIX <= 35 (extra["vix"]), 30-45 DTE, 16-delta shorts /
5-delta wings on both sides, same expiry both sides (fail closed on
mismatch), per-leg (ask-bid)/mid <= 10%, positive net credit.
Risk 1% max loss per condor (max loss = WIDER wing - credit), max 3
concurrent, max 25 contracts per condor.
Exits: 50% of max profit, 2x premium stop, 7-DTE time stop, 21-day
max hold.

DECISIONS #85/#96 EXEMPTION — CARRIED AS CONFIG: an iron condor is a
net-credit premium sale, not a buy; entries are EXEMPT from the
Decision #75 red-day gate and chart-gate staging (confirmed again by
Decision #118, 2026-10-14). The exemption is recorded on the config
block below (gate_exempt) and in every entry intent's reason; the
core Gate must honor it. The sleeve's own gates above are its filters.

Inputs via context.extra:
  "chains":       {SYM: {"put": [contracts], "call": [contracts]}}
                  contracts: {"symbol","strike","expiration"}
  "quotes":       {OCC: {"bid","ask"}}
  "iv":           {SYM: current IV (float)} (core Data product: BS
                  inversion of the nearest 30-45 DTE ATM call mid)
  "iv_history":   {SYM: [stored IV observations]} (core Ledger state)
  "earnings_in_days": {SYM: int | None} (None/absent = unknown =>
                  fail closed, as the old earnings_clear did)
  "vix":          float | None (absent => fail closed on the VIX gate)
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars (arg): daily dicts (spot = last close).
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

RISK_FREE = 0.04
WATCHLIST = ("ARQQ", "NBIS", "WYFI", "AEHR", "POET", "HIVE", "SNDK",
             "IREN", "CORZ", "ARM", "AXTI", "DGXX", "VELO")
IV_RANK_MIN = 50.0
DTE_MIN, DTE_MAX = 30, 45
SHORT_DELTA = 0.16
WING_DELTA = 0.05
PROFIT_TARGET_PCT = 0.50
STOP_MULT = 2.0
EXIT_DTE = 7
RISK_FRACTION = 0.01
MAX_POSITIONS = 3
EARNINGS_CLEAR_DAYS = 45
SPREAD_GATE_FRAC = 0.10   # SPEC level (MF-012 ruling)
VIX_MAX = 35.0
MAX_CONTRACTS_PER_CONDOR = 25
MAX_HOLD_DAYS = 21
IV_RANK_COLD_START_MIN = 60
IV_RANK_WINDOW = 252
# Decisions #85/#96 (confirmed #118): net-credit premium sale — exempt
# from Decision #75 red-day + chart-gate staging. Carried as config.
GATE_EXEMPT_DECISION75 = True

CONFIG = SleeveConfig(
    sleeve_id="iron_condor", cadence_s=300, universe=WATCHLIST,
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


# ------------------------------------------------- Black-Scholes (verbatim)
def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_price(S, K, T, r, sigma, kind):
    try:
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return None
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        if kind == "call":
            return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)
    except (ValueError, OverflowError):
        return None


def bs_delta(S, K, T, r, sigma, kind):
    try:
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return None
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        if kind == "call":
            return _norm_cdf(d1)
        return _norm_cdf(d1) - 1.0
    except (ValueError, OverflowError):
        return None


def implied_vol(market_px, S, K, T, r, kind):
    """Bisection IV inversion, verbatim incl. the 2026-10-11
    non-convergence fail-closed at the 500% cap."""
    if not market_px or market_px <= 0:
        return None
    lo, hi = 0.01, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        px = bs_price(S, K, T, r, mid, kind)
        if px is None:
            return None
        if abs(px - market_px) < 1e-4:
            return mid
        if px < market_px:
            lo = mid
        else:
            hi = mid
    hi_px = bs_price(S, K, T, r, hi, kind)
    if hi_px is None or hi_px < market_px:
        return None
    return (lo + hi) / 2


def compute_iv_rank(iv, history):
    """TRUE IV rank (Decision #97): (IV - low) / (high - low) x 100
    over the last IV_RANK_WINDOW stored observations. Verbatim."""
    window = list(history)[-IV_RANK_WINDOW:]
    if not window:
        return None
    lo, hi = min(window), max(window)
    if hi <= lo:
        return None
    return (float(iv) - lo) / (hi - lo) * 100.0


def iv_rank_ok(iv, history):
    """(rank|None): cold start (< 60 obs) returns None — entries pause."""
    if iv is None or not history or len(history) < IV_RANK_COLD_START_MIN:
        return None
    return compute_iv_rank(iv, history)


# ------------------------------------------------- condor construction
def build_condor(chain_by_kind, quotes, S, iv, session_iso):
    """Pure form of the old build_condor: nearest expiry in 30-45 DTE
    per side; short = strike whose |BS delta| is nearest 0.16; wing =
    nearest 0.05 beyond the short (below for puts, above for calls);
    expiry mismatch across sides fails closed; all four legs need
    two-sided quotes inside the 10% gate; net credit (short bids -
    long asks) must be > 0; max_loss uses the WIDER wing (P1 fix)."""
    from datetime import date as _date
    try:
        ref = _date.fromisoformat(session_iso)
    except ValueError:
        return None
    if not S or S <= 0 or not iv or iv <= 0:
        return None
    legs = {}
    for kind in ("put", "call"):
        contracts = [c for c in (chain_by_kind or {}).get(kind, [])
                     if c.get("tradable", True)]
        exps = set()
        rows = []
        for c in contracts:
            exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
            try:
                strike = float(c["strike"])
                dte = (_date.fromisoformat(exp) - ref).days
            except (TypeError, ValueError, KeyError):
                continue
            if DTE_MIN <= dte <= DTE_MAX:
                exps.add(exp)
                rows.append((exp, strike, c["symbol"]))
        if not exps:
            return None
        exp = sorted(exps)[0]
        dte = (_date.fromisoformat(exp) - ref).days
        T = max(dte, 1) / 365.0
        cands = []
        for e, K, occ in rows:
            if e != exp:
                continue
            d = bs_delta(S, K, T, RISK_FREE, iv, kind)
            if d is None:
                continue
            cands.append((abs(d), K, occ))
        if not cands:
            return None
        short = min(cands, key=lambda x: abs(x[0] - SHORT_DELTA))
        wings = [x for x in cands if (x[1] < short[1] if kind == "put"
                                      else x[1] > short[1])]
        if not wings:
            return None
        wing = min(wings, key=lambda x: abs(x[0] - WING_DELTA))
        legs[kind] = {"short": {"occ": short[2], "strike": short[1],
                                "delta": round(short[0], 3)},
                      "long": {"occ": wing[2], "strike": wing[1],
                               "delta": round(wing[0], 3)},
                      "expiry": exp, "dte": dte}
    if legs["put"]["expiry"] != legs["call"]["expiry"]:
        return None  # cross-leg expiry mismatch: fail closed (semfix)
    occs = [legs["put"]["short"]["occ"], legs["put"]["long"]["occ"],
            legs["call"]["short"]["occ"], legs["call"]["long"]["occ"]]
    mids = {}
    for occ in occs:
        q = (quotes or {}).get(occ, {})
        try:
            b, a = float(q.get("bid") or 0), float(q.get("ask") or 0)
        except (TypeError, ValueError):
            return None
        if b <= 0 or a < b:
            return None
        mid = (b + a) / 2
        if (a - b) / mid > SPREAD_GATE_FRAC:
            return None
        mids[occ] = {"bid": b, "ask": a, "mid": mid}
    credit = (mids[legs["put"]["short"]["occ"]]["bid"]
              - mids[legs["put"]["long"]["occ"]]["ask"]
              + mids[legs["call"]["short"]["occ"]]["bid"]
              - mids[legs["call"]["long"]["occ"]]["ask"])
    if credit <= 0:
        return None
    put_width = legs["put"]["short"]["strike"] - legs["put"]["long"]["strike"]
    call_width = legs["call"]["long"]["strike"] - legs["call"]["short"]["strike"]
    width = max(put_width, call_width)
    if width <= 0:
        return None
    max_loss = (width - credit) * 100
    if max_loss <= 0:
        return None
    return {"put_short_occ": legs["put"]["short"]["occ"],
            "put_long_occ": legs["put"]["long"]["occ"],
            "call_short_occ": legs["call"]["short"]["occ"],
            "call_long_occ": legs["call"]["long"]["occ"],
            "put_short_strike": legs["put"]["short"]["strike"],
            "put_long_strike": legs["put"]["long"]["strike"],
            "call_short_strike": legs["call"]["short"]["strike"],
            "call_long_strike": legs["call"]["long"]["strike"],
            "expiry": legs["put"]["expiry"], "dte": legs["put"]["dte"],
            "credit": round(credit, 2), "max_loss": round(max_loss, 2),
            "width": width,
            "mids": {o: round(m["mid"], 2) for o, m in mids.items()}}


def size_contracts(equity, max_loss):
    """1% risk per condor, capped at 25 contracts (semfix). Verbatim."""
    if equity is None or equity <= 0 or max_loss <= 0:
        return 0
    n = max(0, int((equity * RISK_FRACTION) // max_loss))
    return min(n, MAX_CONTRACTS_PER_CONDOR)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def enhance_enabled(extra):
    """ENH iron_condor (IMPROVE-iron_condor): repaired loss-stop
    switch, ctx.extra['iron_condor_enhance']['enabled'], default ON;
    OFF restores the pre-change 2x-credit-only stop exactly."""
    ov = (extra or {}).get("iron_condor_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def loss_stop_threshold(credit, max_loss_per_share, enhanced=True):
    """Loss (per share) at which the stop fires. Pre-change: 2x
    credit. ENH: smaller of 2x credit and half the condor's own max
    loss per share (width - credit) — the loss-side mirror of the
    50% profit target; 2x credit is unreachable when credit >=
    width/3, so the min() restores a working stop exactly there."""
    base = STOP_MULT * credit
    if enhanced and max_loss_per_share and max_loss_per_share > 0:
        return min(base, 0.5 * max_loss_per_share)
    return base


def exit_due(pos, session_iso, dates, close_cost, enhanced=True,
             max_loss_per_share=None):
    """Verbatim old order: 50% profit, 2x premium stop, 7-DTE, 21-day
    max hold (sessions on the bar calendar; old used calendar days
    from entry_ts — named in the port report). ENH: the premium stop
    threshold is loss_stop_threshold(...) (see above)."""
    credit = pos.get("entry_credit") or 0
    if close_cost is not None and credit > 0:
        if credit - close_cost >= PROFIT_TARGET_PCT * credit:
            return "profit_target_50pct"
        if close_cost - credit >= loss_stop_threshold(
                credit, max_loss_per_share, enhanced):
            return "stop_2x_premium" if not (
                enhanced and max_loss_per_share
                and 0.5 * max_loss_per_share < STOP_MULT * credit) \
                else "stop_half_max_loss"
    try:
        from datetime import date as _date
        dte = (_date.fromisoformat(str(pos["condor"]["expiry"])[:10])
               - _date.fromisoformat(session_iso)).days
        if dte <= EXIT_DTE:
            return "dte_time_stop_7"
    except (ValueError, TypeError, KeyError):
        pass
    if pos.get("entry_date") and pos["entry_date"] in dates:
        if len(dates) - 1 - dates.index(pos["entry_date"]) >= MAX_HOLD_DAYS:
            return "max_hold_21d"
    return None


def condor_close_cost(condor, quotes):
    """Cost to close from quotes: buy shorts at ask, sell longs at bid
    (net debit). None when any leg is unquotable.
    AUDIT3-C (2026-10-16): a long wing quoting bid 0 is worthless,
    not unquotable — the winning condor's normal state; the
    pre-cure v <= 0 guard made the close cost uncomputable
    exactly then and the profit/stop exits could never fire.
    Missing quotes or an unpriceable short leg still fail."""
    q = quotes or {}
    try:
        cost = 0.0
        for occ, side in ((condor["put_short_occ"], "ask"),
                          (condor["call_short_occ"], "ask"),
                          (condor["put_long_occ"], "bid"),
                          (condor["call_long_occ"], "bid")):
            if occ not in q:
                return None
            v = float((q.get(occ) or {}).get(side) or 0)
            if side == "ask" and v <= 0:
                return None
            if side == "bid" and v < 0:
                return None
            cost += v if side == "ask" else -v
        return round(cost, 2)
    except (TypeError, ValueError, KeyError):
        return None


class IronCondor(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        iv_map = extra.get("iv") or {}
        iv_hist = extra.get("iv_history") or {}
        earn_days = extra.get("earnings_in_days") or {}
        vix = extra.get("vix")
        equity = float(context.equity or 0.0)
        universe = extra.get("universe") or list(CONFIG.universe)
        intents = []
        self._paired = []
        self.last_evaluation = {"sleeve": "iron_condor",
                                "enhance_switch": enhance_enabled(extra),
                                "paired": self._paired}
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                # D3 cure: a condor entry fill books NEGATIVE qty (net-credit
                # sale). The old qty<=0 skip made the exit path unreachable
                # on every real booked position. Exits evaluate on |qty|.
                qty = abs(int(float(pos.get("qty") or 0)))
                if qty == 0:
                    continue
                # Core dispatch records positions as {qty, entry_px,
                # entry_date, stop_px} with NO "condor" leg map — the
                # old pos["condor"] indexing raised KeyError inside
                # signal(), and dispatch has no per-sleeve try, so one
                # held condor would kill every desk tick (audit
                # 2026-10-15 batch 4). Fail soft: no leg map => no
                # quote-based exits, DTE/max-hold still evaluate in
                # exit_due (its condor access is already guarded).
                condor = pos.get("condor") or {}
                cost = condor_close_cost(condor, quotes) if condor else None
                enh_on = enhance_enabled(extra)
                ml_ps = None
                try:
                    if condor.get("width") and (pos.get("entry_credit") or 0):
                        ml_ps = float(condor["width"]) - float(pos["entry_credit"])
                except (TypeError, ValueError):
                    ml_ps = None
                paired = getattr(self, "_paired", None)
                if paired is not None and cost is not None:
                    paired.append({
                        "symbol": sym, "credit": pos.get("entry_credit"),
                        "close_cost": cost, "max_loss_per_share": ml_ps,
                        "control": exit_due(pos, context.session, _dates(bl),
                                            cost, enhanced=False),
                        "treatment": exit_due(pos, context.session, _dates(bl),
                                              cost, enhanced=True,
                                              max_loss_per_share=ml_ps),
                        "switch_on": enh_on})
                reason = exit_due(pos, context.session, _dates(bl), cost,
                                  enhanced=enh_on, max_loss_per_share=ml_ps)
                if reason:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bl[-1]["c"]), 2) if bl else None,
                        reason="iron_condor exit: %s close_cost=%s legs=%s/%s/%s/%s"
                               % (reason, cost, condor.get("put_short_occ"),
                                  condor.get("put_long_occ"),
                                  condor.get("call_short_occ"),
                                  condor.get("call_long_occ"))))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0 or not bl:
                continue
            if vix is None or float(vix) > VIX_MAX:
                continue
            rank = iv_rank_ok(iv_map.get(sym), iv_hist.get(sym))
            if rank is None or rank <= IV_RANK_MIN:
                continue
            ed = earn_days.get(sym)
            if ed is None or ed <= EARNINGS_CLEAR_DAYS:
                continue  # earnings inside 45d or unknown: fail closed
            spot = float(bl[-1]["c"])
            condor = build_condor(chains.get(sym), quotes, spot,
                                  float(iv_map[sym]), context.session)
            if not condor:
                continue
            qty = size_contracts(equity, condor["max_loss"])
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(spot, 2),
                reason="iron_condor net_credit: put=%s@%.2f/%s@%.2f "
                       "call=%s@%.2f/%s@%.2f expiry=%s dte=%d credit=%.2f "
                       "max_loss=%.2f width=%.2f iv_rank=%.1f "
                       "structure=iron_condor dte_window=%d-%d "
                       "short_delta=%.2f wing_delta=%.2f "
                       "gate_exempt_decision75=#85/#96 (net-credit sale)"
                       % (condor["put_short_occ"], condor["put_short_strike"],
                          condor["put_long_occ"], condor["put_long_strike"],
                          condor["call_short_occ"], condor["call_short_strike"],
                          condor["call_long_occ"], condor["call_long_strike"],
                          condor["expiry"], condor["dte"], condor["credit"],
                          condor["max_loss"], condor["width"], rank,
                          DTE_MIN, DTE_MAX, SHORT_DELTA, WING_DELTA)))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return IronCondor().signal(bars, slice_state, context)
