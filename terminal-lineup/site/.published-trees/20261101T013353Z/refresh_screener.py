#!/usr/bin/env python3
"""Refresh The Screener data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever.

Evidence class: the freshest full scored run on record (every name
that was scored, not just the published top 50), cross-checked
against the board card's own summary for the same trading day and
against the permanent log entry that records when that day's board
was published. Sector and index membership for each name come from
the same published constituent map the board itself uses, and the
refresh proves that map agrees with the board card on every one of
the card's published names before trusting it for the rest.

Reconstruction choices: the filter controls on the page are the
subset of the published filter module's families that this run can
actually feed (sector choice and index membership, matched exactly
the way the module matches them), plus plain conditions on the run's
own fields (score at least, closing price between two values, checks
in favor at least, passed every check only), with results sorted by
score, highest first, the module's descending-score order. The
module's other families (exchange, country, company size over $10
billion, chart pattern tags, candlestick tags) cannot be fed by
anything the scored run carries, so they are not offered and not
faked. A name whose sector is not on record stays in the list,
shows its sector as not on record, and never matches a sector
choice: absence is stated, never guessed.

Scope: this is a published subset of filters, not the full
commercial filter catalog (the commercial screener this style of
filtering comes from publishes roughly 82 controls). Sector is
shown only for names the constituent map covers; the rest are
labelled not on record.

What the sources carry (and what this script therefore shows):
- The full ranked list covers every name the run checked: symbol,
  closing price, combined score out of 100, how many of the eight
  checks lined up in its favor, how much of the data behind the
  score was present, and whether it passed every check. Names with
  too little data to score are flagged as such and carry no score.
- The board card's summary states the run's counts (checked,
  scored, too little data, passed every check); the refresh
  recomputes every one from the full list and fails if any disagree.
- The card's own date field is the start of its price history
  window, not a publication time, so the moment this run was
  published is taken from the permanent log entry for the session.

Honesty rules:
- Names with too little data are left out of the data file; their
  count is carried in it so the page can state it plainly.
- All timestamps and figures come from the source files, never
  from the clock, so running this script twice produces the same
  file.
- If the card, the full list, the constituent map and the log
  disagree, the script fails instead of publishing a mismatched
  page.

Usage: python3 refresh_screener.py
"""

import json
import os
import sys

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
OUT_PATH = os.path.join(HERE, "screener", "data.json")

# The constituent map names the big indexes the way the map itself
# does; the page shows these plain names for the index choice.
INDEX_WORDS = {
    "sp500": "S&P 500",
    "sp400": "S&P 400",
    "sp600": "S&P 600",
}

CHECKS_TOTAL = 8


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fail(message):
    print(f"Screener refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FULL_PATH, LOG_PATH, GICS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    log_rows = load_log(LOG_PATH)
    gics = load_json(GICS_PATH).get("symbols", {})

    summary = card["summary"]
    session = summary["as_of_session"]
    published_rows = card["board"]

    # --- Cross-check the card against the full ranked list. ---
    if full.get("as_of_session") != session:
        return fail(f"the full list is for {full.get('as_of_session')} "
                    f"but the board card is for {session}; refusing "
                    "to publish a mismatched page.")
    full_rows = full["rows"]
    scored = [r for r in full_rows if not r.get("insufficient_data")]
    short = [r for r in full_rows if r.get("insufficient_data")]
    recomputed = {
        "universe": len(full_rows),
        "scored": len(scored),
        "insufficient_data": len(short),
        "qualified": sum(1 for r in scored if r["qualified"]),
    }
    for key, value in recomputed.items():
        if summary.get(key) != value:
            return fail(f"the card summary says {key}="
                        f"{summary.get(key)} but the full list holds "
                        f"{value}; refusing to publish a mismatched "
                        "page.")
    top = scored[:len(published_rows)]
    for got, want in zip(published_rows, top):
        if (got["symbol"], got["score"], got["qualified"]) != \
                (want["symbol"], want["score"], want["qualified"]):
            return fail(f"the card's published names do not match "
                        f"the top of the full list at {got['symbol']}; "
                        "refusing to publish a mismatched page.")

    # --- Prove the constituent map against the card before using it
    # for names the card does not publish. ---
    for row in published_rows:
        entry = gics.get(row["symbol"]) or {}
        if entry.get("sector") != row.get("sector"):
            return fail(f"the constituent map gives "
                        f"{row['symbol']} the sector "
                        f"{entry.get('sector')!r} but the board card "
                        f"says {row.get('sector')!r}; refusing to "
                        "publish sectors from a map that disagrees "
                        "with the card.")
        if entry and entry.get("index") not in INDEX_WORDS:
            return fail(f"the constituent map lists "
                        f"{row['symbol']} in an index this page "
                        f"does not know how to name: "
                        f"{entry.get('index')!r}; refusing to guess.")

    # --- When was this session's board published? From the log. ---
    published_at = None
    for r in log_rows:
        if r.get("component") == "board-summary" and \
                r.get("value", {}).get("as_of_session") == session:
            if published_at is None or r["ts_utc"] > published_at:
                published_at = r["ts_utc"]
    if published_at is None:
        return fail(f"the log holds no board publication for session "
                    f"{session}; refusing to show names without a "
                    "publication time.")

    # --- Build one row per scored name, in the run's own order
    # (highest score first). ---
    names = []
    sectors = set()
    with_sector = 0
    for row in scored:
        for field in ("close", "score", "confirming", "dc",
                      "qualified"):
            if row.get(field) is None:
                return fail(f"{row['symbol']} is scored but carries "
                            f"no {field}; refusing to publish a "
                            "partial row.")
        if not (0 <= row["confirming"] <= CHECKS_TOTAL):
            return fail(f"{row['symbol']} says "
                        f"{row['confirming']} checks in favor, "
                        f"outside the possible 0 to {CHECKS_TOTAL}; "
                        "refusing to publish it.")
        entry = gics.get(row["symbol"]) or {}
        sector = entry.get("sector")
        index = INDEX_WORDS.get(entry.get("index")) \
            if entry.get("index") else None
        if sector:
            sectors.add(sector)
            with_sector += 1
        names.append({
            "symbol": row["symbol"],
            "sector": sector,
            "index": index,
            "close": row["close"],
            "score": row["score"],
            "checks_in_favor": row["confirming"],
            "checks_total": CHECKS_TOTAL,
            "data_behind_score_pct": row["dc"],
            "passed_every_check": bool(row["qualified"]),
        })

    data = {
        "tool": "The Screener",
        "session": session,
        "published_at_utc": published_at,
        "source": "Daily price and trading history for each stock, "
                  "plus public filings on the positions big "
                  "investors report, combined into the same eight "
                  "checks for every name; each name's sector and "
                  "index come from the published lists of the "
                  "stocks that make up those indexes",
        "counts": {
            "names_checked": summary["universe"],
            "names_scored": summary["scored"],
            "not_enough_data": summary["insufficient_data"],
            "passed_every_check_all": summary["qualified"],
            "names_with_sector_on_record": with_sector,
        },
        "sectors": sorted(sectors),
        "indexes": [INDEX_WORDS[k] for k in
                    ("sp500", "sp400", "sp600")
                    if any(n["index"] == INDEX_WORDS[k] for n in names)],
        "names": names,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, {len(names)} scored "
          f"names, {with_sector} with a sector on record, "
          f"{summary['insufficient_data']} left out for too little "
          f"data, published {published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
