"""Blowoff 1H (R4 transfer) — master-desk port of the old desk's blowoff_1h_sleeve.py.

KILLED in the old desk by ruling 2026-10-08 (TRADING_ENABLED = False: structurally adverse — it buys
exhaustion tops); ported here as a forward test, its law unchanged. Signal: blowoff rising edges
(blowoff_indices_vec — Wilder RSI(14) and OBV each >= trailing-144-bar min + 90% of range, first bar of each
run; vendored byte-identical) in the last 5 closed RTH 1H bars of each basket name, not the recorded signal
bar, de-overlapped >= 20 bars from it. LONG at the next fill (:40), hold 20 RTH 1H bars counted from the bar
after the signal bar, exit backstop + 4 days, 10bp modeled per side, no disaster stop. Scan hourly at :10,
fill at :40, 10:00-15:59 ET, through the old sleeve_core fill law.

Inputs via context.extra: "bars_1h" (RTH-grid 1H bars), "universe" (the basket), "meta", "quotes",
"sleeve_state"."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import sleeve_core as core
from .compat import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
HOLD_BARS = 20
DEOVERLAP_BARS = 20
MIN_BARS = 160
COST_BPS_SIDE = 0.001
FORMING_S = 65 * 60

CONFIG = SleeveConfig(sleeve_id="blowoff_1h", cadence_s=600, universe=(), state_schema={}, risk_pct=None)


def _phase(context):
    t = datetime.fromtimestamp(float(context.now), tz=ET)
    if t.weekday() >= 5 or not (10 <= t.hour <= 15):
        return None
    return "scan" if t.minute < 30 else "fill"


def _closed(bl, now):
    return [b for b in bl or () if float(b["t"]) + FORMING_S <= now]


def new_rising_edges(bl, last_sig_t, lookback=5):
    """old new_rising_edges on closed bars: [(index, bar_t)] in the last `lookback` bars, not the recorded
    signal bar."""
    if len(bl) < MIN_BARS:
        return []
    from ...feedlib import blowoff  # noqa: E402
    idx = blowoff.rising_edges([float(b["c"]) for b in bl], [float(b.get("v") or 0) for b in bl])
    if not idx:
        return []
    idx_set = set(idx)
    out = []
    for i in [i for i in idx if (i - 1) not in idx_set]:
        if i < len(bl) - lookback:
            continue
        t = float(bl[i]["t"])
        if last_sig_t is not None and t == float(last_sig_t):
            continue
        out.append((i, t))
    return out


def scan(context, meta, basket):
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    now = float(context.now)
    h1all = extra.get("bars_1h") or {}
    book = core.book_of(state)
    last_sb = dict(meta.get("last_signal_bar") or {})
    signals = []
    for s in basket:
        bl = _closed(h1all.get(s), now)
        if len(bl) < MIN_BARS:
            continue
        anchor_t = last_sb.get(s)
        anchor_i = None
        if anchor_t is not None:
            anchor_i = next((i for i, b in enumerate(bl) if float(b["t"]) == float(anchor_t)), None)
        for edge_i, sig_t in new_rising_edges(bl, anchor_t):
            if anchor_i is not None and edge_i - anchor_i < DEOVERLAP_BARS:
                continue
            signals.append((s, sig_t))
            anchor_i, anchor_t = edge_i, sig_t
        if anchor_t is not None:
            last_sb[s] = anchor_t
    sells = []
    for s, p in book.items():
        bl = h1all.get(s) or []
        et = p.get("entry_bar_t")
        if et is None or not bl:
            continue
        ei = next((i for i, b in enumerate(bl) if float(b["t"]) >= float(et)), None)
        if ei is not None and len(bl) - 1 - ei >= HOLD_BARS:
            sells.append(s)
    old = dict(meta.get("pending") or {})
    surv = list(old.get("buys") or [])
    buys = []
    for s, sig_t in signals:
        last_sb[s] = sig_t
        if s in book:
            continue
        if len(buys) + len(surv) + len(book) >= core.MAX_POSITIONS:
            break
        buys.append(s)
    today = datetime.fromtimestamp(now, tz=ET).date()
    exit_dates = dict(old.get("exit_dates") or {})
    exit_dates.update({s: (today + timedelta(days=4)).isoformat() for s in buys})
    sig_bars = dict(old.get("signal_bars") or {})
    sig_bars.update({s: t for s, t in signals})
    old_sells = list(old.get("sells") or [])
    pending = {"buys": core.merge_pending_buys(surv, buys, len(book)),
               "sells": old_sells + [s for s in sells if s not in old_sells],
               "exit_dates": exit_dates, "signal_bars": sig_bars}
    return pending, last_sb, signals


def entry_bar(bl, sig_t):
    """old stamp_entry_bars: the bar after the staged signal bar (else the latest bar)."""
    if not bl:
        return None
    if sig_t is not None:
        si = next((i for i, b in enumerate(bl) if float(b["t"]) == float(sig_t)), None)
        if si is not None:
            return float(bl[si + 1]["t"]) if si + 1 < len(bl) else float(bl[-1]["t"])
    return float(bl[-1]["t"])


class Blowoff1H(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        pend = meta.get("pending") or {}
        h1all = extra.get("bars_1h") or {}
        em = {s: {"entry_bar_t": entry_bar(h1all.get(s), t)} for s, t in (pend.get("signal_bars") or {}).items()}
        close_ts = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                             microsecond=0).timestamp()
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, pend,
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "blowoff_1h", close_ts,
                                           extra_meta=em)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "scan":
        basket = list(extra.get("universe") or sorted(bars))
        pending, last_sb, signals = scan(context, meta, basket)
        meta.update(pending=pending, last_signal_bar=last_sb, last_signals=len(signals), last_scan=float(context.now))
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "blowoff_1h")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return Blowoff1H().signal(bars, slice_state, context)
