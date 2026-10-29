"""V-alertsify-5 - the overnight-versus-day split and the level track record.

Overnight / day: per name, from the daily bars, each session splits into the close-to-open gap (held overnight), the
open-to-close move (day only) and the close-to-close total (full). Over the last WINDOW sessions the three are
compounded, in percent. A pair whose close-to-close ratio falls outside [0.6, 1.6] reads as an unadjusted split or a
data fault and is counted in `skipped`, not used. Bars are the record's own: {"t": epoch, "o", "h", "l", "c"}.

Level track record: the hit rate of each shown wall or level kind, from the graded Map cards (wall_study.summarize):
call wall held, put wall held, the flip respected, and a touched wall that held; each with its n and a small-sample
flag. Nothing graded: no_data with the count of cards waiting."""
from .. import calendar as cal
from .stats import no_data

WINDOW = 60
MIN_SESSIONS = 20
RATIO = (0.6, 1.6)
SMALL_N = 30
MAX_NAMES = 20


def _iso(b):
    return cal._as_date(float(b["t"])).isoformat()


def split_sessions(bars, window=WINDOW):
    """-> (pairs used, skipped, overnight, day, full) as compounded percents over the last `window` sessions"""
    pairs = list(zip(bars, bars[1:]))[-window:]
    on = dy = fl = 1.0
    used = skipped = 0
    for p, b in pairs:
        pc, o, c = float(p["c"]), float(b["o"]), float(b["c"])
        if pc <= 0 or o <= 0 or not RATIO[0] <= c / pc <= RATIO[1]:
            skipped += 1
            continue
        on *= o / pc
        dy *= c / o
        fl *= c / pc
        used += 1
    pct = lambda v: round((v - 1.0) * 100, 2)          # noqa: E731
    return used, skipped, pct(on), pct(dy), pct(fl)


def overnight_day(daily, symbols, window=WINDOW, max_names=MAX_NAMES):
    rows, skipped = [], 0
    for s in list(symbols)[:max_names]:
        bars = sorted(daily.get(s) or [], key=lambda b: float(b["t"]))
        n, sk, on, dy, fl = split_sessions(bars, window)
        skipped += sk
        if n >= MIN_SESSIONS:
            rows.append({"symbol": s, "sessions": n, "overnight": on, "day": dy, "full": fl})
    if not rows:
        return no_data(f"no name with {MIN_SESSIONS} sessions of bars", window=window, skipped=skipped)
    k = len(rows)
    mean = lambda key: round(sum(r[key] for r in rows) / k, 2)          # noqa: E731
    return {"status": "ok", "window": window, "rows": rows, "skipped": skipped,
            "all": {"names": k, "overnight": mean("overnight"), "day": mean("day"), "full": mean("full")}}


KINDS = (("Call wall", "call_wall_held_rate"), ("Put wall", "put_wall_held_rate"),
         ("Flip", "flip_respected_rate"), ("Touched wall", "touched_and_held_rate"))


def level_track_record(grades, waiting=0):
    """grades = wall_study.grade_corpus output"""
    from ..morgue import wall_study
    if not grades:
        return no_data("no Map card has completed its grading session", cards_waiting=waiting)
    s = wall_study.summarize(grades)
    return {"status": "ok", "n": s["n"], "small_n": s["n"] < SMALL_N,
            "kinds": [{"kind": name, "rate": round(s[key], 3), "n": s["n"]} for name, key in KINDS]}


def level_record(root, daily):
    """the level track record from the morgue ledger's Map cards and the record's own daily bars"""
    from ..morgue import ledger as mledger
    from ..morgue import scorecards, wall_study
    rows = [r for r in mledger.read(root) if r.get("component") == "gex_static_v1"]
    if not rows:
        return no_data("no Map card in the ledger yet", cards_waiting=0)
    bars = {s: [{"t": _iso(b), "h": float(b["h"]), "l": float(b["l"]), "c": float(b["c"])} for b in v]
            for s, v in daily.items()}
    return level_track_record(wall_study.grade_corpus(rows, bars), waiting=len(scorecards.cards_of_record(rows)))
