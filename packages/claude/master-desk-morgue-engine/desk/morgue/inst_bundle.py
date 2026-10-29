"""The institutional bundle: the once-a-day crawl of EDGAR and Nasdaq that gives the board its institutional leaves, and
the assembly of those leaves.

Silicon built this for the board's top 50 only and kept per-name results in a day's seed file. Here it is a RESUMABLE crawl of
the whole roster under a time budget (the morgue_inst job, evenings and weekends): each name's record is cached with the date
it was read and refreshed only when stale (EDGAR 3 days, short interest 5, a failure 1), the names the board ranks highest
first, so the coverage grows each night and the published coverage figures say how far it has got.

Routes (probed 2026-10-26 by Silicon; every one is a public source, paced by desk/data/http.py, the SEC's with the declared
contact):
  EDGAR company tickers -> submissions -> Form 4 ownership XML (open-market P and S) -> companyconcept shares outstanding
  SEC Form 13F Data Sets (bulk quarterly zips) -> instOwnership, instActivity
  Nasdaq short-interest table (FINRA SI republished; FINRA's own bulk file is 403) -> shortPositioning
Every fetch failure degrades that leaf to None with the exact error in the record, never the run, never a fabricated value.
Fetchers are injectable (`getter`), so the whole of it is fixture-testable."""
import json
import os
import time
from datetime import date, timedelta

from .. import calendar as cal
from ..data import http
from ..util import write_json_atomic
from . import cache_path, fetch, inst_13f, inst_edgar, inst_short, no_data, routes, stamp

EDGAR_TTL_DAYS, SI_TTL_DAYS, RETRY_DAYS = 3, 5, 1
SHARES_TTL_DAYS = 35
TICKERS_TTL_DAYS = 7
SRC_FORM4 = "SEC EDGAR Form 4 filings (open-market purchases and sales)"
DELAY_FORM4 = "filed within 2 business days of the trade; read over a 6-month window"
SRC_SI = "FINRA short interest as republished by Nasdaq"
DELAY_SI = "FINRA publishes about 7 business days after the settlement date; admitted on the retrieval date"
SRC_13F = "SEC Form 13F data sets"
DELAY_13F = "filed up to 45 days after quarter end; two quarters compared"
LEAVES = ("instOwnership", "instActivity", "insiderActivity", "shortPositioning")


def _day(now):
    return cal._as_date(float(now))


def name_path(root, sym):
    return cache_path(root, "inst", sym.replace("/", "_") + ".json")


def load_record(root, sym):
    try:
        with open(name_path(root, sym), encoding="utf-8") as fh:
            r = json.load(fh)
        return r if isinstance(r, dict) else None
    except (OSError, ValueError):
        return None


def save_record(root, sym, rec):
    p = name_path(root, sym)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    write_json_atomic(p, rec)


def load_cik_map(root, today, getter=None):
    """{ticker: (cik, title)}, the SEC's company_tickers.json cached for a week (cache/morgue/company_tickers.json)"""
    p = cache_path(root, "company_tickers.json")
    try:
        age = (today - date.fromtimestamp(os.path.getmtime(p))).days
    except OSError:
        age = None
    if age is None or age >= TICKERS_TTL_DAYS:
        try:
            doc = fetch.sec_json(fetch.SEC_TICKERS, getter)
            if isinstance(doc, dict) and doc:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                write_json_atomic(p, doc)
                routes.record(root, "SEC company tickers", "ok", None, today.isoformat())
        except Exception as e:                                       # noqa: BLE001  (a cached copy serves)
            routes.record(root, "SEC company tickers", "no_data", f"{type(e).__name__}: {str(e)[:100]}", today.isoformat())
            if age is None:
                raise
    with open(p, encoding="utf-8") as fh:
        return inst_edgar.ticker_map(json.load(fh))


def needs(rec, today, key, ttl):
    """True when the record's `key` read ("edgar" or "si") is missing or older than its TTL (a failed read waits
    RETRY_DAYS)"""
    if not rec:
        return True
    d = rec.get("fetched_" + key)
    if not d:
        return True
    age = (today - date.fromisoformat(d)).days
    return age >= (RETRY_DAYS if (rec.get("errors") or {}).get(key) else ttl)


def fetch_edgar(rec, sym, cik, title, today, getter=None):
    """refresh the EDGAR half of a name's record in place: submissions (SIC, Form 4 refs, 8-K 2.02 dates), the Form 4
    filings not cached yet, shares outstanding. An error is recorded and raised for the caller to count."""
    rec.update(symbol=sym, cik=cik, title=title)
    errs = rec.setdefault("errors", {})
    errs.pop("edgar", None)
    subs = fetch.sec_json(fetch.SEC_SUBMISSIONS.format(cik=cik), getter)
    if not isinstance(subs, dict):
        raise LookupError("no submissions document")
    sic, desc = inst_edgar.sic_of(subs)
    rec.update(sic=sic, sic_desc=desc, earnings_dates=inst_edgar.earnings_dates(subs))
    since = (today - timedelta(days=inst_edgar.WINDOW_DAYS)).isoformat()
    form4 = rec.setdefault("form4", {})
    for ref in inst_edgar.form4_refs(subs, since):
        if ref["accession"] in form4:
            continue
        try:
            xml = fetch.sec_text(inst_edgar.form4_url(cik, ref), getter)
            if xml:
                form4[ref["accession"]] = {"filed": ref["filing_date"], "txns": inst_edgar.parse_form4(xml)}
        except http.HostCooling:
            raise
        except Exception as e:                                       # noqa: BLE001  (one filing degrades its data only)
            errs.setdefault("form4_docs", []).append(f"{ref['accession']}: {type(e).__name__}")
    for acc in [a for a, v in form4.items() if v["filed"] < since]:
        del form4[acc]                                               # out of the window: dropped from the cache
    last = rec.get("fetched_shares")
    if not rec.get("shares_outstanding") or not last or (today - date.fromisoformat(last)).days >= SHARES_TTL_DAYS:
        errs.pop("shares_outstanding", None)
        try:                                                         # a company reports shares outstanding quarterly: not every refresh
            rec["shares_outstanding"] = inst_edgar.shares_outstanding(fetch.sec_json(fetch.SEC_CONCEPT.format(cik=cik), getter))
            rec["fetched_shares"] = today.isoformat()
        except http.HostCooling:
            raise
        except Exception as e:                                       # noqa: BLE001
            errs["shares_outstanding"] = f"{type(e).__name__}: {str(e)[:100]}"
    rec["fetched_edgar"] = today.isoformat()


def fetch_si(rec, sym, today, getter=None):
    """refresh the short-interest half: the Nasdaq table's newest rows"""
    errs = rec.setdefault("errors", {})
    errs.pop("si", None)
    payload = fetch.json_(fetch.NASDAQ_SI.format(sym=sym), getter, timeout=45)
    rows = inst_short.parse_nasdaq_si(payload) if isinstance(payload, dict) else []
    rec["si"] = rows[:6]
    rec["fetched_si"] = today.isoformat()


def crawl(root, symbols, now, budget_s=1500.0, getter=None, clock=time.monotonic, only=("edgar", "si")):
    """walk `symbols` in order, refreshing each stale record until the time budget is spent -> counts. A cooling or
    refusing host stops the walk for that source (the next run resumes); a name's own failure is recorded on it."""
    today = _day(now)
    stats = {"seen": 0, "edgar": 0, "si": 0, "skipped_fresh": 0, "no_cik": 0, "errors": 0, "stopped": None}
    t0 = clock()
    cik = {}
    try:
        cik = load_cik_map(root, today, getter)
    except Exception as e:                                           # noqa: BLE001
        stats["stopped"] = f"company tickers: {type(e).__name__}: {str(e)[:100]}"
        return stats
    sec_ok = "edgar" in only
    nas_ok = "si" in only
    for sym in symbols:
        if clock() - t0 > budget_s:
            stats["stopped"] = stats["stopped"] or "time budget spent"
            break
        if not sec_ok and not nas_ok:
            stats["stopped"] = stats["stopped"] or "every source stopped"
            break
        rec = load_record(root, sym) or {"symbol": sym}
        stats["seen"] += 1
        todo_e = sec_ok and needs(rec, today, "edgar", EDGAR_TTL_DAYS)
        todo_s = nas_ok and needs(rec, today, "si", SI_TTL_DAYS)
        if not todo_e and not todo_s:
            stats["skipped_fresh"] += 1
            continue
        hit = cik.get(sym)
        if todo_e:
            if not hit:
                rec.setdefault("errors", {})["edgar"] = "no CIK match for this ticker"
                rec["fetched_edgar"] = today.isoformat()
                stats["no_cik"] += 1
            else:
                try:
                    fetch_edgar(rec, sym, hit[0], hit[1], today, getter)
                    stats["edgar"] += 1
                except http.HostCooling as e:
                    sec_ok = False
                    stats["stopped"] = f"SEC host paused: {str(e)[:80]}"
                except Exception as e:                               # noqa: BLE001
                    rec.setdefault("errors", {})["edgar"] = f"{type(e).__name__}: {str(e)[:120]}"
                    rec["fetched_edgar"] = today.isoformat()
                    stats["errors"] += 1
        if todo_s:
            try:
                fetch_si(rec, sym, today, getter)
                stats["si"] += 1
            except http.HostCooling as e:
                nas_ok = False
                stats["stopped"] = stats["stopped"] or f"Nasdaq host paused: {str(e)[:80]}"
            except Exception as e:                                   # noqa: BLE001
                rec.setdefault("errors", {})["si"] = f"{type(e).__name__}: {str(e)[:120]}"
                rec["fetched_si"] = today.isoformat()
                stats["errors"] += 1
        save_record(root, sym, rec)
    routes.record(root, "SEC EDGAR submissions and Form 4", "ok" if stats["edgar"] or not stats["errors"] else "no_data",
                  None if stats["edgar"] or not stats["errors"] else f"{stats['errors']} errors, 0 names read",
                  today.isoformat())
    routes.record(root, "Nasdaq short-interest table", "ok" if stats["si"] or not stats["errors"] else "no_data",
                  None if stats["si"] or not stats["errors"] else f"{stats['errors']} errors, 0 names read", today.isoformat())
    return stats


# ---- 13F -------------------------------------------------------------------------------------------------------------

def holdings_as_of(end):
    """the quarter end whose holdings the data set ending `end` reports (filings of Jun-Aug report June 30)"""
    return {2: date(end.year - 1, 12, 31), 5: date(end.year, 3, 31), 8: date(end.year, 6, 30),
            11: date(end.year, 9, 30)}.get(end.month)


PROBE_DAYS = 3


def _probe_path(root):
    return cache_path(root, "13f", "unpublished.json")


def probed_recently(root, label, today):
    """True when this data set was asked for and not served in the last PROBE_DAYS days: a set not published yet is not
    asked for at every run (a 403 from the SEC would pause the host for every desk process for ten minutes)"""
    try:
        with open(_probe_path(root), encoding="utf-8") as fh:
            d = json.load(fh).get(label)
        return bool(d) and (today - date.fromisoformat(d)).days < PROBE_DAYS
    except (OSError, ValueError):
        return False


def remember_probe(root, label, today):
    p = _probe_path(root)
    try:
        with open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        doc = {}
    doc[label] = today.isoformat()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    write_json_atomic(p, doc)


def ensure_13f(root, today, getter=None, free_mb=None, want=2, min_free_mb=700):
    """make sure the aggregates of the two newest available 13F data sets are cached -> ([(label, end, agg)], notes).
    A set not published yet answers 403 or 404 and is skipped; a set already aggregated is not downloaded again. A download
    needs min_free_mb of free disk (the zip is written to cache/morgue/13f and deleted after it is read)."""
    got, notes = [], []
    for label, name, end in inst_13f.period_files(today, count=5):
        if len(got) >= want:
            break
        doc = inst_13f.load_agg(root, label)
        if doc:
            got.append((label, end, doc["cusips"]))
            continue
        if free_mb is not None and free_mb < min_free_mb:
            notes.append(f"{label}: not downloaded, {free_mb:.0f} MB free (needs {min_free_mb})")
            continue
        if probed_recently(root, label, today):
            notes.append(f"{label}: not published when last asked (asked again in {PROBE_DAYS} days)")
            continue
        body = None
        for base in fetch.SEC_13F_BASES:
            try:
                body = fetch.binary(base + name, getter, fetch.sec_headers())
            except http.HttpError as e:
                if e.status in (403, 404):
                    body = None
                    continue
                notes.append(f"{label}: {type(e).__name__}: {str(e)[:100]}")
                break
            if body:
                break
        if not body:
            notes.append(f"{label}: not published (or refused)")
            remember_probe(root, label, today)
            continue
        import io
        agg, meta = inst_13f.aggregate_zip(io.BytesIO(body))
        del body
        inst_13f.save_agg(root, label, agg, {**meta, "end": end.isoformat(), "file": name})
        got.append((label, end, agg))
    return got, notes


# ---- assembly --------------------------------------------------------------------------------------------------------

def insider_of(rec, today):
    since = (today - timedelta(days=inst_edgar.WINDOW_DAYS)).isoformat()
    txns, latest = [], None
    for v in (rec.get("form4") or {}).values():
        if v["filed"] >= since:
            txns.extend(v["txns"])
            latest = max(latest or v["filed"], v["filed"])
    sc = inst_edgar.insider_score(txns)
    sc["latest_filing_date"] = latest
    return sc


def si_leaf(rec, shares_out, adv20=None):
    """(leaf dict for the bundle, reading for the card) from a record's newest Nasdaq row and EDGAR shares outstanding"""
    rows = rec.get("si") or []
    if not rows:
        return None, None
    row = rows[0]
    so = (shares_out or {}).get("shares")
    if not so:
        return None, None
    reading = {"symbol": rec["symbol"], "settlement_date": row["settlement_date"], "si_shares": row["si_shares"],
               "float_shares": so, "float_basis": "EDGAR shares outstanding (declared basis)", "split_flag": False,
               "publication_date": rec.get("fetched_si"), "source": SRC_SI}
    leaf = inst_short.short_leaf(reading, adv20 or row.get("adv"))
    leaf.update(days_to_cover=row.get("days_to_cover"))
    return leaf, reading


def assemble(root, symbols, now, adv20=None, thirteen=None, wanted=None):
    """the per-symbol leaves and the card details from the cached records and 13F aggregates -> (bundle, detail, notes).
    bundle[sym][leaf] = {"score","status","reason","as_of","source","delay"}; detail has what the cards list."""
    today = _day(now)
    bundle, detail = {}, {"insider": [], "short": []}
    pit_keys = inst_short.pit_keys(root)
    own = {}
    notes = {}
    if thirteen and len(thirteen) >= 1:
        cur_label, cur_end, cur = thirteen[0]
        prev = thirteen[1][2] if len(thirteen) > 1 else {}
        shares_out = {}
        for sym in symbols:
            rec = load_record(root, sym)
            if rec and rec.get("shares_outstanding"):
                shares_out[sym] = rec["shares_outstanding"]["shares"]
        cmap, st = inst_13f.resolve(cur, wanted or {})
        own = inst_13f.ownership_activity(cur, prev, shares_out, cmap)
        notes.update(cusip_stats=st, cur=cur_label, prev=(thirteen[1][0] if len(thirteen) > 1 else None),
                     as_of=(holdings_as_of(cur_end).isoformat() if holdings_as_of(cur_end) else cur_end.isoformat()))
    h_as_of = notes.get("as_of")
    for sym in symbols:
        rec = load_record(root, sym)
        out = {}
        # insider
        if rec and rec.get("fetched_edgar") and "edgar" not in (rec.get("errors") or {}):
            ins = insider_of(rec, today)
            if ins["score"] is not None:
                out["insiderActivity"] = stamp("ok", rec["fetched_edgar"], SRC_FORM4, DELAY_FORM4, score=ins["score"])
            else:
                out["insiderActivity"] = no_data(ins.get("reason") or "no open-market transaction", rec["fetched_edgar"],
                                                 SRC_FORM4, DELAY_FORM4, score=None)
            if ins["n_transactions"]:
                detail["insider"].append({"symbol": sym, "buy_value_usd": round(ins["buy_value"], 0),
                                          "sell_value_usd": round(ins["sell_value"], 0),
                                          "n_transactions": ins["n_transactions"],
                                          "latest_filing_date": ins["latest_filing_date"],
                                          "score": None if ins["score"] is None else round(ins["score"], 1)})
        else:
            why = ((rec or {}).get("errors") or {}).get("edgar") or "not read yet"
            out["insiderActivity"] = no_data(why, (rec or {}).get("fetched_edgar"), SRC_FORM4, DELAY_FORM4, score=None)
        # short interest
        leaf, reading = si_leaf(rec or {}, (rec or {}).get("shares_outstanding"), (adv20 or {}).get(sym))
        if leaf and leaf["score"] is not None:
            if pit_keys is not None and (sym, reading["settlement_date"]) not in pit_keys:
                inst_short.pit_append(root, reading)                  # the point-in-time store: append-only, once a reading
                pit_keys.add((sym, reading["settlement_date"]))
            out["shortPositioning"] = stamp("ok", reading["settlement_date"], SRC_SI, DELAY_SI, score=leaf["score"])
            detail["short"].append({"symbol": sym, "settlement_date": reading["settlement_date"],
                                    "publication_date": reading["publication_date"], "si_shares": reading["si_shares"],
                                    "si_pct_shares_out": round(leaf["si_pct_float"], 2),
                                    "days_to_cover": (None if leaf.get("days_to_cover") is None
                                                      else round(leaf["days_to_cover"], 2)),
                                    "score": round(leaf["score"], 1)})
        else:
            why = (((rec or {}).get("errors") or {}).get("si")
                   or ("no shares-outstanding basis from EDGAR" if rec and rec.get("si") else "no short-interest row"))
            out["shortPositioning"] = no_data(why, None, SRC_SI, DELAY_SI, score=None)
        # 13F
        o = own.get(sym)
        for k in ("instOwnership", "instActivity"):
            if o and o.get(k) is not None:
                out[k] = stamp("ok", h_as_of, SRC_13F, DELAY_13F, score=o[k])
            else:
                why = ("no 13F data set cached yet" if not thirteen else
                       "issuer name did not resolve to exactly one CUSIP" if not o else
                       "no prior-quarter holding to compare" if k == "instActivity" else "no reading")
                out[k] = no_data(why, h_as_of, SRC_13F, DELAY_13F, score=None)
        bundle[sym] = out
    return bundle, detail, notes


def wanted_names(cik, roster):
    """{symbol: company name} for the roster from the SEC's titles"""
    return {s: cik[s][1] for s in roster if s in cik and cik[s][1]}
