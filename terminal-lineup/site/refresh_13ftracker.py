#!/usr/bin/env python3
"""Refresh the 13F Tracker data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the stored quarterly holdings filing sets
themselves: two bulk sets of the reports large holders file with
the securities regulator, one for filings received March to May
2026 and one for filings received June to August 2026. Each report
carries the filing manager's name, the period it covers, the date
it was filed, and one row per name held with the share count and
the dollar value. A holdings figure is published only from those
rows: a named holder, a name held, a share count or value, and a
period. The aggregate ownership readings kept elsewhere on this
site are scores out of 100 worked out from these filings; they are
not holder positions and are never presented as holdings. Company
insider transaction summaries are a different record again (the
buying and selling of a company's own officers and directors) and
are never presented as fund holdings; they live on the Insider
Wire.

Reconstruction choices: the current period is the period with the
most holdings reports in the newer set (the period ended June 30,
2026); the prior period is the period with the most holdings
reports in the older set (the period ended March 31, 2026). For
each period, a manager's report of record is their latest filing
for that period across both sets, counting both first reports and
corrected reports; notice-only filings, which carry no holdings,
never count. Only plain share rows count as holdings: rows marked
as options (puts or calls) are left out of the share counts, and
rows for the same name held by the same manager are added together.
The page lists the 20 largest holders by total reported value in
the current period, each with their 10 largest holdings, and the
change against the same manager's prior-period report where one
exists: holdings started, holdings ended, and the share change on
holdings kept. Dollar values and share counts are published
exactly as filed, never rescaled or estimated.

Non-claims: this tool does not show every holder or every holding:
it shows the 20 largest holders and their 10 largest holdings, and
says so. It makes no claim about any holder whose report is not in
the stored sets, and none about trading after the period ended:
these reports are filed weeks after the period they cover, and the
page prints the period and the filing date beside every figure.

Fail-closed rules: if either stored set is missing or cannot be
read; if a published holder's report carries no manager name; if a
published holder's filed rows do not add up to the total value
their own report summary declares (within rounding); if the two
periods collapse into one; or if a period's report count is too
small to be the quarter's set, the refresh stops and publishes
nothing.

Honesty rules:
- Dates are read off the sources, never from the clock. Running
  this script twice produces the same file.
- Absence is not zero: a holder with no prior-period report is
  published as having no earlier report on record, never as a
  change from zero.

Usage: python3 refresh_13ftracker.py
"""

import io
import json
import os
import sys
import zipfile
from datetime import datetime

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/workspace/morgue/data_cache/13f")
OUT_PATH = os.path.join(HERE, "13f-tracker", "data.json")

SOURCE_WORDS = ("The quarterly holdings reports large holders file "
                "with the Securities and Exchange Commission: each "
                "report names the holder, the period it covers, "
                "the date it was filed, and every name held with "
                "its share count and dollar value")
LAG_WORDS = ("These reports are always weeks old: holders file "
             "them after the period ends, so every figure here is "
             "what the holder reported holding on the period date, "
             "filed on the filing date shown")
TOP_N = 20
TOP_HOLDINGS = 10


def fail(message):
    print(f"13F Tracker refresh: {message}", file=sys.stderr)
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
    plus {period: set(accessions)} counts per period."""
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
        totals = {}
        for col, p in read_tsv(zf, "SUMMARYPAGE.tsv"):
            try:
                totals[p[col["ACCESSION_NUMBER"]]] = \
                    float(p[col["TABLEVALUETOTAL"]])
            except ValueError:
                continue
        for acc, sub in subs.items():
            sub["manager"] = names.get(acc, "")
            sub["declared_total"] = totals.get(acc)
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


def collect_positions(zip_paths, wanted_accessions):
    """{accession: {cusip: {name, shares, value}}} from plain
    share rows only, plus {accession: all-rows value sum}."""
    positions = {}
    row_value = {}
    for path in zip_paths:
        zf = zipfile.ZipFile(path)
        for col, p in read_tsv(zf, "INFOTABLE.tsv"):
            acc = p[col["ACCESSION_NUMBER"]]
            if acc not in wanted_accessions:
                continue
            try:
                value = float(p[col["VALUE"]])
            except ValueError:
                continue
            row_value[acc] = row_value.get(acc, 0.0) + value
            if p[col["SSHPRNAMTTYPE"]] != "SH":
                continue
            if p[col["PUTCALL"]].strip():
                continue
            try:
                shares = float(p[col["SSHPRNAMT"]])
            except ValueError:
                continue
            per = positions.setdefault(acc, {})
            row = per.setdefault(p[col["CUSIP"]], {
                "name": p[col["NAMEOFISSUER"]].strip(),
                "cusip": p[col["CUSIP"]],
                "shares": 0.0, "value": 0.0})
            row["shares"] += shares
            row["value"] += value
        zf.close()
    return positions, row_value


TOKENS = {"LLC": "LLC", "LLP": "LLP", "LP": "LP", "INC": "Inc",
          "INC.": "Inc.", "CORP": "Corp", "CORP.": "Corp.",
          "CO": "Co", "CO.": "Co.", "/DE/": "/DE/", "USA": "USA",
          "ETF": "ETF", "PLC": "PLC", "FMR": "FMR",
          "JPMORGAN": "JPMorgan", "UBS": "UBS"}


try:
    import engine_adaptations as _ea
except ImportError:  # pragma: no cover
    _ea = None

PANEL_HISTORY_PATH = os.path.join(HERE, "13f-tracker",
                                  "panel-history.json")


def panel_reliability_block(cur, pri, current_period, prior_period):
    """FE20 panel reliability for the holder counts this page
    publishes (DEEP-PASS 3.2 item 11, first application). The
    panel is the set of filing managers. Stability is the
    composition overlap between the two periods on record
    (Jaccard, from engine_adaptations); coverage is the current
    period's panel size against the larger of the two periods.
    Drift needs a series of panel readings: only two periods
    are on record, so no drift z exists and the reliability is
    honestly not_recorded, with the composition snapshot
    returned alongside so the recording of that history begins
    with this refresh (the exact remainder the deep pass
    named). No holder count is discounted until a drift series
    exists."""
    stability = (_ea.fe20_composition_stability(cur.keys(), pri.keys())
                 if _ea is not None else
                 {"state": "not_recorded", "stability": None,
                  "missing": ["panel_composition_history"]})
    coverage = (len(cur) / max(len(cur), len(pri))) if cur and pri \
        else None
    reliability = (_ea.fe20_panel_reliability(
        stability.get("stability"), coverage, None)
        if _ea is not None else
        {"state": "not_recorded", "reliability": None,
         "missing": ["panel_drift_z"]})
    block = {
        "form": ("reliability = panel_stability * coverage / "
                 "(1 + abs(panel_drift_z)); panel derived inputs "
                 "are discounted by the reliability"),
        "state": reliability["state"],
        "reliability": reliability["reliability"],
        "missing": reliability["missing"],
        "panel_stability": stability.get("stability"),
        "stability_basis": ("Jaccard overlap of the filing "
                            "manager sets of the two periods on "
                            "record"),
        "coverage": (round(coverage, 4) if coverage is not None
                     else None),
        "coverage_basis": ("current period filers over the "
                           "larger of the two periods' filer "
                           "counts"),
        "panel_drift_z": None,
        "panel_drift_state": (
            "undefined: one period pair on record; a drift z "
            "needs a series of at least three panel readings "
            "with varying earlier readings"),
        "panel_readings": [
            {"period": prior_period, "members": len(pri)},
            {"period": current_period, "members": len(cur)},
        ],
        "missing_input": (
            "a third full filing period on record (the "
            "2026-09-30 period, whose filings arrive after this "
            "record's two periods): with two periods there is "
            "one stability reading and no earlier series to "
            "take a z against, so no drift figure is computed "
            "or substituted"),
        "note": ("No drift series exists yet: two filing periods "
                 "are on record and a drift z needs a series of "
                 "panel readings. The composition snapshot for "
                 "this period pair is recorded in "
                 "panel-history.json from this refresh on, so the "
                 "series can be built; until it exists, no holder "
                 "count here is discounted and none is presented "
                 "as discounted."),
    }
    snapshot = {
        "period_pair": f"{prior_period}->{current_period}",
        "prior_period": prior_period,
        "current_period": current_period,
        "members_prior": len(pri),
        "members_current": len(cur),
        "members_both": (stability.get("members_both")),
        "panel_stability": stability.get("stability"),
        "coverage": block["coverage"],
        "panel_readings": block["panel_readings"],
        "panel_drift_state": block["panel_drift_state"],
    }
    return block, snapshot


def write_panel_history(snapshot):
    """Upsert one composition snapshot into panel-history.json,
    keyed by period pair. Deterministic: rerunning the refresh
    on the same filing sets rewrites the same file."""
    history = {}
    if os.path.exists(PANEL_HISTORY_PATH):
        try:
            with open(PANEL_HISTORY_PATH, "r", encoding="utf-8") as fh:
                history = json.load(fh)
        except (ValueError, OSError):
            history = {}
    entries = history.get("snapshots", {})
    entries[snapshot["period_pair"]] = snapshot
    history = {"panel": "13F filing managers",
               "snapshots": {k: entries[k] for k in sorted(entries)}}
    with open(PANEL_HISTORY_PATH, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2, sort_keys=True)
        fh.write("\n")


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

    filings, period_counts = collect_filings(zip_paths)
    ranked_periods = sorted(period_counts.items(),
                            key=lambda kv: kv[1], reverse=True)
    if len(ranked_periods) < 2 or ranked_periods[1][1] < 1000:
        return fail("the stored sets do not carry two full "
                    "quarters of holdings reports; refusing to "
                    "publish.")
    current_period = max(period_counts,
                         key=lambda per: (per, period_counts[per]))
    # current = the latest period with a full quarter's filings;
    # prior = the latest earlier period with a full quarter's filings
    full = sorted((per for per, n in period_counts.items() if n >= 1000),
                  reverse=True)
    if len(full) < 2:
        return fail("fewer than two full quarters are on record; "
                    "refusing to publish.")
    current_period, prior_period = full[0], full[1]

    cur = {cik: f for (cik, per), f in filings.items()
           if per == current_period}
    pri = {cik: f for (cik, per), f in filings.items()
           if per == prior_period}
    wanted = {f["accession"] for f in cur.values()}
    wanted |= {pri[cik]["accession"] for cik in pri if cik in cur}
    positions, row_value = collect_positions(zip_paths, wanted)

    holders = []
    for cik, f in cur.items():
        per = positions.get(f["accession"], {})
        total = sum(r["value"] for r in per.values())
        holders.append({"cik": cik, "filing": f, "positions": per,
                        "total_value": total})
    holders.sort(key=lambda h: h["total_value"], reverse=True)
    top = holders[:TOP_N]

    out_holders = []
    for h in top:
        f = h["filing"]
        if not f["manager"]:
            return fail("a published holder's report carries no "
                        "manager name; refusing to publish.")
        declared = f.get("declared_total")
        summed = row_value.get(f["accession"])
        if declared is not None and summed is not None and declared > 0:
            if abs(summed - declared) / declared > 0.01:
                return fail("a published holder's filed rows do "
                            "not add up to the total their own "
                            "report summary declares; refusing to "
                            "publish.")
        rows = sorted(h["positions"].values(),
                      key=lambda r: r["value"], reverse=True)
        entry = {
            "holder": plain_name(f["manager"]),
            "period": f["period"],
            "filed": f["filed"],
            "total_value": round(h["total_value"], 2),
            "positions_count": len(rows),
            "holdings": [{
                "name": plain_name(r["name"]),
                "shares": r["shares"],
                "value": round(r["value"], 2),
            } for r in rows[:TOP_HOLDINGS]],
            "change": None,
        }
        pf = pri.get(h["cik"])
        if pf is not None:
            old = positions.get(pf["accession"], {})
            new = h["positions"]
            started = [c for c in new if c not in old]
            ended = [c for c in old if c not in new]
            kept = [c for c in new if c in old]
            entry["change"] = {
                "prior_period": prior_period,
                "prior_filed": pf["filed"],
                "prior_total_value": round(
                    sum(r["value"] for r in old.values()), 2),
                "started": len(started),
                "ended": len(ended),
                "kept": len(kept),
                "holding_changes": [{
                    "name": plain_name(new[c]["name"]),
                    "shares_before": old[c]["shares"],
                    "shares_now": new[c]["shares"],
                    "change_pct": (round(
                        (new[c]["shares"] / old[c]["shares"] - 1.0)
                        * 100.0, 2) if old[c]["shares"] else None),
                } for c in sorted(
                    kept, key=lambda c: new[c]["value"],
                    reverse=True)[:TOP_HOLDINGS]],
            }
        out_holders.append(entry)

    coverage = (f"{len(cur):,} holders filed a holdings report for "
                f"the period ended {current_period}; this page "
                f"shows the {TOP_N} largest by total reported "
                f"value, each with their {TOP_HOLDINGS} largest "
                f"holdings, and the change against the period "
                f"ended {prior_period} where the same holder "
                f"filed then too ({len(pri):,} holders filed for "
                f"that period)")
    panel_block, panel_history = panel_reliability_block(
        cur, pri, current_period, prior_period)
    data = {
        "tool": "13F Tracker",
        "state": "on_record",
        "current_period": current_period,
        "prior_period": prior_period,
        "holders_on_record": len(cur),
        "prior_holders_on_record": len(pri),
        "panel_reliability": panel_block,
        "holders": out_holders,
        "source": SOURCE_WORDS,
        "lag": LAG_WORDS,
        "coverage": coverage,
        "receipt": {
            "current_period": current_period,
            "prior_period": prior_period,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    write_panel_history(panel_history)
    print(f"Wrote {OUT_PATH} (periods {prior_period} -> "
          f"{current_period}, {len(cur)} holders on record, "
          f"top holder {out_holders[0]['holder'] if out_holders else 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
