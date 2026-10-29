"""edgar_buyback: the old edgar_buyback_scraper.py vs desk/feedlib/edgar_buyback.py.

Part A — parse_buyback, the producer's one decision function: the OLD module's own parse_buyback runs on >= 300
synthetic 8-K texts (every buyback keyword pattern and near misses, percentages inside / outside the +-500 character
window and the 1-50 band, below / at / above 5%, dollar amounts in every unit spelling, malformed amounts, unrelated
percentages, case variants, HTML, non-ASCII text whose lower-casing shifts offsets) against the port's; the returned
documents must be identical.

Part B — the scan path end to end: the OLD scan_mode (its real check_ticker, ticker_to_cik, get_recent_filings,
fetch_filing_text, parse_buyback and scan-file writer; stubbed: fetch_url, which serves the case's synthetic SEC
documents, and the clock — the old datetime.now() is the naive UTC clock; HOME is a temporary directory, so the old
static ticker->CIK map is absent) against the port's Scanner.scan_mode with a fetch that serves the same documents.
Compared exactly: the results, the errors, and the scan file (name, scan_date, days_back, tickers_scanned, count,
tickers_failed). Cases cover duplicate / missing tickers in company_tickers.json, failed and malformed submissions,
other forms (10-Q, 8-K/A), filings inside / outside days_back, more 8-Ks than the 10 kept, failed filing fetches,
malformed filing dates (a scan error) and empty universes."""
import json
import os
import random
import re
import shutil
import tempfile
from datetime import datetime, timedelta, timezone

from desk.feedlib import edgar_buyback as P

from . import old_run, write_receipt

N_TEXTS = 2000
N_SCANS = 400

OLD = r'''
import os, sys, tempfile
sys.dont_write_bytecode = True
HOME = tempfile.mkdtemp()
os.environ["HOME"] = HOME                          # the old module mkdirs ~/workspace/... at import: keep it here
import datetime as _dtmod
from datetime import datetime as _dt, timezone
import edgar_buyback_scraper as O
out = {"parse": [], "scans": []}
for t in PAYLOAD["texts"]:
    out["parse"].append(O.parse_buyback(t["text"], t["ticker"], t["filing_date"]))
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
for case in PAYLOAD["scans"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc).replace(tzinfo=None)
    for f in os.listdir(str(O.OUTPUT_DIR)):
        if os.path.isfile(os.path.join(str(O.OUTPUT_DIR), f)):
            os.remove(os.path.join(str(O.OUTPUT_DIR), f))         # a fresh CIK cache and scan dir per case
    docs = case["docs"]
    O.fetch_url = lambda url, timeout=30, D=docs: D.get(url) or ""
    res = O.scan_mode(case["days_back"], list(case["tickers"]) if case["tickers"] is not None else None)
    files = sorted(f for f in os.listdir(str(O.OUTPUT_DIR)) if f.startswith("buyback_scan_"))
    doc = json.load(open(os.path.join(str(O.OUTPUT_DIR), files[-1]))) if files else None
    out["scans"].append({"results": res, "file": files[-1] if files else None, "doc": doc})
print(json.dumps(out))
'''

KEYWORDS = [
    "stock repurchase program", "stock repurchase plan", "stock repurchase authorization",
    "stock repurchase authorisation", "share repurchase program", "share repurchase plan",
    "share repurchase authorization", "share repurchase authorisation", "repurchase of ", "repurchase up to ",
    "buyback program", "buyback plan", "buyback authorization", "buyback authorisation",
    "authorized a stock repurchase", "authorised the share repurchase", "authorized the stock repurchase",
    "board authorized a repurchase", "board approved the repurchase", "board authorised the repurchase",
    "Stock Repurchase Program", "SHARE REPURCHASE PLAN", "Board Approved a Repurchase", "Buyback Program",
]
NEAR_MISSES = ["repurchase agreement", "stock repurchases", "buy back", "repurchased", "share buy-back program",
               "repurchase obligations", "buybacks", "authorized a stock split", "board approved the merger"]
PCTS = ["5%", "5.0%", "4.9%", "4.99 %", "7.5 percent", "10 %", "12.25%", "50%", "50.01%", "51%", "0.5%", "1%", "0.99%",
        "100%", "3 percent", "6 Percent", "8 PERCENT", "5 %", "15%", "20 percent", "2.5%", "45%", "5 per cent",
        "9.%", ".5%", "1,5%", "25%"]
DOLLARS = ["$1.5 billion", "$500 million", "$10,000,000", "$9,999,999", "$2.5B", "$750M", "$5 million",
           "$12.5 Million", "$.5 billion", "$1,000", "$3.2bn", "$ 50 million", "$1.2.3 million", "$. million",
           "$10 million", "$9.99 million", "$100,000,000", "$1 billion", "$0.01 billion", "$25,000,000.00", "$,"]
FILLER = [
    "The Company reported revenue growth of 12% for the quarter.", "Gross margin was 35 percent.",
    "On {d}, the Company issued a press release.", "Item 8.01 Other Events.", "Item 2.02 Results of Operations.",
    "Net income increased to $4.2 million.", "The notes bear interest at 6.5% per annum.",
    "Forward-looking statements involve risks and uncertainties.", "Exhibit 99.1 Press release dated {d}.",
    "Shares outstanding were approximately 120,000,000.", "<p style=\"font-size:10pt\">SIGNATURES</p>",
    "Pursuant to the requirements of the Securities Exchange Act of 1934.", "The dividend yield is 2%.",
    "Café İstanbul operations grew 30%.", "Operating expenses decreased 7 percent year over year.",
    "The Board of Directors declared a quarterly dividend of $0.25 per share.", "&nbsp;&nbsp;", "—",
]


def _sentence_with(rnd, kw):
    tpl = rnd.choice(["On {d}, the Board {kw}{x}.", "The {kw}{x} was approved.", "{kw}{x}",
                      "The Company announced a {kw}{x} for up to {p} of its outstanding shares.",
                      "The {kw}{x} covers {p} of shares outstanding."])
    return tpl.format(d="October 1, 2026", kw=kw, x=rnd.choice(["", " of up to", " totaling", " (the \"Program\")"]),
                      p=rnd.choice(PCTS))


def _text(rnd):
    parts = [rnd.choice(FILLER).format(d="2026-10-01") for _ in range(rnd.randint(0, 12))]
    u = rnd.random()
    if u < 0.80:
        kw = rnd.choice(KEYWORDS)
        pos = rnd.randint(0, len(parts))
        parts.insert(pos, _sentence_with(rnd, kw))
        # percentages at controlled distances from the keyword sentence
        for _ in range(rnd.randint(0, 3)):
            pad = " " * rnd.choice((0, 10, 200, 480, 495, 499, 500, 501, 510, 700, 1200))
            p = rnd.choice(PCTS)
            if rnd.random() < 0.5:
                parts.insert(pos + 1, pad + "representing " + p + " of shares")
            else:
                parts.insert(pos, "representing " + p + " of shares" + pad)
    elif u < 0.92:
        parts.insert(rnd.randint(0, len(parts)), "The " + rnd.choice(NEAR_MISSES) + " covers " + rnd.choice(PCTS))
    for _ in range(rnd.randint(0, 3)):
        parts.insert(rnd.randint(0, len(parts)), "an amount of " + rnd.choice(DOLLARS))
    sep = rnd.choice((" ", "\n", "<br/>", "  "))
    text = sep.join(parts)
    v = rnd.random()
    if v < 0.08:
        text = text.upper()
    elif v < 0.12:
        text = text.lower()
    return text


def _texts(rnd, n):
    out = []
    for _ in range(n):
        out.append({"text": _text(rnd), "ticker": rnd.choice(("aapl", "MSFT", "Nvda", "BRK.B", "x")),
                    "filing_date": rnd.choice(("2026-10-01", "2026-09-15", "", None))})
    return out


# --------------------------------------------------------------------------------------------- Part B: scans
def _scan_case(rnd, idx, texts):
    now = datetime(2026, 10, 16, 11, 35, tzinfo=timezone.utc).timestamp() + rnd.randint(-200, 200) * 86400 \
        + rnd.randint(0, 86399) + rnd.random()
    today = datetime.fromtimestamp(now, tz=timezone.utc).date()
    pool = ["AAPL", "MSFT", "NVDA", "AMD", "ARM", "MU", "LITE", "AEHR", "XOM", "WMT"]
    tickers = rnd.sample(pool, rnd.randint(0, 6))
    if rnd.random() < 0.15:
        tickers = [" " + t + " " if rnd.random() < 0.5 else t.lower() for t in tickers]
    if rnd.random() < 0.03:
        tickers = None
    docs = {}
    ct, n = {}, 0
    for t in pool:
        u = rnd.random()
        if u < 0.08:
            continue                                            # not listed: cik_not_found
        cik = 100000 + pool.index(t) * 7 + idx % 5
        ct[str(n)] = {"cik_str": cik, "ticker": t, "title": t + " Inc"}
        n += 1
        if u < 0.14:                                            # a duplicate ticker row: the first wins
            ct[str(n)] = {"cik_str": cik + 1, "ticker": t.lower(), "title": t + " Holdings"}
            n += 1
    if rnd.random() < 0.05:
        ct[str(n)] = {"cik_str": 1, "title": "no ticker"}       # a row without a ticker
        n += 1
    if rnd.random() > 0.04:
        docs["https://www.sec.gov/files/company_tickers.json"] = json.dumps(ct)
    for row in ct.values():
        if "ticker" not in row or row["ticker"] != row["ticker"].upper():
            continue
        cik = str(row["cik_str"]).zfill(10)
        u = rnd.random()
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        if u < 0.06:
            continue                                            # fetch failed: filings_fetch_failed
        if u < 0.09:
            docs[url] = "<html>Access denied</html>"            # unreadable: no filings, no error
            continue
        forms, acc, dates, prim = [], [], [], []
        for i in range(rnd.randint(0, 40)):
            forms.append(rnd.choice(("8-K", "8-K", "8-K", "10-Q", "8-K/A", "4", "SC 13G")))
            acc.append("0000%06d-26-%06d" % (row["cik_str"], i))
            back = rnd.choice((0, 1, 5, 20, 28, 29, 30, 31, 45, 90)) + i // 5
            dates.append((today - timedelta(days=back)).isoformat())
            prim.append(rnd.choice(("d8k.htm", "form8-k.htm", "ex99.htm")))
        if acc and rnd.random() < 0.03:
            dates[0] = "2026-13-01"                             # malformed: a scan error for this ticker
        if acc and rnd.random() < 0.03:
            prim = prim[:-1]                                    # ragged arrays: the old's exception -> no filings
        docs[url] = json.dumps({"cik": cik, "filings": {"recent": {"form": forms, "accessionNumber": acc,
                                                                   "filingDate": dates, "primaryDocument": prim}}})
        for i, a in enumerate(acc):
            if i < len(prim) and rnd.random() > 0.05:
                docs[f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a.replace('-', '')}/{prim[i]}"] = \
                    rnd.choice(texts)["text"]
    return {"now": now, "days_back": rnd.choice((30, 30, 30, 7, 60)), "tickers": tickers, "docs": docs}


def _window_pct(text):
    """diagnostics only: the first in-band (1-50) percentage in the keyword's window, None, or "no_keyword"."""
    tl = text.lower()
    for pt in P.BUYBACK_PATTERNS:
        m = re.search(pt, tl)
        if m:
            ctx = text[max(0, m.start() - 500):min(len(text), m.end() + 500)]
            for v in re.findall(P.PCT_PATTERN, ctx, re.IGNORECASE):
                try:
                    v = float(v)
                except ValueError:
                    continue
                if 1 <= v <= 50:
                    return v
            return None
    return "no_keyword"


def _port_scan(case, d):
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))

    def fetch(url, timeout=30, as_text=False, headers=None, D=case["docs"]):
        assert as_text and (headers or {}).get("User-Agent")
        v = D.get(url)
        if v is None:
            return None                                         # the desk's get: a 404 is None
        return v

    sc = P.Scanner(d, clock=lambda c=case["now"]: c, fetch=fetch, sleep=lambda s: None)
    res = sc.scan_mode(case["days_back"], list(case["tickers"]) if case["tickers"] is not None else None)
    files = sorted(f for f in os.listdir(d) if f.startswith("buyback_scan_"))
    doc = json.load(open(os.path.join(d, files[-1]))) if files else None
    return {"results": res, "file": files[-1] if files else None, "doc": doc}


def run():
    rnd = random.Random(1016)
    texts = _texts(rnd, N_TEXTS)
    scans = [_scan_case(rnd, i, texts) for i in range(N_SCANS)]
    old = old_run(OLD, {"texts": texts, "scans": scans})
    diffs, stats = [], {"texts": len(texts), "qualifying": 0, "with_dollar": 0, "pct_values": {},
                        "scans": len(scans), "scan_results": 0,
                        "scan_errors": {}, "scans_written": 0}
    P._LAST[0] = 0.0
    for t, o in zip(texts, old["parse"]):
        p = P.parse_buyback(t["text"], t["ticker"], t["filing_date"])
        if json.dumps(p, sort_keys=True) != json.dumps(o, sort_keys=True):
            diffs.append({"part": "parse", "text": t["text"][:300], "old": o, "port": p})
        if o:
            stats["qualifying"] += 1
            stats["with_dollar"] += o["dollar_amount"] is not None
            k = str(o["buyback_pct"])
            stats["pct_values"][k] = stats["pct_values"].get(k, 0) + 1
        else:
            w = _window_pct(t["text"])
            k = "no_keyword" if w == "no_keyword" else "keyword_no_pct_in_window" if w is None else \
                "keyword_pct_below_5"
            stats[k] = stats.get(k, 0) + 1
    tmp = tempfile.mkdtemp()
    try:
        for i, (c, o) in enumerate(zip(scans, old["scans"])):
            p = _port_scan(c, tmp)
            if json.dumps(p, sort_keys=True) != json.dumps(o, sort_keys=True):
                diffs.append({"part": "scan", "case": i, "old": o, "port": p})
            stats["scan_results"] += len(o["results"])
            stats["scans_written"] += o["file"] is not None
            for e in (o["doc"] or {}).get("errors") or []:
                k = e["error"].split(":")[0]
                stats["scan_errors"][k] = stats["scan_errors"].get(k, 0) + 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    res = {"sleeve": "edgar_buyback", "cases": len(texts) + len(scans),
           "identical": len(texts) + len(scans) - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs),
           "stats": stats,
           "method": "A: the old parse_buyback vs the port's on synthetic 8-K texts; B: the old scan_mode (its real "
                     "check_ticker / ticker_to_cik / get_recent_filings / fetch_filing_text / parse_buyback / scan "
                     "writer; fetch_url and the clock stubbed, HOME a temp dir) vs Scanner.scan_mode on the same "
                     "synthetic SEC documents — results, errors and scan files compared exactly",
           "divergences": {"not_in_this_comparison": [
               "HTTP: the desk's data/http.get (retries on 429/5xx/transport; the old made one attempt)",
               "the old static ticker->CIK research map (absent here, as on this desk)",
               "company_tickers.json downloaded once per scan (the same first-match rule)",
               "U+FFFD: the desk's text decode marks invalid UTF-8, removed again (= the old errors='ignore')",
               "User-Agent from SEC_USER_AGENT (the old header's personal email is not carried)"]}}
    write_receipt("edgar_buyback", res)
    return res
