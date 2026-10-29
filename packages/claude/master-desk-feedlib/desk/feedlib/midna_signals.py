"""Midna's daily signal producers, run by the engine instead of as detached scripts:

  quantpedia  scripts/quantpedia-signals.py (blob 8d2b1184, vendored desk/vendor/midna/quantpedia_signals.py):
              faber_row / reversal_row / pairs_of executed as is over Yahoo daily prices (adjclose, else close) of
              FABER + LARGE, range 2y, sessions before today; main()'s assembly (asOf = the newest last day; faber in
              FABER order; reversal sorted by return; pairs over LARGE) reproduced here without its file write
  board       scripts/board-signals.py (blob e3efe1ad, vendored desk/vendor/midna/board_signals.py): bar_for
              executed as is over the swing basket's Yahoo daily rows (date, high, low, close, volume; range 1y), its
              clock (datetime.now in New York, which drops a bar dated today) set to the pass; asOf = the most common
              last day (main()'s max(set(days), key=days.count)); bars of that day only

Named divergences (plumbing): the source wrote quantpedia-signals.json / board-signals.json from a detached process
the desk pass kicked whenever the file's asOf was not the last completed session (so a session's signals appeared
after midnight New York, when its bar stopped being "today"); here the same functions run inside the pass on the desk's
Yahoo daily bars (BarCache) — the same rows on the same clock. The desk provider drops a Yahoo row without an
open/high/low (the scripts kept a close-only row); range=2y / 1y are reproduced as the sessions dated after the same
calendar day two / one years before the pass."""
import contextlib
from datetime import date, datetime

from ..sleeves.midna import common as M
from ..util import ET
from ..vendor.midna import board_signals as B
from ..vendor.midna import quantpedia_signals as Q
from .midna_panel import swing_universe, ymd_of


def _start(now, years):
    d = date.fromisoformat(M.et_ymd(now))
    try:
        return date(d.year - years, d.month, d.day).isoformat()
    except ValueError:
        return date(d.year - years, d.month, 28).isoformat()


def qp_rows(desk_bars, now):
    """fetch()'s rows [(day, adjclose or close)] for sessions before today, inside the 2y range."""
    today, start = M.et_ymd(now), _start(now, 2)
    rows = []
    for b in desk_bars or []:
        price = b.get("ac") or b.get("c")
        if not price or price <= 0:
            continue
        day = ymd_of(b["t"])
        if day >= today or day <= start:
            continue
        rows.append((day, float(price)))
    return rows


def qp_signals(series):
    """quantpedia-signals.py main() assembly over {sym: rows}."""
    as_of = max((rows[-1][0] for rows in series.values()), default=None)
    return {"asOf": as_of,
            "faber": [row for sym in Q.FABER if (row := Q.faber_row(sym, series.get(sym, [])))],
            "reversal": sorted([row for sym in Q.LARGE if (row := Q.reversal_row(sym, series.get(sym, [])))],
                               key=lambda row: row["ret"]),
            "pairs": Q.pairs_of({sym: [price for _day, price in series[sym]] for sym in Q.LARGE if sym in series})}


def build_qp(hub, now):
    syms = list(Q.FABER) + list(Q.LARGE)
    got = hub.bars("yahoo", "1d", syms, 560)
    series = {}
    for sym in syms:
        rows = qp_rows(got.get(sym), now)
        if rows:
            series[sym] = rows
    return qp_signals(series)


def board_rows(desk_bars, now):
    """fetch()'s rows (day, high, low, close, volume) inside the 1y range (bar_for drops today itself)."""
    start = _start(now, 1)
    rows = []
    for b in desk_bars or []:
        h, l, c, v = b.get("h"), b.get("l"), b.get("c"), b.get("v")
        if not (h and l and c and h > 0 and l > 0 and c > 0):
            continue
        day = ymd_of(b["t"])
        if day <= start:
            continue
        rows.append((day, float(h), float(l), float(c), float(v or 0)))
    return rows


class _Clock(datetime):
    NOW = None

    @classmethod
    def now(cls, tz=None):
        return datetime.fromtimestamp(cls.NOW, tz=tz or ET)


@contextlib.contextmanager
def board_clock(now):
    """bar_for reads datetime.now(ET) for 'today': run it on the pass clock."""
    saved = B.datetime
    _Clock.NOW = float(now)
    B.datetime = _Clock
    try:
        yield
    finally:
        B.datetime = saved


def board_signals(rows_by_sym, now):
    """board-signals.py main() over {sym: rows} in basket order."""
    found = []
    with board_clock(now):
        for sym, rows in rows_by_sym.items():
            fact = B.bar_for(rows)
            if not fact:
                continue
            found.append((sym, fact[0], fact[1]))
    days = [day for _sym, day, _fact in found]
    as_of = max(set(days), key=days.count) if days else None
    return {"asOf": as_of, "bars": [{"sym": sym, **fact} for sym, day, fact in found if day == as_of]}


def build_board(hub, now):
    syms = swing_universe()
    got = hub.bars("yahoo", "1d", syms, 300)
    return board_signals({s: board_rows(got.get(s), now) for s in syms}, now)


def feed_qp(feeds, sleeve, now, arg=None):
    return build_qp(feeds.hub, now)


def feed_board(feeds, sleeve, now, arg=None):
    return build_board(feeds.hub, now)
