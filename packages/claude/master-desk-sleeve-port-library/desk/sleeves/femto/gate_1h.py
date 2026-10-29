"""Gate 1H — lean-desk port. (A STRATEGY named 'Gate 1H'; not the
core chart gate.)

EXTRACTED from the old desk's gate_1h_sleeve.py. The gated daily event
(leader1d research frame: score >= 3 AND gate, >= 252 daily bars) is a
core Data product here (named misfit, ports/gate_1h.md); the 1H timing
logic — first RTH 1H bar strictly after the event date, 20-bar
de-overlap, 20-bar hold counted on the RTH 1H grid — is ported
verbatim. -25% disaster stop (2026-10-10 audit, Decision #18);
MAX_POSITIONS 10 (sleeve_core).

Old grid law (2026-10-07 HIGH fix): HOLD/DEOVERLAP bars count on the
RTH-only 1H grid (13:00-19:00Z bar starts); core Data must supply
RTH-filtered 1H bars in extra["bars_1h"] — the saved cache convention
keeps full bars, the signal read filters (core Data's job now).

Inputs via context.extra:
  "leader_events": {SYM: "YYYY-MM-DD"} (daily gated events)
  "bars_1h": {SYM: [RTH 1H bar dicts {"t","o","h","l","c","v"}]}
  "sleeve_state": {SYM: {"position": {"entry_px","entry_bar_t","qty"} | None}}
  "last_event": {SYM: "YYYY-MM-DD"}, "last_entry_bar": {SYM: t}
Bars (arg): daily dicts for the 42-name basket (SIVEF excluded by the
old basket reader; the core supplies the universe).
"""
from datetime import date, datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 20
DEOVERLAP_BARS = 20
MIN_BARS = 252
MAX_POSITIONS = 10
DISASTER_STOP = 0.25
COST_BPS_SIDE = 0.001

CONFIG = SleeveConfig(
    sleeve_id="gate_1h", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "last_event": "dict",
                  "last_entry_bar": "dict"},
    risk_pct=None)


def _h1_date(b):
    return datetime.fromtimestamp(float(b["t"]),
                                  tz=timezone.utc).date()


def first_bar_after(h1, event_date):
    """First 1H bar strictly after event_date — verbatim old logic
    (bar's UTC date > event date on the RTH grid)."""
    ev = date.fromisoformat(event_date)
    for i, b in enumerate(h1):
        if _h1_date(b) > ev:
            return i
    return None


# ---------------------------------------------------------------- master-desk: the old runtime, restored
from datetime import timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from . import sleeve_core as core  # noqa: E402

ET = ZoneInfo("America/New_York")


def _phase(context):
    """old crons: gate-1h-sleeve-fill hourly at :01 and gate-1h-sleeve-scan hourly at :15, 10:00-15:59 ET."""
    t = datetime.fromtimestamp(float(context.now), tz=ET)
    if t.weekday() >= 5 or not (10 <= t.hour <= 15):
        return None
    return "fill" if t.minute < 15 else "scan"


def _h1(extra):
    b = extra.get("bars_1h") or {}
    return b


def scan(context, meta, events, basket):
    """old mode_scan: for each basket name, its last-close daily gated event (deduped) -> the first RTH 1H bar
    strictly after the event date, 20-bar de-overlap from the previous entry bar; positions >= 20 1H bars past
    their entry bar are staged to sell; capacity as the leader law; exit backstop now + 4 days; entry bars
    staged with the buys. Returns (pending, last_event, last_entry_bar, signals)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    h1all = _h1(extra)
    book = core.book_of(state)
    last_ev = dict(meta.get("last_event") or {})
    last_eb = dict(meta.get("last_entry_bar") or {})
    signals = []
    for s in basket:
        r = (events or {}).get(s)
        if not r or not (int(r[1]) >= 3 and bool(r[2])):
            continue
        ev_date = r[0]
        if last_ev.get(s) == ev_date:
            continue
        h1 = h1all.get(s) or []
        if len(h1) < HOLD_BARS + 2:
            continue
        b0 = first_bar_after(h1, ev_date)
        if b0 is None:
            continue
        prev_bt = last_eb.get(s)
        if prev_bt is not None:
            prev_i = next((i for i, b in enumerate(h1) if float(b["t"]) == float(prev_bt)), None)
            if prev_i is not None and b0 - prev_i < DEOVERLAP_BARS:
                continue
        signals.append((s, ev_date, float(h1[b0]["t"])))
    sells = []
    for s, p in book.items():
        h1 = h1all.get(s) or []
        et = p.get("entry_bar_t")
        if et is None or not h1:
            continue
        ei = next((i for i, b in enumerate(h1) if float(b["t"]) >= float(et)), None)
        if ei is None:
            continue
        if len(h1) - 1 - ei >= HOLD_BARS:
            sells.append(s)
    old = dict(meta.get("pending") or {})
    surv = list(old.get("buys") or [])
    buys = []
    for s, ev_date, bar_t in signals:
        if s in book:
            last_ev[s] = ev_date
            last_eb[s] = bar_t
            continue
        if len(buys) + len(surv) + len(book) >= core.MAX_POSITIONS:
            break
        last_ev[s] = ev_date
        last_eb[s] = bar_t
        buys.append(s)
    today = datetime.fromtimestamp(float(context.now), tz=ET).date()
    exit_dates = dict(old.get("exit_dates") or {})
    exit_dates.update({s: (today + timedelta(days=4)).isoformat() for s in buys})
    entry_bars = dict(old.get("entry_bars") or {})
    entry_bars.update({s: t for s, _, t in signals})
    old_sells = list(old.get("sells") or [])
    pending = {"buys": core.merge_pending_buys(old.get("buys") or [], buys, len(book)),
               "sells": old_sells + [s for s in sells if s not in old_sells],
               "exit_dates": exit_dates, "entry_bars": entry_bars}
    return pending, last_ev, last_eb, signals


class Gate1H(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old two-phase hourly runtime — the :15 scan stages pending (next_meta), the :01
        fill executes it through the old sleeve_core fill law (10bp modeled, -25% disaster stop); each fill
        carries the staged entry bar the 20-bar hold counts from."""
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        pend = meta.get("pending") or {}
        close_ts = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                             microsecond=0).timestamp()
        em = {s: {"entry_bar_t": t} for s, t in (pend.get("entry_bars") or {}).items()}
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, pend,
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "gate_1h", close_ts,
                                           extra_meta=em, disaster_stop=DISASTER_STOP)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "scan":
        events = extra.get("leader_events_last")
        if events is not None:
            basket = list(extra.get("universe") or sorted(bars))
            pending, last_ev, last_eb, signals = scan(context, meta, events, basket)
            meta.update(pending=pending, last_event=last_ev, last_entry_bar=last_eb, last_signals=len(signals),
                        last_scan=float(context.now))
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "gate_1h")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return Gate1H().signal(bars, slice_state, context)
