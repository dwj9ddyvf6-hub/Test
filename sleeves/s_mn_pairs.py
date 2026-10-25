"""s_mn_pairs — Midna Pairs port (Lazarus batch 8).

Catalog rule (§4.2): Pairs, 1D, entry "Distance pairs: spread 2
standard deviations wide", exit "Spread reverts to mean", 3 slots,
$3,000. Reading (Gatev distance method): for each declared pair,
spread = log-price difference normalized over the trailing 60
sessions; |z| >= 2 opens a $1,000 pair ($500/leg): long the cheap
leg, short the rich leg. Exit both legs when |z| <= 0.25 (reverted
to mean). The catalog names no pairs; the desk pairs (same-sector
liquid large caps) are declared in PAIRS and recorded in the
fidelity ledger as a desk-chosen universe.
"""
from sleeves.laz8_common import Intent, SleeveConfig, held_positions, qty_for, xstale_refused

CONFIG = SleeveConfig(sleeve_id="s_mn_pairs", cadence_s=300,
                      state_schema={"position": "dict|None"})
PAIRS = (("KO", "PEP"), ("XOM", "CVX"), ("JPM", "BAC"))
LOOKBACK = 60
ENTRY_Z = 2.0
EXIT_Z = 0.25
PER_LEG = 500.0
MAX_PAIRS = 3


def spread_z(bars, a, b):
    import math
    ba, bb = bars.get(a) or [], bars.get(b) or []
    if len(ba) < LOOKBACK or len(bb) < LOOKBACK:
        return None
    da = {d: x for d, x in zip([str(int(x["t"])) for x in ba], ba)}
    spreads = []
    for x in bb[-LOOKBACK:]:
        y = da.get(str(int(x["t"])))
        if y is None:
            return None
        spreads.append(math.log(float(y["c"])) - math.log(float(x["c"])))
    if len(spreads) < LOOKBACK:
        return None
    m = sum(spreads) / len(spreads)
    var = sum((s - m) ** 2 for s in spreads) / len(spreads)
    sd = var ** 0.5
    if sd <= 0:
        # Constant spread: at its own mean (z=0) unless it jumped.
        return 0.0 if spreads[-1] == m else (99.0 if spreads[-1] > m else -99.0)
    return (spreads[-1] - m) / sd


def _leg(kind, sym, qty, side, pi, z, why):
    return Intent(kind=kind, symbol=sym, qty_hint=qty, side=side,
                  position_intent=pi,
                  reason=f"s_mn_pairs {why}: z={z:.2f}")


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    open_pairs = 0
    working = set()
    for a, b in PAIRS:
        z = spread_z(bars, a, b)
        if z is None:
            continue
        has_a, has_b = a in held, b in held
        if has_a and has_b:
            working.add((a, b))
            if abs(z) <= EXIT_Z:
                for sym in (a, b):
                    pos = held[sym]
                    q = int(abs(float(pos["qty"])))
                    pi = "buy_to_close" if float(pos["qty"]) < 0 else "sell_to_close"
                    out.append(_leg("exit", sym, q,
                                    "buy" if pi == "buy_to_close" else "sell",
                                    pi, z, "exit spread_reverted"))
            else:
                open_pairs += 1
        elif not has_a and not has_b:
            working.add((a, b))  # candidate below
    if open_pairs >= MAX_PAIRS:
        return out
    for a, b in PAIRS:
        if open_pairs >= MAX_PAIRS:
            break
        if a in held or b in held:
            continue
        z = spread_z(bars, a, b)
        if z is None or abs(z) < ENTRY_Z:
            continue
        if (xstale_refused(context, "s_mn_pairs", bars, a)
                or xstale_refused(context, "s_mn_pairs", bars, b)):
            continue  # ENH20: one leg's feed is dead; spread is fiction
        # spread = log(a) - log(b); z>0: a rich -> short a, long b.
        rich, cheap = (a, b) if z > 0 else (b, a)
        qr = qty_for(PER_LEG, float(bars[rich][-1]["c"]))
        qc = qty_for(PER_LEG, float(bars[cheap][-1]["c"]))
        if qr <= 0 or qc <= 0:
            continue
        open_pairs += 1
        out.append(_leg("enter", cheap, qc, "buy", "buy_to_open", z,
                        "entry distance_pair cheap_leg"))
        out.append(_leg("enter", rich, qr, "sell", "sell_to_open", z,
                        "entry distance_pair rich_leg"))
    return out
