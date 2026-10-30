"""Lazarus s_mn_hedge -- Midna port, QQQ->TZA hedge (v3-native).

Catalog SS5.2: QQQ-based hedge signal on -> buy TZA (3x inverse
small caps) at 30% weight (reading: 30% of this sleeve's $1,000
budget -- ledger LAZ-B7); exit when the hedge signal turns off or
after max 20 sessions. 1 slot. Source status Live."""
from laz_sleeves._common import (_bar_stale, _bars, _enh19_on, _intent,
                                 _journal19, _positions, _qty_for, _session,
                                 _sessions_held)

SLEEVE_ID = "s_mn_hedge"
INPUTS = ("bars_1day", "positions", "hedge_signal")
BUDGET_USD, WEIGHT, MAX_SESSIONS = 1000.0, 0.30, 20


def evaluate(view, ctx):
    sess = _session(view)
    if sess is None:
        return []
    out, held = [], _positions(view, SLEEVE_ID)
    bars = _bars(view, "TZA", "1Day")
    on = view.get("hedge_signal") is True
    for p in held:
        if not bars:
            continue
        last = float(bars[-1]["c"])
        if not on:
            out.append(_intent(SLEEVE_ID, "exit", "TZA",
                               abs(float(p["qty"])), last,
                               "mn_hedge_signal_off", sess))
        elif _sessions_held(bars, p.get("opened_at")) >= MAX_SESSIONS:
            out.append(_intent(SLEEVE_ID, "exit", "TZA",
                               abs(float(p["qty"])), last,
                               "mn_hedge_max20", sess))
    if held or not on or not bars:
        return out
    # ENH19 stale-bar gate: same class as s_cl_vmr_qqq -- a hedge
    # entry sized off a provably stale TZA close buys protection at a
    # print the market left days ago. ON default; exits untouched.
    if _enh19_on(view, SLEEVE_ID, "stale_gate") and _bar_stale(
            view, SLEEVE_ID, bars, sess):
        _journal19(view, {"exp_id": "ENH19-LAZB7-20261024",
            "sleeve": SLEEVE_ID, "symbol": "TZA",
            "enhanced": "refuse_stale_bar", "shadow_faithful": "enter",
            "last_bar": str(bars[-1].get("t"))[:10]})
        return out
    last = float(bars[-1]["c"])
    qty = _qty_for(BUDGET_USD * WEIGHT, last)
    if qty <= 0:
        return out
    out.append(_intent(SLEEVE_ID, "entry", "TZA", qty, last,
                       "mn_hedge_signal_on", sess))
    return out
