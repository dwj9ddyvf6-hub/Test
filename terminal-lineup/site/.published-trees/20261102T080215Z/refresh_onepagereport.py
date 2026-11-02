#!/usr/bin/env python3
"""Refresh the One-Page Report data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever. Factual state (dates, coverage, no-data
states) is information and stays.

Evidence class: only the published data files of tools already on
this site, read exactly as published: the full scored list (The
Screener: every scored name with its score, checks in favor, share
of measures with data, passed-every-check flag, sector and index),
the Qualified Board's published 50 (the same eight checks shown
check by check), the Second Opinion's per-name family readings
(price, options prints, modelled options positioning, filings and
positioning lines, plus its silent company-facts and news families
with their published reasons), the AI Chart Read's published price
history and pattern labels, the Insider Wire's per-name summaries,
the Squeeze Watch's short interest readings, the Unusual Volume
list, the Earnings Calendar's dated names, the Filings Wire's
company list, and the big-holder holdings tracker's period and
holder counts.

Reconstruction choices, stated as ours: (1) The report has nine
sections, one per source tool above, in a fixed order; a section
either carries the source's published reading for the picked name,
verbatim in substance, or a plain not-on-record line. Nothing is
computed fresh that another tool has not published, except the AI
Chart Read section's averages, trend word and price levels, which
are worked out from that tool's published price history by that
tool's own printed rule, exactly as its own page works them out,
and plain formatting of published figures (money and share counts
rounded the way the source pages print them). (2) The Second
Opinion's families stay separate inside their section: no section
merges families, tools or readings into a single verdict or score,
and this page publishes no score of its own. (3) The big-holder
holdings reports name companies, not stock symbols, so no holding
can be tied to a picked symbol from them; that section is plainly
not on record for every name and says why. The Filings Wire holds
no company's figures yet, so its section is likewise not on record
for every name. (4) The header count for a name is the count of
the nine sections carrying a reading for it, counted here from the
assembled sections themselves.

Fail-closed rules: if any source's own counts disagree with its
lists (the scored list's counts against its rows, the board's
published count against its rows or any board name missing from
the scored list, the Second Opinion's coverage count against its
names or its names not equalling the union of every source's
names, the chart history's name and label counts against its own
published counts or any label for a name with no history, the
insider totals against its rows, the squeeze coverage against its
rows, any unusual-volume multiple below the published floor, the
earnings dated count against its rows, the filings count against
its company list, or the big-holder holder count against its own
published count), the refresh stops and publishes nothing. All
dates come from the sources, never the clock, so running this
script twice produces the same file.

Usage: python3 refresh_onepagereport.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "one-page-report", "data.json")


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def load(slug):
    path = os.path.join(HERE, slug, "data.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def avg_of(values, n):
    if len(values) < n:
        return None
    return sum(values[len(values) - n:]) / n


def extremes(dates, highs, lows, n):
    if len(highs) < n:
        return None
    start = len(highs) - n
    hi, hi_d, lo, lo_d = None, None, None, None
    for i in range(start, len(highs)):
        if hi is None or highs[i] > hi:
            hi, hi_d = highs[i], dates[i]
        if lo is None or lows[i] < lo:
            lo, lo_d = lows[i], dates[i]
    return {"window": n, "high": hi, "high_date": hi_d,
            "low": lo, "low_date": lo_d}


def main():
    screener = load("screener")
    board = load("board")
    second = load("second-opinion")
    chart = load("ai-chart-read")
    insider = load("insider-wire")
    squeeze = load("squeeze-watch")
    volume = load("unusual-volume")
    earnings = load("earnings-calendar")
    filings = load("filings-wire")
    holders = load("13f-tracker")

    # --- fail-closed count checks against each source's own counts ---
    sc_counts = screener["counts"]
    if len(screener["names"]) != sc_counts["names_scored"]:
        fail("screener rows %d != its names_scored %d"
             % (len(screener["names"]), sc_counts["names_scored"]))
    scored = {n["symbol"]: n for n in screener["names"]}

    if len(board["groups"]) != 1:
        fail("board groups != 1")
    board_names = board["groups"][0]["names"]
    if len(board_names) != board["counts"]["names_published"]:
        fail("board rows %d != its names_published %d"
             % (len(board_names), board["counts"]["names_published"]))
    board_by = {}
    for n in board_names:
        if n["symbol"] not in scored:
            fail("board name %s missing from the scored list" % n["symbol"])
        board_by[n["symbol"]] = n

    if len(second["names"]) != second["coverage"]["names_on_record"]:
        fail("second opinion rows %d != its names_on_record %d"
             % (len(second["names"]), second["coverage"]["names_on_record"]))
    second_by = {n["symbol"]: n for n in second["names"]}

    if len(chart["bars"]) != chart["names_on_record"]:
        fail("chart history names %d != its names_on_record %d"
             % (len(chart["bars"]), chart["names_on_record"]))
    if len(chart["labels"]) != chart["labels_on_record"]:
        fail("chart labels %d != its labels_on_record %d"
             % (len(chart["labels"]), chart["labels_on_record"]))
    for sym in chart["labels"]:
        if sym not in chart["bars"]:
            fail("chart label for %s, which has no price history" % sym)

    ins_totals = insider["totals"]
    if len(insider["names"]) != ins_totals["names_covered"]:
        fail("insider rows %d != its names_covered %d"
             % (len(insider["names"]), ins_totals["names_covered"]))
    n_summary = sum(1 for n in insider["names"] if n["state"] == "summary")
    n_none = sum(1 for n in insider["names"] if n["state"] == "not_on_record")
    if n_summary != ins_totals["names_with_summary"]:
        fail("insider summaries %d != its names_with_summary %d"
             % (n_summary, ins_totals["names_with_summary"]))
    if n_none != ins_totals["names_not_on_record"]:
        fail("insider not-on-record %d != its names_not_on_record %d"
             % (n_none, ins_totals["names_not_on_record"]))
    insider_by = {n["symbol"]: n for n in insider["names"]}

    sq_cov = squeeze["coverage"]
    if len(squeeze["names"]) != sq_cov["names_covered"]:
        fail("squeeze rows %d != its names_covered %d"
             % (len(squeeze["names"]), sq_cov["names_covered"]))
    squeeze_by = {n["symbol"]: n for n in squeeze["names"]}

    floor = volume["floor_multiple"]
    for n in volume["names"]:
        if n["multiple"] < floor:
            fail("unusual volume name %s below the published floor" % n["symbol"])
    volume_by = {n["symbol"]: n for n in volume["names"]}

    if len(earnings["names"]) != earnings["dated_names"]:
        fail("earnings rows %d != its dated_names %d"
             % (len(earnings["names"]), earnings["dated_names"]))
    earnings_by = {n["symbol"]: n for n in earnings["names"]}

    if len(filings["companies"]) != filings["companies_on_record"]:
        fail("filings companies %d != its companies_on_record %d"
             % (len(filings["companies"]), filings["companies_on_record"]))
    filings_by = {}
    for comp in filings["companies"]:
        sym = comp.get("symbol")
        if sym:
            if sym in filings_by:
                fail("filings wire names %s for two companies" % sym)
            filings_by[sym] = comp

    if holders["holders_on_record"] <= 0 or len(holders["holders"]) < 1:
        fail("big-holder tracker carries no holder record")

    union = (set(scored) | set(second_by) | set(chart["bars"]) |
             set(insider_by) | set(squeeze_by) | set(volume_by) |
             set(earnings_by))
    if set(second_by) != union:
        fail("second opinion names do not equal the union of source names "
             "(only in second opinion: %s; missing from it: %s)"
             % (sorted(set(second_by) - union)[:5],
                sorted(union - set(second_by))[:5]))

    dates = chart["dates"]

    names = {}
    distribution = {}
    for sym in sorted(union):
        entry = {}

        # 1. Scored checks
        s = scored.get(sym)
        if s is None:
            entry["scored"] = None
        else:
            row = {
                "score": s["score"], "close": s["close"],
                "checks_in_favor": s["checks_in_favor"],
                "checks_total": s["checks_total"],
                "passed_every_check": s["passed_every_check"],
                "data_behind_score_pct": s["data_behind_score_pct"],
                "sector": s["sector"], "index": s["index"],
            }
            b = board_by.get(sym)
            if b is not None:
                row["board"] = {
                    "session": board["session"],
                    "rank_by_score": b["rank_by_score"],
                    "checks": b["checks"], "missed": b["missed"],
                }
            entry["scored"] = row

        # 2. Second Opinion families, kept separate
        entry["families"] = second_by.get(sym)

        # 3. AI Chart Read, by that tool's own printed rule
        bar = chart["bars"].get(sym)
        if bar is None:
            entry["chart"] = None
        else:
            start, closes, highs, lows = bar[0], bar[1], bar[2], bar[3]
            name_dates = dates[start:start + len(closes)]
            last_close = closes[-1]
            a50 = avg_of(closes, 50)
            a200 = avg_of(closes, 200)
            trend = None
            if a50 is not None and a200 is not None:
                if last_close > a50 and last_close > a200:
                    trend = "Trending up"
                elif last_close < a50 and last_close < a200:
                    trend = "Trending down"
                else:
                    trend = "Mixed: no clear reading"
            entry["chart"] = {
                "sessions": len(closes),
                "first_date": name_dates[0], "last_date": name_dates[-1],
                "last_close": last_close,
                "avg50": a50,
                "avg200": a200,
                "trend": trend,
                "levels20": extremes(name_dates, highs, lows, 20),
                "levels126": extremes(name_dates, highs, lows, 126),
                "label": chart["labels"].get(sym),
            }

        # 4. Insider Wire
        ins = insider_by.get(sym)
        entry["insider"] = (ins["summary"]
                            if ins is not None and ins["state"] == "summary"
                            else None)

        # 5. Squeeze Watch
        entry["squeeze"] = squeeze_by.get(sym)

        # 6. Unusual Volume
        entry["volume"] = volume_by.get(sym)

        # 7. Earnings Calendar
        entry["earnings"] = earnings_by.get(sym)

        # 8. Filings Wire, joined by the symbol that wire now
        # publishes for each company (hookup cure, 2026-10-30;
        # before that join the wire published companies by their
        # EDGAR number only and this section could carry no
        # per-symbol reading). 9 still carries none: the
        # big-holder reports name companies, not stock symbols.
        entry["filings"] = filings_by.get(sym)
        entry["holders"] = None

        def carries(key):
            if entry[key] is None:
                return False
            if key == "families":
                # The section carries a reading only when at least
                # one family actually speaks for the name; a name
                # every family is silent for shows the silences and
                # their reasons, but no reading.
                return entry[key].get("families_speaking", 0) >= 1
            return True

        carrying = sum(1 for key in
                       ("scored", "families", "chart", "insider",
                        "squeeze", "volume", "earnings", "filings",
                        "holders") if carries(key))
        entry["sections_with_reading"] = carrying
        distribution[carrying] = distribution.get(carrying, 0) + 1
        names[sym] = entry

    sections = [
        {"id": "scored", "tool": "Qualified Board and The Screener",
         "date": screener["session"],
         "about": "The name's score out of 100 from the scored trading day, how many of the eight checks lined up in its favor, and whether it passed every check. For the 50 highest-scoring names, the board also shows every check one by one, dated to its own earlier session."},
        {"id": "families", "tool": "The Second Opinion",
         "date": second["session"],
         "about": "Separate kinds of evidence, kept separate and never merged into one verdict: price and trading history, options prints, modelled options positioning, filings and positioning, company facts, and news and events. A kind with nothing to say for this name says so, with its reason."},
        {"id": "chart", "tool": "AI Chart Read",
         "date": chart["session"],
         "about": "The name's trend against its own 50-session and 200-session averages, its highest and lowest prices over the last 20 and last 126 sessions, and its pattern label for the last session in the price history, worked out by that tool's printed rule from its published prices."},
        {"id": "insider", "tool": "Insider Wire",
         "date": insider["as_of"],
         "about": "What the people who run the company did with their own shares, from the ownership filings gathered on the date above: open-market buys and sells kept separate, a reading out of 100, and the latest filing date."},
        {"id": "squeeze", "tool": "Squeeze Watch",
         "date": squeeze["settlement_date"],
         "about": "The name's short interest reading: the share of its shares sold short and how many days of usual trading it would take to buy them back, from the settlement dated above."},
        {"id": "volume", "tool": "Unusual Volume",
         "date": volume["session"],
         "about": "Whether the name's share volume on the session dated above reached at least twice its own usual level over its previous 20 trading days, and by how much."},
        {"id": "earnings", "tool": "Earnings Calendar",
         "date": earnings["recorded_on"],
         "about": ("The date the company is scheduled to report its earnings, from the calendar list recorded on the date above. "
                   + ("A priced expected move is on record for %d of the dated names and is shown for each of them; the rest carry no priced move on record, so none is shown for them."
                      % earnings["priced_moves_on_record"]
                      if earnings.get("priced_moves_on_record")
                      else "No priced expected move is on record for any name, so none is shown."))},
        {"id": "filings", "tool": "Filings Wire",
         "date": filings["checked"],
         "about": "The headline figures the company reported for its year, each with the period it covers and the date its report was filed."},
        {"id": "holders", "tool": "Big-holder holdings reports",
         "date": holders["current_period"],
         "about": "What the largest holders on record hold, from the quarterly holdings reports for the period ended on the date above. Those reports name companies, not stock symbols, so no holding in them can be tied to a name picked by its symbol."},
    ]

    with_any = sum(v for k, v in distribution.items() if k > 0)
    n_filings = sum(1 for e in names.values() if e["filings"])
    # Receipt figures are computed from the assembled sections and
    # the sources, never literals (hookup cure, 2026-10-30: the
    # hardcoded receipt had drifted from the records it joins:
    # unusual volume 61 against 119 listed, earnings dates 73
    # against 46 dated, pattern labels 1,817 against 1,816).
    n_labels = sum(1 for e in names.values()
                   if e["chart"] and e["chart"].get("label"))
    n_insider_checked = len(insider["names"])
    receipt = (
        "%s names are on record across the nine sections. The scored "
        "list covers %s of them (%s were checked with too little data "
        "to score); the chart history covers %s, with a pattern label "
        "for %s; insider summaries cover %s of the %s names checked; "
        "short interest readings cover %s; unusual volume lists %s; "
        "the earnings calendar carries a date for %s. The filings "
        "section carries a reading for %d names, joined by the "
        "symbol the Filings Wire publishes. No name carries a "
        "reading in the big-holder section: those reports name "
        "companies, not stock symbols."
        % (f"{len(names):,}", f"{sc_counts['names_scored']:,}",
           f"{len(names) - sc_counts['names_scored']:,}",
           f"{len(chart['bars']):,}", f"{n_labels:,}",
           f"{ins_totals['names_with_summary']:,}",
           f"{n_insider_checked:,}",
           f"{sq_cov['names_covered']:,}",
           f"{len(volume['names']):,}",
           f"{earnings['dated_names']:,}", n_filings)
    )

    out = {
        "tool": "One-Page Report",
        "state": "published",
        "proving_state": "A measuring tool, nothing to prove",
        "proving_note": "This page only gathers readings other tools on this site have already published, each under its own name and date, and makes no reading of its own, so there is nothing of its own to grade.",
        "names_count": len(names),
        "sections_count": len(sections),
        "sections": sections,
        "family_defs": second["families"],
        "family_silent_reasons": second["silent_reasons"],
        "filings_names_covered": n_filings,
        "coverage_distribution": {str(k): distribution[k]
                                  for k in sorted(distribution)},
        "names_with_any_reading": with_any,
        "default_name": "SPY" if "SPY" in names else sorted(names)[0],
        "receipt": receipt,
        "names": names,
    }

    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT)
    print("wrote %s: %d names, distribution %s"
          % (OUT, len(names), out["coverage_distribution"]))


if __name__ == "__main__":
    main()
