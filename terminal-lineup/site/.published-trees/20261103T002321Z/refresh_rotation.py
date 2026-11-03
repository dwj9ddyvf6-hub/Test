#!/usr/bin/env python3
"""Refresh the Sector Rotation data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever.

Evidence class: the real daily price history behind the daily
scoring run (daily closing prices for every scored stock, 399
trading sessions from March 25, 2025 to October 23, 2026), plus
the sector assignment for each scored stock from the same
published constituent map the daily board itself uses, cross-
checked against the scored run's own published data (the board
card's summary, the full scored list, and the card's published
names' sectors). The rotation figures are computed directly from
those closing prices and those sector assignments,
deterministically: the same sources always produce the same file.

Reconstruction choices: a stock's change over a window is its
closing price on the price history's freshest session divided by
its closing price 5 (or 21) of its own trading sessions earlier,
minus one, in percent. A sector's figure is the plain average of
its counted stocks' changes; every stock counts once, whatever
its size. A stock is counted only if it has a sector on record,
traded on the freshest session, and has at least 21 of its own
sessions behind that close, so the 5-session and 21-session
figures for a sector always rest on the same counted stocks, and
each sector's counted number is printed beside its figures.
Stocks with a sector on record that did not trade on the
freshest session, or lack the sessions behind it, are counted
and stated, never silently dropped; stocks with no sector on
record are counted and stated the same way. Sectors are ranked
separately on each window by their unrounded average change,
highest first, ties broken by sector name so the order never
depends on file order; the printed averages are rounded to two
decimals. Labels, stated in plain words on the page: a sector is
turning when its 5-session average and its 21-session average
point in opposite directions (one a gain, the other a loss);
otherwise a sector ranked in the top three over 21 sessions is
leading, a sector ranked in the bottom three over 21 sessions
is lagging, and any other sector is in the middle. A sector with
fewer than 10 counted stocks is too thin to rank: it is named as
thin and shows its counts only, with no average, rank or label,
and it takes no part in the rankings. The rotation is computed
on the price history's own sessions, never mixed with the scored
run's session: the history's freshest session (October 23, 2026)
is the session the figures belong to, and the page shows the
stale state because that session is behind the last completed
session.

Scope: the counted universe is the stocks in the daily scoring
run, stated as such on the page. Those are stocks listed today,
so a stock that stopped trading earlier is not in the count; the
page says so in plain words. The figures are never presented as
the whole market, and no figure is shown for a sector the
records cannot support.

What the sources carry (and what this script therefore shows):
- The price history: per stock, dated daily bars with closing
  prices. Its freshest session (October 23, 2026) is the session
  this page headlines; all timestamps come from the sources,
  never from the clock.
- The scored run's published counts: checked, scored, and too
  little data, for the run's own session (October 27, 2026),
  recomputed from the full scored list.
- The constituent map's sector assignments: the refresh proves
  the map agrees with the board card on every one of the card's
  published names before trusting it for the rest, and counts
  how many scored stocks it covers (1,498 of 1,833 on the run of
  record; the other 335 have no sector on record).

Honesty rules:
- If the card, the full list, the constituent map and the price
  history disagree with each other in any of those checks, the
  script fails instead of publishing a mismatched page.
- A stock with no bar on the freshest session is not counted in
  any average; its absence is counted and stated, never treated
  as a zero change.
- Running this script twice on the same sources produces the
  same file, byte for byte.

Usage: python3 refresh_rotation.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "board_card.json")
FULL_PATH = os.path.join(SOURCE_DIR, "board_full.json")
BARS_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
GICS_PATH = os.path.expanduser(
    "~/workspace/femto-lean/config/gics_sectors.json")
SCREENER_PATH = os.path.join(HERE, "screener", "data.json")
OUT_PATH = os.path.join(HERE, "sector-rotation", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

SHORT_WINDOW = 5
LONG_WINDOW = 21
THIN_FLOOR = 10

SOURCE_WORDS = ("Daily closing prices for the stocks in the daily "
                "scoring run, over the price history on record, "
                "with each stock's sector from the published "
                "lists of the stocks that make up the big indexes")

DEFINITIONS = {
    "average": ("A sector's figure is the average of its counted "
                "stocks' price changes over the window: each "
                "counted stock's closing price on the last "
                "session in the price history, compared with its "
                "closing price 5 (or 21) of its own trading "
                "sessions earlier. Every counted stock counts "
                "once, whatever its size, and the number counted "
                "is printed beside the figure."),
    "turning": ("A sector is turning when its average change "
                "over the last 5 sessions points the opposite "
                "way from its average change over the last 21 "
                "sessions: rising lately after falling over the "
                "longer stretch, or falling lately after rising."),
    "leading_lagging": ("A sector that is not turning and ranks "
                        "in the top three over 21 sessions is "
                        "leading; one that is not turning and "
                        "ranks in the bottom three over 21 "
                        "sessions is lagging; any other sector is "
                        "in the middle."),
    "thin": ("A sector with fewer than 10 counted stocks is too "
             "thin to rank: it is named as thin and shows its "
             "counts only, with no average and no label."),
    "universe": ("The count covers the stocks in the daily "
                 "scoring run, which are stocks listed today, so "
                 "stocks that stopped trading earlier are not "
                 "in it."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Sector Rotation refresh: {message}", file=sys.stderr)
    return 1


SCAN_PATH = os.path.join(HERE, "sector-rotation",
                         "sector_scan_20261030.json")


def _stated_limit(unmapped_sorted):
    """RC-12 stated limit (2026-10-30): the four route scan in
    scan_sector_sources.py found no sector for any unmapped
    name in the terminal's own stores, the chain store
    metadata, the EDGAR company record, or the panel metadata.
    Published here in plain words with the count, which is the
    terminal state of this source limit. If the scan record is
    missing, the block says so instead of claiming the scan."""
    base = {"state": "stated_limit",
            "count": len(unmapped_sorted),
            "names": unmapped_sorted}
    if not os.path.exists(SCAN_PATH):
        base["text"] = (
            f"{len(unmapped_sorted)} scored names have no sector "
            "on record. The four route scan record is not on "
            "disk, so no stronger statement is published.")
        return base
    with open(SCAN_PATH, encoding="utf-8") as fh:
        scan = json.load(fh)
    base["scan_record"] = "sector-rotation/sector_scan_20261030.json"
    base["routes_checked"] = sorted((scan.get("routes") or {}).keys())
    base["found_count"] = scan.get("found_count")
    base["text"] = (
        f"Stated limit: {scan.get('still_unmapped_count')} scored "
        "names have no sector on any record this terminal can "
        "read. On 2026-10-30 four more routes were checked and "
        "each came back empty: every data file in the terminal's "
        "own stores, the options chain store's metadata (it "
        "carries price rows for three index funds only, with no "
        "sector field), the EDGAR company record (it carries a "
        "company number, ticker and company name only, no sector "
        "or industry field), and the price panel's metadata (it "
        "carries price rows and session dates only). All of the "
        "names are listed by name below. No sector is assigned "
        "to a name the records do not carry one for.")
    return base


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH, GICS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars = load_json(BARS_PATH)
    gics = load_json(GICS_PATH).get("symbols", {})

    # --- Second sector source, held in the terminal's own
    # records (RC-12 cure, 2026-10-30): the Screener's published
    # record carries a sector per scored name. Where it carries
    # one the constituent lists miss, that sector is adopted
    # (counted as filled from the terminal's records); where the
    # two records disagree on a name, the refresh fails closed
    # rather than publish a contested sector. ---
    screener = load_json(SCREENER_PATH)
    screener_sectors = {}
    for n in screener.get("names") or []:
        if n.get("symbol") and n.get("sector"):
            screener_sectors[n["symbol"]] = n["sector"]
    filled_from_terminal = []
    for sym, sec in screener_sectors.items():
        listed = (gics.get(sym) or {}).get("sector")
        if listed and listed != sec:
            return fail(f"the Screener's record gives {sym} the "
                        f"sector {sec!r} but the constituent lists "
                        f"say {listed!r}; refusing to publish a "
                        "contested sector.")
        if not listed:
            gics[sym] = {"sector": sec}
            filled_from_terminal.append(sym)

    summary = card["summary"]
    run_session = summary["as_of_session"]
    if full.get("as_of_session") != run_session:
        return fail(f"the full scored list is for "
                    f"{full.get('as_of_session')} but the board "
                    f"card is for {run_session}; refusing to "
                    "publish a mismatched page.")

    # --- Recompute the scored run's published counts from its
    # full list; the card must agree with its own list. ---
    rows = full["rows"]
    scored = [r for r in rows if not r.get("insufficient_data")]
    short = [r for r in rows if r.get("insufficient_data")]
    recomputed = {
        "universe": len(rows),
        "scored": len(scored),
        "insufficient_data": len(short),
        "qualified": sum(1 for r in scored if r["qualified"]),
    }
    for key, value in recomputed.items():
        if summary.get(key) != value:
            return fail(f"the card summary says {key}="
                        f"{summary.get(key)} but the full list "
                        f"holds {value}; refusing to publish a "
                        "mismatched page.")

    # --- Prove the constituent map against the card's published
    # names before trusting its sector assignments for the rest.
    for row in card["board"]:
        entry = gics.get(row["symbol"]) or {}
        if entry.get("sector") != row.get("sector"):
            return fail(f"the constituent map gives "
                        f"{row['symbol']} the sector "
                        f"{entry.get('sector')!r} but the board "
                        f"card says {row.get('sector')!r}; "
                        "refusing to publish sectors from a map "
                        "that disagrees with the card.")

    # --- The price history must hold exactly the scored names:
    # every scored stock present, every too-little-data stock
    # absent. That is the history agreeing with the scored run's
    # own published data. ---
    scored_names = {r["symbol"] for r in scored}
    short_names = {r["symbol"] for r in short}
    bar_names = set(bars)
    if bar_names != scored_names:
        return fail(f"the price history holds {len(bar_names)} "
                    f"stocks but the scored run scored "
                    f"{len(scored_names)}; the names differ "
                    f"(history only: "
                    f"{sorted(bar_names - scored_names)[:5]}, "
                    f"run only: "
                    f"{sorted(scored_names - bar_names)[:5]}); "
                    "refusing to publish a mismatched page.")
    if bar_names & short_names:
        return fail("the price history holds stocks the scored "
                    "run set aside for too little data: "
                    f"{sorted(bar_names & short_names)}; "
                    "refusing to publish a mismatched page.")
    if not bars:
        return fail("the price history is empty; refusing to "
                    "publish.")

    # --- Per-stock closing series, dates strictly increasing. ---
    series = {}
    calendar = set()
    for symbol, stock_rows in bars.items():
        dates = []
        closes = []
        prev = None
        for row in stock_rows:
            date, close = row[0], row[4]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            if not isinstance(close, (int, float)):
                return fail(f"{symbol} has a closing price that "
                            f"is not a number on {date}; refusing "
                            "to publish.")
            prev = date
            dates.append(date)
            closes.append(float(close))
            calendar.add(date)
        series[symbol] = (dates, closes,
                          {d: i for i, d in enumerate(dates)})
    if not calendar:
        return fail("the price history holds no dated bars; "
                    "refusing to publish.")
    calendar = sorted(calendar)
    freshest = calendar[-1]
    if len(calendar) <= LONG_WINDOW:
        return fail(f"the price history holds only "
                    f"{len(calendar)} sessions, too few for a "
                    f"{LONG_WINDOW}-session window; refusing to "
                    "publish.")

    # --- Per-sector changes, anchored on the freshest session. ---
    sectors = {}
    with_sector = 0
    without_sector = 0
    unmapped_names = []
    not_counted = 0
    counted_total = 0
    for symbol in sorted(scored_names):
        entry = gics.get(symbol) or {}
        sector = entry.get("sector")
        if not sector:
            without_sector += 1
            unmapped_names.append(symbol)
            continue
        with_sector += 1
        cell = sectors.setdefault(
            sector, {"names_on_record": 0, "counted": 0,
                     "changes_5": [], "changes_21": []})
        cell["names_on_record"] += 1
        dates, closes, pos = series[symbol]
        i = pos.get(freshest)
        if i is None or i < LONG_WINDOW:
            not_counted += 1
            continue
        cell["counted"] += 1
        counted_total += 1
        cell["changes_5"].append(
            (closes[i] / closes[i - SHORT_WINDOW] - 1.0) * 100.0)
        cell["changes_21"].append(
            (closes[i] / closes[i - LONG_WINDOW] - 1.0) * 100.0)

    ranked = []
    thin = []
    for name in sorted(sectors):
        cell = sectors[name]
        if cell["counted"] == 0:
            return fail(f"sector {name} has names on record but "
                        "none counted on the freshest session; "
                        "refusing to publish a sector with no "
                        "honest state.")
        row = {"sector": name,
               "names_on_record": cell["names_on_record"],
               "names_counted": cell["counted"]}
        if cell["counted"] < THIN_FLOOR:
            row["thin"] = True
            thin.append(row)
            continue
        row["thin"] = False
        row["_avg5"] = sum(cell["changes_5"]) / cell["counted"]
        row["_avg21"] = sum(cell["changes_21"]) / cell["counted"]
        ranked.append(row)
    if not ranked:
        return fail("no sector has enough counted stocks to "
                    "rank; refusing to publish an empty page.")

    for key, rank_key in (("_avg5", "rank_5"), ("_avg21", "rank_21")):
        order = sorted(ranked,
                       key=lambda r: (-r[key], r["sector"]))
        for idx, row in enumerate(order, 1):
            row[rank_key] = idx
    n_ranked = len(ranked)
    for row in ranked:
        avg5, avg21 = row.pop("_avg5"), row.pop("_avg21")
        row["avg_change_5_pct"] = round(avg5, 2)
        row["avg_change_21_pct"] = round(avg21, 2)
        if (avg5 > 0 > avg21) or (avg5 < 0 < avg21):
            row["label"] = "Turning"
        elif row["rank_21"] <= 3:
            row["label"] = "Leading"
        elif row["rank_21"] >= n_ranked - 2:
            row["label"] = "Lagging"
        else:
            row["label"] = "In the middle"
    ranked.sort(key=lambda r: r["rank_21"])

    universe_words = (
        f"Counted from the {len(scored_names):,} stocks in the "
        f"daily scoring run (the run checked "
        f"{summary['universe']:,} stocks for {run_session} and "
        f"scored {summary['scored']:,}; "
        f"{summary['insufficient_data']} had too little data to "
        "score and are not counted)")

    data = {
        "tool": "Sector Rotation",
        "session": freshest,
        "scored_run_session": run_session,
        "source": SOURCE_WORDS,
        "history_sessions_on_record": len(calendar),
        "history_from": calendar[0],
        "history_to": freshest,
        "windows": {
            "sessions_5": {"from": calendar[-1 - SHORT_WINDOW],
                           "to": freshest},
            "sessions_21": {"from": calendar[-1 - LONG_WINDOW],
                            "to": freshest},
        },
        "counts": {
            "names_checked": summary["universe"],
            "names_scored": summary["scored"],
            "names_too_little_data": summary["insufficient_data"],
            "names_with_sector_on_record": with_sector,
            "names_without_sector_on_record": without_sector,
            "names_with_sector_not_counted": not_counted,
            "names_counted": counted_total,
            "sectors_ranked": n_ranked,
            "sectors_thin": len(thin),
        },
        "sectors": ranked,
        "thin_sectors": thin,
        "names_filled_from_terminal_records": len(
            [n for n in filled_from_terminal if n in scored_names]),
        "stated_limit": _stated_limit(sorted(unmapped_names)),
        "unmapped_names": sorted(unmapped_names),
        "unmapped_note": (
            "These scored names are listed by name because no "
            "sector for them exists in the published constituent "
            "lists this page reads or in any other record the "
            "terminal holds (the Screener's published record is "
            "checked on every run, and a sector appearing there "
            "for one of these names would be adopted and counted "
            "above). They are named as unmapped rather than "
            "assigned a sector the records do not carry."),
        "definitions": DEFINITIONS,
        "coverage": (
            f"{universe_words}; {with_sector:,} of the scored "
            f"stocks have a sector on record and "
            f"{without_sector:,} do not; of the ones with a "
            f"sector, {counted_total:,} traded on {freshest} "
            f"with the {LONG_WINDOW} sessions behind them and "
            f"are counted in the averages, and {not_counted} did "
            "not trade that session and are not counted; the "
            f"{without_sector:,} names with no sector on record "
            "are listed by name on this page as unmapped, with "
            "the reason"),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {freshest}, "
          f"{n_ranked} sectors ranked, {len(thin)} thin, "
          f"{counted_total} stocks counted, {with_sector} with "
          f"a sector on record, {without_sector} without, "
          f"scored run {run_session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
