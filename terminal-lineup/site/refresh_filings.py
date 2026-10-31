#!/usr/bin/env python3
"""Refresh the Filings Wire data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the stored company-facts record itself: one stored
file per company, each holding the reported figures the lane keeps,
every figure carrying the period it covers, the date its report was
filed, and the kind of report it came from. Three published records
stamp the same collection's state (the gathering record, its
published card, and the published daily summary); all three stamps
must agree with each other and with the files actually stored, or
the refresh stops.

Reconstruction choices: figures are read the way the lane reads
them: annual figures only (a flow figure must cover 330 to 400 days;
a balance figure counts only as a year-end figure). Where a figure
can be reported under more than one name, the names are read in the
lane's order and the choice is made per period: the first name wins
for each period it covers, later names fill periods the first name
lacks. Per period, the latest report filed on or before the checked
date wins, so a corrected figure counts only from the date its
correction was filed. Money figures are shown in dollars and share
counts in shares, exactly as stored, never rescaled or estimated.
A figure the record does not carry for a company is published as
not on record for that company, never as zero and never filled in.

Non-claims: this tool publishes no list of filing events, because
the record does not keep one: the only filing detail stored is the
kind of report and the filed date attached to each figure itself,
and only those are shown. It carries no cash-balance figure (the
lane does not keep one) and its borrowing figure is long-term
borrowing only. It makes no claim about any company whose facts are
not stored.

Fail-closed rules: if the three state stamps disagree with each
other; if the stamps' state disagrees with the files actually
stored (a no-data stamp while files are stored, or a live stamp
while none are); if a stored file cannot be read, carries a figure
that is not a number, or a period or filed date that is not a date,
the refresh stops and publishes nothing.

Honesty rules:
- Dates are read off the sources, never from the clock. The
  checked date comes from the state stamps, so running this script
  twice produces the same file.
- Absence is not zero: no stored company is published as the plain
  not-on-record state, and a missing figure stays missing.

Usage: python3 refresh_filings.py
"""

import gzip
import json
import os
import re
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
FACTS_DIR = os.path.join(MORGUE, "state", "morgue", "facts")
TICKERS_PATH = os.path.join(MORGUE, "data_cache", "edgar",
                            "company_tickers.json")
EXT_PATH = os.path.join(MORGUE, "state", "morgue", "ext.json")
CARD_PATH = os.path.join(MORGUE, "output", "ext_card.json")
FEED_PATH = os.path.join(MORGUE, "output", "morgue-feed.json")
OUT_PATH = os.path.join(HERE, "filings-wire", "data.json")

SOURCE_WORDS = ("The yearly financial reports companies publish: "
                "each figure kept with the period it covers and "
                "the date its report was filed")
DELAY_WORDS = ("A figure appears here only from the date its "
               "report was filed, so a corrected figure counts "
               "only from the date the correction was filed")
EMPTY_COVERAGE = ("No company's reported figures are on record "
                  "yet: 0 companies on record, no figure on record "
                  "for any company, and no most recent filing date. "
                  "Nothing is shown for any company because there "
                  "is no stored report to show")

# Lane concept order and tag order, mirrored from the lane's own
# concept list (read from the lane on 2026-10-28). Plain reader
# labels and units only; the stored tag names never reach the page.
FIGURES = [
    ("revenue", "Sales", "dollars",
     ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
      "SalesRevenueNet"]),
    ("net_income", "Earnings", "dollars", ["NetIncomeLoss"]),
    ("gross_profit", "Gross profit", "dollars", ["GrossProfit"]),
    ("cost_of_revenue", "Cost of sales", "dollars",
     ["CostOfRevenue", "CostOfGoodsAndServicesSold"]),
    ("ebit", "Operating earnings", "dollars", ["OperatingIncomeLoss"]),
    ("cfo", "Cash from running the business", "dollars",
     ["NetCashProvidedByUsedInOperatingActivities"]),
    ("assets", "Everything the company owns", "dollars", ["Assets"]),
    ("assets_current", "What it owns that can turn into cash within a year",
     "dollars", ["AssetsCurrent"]),
    ("liabilities", "Everything the company owes", "dollars",
     ["Liabilities"]),
    ("liabilities_current", "What it owes within a year", "dollars",
     ["LiabilitiesCurrent"]),
    ("ltd", "Long-term borrowing", "dollars",
     ["LongTermDebtNoncurrent", "LongTermDebt"]),
    ("equity", "The owners' stake", "dollars", ["StockholdersEquity"]),
    ("retained", "Earnings kept in the business", "dollars",
     ["RetainedEarningsAccumulatedDeficit"]),
    ("shares", "Shares", "shares",
     ["WeightedAverageNumberOfSharesOutstandingBasic",
      "CommonStockSharesOutstanding"]),
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Filings Wire refresh: {message}", file=sys.stderr)
    return 1


def lane_stamp(doc):
    lanes = (doc.get("lanes") or {}).get("lanes") or {}
    return lanes.get("sec_facts")


def plain_report_kind(form):
    if not form:
        return None
    if form.endswith("/A"):
        return "Yearly report, corrected"
    return "Yearly report"


def stored_files():
    try:
        names = os.listdir(FACTS_DIR)
    except OSError:
        return []
    return sorted(n for n in names
                  if re.fullmatch(r"CIK\d{10}\.json\.gz", n))


def annual_series(facts, key, tags, asof):
    """[(period_end, value, filed, form)] per the lane's annual rule:
    per tag, per period, latest filing at or before asof wins; tags
    merge per period in listed order."""
    merged = {}
    for tag in tags:
        best = {}
        for f in facts:
            if f.get("k") != key or f.get("tag") != tag:
                continue
            if f["filed"] > asof:
                continue
            if f.get("start"):
                span = (date.fromisoformat(f["end"])
                        - date.fromisoformat(f["start"])).days
                if not 330 <= span <= 400:
                    continue
            elif f.get("fp") != "FY":
                continue
            cur = best.get(f["end"])
            if cur is None or f["filed"] > cur[2]:
                best[f["end"]] = (f["end"], f["val"], f["filed"],
                                  f.get("form"))
        for end, row in best.items():
            if end not in merged:
                merged[end] = row
    return [merged[e] for e in sorted(merged)]


def build():
    for path in (EXT_PATH, CARD_PATH, FEED_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    stamps = []
    for path in (EXT_PATH, CARD_PATH, FEED_PATH):
        stamp = lane_stamp(load_json(path))
        if not stamp:
            return fail("one of the records carries no company "
                        "reports state stamp; refusing to guess "
                        "the collection's state.")
        stamps.append(stamp)
    if stamps[0] != stamps[1] or stamps[0] != stamps[2]:
        return fail("the records stamp the company reports "
                    "collection differently; refusing to publish "
                    "until they agree.")
    stamp = stamps[0]
    as_of = stamp.get("as_of")
    if not as_of:
        return fail("the state stamp carries no date; refusing "
                    "to guess.")

    files = stored_files()

    if not files:
        if stamp.get("status") != "no_data" \
                or stamp.get("reason") != "no company's facts stored yet":
            return fail("no company is stored, but the state stamp "
                        "does not say the collection is empty; "
                        "refusing to publish a state the records "
                        "do not agree on.")
        data = {
            "tool": "Filings Wire",
            "state": "not_on_record",
            "checked": as_of,
            "companies_on_record": 0,
            "freshest_filed": None,
            "companies": [],
            "source": SOURCE_WORDS,
            "delay": DELAY_WORDS,
            "coverage": EMPTY_COVERAGE,
            "receipt": {
                "checked": as_of,
                "source": SOURCE_WORDS,
                "coverage": EMPTY_COVERAGE,
            },
        }
    else:
        if stamp.get("status") == "no_data":
            return fail(f"{len(files)} company file(s) are stored, "
                        "but the state stamp still says none is "
                        "stored; refusing to publish until the "
                        "records agree.")
        # Hookup wire (2026-10-30): companies were published by
        # their EDGAR number only, so no consumer could join this
        # wire to a stock symbol. The EDGAR ticker map the facts
        # lane itself resolves through is the one source for the
        # number-to-symbol join; publish symbol and company name
        # from it. A number the map does not carry stays unnamed
        # here (symbol null), never guessed.
        if not os.path.exists(TICKERS_PATH):
            return fail("the EDGAR ticker map was not found; "
                        "refusing to publish companies no consumer "
                        "can join to a name.")
        try:
            ticker_doc = load_json(TICKERS_PATH)
        except (OSError, ValueError):
            return fail("the EDGAR ticker map cannot be read; "
                        "refusing to publish.")
        by_cik = {}
        for entry in ticker_doc.values():
            if isinstance(entry, dict) and entry.get("ticker"):
                by_cik.setdefault(int(entry["cik_str"]), []).append(
                    (entry["ticker"], entry.get("title")))
        # One number can carry several tickers (a common stock, a
        # warrant, a second share class). The facts lane fetched
        # these files by resolving the tracked symbols forward to
        # numbers, so the tracked set inverted is the join of
        # record; outside it, a number with exactly one ticker
        # joins to that ticker, and a number with several stays
        # unnamed rather than guessed.
        inst_path = os.path.join(MORGUE, "output", "inst_bundle.json")
        tracked = set()
        if os.path.exists(inst_path):
            try:
                tracked = set(load_json(inst_path))
            except (OSError, ValueError):
                tracked = set()
        resolved = {}
        for cik, options in by_cik.items():
            tracked_hits = [o for o in options if o[0] in tracked]
            if len(tracked_hits) == 1:
                resolved[cik] = tracked_hits[0]
            elif len(options) == 1:
                resolved[cik] = options[0]
        by_cik = resolved
        companies = []
        freshest = None
        for name in files:
            path = os.path.join(FACTS_DIR, name)
            try:
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError, EOFError):
                return fail(f"the stored file {name} cannot be "
                            "read; refusing to publish a partial "
                            "wire.")
            facts = doc.get("facts") or []
            for f in facts:
                if not isinstance(f.get("val"), (int, float)) \
                        or isinstance(f.get("val"), bool):
                    return fail("a stored figure is not a number; "
                                "refusing to publish.")
                try:
                    date.fromisoformat(f["end"])
                    date.fromisoformat(f["filed"])
                    if f.get("start"):
                        date.fromisoformat(f["start"])
                except (KeyError, TypeError, ValueError):
                    return fail("a stored figure carries a period "
                                "or filed date that is not a date; "
                                "refusing to publish.")
            figures = []
            for key, label, unit, tags in FIGURES:
                series = annual_series(facts, key, tags, as_of)
                if not series:
                    figures.append({"label": label, "unit": unit,
                                    "state": "not_on_record",
                                    "readings": []})
                else:
                    readings = []
                    for end, val, filed, form in series:
                        if freshest is None or filed > freshest:
                            freshest = filed
                        readings.append({
                            "period_end": end, "value": val,
                            "filed": filed,
                            "report_kind": plain_report_kind(form),
                        })
                    figures.append({"label": label, "unit": unit,
                                    "state": "recorded",
                                    "readings": readings})
            symbol, title = by_cik.get(int(name[3:13]),
                                       (None, None))
            companies.append({
                "company_number": name[3:13].lstrip("0") or "0",
                "symbol": symbol,
                "company_name": title,
                "figures": figures,
            })
        coverage = (f"{len(companies)} company file(s) on record, "
                    f"checked {as_of}. A figure a company has no "
                    "stored annual reading for is shown as not on "
                    "record, never as zero")
        data = {
            "tool": "Filings Wire",
            "state": "on_record",
            "checked": as_of,
            "companies_on_record": len(companies),
            "freshest_filed": freshest,
            "companies": companies,
            "source": SOURCE_WORDS,
            "delay": DELAY_WORDS,
            "coverage": coverage,
            "receipt": {
                "checked": as_of,
                "source": SOURCE_WORDS,
                "coverage": coverage,
            },
        }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (state {data['state']}, "
          f"{data['companies_on_record']} companies on record, "
          f"checked {as_of})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
