"""s_mn_moonshot — Midna Moonshot port (Lazarus batch 8).

Catalog rule (§4.2): Lottery/deep-reset, 1D, entry "Midna moonshot
pick at 1% weight", exit "No stop; 78 weeks", 1 slot, $1,000.
The pick itself is generated upstream (Midna entire-branch signal
files -> midna_fires_v1.json, research-archive — NOT reachable from
this box, V3-SCOPE §3.4). Per the scope contract (§7.6) this lane
is a FIRE-CONSUMER: it enters only on a fresh ingested fire naming
this sleeve, and owns position management desk-side: no stop, exit
at 78 weeks (390 sessions) held. Absent/stale/malformed fires fail
closed. The $1,000 slot IS the 1%-weight pick on the TEST book.
Substitution recorded in FIDELITY-LEDGER.md.
"""
from sleeves.laz8_common import (Intent, SleeveConfig, held_positions,
                                  qty_for, xstale_refused, sessions_held)

CONFIG = SleeveConfig(sleeve_id="s_mn_moonshot", cadence_s=300,
                      state_schema={"position": "dict|None"})
BUDGET = 1000.0
HOLD_SESSIONS = 390  # 78 weeks x 5
MAX_FIRE_AGE_DAYS = 7


def _fresh_fire(context, session):
    from datetime import date
    fires = (context.extra or {}).get("fires") or []
    try:
        today = date.fromisoformat(str(session)[:10])
    except ValueError:
        return None
    best = None
    for f in fires:
        if not isinstance(f, dict) or f.get("sleeve_id") != "s_mn_moonshot":
            continue
        sym, fdate = f.get("symbol"), str(f.get("date") or "")[:10]
        if not sym or not fdate:
            continue
        try:
            age = (today - date.fromisoformat(fdate)).days
        except ValueError:
            continue
        if 0 <= age <= MAX_FIRE_AGE_DAYS and (best is None or fdate > best[1]):
            best = (sym, fdate)
    return best


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    for sym, pos in held.items():
        b = bars.get(sym) or []
        if sessions_held(b, pos.get("entry_date")) >= HOLD_SESSIONS:
            out.append(Intent(
                kind="exit", symbol=sym, qty_hint=int(abs(float(pos["qty"]))),
                side="sell", position_intent="sell_to_close",
                price_hint=float(b[-1]["c"]) if b else None,
                reason="s_mn_moonshot exit: hold_complete_78_weeks no_stop"))
    if out or held:
        return out
    fire = _fresh_fire(context, context.session)
    if not fire:
        return out  # fail closed: no fresh upstream pick
    sym, fdate = fire
    b = bars.get(sym) or []
    if not b:
        return out
    if xstale_refused(context, "s_mn_moonshot", bars, sym):
        return out  # ENH20: pick's feed is dead; price is fiction
    px = float(b[-1]["c"])
    q = qty_for(BUDGET, px)
    if q > 0:
        out.append(Intent(
            kind="enter", symbol=sym, qty_hint=q, side="buy",
            position_intent="buy_to_open", price_hint=px, signal_date=fdate,
            reason=f"s_mn_moonshot entry: upstream_pick fire={fdate} weight=1pct"))
    return out
