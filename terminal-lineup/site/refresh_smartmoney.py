#!/usr/bin/env python3
"""Refresh the Smart Money Tracker data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the change view over the same record the 13F
Tracker publishes: the two stored quarterly holdings filing sets
(filings received March to May 2026 and June to August 2026). Each
report carries the filing manager's name, the period it covers, the
date it was filed, and one row per name held with the share count
and the dollar value. This page publishes only changes those rows
themselves carry, between the two quarters on record: the period
ended March 31, 2026 and the period ended June 30, 2026. That is
exactly one step of change, and the page says so. The aggregate
ownership scores kept elsewhere on this site and the company
insider summaries are different records; neither is merged into
this page (the 13F Tracker itself states they are different
records, and its published figures are used here only as the
cross-check this refresh must agree with).

Reconstruction choices: a manager's report of record is their
latest filing for the period across both sets, counting both first
reports and corrected reports; notice-only filings never count.
Only plain share rows count: rows marked as options (puts or
calls) are left out, and rows for the same name held by the same
manager are added together. Names are grouped by the identifier
the filings themselves carry for the name; a name's printed name
is the name string its rows use most often across the two sets
(name strings are free text and vary from filer to filer; an
alphabetical choice would print the wrong company for some
identifiers, so the most common string is the only honest one).
The change view covers the holders who reported plain-share
holdings in BOTH periods (8,719 of the holders on record): a
holder with no report in one period has nothing to compare, and
their holdings are never counted as started or ended. Across
those holders the page counts holdings started, holdings ended
and holdings kept, and on kept holdings the shares added and the
shares trimmed. The four leader lists name the 15 names at the
top of each count, exactly as recorded. Started and ended lists
carry a plain-words note on the page: a name can appear there
because its identifier changed, because a company was newly
listed, or because it was spun off from another company, not only
because holders chose it anew, so those two lists are never
presented as buying or selling. Per-holder change summaries are
published for the 20 largest holders only, exactly as the 13F
Tracker publishes them, and the page says so. No percentage is
published anywhere on this page: every figure is a count or a
share count.

Non-claims: this tool does not show every holder's changes, only
the full-set totals and leader lists and the 20 largest holders'
summaries. It makes no claim about trading after the period
ended: these reports are filed weeks after the period they
cover, and the page prints both periods and the filing-date
ranges beside the figures.

Fail-closed rules: if either stored set is missing or the sets
on record are not exactly the two on record; if the recomputed
periods or holder counts disagree with the 13F Tracker's
published record; if any of the 20 largest holders' published
figures (total value, holding count, started / ended / kept
counts, earlier total value) disagrees with the recomputation
from the filing rows; if the kept / started / ended counts do
not add up to the position counts of the compared holders; if
the Proving Ground's published vocabulary does not carry the
measuring state this page uses; or if any assembled words carry
an internal file name or desk wording, the refresh stops and
publishes nothing.

Honesty rules:
- Dates are read off the sources, never from the clock. Running
  this script twice produces the same file.
- Absence is not zero: a holder with no report in a period is
  outside the comparison, never a change from zero.

Usage: python3 refresh_smartmoney.py
"""

import io
import json
import os
import shutil
import sqlite3
import sys
import zipfile
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/workspace/morgue/data_cache/13f")
TRACKER_PATH = os.path.join(HERE, "13f-tracker", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "smart-money-tracker", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

SOURCE_WORDS = ("The quarterly holdings reports large holders file "
                "with the Securities and Exchange Commission: each "
                "report names the holder, the period it covers, "
                "the date it was filed, and every name held with "
                "its share count and dollar value")
LAG_WORDS = ("These reports are always weeks old: holders file "
             "them after the period ends, so every figure here is "
             "what the holder reported holding on the period date, "
             "filed on the filing date shown")
STEP_WORDS = ("Two quarters are on record, so there is exactly one "
              "step of change to show: from the period ended "
              "March 31, 2026 to the period ended June 30, 2026. "
              "Nothing here shows a longer run of changes.")
CHURN_WORDS = ("A name can appear on the started or ended lists "
               "because its identifier changed, because a company "
               "was newly listed, or because it was spun off from "
               "another company, not only because holders chose "
               "it anew. Those two lists count what the reports "
               "show; they are not, on their own, buying or "
               "selling.")
NAME_WORDS = ("Holders write company names in their own words, so "
              "the same name can be written many ways across the "
              "reports. Each name below is printed the way its "
              "reports write it most often. Two entries can print "
              "the same name when the filings carry that name under "
              "two different identifiers; each entry is one "
              "identifier's record, exactly as filed.")
TOP_LIST = 15
TOP_HOLDERS = 20

FORBIDDEN = (".json", ".md", ".py", ".jsonl", ".tsv", ".zip",
             "morgue", "CUSIP", "cusip", "INFOTABLE", "sleeve",
             "Midna", "workspace", "data_cache")


def fail(message):
    print(f"Smart Money Tracker refresh: {message}", file=sys.stderr)
    return 1


def parse_date(text):
    return datetime.strptime(text.strip(), "%d-%b-%Y").date().isoformat()


def read_tsv(zf, member):
    with zf.open(member) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
        header = text.readline().rstrip("\n").split("\t")
        col = {name: i for i, name in enumerate(header)}
        for line in text:
            p = line.rstrip("\n").split("\t")
            if len(p) < len(header):
                continue
            yield col, p


def collect_filings(zip_paths):
    """{(cik, period): filing} latest filing per manager+period,
    plus {period: count}."""
    best = {}
    period_counts = {}
    for path in zip_paths:
        zf = zipfile.ZipFile(path)
        subs = {}
        for col, p in read_tsv(zf, "SUBMISSION.tsv"):
            if p[col["SUBMISSIONTYPE"]] not in ("13F-HR", "13F-HR/A"):
                continue
            subs[p[col["ACCESSION_NUMBER"]]] = {
                "accession": p[col["ACCESSION_NUMBER"]],
                "cik": p[col["CIK"]],
                "period": parse_date(p[col["PERIODOFREPORT"]]),
                "filed": parse_date(p[col["FILING_DATE"]]),
                "amended": p[col["SUBMISSIONTYPE"]].endswith("/A"),
            }
        names = {}
        for col, p in read_tsv(zf, "COVERPAGE.tsv"):
            names[p[col["ACCESSION_NUMBER"]]] = \
                p[col["FILINGMANAGER_NAME"]].strip()
        for acc, sub in subs.items():
            sub["manager"] = names.get(acc, "")
            key = (sub["cik"], sub["period"])
            cur = best.get(key)
            rank = (sub["filed"], 1 if sub["amended"] else 0)
            if cur is None or rank > (cur["filed"],
                                      1 if cur["amended"] else 0):
                best[key] = sub
        zf.close()
    for (cik, period) in best:
        period_counts[period] = period_counts.get(period, 0) + 1
    return best, period_counts


TOKENS = {"LLC": "LLC", "LLP": "LLP", "LP": "LP", "INC": "Inc",
          "INC.": "Inc.", "CORP": "Corp", "CORP.": "Corp.",
          "CO": "Co", "CO.": "Co.", "/DE/": "/DE/", "USA": "USA",
          "ETF": "ETF", "PLC": "PLC", "FMR": "FMR",
          "JPMORGAN": "JPMorgan", "UBS": "UBS", "AT&T": "AT&T",
          "KLA": "KLA", "ISHARES": "iShares"}


def plain_name(raw):
    out = []
    for w in raw.split():
        key = w.upper()
        if key in TOKENS:
            out.append(TOKENS[key])
        elif w.isupper():
            out.append(w.capitalize())
        else:
            out.append(w)
    return " ".join(out)


def build():
    if not os.path.isdir(CACHE):
        return fail("the stored holdings filing sets are not on "
                    "record; refusing to publish.")
    zip_paths = sorted(os.path.join(CACHE, n) for n in os.listdir(CACHE)
                       if n.endswith("_form13f.zip"))
    if len(zip_paths) != 2:
        return fail(f"expected the two stored quarterly filing "
                    f"sets, found {len(zip_paths)}; refusing to "
                    "publish a partial record.")
    if not os.path.exists(TRACKER_PATH):
        return fail("the 13F Tracker's published record is missing; "
                    "refusing to publish without its cross-check.")
    with open(TRACKER_PATH, encoding="utf-8") as fh:
        tracker = json.load(fh)
    if not os.path.exists(PROVING_PATH):
        return fail("the Proving Ground's published record is "
                    "missing; refusing to publish.")
    with open(PROVING_PATH, encoding="utf-8") as fh:
        proving = json.load(fh)
    states = {s.get("key"): s for s in proving.get("states") or []}
    if "measuring" not in states:
        return fail("the Proving Ground's vocabulary does not carry "
                    "the measuring state; refusing to publish.")
    proving_state = states["measuring"]["words"]
    proving_definition = states["measuring"]["definition"]

    filings, period_counts = collect_filings(zip_paths)
    full = sorted((per for per, n in period_counts.items() if n >= 1000),
                  reverse=True)
    if len(full) != 2:
        return fail("the stored sets do not carry exactly the two "
                    "full quarters on record; refusing to publish.")
    current_period, prior_period = full[0], full[1]
    if (current_period != tracker.get("current_period")
            or prior_period != tracker.get("prior_period")):
        return fail("the recomputed periods disagree with the 13F "
                    "Tracker's published record; refusing to "
                    "publish.")
    cur = {cik: f for (cik, per), f in filings.items()
           if per == current_period}
    pri = {cik: f for (cik, per), f in filings.items()
           if per == prior_period}
    if (len(cur) != tracker.get("holders_on_record")
            or len(pri) != tracker.get("prior_holders_on_record")):
        return fail("the recomputed holder counts disagree with "
                    "the 13F Tracker's published record; refusing "
                    "to publish.")
    cur_filed = sorted(f["filed"] for f in cur.values())
    pri_filed = sorted(f["filed"] for f in pri.values())
    both_filing = set(cur) & set(pri)

    acc_period = {}
    for cik, f in cur.items():
        acc_period[f["accession"]] = (current_period, cik)
    for cik, f in pri.items():
        acc_period[f["accession"]] = (prior_period, cik)

    # The scratch database is about 400 MB and /tmp on this box is
    # a small shared memory disk, so the scratch lives on the
    # workspace disk and is cleared at the start of every run.
    tmp = os.path.expanduser("~/workspace/.jarvis/smartmoney-refresh")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    db_path = os.path.join(tmp, "pos.db")
    con = sqlite3.connect(db_path)
    c = con.cursor()
    c.execute("CREATE TABLE pos(period TEXT, cik TEXT, cusip TEXT, "
              "shares REAL, PRIMARY KEY(period, cik, cusip))")
    value_by_acc = {}
    name_counts = {}
    for path in zip_paths:
        zf = zipfile.ZipFile(path)
        batch = []
        for col, p in read_tsv(zf, "INFOTABLE.tsv"):
            acc = p[col["ACCESSION_NUMBER"]]
            meta = acc_period.get(acc)
            if meta is None:
                continue
            try:
                value = float(p[col["VALUE"]])
            except ValueError:
                continue
            if p[col["SSHPRNAMTTYPE"]] != "SH":
                continue
            if p[col["PUTCALL"]].strip():
                continue
            try:
                shares = float(p[col["SSHPRNAMT"]])
            except ValueError:
                continue
            value_by_acc[acc] = value_by_acc.get(acc, 0.0) + value
            cusip = p[col["CUSIP"]]
            nm = " ".join(p[col["NAMEOFISSUER"]].split())
            if nm:
                name_counts.setdefault(cusip, Counter())[nm] += 1
            batch.append((meta[0], meta[1], cusip, shares))
            if len(batch) >= 50000:
                c.executemany(
                    "INSERT INTO pos VALUES(?,?,?,?) ON CONFLICT"
                    "(period, cik, cusip) DO UPDATE SET "
                    "shares = shares + excluded.shares", batch)
                batch = []
        if batch:
            c.executemany(
                "INSERT INTO pos VALUES(?,?,?,?) ON CONFLICT"
                "(period, cik, cusip) DO UPDATE SET "
                "shares = shares + excluded.shares", batch)
        zf.close()
    con.commit()

    def display_name(cusip):
        counter = name_counts.get(cusip)
        if not counter:
            return ""
        raw = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return plain_name(raw)

    # Holders with plain-share holdings in both periods.
    cur_pos_ciks = {r[0] for r in c.execute(
        "SELECT DISTINCT cik FROM pos WHERE period=?", (current_period,))}
    pri_pos_ciks = {r[0] for r in c.execute(
        "SELECT DISTINCT cik FROM pos WHERE period=?", (prior_period,))}
    compared = cur_pos_ciks & pri_pos_ciks
    if not compared or len(compared) > len(both_filing):
        return fail("the compared holder set does not add up; "
                    "refusing to publish.")
    c.execute("CREATE TEMP TABLE both(cik TEXT PRIMARY KEY)")
    c.executemany("INSERT INTO both VALUES(?)", [(x,) for x in compared])

    # Per-name aggregates across the compared holders.
    agg = {}

    def slot(cusip):
        return agg.setdefault(cusip, {
            "started": 0, "ended": 0, "kept_by": 0, "added": 0.0,
            "trimmed": 0.0, "net": 0.0, "started_shares_now": 0.0,
            "ended_shares_before": 0.0})

    for cusip, n, sh in c.execute(
            "SELECT n.cusip, COUNT(*), SUM(n.shares) FROM pos n "
            "JOIN both b ON b.cik = n.cik WHERE n.period = ? AND "
            "NOT EXISTS (SELECT 1 FROM pos p WHERE p.period = ? "
            "AND p.cik = n.cik AND p.cusip = n.cusip) "
            "GROUP BY n.cusip", (current_period, prior_period)):
        s = slot(cusip)
        s["started"] = n
        s["started_shares_now"] = sh
    for cusip, n, sh in c.execute(
            "SELECT p.cusip, COUNT(*), SUM(p.shares) FROM pos p "
            "JOIN both b ON b.cik = p.cik WHERE p.period = ? AND "
            "NOT EXISTS (SELECT 1 FROM pos n WHERE n.period = ? "
            "AND n.cik = p.cik AND n.cusip = p.cusip) "
            "GROUP BY p.cusip", (prior_period, current_period)):
        s = slot(cusip)
        s["ended"] = n
        s["ended_shares_before"] = sh
    kept_total = 0
    for cusip, n, added, trimmed, net in c.execute(
            "SELECT n.cusip, COUNT(*), "
            "SUM(CASE WHEN n.shares > p.shares "
            "THEN n.shares - p.shares ELSE 0 END), "
            "SUM(CASE WHEN n.shares < p.shares "
            "THEN n.shares - p.shares ELSE 0 END), "
            "SUM(n.shares - p.shares) "
            "FROM pos n JOIN both b ON b.cik = n.cik "
            "JOIN pos p ON p.period = ? AND p.cik = n.cik "
            "AND p.cusip = n.cusip WHERE n.period = ? "
            "GROUP BY n.cusip", (prior_period, current_period)):
        s = slot(cusip)
        s["kept_by"] = n
        s["added"] = added or 0.0
        s["trimmed"] = trimmed or 0.0
        s["net"] = net or 0.0
        kept_total += n

    totals = {
        "started": sum(s["started"] for s in agg.values()),
        "ended": sum(s["ended"] for s in agg.values()),
        "kept": kept_total,
        "added_shares": sum(s["added"] for s in agg.values()),
        "trimmed_shares": sum(s["trimmed"] for s in agg.values()),
        "net_shares": sum(s["net"] for s in agg.values()),
    }
    cur_pos_compared = c.execute(
        "SELECT COUNT(*) FROM pos n JOIN both b ON b.cik = n.cik "
        "WHERE n.period = ?", (current_period,)).fetchone()[0]
    pri_pos_compared = c.execute(
        "SELECT COUNT(*) FROM pos p JOIN both b ON b.cik = p.cik "
        "WHERE p.period = ?", (prior_period,)).fetchone()[0]
    if (totals["kept"] + totals["started"] != cur_pos_compared
            or totals["kept"] + totals["ended"] != pri_pos_compared):
        return fail("the started / ended / kept counts do not add "
                    "up to the compared holders' position counts; "
                    "refusing to publish.")
    names_on_record = c.execute(
        "SELECT COUNT(DISTINCT cusip) FROM pos n "
        "JOIN both b ON b.cik = n.cik").fetchone()[0]
    if names_on_record != len(agg):
        return fail("the name count does not add up; refusing to "
                    "publish.")

    # Cross-check the 20 largest holders against the Tracker's
    # published record, figure for figure.
    tracker_holders = tracker.get("holders") or []
    if len(tracker_holders) != TOP_HOLDERS:
        return fail("the 13F Tracker's published record does not "
                    "carry the 20 largest holders; refusing to "
                    "publish.")
    holders20 = []
    for th in tracker_holders:
        cik = None
        for k, f in cur.items():
            if plain_name(f["manager"]) == th["holder"]:
                cik = k
                break
        if cik is None:
            return fail("a published holder cannot be found in the "
                        "filing sets; refusing to publish.")
        f = cur[cik]
        total = value_by_acc.get(f["accession"], 0.0)
        if abs(total - th["total_value"]) > max(1.0, total * 1e-9):
            return fail("a published holder's total value disagrees "
                        "with the recomputation; refusing to "
                        "publish.")
        positions_count = c.execute(
            "SELECT COUNT(*) FROM pos WHERE period = ? AND cik = ?",
            (current_period, cik)).fetchone()[0]
        if positions_count != th["positions_count"]:
            return fail("a published holder's holding count "
                        "disagrees with the recomputation; refusing "
                        "to publish.")
        tch = th.get("change") or {}
        pf = pri.get(cik)
        if pf is None or not tch:
            return fail("a published holder's change record is "
                        "missing; refusing to publish.")
        prior_total = value_by_acc.get(pf["accession"], 0.0)
        if abs(prior_total - tch["prior_total_value"]) > max(
                1.0, prior_total * 1e-9):
            return fail("a published holder's earlier total value "
                        "disagrees with the recomputation; refusing "
                        "to publish.")
        started = c.execute(
            "SELECT COUNT(*) FROM pos n WHERE n.period = ? AND "
            "n.cik = ? AND NOT EXISTS (SELECT 1 FROM pos p WHERE "
            "p.period = ? AND p.cik = n.cik AND p.cusip = n.cusip)",
            (current_period, cik, prior_period)).fetchone()[0]
        ended = c.execute(
            "SELECT COUNT(*) FROM pos p WHERE p.period = ? AND "
            "p.cik = ? AND NOT EXISTS (SELECT 1 FROM pos n WHERE "
            "n.period = ? AND n.cik = p.cik AND n.cusip = p.cusip)",
            (prior_period, cik, current_period)).fetchone()[0]
        kept = c.execute(
            "SELECT COUNT(*) FROM pos n JOIN pos p ON p.period = ? "
            "AND p.cik = n.cik AND p.cusip = n.cusip "
            "WHERE n.period = ? AND n.cik = ?",
            (prior_period, current_period, cik)).fetchone()[0]
        if (started != tch["started"] or ended != tch["ended"]
                or kept != tch["kept"]):
            return fail("a published holder's started / ended / "
                        "kept counts disagree with the "
                        "recomputation; refusing to publish.")
        holders20.append({
            "holder": th["holder"],
            "filed": f["filed"],
            "prior_filed": pf["filed"],
            "total_value": th["total_value"],
            "prior_total_value": tch["prior_total_value"],
            "positions_count": th["positions_count"],
            "started": started,
            "ended": ended,
            "kept": kept,
        })
    con.close()

    def usable(cusip):
        nm = display_name(cusip)
        return bool(nm) and nm.upper() not in (
            "N/A", "NA", "NONE", "NOT AVAILABLE")

    def entry(cusip, fields):
        s = agg[cusip]
        out = {"name": display_name(cusip)}
        for fld in fields:
            out[fld] = s[fld]
        return out

    pool = [cu for cu in agg if usable(cu)]
    added_list = [entry(cu, ("added", "trimmed", "net", "kept_by",
                             "started", "ended"))
                  for cu in sorted(
                      pool, key=lambda cu: (-agg[cu]["added"], cu))[:TOP_LIST]]
    trimmed_list = [entry(cu, ("added", "trimmed", "net", "kept_by",
                               "started", "ended"))
                    for cu in sorted(
                        pool, key=lambda cu: (agg[cu]["trimmed"], cu))[:TOP_LIST]]
    started_list = [entry(cu, ("started", "started_shares_now",
                               "ended", "kept_by"))
                    for cu in sorted(
                        pool, key=lambda cu: (-agg[cu]["started"], cu))[:TOP_LIST]]
    ended_list = [entry(cu, ("ended", "ended_shares_before",
                             "started", "kept_by"))
                  for cu in sorted(
                      pool, key=lambda cu: (-agg[cu]["ended"], cu))[:TOP_LIST]]
    if not (len(added_list) == len(trimmed_list) == len(started_list)
            == len(ended_list) == TOP_LIST):
        return fail("a leader list came up short; refusing to "
                    "publish.")

    coverage = (
        f"{len(cur):,} holders filed a holdings report for the "
        f"period ended {current_period} and {len(pri):,} for the "
        f"period ended {prior_period}; the change view compares "
        f"the {len(compared):,} holders who reported plain-share "
        f"holdings in both periods, across {names_on_record:,} "
        f"names")
    data = {
        "tool": "Smart Money Tracker",
        "state": "on_record",
        "proving_state": proving_state,
        "proving_definition": proving_definition,
        "current_period": current_period,
        "prior_period": prior_period,
        "current_filed_first": cur_filed[0],
        "current_filed_last": cur_filed[-1],
        "prior_filed_first": pri_filed[0],
        "prior_filed_last": pri_filed[-1],
        "holders_on_record": len(cur),
        "prior_holders_on_record": len(pri),
        "holders_in_both_filings": len(both_filing),
        "holders_compared": len(compared),
        "names_on_record": names_on_record,
        "totals": totals,
        "added": added_list,
        "trimmed": trimmed_list,
        "started": started_list,
        "ended": ended_list,
        "holders": holders20,
        "source": SOURCE_WORDS,
        "lag": LAG_WORDS,
        "step": STEP_WORDS,
        "churn_note": CHURN_WORDS,
        "name_note": NAME_WORDS,
        "coverage": coverage,
        "receipt": {
            "current_period": current_period,
            "prior_period": prior_period,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }
    data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
    blob = json.dumps(data, indent=2, sort_keys=True)
    for bad in FORBIDDEN:
        if bad in blob:
            return fail(f"assembled data carries forbidden wording "
                        f"({bad}); refusing to publish.")
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(blob + "\n")
    print(f"Wrote {OUT_PATH} (periods {prior_period} -> "
          f"{current_period}, {len(compared)} holders compared, "
          f"started {totals['started']}, ended {totals['ended']}, "
          f"kept {totals['kept']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
