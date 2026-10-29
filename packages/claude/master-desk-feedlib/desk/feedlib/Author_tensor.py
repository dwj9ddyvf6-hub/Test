"""The Author desk's Tensor stack (Author-desk@652db7af src/lib/tensor + tensor0), executed, never reimplemented.

desk/vendor/Author_mon/src/lib holds the closure of adapter.ts analyzeSymbol, tensor0/read.ts, anna-printer.ts,
inferred-weights.ts and live-signals.ts byte-exact (git blob pins in desk/vendor/MANIFEST.json, re-verified before
every run and by tests/test_vendor.py). desk/feedlib/node/Author_tensor.mjs calls the source's own entry points
with fetch serving the desk's tapes as the Yahoo chart API results the source's yahoo.ts requested (rangeFor):
  60m  range 1y, regular session      (the 1h frame: the desk's, the owner's 1H decision 2026-10-18)
  5m   range 1mo, pre/post included   (the watch desk's default frame and Tensor 0's clock; the GREEN study's)
  1d   range 2y                        (analyzeSymbol's daily horizon frame)
and Date reading the pass clock. One node process per call (bounded heap)."""
import calendar
from datetime import datetime

from ..util import ET
from . import node_source as NS

PREFIX = "Author_mon/src/lib/"
RUNNER = "Author_tensor.mjs"
MIN_FILES = 31


def month_back(now):
    d = datetime.fromtimestamp(now, tz=ET)
    y, m = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1])).timestamp()


def years_back(now, n):
    d = datetime.fromtimestamp(now, tz=ET)
    try:
        return d.replace(year=d.year - n).timestamp()
    except ValueError:
        return d.replace(year=d.year - n, day=28).timestamp()


def charts(symbol, bars, bars1d, now, interval="5m"):
    """the two chart results analyzeSymbol(symbol, interval) fetches (keyed by the request's interval parameter), cut
    to the source's ranges: 1h -> "60m" from a year back, 5m -> "5m" from a month back; the 1d horizon from two
    years back."""
    t1 = years_back(now, 2)
    if interval == "1h":
        key, cut = "60m", years_back(now, 1)
    else:
        key, cut = "5m", month_back(now)
    return {key: NS.yahoo_chart(symbol, [b for b in bars if float(b["t"]) >= cut]),
            "1d": NS.yahoo_chart(symbol, [b for b in bars1d if float(b["t"]) >= t1])}


def analyze(requests, now, timeout=600, chunk=8, workspace=None, interval="5m"):
    """[{symbol, charts}] -> one result per request (status, the current replica row, Tensor context, native read,
    causal events, forecast / prognosis / frames, Tensor 2 marker, printer snapshot, inferred evidence; on the 5m
    frame also the Green event + gold class and the Tensor 0 frame, and — with `workspace`, the GREEN study's
    directory — the study's live snapshot of a GREEN print / its control). `now` in epoch seconds."""
    if not requests:
        return []
    NS.verify(PREFIX, MIN_FILES)
    out = []
    study = {"workspace": workspace} if workspace else None
    for i in range(0, len(requests), chunk):
        res = NS.run(RUNNER, {"now": int(now * 1000), "mode": "pass", "interval": interval, "study": study,
                              "requests": requests[i:i + chunk]}, timeout=timeout)
        out += res["results"]
    return out


def sessions_back(now, n):
    """the first epoch of Yahoo's `{n}d` intraday range: the session start n trading days back (inclusive)."""
    from .. import calendar as cal
    d = cal._as_date(now)
    k = 0
    while True:
        if cal.is_trading_day(d):
            k += 1
            if k == n:
                break
        d = d.fromordinal(d.toordinal() - 1)
    return datetime(d.year, d.month, d.day, tzinfo=ET).timestamp()


def study_eod(now, date_et, bars1m, workspace, timeout=900):
    """runGreenStudy(dateEt) in the study's workspace on the 1m tapes ({symbol: bars}, Yahoo's 5d range with
    pre/post) -> {n, marked, controls, report}."""
    NS.verify(PREFIX, MIN_FILES)
    t0 = sessions_back(now, 5)
    charts1 = {s: NS.yahoo_chart(s, [b for b in bl if float(b["t"]) >= t0]) for s, bl in bars1m.items()}
    res = NS.run(RUNNER, {"now": int(now * 1000), "mode": "study_eod", "study": {"workspace": workspace},
                          "eod": {"dateEt": date_et, "charts": charts1}}, timeout=timeout)
    return res["study"]
