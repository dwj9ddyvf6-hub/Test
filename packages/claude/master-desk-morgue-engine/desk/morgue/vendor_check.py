"""MG8, the acceptance check of Slice 1: do our DIX and GEX track SqueezeMetrics' public daily series?

The public file (squeezemetrics.com's DIX.csv) has the columns date, price, dix, gex: dix a fraction, gex in dollars for the
S&P 500 index. Ours differ by construction (the DIX here is built from FNQC for the constituents, the GEX from SPY's chain
by SpotGamma's convention), so the check asks for what must agree, not for equal levels:
  DIX  mean absolute difference <= DIX_MAD_MAX (3 points of ratio) over the overlap;
  GEX  the sign of our net gamma agrees with theirs on >= GEX_SIGN_MIN of days, and the rank correlation is >= GEX_RANK_MIN.
Both need at least MIN_OVERLAP common days; fewer is no_data with the count, never a pass. The thresholds are set here, before any
real overlap was looked at.

Nothing is stored: compare() takes the CSV text and returns numbers (SqueezeMetrics data is allowed, owner ruling DAT-12; the
check holds the text only in memory). fetch_csv() is the one read, through the desk's data layer; it is UNVERIFIED live."""
import csv
import io
import math
from datetime import date

from .. import calendar as cal
from . import ledger

CSV_URL = "https://squeezemetrics.com/monitor/static/DIX.csv"
DIX_MAD_MAX = 0.03
GEX_SIGN_MIN = 0.80
GEX_RANK_MIN = 0.50
MIN_OVERLAP = 30


def parse_vendor_csv(text):
    """{date: {"dix","gex"}} from the public file's text; a row that does not parse is skipped"""
    out = {}
    for r in csv.DictReader(io.StringIO(text or "")):
        try:
            out[r["date"].strip()] = {"dix": float(r["dix"]), "gex": float(r["gex"])}
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return out


def fetch_csv(getter=None):
    from . import fetch
    return fetch.text(CSV_URL, getter, timeout=45, tries=2)


def ours_rows(root):
    """[{"date","dix","gex"}] from the ledger: the DIX index of each FNQC file date, and the SPY Map card's net gamma dated to the
    session whose close its open interest is (the card is built before the open, from the prior close)"""
    dix, gex = {}, {}
    for r in ledger.read(root):
        if r.get("component") == "dix" and isinstance(r.get("value"), dict):
            v = r["value"]
            if v.get("file_date") and v.get("index") is not None:
                dix[v["file_date"]] = float(v["index"])
        elif r.get("component") == "gex_static_v1" and r.get("underlying") == "SPY" and r.get("as_of"):
            try:
                d = cal.prev_trading_day(date.fromisoformat(r["as_of"])).isoformat()
            except ValueError:
                continue
            gex[d] = float(r["net_gex_usd_per_1pct"])
    return [{"date": d, "dix": dix.get(d), "gex": gex.get(d)} for d in sorted(set(dix) | set(gex))]


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out, i = [0.0] * len(xs), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2.0
        i = j + 1
    return out


def _corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((x - mb) ** 2 for x in b))
    return None if sa == 0 or sb == 0 else sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def compare(ours, vendor_text):
    """the acceptance numbers over the dates both series hold -> {"status","reason","dix": {...},"gex": {...},"passed"}"""
    vendor = parse_vendor_csv(vendor_text)
    dpairs = [(o["dix"], vendor[o["date"]]["dix"]) for o in ours if o.get("dix") is not None and o["date"] in vendor]
    gpairs = [(o["gex"], vendor[o["date"]]["gex"]) for o in ours if o.get("gex") is not None and o["date"] in vendor]
    out = {"min_overlap": MIN_OVERLAP, "thresholds": {"dix_mad_max": DIX_MAD_MAX, "gex_sign_min": GEX_SIGN_MIN,
                                                      "gex_rank_min": GEX_RANK_MIN}}
    if len(dpairs) < MIN_OVERLAP and len(gpairs) < MIN_OVERLAP:
        return {"status": "no_data", "reason": f"{len(dpairs)} DIX days and {len(gpairs)} GEX days overlap, {MIN_OVERLAP} needed",
                "passed": None, **out}
    res = {}
    if len(dpairs) >= MIN_OVERLAP:
        diffs = [abs(a - b) for a, b in dpairs]
        mad = sum(diffs) / len(diffs)
        res["dix"] = {"n": len(dpairs), "mad": mad, "max": max(diffs), "ok": mad <= DIX_MAD_MAX}
    if len(gpairs) >= MIN_OVERLAP:
        agree = sum(1 for a, b in gpairs if (a > 0) == (b > 0)) / len(gpairs)
        rc = _corr(_ranks([a for a, _ in gpairs]), _ranks([b for _, b in gpairs]))
        res["gex"] = {"n": len(gpairs), "sign_agreement": agree, "rank_corr": rc,
                      "ok": agree >= GEX_SIGN_MIN and rc is not None and rc >= GEX_RANK_MIN}
    return {"status": "ok", "passed": all(v["ok"] for v in res.values()), **res, **out}
