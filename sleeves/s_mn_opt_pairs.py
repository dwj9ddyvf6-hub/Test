"""s_mn_opt_pairs — Midna Opt Pairs port (Lazarus batch 8).

Catalog rule (§4.2): Options, 1D, Shadow, entry "Pairs traded with
listed options", exit "Spread reverts", $1,000.
Reading: the s_mn_pairs distance rule (60-session log-spread,
|z| >= 2) expressed in listed options — buy a put on the rich leg
and a call on the cheap leg (ATM-ish, 21-75 DTE, laz8_opt
selection), $500 of premium budget per leg; exit both legs
sell-to-close when |z| <= 0.25. Pairs are s_mn_pairs' PAIRS.
"""
from sleeves.laz8_common import Intent, SleeveConfig, held_positions, xstale_refused
from sleeves.laz8_opt import contracts_for, pick_option, underlying_of
from sleeves.s_mn_pairs import PAIRS, EXIT_Z, ENTRY_Z, spread_z

CONFIG = SleeveConfig(sleeve_id="s_mn_opt_pairs", cadence_s=300,
                      state_schema={"position": "dict|None"})
PER_LEG = 500.0


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    held_und = {}
    for occ in held:
        und = underlying_of(occ)
        if und:
            held_und[und] = occ
    active_pair = None
    for a, b in PAIRS:
        if a in held_und and b in held_und:
            active_pair = (a, b)
            z = spread_z(bars, a, b)
            if z is not None and abs(z) <= EXIT_Z:
                for und in (a, b):
                    occ = held_und[und]
                    out.append(Intent(
                        kind="exit", symbol=occ,
                        qty_hint=int(abs(float(held[occ]["qty"]))),
                        side="sell", position_intent="sell_to_close",
                        reason=f"s_mn_opt_pairs exit: spread_reverted z={z:.2f} occ={occ}"))
            break
    if out or active_pair:
        return out
    if held:
        return out
    for a, b in PAIRS:
        z = spread_z(bars, a, b)
        if z is None or abs(z) < ENTRY_Z:
            continue
        if (xstale_refused(context, "s_mn_opt_pairs", bars, a)
                or xstale_refused(context, "s_mn_opt_pairs", bars, b)):
            continue  # ENH20
        rich, cheap = (a, b) if z > 0 else (b, a)
        pk = pick_option(context, rich, float(bars[rich][-1]["c"]), "put")
        ck = pick_option(context, cheap, float(bars[cheap][-1]["c"]), "call")
        if not pk or not ck:
            continue
        np_ = contracts_for(PER_LEG, pk[1])
        nc = contracts_for(PER_LEG, ck[1])
        if np_ <= 0 or nc <= 0:
            continue
        out.append(Intent(
            kind="enter", symbol=ck[0], qty_hint=nc, side="buy",
            position_intent="buy_to_open",
            reason=f"s_mn_opt_pairs entry: cheap_leg_call underlying={cheap} occ={ck[0]} z={z:.2f}"))
        out.append(Intent(
            kind="enter", symbol=pk[0], qty_hint=np_, side="buy",
            position_intent="buy_to_open",
            reason=f"s_mn_opt_pairs entry: rich_leg_put underlying={rich} occ={pk[0]} z={z:.2f}"))
        break
    return out
