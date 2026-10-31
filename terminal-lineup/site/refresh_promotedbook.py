#!/usr/bin/env python3
"""Refresh the Promoted Book data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the forecast program's own book of promoted entries,
read exactly as it stands: the frozen book record (388 entries, each
with its recipe code, the outcome it is scored against, its
narrowing, its grade, its standing, and the numbers from the two
study windows it was measured over), whose file hash matches the pin
printed in the second search's written report. The plain-word
recipes are assembled from the same study bundle's definition notes
(the rule definitions, the narrowing meanings, the outcome
definitions), each definition anchored by a check against those
notes before anything is built. The headline counts this page is
built around (388 entries in the book, 63 at the top grade, 325 on
probation) are the counts the Router's published record carries, and
the refresh recounts the book and publishes nothing if the two
disagree. The proving-state words are read from the Proving Ground's
published record.

Reconstruction choices, stated as ours: (1) Entries are grouped
first by standing, in the book's own standing words with a plain
meaning for each, then by recipe and the outcome it is scored
against. (2) Each entry's recipe is stated in plain words assembled
from the study's own definitions: what the rule watches, what
outcome it is scored against, and what narrowing (if any) the entry
applies; the wording is ours, every threshold in it is the study's.
(3) The numbers shown for an entry are the book's own per-window
numbers, stated as shares and counts: in each window, the share of
flagged stocks that beat the average stock, the same share for all
stocks, the gap between them, and how many times the flag was up.
The 57 movement entries at the top grade carry no per-window numbers
in the book, and the page says so rather than borrowing numbers from
anywhere else. (4) The book records no age for an entry beyond the
two windows it was measured over, and no decay state for any entry;
the page states both plainly and derives neither. (5) No time on
this page comes from the clock: every date comes from the records,
so running this script twice produces the same file.

Non-claims: this page does not re-grade anything, does not change
any entry's standing, does not turn a movement entry into a stock
pick, and does not publish any number beyond what the book itself
carries.

Fail-closed rules: if the book record is missing, if its hash does
not match the pin in the written report, if it does not carry
exactly 388 entries with unique ids that match their own parts, if
its counts per standing disagree with the Router's published counts
(388 in the book, 63 at the top grade, 325 on probation), if any
entry cannot be re-read from the record (a field missing, a
narrowing with no plain words, a window whose numbers do not parse),
if any definition anchor cannot be re-read from the definition
notes, if the Proving Ground's study-state words are missing, or if
any words assembled here carry an internal file name or desk
wording, the refresh stops and publishes nothing.

Usage: python3 refresh_promotedbook.py
"""

import hashlib
import json
import os

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.abspath(os.path.join(
    HERE, "..", "records", "forecast-search-2026-10-27"))
BOOK_PATH = os.path.abspath(os.path.join(
    HERE, "..", "..", "peer-execute-20261027", "sources", "a_factory",
    "desk", "forecast", "frozen", "promoted-book-1.json"))
RUN2_MD = os.path.join(RECORD_DIR, "forecast-search-rerun-2026-10-27.md")
ROUTER_PATH = os.path.join(HERE, "router", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "promoted-book", "data.json")

SOURCE_WORDS = ("Our own forecast program's book of promoted entries, "
                "frozen as the program recorded it, with the recipes "
                "stated from the same study's own definitions")

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "Femto", "Midna", "Codex",
             "forecast-search", "promoted-book", "holdout", "discovery",
             "not financial advice", "for informational purposes",
             "for educational purposes", "do your own research",
             "past performance", "no guarantee", "at your own risk",
             "Slate", "ledger", "fid")

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
                    "prices move; this entry uses its rank within the last "
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
    "alt.antichase": ("A warning flag on runaway climbers. It flags a "
                      "stock that has at least doubled over the last 126 "
                      "trading days (up 100% or more)."),
    "avoid.idio": ("A warning flag on stocks falling for their own "
                   "reasons. It flags a stock that is down at least 5% in "
                   "the last 5 trading days where most of that fall is the "
                   "stock's own move rather than the market's, measured "
                   "against how the stock usually moves with SPY and "
                   "checked against the study's frozen cutoff for how "
                   "much of the fall counts as its own."),
    "avoid.jump25": ("A warning flag on a single huge day. It flags a "
                     "stock that jumped at least 25% in any one day "
                     "within the last 20 trading days."),
    "avoid.mfi75": ("A warning flag on heavy money flowing in. It flags a "
                    "stock whose 14-day money-flow reading (a standard "
                    "measure that weighs each day's price by how much "
                    "traded, scaled from 0 to 100) sits at 75 or above."),
    "avoid.newlist": ("A warning flag on new listings. It flags a stock "
                      "with fewer than 252 trading days of price history "
                      "behind it."),
    "avoid.stretch": ("A warning flag on stocks stretched far above their "
                      "own average. It flags a stock whose price sits "
                      "above its average price of the last 50 trading days "
                      "by at least the study's frozen cutoff, the level "
                      "only the most stretched 5% of stocks reached in "
                      "the study's earlier years."),
    "avoid.surge2": ("A warning flag on repeated violent days. It flags a "
                     "stock with at least 2 days in the last 20 trading "
                     "days that moved at least 10% either way on at "
                     "least 3 times its usual trading volume, where usual "
                     "is the middle value of the 60 trading days before."),
    "avoid.x1p6": ("A warning flag on stocks priced far above their own "
                   "average. It flags a stock whose price is at least "
                   "60% above its average price of the last 50 trading "
                   "days."),
    "cs.correction": ("A score for spotting a correction inside a swing. "
                      "It blends five parts: 35% how much the stock's "
                      "momentum reading has faded over 4 days, 25% how "
                      "far today's trading volume has dropped below its "
                      "20-day average, 20% the day's candle shape (a full "
                      "point for a candle that swallows the day before "
                      "in the opposite direction, half a point for a "
                      "doji), 15% how far the current swing has stretched "
                      "for its usual wiggle, and 5% that wiggle itself. "
                      "It is only scored inside a confirmed swing: in an "
                      "up-swing (momentum strong, above 60) the score "
                      "counts against the stock; in a down-swing "
                      "(momentum weak, below 40) it counts for it."),
    "veto.cgtph": ("A warning flag on short-term strength. It flags a "
                   "stock that closed above the highest price of the day "
                   "before."),
    "veto.crashed": ("A warning flag on crashed, jumpy stocks. It flags a "
                     "stock that is down at least 50% over the last 120 "
                     "trading days and whose price still swings hard: "
                     "its movement over the last 60 trading days works "
                     "out to at least 100% a year."),
    "veto.panic": ("A warning flag on a panic day. It flags a stock that "
                   "fell at least 15% in one day on at least 3 times its "
                   "usual trading volume, where usual is the middle value "
                   "of the 60 trading days before."),
    "veto.pump100": ("A warning flag on a fresh doubling. It flags a "
                     "stock that is up at least 100% over the last 20 "
                     "trading days."),
    "veto.spikemem": ("A warning flag with a memory of a spike. It flags "
                      "a stock whose biggest single-day gain in the last "
                      "60 trading days was at least 40%."),
}

GROUP_TITLES = {
    "vol.garch": "A jumpiness formula: forecasting how much a stock moves",
    "tai.pct": "Unusually busy trading: forecasting how much a stock moves",
    "vol.gex_pct": "Dealer gamma rank: forecasting how much SPY moves",
    "avoid.deadcat": "Beaten-down stocks that bounce: a warning flag",
    "avoid.pump": "Sudden pumps on heavy volume: a warning flag",
    "veto.gapup10": "Big opening gaps up: a warning flag",
    "alt.antichase": "Runaway climbers: a warning flag",
    "avoid.idio": "Falling for their own reasons: a warning flag",
    "avoid.jump25": "One huge day up: a warning flag",
    "avoid.mfi75": "Heavy money flowing in: a warning flag",
    "avoid.newlist": "New listings: a warning flag",
    "avoid.stretch": "Stretched far above their average: a warning flag",
    "avoid.surge2": "Repeated violent days: a warning flag",
    "avoid.x1p6": "Priced far above their average: a warning flag",
    "cs.correction": "A correction score inside a swing",
    "veto.cgtph": "Closed above yesterday's high: a warning flag",
    "veto.crashed": "Crashed and still jumpy: a warning flag",
    "veto.panic": "A panic day down: a warning flag",
    "veto.pump100": "Doubled in 20 days: a warning flag",
    "veto.spikemem": "A huge spike in the last 60 days: a warning flag",
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
    ("avoid.py", "any r >= +25% in the last 20 bars"),
    ("avoid.py", "the 14-bar money-flow index >= 75"),
    ("avoid.py", "fewer than 252 bars of the name's history"),
    ("avoid.py", "c / m50 - 1 >= stretch_q95 (frozen)"),
    ("avoid.py", ">= 2 bars in 20 with |r| >= 10% on volume >= 3 vm1"),
    ("avoid.py", "c / m50 - 1 >= 0.6"),
    ("avoid.py", "r5 <= -5% and |r5 - beta SPY r5| / |r5| >= idio_q80_r5neg (frozen)"),
    ("survivors.py", "o / c[-1] - 1 >= +10%"),
    ("survivors.py", "panic flush (D8): r1 <= -15% on volume >= 3x the median of the 60 bars before"),
    ("survivors.py", "spike memory (D17): the largest r1 of the last 60 bars >= +40%"),
    ("survivors.py", "r120 <= -50% and the 60-bar"),
    ("survivors.py", "fresh pump (A2b): r20 >= +100%"),
    ("survivors.py", "short-term strength (A4/D4): close above the previous bar's high"),
    ("vendors.py", "s2_t = w + 0.08 r_t^2 + 0.90 s2_{t-1}"),
    ("vendors.py", "ln(c v)'s percentile within its own trailing 252"),
    ("vendors.py", "P = 0.35 div + 0.25 volDrop + 0.20 candle + 0.15 waveExt + 0.05 volPressure, in an up-wave"),
    ("vendors.py", "AltIndex anti-chase: r126 >= +100% (a veto, sign -1)"),
    ("regime.py", "the GEX's percentile within its trailing 252 sessions"),
    ("contexts.py", "fear = SPY's close-to-close return <= -1% on d"),
    ("contexts.py", "above = SPY's close > its 200-session mean"),
    ("contexts.py", "the per-day quintile of the name's 20-session mean dollar volume"),
    ("contexts.py", "fewer than AGE_NEW (252) sessions since the name's first bar"),
    ("targets.py", "close[i+h] / open[i+1] - 1"),
    ("targets.py", "log of the realized daily volatility over i+1..i+h"),
    ("EVIDENCE.md", "RESET names (≥35% off the high, near the low)"),
]

STANDINGS = [
    {
        "key": "promoted",
        "grade": "A",
        "words": "Promoted, grade A (top grade)",
        "meaning": ("Earned the top grade: the recipe held up in both "
                    "searches. These 63 are the same entries the Grade-A "
                    "Board lists."),
    },
    {
        "key": "probation",
        "grade": "B",
        "words": "On probation, grade B",
        "meaning": ("Earned the second grade: kept in the book and shown "
                    "when they match a name, but never used to set a call."),
    },
]

WINDOW_LABELS = {
    "2023-01-01": "the first window, from January 1, 2023 (the first "
                  "search's held-back years)",
    "2025-07-01": "the second window, from July 1, 2025 (the second "
                  "search's years)",
}


def fail(msg):
    raise SystemExit("refresh_promotedbook: FAIL: " + msg)


def expects(fid, target, direction):
    h = {"up_excess_5": 5, "up_excess_20": 20,
         "realized_vol_20": 20, "spy_rv_5": 5}[target]
    if target in ("realized_vol_20", "spy_rv_5"):
        if fid == "vol.gex_pct":
            return ("The lower the reading, the more SPY will move "
                    "around over the next 5 trading days.")
        return ("Stocks with a higher reading will in fact move around "
                "more over the next %d trading days." % h)
    if direction == "up":
        return ("Stocks this score points to will do better over the "
                "next %d trading days than the average stock in the same "
                "state on the same day." % h)
    return ("Flagged stocks will do worse over the next %d trading days "
            "than the average stock in the same state on the same day."
            % h)


def cell_words(cell):
    if cell == "all":
        return "Counted across every stock and every day, with no narrowing."
    parts = []
    for piece in cell.split("|"):
        dim, _, val = piece.partition("=")
        key = (dim, val)
        if key not in DIM_WORDS:
            fail("an entry carries a narrowing this page has no plain "
                 "words for: %r" % piece)
        parts.append(DIM_WORDS[key])
    return "Counted only " + " and only ".join(parts) + "."


def build():
    for path in (BOOK_PATH, RUN2_MD, ROUTER_PATH, PROVING_PATH):
        if not os.path.exists(path):
            fail("a record this page reads is missing: %s"
                 % os.path.basename(path))
    for fname, needle in ANCHORS:
        path = os.path.join(RECORD_DIR, fname)
        if not os.path.exists(path):
            fail("definition notes missing: %s" % fname)
        with open(path, encoding="utf-8") as f:
            if needle not in f.read():
                fail("a recipe definition could not be re-read from the "
                     "study's definition notes (%s: %r)" % (fname, needle))

    with open(BOOK_PATH, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    with open(RUN2_MD, encoding="utf-8") as f:
        md2 = f.read()
    if digest not in md2:
        fail("the book's contents do not match the pin printed in the "
             "written report")
    book = json.loads(raw.decode("utf-8"))
    if book.get("version") != "promoted-book-1":
        fail("the book record is not the version this page is built on")

    with open(ROUTER_PATH, encoding="utf-8") as f:
        router = json.load(f)
    rcounts = router.get("counts") or {}
    published = {"total": rcounts.get("book_entries"),
                 "promoted": rcounts.get("top_grade"),
                 "probation": rcounts.get("on_probation")}
    if published != {"total": 388, "promoted": 63, "probation": 325}:
        fail("the Router's published book counts are not the counts this "
             "page is built around: %r" % (published,))

    with open(PROVING_PATH, encoding="utf-8") as f:
        proving = json.load(f)
    study_state = None
    for s in proving.get("states") or []:
        if s.get("key") == "study":
            study_state = s
    if not study_state or not study_state.get("words"):
        fail("the proving ground's study-state words are missing")

    entries = book.get("entries")
    if not isinstance(entries, list) or len(entries) != published["total"]:
        fail("the book does not carry the published number of entries")
    seen = set()
    counts = {"promoted": 0, "probation": 0}
    movement = 0
    warning = 0
    built = []
    for e in entries:
        for field in ("id", "fid", "target", "cell", "dims", "sign",
                      "direction", "binary", "h", "grade", "status",
                      "windows"):
            if field not in e:
                fail("an entry in the book is missing a field: %r" % field)
        if e["id"] != "%s|%s|%s" % (e["fid"], e["target"], e["cell"]):
            fail("an entry's id does not match its own parts: %r" % e["id"])
        if e["id"] in seen:
            fail("the book carries a duplicate entry: %r" % e["id"])
        seen.add(e["id"])
        standing = None
        for s in STANDINGS:
            if e["status"] == s["key"] and e["grade"] == s["grade"]:
                standing = s
        if standing is None:
            fail("an entry carries a standing this page does not know: "
                 "%r / %r" % (e["status"], e["grade"]))
        counts[e["status"]] += 1
        if e["fid"] not in WATCHES or e["fid"] not in GROUP_TITLES:
            fail("an entry carries a recipe this page has no plain words "
                 "for: %r" % e["fid"])
        # The narrowing in the entry's name must match its recorded parts.
        want_dims = {}
        if e["cell"] != "all":
            for piece in e["cell"].split("|"):
                dim, _, val = piece.partition("=")
                want_dims[dim] = val
        if e["dims"] != want_dims:
            fail("an entry's narrowing parts disagree with its name: %r"
                 % e["id"])
        is_vol = e["target"] in ("realized_vol_20", "spy_rv_5")
        if is_vol:
            movement += 1
        else:
            warning += 1
        windows = []
        for w in e["windows"]:
            if w.get("fid") != e["fid"] or w.get("target") != e["target"] \
                    or w.get("cell") != e["cell"] or w.get("status") != "ok":
                fail("a window of an entry cannot be re-read from the "
                     "record: %r" % e["id"])
            start = (w.get("window") or [None])[0]
            if start not in WINDOW_LABELS:
                fail("a window carries a start this page does not know: "
                     "%r" % (start,))
            for num in ("base_rate", "rate", "lift", "n_dates", "n_obs",
                        "n_set"):
                if not isinstance(w.get(num), (int, float)):
                    fail("a window number cannot be re-read: %r / %s"
                         % (e["id"], num))
            windows.append({
                "label": WINDOW_LABELS[start],
                "starts": start,
                "flagged_share_pct": round(100.0 * float(w["rate"]), 1),
                "all_share_pct": round(100.0 * float(w["base_rate"]), 1),
                "gap_points": round(100.0 * float(w["lift"]), 1),
                "times_flagged": int(w["n_set"]),
                "stocks_counted": int(w["n_obs"]),
                "days_counted": int(w["n_dates"]),
            })
        if not is_vol and len(windows) != 2:
            fail("a stock-direction entry does not carry its two "
                 "windows: %r" % e["id"])
        if is_vol and windows:
            fail("a movement entry carries window numbers the book is "
                 "not expected to hold: %r" % e["id"])
        built.append({
            "fid": e["fid"],
            "target": e["target"],
            "standing": e["status"],
            "grade": e["grade"],
            "kind": ("How much prices move" if is_vol else
                     "A score that points up" if e["direction"] == "up"
                     else "A warning flag (it says avoid, never buy)"),
            "expects": expects(e["fid"], e["target"], e["direction"]),
            "where": cell_words(e["cell"]),
            "days_ahead": int(e["h"]),
            "windows": windows,
        })

    for s in STANDINGS:
        if counts[s["key"]] != published[s["key"]]:
            fail("the book's count at the %r standing recomputes to %d, "
                 "not the Router's published %d"
                 % (s["key"], counts[s["key"]], published[s["key"]]))

    # Groups: standing first, then recipe and outcome, in book order.
    standings_out = []
    for s in STANDINGS:
        mine = [b for b in built if b["standing"] == s["key"]]
        order = []
        for b in mine:
            gkey = (b["fid"], b["target"])
            if gkey not in order:
                order.append(gkey)
        groups = []
        for gkey in order:
            members = [b for b in mine if (b["fid"], b["target"]) == gkey]
            groups.append({
                "title": GROUP_TITLES[gkey[0]],
                "watches": WATCHES[gkey[0]],
                "expects": members[0]["expects"],
                "kind": members[0]["kind"],
                "count": len(members),
                "entries": [{
                    "where": m["where"],
                    "grade": m["grade"],
                    "days_ahead": m["days_ahead"],
                    "windows": m["windows"],
                } for m in members],
            })
        standings_out.append({
            "key": s["key"],
            "grade": s["grade"],
            "words": s["words"],
            "meaning": s["meaning"],
            "count": len(mine),
            "groups": groups,
        })

    out = {
        "tool": "Promoted Book",
        "source": SOURCE_WORDS,
        "state": "published",
        "proving_state": study_state["words"],
        "proving_words": study_state["definition"],
        "counts": {
            "total": len(built),
            "promoted": counts["promoted"],
            "probation": counts["probation"],
            "movement": movement,
            "stock_direction": warning,
        },
        "standings": standings_out,
        "difference_note": (
            "How this page differs from the Grade-A Board: that board "
            "lists only the 63 entries at the top grade. This page is "
            "the whole book the program keeps: all 388 promoted "
            "entries, the 63 at the top grade and the 325 one grade "
            "down, on probation, each with the standing the program's "
            "own record gives it."),
        "numbers_note": (
            "The numbers under a stock-direction entry are the book's "
            "own, for each of the two windows it was measured over: the "
            "share of flagged stocks that went on to beat the average "
            "stock in the same state, the same share counted across all "
            "stocks, the gap between the two in points, and how many "
            "times the flag was up. The 57 movement entries at the top "
            "grade carry no per-window numbers in the book itself, so "
            "none are shown for them; their study numbers are the ones "
            "on the Grade-A Board."),
        "age_note": (
            "The book records no age for an entry and no decay state "
            "for any entry. The only dates it carries are the two "
            "window starts above (January 1, 2023 and July 1, 2025), "
            "so no age and no decay state is shown for any entry here."),
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
    print("refresh_promotedbook: wrote %s with %d entries (%d promoted "
          "grade A, %d on probation grade B; %d movement, %d "
          "stock-direction)"
          % (OUT_PATH, len(built), counts["promoted"], counts["probation"],
             movement, warning))


if __name__ == "__main__":
    build()
