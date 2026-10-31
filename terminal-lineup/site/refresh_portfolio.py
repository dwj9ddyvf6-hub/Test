#!/usr/bin/env python3
"""Refresh the Portfolio Builder data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever.

Evidence class: a single dated snapshot of scored stocks: the
freshest scored trading day on record, whose own summary declares
its totals (how many names were checked, scored, left unscored for
too little data, and how many passed every check), cross-checked
against the full ranked list for that same day, against the board
card published from it, and against the permanent log entry that
records when that day's board was published. Each name's sector
comes from the same published constituent map the board itself
uses, proven against the board card before it is trusted.

Reconstruction choices: the construction follows the published
sector portfolio construction this tool is built from (rank
sectors by the average score of their passing names, take the top
5 sectors, take up to the top 5 names in each by score, weight
every member equally), with three choices that are ours, stated
here: (1) "passing" means the names this snapshot itself marks as
having passed every check, because the snapshot carries no separate
risk grade or trading-volume average for the construction's own
published pass filter, and those numbers are not invented; (2) a
sector with fewer than five passing names contributes only the
names it has, never a substitute from another sector; (3) names
tied on score keep the order the snapshot itself gave them. The
7-day freshness limit and the completeness gate are the adopted
gates for this tool: selection is refused on a snapshot more than
7 days old, and refused on a snapshot whose totals are not
declared. Snapshot age is measured from the snapshot's trading day
to the freshest date the permanent record itself carries, so the
verdict comes from the sources, never from the clock, and running
this script twice produces the same file.

Scope: The weights are the
construction rule's weights, shown so anyone can check them.
Membership is never carried past the last snapshot: the basket is
rebuilt only when a new snapshot that passes every check exists,
and if the freshest snapshot fails a gate, no basket is shown from
it at all.

What the sources carry (and what this script therefore shows):
- The scored day: every name checked, its closing price, its
  combined score out of 100, and whether it passed every check.
- The day's own declared totals, which the refresh recomputes from
  the full list; any disagreement is a hard stop and nothing is
  published (the script exits with the mismatch named).
- The moment the day's board was published, from the permanent log.

Gate behaviour:
- Age gate: if the snapshot's trading day is more than 7 days
  before the freshest date in the permanent record, the script
  publishes a refusal file: the gate verdicts and the reason, and
  no members.
- Completeness gate: if the snapshot does not declare its totals,
  the script publishes the same kind of refusal file. If totals
  are declared but the full list disagrees with them, that is a
  contradiction in the record itself, so the script fails closed
  and publishes nothing.

Usage: python3 refresh_portfolio.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "board_card.json")
FULL_PATH = os.path.join(SOURCE_DIR, "board_full.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
GICS_PATH = os.path.expanduser(
    "~/workspace/femto-lean/config/gics_sectors.json")
OUT_PATH = os.path.join(HERE, "portfolio-builder", "data.json")

AGE_LIMIT_DAYS = 7
TOP_SECTORS = 5
PER_SECTOR = 5

SOURCE_WORDS = (
    "Daily price and trading history for each stock, plus public "
    "filings on the positions big investors report, combined into "
    "the same eight checks for every name; each name's sector "
    "comes from the published lists of the stocks that make up "
    "the big indexes"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fail(message):
    print(f"Portfolio refresh: {message}", file=sys.stderr)
    return 1


def write_data(data):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def build():
    for path in (CARD_PATH, FULL_PATH, LOG_PATH, GICS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    log_rows = load_log(LOG_PATH)
    gics = load_json(GICS_PATH).get("symbols", {})

    summary = card.get("summary") or {}
    session = summary.get("as_of_session") or full.get("as_of_session")
    if not session:
        return fail("the snapshot names no trading day; refusing "
                    "to publish a basket without its day.")
    if full.get("as_of_session") != session:
        return fail(f"the full list is for {full.get('as_of_session')} "
                    f"but the board card is for {session}; refusing "
                    "to publish a mismatched page.")

    # --- When was this session's board published? From the log. ---
    published_at = None
    for r in log_rows:
        if r.get("component") == "board-summary" and \
                r.get("value", {}).get("as_of_session") == session:
            if published_at is None or r["ts_utc"] > published_at:
                published_at = r["ts_utc"]
    if published_at is None:
        return fail(f"the log holds no board publication for session "
                    f"{session}; refusing to show a basket without a "
                    "publication time.")

    # The freshest date the permanent record itself carries: the
    # reference the age gate is measured against (never the clock).
    reference_date = max(r["ts_utc"][:10] for r in log_rows)
    age_days = (date.fromisoformat(reference_date)
                - date.fromisoformat(session)).days

    # --- The two adopted gates. ---
    declared_keys = ("universe", "scored", "insufficient_data",
                     "qualified")
    completeness_declared = all(
        isinstance(summary.get(k), int) for k in declared_keys)
    age_ok = age_days <= AGE_LIMIT_DAYS

    gates = [
        {
            "name": "Fresh enough",
            "passed": age_ok,
            "detail": (
                f"The snapshot is from {session}, {age_days} day"
                f"{'' if age_days == 1 else 's'} before the newest "
                f"date in the record ({reference_date}). The limit "
                f"is {AGE_LIMIT_DAYS} days."
                if age_ok else
                f"The snapshot is from {session}, {age_days} days "
                f"before the newest date in the record "
                f"({reference_date}). That is older than the "
                f"{AGE_LIMIT_DAYS}-day limit, so no basket is built "
                "from it."),
        },
        {
            "name": "Complete and declared",
            "passed": completeness_declared,
            "detail": (
                "The snapshot declares its own totals: how many "
                "names were checked, scored, left unscored, and how "
                "many passed every check."
                if completeness_declared else
                "The snapshot does not declare its own totals, so "
                "there is no way to prove it is complete. No basket "
                "is built from an undeclared snapshot."),
        },
    ]

    base = {
        "tool": "Portfolio Builder",
        "session": session,
        "published_at_utc": published_at,
        "source": SOURCE_WORDS,
        "gates": gates,
        "age_limit_days": AGE_LIMIT_DAYS,
        "age_days": age_days,
    }

    if not (age_ok and completeness_declared):
        reasons = [g["name"] + ": " + g["detail"]
                   for g in gates if not g["passed"]]
        data = dict(base)
        data.update({
            "status": "cannot_build",
            "refusal_reasons": reasons,
            "counts": {"members": 0},
            "members": [],
            "sector_mix": [],
        })
        write_data(data)
        print(f"Wrote {OUT_PATH} (refusal: snapshot {session} failed "
              f"a gate; no members published)")
        return 0

    # --- Declared totals must agree with the full list, exactly.
    # A disagreement is a contradiction in the record: fail closed.
    full_rows = full["rows"]
    scored = [r for r in full_rows if not r.get("insufficient_data")]
    recomputed = {
        "universe": len(full_rows),
        "scored": len(scored),
        "insufficient_data": len(full_rows) - len(scored),
        "qualified": sum(1 for r in scored if r["qualified"]),
    }
    for key, value in recomputed.items():
        if summary.get(key) != value:
            return fail(f"the board card summary says {key}="
                        f"{summary.get(key)} but the full list holds "
                        f"{value}; refusing to publish a mismatched "
                        "page.")
    published_rows = card["board"]
    top = scored[:len(published_rows)]
    for got, want in zip(published_rows, top):
        if (got["symbol"], got["score"], got["qualified"]) != \
                (want["symbol"], want["score"], want["qualified"]):
            return fail(f"the card's published names do not match "
                        f"the top of the full list at {got['symbol']}; "
                        "refusing to publish a mismatched page.")

    # --- Prove the sector map against the card before trusting it
    # for names the card does not publish. ---
    for row in published_rows:
        entry = gics.get(row["symbol"]) or {}
        if entry.get("sector") != row.get("sector"):
            return fail(f"the sector list gives {row['symbol']} the "
                        f"sector {entry.get('sector')!r} but the board "
                        f"card says {row.get('sector')!r}; refusing to "
                        "publish sectors from a list that disagrees "
                        "with the card.")

    # --- The construction: passing names grouped by sector,
    # sectors ranked by their passing names' average score, the
    # top sectors, up to the top names in each by score, equal
    # weight. Ties keep the snapshot's own order. ---
    passing = []
    for position, row in enumerate(scored):
        if not row["qualified"]:
            continue
        entry = gics.get(row["symbol"]) or {}
        sector = entry.get("sector")
        if not sector:
            return fail(f"{row['symbol']} passed every check but has "
                        "no sector on record; refusing to place it in "
                        "a sector it may not belong to.")
        passing.append({
            "symbol": row["symbol"],
            "sector": sector,
            "score": row["score"],
            "close": row["close"],
            "_position": position,
        })

    by_sector = {}
    for r in passing:
        by_sector.setdefault(r["sector"], []).append(r)
    sector_rows = []
    for sector, rows in by_sector.items():
        mean = sum(r["score"] for r in rows) / len(rows)
        sector_rows.append({"sector": sector, "mean_score": mean,
                            "names": rows})
    sector_rows.sort(key=lambda s: (-s["mean_score"], s["sector"]))
    chosen_sectors = sector_rows[:TOP_SECTORS]

    members = []
    for srow in chosen_sectors:
        names = sorted(srow["names"],
                       key=lambda r: (-r["score"], r["_position"]))
        members.extend(names[:PER_SECTOR])
    if not members:
        data = dict(base)
        data.update({
            "status": "cannot_build",
            "refusal_reasons": [
                "No name in this snapshot passed every check, so "
                "the construction has nothing to build from."],
            "counts": {"members": 0,
                       "names_checked": summary["universe"],
                       "names_scored": summary["scored"],
                       "passed_every_check_all": summary["qualified"]},
            "members": [],
            "sector_mix": [],
        })
        write_data(data)
        print(f"Wrote {OUT_PATH} (refusal: no passing names in "
              f"snapshot {session})")
        return 0

    weight = 100.0 / len(members)
    member_rows = [{
        "symbol": r["symbol"],
        "sector": r["sector"],
        "score": r["score"],
        "close": r["close"],
        "weight_pct": round(weight, 2),
    } for r in members]

    sector_mix = []
    for srow in chosen_sectors:
        count = sum(1 for r in members if r["sector"] == srow["sector"])
        if count:
            sector_mix.append({
                "sector": srow["sector"],
                "members": count,
                "share_pct": round(100.0 * count / len(members), 1),
            })

    data = dict(base)
    data.update({
        "status": "built",
        "refusal_reasons": [],
        "counts": {
            "members": len(member_rows),
            "names_checked": summary["universe"],
            "names_scored": summary["scored"],
            "not_enough_data": summary["insufficient_data"],
            "passed_every_check_all": summary["qualified"],
            "sectors_in_basket": len(sector_mix),
        },
        "members": member_rows,
        "sector_mix": sector_mix,
    })
    write_data(data)
    print(f"Wrote {OUT_PATH} (session {session}, {len(member_rows)} "
          f"members at {weight:.4f}% each before rounding, "
          f"{len(sector_mix)} sectors, age {age_days} day(s), "
          f"published {published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
