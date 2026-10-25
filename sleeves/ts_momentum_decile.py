"""TS Momentum Decile — lean-desk port (Wave C), ACTIVE.

EXTRACTED from the old desk's ts_momentum_decile.py (frozen spec).
Was PARKED per Decision #86 (2026-10-13; de-ghosted re-run t=0.68);
the owner's 2026-10-14 21:54 clarification ("ALL OF THE SLEEVES, LOGICAL,
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

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending, genome universe
(bars keys). Rebalance gating (first trading day / once per month) is
the Scheduler's; this function emits the rebalance diff whenever called.
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

MIN_BARS = 253
MEDIAN_DV_DAYS = 63
MEDIAN_DV_MIN = 1_000_000
DECILE = 0.10
EQUITY_UTIL = 0.95
NEW_ENTRIES_PAUSED = False  # was Decision #86's enforcer; park lifted by the owner 2026-10-14 21:54
SECTOR_CAP = 0.25

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


def improve_enabled(extra):
    """ENH (IMPROVE-ts_momentum_decile): the by-value sector-cap pass
    switch — context.extra["ts_momentum_decile_improve"]
    ["sector_cap_value_pass"], default ON; OFF restores the
    pre-change rule exactly (count cap only)."""
    ov = (extra or {}).get("ts_momentum_decile_improve")
    if isinstance(ov, dict) and "sector_cap_value_pass" in ov:
        return bool(ov["sector_cap_value_pass"])
    return True


def apply_sector_cap_by_value(entries):
    """ENH: second enforcement of SECTOR_CAP on the SIZED entry set,
    by value. entries: [(sym, qty, px)] in rank order. Drops the
    lowest-ranked names of any known sector over the cap until its
    share of total sized notional is <= SECTOR_CAP; dropped slots
    stay unspent. Returns (kept, trims)."""
    kept = list(entries)
    trims = []
    while kept:
        total = sum(q * px for _, q, px in kept)
        if total <= 0:
            break
        over = None
        for sec in sorted({SECTOR_MAP.get(sy) for sy, _, _ in kept} - {None}):
            val = sum(q * px for sy, q, px in kept if SECTOR_MAP.get(sy) == sec)
            if val / total > SECTOR_CAP:
                over = sec
                break
        if over is None:
            break
        victim = [e for e in reversed(kept) if SECTOR_MAP.get(e[0]) == over][0]
        kept.remove(victim)
        trims.append((victim[0], over))
    return kept, trims


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


class TsMomentumDecile(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        equity = float(context.equity or 0.0)
        decile, _eligible, _stats = rank_decile(bars, context.session)
        decile, _trims = apply_sector_cap(decile)
        target = set(decile)
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        # Rebalance sells: held names no longer in the decile exit.
        for sym, p in book.items():
            if sym in target:
                continue
            bl = bars.get(sym) or []
            qty = int(float(p.get("qty") or 0))
            if qty > 0 and bl:
                intents.append(Intent(
                    "exit", sym, qty_hint=qty,
                    price_hint=round(float(bl[-1]["c"]), 2),
                    reason="ts_momentum_decile rebalance: dropped from "
                           "top decile"))
        # Entries: emitted only when not paused (NEW_ENTRIES_PAUSED is
        # False since the owner lifted the #86 park on 2026-10-14 21:54).
        if NEW_ENTRIES_PAUSED or equity <= 0:
            return intents
        per_name = equity * EQUITY_UTIL / max(1, len(decile))
        sized = []
        for sym in decile:
            if sym in book:
                continue
            bl = bars.get(sym) or []
            if not bl:
                continue
            px = float(bl[-1]["c"])
            if px <= 0:
                continue
            qty = int(per_name // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): no 1-share minimum.
                # The "Decision #20" floor this line cited is
                # superseded by the desk's own record — the old
                # desk removed the forced floor as a HIGH bugfix
                # on 2026-10-09 (it ordered a share the risk
                # budget had sized at zero), and the sibling
                # ports record that removal as the correct
                # semantics. A per-name budget that buys nothing
                # takes no position.
                continue
            sized.append((sym, qty, px))
        gate_on = improve_enabled(extra)
        control_syms = [e[0] for e in sized]
        if gate_on:
            sized, vtrims = apply_sector_cap_by_value(sized)
        else:
            vtrims = []
        self.last_evaluation = {
            "improve_switch": gate_on,
            "paired_record": {"control_entries": control_syms,
                              "treatment_entries": [e[0] for e in sized],
                              "value_trims": vtrims}}
        for sym, qty, px in sized:
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                reason="ts_momentum_decile rebalance: top-decile 252d "
                       "momentum, equal weight %.2f" % per_name))
        return intents


def signal(bars, slice_state, context):
    return TsMomentumDecile().signal(bars, slice_state, context)
