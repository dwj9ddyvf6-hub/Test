"""s_mn_faber — Midna Faber port (Lazarus batch 8).

Catalog rule (§4.2): Trend/momentum, 1D, "Faber: holds any of five
ETFs above its 10-month average", exit "ETF closes below its 10-month
average", budget $3,000. The five ETFs are the classic Faber GTAA-5
set (SPY, EFA, EEM, VNQ, AGG) — the catalog says "five ETFs" without
naming them; the GTAA-5 reading is recorded in FIDELITY-LEDGER.md.
10-month average = 210-session SMA of daily closes. The book holds
every qualifying ETF with an equal $600 share of the $3,000 budget
(the catalog's "3 slots" conflicts with a five-ETF hold-any rule;
ledger records the reading). Monthly method traded on the daily
clock: entries/exits evaluate every session, per the catalog TF=1D.
"""
from datetime import date as _date

from sleeves.laz8_common import (Intent, SleeveConfig, closes,
                                  held_positions, qty_for, sma)

EXP_ID_FABER19 = "ENH19-FABER-STALE-20261024"


def _faber_stale(b, context):
    """ENH19: entry decision bar provably stale vs the session
    (>4 calendar days; Mon-after-Fri and post-holiday Tue pass)."""
    cfg = (getattr(context, "extra", None) or {}).get("s_mn_faber_enh19") or {}
    if cfg.get("stale_gate", True) is False:
        return False
    try:
        bd = _date.fromisoformat(str(b[-1].get("t"))[:10])
        sd = _date.fromisoformat(str(getattr(context, "session", ""))[:10])
    except (TypeError, ValueError):
        return False
    stale = (sd - bd).days > 4
    if stale:
        j = (getattr(context, "extra", None) or {}).get("enh19_journal")
        if isinstance(j, list):
            j.append({"exp_id": EXP_ID_FABER19, "sleeve": "s_mn_faber",
                      "enhanced": "refuse_stale_bar",
                      "shadow_faithful": "enter",
                      "last_bar": str(b[-1].get("t"))[:10]})
    return stale

CONFIG = SleeveConfig(sleeve_id="s_mn_faber", cadence_s=300,
                      universe=("SPY", "EFA", "EEM", "VNQ", "AGG"),
                      state_schema={"position": "dict|None"})
ETFS = ("SPY", "EFA", "EEM", "VNQ", "AGG")
BUDGET = 3000.0
PER_ETF = BUDGET / len(ETFS)
MA_BARS = 210


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    for sym in ETFS:
        b = bars.get(sym) or []
        if len(b) < MA_BARS:
            continue
        ma = sma(closes(b), MA_BARS)
        px = float(b[-1]["c"])
        if sym in held and px < ma:
            out.append(Intent(
                kind="exit", symbol=sym,
                qty_hint=int(abs(float(held[sym]["qty"]))),
                side="sell", position_intent="sell_to_close", price_hint=px,
                reason=f"s_mn_faber exit: close {px:.2f} below 10mo_avg {ma:.2f}"))
        elif sym not in held and px > ma and not _faber_stale(b, context):
            q = qty_for(PER_ETF, px)
            if q > 0:
                out.append(Intent(
                    kind="enter", symbol=sym, qty_hint=q, side="buy",
                    position_intent="buy_to_open", price_hint=px,
                    reason=f"s_mn_faber entry: close {px:.2f} above 10mo_avg {ma:.2f}"))
    return out
