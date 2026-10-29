"""Wall validation as a research harness (Silicon's S4).

The research cut of the Map grades. The definitions are IMPORTED from scorecards.py (grade_map_row, map_grading_date),
never forked: a parity test asserts the harness's headline rates equal the scorecard's on the same corpus. Every figure is
recomputed from the append-only ledger at run time; while the record accrues, windows say not-yet-graded, never 0%.

Windows: the last 20 cards, the last 60, all. By underlying and by the sign of the net gamma on the card (the regime)."""
from . import scorecards
from .scorecards import cards_of_record, grade_map_row, map_grading_date

WINDOWS = (20, 60, None)


def grade_corpus(map_rows, bars_by_symbol):
    """every Map card of record whose grading session is complete -> its grade with the regime sign"""
    grades = []
    for (sym, _), r in sorted(cards_of_record(map_rows).items()):
        bars = bars_by_symbol.get(sym, [])
        gd = map_grading_date(r["ts_utc"], [b["t"][:10] for b in bars])
        if gd is None:
            continue
        bar = next(b for b in bars if b["t"][:10] == gd)
        grades.append({"underlying": sym, "card_ts": r["ts_utc"], "session": gd,
                       "net_gex_sign": "positive" if (r.get("net_gex_usd_per_1pct") or 0) >= 0 else "negative",
                       **grade_map_row(r, bar)})
    grades.sort(key=lambda g: g["card_ts"])
    return grades


def summarize(grades):
    if not grades:
        return {"state": "not_yet_graded", "n": 0}
    n = len(grades)
    touched_held = sum(1 for g in grades if (g["call_wall_touched"] and g["call_wall_held"])
                       or (g["put_wall_touched"] and g["put_wall_held"]))
    blown = sum(1 for g in grades if not g["call_wall_held"] or not g["put_wall_held"])
    return {"state": "graded", "n": n, "call_wall_held_rate": sum(g["call_wall_held"] for g in grades) / n,
            "put_wall_held_rate": sum(g["put_wall_held"] for g in grades) / n, "touched_and_held": touched_held,
            "touched_and_held_rate": touched_held / n, "blown_through": blown, "blown_through_rate": blown / n,
            "flip_respected_rate": sum(g["flip_respected"] for g in grades) / n}


def wall_validation(map_rows, bars_by_symbol):
    grades = grade_corpus(map_rows, bars_by_symbol)
    total = len(cards_of_record(map_rows))
    if not grades:
        return {"state": "not_yet_graded", "cards_of_record": total, "cards_graded": 0,
                "line": f"not yet graded: {total} Map card(s) of record accrued; grades land after their sessions complete",
                "windows": {}, "by_underlying": {}, "by_regime": {}}
    windows = {("all" if w is None else str(w)): summarize(grades if w is None else grades[-w:]) for w in WINDOWS}
    by_u, by_r = {}, {}
    for g in grades:
        by_u.setdefault(g["underlying"], []).append(g)
        by_r.setdefault(g["net_gex_sign"], []).append(g)
    return {"state": "graded", "cards_of_record": total, "cards_graded": len(grades), "windows": windows,
            "by_underlying": {k: summarize(v) for k, v in sorted(by_u.items())},
            "by_regime": {k: summarize(v) for k, v in sorted(by_r.items())}, "grades": grades,
            "line": f"{len(grades)} of {total} Map cards graded"}


__all__ = ["wall_validation", "grade_corpus", "summarize", "scorecards"]
