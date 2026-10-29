"""TS Momentum Decile — lean-desk port (Wave C), ACTIVE.

EXTRACTED from the old desk's ts_momentum_decile.py (frozen spec).
Was PARKED per Decision #86 (2026-10-13; de-ghosted re-run t=0.68);
User's 2026-10-14 21:54 clarification ("ALL OF THE SLEEVES, LOGICAL,
AND ON") takes it OFF the park: its stated un-park blocker was the
missing risk_gate wiring, which the no-gates cutover doctrine
dissolves. CONFIG.parked=False and NEW_ENTRIES_PAUSED=False — the
sleeve trades its frozen spec exactly as written below; rebalance
SELLS (exits) proceed as they always did.

Frozen spec (verbatim): monthly rebalance on the first trading day;
signal = 252-trading-day return on closed daily bars; eligibility >= 253
bars AND $1M trailing-63d MEDIAN dollar volume; bankruptcy hygiene —
exclude any symbol whose trailing window contains a month > +500%
preceded by >= 3 months each |return| < 5% (monthly returns measured
from the PREVIOUS month's final close — the 2026-10-12 audit fix);
rank desc, take the top decile (ceil(10%)); sector cap 25% of sleeve
notional (MF-052) trimming the lowest-ranked names of over-cap sectors,
unknown sector ("OTHER") uncapped; equal weight per-name notional =
equity x 0.95 / N_decile (sizing is core Risk's; the qty hint follows
it); NO stops, NO take profit — the rebalance is the risk management.
The rank drops the forming bar (last bar dated >= session is excluded,
the old rank_decile point-in-time law).

Master-desk restoration of the old runtime (the femto port emitted the
diff on every call and sized off the prior close): the rebalance runs on
the first trading day of the month (old cron dom 1-4 10:00 ET, self-gated
on first-trading-day + once-per-month). The rank stages the diff at
>= 10:00 once the genome carries the previous session (by 15:30 it ranks
on what it has, never skipping the month); the next pass fills it: sells
first (full qty, market, day), then buys — per_name = equity x 0.95 /
N(sector-capped decile), qty = max(1, floor(per_name / ref)), ref = the
fresh regular-hours mid (old: the topped-up cache's intraday close at
10:00), else the last close; market, day. The rank sees what the old one
saw: its fetch top-up kept 400 bars including today's partial (dropped),
so the last 399 completed bars. Named divergence: the desk-wide earnings
blackout (desk/earnings.py, Decision #8) is not applied — the cutover
doctrine — like the 150% breaker, drawdown brake, context gate and
Decision #75 the old fill path also called.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "meta": the sleeve's stamps (pending, last_rank_month, filled_month)
  "quotes": {SYM: {"bid","ask","t"}} for held and staged names
  "nyse_holidays": ["YYYY-MM-DD", ...]
Bars: daily dicts {"t","o","h","l","c","v"} ascending, genome universe
(bars keys), completed sessions.
"""
import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig

MIN_BARS = 253
MEDIAN_DV_DAYS = 63
MEDIAN_DV_MIN = 1_000_000
DECILE = 0.10
EQUITY_UTIL = 0.95
NEW_ENTRIES_PAUSED = False  # was Decision #86's enforcer; park lifted by User 2026-10-14 21:54
SECTOR_CAP = 0.25
FETCH_KEEP = 400          # old fetch_bars top-up keep (incl. today's partial bar, dropped by the rank)
RANK_HM = (10, 0)         # old cron dom 1-4 10:00 ET
LAST_CALL_HM = (15, 30)   # rank on whatever the genome carries rather than skip the month
MIN_FRESH = 0.5           # share of ranked names that must carry the previous session
ET = ZoneInfo("America/New_York")

# Verbatim from the old sleeve (strategic audit 2026-10-07, MF-052).
SECTOR_MAP = {
    "NVDA": "SEMI", "AMD": "SEMI", "INTC": "SEMI", "MU": "SEMI",
    "AVGO": "SEMI", "QCOM": "SEMI", "TXN": "SEMI", "ADI": "SEMI",
    "AMAT": "SEMI", "LRCX": "SEMI", "KLAC": "SEMI", "ASML": "SEMI",
    "MCHP": "SEMI", "ON": "SEMI", "NXPI": "SEMI", "MPWR": "SEMI",
    "SWKS": "SEMI", "QRVO": "SEMI", "MRVL": "SEMI", "MXL": "SEMI",
    "SNDK": "SEMI", "WDC": "SEMI", "STX": "SEMI", "LITE": "SEMI",
    "COHR": "SEMI", "CIEN": "SEMI", "TER": "SEMI", "FORM": "SEMI",
    "COHU": "SEMI", "TSEM": "SEMI", "SILC": "SEMI", "AEHR": "SEMI",
    "ICHR": "SEMI", "AXTI": "SEMI", "VICR": "SEMI", "DOCN": "SEMI",
    "VSXY": "SEMI", "ASX": "SEMI", "UMC": "SEMI", "STM": "SEMI",
    "IFX": "SEMI", "ARM": "SEMI", "SMCI": "SEMI", "DELL": "SEMI",
    "HPE": "SEMI", "ANET": "SEMI",
    "SOXL": "LEV_ETF", "SOXS": "LEV_ETF", "TQQQ": "LEV_ETF",
    "SQQQ": "LEV_ETF", "TECL": "LEV_ETF", "TECS": "LEV_ETF",
    "LABU": "LEV_ETF", "LABD": "LEV_ETF", "FAS": "LEV_ETF",
    "FAZ": "LEV_ETF",
    "MRNA": "BIOTECH", "BNTX": "BIOTECH", "REGN": "BIOTECH",
    "VRTX": "BIOTECH", "AMGN": "BIOTECH", "GILD": "BIOTECH",
    "BIIB": "BIOTECH", "ILMN": "BIOTECH", "PRAX": "BIOTECH",
    "RVMD": "BIOTECH", "IBRX": "BIOTECH", "BFLY": "BIOTECH",
    "GH": "BIOTECH",
    "MSFT": "SOFTWARE", "ORCL": "SOFTWARE", "CRM": "SOFTWARE",
    "NOW": "SOFTWARE", "SNOW": "SOFTWARE", "DDOG": "SOFTWARE",
    "TWLO": "SOFTWARE", "FSLY": "SOFTWARE", "RNG": "SOFTWARE",
    "VSTS": "SOFTWARE", "SMTC": "SOFTWARE", "MTSI": "SOFTWARE",
    "VIAV": "SOFTWARE", "CRNX": "SOFTWARE", "VELO": "SOFTWARE",
    "XOM": "ENERGY", "CVX": "ENERGY", "EOG": "ENERGY",
    "PXD": "ENERGY", "VLO": "ENERGY", "PBF": "ENERGY",
    "BE": "ENERGY",
    "JPM": "FIN", "BAC": "FIN", "WFC": "FIN", "GS": "FIN", "MS": "FIN",
}

CONFIG = SleeveConfig(
    sleeve_id="ts_momentum_decile", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=0.0075, parked=False)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def median_dv(bars, days=MEDIAN_DV_DAYS):
    """Trailing median daily dollar volume — verbatim port."""
    tail = bars[-days:]
    if not tail:
        return 0.0
    dvs = sorted(float(b["c"]) * float(b["v"]) for b in tail)
    n = len(dvs)
    return dvs[n // 2] if n % 2 else (dvs[n // 2 - 1] + dvs[n // 2]) / 2


def monthly_returns(bars):
    """[(yyyy-mm, ret)] with each month measured from the PREVIOUS
    month's final close — verbatim port (2026-10-12 audit fix)."""
    months = {}
    for b, d in zip(bars, _dates(bars)):
        months.setdefault(d[:7], []).append(b)
    out = []
    prev_close = None
    for ym in sorted(months):
        mb = months[ym]
        base = prev_close if prev_close else float(mb[0]["c"])
        c = float(mb[-1]["c"])
        out.append((ym, (c / base - 1) if base else 0.0))
        prev_close = c
    return out


def has_artifact_signature(bars):
    """v2 bankruptcy hygiene: a month > +500% preceded by >= 3 flat
    months (|ret| < 5%). Verbatim port."""
    bl = bars[-504:] if len(bars) > 504 else bars
    mr = monthly_returns(bl)
    for i in range(3, len(mr)):
        if mr[i][1] > 5.0 and all(abs(mr[j][1]) < 0.05
                                  for j in range(i - 3, i)):
            return True, mr[i][0]
    return False, None


def apply_sector_cap(ranked_syms):
    """Verbatim port: iteratively trim the lowest-ranked names of any
    known sector over SECTOR_CAP of the kept count; OTHER uncapped."""
    from collections import Counter
    if not ranked_syms:
        return ranked_syms, []
    keep = set(ranked_syms)
    trims = []
    while True:
        total = len(keep)
        if total == 0:
            break
        counts = Counter(SECTOR_MAP.get(s, "OTHER")
                         for s in ranked_syms if s in keep)
        trimmed_this_round = False
        for sector, cnt in counts.items():
            if sector == "OTHER":
                continue
            while cnt / total > SECTOR_CAP and total > 1:
                victims = [s for s in reversed(ranked_syms)
                           if SECTOR_MAP.get(s) == sector and s in keep]
                if not victims:
                    break
                s = victims[0]
                keep.discard(s)
                trims.append((s, sector))
                cnt -= 1
                total -= 1
                trimmed_this_round = True
        if not trimmed_this_round:
            break
    return [s for s in ranked_syms if s in keep], trims


def rank_decile(bars_by_sym, today):
    """Verbatim port of rank_decile: (decile_syms, eligible_count, stats).
    The forming bar (last bar dated >= today) is dropped before ranking."""
    scored = []
    excluded_artifact = []
    for s, bl in bars_by_sym.items():
        if len(bl) < MIN_BARS:
            continue
        if bl and _dates(bl)[-1] >= today:
            bl = bl[:-1]
        if len(bl) < MIN_BARS:
            continue
        if median_dv(bl) < MEDIAN_DV_MIN:
            continue
        bad, ym = has_artifact_signature(bl)
        if bad:
            excluded_artifact.append((s, ym))
            continue
        closes = [float(b["c"]) for b in bl]
        if closes[-253] <= 0 or not math.isfinite(closes[-1]):
            continue
        scored.append((s, closes[-1] / closes[-253] - 1))
    scored.sort(key=lambda t: -t[1])
    n = max(1, math.ceil(len(scored) * DECILE)) if scored else 0
    return ([s for s, _ in scored[:n]], len(scored),
            {"excluded_artifact": excluded_artifact,
             "top_ret": scored[0][1] if scored else None,
             "cut_ret": scored[n - 1][1] if scored and n else None})


def _trading_day(d, holidays):
    return d.weekday() < 5 and d.isoformat() not in holidays


def first_trading_day(year, month, holidays):
    d = date(year, month, 1)
    while not _trading_day(d, holidays):
        d += timedelta(days=1)
    return d


def prev_trading_day(d, holidays):
    d -= timedelta(days=1)
    while not _trading_day(d, holidays):
        d -= timedelta(days=1)
    return d


def _now_et(context):
    return datetime.fromtimestamp(float(context.now), tz=ET)


def _holidays(context):
    return set((context.extra or {}).get("nyse_holidays") or ())


def _phase(context):
    """the rebalance day (the month's first trading day) during the session after 10:00 ET."""
    t = _now_et(context)
    if t.date() != first_trading_day(t.year, t.month, _holidays(context)):
        return None
    if (t.hour, t.minute) < RANK_HM or t.hour >= 16:
        return None
    return "rebalance"


def _book(state):
    return {s: v["position"] for s, v in state.items() if isinstance(v, dict) and v.get("position")}


def rank(bars, context):
    """old mode_rank: the sector-capped top decile on the last 399 completed bars, buys = decile names not
    held, sells = held names out of the decile. None while the genome lacks the previous session."""
    today = context.session
    t = _now_et(context)
    prev = prev_trading_day(t.date(), _holidays(context)).isoformat()
    trimmed = {s: bl[-(FETCH_KEEP - 1):] for s, bl in bars.items() if bl}
    if (t.hour, t.minute) < LAST_CALL_HM:
        long_enough = [bl for bl in trimmed.values() if len(bl) >= MIN_BARS]
        fresh = sum(1 for bl in long_enough if _dates(bl[-1:])[0] >= prev)
        if not long_enough or fresh < MIN_FRESH * len(long_enough):
            return None
    decile, eligible, stats = rank_decile(trimmed, today)
    decile, trims = apply_sector_cap(decile)
    book = _book((context.extra or {}).get("sleeve_state") or {})
    dset = set(decile)
    return {"buys": [s for s in decile if s not in book], "sells": [s for s in book if s not in dset],
            "decile": decile, "eligible": eligible, "trims": [s for s, _sec in trims],
            "excluded_artifact": [s for s, _ym in stats["excluded_artifact"]], "rank_date": today}


def _ref_px(sym, bars, quotes, now):
    q = quotes.get(sym) or {}
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
    except (TypeError, ValueError):
        bid = ask = 0.0
    if 0 < bid <= ask and q.get("t") is not None and now - float(q["t"]) <= 900:
        t = datetime.fromtimestamp(float(q["t"]), tz=ET)
        if (9, 30) <= (t.hour, t.minute) < (16, 0):
            return (bid + ask) / 2.0
    bl = bars.get(sym) or []
    return float(bl[-1]["c"]) if bl else None


class TsMomentumDecile(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """the fill pass: the staged sells, then equal-weight buys (old mode_fill minus the desk gates)."""
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        pend = meta.get("pending") or {}
        if _phase(context) != "rebalance" or pend.get("rank_date") != context.session \
                or meta.get("filled_month") == context.session[:7]:
            return []
        state = extra.get("sleeve_state") or {}
        book = _book(state)
        now = float(context.now)
        close_ts = _now_et(context).replace(hour=16, minute=0, second=0, microsecond=0).timestamp()
        order = {"type": "market", "tif": "day", "not_after": close_ts}
        intents = []
        for sym in pend.get("sells") or []:
            p = book.get(sym) or {}
            qty = float(p.get("qty") or 0)
            if qty <= 0 or p.get("exit_submitted"):
                continue
            bl = bars.get(sym) or []
            intents.append(Intent("exit", sym, qty=qty, price_hint=round(float(bl[-1]["c"]), 2) if bl else None,
                                  order=dict(order), signal_key="%s:%s:tsmom_sell" % (sym, context.session),
                                  reason="ts_momentum_decile rebalance: dropped from top decile"))
        equity = float(context.equity or 0.0)
        if NEW_ENTRIES_PAUSED or equity <= 0:
            return intents
        decile = pend.get("decile") or []
        buys = list(pend.get("buys") or [])
        n_target = len(decile) if decile else max(1, len(buys) + len(book))
        per_name = equity * EQUITY_UTIL / n_target
        quotes = extra.get("quotes") or {}
        for sym in buys:
            if sym in book or (state.get(sym) or {}).get("pending_entry"):
                continue
            ref = _ref_px(sym, bars, quotes, now)
            if not ref or ref <= 0:
                continue
            qty = max(1, math.floor(per_name / ref))             # 1-share minimum (Decision #20)
            intents.append(Intent("enter", sym, qty=float(qty), price_hint=round(ref, 2), order=dict(order),
                                  signal_key="%s:%s:tsmom_buy" % (sym, context.session),
                                  reason="ts_momentum_decile rebalance: top-decile 252d momentum, equal weight "
                                         "%.2f of %d" % (per_name, n_target)))
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    if _phase(context) != "rebalance":
        return meta
    month = context.session[:7]
    pend = meta.get("pending") or {}
    if meta.get("last_rank_month") != month:
        p = rank(bars, context)
        if p is not None:
            meta.update(pending=p, last_rank_month=month)
    elif pend.get("rank_date") == context.session and meta.get("filled_month") != month:
        meta["filled_month"] = month                            # the fill pass ran (signal emitted the diff)
        meta["last_fill"] = {"date": context.session, "buys": [i.symbol for i in intents if i.kind == "enter"],
                             "sells": [i.symbol for i in intents if i.kind == "exit"]}
        meta["pending"] = {}
    return meta


def signal(bars, slice_state, context):
    return TsMomentumDecile().signal(bars, slice_state, context)
