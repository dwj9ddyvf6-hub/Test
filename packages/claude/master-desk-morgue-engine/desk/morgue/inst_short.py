"""shortPositioning from FINRA short interest, as republished per name by Nasdaq's public quote API, and the point-in-time
store that keeps what was read.

Why Nasdaq: FINRA's own bulk file (cdn.finra.org/equity/shortinterest/) returned HTTP 403 and its query API HTTP 404 without
credentials on 2026-10-26 (Silicon's route probe), so the documented route is the exchange's republication of the same
FINRA numbers, free and keyless. A101 discipline from the original: a reading is admitted only on or after its publication
date; the store records the RETRIEVAL date as the publication date (never earlier than FINRA's, so conservatively
point-in-time going forward; there is no history before the first retrieval). The float basis is EDGAR shares outstanding
(declared; the file has no float). Leaf transform (the desk's): board.lin(shares short / shares outstanding in percent, 25, 0).
Short VOLUME (map_dix) is a different dataset and is never substituted here."""
import json
import os

from . import board, state_path

PIT = "short_interest_pit.jsonl"


def parse_short_interest(text):
    """a pipe-delimited FINRA short-interest file (symbol|settlement_date|si_shares|float_shares?|split_flag?) -> rows. FINRA's
    own bulk route is closed to the desk (HTTP 403 without credentials, 2026-10-26); the parser stays for the day it opens and
    for recorded excerpts."""
    out = []
    lines = [ln for ln in (text or "").strip().splitlines() if ln.strip()]
    for line in lines[1:]:
        p = line.split("|")
        if len(p) < 3:
            continue
        try:
            out.append({"symbol": p[0], "settlement_date": p[1], "si_shares": float(p[2]),
                        "float_shares": float(p[3]) if len(p) > 3 and p[3] else None,
                        "split_flag": len(p) > 4 and p[4].strip().lower() in ("y", "true", "1")})
        except ValueError:
            continue
    return out


def parse_nasdaq_si(payload):
    """Nasdaq's short-interest table -> rows, newest settlement first:
    {"settlement_date","si_shares","adv","days_to_cover"}"""
    rows = (((payload or {}).get("data") or {}).get("shortInterestTable") or {}).get("rows") or []
    out = []
    for r in rows:
        try:
            mm, dd, yyyy = r["settlementDate"].split("/")
            out.append({"settlement_date": f"{yyyy}-{mm}-{dd}",
                        "si_shares": float(str(r["interest"]).replace(",", "")),
                        "adv": float(str(r["avgDailyShareVolume"]).replace(",", "")),
                        "days_to_cover": float(r["daysToCover"])})
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    out.sort(key=lambda r: r["settlement_date"], reverse=True)
    return out


def admitted(reading, as_of):
    """True when the reading was published on or before `as_of` and is not split-flagged"""
    if reading.get("split_flag"):
        return False
    pub = reading.get("publication_date")
    return bool(pub) and pub <= as_of


def si_pct(reading):
    if not reading.get("float_shares"):
        return None
    return reading["si_shares"] / reading["float_shares"] * 100.0


def short_leaf(reading, adv20=None):
    pct = si_pct(reading)
    if pct is None:
        return {"score": None, "si_pct_float": None}
    return {"score": board.lin(pct, 25, 0), "si_pct_float": pct,
            "days_to_cover": (reading["si_shares"] / adv20 if adv20 else None),
            "settlement_date": reading.get("settlement_date"), "publication_date": reading.get("publication_date")}


def pit_path(root):
    return state_path(root, PIT)


def pit_append(root, reading):
    """append a reading to the point-in-time store unless that (symbol, settlement date) is already there; True when
    written. Append-only: a restated reading would be a new line, never an edit."""
    p = pit_path(root)
    key = (reading["symbol"], reading["settlement_date"])
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if (r.get("symbol"), r.get("settlement_date")) == key:
                    return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(reading) + "\n")
    return True


def pit_keys(root):
    """{(symbol, settlement_date)} already stored (read once per run, not per name)"""
    out = set()
    try:
        with open(pit_path(root), encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                out.add((r.get("symbol"), r.get("settlement_date")))
    except OSError:
        pass
    return out
