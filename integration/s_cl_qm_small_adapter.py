"""Lazarus s_cl_qm_small -- ChartsLector study lane (v3-native).

Catalog SS4.6: Qullamaggie-style breakout leaders in small caps:
close >= $5, breakout over the prior 20-session high, not
over-extended (close <= 1.25x the 20-session SMA), small-cap band
tag, with the QQQ-down house rule. No stop; time exit at 90
sessions. 8 slots x $1,000. Source status Live."""
from laz_sleeves._common import (_bars, _enh19_on, _intent, _journal19,
                                 _positions, _qqq_down, _qty_for, _session)

SLEEVE_ID = "s_cl_qm_small"
INPUTS = ("bars_1day", "positions", "alt_data")
SLOTS, SLOT_USD, HOLD_SESSIONS = 8, 1000.0, 90


def evaluate(view, ctx):
    sess = _session(view)
    if sess is None:
        return []
    out, held = [], _positions(view, SLEEVE_ID)
    held_syms = set()
    for p in held:
        sym = p["symbol"]
        held_syms.add(sym)
        bars = _bars(view, sym, "1Day")
        if bars and sum(1 for b in bars
                        if str(b.get("t"))[:10] > str(p.get("opened_at"))[:10]
                        ) >= HOLD_SESSIONS:
            out.append(_intent(SLEEVE_ID, "exit", sym, abs(float(p["qty"])),
                               float(bars[-1]["c"]), "cl_qm_time90", sess))
    if len(held) >= SLOTS or not _qqq_down(view):
        return out
    alt = view.get("alt_data") or {}
    bars_map = view.get("bars") or {}
    for key in sorted(bars_map):
        if not key.endswith("|1Day") or key == "QQQ|1Day":
            continue
        sym = key[:-5]
        if sym in held_syms:
            continue
        if (alt.get(sym) or {}).get("mcap_band") != "small":
            continue
        bars = bars_map[key]
        if len(bars) < 21:
            continue
        closes = [float(b["c"]) for b in bars]
        last = closes[-1]
        prior_high = max(float(b["h"]) for b in bars[-21:-1])
        sma20 = sum(closes[-21:-1]) / 20.0
        if last < 5.0 or last <= prior_high or last > 1.25 * sma20:
            continue
        qty = _qty_for(SLOT_USD, last)
        if qty <= 0:
            continue
        out.append(_intent(SLEEVE_ID, "entry", sym, qty, last,
                           "cl_qm_breakout", sess))
        # ENH19 slot-count cure: pre-change the break test used the
        # FIXED held count (len(held)+1), so with fewer than 8 held it
        # never fired and every qualifying breakout emitted (measured
        # 10 entries into 8 slots = $10k against the $8k book). ON
        # (default): count entries already emitted this pass; symbols
        # past the cap are the shadow-faithful overflow, journalled.
        if _enh19_on(view, SLEEVE_ID, "slot_guard"):
            if len(held) + sum(1 for i in out if i["kind"] == "entry") >= SLOTS:
                for key2 in sorted(bars_map):
                    if key2.endswith("|1Day") and key2 != "QQQ|1Day":
                        _journal19(view, {"exp_id": "ENH19-LAZB7-20261024",
                            "sleeve": SLEEVE_ID, "enhanced": "slot_cap_reached",
                            "shadow_faithful": "enter_overflow"})
                        break
                break
        elif len(held) + 1 >= SLOTS:
            break
    return out
