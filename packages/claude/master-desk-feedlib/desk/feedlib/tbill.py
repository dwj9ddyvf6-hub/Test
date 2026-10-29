"""The discount rate FREE_OPT_PARITY_V1's carry reads: the 3-month Treasury bill's secondary-market rate (FRED series
DTB3, the Federal Reserve's H.15 release; public CSV, no key), cached by a job.

  job    tbill_rate: fetch https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3, keep the newest observation with a
         value (a holiday's blank row is skipped) -> cache/tbill.json {"series": "DTB3", "date", "rate" (percent),
         "source", "source_sha256", "fetched_at"}; a failed fetch keeps the last file.
  load   the cached observation (None until the job has written one).
  discount(rate, days)  exp(-rate x days / 365): the continuously compounded discount factor."""
import hashlib
import math
import os
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3"
FILE = os.path.join("cache", "tbill.json")


def parse(csv_text):
    """the newest (date, rate %) with a value; None without one."""
    last = None
    for line in (csv_text or "").splitlines()[1:]:
        parts = line.strip().split(",")
        if len(parts) != 2:
            continue
        try:
            last = (parts[0], float(parts[1]))
        except ValueError:                           # "." or "": a day without an observation
            continue
    return last


def job(root, now, fetch=None):
    if fetch is None:
        from ..data.http import get

        def fetch(url):
            return get(url, as_text=True, timeout=30)
    try:
        text = fetch(URL)
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, str(e)[:160])}
    got = parse(text)
    if got is None:
        return {"error": "no observation in the DTB3 file"}
    doc = {"series": "DTB3", "date": got[0], "rate": got[1], "source": URL,
           "source_sha256": hashlib.sha256((text or "").encode("utf-8")).hexdigest(),
           "fetched_at": datetime.fromtimestamp(float(now), tz=timezone.utc).isoformat()}
    write_json_atomic(os.path.join(root, FILE), doc)
    return {"date": doc["date"], "rate": doc["rate"]}


def load(root):
    return read_json(os.path.join(root, FILE), None)


def discount(rate_pct, days):
    return math.exp(-float(rate_pct) / 100.0 * max(0.0, float(days)) / 365.0)
