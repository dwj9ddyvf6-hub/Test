"""Iron Condor — lean-desk port (Wave B).

master-desk: the old desk's iron_condor_sleeve.py restored on the engine. A net-credit premium sale on the high-IV
watchlist: sell the 16-delta put and call, buy the 5-delta wings, 30-45 DTE, when implied volatility is rich
against its own history.

  iv store . one ATM IV observation per name per session (Black-Scholes inversion of the nearest 30-45 DTE
             at-the-money call's mid on the spot, r = 4%), kept in the sleeve's state; TRUE IV rank = (IV - low) /
             (high - low) x 100 over the last 252 stored observations; fewer than 60 stored = cold start, no entry
             (Decision #97, fail closed on the measurement).
  entry .... the watchlist in order, at most 3 condors held or in flight: VIX <= 35 (unknown: no entry), IV rank
             >= 50, no earnings within 45 days on a confirmed, fresh calendar (unknown: no entry), spot >= $10;
             the nearest expiry in 30-45 DTE per side, short = |BS delta at that IV| nearest 0.16, wing nearest
             0.05 beyond it, both sides the same expiry; all four legs two-sided with (ask - bid) / mid <= 10%;
             credit = short bids - wing asks > 0; max loss = (the wider wing - credit) x 100;
             floor(1% of equity / max loss) condors, at most 25; one four-leg package at that natural credit.
  exits .... (never gated) in the old order: 50% of the credit kept on the conservative close cost (shorts at
             the ask, wings at the bid); a close cost >= 3x the credit (the 2x-premium stop); <= 7 DTE; 21 days
             since the fill; a short leg deep in the money (|delta| > 0.80 at its own implied vol, or intrinsic
             >= 60% of its mid: the early-assignment guard); earnings now inside 45 days. The package closes at
             its natural (a worthless wing at zero).

Gone under the cutover doctrine: the risk gate (kill switch), drawdown brake, circuit breaker, context gate and
150% desk cap (Decision #85 / #96 had already exempted it from the chart gate). Named divergences: the IV store
records every watchlist name at the session's first pass from 10:00 ET (the old recorded a name only on the
passes that evaluated it for entry, the first of them often overnight on the prior close's quotes); the spot is
the live quote (the old read the latest SIP daily bar's close); a wing quoted with no bid counts at zero in the
close cost (the old read it as unquoted, which blinded the 50% target and the 2x stop on exactly the condors whose
wings had decayed); one atomic four-leg package at the natural credit to open and at the natural to close (the old
sent four single-leg orders, shorts first, at the same prices, and could not close a condor whose wing had no
bid); hourly passes at :31 in the session from 10:31 (the old cron ran hourly around the clock).

Inputs via context.extra:
  "universe"      the watchlist, in scan order (default WATCHLIST)
  "chains"        {SYM: rows 30-45 DTE {"symbol","strike","expiration","type","bid","ask"}} (fetched on demand)
  "option_quotes" {OCC: {"bid","ask"}} — the held legs
  "quotes"        {SYM: {"bid","ask","last"}} — spots
  "earnings"      {SYM: "YYYY-MM-DD" | None}; "earnings_fresh": bool
  "vix"           the live VIX | None
  "meta"          {"iv": {SYM: [[session, iv], ...]}}
  "iv_backfill"   {SYM: [[session, iv], ...]} the same measurement for past sessions from Alpaca's historical option
                  bars (desk/feedlib/iv_backfill.py), merged under the sleeve's own observations (its own wins a
                  session) — so the rank has its history from the first day (named divergence iv_backfill: a past
                  session's call is priced at its daily close, the sleeve's own observations at the live mid)
  "sleeve_state"  {SYM: {"position": condor group | None, "pending_entry": ...}}
Bars (arg): daily bars (the spot when no quote)."""
import math
from datetime import date, datetime, timezone

from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

_ET = ZoneInfo("America/New_York")

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


IV_STORE_CAP = 400
EARLIEST_RECORD_ET = (10, 0)


def earnings_status(sym, calendar, fresh, today, days=EARNINGS_CLEAR_DAYS):
    """the old earnings_status: "clear" | "blocked" | "unknown" (absent from the calendar or a stale calendar =
    unknown; an explicit None = no earnings; a report today .. +45 days = blocked)."""
    s = (sym or "").upper()
    if not fresh or s not in (calendar or {}):
        return "unknown"
    d = calendar[s]
    if d is None:
        return "clear"
    try:
        delta = (date.fromisoformat(str(d)[:10]) - date.fromisoformat(today)).days
    except ValueError:
        return "unknown"
    return "blocked" if 0 <= delta <= days else "clear"


def atm_iv(rows, S, session_iso):
    """the old get_iv_rank measurement: the nearest 30-45 DTE expiry's call with the strike nearest the spot, its
    mid inverted (r = 4%); None when it cannot be measured (iv <= 0 or > 500%: fail closed)."""
    try:
        ref = date.fromisoformat(session_iso)
    except ValueError:
        return None
    calls = []
    for r in rows or []:
        if r.get("type", "call") != "call" or not r.get("tradable", True):
            continue
        try:
            exp = str(r.get("expiration") or "")[:10]
            dte = (date.fromisoformat(exp) - ref).days
            calls.append((exp, dte, float(r["strike"]), r))
        except (KeyError, TypeError, ValueError):
            continue
    calls = [c for c in calls if DTE_MIN <= c[1] <= DTE_MAX]
    if not calls or not S or S <= 0:
        return None
    exp = min(c[0] for c in calls)
    cands = [c for c in calls if c[0] == exp]
    e, dte, K, row = min(cands, key=lambda c: abs(c[2] - S))
    try:
        mid = (float(row["bid"]) + float(row["ask"])) / 2
    except (KeyError, TypeError, ValueError):
        return None
    if mid <= 0:
        return None
    iv = implied_vol(mid, S, K, max(dte, 1) / 365.0, RISK_FREE, "call")
    if iv is None or iv <= 0 or iv > 5:
        return None
    return iv


def spot_of(sym, quotes, bars):
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


def held_condor(pos):
    """the held condor: its legs (from the position's meta) and the credit received / open time of the fills."""
    c = pos.get("condor") or {}
    legs = pos.get("legs") or {}
    occs = (c.get("put_short_occ"), c.get("put_long_occ"), c.get("call_short_occ"), c.get("call_long_occ"))
    if not all(occs) or not all(o in legs for o in occs):
        return None
    return dict(c, entry_credit=-float(pos.get("net_entry") or 0.0), opened_at=pos.get("opened_at"),
                contracts=int(abs(float(pos.get("qty") or 0))))


def leg_quotes(condor, quotes):
    """{leg: {"bid","ask","mid"}} (mid 0 unless two-sided)."""
    out = {}
    for leg in ("put_short", "put_long", "call_short", "call_long"):
        q = (quotes or {}).get(condor[leg + "_occ"]) or {}
        try:
            b, a = float(q.get("bid") or 0), float(q.get("ask") or 0)
        except (TypeError, ValueError):
            return None
        out[leg] = {"bid": b, "ask": a, "mid": (b + a) / 2 if b > 0 and a > 0 else 0}
    return out


def close_cost_of(lqs):
    """the old _close_cost_from_quotes: shorts at the ask, wings at the bid; None if a short has no ask or a wing
    has no quote at all. A wing quoted with no bid is worth zero (the old read it as unquoted)."""
    if not lqs:
        return None
    cost = 0.0
    for leg in ("put_short", "call_short"):
        if lqs[leg]["ask"] <= 0:
            return None
        cost += lqs[leg]["ask"]
    for leg in ("put_long", "call_long"):
        if lqs[leg]["bid"] <= 0 and lqs[leg]["ask"] <= 0:
            return None
        cost -= max(lqs[leg]["bid"], 0.0)
    return cost


def exit_due(condor, now, session_iso, close_cost):
    """the old exit_due: 50% of max profit, the 2x-premium stop, <= 7 DTE, 21 days since the fill."""
    credit = condor.get("entry_credit") or 0
    if close_cost is not None and credit > 0:
        if credit - close_cost >= PROFIT_TARGET_PCT * credit:
            return "profit_target_50pct"
        if close_cost - credit >= STOP_MULT * credit:
            return "stop_2x_premium"
    try:
        if (date.fromisoformat(str(condor["expiry"])[:10]) - date.fromisoformat(session_iso)).days <= EXIT_DTE:
            return "dte_time_stop_7"
    except (KeyError, TypeError, ValueError):
        pass
    if condor.get("opened_at") is not None and int((float(now) - float(condor["opened_at"])) // 86400) \
            >= MAX_HOLD_DAYS:
        return "max_hold_21d"
    return None


def short_leg_deep_itm(condor, lqs, S, session_iso):
    """the old early-assignment guard: (deep, why) — either short leg |delta| > 0.80 at its own implied vol, or
    intrinsic >= 60% of its mid."""
    if not lqs:
        return False, "no_quotes"
    if not S:
        return False, "price_unavailable"
    try:
        T = max((date.fromisoformat(str(condor["expiry"])[:10]) - date.fromisoformat(session_iso)).days, 1) / 365.0
    except (KeyError, TypeError, ValueError):
        return False, "bad_expiry"
    for leg, kind, kkey in (("put_short", "put", "put_short_strike"), ("call_short", "call", "call_short_strike")):
        q = lqs.get(leg)
        K = condor.get(kkey)
        if not q or not K:
            continue
        mid = q["mid"]
        if mid <= 0:
            continue
        iv = implied_vol(mid, S, K, T, RISK_FREE, kind)
        d = bs_delta(S, K, T, RISK_FREE, iv, kind) if iv else None
        if d is not None and abs(d) > 0.80:
            return True, "%s |delta|=%.2f" % (leg, abs(d))
        intr = max(K - S, 0.0) if kind == "put" else max(S - K, 0.0)
        if intr > 0 and intr >= 0.60 * mid:
            return True, "%s intrinsic-heavy (intr %.2f of mid %.2f)" % (leg, intr, mid)
    return False, "ok"


def record_iv(store, sym, iv, session_iso):
    """one observation per name per session: the session's first measurement is kept."""
    obs = list((store or {}).get(sym) or [])
    if iv is None or (obs and obs[-1][0] == session_iso):
        return obs, False
    obs.append([session_iso, round(float(iv), 6)])
    return obs[-IV_STORE_CAP:], True


def decide(bars, context):
    """(intents, iv_store updates): exits first, then the watchlist's entries, at most MAX_POSITIONS live."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    meta = extra.get("meta") or {}
    oq = extra.get("option_quotes") or {}
    chains = extra.get("chains") or {}
    quotes = extra.get("quotes") or {}
    cal, fresh = extra.get("earnings"), extra.get("earnings_fresh")
    vix = extra.get("vix")
    now = float(context.now)
    today = context.session
    equity = float(context.equity or 0.0)
    from ...feedlib.iv_backfill import merge as _merge_backfill
    store = _merge_backfill(meta.get("iv") or {}, extra.get("iv_backfill") or {}, IV_STORE_CAP)
    updates = {}
    intents, live = [], 0
    for sym, st in state.items():
        pos = (st or {}).get("position")
        if (st or {}).get("pending_entry") and not pos:
            live += 1
        if not pos:
            continue
        c = held_condor(pos)
        if c is None:
            continue
        live += 1
        if pos.get("exit_submitted"):
            continue
        lqs = leg_quotes(c, oq)
        cost = close_cost_of(lqs)
        why = exit_due(c, now, today, cost)
        if why is None:
            deep, detail = short_leg_deep_itm(c, lqs, spot_of(sym, quotes, bars), today)
            if deep:
                why = "assignment_guard_deep_itm"
        if why is None and earnings_status(sym, cal, fresh, today) == "blocked":
            why = "earnings_entered_window"
        if why:
            intents.append(Intent(
                "exit", sym, qty_hint=c["contracts"] or None, order={"window_s": 3600},
                signal_key="%s:%s:ic-exit" % (sym, today),
                reason="iron_condor exit: %s close_cost=%s credit=%.2f legs=%s/%s/%s/%s"
                       % (why, None if cost is None else round(cost, 2), c["entry_credit"], c["put_short_occ"],
                          c["put_long_occ"], c["call_short_occ"], c["call_long_occ"])))
    et = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(_ET)
    measure = (et.hour, et.minute) >= EARLIEST_RECORD_ET
    for sym in extra.get("universe") or CONFIG.universe:
        S = spot_of(sym, quotes, bars)
        st = state.get(sym) or {}
        need_entry = not (st.get("position") or st.get("pending_entry")) and live < MAX_POSITIONS and equity > 0
        recorded = bool((store.get(sym) or []) and store[sym][-1][0] == today)
        if not need_entry and (recorded or not measure):
            continue
        rows = chains.get(sym) if (need_entry or measure) else None
        iv = atm_iv(rows, S, today) if rows else None
        if measure and not recorded:
            obs, added = record_iv(store, sym, iv, today)
            if added:
                store[sym] = obs
                updates[sym] = obs
        if not need_entry or vix is None or float(vix) > VIX_MAX or iv is None:
            continue
        hist = [o[1] for o in store.get(sym) or []]
        if len(hist) < IV_RANK_COLD_START_MIN:
            continue
        rank = compute_iv_rank(iv, hist)
        if rank is None or rank < IV_RANK_MIN:
            continue
        if earnings_status(sym, cal, fresh, today) != "clear":
            continue
        if S is None or S < 10:
            continue
        by_kind = {"put": [r for r in rows if r.get("type") == "put"],
                   "call": [r for r in rows if r.get("type") == "call"]}
        condor = build_condor(by_kind, {r["symbol"]: r for r in rows if r.get("symbol")}, S, iv, today)
        if not condor:
            continue
        n = size_contracts(equity, condor["max_loss"])
        if n <= 0:
            continue
        condor["iv_rank"] = round(rank, 1)
        intents.append(Intent(
            "enter", sym, qty_hint=n, asset="mleg",
            legs=({"symbol": condor["put_short_occ"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},
                  {"symbol": condor["call_short_occ"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},
                  {"symbol": condor["put_long_occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},
                  {"symbol": condor["call_long_occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"}),
            net_price=-condor["credit"], order={"window_s": 3600}, signal_key="%s:%s:iron-condor" % (sym, today),
            position_meta={"condor": {k: condor[k] for k in (
                "put_short_occ", "put_long_occ", "call_short_occ", "call_long_occ", "put_short_strike",
                "put_long_strike", "call_short_strike", "call_long_strike", "expiry", "dte", "credit", "max_loss",
                "width", "iv_rank")}, "iv": round(iv, 4)},
            reason="iron_condor: put %s@%g/%s@%g call %s@%g/%s@%g expiry %s dte %d credit %.2f max_loss %.2f x%d; "
                   "iv %.3f rank %.1f vix %.1f; Decision #85/#96 net-credit sale"
                   % (condor["put_short_occ"], condor["put_short_strike"], condor["put_long_occ"],
                      condor["put_long_strike"], condor["call_short_occ"], condor["call_short_strike"],
                      condor["call_long_occ"], condor["call_long_strike"], condor["expiry"], condor["dte"],
                      condor["credit"], condor["max_loss"], n, iv, rank, float(vix))))
        live += 1
    return intents, updates


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_ic_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:            # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_ic_pass"] = memo
    return memo[1]


class IronCondor(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)[0])


def signal(bars, slice_state, context):
    return IronCondor().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    _intents, updates = _pass(bars, context)
    if updates:
        store = dict(meta.get("iv") or {})
        store.update(updates)
        meta["iv"] = store
    return meta
