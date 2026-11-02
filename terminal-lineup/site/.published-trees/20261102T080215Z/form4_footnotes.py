#!/usr/bin/env python3
"""Form 4 footnote lane (publication cure B6 / R-27 FE23,
2026-10-30).

FE23's plan classifier (engine_adaptations.classify_plan_status)
was built and registered, but the insider record is summary grain:
whether a sale ran under a Rule 10b5-1 plan is stated only in Form
4 footnote text, and no footnote record existed. Form 4 ownership
documents are structured XML: a footnotes element whose footnote
children are keyed by id, with transactions referencing those ids.
This lane collects exactly that, for the Insider Wire tracked
universe (read from the bundle seed's own keys, no second list),
from EDGAR under the same declared operator identity the morgue
SEC lanes already send (recorded in inst_bundle.py), self paced
well under the SEC fair access ceiling, caching every filing:

  site/insider-divergence/footnotes/<accession>.xml  raw filings
  site/insider-divergence/footnotes/record.json      parsed store:
    per filing, per transaction, the footnote texts actually
    referenced by that transaction (a filing with no footnotes
    element yields no texts, so its sales stay unknown, never
    discretionary by default), plus a labelled set.

Labelling rule (independent of the classifier): a footnote is
labelled plan_10b5_1 when its raw text contains the literal
string "10b5-1" together with the word "plan"; discretionary
when its text is non empty and contains no "10b5" at all. Every
label is read off the raw filing XML stored here, so the
classifier's precision is measured against filing text, not
against its own output.

Usage: python3 form4_footnotes.py [--per-name 4]
"""

import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
SEED = os.path.join(WORKSPACE, "morgue", "data_cache", "edgar",
                    "seed_2026-10-30.json")
TICKERS = os.path.join(WORKSPACE, "morgue", "data_cache", "edgar",
                       "company_tickers.json")
OUT_DIR = os.path.join(HERE, "insider-divergence", "footnotes")
RECORD_PATH = os.path.join(OUT_DIR, "record.json")
UA = {"User-Agent": "Morgue Engine (the owner; "
                    "the owner's email)"}
SINCE = "2026-05-01"


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    time.sleep(0.25)
    return data if binary else json.loads(data.decode("utf-8"))


def parse_form4(xml_bytes):
    """{transactions: [{code, shares, price, footnote_texts}],
    footnotes: {id: text}} from one ownership XML document."""
    root = ET.fromstring(xml_bytes)
    footnotes = {}
    fn_el = root.find("footnotes")
    if fn_el is not None:
        for fn in fn_el.findall("footnote"):
            fid = fn.get("id")
            text = "".join(fn.itertext()).strip()
            if fid:
                footnotes[fid] = re.sub(r"\s+", " ", text)
    txns = []
    for tag in ("nonDerivativeTransaction", "derivativeTransaction"):
        for txn in root.iter(tag):
            refs = []
            for ref in txn.iter("footnoteId"):
                fid = ref.get("id")
                if fid in footnotes:
                    refs.append(footnotes[fid])
            code_el = txn.find("transactionCoding/transactionCode")
            txns.append({
                "code": code_el.text if code_el is not None else None,
                "footnote_texts": refs,
            })
    return {"footnotes": footnotes, "transactions": txns}


def label_for(text):
    low = text.lower()
    if "10b5-1" in low and "plan" in low:
        return "plan_10b5_1"
    if "10b5" not in low:
        return "discretionary"
    return None


def main(argv):
    per_name = 4
    if "--per-name" in argv:
        per_name = int(argv[argv.index("--per-name") + 1])
    with open(SEED, encoding="utf-8") as fh:
        tracked = sorted(json.load(fh))
    with open(TICKERS, encoding="utf-8") as fh:
        tick = json.load(fh)
    cik_of = {v["ticker"]: v["cik_str"] for v in tick.values()}
    os.makedirs(OUT_DIR, exist_ok=True)
    filings_out, labelled, errors = [], [], []
    n_classified_names = set()
    for sym in tracked:
        cik = cik_of.get(sym)
        if not cik:
            errors.append({"symbol": sym, "error": "no_cik_on_record"})
            continue
        try:
            subs = fetch(f"https://data.sec.gov/submissions/"
                         f"CIK{cik:010d}.json")
        except Exception as exc:  # noqa: BLE001 - named per name
            errors.append({"symbol": sym, "error": str(exc)[:120]})
            continue
        recent = subs.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accs = recent.get("accessionNumber", [])
        docs = recent.get("primaryDocument", [])
        picked = 0
        for form, fdate, acc, doc in zip(forms, dates, accs, docs):
            if picked >= per_name:
                break
            if form != "4" or fdate < SINCE or not doc:
                continue
            picked += 1
            cache = os.path.join(OUT_DIR, acc.replace("-", "") + ".xml")
            try:
                if os.path.exists(cache):
                    with open(cache, "rb") as fh:
                        raw = fh.read()
                else:
                    # The submissions record's primary document
                    # for a Form 4 is the rendered .htm, not the
                    # ownership XML. Resolve the raw XML through
                    # the filing index: the .xml item that is
                    # not an R (report) file.
                    idx = fetch(
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik}/{acc.replace('-', '')}/index.json")
                    items = (idx.get("directory") or {}).get(
                        "item") or []
                    xml_names = [it["name"] for it in items
                                 if it["name"].endswith(".xml")
                                 and not it["name"].startswith("R")]
                    if not xml_names:
                        raise RuntimeError(
                            "no ownership xml in filing index")
                    raw = fetch(
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik}/{acc.replace('-', '')}/"
                        f"{xml_names[0]}", binary=True)
                    if b"<ownershipDocument" not in raw[:2000]:
                        raise RuntimeError(
                            "filing index xml is not an ownership "
                            "document")
                    with open(cache, "wb") as fh:
                        fh.write(raw)
                parsed = parse_form4(raw)
            except Exception as exc:  # noqa: BLE001
                errors.append({"symbol": sym, "accession": acc,
                               "error": str(exc)[:120]})
                continue
            filings_out.append({
                "symbol": sym, "accession": acc,
                "filed": fdate,
                "footnotes": parsed["footnotes"],
                "transactions": parsed["transactions"],
            })
            for txn in parsed["transactions"]:
                for text in txn["footnote_texts"]:
                    lab = label_for(text)
                    if lab:
                        labelled.append([text, lab])
                        n_classified_names.add(sym)
    record = {
        "updated_ts": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": ("SEC EDGAR Form 4 ownership XML, footnotes "
                   "element, collected by form4_footnotes.py "
                   "under the declared morgue EDGAR identity"),
        "window_since": SINCE,
        "names_tracked": len(tracked),
        "filings_on_record": len(filings_out),
        "names_with_classified_transactions": len(n_classified_names),
        "labelled_footnotes": len(labelled),
        "labelled": labelled,
        "errors": errors,
        "filings": filings_out,
    }
    tmp = RECORD_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=1) + "\n")
    os.replace(tmp, RECORD_PATH)
    print(f"form4_footnotes: {len(filings_out)} filings, "
          f"{len(n_classified_names)} names classified, "
          f"{len(labelled)} labelled footnotes, "
          f"{len(errors)} errors")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
