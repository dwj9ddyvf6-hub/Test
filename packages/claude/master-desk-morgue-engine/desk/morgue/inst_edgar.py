"""insiderActivity from EDGAR Form 4 (free, a declared User-Agent), and the SEC reads the other leaves share.

Ported from Silicon's inst_edgar.py. Pure scorers separated from fetching. Score (the desk's, declared): open-market
transactions only (codes P and S; grants, awards and exercises are excluded); score = board.lin(net buy value / (buy value
+ sell value), -1, 1); fewer than 2 open-market transactions in the 6-month window gives None. Fetch failures degrade the
leaf to None, never the run.

Two things Silicon did not do: the parsed transactions of a filing are cached for good (a filing never changes), so a
refresh asks for the new filings only; and the submissions document also yields the registrant's SIC code (sectors.py)
and its 8-K Item 2.02 dates (the earnings study's calendar)."""
import xml.etree.ElementTree as ET

from . import board

WINDOW_DAYS = 183
MAX_FILINGS = 20


def parse_form4(xml_text):
    """non-derivative transactions of a Form 4 ownership XML -> [{"code","shares","price","ad"}]"""
    root = ET.fromstring(xml_text)
    out = []
    for txn in root.iter("nonDerivativeTransaction"):
        def _v(tag):
            el = txn.find(f".//{tag}/value")
            if el is not None and el.text:
                return el.text
            el = txn.find(f".//{tag}")                  # the real schema: the code is bare text
            return el.text if el is not None else None
        code = _v("transactionCode")
        shares, price = _v("transactionShares"), _v("transactionPricePerShare")
        ad = _v("transactionAcquiredDisposedCode") or _v("acquiredDisposedCode")
        if code is None or shares is None or price is None:
            continue
        try:
            out.append({"code": code.strip(), "shares": float(shares), "price": float(price), "ad": ad})
        except ValueError:
            continue
    return out


def ticker_map(tickers_json):
    """company_tickers.json -> {ticker: (cik_int, title)}"""
    out = {}
    for row in (tickers_json or {}).values():
        try:
            out[row["ticker"].upper()] = (int(row["cik_str"]), row.get("title", ""))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return out


def form4_refs(submissions, since, limit=MAX_FILINGS):
    """the Form 4 filings on or after `since` (ISO date), newest first, ownership XML documents only"""
    recent = (submissions.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    refs = []
    for i, form in enumerate(forms):
        if form != "4":
            continue
        filed = (recent.get("filingDate") or [None] * len(forms))[i]
        doc = (recent.get("primaryDocument") or [None] * len(forms))[i]
        acc = (recent.get("accessionNumber") or [None] * len(forms))[i]
        if not filed or filed < since or not doc or not acc:
            continue
        if not doc.lower().endswith(".xml"):
            continue
        refs.append({"accession": acc, "primary_document": doc, "filing_date": filed})
        if len(refs) >= limit:
            break
    return refs


def form4_url(cik, ref):
    """the raw ownership XML of a filing: primaryDocument may carry the XSLT stylesheet prefix ("xslF345X06/form4.xml"),
    which serves rendered HTML; the raw document is the basename in the accession folder"""
    from .fetch import SEC_ARCHIVE
    acc = ref["accession"].replace("-", "")
    return SEC_ARCHIVE.format(cik=cik, acc=acc, doc=ref["primary_document"].rsplit("/", 1)[-1])


def insider_score(transactions):
    open_mkt = [t for t in transactions if t["code"] in ("P", "S")]
    buy = sum(t["shares"] * t["price"] for t in open_mkt if t["code"] == "P")
    sell = sum(t["shares"] * t["price"] for t in open_mkt if t["code"] == "S")
    if len(open_mkt) < 2 or (buy + sell) == 0:
        return {"score": None, "n_transactions": len(open_mkt), "buy_value": buy, "sell_value": sell,
                "reason": "fewer than 2 open-market transactions in the window"}
    return {"score": board.lin((buy - sell) / (buy + sell), -1, 1), "n_transactions": len(open_mkt),
            "buy_value": buy, "sell_value": sell}


def sic_of(submissions):
    """(sic code, description) of the registrant, or (None, None)"""
    sic = (submissions or {}).get("sic")
    try:
        return int(sic), (submissions.get("sicDescription") or None)
    except (TypeError, ValueError):
        return None, None


def earnings_dates(submissions):
    """8-K Item 2.02 filing dates (results of operations): the desk's proxy for an earnings calendar. An 8-K whose items
    are not listed is not counted."""
    recent = (submissions.get("filings") or {}).get("recent") or {}
    forms, dates, items = recent.get("form") or [], recent.get("filingDate") or [], recent.get("items") or []
    out = []
    for i, f in enumerate(forms):
        if f == "8-K" and i < len(dates) and i < len(items) and "2.02" in (items[i] or ""):
            out.append(dates[i])
    return sorted(set(out))


def shares_outstanding(concept):
    """the latest EntityCommonStockSharesOutstanding by FILED date from a companyconcept document ->
    {"shares","filed","end"} or None"""
    units = (concept or {}).get("units") or {}
    entries = [e for vals in units.values() for e in vals if "val" in e]
    if not entries:
        return None
    latest = max(entries, key=lambda e: e.get("filed", ""))
    return {"shares": latest["val"], "filed": latest.get("filed"), "end": latest.get("end")}


def shares_outstanding_facts(companyfacts):
    """the same from a companyfacts document (facts.dei.EntityCommonStockSharesOutstanding)"""
    units = ((companyfacts.get("facts") or {}).get("dei") or {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {})
    return shares_outstanding({"units": units})
