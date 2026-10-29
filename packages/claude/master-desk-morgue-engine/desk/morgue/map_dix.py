"""THE MAP, DIX: dark-pool short-sale ratios from FINRA's free daily FNQC file (SqueezeMetrics' published construction).

DIX = the dollar-weighted average of the constituents' off-exchange short volume over total volume. Three numbers, never
substituted for one another:
  etf     each ETF's own FNQC short / total ratio (SPY, QQQ, IWM) and their simple mean
  index   the constituent-weighted index over the S&P 500's names, weights = the last session's close x volume (the
          desk's declared weight: the vendor's exact constituent handling was never published). Under 80% constituent
          coverage it is no_data with the reason, never a partial number presented whole.
  roster  the same construction over the desk's 1,838-name roster, from the same file and the cached bars: always
          computable, labelled as the roster's, not the S&P 500's.
FINRA posts the file after the close, so the value is the latest completed session's and says its date. The file's
symbols use a slash for a share class (BRK/B); the desk uses a dot (BRK.B): norm() makes them one."""
import csv
import io
import re

from . import no_data, stamp

SOURCE = "FINRA FNQC daily short-volume file"
DELAY = "posts after the close; the newest file is the last completed session's"
CONSTRUCTION = ("constituent-weighted DIX (SqueezeMetrics' published definition: the dollar-weighted average of the "
                "constituents' off-exchange short-sale ratios)")
NOT_THE_SAME_AS = ("the per-ETF DIX ratio (the ETF's own FNQC short over total) is a different construction; the two are "
                   "never substituted for each other")
COVERAGE_FLOOR = 0.8
MIN_NAMES = 400                    # a constituent list under this many names is a partial or a wrong page, not the index
WEIGHT_SOURCE = "last session's close x volume from the desk's split-adjusted daily bars (the desk's declared weight)"


def norm(sym):
    """one spelling of a ticker: FINRA's BRK/B and the desk's BRK.B are the same symbol"""
    return (sym or "").strip().upper().replace("/", ".")


def parse_fnqc(text):
    """the pipe-delimited FNQC file -> {symbol: (short_volume, total_volume)}; the header, the trailing record count and
    any line that does not parse are skipped"""
    out = {}
    for line in (text or "").strip().splitlines()[1:]:
        p = line.split("|")
        if len(p) < 5:
            continue
        try:
            out[norm(p[1])] = (float(p[2]), float(p[4]))
        except ValueError:
            continue
    return out


def etf_ratios(data, funds):
    """{symbol: {"ratio","short_volume","total_volume"}} for the funds the file carries, and their mean"""
    out = {}
    for s in funds:
        v = data.get(s)
        if v and v[1] > 0:
            out[s] = {"ratio": round(v[0] / v[1], 4), "short_volume": round(v[0], 1), "total_volume": round(v[1], 1)}
    avg = (sum(r["ratio"] for r in out.values()) / len(out)) if out else None
    return out, (None if avg is None else round(avg, 4))


def weighted_dix(data, names, weights, floor=COVERAGE_FLOOR):
    """sum(w x short/total) / sum(w) over the names that have a file row (total > 0) and a weight (> 0) ->
    (value or None, used, total, coverage). Below the coverage floor the value is None."""
    used, wsum, acc = 0, 0.0, 0.0
    for sym in names:
        v, w = data.get(sym), weights.get(sym)
        if v and v[1] > 0 and w and w > 0:
            used += 1
            wsum += w
            acc += w * (v[0] / v[1])
    total = len(names)
    cov = (used / total) if total else 0.0
    if not total or cov < floor or wsum <= 0:
        return None, used, total, cov
    return acc / wsum, used, total, cov


def index_block(file_date, data, constituents, weights, route, weights_error=None, floor=COVERAGE_FLOOR):
    """the contract's morgue.map.dix.index block"""
    base = dict(construction=CONSTRUCTION, not_the_same_as=NOT_THE_SAME_AS, route=route, weight_source=WEIGHT_SOURCE)
    if not constituents:
        return no_data("no S&P 500 constituent list from any route" + (f": {weights_error}" if weights_error else ""),
                       file_date, SOURCE, DELAY, value=None, constituents_used=0, constituents_total=0, coverage=0.0,
                       **base)
    if not weights:
        return no_data("constituent dollar-volume weights unavailable" + (f": {weights_error}" if weights_error else ""),
                       file_date, SOURCE, DELAY, value=None, constituents_used=0,
                       constituents_total=len(constituents), coverage=0.0, **base)
    val, used, total, cov = weighted_dix(data, constituents, weights, floor)
    if val is None:
        return no_data(f"constituent coverage {cov:.0%} is below the {floor:.0%} floor ({used} of {total} names)",
                       file_date, SOURCE, DELAY, value=None, constituents_used=used, constituents_total=total,
                       coverage=round(cov, 4), **base)
    return stamp("ok", file_date, SOURCE, DELAY, value=round(val, 4), constituents_used=used,
                 constituents_total=total, coverage=round(cov, 4), **base)


def roster_block(file_date, data, roster, weights, floor=COVERAGE_FLOOR):
    """the contract's morgue.map.dix.roster block"""
    base = dict(construction="the same dollar-weighted construction over the desk's roster, not the S&P 500",
                not_the_same_as=NOT_THE_SAME_AS, weight_source=WEIGHT_SOURCE)
    if not weights:
        return no_data("no cached daily bars to weight by", file_date, SOURCE, DELAY, value=None, names_used=0,
                       names_total=len(roster), coverage=0.0, **base)
    val, used, total, cov = weighted_dix(data, roster, weights, floor)
    if val is None:
        return no_data(f"roster coverage {cov:.0%} is below the {floor:.0%} floor ({used} of {total} names)",
                       file_date, SOURCE, DELAY, value=None, names_used=used, names_total=total,
                       coverage=round(cov, 4), **base)
    return stamp("ok", file_date, SOURCE, DELAY, value=round(val, 4), names_used=used, names_total=total,
                 coverage=round(cov, 4), **base)


def dix_block(file_date, data, funds, index, roster, why_missing=None):
    """the contract's morgue.map.dix block from a parsed file (data) or its absence (why_missing)"""
    if not data:
        return no_data(why_missing or "no FNQC file in the last 8 days", file_date, SOURCE, DELAY, file_date=file_date,
                       etf={}, etf_avg=None, index=index, roster=roster)
    etf, avg = etf_ratios(data, funds)
    return stamp("ok", file_date, SOURCE, DELAY, file_date=file_date, etf=etf, etf_avg=avg, index=index, roster=roster)


# ---- the S&P 500 constituent list (two routes; either may be refused: the block says which) -------------------------

def parse_ivv_csv(text):
    """iShares' IVV holdings file -> [tickers] of its equity rows. The file opens with fund lines, then a header row that
    starts 'Ticker,'; rows are quoted CSV. Cash, futures and other asset classes are skipped. iShares writes a share
    class without a separator (BRKB): such a name will not match the file's BRK.B, which the coverage figure shows."""
    rows = list(csv.reader(io.StringIO((text or "").lstrip("﻿"))))
    head = next((i for i, r in enumerate(rows) if r and r[0].strip().strip('"') == "Ticker"), None)
    if head is None:
        return []
    cols = [c.strip() for c in rows[head]]
    ti, ai = cols.index("Ticker"), (cols.index("Asset Class") if "Asset Class" in cols else None)
    out = []
    for r in rows[head + 1:]:
        if len(r) <= ti or not r[ti].strip() or r[ti].strip() == "-":
            continue
        if ai is not None and len(r) > ai and r[ai].strip().lower() != "equity":
            continue
        t = norm(r[ti])
        if re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", t):
            out.append(t)
    return sorted(set(out))


def parse_wikitext_sp500(text):
    """Wikipedia's 'List of S&P 500 companies' wikitext -> [tickers] of the first table's rows. A row (split at '|-')
    starts with its ticker cell: {{NyseSymbol|MMM}}, {{Nasdaq link|AAPL}}, an external link [https://... MMM], a wiki
    link [[...|MMM]] or the plain ticker."""
    out = []
    body = text or ""
    start = body.find("{|")
    if start < 0:
        return []
    end = body.find("\n|}", start)
    table = body[start:end if end > 0 else len(body)]
    for row in table.split("\n|-")[1:]:
        cell = next((ln[1:].split("||")[0] for ln in row.splitlines() if ln.startswith("|") and not ln.startswith("|-")),
                    None)
        if cell is None:
            continue
        m = (re.search(r"\{\{\s*(?:nyse|nasdaq)[^|}]*\|\s*([A-Z][A-Z.\-]{0,9})\s*\}\}", cell, re.I)
             or re.search(r"\[https?://[^\s\]]+\s+([A-Z][A-Z.\-]{0,9})\]", cell)
             or re.search(r"\[\[[^\]|]*\|([A-Z][A-Z.\-]{0,9})\]\]", cell)
             or re.fullmatch(r"\s*([A-Z][A-Z.\-]{0,9})\s*", cell))
        if m:
            t = norm(m.group(1).replace("-", "."))
            if t not in out:
                out.append(t)
    return sorted(out)


def sp500_constituents(getter=None, errors=None):
    """-> (tickers, route) from the first route that yields at least 400 names; the errors of the routes tried go to
    `errors` (a list). The caller caches the answer for a week."""
    from . import fetch
    errors = errors if errors is not None else []
    for route, url, parse in (("iShares IVV holdings file", fetch.IVV_HOLDINGS, parse_ivv_csv),
                              ("Wikipedia list of S&P 500 companies", fetch.WIKI_SP500, parse_wikitext_sp500)):
        try:
            body = fetch.text(url, getter, timeout=60, tries=2)
            names = parse(body or "")
            if len(names) >= MIN_NAMES:
                return names, route
            errors.append(f"{route}: {len(names)} names parsed (fewer than {MIN_NAMES})")
        except Exception as e:                                         # noqa: BLE001  (the next route serves)
            errors.append(f"{route}: {type(e).__name__}: {str(e)[:100]}")
    return [], None


def dollar_weights(bars_by_symbol):
    """{symbol: last close x volume} from daily bars (ascending dicts with c and v)"""
    out = {}
    for sym, bars in bars_by_symbol.items():
        for b in reversed(bars or []):
            try:
                c, v = float(b["c"]), float(b["v"])
            except (KeyError, TypeError, ValueError):
                continue
            if c > 0 and v > 0:
                out[norm(sym)] = c * v
            break
    return out
