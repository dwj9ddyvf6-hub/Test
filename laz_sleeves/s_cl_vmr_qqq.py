"""Lazarus s_cl_vmr_qqq -- ChartsLector study lane (v3-native).

Catalog SS4.6: the VIX Mood Ring fear gauge at 35 or lower buys QQQ
(market intent priced off the last close; the source's next-open fill
is the dispatcher's first print). No stop; time exit at 5 sessions.
1 slot x $1,000. Source status Live."""
from laz_sleeves._common import (_bar_stale, _bars, _enh19_on, _intent,
                                 _journal19, _positions, _qty_for, _session,
                                 _sessions_held)

SLEEVE_ID = "s_cl_vmr_qqq"
INPUTS = ("bars_1day", "positions", "vix")
SLOT_USD, HOLD_SESSIONS, VIX_MAX = 1000.0, 5, 35.0


def evaluate(view, ctx):
    sess = _session(view)
    if sess is None:
        return []
    out, held = [], _positions(view, SLEEVE_ID)
    bars = _bars(view, "QQQ", "1Day")
    for p in held:
        if bars and _sessions_held(bars, p.get("opened_at")) >= HOLD_SESSIONS:
            out.append(_intent(SLEEVE_ID, "exit", "QQQ",
                               abs(float(p["qty"])), float(bars[-1]["c"]),
                               "cl_vmr_time5", sess))
    if held or not bars:
        return out
    vix = view.get("vix")
    try:
        vix_f = float(vix) if vix is not None else None
    except (TypeError, ValueError):
        # CURE2-2: a non-scalar vix payload (producer shape not yet the
        # sanctioned Yahoo ^VIX close) means NO reading — fail closed,
        # never crash the evaluation.
        return out
    if vix_f is None or vix_f > VIX_MAX:
        return out
    # ENH19 stale-bar gate: pre-change the entry sized off the last
    # QQQ close regardless of age -- a stale snapshot (producer lag /
    # holiday gap) bought at a days-old print while the fill prints
    # current. ON (default): refuse entry when the decision bar is
    # >4 calendar days before the session; exits untouched.
    if _enh19_on(view, SLEEVE_ID, "stale_gate") and _bar_stale(
            view, SLEEVE_ID, bars, sess):
        _journal19(view, {"exp_id": "ENH19-LAZB7-20261024",
            "sleeve": SLEEVE_ID, "symbol": "QQQ",
            "enhanced": "refuse_stale_bar", "shadow_faithful": "enter",
            "last_bar": str(bars[-1].get("t"))[:10]})
        return out
    last = float(bars[-1]["c"])
    qty = _qty_for(SLOT_USD, last)
    if qty <= 0:
        return out
    out.append(_intent(SLEEVE_ID, "entry", "QQQ", qty, last,
                       "cl_vmr_vix_le35", sess))
    return out
