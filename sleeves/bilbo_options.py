"""Bilbo Box Options — lean-desk port (Wave B).

EXTRACTED from the old desk's bilbo_options_signals.py (the pure
signal engine, itself a faithful reimplementation of Milkman's
box_signals.py with the LIVE flags: minutes=60, session='eth',
break_rule='close', min_grey=1, first_bar_only=True, stdev_ddof=1)
plus bilbo_options.py's runner constants. The pandas engine is
re-expressed on bar lists with identical formulas. See
ports/bilbo_options.md.

Rules (old docstrings): 5-min ET bars 04:00-19:55 resampled to 60-min
on the on-the-hour grid (extended hours). Grey = Saty Phase
compression (21 BB inside 2x ATR14 Keltner, except not-shrinking +
inside the 1.854x expansion zone). Box = high/low of the FIRST 5 grey
hourly candles of a run, frozen after the 5th; run live 10 calendar
days. Entry: FIRST candle out of compression CLOSES above box high;
long only; ONE SHOT per run. Gates: hourly close lands 10:00-15:00 ET
Mon-Fri; spot strictly above daily 21 EMA at the prior completed RTH
close; two-sided call quote with spread <= 5% of mid.
Contract: ONE call, strike nearest (spot + 0.75 x prior daily ATR14),
nearest expiry in 21-37 DTE. 4% of equity in premium, 1-contract min.
The entry submits as a LIMIT order at the quoted mid (the enter
Intent's limit_price; CURE11, 2026-10-18) — never a market order.
Exits (keyed to the STOCK): 5-min close below box low; giveback once
+1.25 x dATR in favour (sell at/below entry + 25% of peak gain);
10-trading-day time cap; expiry-proximity backstop (DTE <= 5).

Inputs via context.extra:
  "bars_5m":      {SYM: [5-min bar dicts, epoch t, ascending]}
  "chains":       {SYM: [{"symbol","strike","expiration"}]} (calls)
  "quotes":       {OCC: {"bid","ask"}}
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars (arg): unused for this sleeve (its series are 5-min/hourly);
kept for contract uniformity.
"""
import math
import re
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

UNIVERSE = ("NVDA", "NFLX", "AMD", "GOOGL", "AAPL", "AMZN", "MSFT",
            "AVGO", "TSLA", "PLTR", "INTC", "MU", "JPM", "UBER", "BAC",
            "DIS", "META", "SMCI", "HOOD", "COIN")
MAX_POSITIONS = 5
WATCH_DAYS = 10
BOX_FREEZE = 5
MIN_GREY = 1
TIME_CAP_TRADING_DAYS = 10
EXPIRY_PROXIMITY_DTE = 5
GIVEBACK_ARM_ATR = 1.25   # 2026-10-02 post-mortem fix (was 1.0)
GIVEBACK_KEEP = 0.25
SPREAD_GATE = 0.05
STRIKE_ATR_MULT = 0.75
MIN_DTE, MAX_DTE = 15, 21  # ENH 2026-10-24 (IMPROVE-bilbo_options)
CONTROL_MIN_DTE, CONTROL_MAX_DTE = 21, 37  # pre-change window (control)


# --- ENH switch + paired record (Edge IMPROVE-bilbo_options, Group A):
# buy the nearest expiry >=15 DTE (cap 21) instead of 21-37 DTE.
# Switch: extra["bilbo_options_improve"] {"expiry_window_15_21": bool},
# default ON; OFF restores the 21-37 window exactly. Paired records go
# to extra["bilbo_options_exp_journal"]["records"] when served.
EXP_ID_BILBO = "ENH-BILBO-20261024"


def _bilbo_enh_enabled(extra):
    ov = (extra or {}).get("bilbo_options_improve")
    if isinstance(ov, dict) and "expiry_window_15_21" in ov:
        return bool(ov["expiry_window_15_21"])
    return True


def _bilbo_paired(extra, record):
    j = (extra or {}).get("bilbo_options_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)
PREMIUM_FRACTION = 0.04
ENTRY_HOUR_LO, ENTRY_HOUR_HI = 10, 15

CONFIG = SleeveConfig(
    sleeve_id="bilbo_options", cadence_s=300, universe=UNIVERSE,
    state_schema={"position": "dict|None"}, risk_pct=PREMIUM_FRACTION)


# ------------------------------------------------------------ series
def _ewm(values, alpha):
    out, v = [], None
    for x in values:
        v = x if v is None else v + alpha * (x - v)
        out.append(v)
    return out


def ema(values, n):
    return _ewm(values, 2.0 / (n + 1.0))


def rma(values, n):
    return _ewm(values, 1.0 / n)


def atr_series(bars, n=14):
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(float(b["h"]) - float(b["l"]))
        else:
            pc = float(bars[i - 1]["c"])
            trs.append(max(float(b["h"]) - float(b["l"]),
                           abs(float(b["h"]) - pc), abs(float(b["l"]) - pc)))
    return rma(trs, n)


def _rolling_std(values, window=21):
    out = []
    for i in range(len(values)):
        w = values[max(0, i - window + 1):i + 1]
        if len(w) < 2:
            out.append(float("nan"))
            continue
        m = sum(w) / len(w)
        out.append(math.sqrt(sum((x - m) ** 2 for x in w) / (len(w) - 1)))
    return out


def phase_compression(bars):
    """Saty Phase compression flag (grey) on hourly bars — identical
    formula to the old phase_compression (ddof=1)."""
    n = len(bars)
    if n == 0:
        return []
    price = [float(b["c"]) for b in bars]
    a14 = atr_series(bars, 14)
    pivot = ema(price, 21)
    sd = _rolling_std(price, 21)
    comp, inexp = [], []
    for i in range(n):
        above = price[i] >= pivot[i]
        bb_up, bb_dn = pivot[i] + 2.0 * sd[i], pivot[i] - 2.0 * sd[i]
        kc_up, kc_dn = pivot[i] + 2.0 * a14[i], pivot[i] - 2.0 * a14[i]
        ex_up, ex_dn = pivot[i] + 1.854 * a14[i], pivot[i] - 1.854 * a14[i]
        comp.append((bb_up - kc_up) if above else (kc_dn - bb_dn))
        inexp.append((bb_up - ex_up) if above else (ex_dn - bb_dn))
    grey = [0] * n
    for i in range(1, n):
        widening = comp[i - 1] <= comp[i]
        if widening and inexp[i] > 0:
            grey[i] = 0
        elif comp[i] <= 0:
            grey[i] = 1
    return grey


# ------------------------------------------------------------ resample
def _et(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone(ET)


def resample_eth_hourly(bars5):
    """5-min bars (bar-START t) -> hourly on-the-hour ET bars, keeping
    04:00-19:55 ET; empty hours dropped. Verbatim old resample."""
    groups = {}
    for b in bars5:
        lt = _et(b["t"])
        if not (dtime(4, 0) <= lt.time() <= dtime(19, 55)):
            continue
        key = lt.replace(minute=0, second=0, microsecond=0).timestamp()
        groups.setdefault(key, []).append(b)
    out = []
    for key in sorted(groups):
        g = groups[key]
        out.append({"t": key, "o": float(g[0]["o"]),
                    "h": max(float(x["h"]) for x in g),
                    "l": min(float(x["l"]) for x in g),
                    "c": float(g[-1]["c"]),
                    "v": sum(float(x.get("v") or 0) for x in g)})
    return out


def daily_rth(bars5):
    """5-min bars -> daily RTH (09:30-15:55 ET) bars, date-ordered."""
    groups = {}
    for b in bars5:
        lt = _et(b["t"])
        if not (dtime(9, 30) <= lt.time() <= dtime(15, 55)):
            continue
        groups.setdefault(lt.date().isoformat(), []).append(b)
    out = []
    for d in sorted(groups):
        g = groups[d]
        first = _et(g[0]["t"]).replace(hour=0, minute=0, second=0,
                                       microsecond=0)
        out.append({"t": first.timestamp(), "date": d,
                    "o": float(g[0]["o"]),
                    "h": max(float(x["h"]) for x in g),
                    "l": min(float(x["l"]) for x in g),
                    "c": float(g[-1]["c"]),
                    "v": sum(float(x.get("v") or 0) for x in g)})
    return out


# ------------------------------------------------------------ episodes
def detect_episodes(bars5):
    """Verbatim port of the old detect_episodes (live flags). Returns
    episode dicts: start_t, box_hi, box_lo, n_grey, out_idx, direction,
    broke, entry_t (close time of the out-bar), spot, datr14_prior."""
    h = resample_eth_hourly(bars5)
    if len(h) < 200:
        return []
    grey = phase_compression(h)
    close_t = [float(b["t"]) + 3600 for b in h]
    dly = daily_rth(bars5)
    atr = atr_series(dly, 14)
    datr_prior = [None] + atr[:-1]  # prior completed RTH day (shift 1)
    dly_dates = [d["date"] for d in dly]
    episodes, ep = [], 0
    for i in range(len(h)):
        if grey[i] != 1 or (i > 0 and grey[i - 1] == 1):
            continue
        if i == 0:
            continue
        start_date = _et(h[i]["t"]).date().isoformat()
        cand = [j for j, d in enumerate(dly_dates) if d <= start_date]
        if not cand:
            continue
        dp = datr_prior[cand[-1]]
        if dp is None or (isinstance(dp, float) and math.isnan(dp)):
            continue
        ep += 1
        box_hi, box_lo, n_grey = float(h[i]["h"]), float(h[i]["l"]), 1
        deadline = close_t[i] + WATCH_DAYS * 86400
        j = i + 1
        out_idx, direction = None, 0
        while j < len(h) and close_t[j] <= deadline:
            if grey[j] == 1:
                n_grey += 1
                if n_grey <= BOX_FREEZE:
                    box_hi = max(box_hi, float(h[j]["h"]))
                    box_lo = min(box_lo, float(h[j]["l"]))
                j += 1
                continue
            out_idx = j
            c = float(h[j]["c"])
            direction = 1 if c > box_hi else -1 if c < box_lo else 0
            break  # first_bar_only: the run dies here either way
        episodes.append({
            "ep_id": ep, "start_t": float(h[i]["t"]),
            "box_hi": box_hi, "box_lo": box_lo, "n_grey": int(n_grey),
            "out_idx": out_idx, "direction": int(direction),
            "broke": bool(n_grey >= MIN_GREY and direction == 1),
            "entry_t": close_t[out_idx] if out_idx is not None else None,
            "spot": float(h[out_idx]["c"]) if out_idx is not None else None,
            "datr14_prior": float(dp)})
    return episodes


# ------------------------------------------------------------ gates
def time_gate_ok(entry_t):
    """Gate 1: hourly close lands 10:00-15:00 ET, Monday-Friday."""
    lt = _et(entry_t)
    if lt.weekday() >= 5:
        return False
    return dtime(ENTRY_HOUR_LO, 0) <= lt.time() <= dtime(ENTRY_HOUR_HI, 0)


def ema21_gate_ok(spot, daily, entry_t):
    """Gate 2: spot strictly above the daily 21 EMA as of the prior
    completed RTH close (daily bars strictly before entry date)."""
    if not daily or len(daily) < 21:
        return False
    entry_date = _et(entry_t).date().isoformat()
    prior = [d for d in daily if d["date"] < entry_date]
    if not prior:
        return False
    e21 = ema([float(d["c"]) for d in daily], 21)
    idx = len(prior) - 1
    return bool(spot > e21[idx])


def target_strike(spot, datr14_prior, strikes):
    """Strike nearest (spot + 0.75 x prior dATR14). Verbatim."""
    target = spot + STRIKE_ATR_MULT * datr14_prior
    ss = sorted(float(s) for s in strikes)
    return min(ss, key=lambda s: abs(s - target))


def select_expiry(expirations, session_iso, min_dte=MIN_DTE, max_dte=MAX_DTE):
    """Nearest expiry inside the 21-37 calendar-day window."""
    from datetime import date as _date
    try:
        ref = _date.fromisoformat(session_iso)
    except ValueError:
        return None
    cands = []
    for e in expirations:
        try:
            d = _date.fromisoformat(str(e)[:10])
        except ValueError:
            continue
        dte = (d - ref).days
        if min_dte <= dte <= max_dte:
            cands.append((dte, d.isoformat()))
    return min(cands)[1] if cands else None


def spread_gate_ok(bid, ask, max_frac=SPREAD_GATE):
    """Gate 3: two-sided quote no wider than 5% of mid. Verbatim."""
    try:
        b, a = float(bid), float(ask)
    except (TypeError, ValueError):
        return False
    if b <= 0 or a <= 0 or a < b:
        return False
    return (a - b) / ((a + b) / 2.0) <= max_frac


def size_contracts(equity, premium_per_contract, fraction=PREMIUM_FRACTION):
    """4% of equity in premium. Verbatim shape, two OBS-1
    defects cured under Midna's ruling (2026-10-22, F-A1(a)):
    the old body forced a 1-contract minimum over the premium
    budget and returned 1 on unpriceable input — it ordered a
    contract the budget had sized at zero, or could not price
    at all, and reported no overshoot to any caller (the
    defect class OBS-1 cured desk-wide; the sleeves cleared
    under that ruling surface their overshoot, this one never
    did). Now: bad input or a non-positive premium sizes to
    0 (fail closed), and a budget that buys less than one
    contract takes no position."""
    try:
        prem, eq = float(premium_per_contract), float(equity)
    except (TypeError, ValueError):
        return 0
    if prem <= 0 or eq <= 0:
        return 0
    return int((fraction * eq) // prem)


_OCC_EXP_RE = re.compile(r"^[A-Z.\-]{1,6}(\d{6})[CP]\d{8}$")


def occ_expiry_date(occ):
    """Expiration date parsed from an OCC symbol, or None. Verbatim."""
    m = _OCC_EXP_RE.match(str(occ or ""))
    if not m:
        return None
    yymmdd = m.group(1)
    yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    from datetime import date as _date
    year = 2000 + yy if yy < 70 else 1900 + yy
    try:
        return _date(year, mm, dd)
    except ValueError:
        return None


def evaluate_exit(bars5, pos, session_iso=None):
    """Old evaluate_exits over 5-min bar dicts at/after entry. Returns
    (last_bar_t, reason) for the FIRST trigger, else None. Per-bar
    order: expiry rail (pre-check), time cap, box low, giveback.

    The expiry rail runs FIRST and is not hostage to bars (cure
    2026-10-19, exit_route_data_hostage): it needs only the OCC
    expiry and a reference date — the last bar's ET date when bars
    were served (unchanged), else the context session date. With
    neither, it fails closed. The stock-keyed exits below still
    require bars. When the rail fires bars-less, the returned t is
    the session date's ET midnight (no bar exists to timestamp it).
    """
    expiry = occ_expiry_date(pos.get("occ"))
    if expiry is not None:
        ref_date = None
        ref_t = None
        if bars5:
            ref_t = float(bars5[-1]["t"])
            ref_date = _et(ref_t).date()
        elif session_iso:
            from datetime import date as _date
            try:
                ref_date = _date.fromisoformat(str(session_iso)[:10])
            except ValueError:
                ref_date = None
            if ref_date is not None:
                ref_t = datetime.combine(
                    ref_date, dtime(0, 0), tzinfo=ET).timestamp()
        if ref_date is not None and \
                (expiry - ref_date).days <= EXPIRY_PROXIMITY_DTE:
            return ref_t, "expiry_proximity"
    if not bars5:
        return None
    last = bars5[-1]
    if pos.get("box_metadata_unknown"):
        return None  # stock-keyed exits need trusted levels; DTE rail ran
    if any(pos.get(k) is None for k in
           ("entry_t", "entry_spot", "box_lo", "datr14_prior",
            "entry_date")):
        return None  # repair 2026-10-15: core-recorded positions carry
        # only {qty,entry_px,entry_date,stop_px}; the old direct indexing
        # raised KeyError, which killed the whole dispatcher tick (no
        # per-sleeve try in core/dispatch). Fail closed like the
        # box_metadata_unknown path above; the DTE rail already ran.
    entry_t = float(pos["entry_t"])
    floor5 = entry_t - (entry_t % 300)
    bars = [b for b in bars5 if float(b["t"]) >= floor5]
    if not bars:
        return None
    entry_spot = float(pos["entry_spot"])
    box_lo = float(pos["box_lo"])
    datr = float(pos["datr14_prior"])
    from datetime import date as _date
    entry_date = _date.fromisoformat(str(pos["entry_date"])[:10])
    peak = entry_spot
    rth_dates = set()
    for b in bars:
        lt = _et(b["t"])
        c = float(b["c"])
        if dtime(9, 30) <= lt.time() <= dtime(15, 55):
            rth_dates.add(lt.date())
            if len([d for d in rth_dates if d > entry_date]) \
                    >= TIME_CAP_TRADING_DAYS:
                return float(b["t"]), "time_cap"
        if c < box_lo:
            return float(b["t"]), "box_low"
        peak = max(peak, float(b["h"]))
        gain = peak - entry_spot
        if gain >= GIVEBACK_ARM_ATR * datr:
            if c <= entry_spot + GIVEBACK_KEEP * gain:
                return float(b["t"]), "giveback"
    return None


class BilboOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        bars5map = extra.get("bars_5m") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        equity = float(context.equity or 0.0)
        universe = extra.get("universe") or list(CONFIG.universe)
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            st = state.get(sym) or {}
            pos = st.get("position")
            bars5 = bars5map.get(sym) or []
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                hit = evaluate_exit(bars5, pos, context.session)
                if hit:
                    # price_hint is a reference only: the last 5-min
                    # close when bars were served; when the expiry
                    # rail fired bars-less (cure 2026-10-19) there is
                    # no bar to read — fall back to the recorded
                    # entry premium instead of indexing empty bars.
                    # READINESS-20261022 F-A1: a missing entry_px
                    # must not turn a due exit into a zero-hint
                    # raise — price_hint=None is the desk's
                    # bars-less idiom (beatendown/confluence).
                    if bars5:
                        hint = float(bars5[-1]["c"])
                    else:
                        _ep = pos.get("entry_px")
                        hint = float(_ep) if _ep and float(_ep) > 0 else None
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=(round(hint, 2) if hint else None),
                        reason="bilbo_options exit: %s occ=%s" % (hit[1], pos.get("occ"))))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0 or not bars5:
                continue
            hourly = resample_eth_hourly(bars5)
            if len(hourly) < 200:
                continue
            eps = detect_episodes(bars5)
            if not eps:
                continue
            ep = eps[-1]
            if not ep["broke"] or ep["out_idx"] is None:
                continue
            # Only the FIRST bar out counts, and only on its own bar:
            # the out-bar must be the last hourly bar.
            if ep["out_idx"] != len(hourly) - 1:
                continue
            if not time_gate_ok(ep["entry_t"]):
                continue
            daily = daily_rth(bars5)
            if not ema21_gate_ok(ep["spot"], daily, ep["entry_t"]):
                continue
            chain = chains.get(sym) or []
            expirations = sorted({str(c.get("expiration") or "")[:10]
                                  for c in chain if c.get("expiration")})
            _eff = (MIN_DTE, MAX_DTE) if _bilbo_enh_enabled(extra) \
                else (CONTROL_MIN_DTE, CONTROL_MAX_DTE)
            _ctrl_expiry = select_expiry(
                expirations, context.session,
                min_dte=CONTROL_MIN_DTE, max_dte=CONTROL_MAX_DTE)
            expiry = select_expiry(expirations, context.session,
                                   min_dte=_eff[0], max_dte=_eff[1])
            _bilbo_paired(extra, {
                "exp_id": EXP_ID_BILBO, "symbol": sym,
                "control_expiry": _ctrl_expiry,
                "treatment_expiry": expiry})
            if not expiry:
                continue
            strikes = [float(c["strike"]) for c in chain
                       if str(c.get("expiration") or "")[:10] == expiry
                       and c.get("strike") is not None]
            if not strikes:
                continue
            strike = target_strike(ep["spot"], ep["datr14_prior"], strikes)
            occ = next((c["symbol"] for c in chain
                        if str(c.get("expiration") or "")[:10] == expiry
                        and float(c.get("strike") or -1) == strike), None)
            if not occ:
                continue
            q = quotes.get(occ) or {}
            if not spread_gate_ok(q.get("bid"), q.get("ask")):
                continue
            mid = (float(q["bid"]) + float(q["ask"])) / 2.0
            qty = size_contracts(equity, mid * 100.0)
            if qty < 1:
                continue  # OBS-1 / F-A1(a): sized to zero — no position
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(ep["spot"], 2),
                # CURE11 (2026-10-18): the entry is a LIMIT order at
                # the quoted mid — the quote just passed the 5%-of-mid
                # spread gate above, so the mid is the sleeve's own
                # disciplined price. The port carried no limit_price,
                # so dispatch submitted the single-leg call as a
                # MARKET order (price_hint is the underlying spot, a
                # reference only) — the old runner's limit discipline
                # was never rebuilt. price_hint stays the spot: the
                # exit record's entry_spot derives from it (XT-5).
                limit_price=round(mid, 2),
                reason="bilbo_options long_call: occ=%s strike=%.2f expiry=%s "
                       "mid=%.2f box_hi=%.2f box_lo=%.2f datr14_prior=%.2f "
                       "structure=long_call dte_window=%d-%d strike_rule="
                       "nearest(spot+0.75*datr14)"
                       % (occ, strike, expiry, mid, ep["box_hi"], ep["box_lo"],
                          ep["datr14_prior"], _eff[0], _eff[1])))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return BilboOptions().signal(bars, slice_state, context)
