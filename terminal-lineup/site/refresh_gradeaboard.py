#!/usr/bin/env python3
"""Refresh the Grade-A Board data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: our own forecast study records, read exactly as
they stand: the first search's full result record (every recipe
cell it scored, with its verdicts) and the second search's full
result record plus its written report, whose list of the cells
graded A is the materialized output of the grading rule the second
search wrote down before it ran. The recipe definitions (what each
rule watches, what each narrowing means) are read from the same
study bundle's definition notes. Every grade and every number on
this page is recomputed or read from those records by this script;
nothing is typed in from anywhere else.

Reconstruction choices, stated as ours: (1) The grade itself is
recomputed here by applying the second search's own pre-written
rule to the two result records (a first-search promoted cell,
tested again, pointing the same way, and earning the second
search's own top verdict), and the recomputed set of 63 must match
the written report's own list of 63 cell for cell and number for
number, or nothing is published. (2) Each cell's recipe is stated
in plain words assembled from the study's own definitions: what
the rule watches, what outcome it is scored against, and what
narrowing (if any) the cell applies; the wording is ours, every
threshold in it is the study's, and each definition is anchored by
a check against the definition notes before anything is built.
(3) Cells are grouped by the recipe and the outcome it is scored
against (7 groups cover the 63), in the written report's own
order. (4) The first search's full outcome tally and the second
search's full outcome tally both travel with the page, counted
from the records, never typed in separately. (5) No time on this
page comes from the clock: every date comes from the records, so
running this script twice produces the same file.

Non-claims: this page does not re-grade anything, does not merge
in the separate book of 388 promoted entries (a different tool),
does not turn a volatility cell into a stock pick, and does not
publish any number beyond what the two study records carry. The
second search's own note travels with the page: its data covers
the same calendar years as the first search's held-back part, so
the top grade means the recipe held up on a separately gathered
set of stocks and a fresh split of the same years, not in new
years.

Fail-closed rules: if any record file is missing, if either
record's own tallies disagree with the counts recomputed from its
rows, if either tally disagrees with the published counts this
page is built around (1,217 promoted in the first search; 63 top
grade, 337 held up, 0 flipped, 564 did not reproduce, 253 not
testable in the second), if the recomputed top-grade set is not
exactly the written report's list of 63 with matching numbers, if
any definition anchor cannot be re-read from the definition
notes, or if any words assembled here carry an internal file name
or desk wording, the refresh stops and publishes nothing.

Usage: python3 refresh_gradeaboard.py
"""

import json
import os
import re

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.abspath(os.path.join(
    HERE, "..", "records", "forecast-search-2026-10-27"))
RUN1_JSON = os.path.join(RECORD_DIR, "forecast-search-2026-10-27.json")
RUN2_JSON = os.path.join(RECORD_DIR, "forecast-search-rerun-2026-10-27.json")
RUN2_MD = os.path.join(RECORD_DIR, "forecast-search-rerun-2026-10-27.md")
OUT_PATH = os.path.join(HERE, "grade-a-board", "data.json")

SOURCE_WORDS = ("Our own forecast study records: the first search over 6,385 "
                "stocks and the second search, its rule written down before "
                "it ran, over a second set of 3,337 stocks")

PUBLISHED = {
    "promoted": 1217,
    "A": 63, "confirmed": 337, "flipped": 0,
    "not-replicated": 564, "untestable": 253,
    "denominator": 964,
}

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "Femto", "Midna", "Codex",
             "forecast-search", "holdout", "discovery",
             "not financial advice", "for informational purposes",
             "for educational purposes", "do your own research",
             "past performance", "no guarantee", "at your own risk",
             "Slate", "ledger")

# --- plain-word recipe definitions, every threshold from the study bundle ---

WATCHES = {
    "vol.garch": ("A fixed formula that forecasts how much a stock's price "
                  "will move around. Each day it blends three parts: 90% of "
                  "yesterday's forecast, 8% of that day's squared move, and "
                  "2% of the stock's long-run average restlessness (its "
                  "average over the last 252 trading days). A higher reading "
                  "means the formula expects a jumpier stock."),
    "tai.pct": ("Where today's trading activity sits in the stock's own "
                "recent past. Activity is the stock's price times its "
                "shares traded, logged; the reading is that figure's rank "
                "within the stock's own last 252 trading days, from 0 (the "
                "quietest) to 1 (the busiest). A higher reading means an "
                "unusually busy stock."),
    "vol.gex_pct": ("Where the whole market's dealer gamma reading sits in "
                    "its own recent past. The reading tracks how much "
                    "dealers, as a group, would have to buy or sell as "
                    "prices move; this cell uses its rank within the last "
                    "252 trading days. This recipe runs the other way from "
                    "the others: a lower reading goes with a jumpier "
                    "market."),
    "avoid.deadcat": ("A warning flag on beaten-down stocks that bounce. "
                      "It flags a stock whose price is at or below 60% of "
                      "its highest price of the last 60 trading days and "
                      "that has still bounced at least 15% in the last 5 "
                      "trading days."),
    "avoid.pump": ("A warning flag on sudden pumps. It flags a stock that "
                   "is up at least 30% in the last 5 trading days on at "
                   "least 3 times its usual trading volume, where usual is "
                   "the middle value of the 60 trading days before."),
    "veto.gapup10": ("A warning flag on big opening gaps. It flags a stock "
                     "that opened at least 10% above its previous day's "
                     "closing price."),
}

EXPECTS = {
    ("vol.garch", "realized_vol_20"): (
        "Stocks with a higher reading will in fact move around more over "
        "the next 20 trading days."),
    ("tai.pct", "realized_vol_20"): (
        "Stocks with a higher reading will in fact move around more over "
        "the next 20 trading days."),
    ("vol.gex_pct", "spy_rv_5"): (
        "The lower the reading, the more SPY will move around over the "
        "next 5 trading days."),
    ("avoid.deadcat", "up_excess_20"): (
        "Flagged stocks will do worse over the next 20 trading days than "
        "the average stock in the same state on the same day."),
    ("avoid.pump", "up_excess_20"): (
        "Flagged stocks will do worse over the next 20 trading days than "
        "the average stock in the same state on the same day."),
    ("veto.gapup10", "up_excess_5"): (
        "Flagged stocks will do worse over the next 5 trading days than "
        "the average stock in the same state on the same day."),
    ("veto.gapup10", "up_excess_20"): (
        "Flagged stocks will do worse over the next 20 trading days than "
        "the average stock in the same state on the same day."),
}

GROUP_TITLES = {
    ("avoid.deadcat", "up_excess_20"):
        "Beaten-down stocks that bounce: a warning flag, next 20 trading days",
    ("avoid.pump", "up_excess_20"):
        "Sudden pumps on heavy volume: a warning flag, next 20 trading days",
    ("veto.gapup10", "up_excess_5"):
        "Big opening gaps up: a warning flag, next 5 trading days",
    ("veto.gapup10", "up_excess_20"):
        "Big opening gaps up: a warning flag, next 20 trading days",
    ("tai.pct", "realized_vol_20"):
        "Unusually busy trading: forecasting how much a stock moves, next 20 trading days",
    ("vol.garch", "realized_vol_20"):
        "A jumpiness formula: forecasting how much a stock moves, next 20 trading days",
    ("vol.gex_pct", "spy_rv_5"):
        "Dealer gamma rank: forecasting how much SPY moves, next 5 trading days",
}

DIM_WORDS = {
    ("fear", "fear"): ("on fear days only (days when SPY fell 1% or more, "
                       "or closed below its average price of the last 50 "
                       "trading days)"),
    ("fear", "calm"): ("on calm days only (days when SPY did neither: it "
                       "did not fall 1% or more and it closed at or above "
                       "its average price of the last 50 trading days)"),
    ("spy200", "above_rising"): ("on days when SPY closed above its "
                                 "average price of the last 200 trading "
                                 "days and that average was higher than it "
                                 "was 20 trading days earlier"),
    ("spy200", "above_falling"): ("on days when SPY closed above its "
                                  "average price of the last 200 trading "
                                  "days and that average was not higher "
                                  "than it was 20 trading days earlier"),
    ("spy200", "below"): ("on days when SPY closed at or below its "
                          "average price of the last 200 trading days"),
    ("vix", "lo"): ("on days when the fear gauge sat in the lowest third "
                    "of its own last 504 trading days"),
    ("vix", "mid"): ("on days when the fear gauge sat in the middle third "
                     "of its own last 504 trading days"),
    ("vix", "hi"): ("on days when the fear gauge sat in the highest third "
                    "of its own last 504 trading days"),
    ("age", "new"): "for stocks with fewer than 252 trading days of history",
    ("age", "old"): "for stocks with at least 252 trading days of history",
    ("state", "UP"): ("for stocks the study put in its up state that day "
                      "(trending up, as opposed to its reset state)"),
    ("state", "RESET"): ("for stocks in the study's reset state that day "
                         "(at least 35% below their high and near their "
                         "low)"),
}
for _q in range(1, 6):
    DIM_WORDS[("tier", "q%d" % _q)] = (
        "for stocks in the %s fifth of trading activity that day, ranked "
        "by the money traded over their last 20 trading days (the first "
        "fifth is the least traded, the fifth is the most traded)"
        % ("first" if _q == 1 else "second" if _q == 2 else
           "third" if _q == 3 else "fourth" if _q == 4 else "fifth"))

# Definition anchors: each plain-word definition must trace to the
# study bundle's own definition notes, checked before building.
ANCHORS = [
    ("avoid.py", "c / 60-bar high <= 0.6 and r5 >= +15%"),
    ("avoid.py", "r5 >= +30% on volume >= 3 vm1"),
    ("survivors.py", "o / c[-1] - 1 >= +10%"),
    ("vendors.py", "s2_t = w + 0.08 r_t^2 + 0.90 s2_{t-1}"),
    ("vendors.py", "ln(c v)'s percentile within its own trailing 252"),
    ("regime.py", "the GEX's percentile within its trailing 252 sessions"),
    ("contexts.py", "fear = SPY's close-to-close return <= -1% on d"),
    ("contexts.py", "above = SPY's close > its 200-session mean"),
    ("contexts.py", "the per-day quintile of the name's 20-session mean dollar volume"),
    ("contexts.py", "fewer than AGE_NEW (252) sessions since the name's first bar"),
    ("targets.py", "close[i+h] / open[i+1] - 1"),
    ("targets.py", "log of the realized daily volatility over i+1..i+h"),
    ("EVIDENCE.md", "RESET names (≥35% off the high, near the low)"),
    ("REGISTRY.md", "cells graded A out of the cells run 1 promoted"),
]


def fail(msg):
    raise SystemExit("refresh_gradeaboard: FAIL: " + msg)


def rows_of(rep):
    r = rep["rows"]
    if isinstance(r, dict):
        cols = r["columns"]
        return [dict(zip(cols, x)) for x in r["data"]]
    return list(r)


def fmt4(x):
    return "—" if x is None else "%+.4f" % float(x)


def fmt1(x):
    return "—" if x is None else "%+.1f" % float(x)


def cell_words(cell):
    if cell == "all":
        return "Counted across every stock and every day, with no narrowing."
    parts = []
    for piece in cell.split("|"):
        dim, _, val = piece.partition("=")
        key = (dim, val)
        if key not in DIM_WORDS:
            fail("a top-grade cell carries a narrowing this page has no "
                 "plain words for: %r" % piece)
        parts.append(DIM_WORDS[key])
    return "Counted only " + " and only ".join(parts) + "."


def grade_cells(rep1, rep2):
    """The second search's own pre-written rule, applied to the records."""
    idx2 = {(r["forecaster"], r["target"], r["cell"]): r
            for r in rows_of(rep2)}
    out = []
    for r1 in rows_of(rep1):
        if r1.get("verdict") != "promoted-B":
            continue
        key = (r1["forecaster"], r1["target"], r1["cell"])
        r2 = idx2.get(key)
        if r2 is None or r2.get("status") != "tested":
            g = "untestable"
        else:
            s1 = int(r1["sign"])
            ht = r2.get("hold_t_signed")
            s2 = r2.get("sign")
            t1 = None if ht is None or s2 is None else float(ht) * int(s2) * s1
            if t1 is not None and t1 <= -2.0:
                g = "flipped"
            elif s2 is not None and int(s2) == s1 and \
                    r2.get("verdict") == "promoted-B":
                g = "A"
            elif s2 is not None and int(s2) == s1 and \
                    t1 is not None and t1 >= 2.0:
                g = "confirmed"
            else:
                g = "not-replicated"
        x = r2 or {}
        out.append({
            "forecaster": key[0], "target": key[1], "cell": key[2],
            "grade": g, "sign": int(r1["sign"]),
            "disc2": x.get("disc_mean"), "hold2": x.get("hold_signed"),
            "hold2_t": x.get("hold_t_signed"), "net2": x.get("execution_net"),
            "hold1": r1.get("hold_signed"),
            "hold1_t": r1.get("hold_t_signed"),
        })
    return out


def check_search(rep, name, cells, tested, untested, bh, verdicts):
    if rep["cells_total"] != cells or rep["cells_tested"] != tested or \
            rep["cells_untested"] != untested or rep["bh_pass"] != bh:
        fail("%s: the record's own headline tallies are not the tallies "
             "this page is built around" % name)
    if rep["verdicts"] != verdicts:
        fail("%s: the record's own verdict tally disagrees with the "
             "published tally" % name)
    rows = rows_of(rep)
    if len(rows) != cells:
        fail("%s: the record carries %d rows, not %d"
             % (name, len(rows), cells))
    counted = {}
    n_tested = 0
    for r in rows:
        counted[r["verdict"]] = counted.get(r["verdict"], 0) + 1
        if r["status"] == "tested":
            n_tested += 1
    if counted != verdicts:
        fail("%s: verdicts recomputed from its rows %r disagree with "
             "its published tally %r" % (name, counted, verdicts))
    if n_tested != tested:
        fail("%s: tested rows recompute to %d, not %d"
             % (name, n_tested, tested))


def parse_section6(md_text):
    m = re.search(r"## 6\. Cells graded A: (\d+)\n(.*?)\n## 7\.",
                  md_text, re.S)
    if not m:
        fail("the written report's list of top-grade cells is missing")
    declared = int(m.group(1))
    rows = []
    for line in m.group(2).splitlines():
        if not line.startswith("|") or line.startswith("|---") or \
                "forecaster" in line:
            continue
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(parts) < 8:
            fail("a row in the written list does not parse: %r" % line)
        # The cell name itself can contain the separator (it joins two
        # narrowings), so anchor on the first two and last five fields.
        cells = parts[:2] + ["|".join(parts[2:-5])] + parts[-5:]
        rows.append(cells)
    if len(rows) != declared:
        fail("the written list declares %d cells but carries %d rows"
             % (declared, len(rows)))
    return rows


def build():
    for path in (RUN1_JSON, RUN2_JSON, RUN2_MD):
        if not os.path.exists(path):
            fail("study record missing: %s" % os.path.basename(path))
    for fname, needle in ANCHORS:
        path = os.path.join(RECORD_DIR, fname)
        if not os.path.exists(path):
            fail("definition notes missing: %s" % fname)
        with open(path, encoding="utf-8") as f:
            if needle not in f.read():
                fail("a recipe definition could not be re-read from the "
                     "study's definition notes (%s: %r)" % (fname, needle))

    with open(RUN1_JSON, encoding="utf-8") as f:
        rep1 = json.load(f)
    with open(RUN2_JSON, encoding="utf-8") as f:
        rep2 = json.load(f)
    with open(RUN2_MD, encoding="utf-8") as f:
        md2 = f.read()

    check_search(rep1, "the first search", 15135, 11150, 3985, 2986, {
        "null-overall": 7867, "untested": 3985, "promoted-B": 1217,
        "holdout-failed": 682, "cost-failed": 590, "wf-failed": 455,
        "sign-flip": 308, "holdout-insufficient": 24, "tiny": 7})
    check_search(rep2, "the second search", 21345, 13841, 7504, 195, {
        "null-overall": 13240, "untested": 7504, "sign-flip": 406,
        "promoted-B": 69, "holdout-failed": 43, "cost-failed": 27,
        "wf-failed": 14, "holdout-insufficient": 41, "tiny": 1})

    graded = grade_cells(rep1, rep2)
    summary = {}
    for g in ("A", "confirmed", "flipped", "not-replicated", "untestable"):
        summary[g] = sum(1 for c in graded if c["grade"] == g)
    summary["promoted"] = len(graded)
    summary["denominator"] = (summary["A"] + summary["confirmed"]
                              + summary["flipped"] + summary["not-replicated"])
    for key, want in PUBLISHED.items():
        got = summary["promoted"] if key == "promoted" else summary[key]
        if got != want:
            fail("the grades recomputed from the records give %s = %r, "
                 "not the published %r" % (key, got, want))
    # The written report's own replication tally must agree too.
    for needle in ("| A | 63 |", "| confirmed | 337 |", "| flipped | 0 |",
                   "| not-replicated | 564 |", "| untestable | 253 |",
                   "Denominator (tested here, not untestable): 964"):
        if needle not in md2:
            fail("the written report's replication tally could not be "
                 "re-read (missing: %r)" % needle)

    a_cells = [c for c in graded if c["grade"] == "A"]
    # The written report's list of 63, cell for cell and number for number.
    md_rows = parse_section6(md2)
    md_map = {}
    for cells in md_rows:
        md_map[(cells[0], cells[1], cells[2])] = cells
    if len(md_map) != 63:
        fail("the written list carries duplicate cells")
    rec_map = {(c["forecaster"], c["target"], c["cell"]): c for c in a_cells}
    if set(md_map) != set(rec_map):
        fail("the recomputed top-grade set is not the written report's "
             "list of 63")
    for key, cells in md_map.items():
        c = rec_map[key]
        expect = [c["forecaster"], c["target"], c["cell"],
                  "%+d" % c["sign"], fmt4(c["disc2"]),
                  "%s (%s)" % (fmt4(c["hold2"]), fmt1(c["hold2_t"])),
                  fmt4(c["net2"]),
                  "%s (%s)" % (fmt4(c["hold1"]), fmt1(c["hold1_t"]))]
        if cells != expect:
            fail("a listed cell's numbers cannot be re-read from the "
                 "records: %r vs %r" % (cells, expect))
    if "passes as a whole" not in md2 or "10 of 45" not in md2:
        fail("the written report's whole-recipe pass count could not "
             "be re-read")

    # Groups, in the written report's own order.
    order = []
    for cells in md_rows:
        gkey = (cells[0], cells[1])
        if gkey not in order:
            order.append(gkey)
    groups = []
    vol_count = 0
    stock_count = 0
    for gkey in order:
        if gkey not in GROUP_TITLES or gkey[0] not in WATCHES or \
                gkey not in EXPECTS:
            fail("a top-grade group has no plain-word recipe: %r" % (gkey,))
        members = [rec_map[k] for k in
                   [(r[0], r[1], r[2]) for r in md_rows
                    if (r[0], r[1]) == gkey]]
        is_vol = gkey[1] in ("realized_vol_20", "spy_rv_5")
        if is_vol:
            vol_count += len(members)
        else:
            stock_count += len(members)
        groups.append({
            "title": GROUP_TITLES[gkey],
            "watches": WATCHES[gkey[0]],
            "expects": EXPECTS[gkey],
            "kind": ("How much prices move" if is_vol
                     else "A warning flag (it says avoid, never buy)"),
            "cells": [{
                "where": cell_words(c["cell"]),
                "grade": "A (top grade)",
                "sign": c["sign"],
                "disc_second": c["disc2"],
                "hold_second": c["hold2"], "hold_second_t": c["hold2_t"],
                "net_second": c["net2"],
                "hold_first": c["hold1"], "hold_first_t": c["hold1_t"],
            } for c in members],
            "count": len(members),
        })
    if vol_count != 57 or stock_count != 6:
        fail("the top-grade mix recomputes to %d movement cells and %d "
             "warning flags, not 57 and 6" % (vol_count, stock_count))

    out = {
        "tool": "Grade-A Board",
        "source": SOURCE_WORDS,
        "state": "published",
        "proving_state": "Backed by a finished study",
        "proving_words": ("The tool's numbers are the counted result of a "
                          "study that has already run on the record."),
        "first_search_finished": rep1["generated"],
        "second_search_finished": rep2["generated"],
        "counts": {
            "promoted": summary["promoted"],
            "grade_a": summary["A"],
            "confirmed": summary["confirmed"],
            "flipped": summary["flipped"],
            "not_replicated": summary["not-replicated"],
            "untestable": summary["untestable"],
            "tested_denominator": summary["denominator"],
            "a_rate_pct": round(100.0 * summary["A"]
                                / summary["denominator"], 1),
            "a_or_confirmed_pct": round(
                100.0 * (summary["A"] + summary["confirmed"])
                / summary["denominator"], 1),
            "movement_cells": vol_count,
            "warning_cells": stock_count,
        },
        "grading_rule": (
            "A recipe earned the top grade only if all of this held. It "
            "was one of the 1,217 recipes the first search promoted. The "
            "second search could test it again (enough days and enough "
            "stocks). It pointed the same way in the second search as in "
            "the first. And in the second search it passed every one of "
            "that search's own gates again: a screen that limits false "
            "alarms when thousands of recipes are tested at once, a "
            "check that it pointed the same way in stretch after stretch "
            "of the earlier years, a check on the held-back later years "
            "it had not been picked on, a check that it still worked "
            "after trading costs, and a check that enough money could "
            "actually trade it. Anything weaker earned a lower grade, "
            "not this one."),
        "overlap_note": (
            "One limit travels with the top grade, in the second "
            "search's own words: its second set of stocks covers the "
            "same calendar years as the first search's held-back years. "
            "So the top grade means a recipe held up on a separately "
            "gathered set of stocks, a different mix of companies, and "
            "a fresh split of the same years. It does not mean the "
            "recipe has been tested in new years; only time going "
            "forward can test that."),
        "first_search": {
            "names": rep1["data"]["names"],
            "window": rep1["data"]["window"],
            "split": rep1["split"],
            "cells": rep1["cells_total"],
            "tested": rep1["cells_tested"],
            "untested": rep1["cells_untested"],
            "screen_pass": rep1["bh_pass"],
            "verdicts": [
                ["Promoted (the 1,217 this board re-grades)", 1217],
                ["Nothing there overall", 7867],
                ["Not tested (too little data)", 3985],
                ["Failed on the held-back years", 682],
                ["Failed after trading costs", 590],
                ["Failed the stretch-after-stretch check", 455],
                ["Pointed the other way in the held-back years", 308],
                ["Too little held-back data to judge", 24],
                ["Too small to count", 7],
            ],
        },
        "second_search": {
            "names": rep2["data"]["names"],
            "window": rep2["data"]["window"],
            "split": rep2["split"],
            "cells": rep2["cells_total"],
            "tested": rep2["cells_tested"],
            "untested": rep2["cells_untested"],
            "screen_pass": rep2["bh_pass"],
            "verdicts": [
                ["Nothing there overall", 13240],
                ["Not tested (too little data)", 7504],
                ["Pointed the other way while being picked", 406],
                ["Promoted in this search too", 69],
                ["Failed on the held-back years", 43],
                ["Too little held-back data to judge", 41],
                ["Failed after trading costs", 27],
                ["Failed the stretch-after-stretch check", 14],
                ["Too small to count", 1],
            ],
            "pairs_passed": "10 of the 45 recipe-and-outcome pairs passed "
                            "as a whole (at least half of their tested "
                            "promoted cells earned the top grade or held "
                            "up).",
        },
        "groups": groups,
    }

    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fail("assembled output carries forbidden wording: %r" % bad)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print("refresh_gradeaboard: wrote %s with %d top-grade cells in "
          "%d groups (of %d promoted; confirmed %d, did not reproduce "
          "%d, not testable %d)"
          % (OUT_PATH, len(a_cells), len(groups), summary["promoted"],
             summary["confirmed"], summary["not-replicated"],
             summary["untestable"]))


if __name__ == "__main__":
    build()
