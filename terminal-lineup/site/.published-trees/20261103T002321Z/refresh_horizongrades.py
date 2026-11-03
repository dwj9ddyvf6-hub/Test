#!/usr/bin/env python3
"""Refresh the Horizon Grades data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the published grading record itself, exactly as The
Record published it: the Board's calls in their publishing day-groups
with the grade each group carries at 1, 5 and 21 sessions, the whole
qualified cohort block (the calls that passed every check) at the
same horizons, the published totals, and the Morning Map count that
keeps the published total honest. The proving state words come from
the Proving Ground's published vocabulary.

Reconstruction choices, stated as ours: (1) This page is the horizon
view of that one record, never a second grading: the per-horizon
figures for all Board calls are the record's own totals and group
grades, rearranged by horizon and by nothing else. Where the record
attaches a graded horizon to one publishing day-group, the horizon
carries that attachment as it stands; the other day-groups carry
their own first-grade dates. (2) The qualified cohort is shown as
the one whole-cohort block per horizon the record carries, never
split by day-group, because the record does not split it.
(3) No percentage is presented as a rate anywhere: every graded
count on record is under 30, so the page shows counts, and the
record's average and middle figures are shown exactly as the record
states them, labelled as the average and middle of the graded few.
(4) The Morning Map's cards are not part of these horizons: the
record grades them per session on walls and flip level, so they are
named here only to keep the published total (56) reconciled with
the Board total (50) that these horizons cover. (5) Every date and
figure comes from the record, never from the clock, so running this
script twice produces the same file.

Non-claims: this page does not grade anything itself, does not split
a group grade into single calls, does not invent a horizon the
record does not carry, and does not present an average of a few
graded calls as a rate or a forecast.

Fail-closed rules: the refresh stops and publishes nothing if any
figure it would show disagrees with The Record's published data on
any shared figure: the published totals against the counted groups,
the graded-so-far total against the 1-session outcome block, the
qualified published count against the counted calls that passed
every check, any horizon's rose plus did-not-rise against its graded
count, a graded horizon's block against the day-group the record
attaches it to, or the proving words against the Proving Ground's
published vocabulary. Forbidden internal wording in the assembled
output also stops the refresh.

Usage: python3 refresh_horizongrades.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD_PATH = os.path.join(HERE, "record", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "horizon-grades", "data.json")

HORIZONS = (("1d", 1), ("5d", 5), ("21d", 21))
FORBIDDEN = (".json", ".py", "morgue", "ledger", "scorecard")


def fail(msg):
    raise SystemExit("refresh_horizongrades: FAIL: " + msg)


def load(path, what):
    if not os.path.exists(path):
        fail(f"{what}: published data missing")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_block(block, what):
    if block.get("state") == "graded":
        if block["rose_count"] + block["did_not_rise_count"] != block["graded_count"]:
            fail(f"{what}: rose plus did-not-rise disagrees with the graded count")
    elif block.get("state") == "not_yet_graded":
        if not block.get("first_grade_date"):
            fail(f"{what}: not yet graded but carries no first grade date")
    else:
        fail(f"{what}: unknown grading state {block.get('state')!r}")


def horizon_view(key, days, record, groups):
    """One horizon for all Board calls, following the record's own
    day-group structure: a graded block sits on the group the record
    attaches it to; every other group keeps its own first date."""
    graded_total = 0
    graded_block = None
    group_lines = []
    for g in groups:
        block = g["grades"][key]
        check_block(block, f"Board {key} group {g['session']}")
        if block["state"] == "graded":
            # Aggregate every graded day-group (cure G17, 2026-10-29:
            # the Record now attaches real per-group grades, so more
            # than one group can be graded; the old single-group
            # assumption refused the cured record). Cohort average
            # and middle come from the record's cohort block, which
            # the group counts must reconcile with below.
            graded_block = block
            graded_total += block["graded_count"]
            group_lines.append({
                "session": g["session"],
                "state": "graded",
                "graded_count": block["graded_count"],
                "graded_of_group": block["graded_of_group"],
                "rose_count": block["rose_count"],
                "did_not_rise_count": block["did_not_rise_count"],
            })
        else:
            group_lines.append({
                "session": g["session"],
                "state": "not_yet_graded",
                "first_grade_date": block["first_grade_date"],
            })
    first_date = None
    if graded_block is None:
        first_date = min(line["first_grade_date"] for line in group_lines)
        return {
            "days": days,
            "state": "not_yet_graded",
            "published_count": record["totals"]["board_calls"],
            "graded_count": 0,
            "first_grade_date": first_date,
            "groups": group_lines,
        }
    cohort = (record["board"].get("cohort") or {}).get(key) or {}
    rose_total = sum(line.get("rose_count", 0) for line in group_lines)
    did_total = sum(line.get("did_not_rise_count", 0)
                    for line in group_lines)
    if cohort.get("state") == "graded":
        if cohort["graded_count"] != graded_total or \
                cohort["rose_count"] != rose_total:
            fail(f"Board {key}: day-group grades ({graded_total} "
                 f"graded, {rose_total} rose) disagree with the "
                 f"record's cohort block ({cohort['graded_count']} "
                 f"graded, {cohort['rose_count']} rose)")
        average_pct = cohort["average_pct"]
        middle_pct = cohort["middle_pct"]
    else:
        # Older record without a cohort block: a single graded
        # group is the cohort, so its own figures stand.
        if sum(1 for line in group_lines
               if line["state"] == "graded") != 1:
            fail(f"Board {key}: graded day-groups exist but the "
                 "record carries no cohort block to summarise them")
        average_pct = graded_block["average_pct"]
        middle_pct = graded_block["middle_pct"]
    return {
        "days": days,
        "state": "graded",
        "published_count": record["totals"]["board_calls"],
        "graded_count": graded_total,
        "rose_count": rose_total,
        "did_not_rise_count": did_total,
        "average_pct": average_pct,
        "middle_pct": middle_pct,
        "groups": group_lines,
    }


def build():
    record = load(RECORD_PATH, "The Record")
    if record.get("tool") != "The Record":
        fail(f"record: tool name {record.get('tool')!r} != expected 'The Record'")
    proving = load(PROVING_PATH, "The Proving Ground")
    states = {s["key"]: s for s in proving.get("states", [])}
    if "measuring" not in states:
        fail("proving-ground: the measuring state is missing from its vocabulary")

    totals = record["totals"]
    groups = record["board"]["groups"]
    board_counted = sum(len(g["calls"]) for g in groups)
    if board_counted != totals["board_calls"]:
        fail(f"Board calls counted in the groups ({board_counted}) disagree "
             f"with the published total ({totals['board_calls']})")
    map_counted = sum(len(g["cards"]) for g in record["map"]["groups"])
    if map_counted != totals["map_calls"]:
        fail(f"Morning Map cards counted in the groups ({map_counted}) "
             f"disagree with the published total ({totals['map_calls']})")
    if totals["board_calls"] + totals["map_calls"] != totals["calls_published"]:
        fail("the published total disagrees with its Board and Map parts")
    if record["map"]["cards_graded"] + record["map"]["cards_waiting"] != map_counted:
        fail("the Morning Map graded plus waiting counts disagree with its cards")

    qualified = record["board"]["strongest"]
    qualified_counted = sum(
        1 for g in groups for c in g["calls"] if c["passed_every_check"])
    if qualified_counted != qualified["calls"]:
        fail(f"calls that passed every check counted in the groups "
             f"({qualified_counted}) disagree with the published qualified "
             f"count ({qualified['calls']})")

    horizons = []
    for key, days in HORIZONS:
        view = horizon_view(key, days, record, groups)
        q = qualified["horizons"][key]
        check_block(q, f"qualified cohort {key}")
        if q["state"] == "graded":
            view["qualified"] = {
                "state": "graded",
                "published_count": qualified["calls"],
                "graded_count": q["graded_count"],
                "rose_count": q["rose_count"],
                "did_not_rise_count": q["did_not_rise_count"],
                "average_pct": q["average_pct"],
                "middle_pct": q["middle_pct"],
            }
        else:
            if view["state"] == "not_yet_graded" and \
                    q["first_grade_date"] != view["first_grade_date"]:
                fail(f"qualified cohort {key}: its first grade date "
                     f"({q['first_grade_date']}) disagrees with the Board "
                     f"horizon's ({view['first_grade_date']})")
            view["qualified"] = {
                "state": "not_yet_graded",
                "published_count": qualified["calls"],
                "graded_count": 0,
                "first_grade_date": q["first_grade_date"],
            }
        horizons.append(view)

    # The published graded-so-far total and its outcome block are the
    # 1-session horizon, shared figures with this page's first panel.
    outcomes = totals["outcomes_so_far"]
    first = horizons[0]
    # The graded-so-far total spans both published surfaces: the
    # Board's 1-session outcomes plus the Morning Map's graded
    # cards (cure G17, 2026-10-29: the old equality bound the total
    # to the Board block alone, which held only while no Map card
    # had graded; 75 = 66 Board + 9 Map on the current record).
    if totals["calls_graded_so_far"] != outcomes["graded_count"] \
            + record["map"]["cards_graded"]:
        fail("the graded-so-far total disagrees with its outcome block")
    if outcomes["horizon_days"] != 1 or first["state"] != "graded" or \
            first["graded_count"] != outcomes["graded_count"] or \
            first["rose_count"] != outcomes["rose_count"] or \
            first["did_not_rise_count"] != outcomes["did_not_rise_count"]:
        fail("the 1-session horizon disagrees with the published "
             "graded-so-far outcomes")

    out = {
        "tool": "Horizon Grades",
        "source": ("The same published record The Record keeps: every call "
                   "the Board published, kept in a permanent log and graded "
                   "against what prices actually did next"),
        "generated_at_utc": record["generated_at_utc"],
        "proving": {
            "state": "measuring",
            "words": states["measuring"]["words"],
            "definition": states["measuring"]["definition"],
        },
        "totals": {
            "calls_published": totals["calls_published"],
            "board_calls": totals["board_calls"],
            "map_calls": totals["map_calls"],
            "calls_graded_so_far": totals["calls_graded_so_far"],
        },
        "method": ("Grades are recorded for each publishing day as a group, "
                   "so a horizon's grade belongs to the day-group the record "
                   "attaches it to, and is never split into a separate "
                   "figure for each single call. A call is graded on the "
                   "change from the closing price on the day it was "
                   "published to the close 1, 5 and 21 trading days later. "
                   "It counts as rose only if that change is above zero; "
                   "flat counts with the ones that did not rise. Grades, "
                   "once published, are never rewritten."),
        "map_note": ("The Morning Map's index cards are graded per session "
                     "on their walls and flip level, not at these horizons, "
                     "so they are not in the panels below: they are the "
                     "rest of the published total."),
        "horizons": horizons,
    }

    blob = json.dumps(out)
    for bad in FORBIDDEN:
        if bad in blob:
            fail(f"assembled output carries forbidden internal wording: {bad}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    # Record-surface cure (2026-10-31): surface this page's full
    # record in its own data.json, from numbers already on file.
    try:
        import record_surface as _rs
        _rs.enrich_slug("horizon-grades")
    except Exception as _exc:
        print(f"record-surface enrich failed: {_exc}")
    print(f"refresh_horizongrades: wrote {OUT_PATH} "
          f"({totals['board_calls']} Board calls, "
          f"{totals['calls_graded_so_far']} graded so far)")


if __name__ == "__main__":
    build()
