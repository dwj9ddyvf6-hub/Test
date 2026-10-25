"""s_mn_opt_turtle — Midna Opt Turtle port (Lazarus batch 8).

Catalog rule (§4.2): Options, 1D, Shadow, entry "Turtle breakout
traded with listed options", exit "Turtle exit", $1,000.
Reading: the underlying Turtle rule (catalog s_mn_turtle row:
20- or 55-day high breakouts; 2-ATR stop or 10-day low) expressed
in listed options — on a breakout buy an ATM-ish call 21-75 DTE
(selection in laz8_opt); exits sell-to-close when the underlying
prints the Turtle exit (close below the prior 10-day low, or close
at/below entry-day close - 2xATR14). One position (catalog slots=1).
"""
from sleeves.laz8_common import (Intent, SleeveConfig, atr, closes,
                                  held_positions, xstale_refused)
from sleeves.laz8_opt import contracts_for, pick_option, underlying_of

CONFIG = SleeveConfig(sleeve_id="s_mn_opt_turtle", cadence_s=300,
                      state_schema={"position": "dict|None"})
BUDGET = 1000.0


def _breakout(b):
    if len(b) < 56:
        return False
    c = closes(b)
    return c[-1] > max(c[-21:-1]) or c[-1] > max(c[-56:-1])


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    for occ, pos in held.items():
        und = underlying_of(occ)
        b = bars.get(und) or [] if und else []
        if len(b) < 15:
            continue
        c = closes(b)
        exit_why = None
        if c[-1] < min(c[-11:-1]):
            exit_why = "10day_low"
        else:
            entry_date = str(pos.get("entry_date") or "")[:10]
            from sleeves.laz8_common import bar_dates
            dates = bar_dates(b)
            a = atr(b)
            if entry_date in dates and a:
                entry_close = c[dates.index(entry_date)]
                if c[-1] <= entry_close - 2 * a:
                    exit_why = "2atr_stop"
        if exit_why:
            out.append(Intent(
                kind="exit", symbol=occ, qty_hint=int(abs(float(pos["qty"]))),
                side="sell", position_intent="sell_to_close",
                reason=f"s_mn_opt_turtle exit: turtle_exit {exit_why} occ={occ}"))
    if out or held:
        return out
    for sym in sorted(bars):
        b = bars[sym]
        if not _breakout(b):
            continue
        if xstale_refused(context, "s_mn_opt_turtle", bars, sym):
            continue  # ENH20
        spot = float(b[-1]["c"])
        picked = pick_option(context, sym, spot, "call")
        if not picked:
            continue
        occ, ask = picked
        n = contracts_for(BUDGET, ask)
        if n <= 0:
            continue
        out.append(Intent(
            kind="enter", symbol=occ, qty_hint=n, side="buy",
            position_intent="buy_to_open", price_hint=spot,
            reason=f"s_mn_opt_turtle entry: turtle_breakout underlying={sym} occ={occ} ask={ask:.2f}"))
        break
    return out
