"""The Morgue Engine's public-data reads, through the desk's data layer (desk/data/http.py): one User-Agent, a shared
per-host rate ledger (the jobs run in the bulk lane and yield to the loop), retries with backoff, the refusal breaker.

Every function takes a `getter` (default: http.get) so a test serves recorded text and no network is touched.

Hosts and their pacing (http._LIMITS): cdn.finra.org 0.1 s, data.sec.gov / www.sec.gov 0.15 s (the SEC allows 10 a
second), api.nasdaq.com 0.25 s, www.ishares.com and en.wikipedia.org 1 s (added with this port). The SEC contact is
$SEC_USER_AGENT, else the desk's default naming Jack Tailor, no email (owner, 2026-10-27; edgar_buyback.user_agent)."""
from datetime import date, timedelta

from ..data import http
from ..feedlib import edgar_buyback

FNQC = "https://cdn.finra.org/equity/regsho/daily/FNQCshvol{yyyymmdd}.txt"
NASDAQ_SI = "https://api.nasdaq.com/api/quote/{sym}/short-interest?assetclass=stocks"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SEC_CONCEPT = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/dei/EntityCommonStockSharesOutstanding.json"
SEC_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
IVV_HOLDINGS = ("https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/1467271812596.ajax"
                "?fileType=csv&fileName=IVV_holdings&dataType=fund")
WIKI_SP500 = "https://en.wikipedia.org/w/index.php?title=List_of_S%26P_500_companies&action=raw"
SEC_13F_BASES = ("https://www.sec.gov/files/structureddata/data/form-13f-data-sets/",
                 "https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/")


def sec_headers():
    return {"User-Agent": edgar_buyback.user_agent()}


def text(url, getter=None, headers=None, timeout=30, tries=3):
    """the body as text; None on a 404; raises what http.get raised on a refusal or a transport failure"""
    return (getter or http.get)(url, as_text=True, headers=headers, timeout=timeout, tries=tries)


def json_(url, getter=None, headers=None, timeout=30, tries=3):
    return (getter or http.get)(url, headers=headers, timeout=timeout, tries=tries)


def binary(url, getter=None, headers=None, timeout=900, tries=2):
    return (getter or http.get)(url, as_bytes=True, headers=headers, timeout=timeout, tries=tries)


def sec_text(url, getter=None, timeout=30):
    return text(url, getter, sec_headers(), timeout)


def sec_json(url, getter=None, timeout=30):
    return json_(url, getter, sec_headers(), timeout)


def fnqc_dates(today, max_back=7):
    """the dates to try for the newest FNQC file, newest first"""
    return [today - timedelta(days=i) for i in range(max_back + 1)]


def fnqc_latest(today=None, getter=None, max_back=7):
    """walk back from today to the newest published FNQC file -> (ISO date, text, tried), or (None, None, tried) with no
    file in the window. FINRA's CDN answers 403 (not 404) for a file that is not posted (a weekend, a holiday, today's
    before the evening: probed 2026-10-27), so 403 and 404 mean 'not there' for this host; any other failure (429, 5xx,
    transport) is raised: a refusal is not 'no file'. `tried` lists the dates asked, for the reason a miss reports."""
    today = today or date.today()
    tried = []
    for d in fnqc_dates(today, max_back):
        tried.append(d.isoformat())
        try:
            body = text(FNQC.format(yyyymmdd=d.strftime("%Y%m%d")), getter, timeout=45, tries=2)
        except http.HttpError as e:
            if e.status in (403, 404):
                continue
            raise
        if body and body.strip():
            return d.isoformat(), body, tried
    return None, None, tried
