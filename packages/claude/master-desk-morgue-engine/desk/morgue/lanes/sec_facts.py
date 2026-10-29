"""L1, SEC companyfacts as point-in-time fundamentals: every fact keeps the date it was FILED, and a read for a decision date
sees only what had been filed by then (a restated figure replaces its earlier version only from its own filing date).

Source: data.sec.gov/api/xbrl/companyfacts/CIK##########.json, one name a request through the desk's data layer (the SEC
contact is 'Jack Tailor', no email; 0.15 s a request; owner rulings DAT-11, SEC-05). The reply is large, so only the CONCEPTS
the first outputs need are kept, as compact facts, under state/morgue/facts/ (one gzip file a name).

First outputs (functions of the point-in-time annual series): ROE, asset growth, gross profitability (Novy-Marx), accruals
(Sloan), Piotroski F (nine signals), Altman Z (the original five-term form; the market value of equity is an input, from
shares and a close, because the filings do not carry it). A figure the filings do not give is None with the reason, never a
default. Annual means the 10-K's fiscal-year duration (330 to 400 days) or its balance-sheet instant."""
import gzip
import json
import os
from datetime import date

from .. import fetch, state_path

DIR = "facts"
URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SOURCE = "SEC EDGAR companyfacts (XBRL), point in time by filing date"
DELAY = "a fact is visible from the day its filing was accepted"
# the first outputs' inputs; alternates are read in order, the first that exists for a period wins
CONCEPTS = {
    "assets": ["Assets"], "liabilities": ["Liabilities"], "equity": ["StockholdersEquity"],
    "net_income": ["NetIncomeLoss"], "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                                                 "SalesRevenueNet"],
    "gross_profit": ["GrossProfit"], "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "ebit": ["OperatingIncomeLoss"], "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "assets_current": ["AssetsCurrent"], "liabilities_current": ["LiabilitiesCurrent"],
    "ltd": ["LongTermDebtNoncurrent", "LongTermDebt"], "retained": ["RetainedEarningsAccumulatedDeficit"],
    "shares": ["WeightedAverageNumberOfSharesOutstandingBasic", "CommonStockSharesOutstanding"],
}
_WANT = {tag: key for key, tags in CONCEPTS.items() for tag in tags}


def parse_companyfacts(doc):
    """the companyfacts JSON -> compact facts [{"k","tag","end","start","val","filed","form","fy","fp"}] for the CONCEPTS (us-gaap
    USD and shares units); a malformed fact is skipped"""
    out = []
    for tag, node in ((doc.get("facts") or {}).get("us-gaap") or {}).items():
        key = _WANT.get(tag)
        if not key:
            continue
        for unit, rows in (node.get("units") or {}).items():
            if unit not in ("USD", "shares"):
                continue
            for r in rows:
                try:
                    date.fromisoformat(r["end"])
                    date.fromisoformat(r["filed"])
                    val = float(r["val"])
                except (KeyError, TypeError, ValueError):
                    continue
                out.append({"k": key, "tag": tag, "end": r["end"], "start": r.get("start"), "val": val,
                            "filed": r["filed"], "form": r.get("form"), "fy": r.get("fy"), "fp": r.get("fp")})
    return out


def _path(root, cik):
    return state_path(root, os.path.join(DIR, f"CIK{int(cik):010d}.json.gz"))


def save(root, cik, facts, fetched_on):
    p = _path(root, cik)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as fh:
        json.dump({"cik": int(cik), "fetched_on": fetched_on, "facts": facts}, fh, separators=(",", ":"))
    os.replace(tmp, p)


def load(root, cik):
    """(facts, fetched_on) or ([], None)"""
    try:
        with gzip.open(_path(root, cik), "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
        return doc.get("facts") or [], doc.get("fetched_on")
    except (OSError, ValueError, EOFError):
        return [], None


def refresh(root, cik, today, getter=None, max_age_days=30):
    """fetch and store a name's facts unless the stored copy is under `max_age_days` old -> "fetched", "fresh" or "missing" (the
    SEC has no such file: a 404); a refusal is raised"""
    _, on = load(root, cik)
    if on and (today - date.fromisoformat(on)).days < max_age_days:
        return "fresh"
    doc = fetch.sec_json(URL.format(cik=int(cik)), getter, timeout=60)
    if not doc:
        return "missing"
    save(root, cik, parse_companyfacts(doc), today.isoformat())
    return "fetched"


# ---- point-in-time reads ------------------------------------------------------------------------------------------------------

def _days(start, end):
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def annual(facts, key, asof):
    """[(end, value, filed)] ascending by period end: the annual figures of `key` as known on `asof` (filed on or before it).
    Per period the LATEST filing at or before asof wins (a restatement counts from its own filing date); the tags of a concept
    are read in order and the first tag with any annual figure is used. Flows must span 330-400 days, balances are instants."""
    for tag in dict.fromkeys(t for t, k in _WANT.items() if k == key):
        best = {}
        for f in facts:
            if f["k"] != key or f["tag"] != tag or f["filed"] > asof:
                continue
            if f.get("start"):
                if not 330 <= _days(f["start"], f["end"]) <= 400:
                    continue
            elif f.get("fp") != "FY":                      # a quarter-end balance is no annual figure
                continue
            cur = best.get(f["end"])
            if cur is None or f["filed"] > cur[2]:
                best[f["end"]] = (f["end"], f["val"], f["filed"])
        if best:
            return [best[e] for e in sorted(best)]
    return []


def _last2(facts, key, asof):
    s = annual(facts, key, asof)
    return (s[-1][1], s[-2][1]) if len(s) >= 2 else ((s[-1][1], None) if s else (None, None))


def _div(a, b):
    return None if a is None or b in (None, 0) else a / b


def fundamentals(facts, asof, market_cap=None):
    """the first outputs as known on `asof` (ISO date) -> a stamped dict: roe, asset_growth, gross_profitability, accruals,
    piotroski_f (with its signals), altman_z (needs market_cap). Each is None with its reason in "missing" where the filings
    on file by then do not support it. status no_data when the name has no annual assets by then."""
    g = {k: _last2(facts, k, asof) for k in CONCEPTS}
    ta, ta0 = g["assets"]
    base = {"as_of": asof, "source": SOURCE, "delay": DELAY}
    if ta is None:
        return {"status": "no_data", "reason": "no annual filing by this date", **base}
    ni, ni0 = g["net_income"]
    cfo, cfo0 = g["cfo"]
    eq, eq0 = g["equity"]
    rev, rev0 = g["revenue"]
    gp, gp0 = g["gross_profit"]
    if gp is None and rev is not None and g["cost_of_revenue"][0] is not None:
        gp = rev - g["cost_of_revenue"][0]
    if gp0 is None and rev0 is not None and g["cost_of_revenue"][1] is not None:
        gp0 = rev0 - g["cost_of_revenue"][1]
    missing = {}
    out = {"roe": _div(ni, (eq + eq0) / 2.0 if eq is not None and eq0 is not None else eq),
           "asset_growth": None if ta0 in (None, 0) else ta / ta0 - 1.0,
           "gross_profitability": _div(gp, ta),
           "accruals": _div(None if ni is None or cfo is None else ni - cfo,
                            (ta + ta0) / 2.0 if ta0 is not None else ta)}
    for k, v in out.items():
        if v is None:
            missing[k] = "an input is not in the filings on file by this date"
    # Piotroski F: nine signals, each 1 or 0; the score exists only when all nine can be computed
    roa, roa0 = _div(ni, ta), _div(ni0, ta0)
    lev, lev0 = _div(g["ltd"][0] or 0.0, ta), (_div(g["ltd"][1] or 0.0, ta0) if ta0 else None)
    cr, cr0 = _div(g["assets_current"][0], g["liabilities_current"][0]), _div(g["assets_current"][1], g["liabilities_current"][1])
    gm, gm0 = _div(gp, rev), _div(gp0, rev0)
    at, at0 = _div(rev, ta), _div(rev0, ta0)
    sh, sh0 = g["shares"]
    sig = {"roa_positive": None if roa is None else roa > 0, "cfo_positive": None if cfo is None else cfo > 0,
           "roa_up": None if roa is None or roa0 is None else roa > roa0,
           "cfo_exceeds_income": None if cfo is None or ni is None else cfo > ni,
           "leverage_down": None if lev is None or lev0 is None else lev < lev0,
           "current_ratio_up": None if cr is None or cr0 is None else cr > cr0,
           "no_new_shares": None if sh is None or sh0 is None else sh <= sh0,
           "gross_margin_up": None if gm is None or gm0 is None else gm > gm0,
           "asset_turnover_up": None if at is None or at0 is None else at > at0}
    unknown = sorted(k for k, v in sig.items() if v is None)
    out["piotroski_f"] = None if unknown else sum(1 for v in sig.values() if v)
    if unknown:
        missing["piotroski_f"] = "signals not computable: " + ", ".join(unknown)
    # Altman Z (original): 1.2 WC/TA + 1.4 RE/TA + 3.3 EBIT/TA + 0.6 MVE/TL + 1.0 Sales/TA
    parts = [_div(None if g["assets_current"][0] is None or g["liabilities_current"][0] is None
                  else g["assets_current"][0] - g["liabilities_current"][0], ta), _div(g["retained"][0], ta),
             _div(g["ebit"][0], ta), _div(market_cap, g["liabilities"][0]), at]
    if any(p is None for p in parts):
        out["altman_z"] = None
        missing["altman_z"] = ("market value of equity not given" if market_cap is None else
                               "an input is not in the filings on file by this date")
    else:
        out["altman_z"] = 1.2 * parts[0] + 1.4 * parts[1] + 3.3 * parts[2] + 0.6 * parts[3] + 1.0 * parts[4]
    out["piotroski_signals"] = sig
    latest_filed = max(f["filed"] for f in facts if f["k"] == "assets" and f["filed"] <= asof)
    return {"status": "ok", **base, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()},
            "missing": missing, "latest_filed": latest_filed, "fiscal_end": annual(facts, "assets", asof)[-1][0]}
