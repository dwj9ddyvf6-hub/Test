"""The spec's listing filter (universe.listing_filter): which symbols are US common stocks, from Alpaca's asset list
(/v2/assets, class us_equity, active then inactive) and the ETF flags of Nasdaq Trader's symbol directory
(nasdaqlisted.txt column Symbol, otherlisted.txt column ACT Symbol).

The rule is applied in the research's own two stages (eyes/DEEP/alpaca_universe.py universe(), then build_panel.py
load()), which the spec states as one list:
  1. every asset row, in order: class us_equity, exchange NYSE, NASDAQ, AMEX, ARCA or BATS, the symbol pattern (a full
     match) and the first name rule; a symbol keeps its first row that passes (active rows come first);
  2. that row is dropped when its exchange is ARCA, when the second name rule matches its name, or when the
     directory flags the symbol as an ETF.
The symbol pattern and both name rules are read from the pinned spec's own text. Pure: the job fetches the inputs
(desk/analysis/job.py) and caches the result (desk/analysis/store.py)."""
import re

EXCHANGES = ("NYSE", "NASDAQ", "AMEX", "BATS")          # the spec's: ARCA-listed names are excluded
FIRST_STAGE = EXCHANGES + ("ARCA",)                     # stage 1 keeps ARCA rows, stage 2 drops them (as the research)
LISTING_VERSION = 1


def _rule(text):
    """the spec states each rule as '<pattern>  (<how it is applied>)'"""
    return text.split("  (", 1)[0]


def rules(spec):
    lf = spec["universe"]["listing_filter"]
    return {"symbol": re.compile(_rule(lf["symbol_regex"])),
            "name1": re.compile(_rule(lf["name_excluded_if_contains_1"]), re.I),
            "name2": re.compile(_rule(lf["name_excluded_if_contains_2"]), re.I)}


def etf_flags(text, column):
    """the symbols one Nasdaq Trader symbol-directory file flags ETF = Y (`column`: Symbol or ACT Symbol)"""
    lines = [x for x in (text or "").splitlines() if x.strip()]
    if not lines:
        raise ValueError("an empty symbol directory")
    head = [x.strip() for x in lines[0].split("|")]
    if "ETF" not in head or column not in head:
        raise ValueError("not a symbol directory: no ETF or %s column" % column)
    i, j = head.index(column), head.index("ETF")
    out = set()
    for line in lines[1:]:
        if line.startswith("File Creation Time"):
            continue
        p = line.split("|")
        if len(p) > max(i, j) and p[j].strip() == "Y" and p[i].strip():
            out.add(p[i].strip())
    return out


def build(assets, nasdaqlisted, otherlisted, spec):
    """the listing: {"symbols": {symbol: {name, exchange, status}} (the names that pass), "excluded": {symbol:
    reason}, "counts"}; a reason is class, exchange, symbol or name (stage 1, from the symbol's first row) or arca,
    fund_name or etf (stage 2)"""
    rl = rules(spec)
    etf = etf_flags(nasdaqlisted, "Symbol") | etf_flags(otherlisted, "ACT Symbol")
    first, why = {}, {}
    for a in assets or ():
        s, name = str(a.get("symbol") or ""), str(a.get("name") or "")
        if not s:
            continue
        if (a.get("class") or "us_equity") != "us_equity":
            r = "class"
        elif a.get("exchange") not in FIRST_STAGE:
            r = "exchange"
        elif not rl["symbol"].fullmatch(s):
            r = "symbol"
        elif rl["name1"].search(name):
            r = "name"
        else:
            r = None
        if r is None:
            first.setdefault(s, a)
        else:
            why.setdefault(s, r)
    keep, out = {}, {}
    for s, a in first.items():
        name = str(a.get("name") or "")
        if a.get("exchange") == "ARCA":
            out[s] = "arca"
        elif rl["name2"].search(name):
            out[s] = "fund_name"
        elif s in etf:
            out[s] = "etf"
        else:
            keep[s] = {"name": name, "exchange": a.get("exchange"), "status": a.get("status")}
    for s, r in why.items():
        if s not in first:                               # no row passed stage 1: the first row's reason
            out[s] = r
    counts = {"assets": len(assets or ()), "symbols": len(keep), "excluded": len(out), "etf_flags": len(etf)}
    for r in out.values():
        counts["excluded_" + r] = counts.get("excluded_" + r, 0) + 1
    return {"version": LISTING_VERSION, "symbols": keep, "excluded": out, "counts": counts}


def check(listing, symbol):
    """None when the symbol passes the listing filter, else why not ("not_listed": no Alpaca us_equity asset)"""
    if symbol in listing["symbols"]:
        return None
    r = listing["excluded"].get(symbol)
    return "not_listed" if r is None else "listing_" + r
