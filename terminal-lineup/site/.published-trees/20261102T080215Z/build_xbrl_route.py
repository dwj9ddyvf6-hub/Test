#!/usr/bin/env python3
"""FE21 XBRL route: what the terminal's facts store actually holds.

The registry carried FE21's route "XBRL company facts with
acceptance timestamps, accession ids and restatement handling"
as absent. The terminal does hold an XBRL facts store (the
morgue facts cache: one flattened file per filer, built from
EDGAR company facts). This builder reads that store as it
stands and writes site/filings-wire/xbrl_record.json:

- per fact, the acceptance timestamp the store carries is the
  filed date (date granularity; the store carries no accession
  id on any fact). From 2026-10-30 the builder also carries
  intraday acceptance timestamps at filing level, from the
  same EDGAR submissions fetch the filings lanes already run:
  per filer, recent 10-K and 10-Q filings with accession
  number, acceptance timestamp, filed date and form. The one
  absence that remains, per fact accession linkage, is named
  in the record instead of invented;
- restatement handling: facts sharing a concept and period end
  with more than one filed date are restatements; the route's
  rule is latest filed wins, amendments (forms ending /A) are
  counted, and the superseded values are named as superseded;
- filing quality series: cash conversion (operating cash flow
  over net income) per filer per period from the concepts the
  store actually carries, read point in time by filed date;
  the concepts FE21 also names (receivables growth gap,
  deferred revenue) are not in the store and are named absent;
- tag heterogeneity: per concept, the share of filers carrying
  it, the registry's named practical risk, measured.

Usage: python3 build_xbrl_route.py
"""

import gzip
import json
import os
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone

UA = {"User-Agent": "Morgue Engine (the owner; "
                    "the owner's email)"}
ACCEPTANCE_FORMS = ("10-K", "10-Q", "10-K/A", "10-Q/A")
ACCEPTANCE_PER_FILER = 40


def fetch_acceptance(cik):
    """Intraday acceptance timestamps for one filer's recent
    10-K and 10-Q filings, from the same EDGAR submissions
    fetch the filings lanes already run (RC-30 FE21 cure,
    2026-10-30). Returns a list of {accession, acceptance,
    filed, form} or None when the fetch fails, named by the
    caller, never fabricated."""
    if not cik:
        return None
    url = (f"https://data.sec.gov/submissions/"
           f"CIK{int(cik):010d}.json")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        subs = json.loads(resp.read().decode("utf-8"))
    time.sleep(0.25)
    recent = ((subs.get("filings") or {}).get("recent") or {})
    out = []
    for acc, acc_ts, filed, form in zip(
            recent.get("accessionNumber", []),
            recent.get("acceptanceDateTime", []),
            recent.get("filingDate", []),
            recent.get("form", [])):
        if form in ACCEPTANCE_FORMS and acc_ts:
            out.append({"accession": acc, "acceptance": acc_ts,
                        "filed": filed, "form": form})
        if len(out) >= ACCEPTANCE_PER_FILER:
            break
    return out

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
FACTS_DIR = os.path.join(WS, "morgue", "state", "morgue", "facts")
TICKERS_PATH = os.path.join(WS, "morgue", "data_cache", "edgar",
                            "company_tickers.json")
OUT_PATH = os.path.join(HERE, "filings-wire", "xbrl_record.json")

QUALITY_CONCEPTS = ("cfo", "net_income", "revenue")
ABSENT_CONCEPTS = ("receivables", "deferred_revenue", "capex")


def main():
    tickers = {}
    if os.path.exists(TICKERS_PATH):
        with open(TICKERS_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        rows = raw.values() if isinstance(raw, dict) else raw
        for row in rows:
            if isinstance(row, dict) and row.get("cik_str"):
                tickers[int(row["cik_str"])] = row.get("ticker")

    filers = []
    concept_filers = Counter()
    total_facts = 0
    facts_with_filed = 0
    restated_keys = 0
    amended_facts = 0
    for name in sorted(os.listdir(FACTS_DIR)):
        if not name.endswith(".json.gz"):
            continue
        with gzip.open(os.path.join(FACTS_DIR, name), "rt",
                       encoding="utf-8") as fh:
            doc = json.load(fh)
        cik = doc.get("cik")
        facts = doc.get("facts") or []
        total_facts += len(facts)
        by_key = defaultdict(list)
        concepts_here = set()
        for f in facts:
            concepts_here.add(f.get("k"))
            if f.get("filed"):
                facts_with_filed += 1
            if str(f.get("form", "")).endswith("/A"):
                amended_facts += 1
            by_key[(f.get("k"), f.get("start"), f.get("end"))].append(f)
        for key, group in by_key.items():
            if len({g.get("filed") for g in group}) > 1:
                restated_keys += 1
        for c in concepts_here:
            concept_filers[c] += 1
        # cash conversion series: duration facts (start present)
        # for cfo and net income, latest filed per period end.
        def latest(concept):
            out = {}
            for f in facts:
                if f.get("k") != concept or not f.get("start"):
                    continue
                end = f.get("end")
                if end not in out or (f.get("filed") or "") >= \
                        (out[end].get("filed") or ""):
                    out[end] = f
            return out
        cfo = latest("cfo")
        inc = latest("net_income")
        series = []
        for end in sorted(set(cfo) & set(inc)):
            ni = inc[end].get("val")
            if ni:
                series.append({
                    "period_end": end,
                    "filed": max(cfo[end].get("filed") or "",
                                 inc[end].get("filed") or ""),
                    "cash_conversion": round(cfo[end]["val"] / ni, 4),
                })
        acceptance, acceptance_error = None, None
        try:
            acceptance = fetch_acceptance(cik)
        except Exception as exc:  # named per filer, never silent
            acceptance_error = str(exc)[:120]
        filers.append({
            "cik": cik,
            "ticker": tickers.get(cik),
            "facts": len(facts),
            "concepts": sorted(concepts_here),
            "cash_conversion_periods": len(series),
            "cash_conversion_latest": series[-1] if series else None,
            "cash_conversion_prior": series[-2] if len(series) > 1
                                     else None,
            "acceptance_filings": acceptance,
            "acceptance_error": acceptance_error,
        })

    n = len(filers)
    heterogeneity = {
        c: {"filers": concept_filers.get(c, 0),
            "share_of_filers": (round(concept_filers.get(c, 0) / n, 4)
                                if n else None)}
        for c in sorted(set(QUALITY_CONCEPTS) | set(concept_filers))}
    record = {
        "record": "FE21 XBRL route, read from the terminal facts store",
        "built_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "store": "morgue facts cache (EDGAR company facts, flattened)",
        "filers": n,
        "facts_total": total_facts,
        "facts_with_filed_date": facts_with_filed,
        "acceptance_timestamps": {
            "state": "recorded_at_filing_level",
            "carries": ("filed date per fact (date granularity) "
                        "from the facts store, plus intraday "
                        "acceptance timestamps with accession "
                        "numbers per recent 10-K and 10-Q filing "
                        "from the EDGAR submissions fetch, "
                        "carried per filer in acceptance_filings"),
            "filers_with_acceptance": sum(
                1 for f in filers if f.get("acceptance_filings")),
            "acceptance_filings_total": sum(
                len(f.get("acceptance_filings") or [])
                for f in filers),
            "missing": ("per fact accession linkage: the "
                        "flattened facts store carries no "
                        "accession id on any fact, so a single "
                        "fact cannot be tied to one filing's "
                        "acceptance timestamp; the filing level "
                        "timestamps are on record"),
        },
        "restatement_handling": {
            "state": "recorded",
            "rule": "latest filed wins per concept and period; "
                    "superseded values stay in the store and are "
                    "counted here, never silently overwritten",
            "restated_concept_periods": restated_keys,
            "amendment_facts": amended_facts,
        },
        "tag_heterogeneity": heterogeneity,
        "concepts_absent_from_store": list(ABSENT_CONCEPTS),
        "filers_detail": filers,
        "note": ("Cash conversion is computable point in time from "
                 "filed dates for the filers and periods counted "
                 "here. FE21's receivables and deferred revenue legs "
                 "have no concept in the store. Acceptance "
                 "timestamps landed 2026-10-30 at filing level "
                 "from the submissions fetch; what keeps the route "
                 "partial is the per fact accession linkage the "
                 "flattened store cannot carry."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"xbrl route: {n} filers, {total_facts} facts, "
          f"{restated_keys} restated concept periods, "
          f"{amended_facts} amendment facts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
