"""master-desk: the old leader sleeves' shared rank law (leader_d_sleeve / leader_sc_sleeve mode_rank), pure.

  signals   each candidate (sorted) with >= 252 bars whose latest closed bar is a gated leader event
            (score >= 3 and gate, from the genome job's frame rows) and not its last recorded event
  sells     held positions with >= 19 bars after the entry date (fills land next morning: the 20th session)
  buys      signals not held, until staged + surviving + held reach 10; a held signal only refreshes the
            dedupe; exit backstop today + int(20 x 1.45) + 3 days; merged into the surviving pending"""
from datetime import date, datetime, timedelta, timezone

from . import sleeve_core as core

HOLD_BARS = 20
MIN_BARS = 252


def _date(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat()


def sell_due(bars, entry_date):
    if not entry_date or not bars:
        return False
    return sum(1 for b in bars if _date(b) > entry_date) >= HOLD_BARS - 1


def rank(bars, state, meta, events, today, candidates):
    book = core.book_of(state)
    last_ev = dict(meta.get("last_event") or {})
    old = dict(meta.get("pending") or {})
    signals = []
    for s in sorted(candidates):
        if len(bars.get(s) or ()) < MIN_BARS:
            continue
        r = (events or {}).get(s)
        if not r or r[0] != today or not (int(r[1]) >= 3 and bool(r[2])):
            continue
        if last_ev.get(s) == r[0]:
            continue
        signals.append((s, r[0]))
    sells = [s for s, p in book.items() if p.get("entry_date") and sell_due(bars.get(s) or [], str(p["entry_date"])[:10])]
    surv = list(old.get("buys") or [])
    buys = []
    for s, ev in signals:
        if s in book:
            last_ev[s] = ev
            continue
        if len(buys) + len(surv) + len(book) >= core.MAX_POSITIONS:
            break
        last_ev[s] = ev
        buys.append(s)
    exit_dates = {s: (date.fromisoformat(today) + timedelta(days=int(HOLD_BARS * 1.45) + 3)).isoformat()
                  for s in buys}
    merged = dict(old.get("exit_dates") or {})
    merged.update(exit_dates)
    old_sells = list(old.get("sells") or [])
    pending = {"buys": core.merge_pending_buys(surv, buys, len(book)),
               "sells": old_sells + [s for s in sells if s not in old_sells], "exit_dates": merged}
    return pending, last_ev, signals
