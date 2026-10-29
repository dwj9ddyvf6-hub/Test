"""The Ledger scorecards for Map and Board rows (fixed 1d / 5d / 21d grading).

Ported from Silicon's scorecards.py. Every figure is computed from the append-only ledger at run time (a number that cannot
be recomputed from the log does not ship). Outcomes are forward returns at fixed horizons from the logged session, never
the best moment in the window. A horizon with no matured rows renders the explicit not-yet-graded state with the date its
first grade lands, never a borrowed or blended figure.

Board rows: graded from the NEXT session's open (basis "next_open": the card publishes at the next preopen, so the
overnight gap is not a return anyone could trade), the horizon counted from that session; the close logged in the row is
kept for the "close" basis. Scorecard rows now carry basis; earlier rows (close-based) are never rewritten. Forward
returns use the desk's split-adjusted daily bars, completed sessions only.

Map cards: the card of record for a day is the LAST gex_static_v1 row per underlying per ET date. A card written before the
session's close grades against its own session, one written after against the next. Grading (declared): call wall held =
the session high never passed the call wall; touched = the high came within 0.2% of it; the put wall mirrored; flip
respected = the close stayed on the card-spot side of the zero-gamma level.

Changes from Silicon: the bars are the desk's cache (no second SIP download); 'before the close' is the session's real
close (an early close, and winter's 21:00 UTC), where Silicon used 20:00 UTC; the board cohorts are built from the rows the
page shows (the top 50), which are all logged."""
import statistics
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..util import ET
from . import ledger

HORIZONS = (1, 5, 21)
BASIS = "next_open"       # the board's grade basis: the card publishes at the next preopen, so the entry is the next session's
                          # open (rows graded before this field existed were close-based; the ledger is append-only)
BASES = ("close", "next_open")
TOUCH = 0.002


def dated(raw, now):
    """the hub's daily bars -> [{"t": ET date, "o","h","l","c","v"}] ascending, completed sessions only (a bar dated today
    is kept only once the close plus 20 minutes has passed)"""
    out = []
    for b in raw or []:
        try:
            d = cal._as_date(float(b["t"]))
            row = {"t": d.isoformat(), "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]), "c": float(b["c"]),
                   "v": float(b.get("v") or 0.0)}
        except (KeyError, TypeError, ValueError):
            continue
        if d >= cal._as_date(now) and now < cal.session_close(d) + 20 * 60:
            continue
        if out and row["t"] <= out[-1]["t"]:
            continue
        out.append(row)
    return out


def _bdate(bar):
    return bar["t"][:10]


def forward_returns(bars, as_of, close0, horizons=HORIZONS, basis="close"):
    """forward returns at fixed session horizons after `as_of` (ISO date). basis "close": from `close0`, the logged
    session's close, to the h-th later close. basis "next_open": from the open of the first session after `as_of` (what a
    reader of the next preopen card could trade) to the close of the h-th session counting that one as the first. An
    immature horizon reports the weekday date its first grade is expected"""
    if basis not in BASES:
        raise ValueError(f"unknown grade basis: {basis}")
    dates = [_bdate(b) for b in bars]
    closes = {d: b["c"] for d, b in zip(dates, bars)}
    opens = {d: b["o"] for d, b in zip(dates, bars)}
    after = [d for d in dates if d > as_of]
    out = {}
    for h in horizons:
        if len(after) >= h:
            d = after[h - 1]
            if basis == "next_open":
                out[h] = {"mature": True, "date": d, "ret": closes[d] / opens[after[0]] - 1.0, "basis": basis,
                          "entry_date": after[0]}
            else:
                out[h] = {"mature": True, "date": d, "ret": closes[d] / close0 - 1.0}
        else:
            need = h - len(after)
            d = date.fromisoformat(after[-1] if after else as_of)
            while need > 0:
                d += timedelta(days=1)
                if cal.is_trading_day(d):
                    need -= 1
            out[h] = {"mature": False, "expected": d.isoformat()}
    return out


def grade_map_row(row, bar):
    cw, pw, zg = row["call_wall"], row["put_wall"], row["zero_gamma"]
    return {"call_wall_touched": bar["h"] >= (1 - TOUCH) * cw, "call_wall_held": bar["h"] <= cw,
            "put_wall_touched": bar["l"] <= (1 + TOUCH) * pw, "put_wall_held": bar["l"] >= pw,
            "flip_respected": (bar["c"] - zg >= 0) == (row["spot"] - zg >= 0)}


def map_grading_date(ts_utc, session_dates):
    """the first session a card grades against: its own ET date when the card was written before that session's close,
    else the next; None while that session is not among the completed ones"""
    ts = datetime.fromisoformat(ts_utc.replace("Z", "+00:00"))
    epoch = ts.timestamp()
    card_date = ts.astimezone(ET).date()
    own = cal.is_trading_day(card_date) and epoch < cal.session_close(card_date)
    first = card_date if own else cal.next_trading_day(card_date)
    iso = first.isoformat()
    return iso if iso in session_dates else None


def summarize_horizon(rets, expected):
    if not rets:
        return {"state": "not_yet_graded", "n_mature": 0,
                "line": f"not yet graded: the first grades land after the {expected} close" if expected else "not yet graded"}
    pos = sum(1 for r in rets if r > 0) / len(rets)
    return {"state": "graded", "n_mature": len(rets), "hit_rate": pos, "mean": statistics.fmean(rets),
            "median": statistics.median(rets),
            "line": (f"{pos:.0%} positive, average {statistics.fmean(rets):+.2%}, median {statistics.median(rets):+.2%} "
                     f"(n={len(rets)})")}


def dedupe_paired(paired):
    """identical republications (same as-of session and inputs hash) count once"""
    seen, out = set(), []
    for r, as_of in paired:
        key = (as_of, r.get("inputs_hash"))
        if key in seen:
            continue
        seen.add(key)
        out.append((r, as_of))
    return out


def split_board_cohorts(rows):
    return {"published": list(rows), "qualified": [r for r in rows if r["value"].get("qualified")]}


def board_batches(rows):
    """pair the board rows with their batch summary's as-of session (the last summary logged before the row)"""
    summaries = sorted((r for r in rows if r.get("component") == "board-summary"), key=lambda r: r["ts_utc"])
    paired = []
    for r in (r for r in rows if r.get("component") == "board-row"):
        as_of = None
        for s in summaries:
            if s["ts_utc"] <= r["ts_utc"]:
                as_of = s["value"]["as_of_session"]
            else:
                break
        if as_of:
            paired.append((r, as_of))
    return paired


def cards_of_record(map_rows):
    """the last card per (underlying, ET date); the ledger is chronological, so the last wins"""
    rec = {}
    for r in map_rows:
        ts = datetime.fromisoformat(r["ts_utc"].replace("Z", "+00:00")).astimezone(ET).date().isoformat()
        rec[(r["underlying"], ts)] = r
    return rec


def compute(rows, bars, now):
    """the scorecard payload from the ledger rows and the completed daily bars {symbol: [dated bars]}"""
    paired = dedupe_paired(board_batches(rows))
    cohorts = {"published": [], "qualified": []}
    for r, as_of in paired:
        v = r["value"]
        fr = forward_returns(bars.get(v["symbol"], []), as_of, v["close"], basis=BASIS)
        cohorts["published"].append(fr)
        if v.get("qualified"):
            cohorts["qualified"].append(fr)
    board_sc = {}
    for name, items in cohorts.items():
        hs = {}
        for h in HORIZONS:
            rets = [it[h]["ret"] for it in items if it[h]["mature"]]
            exp = next((it[h]["expected"] for it in items if not it[h]["mature"]), None)
            hs[f"{h}d"] = dict(summarize_horizon(rets, exp), basis=BASIS)
        board_sc[name] = {"n_logged": len(items), "horizons": hs}
    of_record = cards_of_record([r for r in rows if r.get("component") == "gex_static_v1"])
    grades, pending = [], []
    for (sym, _), r in sorted(of_record.items()):
        dates = [_bdate(b) for b in bars.get(sym, [])]
        gd = map_grading_date(r["ts_utc"], dates)
        if gd is None:
            pending.append({"underlying": sym, "card_ts": r["ts_utc"]})
            continue
        bar = next(b for b in bars[sym] if _bdate(b) == gd)
        grades.append({"underlying": sym, "card_ts": r["ts_utc"], "session": gd, **grade_map_row(r, bar)})
    if grades:
        n = len(grades)
        map_sc = {"state": "graded", "cards_graded": n, "cards_pending": len(pending),
                  "call_wall_held_rate": sum(g["call_wall_held"] for g in grades) / n,
                  "put_wall_held_rate": sum(g["put_wall_held"] for g in grades) / n,
                  "touched_and_held": sum(1 for g in grades if (g["call_wall_touched"] and g["call_wall_held"])
                                          or (g["put_wall_touched"] and g["put_wall_held"])),
                  "flip_respected_rate": sum(g["flip_respected"] for g in grades) / n,
                  "line": f"{n} Map cards graded of {n + len(pending)} logged", "grades": grades}
    else:
        map_sc = {"state": "not_yet_graded", "cards_graded": 0, "cards_pending": len(pending),
                  "line": "not yet graded: the first grades land after a logged card's session closes", "grades": []}
    tape_n = sum(1 for r in rows if r.get("component") == "tape-alert")
    return {"generated_at": datetime.fromtimestamp(float(now), tz=timezone.utc).isoformat(), "board": board_sc,
            "map": map_sc,
            "counters": {"units_published": len(paired) + len(of_record) + tape_n, "board_rows_logged": len(paired),
                         "map_cards_of_record": len(of_record),
                         "units_graded": len(grades) + sum(1 for it in cohorts["published"]
                                                           if any(it[h]["mature"] for h in HORIZONS))},
            "paired_hashes": [r.get("inputs_hash") for r, _ in paired] + [r.get("inputs_hash") for r in of_record.values()],
            "grade_basis": BASIS,
            "labels": ["outcomes are forward returns at fixed horizons (1d, 5d, 21d), never the best moment in the window",
                       "board grades enter at the next session's open, the first price a reader of the preopen card can trade",
                       "a horizon with no matured rows says so, with the date its first grade lands",
                       "map grading: wall held = price never traded through it; touched = came within 0.2%; "
                       "flip respected = the close stayed on the card's side of the zero-gamma level"]}


def run(root, bars_raw, now):
    """compute from the ledger on disk and log the scorecard row (ledger-first) -> the payload. bars_raw: {symbol: the
    hub's daily bars}; only the ledger's symbols are needed."""
    rows = ledger.read(root)
    bars = {s: dated(b, now) for s, b in (bars_raw or {}).items()}
    card = compute(rows, bars, now)
    ledger.append(root, {"layer": "ledger", "component": "scorecard", "name": "map+board",
                         "value": {"board_rows": card["counters"]["board_rows_logged"],
                                   "map_cards": card["counters"]["map_cards_of_record"],
                                   "map_graded": card["map"]["cards_graded"],
                                   "board_1d_mature": card["board"]["published"]["horizons"]["1d"]["n_mature"],
                                   "basis": card["grade_basis"]},
                         "inputs_hash": ledger.inputs_hash(card["paired_hashes"]),
                         "grade": "the desk's scorer over the append-only record"}, now)
    return card


def symbols_needed(rows):
    """the symbols whose bars the scorecard needs: every logged board row and every Map underlying"""
    return sorted({r["name"] for r in rows if r.get("component") == "board-row"}
                  | {r["underlying"] for r in rows if r.get("component") == "gex_static_v1"})
