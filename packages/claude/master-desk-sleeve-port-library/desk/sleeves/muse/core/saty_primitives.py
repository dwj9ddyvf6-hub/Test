"""SATY PORT — shared Pine-parity math primitives (SPEC §4) and
the compression rule (SPEC §7.1, corrected 2026-10-21).

Clean-room desk port of the Saty Mahajan indicator stack, built
from ~/workspace/opt/rea-teardowns/saty-stack/SPEC.md against the
five verbatim originals in that folder's source/. Pure functions,
no I/O, no data fetching: bars arrive as dicts from the caller
(Alpaca SIP is the desk's only lawful source for these series —
see SPEC §2; this module never fetches anything).

Pine-parity definitions (SPEC §4 — the traps live here):
- EMA(n): alpha = 2/(n+1), seeded with the first non-None input
  (Pine ta.ema semantics). NOT masked until bar n-1.
- RMA(n): Wilder smoothing, alpha = 1/n, seeded with the SMA of
  the first n values; None before the seed bar. (pandas
  ewm(alpha=1/n, adjust=False) matches the recursion but NOT the
  seed — the seed is implemented explicitly.)
- ATR(n) = RMA(true range, n); first bar TR = H - L.
- Stdev(n): POPULATION standard deviation (divide by N; Pine
  ta.stdev default biased=true). pandas .std() defaults to
  ddof=1 and is wrong here by sqrt(n/(n-1)) on every value —
  trap T1 in tests/test_saty_traps_20261021.py.

None convention: a series value is None until its inputs exist
(ATR before bar n-1, stdev before a full window). EMA is numeric
from the first input per the Pine seed rule; consumers gate
trust on the warmed_up flags in core/saty_indicators.py, never
on None-ness of an EMA.
"""


def ema_series(values, length):
    """Pine ta.ema: alpha = 2/(length+1); seed = first non-None
    input; a None input yields None and re-seeds at the next
    non-None input (Pine na propagation)."""
    alpha = 2.0 / (length + 1)
    out = []
    state = None
    for v in values:
        if v is None:
            out.append(None)
            state = None
            continue
        state = v if state is None else alpha * v + (1.0 - alpha) * state
        out.append(state)
    return out


def sma_series(values, length):
    """Plain SMA; None until `length` consecutive non-None inputs
    exist, and None again after any gap until the window refills."""
    out = []
    window = []
    for v in values:
        window.append(v)
        if len(window) > length:
            window.pop(0)
        if len(window) == length and all(x is not None for x in window):
            out.append(sum(window) / length)
        else:
            out.append(None)
    return out


def rma_series(values, length):
    """Pine ta.rma: seed = SMA of the first `length` values at
    index length-1; then alpha = 1/length Wilder recursion.
    None before the seed bar."""
    out = [None] * len(values)
    if len(values) < length:
        return out
    seed = sum(values[:length]) / length
    out[length - 1] = seed
    alpha = 1.0 / length
    prev = seed
    for i in range(length, len(values)):
        prev = alpha * values[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def true_range_series(bars):
    """TR_t = max(H-L, |H-C_prev|, |L-C_prev|); first bar H-L.
    Bars are dicts with high/low/close keys."""
    out = []
    prev_close = None
    for b in bars:
        h, l, c = b["high"], b["low"], b["close"]
        if prev_close is None:
            tr = h - l
        else:
            tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        out.append(tr)
        prev_close = c
    return out


def atr_series(bars, length=14):
    """Pine ta.atr(length) = RMA(true range, length), SMA-seeded.
    Trap T2: a naive ewm seeded with TR_0 diverges from bar 0."""
    return rma_series(true_range_series(bars), length)


def stdev_series(values, length=21):
    """Pine ta.stdev(values, length) with the default biased=true:
    POPULATION standard deviation (divide by N) over the trailing
    window; None until a full window of non-None values exists.
    Trap T1: sample stdev (ddof=1) inflates every value by
    sqrt(length/(length-1))."""
    out = []
    for i in range(len(values)):
        if i + 1 < length:
            out.append(None)
            continue
        window = values[i + 1 - length:i + 1]
        if any(x is None for x in window):
            out.append(None)
            continue
        mean = sum(window) / length
        var = sum((x - mean) ** 2 for x in window) / length
        out.append(var ** 0.5)
    return out


def compression_rule(close, pivot, sd, atr, comp_prev):
    """SPEC §7.1 compression — the original's STATELESS per-bar
    rule (corrected 2026-10-21; the latch in the first teardown
    draft does not exist in either original — PO lines 97-103,
    Pro lines 173-179 re-initialize the tracker every bar).

    Returns (state, comp) where state is True/False, or
    (None, None) when any input is missing. `comp_prev` is the
    previous bar's metric — the rule's ONLY use of history
    (the expansion comparison). The state itself holds no
    memory: comp > 0 turns it off the same bar, and a rising
    metric inside the 1.854-2.0 ATR window turns it off early
    while comp is still <= 0.

    Side formulas as written in the originals; both sides reduce
    to comp = W - 2A and in_exp = W - 1.854A with W = 2*sd."""
    if close is None or pivot is None or sd is None or atr is None:
        return None, None
    width = 2.0 * sd
    if close >= pivot:  # UPPER side
        comp = (pivot + width) - (pivot + 2.0 * atr)
        in_exp = (pivot + width) - (pivot + 1.854 * atr)
    else:  # LOWER side
        comp = (pivot - 2.0 * atr) - (pivot - width)
        in_exp = (pivot - 1.854 * atr) - (pivot - width)
    expansion = comp_prev is not None and comp_prev <= comp
    state = (comp <= 0) and not (expansion and in_exp > 0)
    return state, comp
