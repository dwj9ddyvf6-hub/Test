"""Blowoff Daily (R4, down regime) — master-desk port of the old desk's blowoff_d_sleeve.py.

KILLED in the old desk by ruling 2026-10-08 (TRADING_ENABLED = False: the signal buys exhaustion tops);
ported here as a forward test, its law unchanged. Signal: a rising-edge daily BLOWOFF (rsiobv.scan_exhaustion,
RSI 14, 144-bar range, vendored byte-identical) on the latest closed bar, de-overlapped >= 20 sessions per
name, only while SPY's trailing-60-session return is <= 0 (B8). LONG at the next session's fill (10:30 ET),
exit staged once 19 bars have closed after entry (the 20th session), exit backstop rank + 28 days, 10bp
modeled per side, no disaster stop. Universe: the genome (>= 252 bars). Rank 16:30 ET after the close,
fill 10:30 ET through the old sleeve_core fill law.

Inputs via context.extra: "blowoff_events" (the genome job's last-close rows), "meta", "quotes",
"sleeve_state". Bars: the genome's daily bars (cache-only)."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import sleeve_core as core
from .compat import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
HOLD_BARS = 20
DEOVERLAP_BARS = 20
MIN_BARS = 252
COST_BPS_SIDE = 0.001
RANK_HM = (16, 30)
FILL_HM = (10, 30)

CONFIG = SleeveConfig(sleeve_id="blowoff_d", cadence_s=1800, universe=(), state_schema={}, risk_pct=None)


def _d(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat()


def spy_down_regime(spy_bars, asof):
    sc = [b for b in spy_bars or () if _d(b) <= asof]
    if len(sc) < 61:
        return None
    c0, c1 = float(sc[-61]["c"]), float(sc[-1]["c"])
    if not c0 or not c1:
        return None
    return (c1 / c0 - 1) <= 0


def _phase(context):
    t = datetime.fromtimestamp(float(context.now), tz=ET)
    if t.weekday() >= 5:
        return None
    if (t.hour, t.minute) >= RANK_HM:
        return "rank"
    if FILL_HM <= (t.hour, t.minute) < (16, 0):
        return "fill"
    return None


def rank(bars, context, meta, events):
    """old mode_rank (with entries enabled for the forward test)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    today = context.session
    book = core.book_of(state)
    last_sig = dict(meta.get("last_signal") or {})
    down = spy_down_regime(bars.get("SPY"), today)
    signals = []
    if down:
        for s in sorted(bars):
            if s == "SPY" or len(bars[s] or ()) < MIN_BARS:
                continue
            r = (events or {}).get(s)
            sig = r[1] if r and r[0] == today else None
            if not sig:
                continue
            prev = last_sig.get(s)
            if prev:
                sess = sorted(_d(b) for b in bars[s])
                try:
                    gap = sess.index(sig) - sess.index(prev)
                except ValueError:
                    gap = None
                if gap is not None and gap < DEOVERLAP_BARS:
                    continue
            signals.append((s, sig))
    sells = []
    for s, p in book.items():
        bl = bars.get(s) or []
        entry = str(p.get("entry_date") or "")[:10]
        if entry and bl and sum(1 for b in bl if _d(b) > entry) >= HOLD_BARS - 1:
            sells.append(s)
    old = dict(meta.get("pending") or {})
    surv = list(old.get("buys") or [])
    buys = []
    for s, sig in signals:
        last_sig[s] = sig
        if s in book:
            continue
        if len(buys) + len(surv) + len(book) >= core.MAX_POSITIONS:
            break
        buys.append(s)
    exit_dates = dict(old.get("exit_dates") or {})
    exit_dates.update({s: (date.fromisoformat(today) + timedelta(days=28)).isoformat() for s in buys})
    old_sells = list(old.get("sells") or [])
    pending = {"buys": core.merge_pending_buys(surv, buys, len(book)),
               "sells": old_sells + [s for s in sells if s not in old_sells], "exit_dates": exit_dates}
    return pending, last_sig, down, signals


class BlowoffD(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        close_ts = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                             microsecond=0).timestamp()
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "blowoff_d", close_ts)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "rank" and meta.get("last_rank_date") != context.session:
        events = extra.get("blowoff_events")
        if events is not None:
            pending, last_sig, down, signals = rank(bars, context, meta, events)
            meta.update(pending=pending, last_signal=last_sig, last_rank_date=context.session, spy_down_regime=down,
                        last_signals=len(signals))
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "blowoff_d")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return BlowoffD().signal(bars, slice_state, context)
