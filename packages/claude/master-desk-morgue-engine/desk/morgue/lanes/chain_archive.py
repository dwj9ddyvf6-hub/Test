"""L2, the daily option-chain archive: one gzip file a session and underlying under state/morgue/chains/<UND>/<date>.json.gz,
holding every contract the Map read (open interest, the snapshot's volume, IV and gamma), so tomorrow's reads can compare with
today's: the top open-interest changes (CX-fa-2), the next-day confirmation of an alerted print (B210), an IV history.

Size: about 13,000 SPY contracts, each a row of five numbers and a symbol, is a few hundred KB gzipped a session for the three
funds together. The disk is tight, so the archive rotates by age (KEEP_DAYS = 400 files an underlying).
A stored day is never rewritten (append-only: a second call for the same day returns False)."""
import gzip
import json
import os

from .. import state_path

DIR = "chains"
KEEP_DAYS = 400
COLUMNS = ["occ", "oi", "volume", "iv", "gamma"]


def _dir(root, underlying):
    return state_path(root, os.path.join(DIR, underlying))


def _file(root, underlying, day):
    return os.path.join(_dir(root, underlying), f"{day}.json.gz")


def _r(x, k):
    return None if x is None else round(float(x), k)


def archive_chain(root, underlying, day, rows, spot, oi_date=None, keep=KEEP_DAYS):
    """write the day's chain -> True, or False when that day is already stored. `rows`: opt_ext rows (or the Map's chain rows)
    with "symbol", "oi" and optionally "volume", "iv", "gamma". Rotates after writing."""
    p = _file(root, underlying, day)
    if os.path.exists(p):
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    body = {"underlying": underlying, "day": day, "spot": _r(spot, 4), "oi_date": oi_date, "columns": COLUMNS,
            "rows": [[r["symbol"], r["oi"], r.get("volume"), _r(r.get("iv"), 5), _r(r.get("gamma"), 8)]
                     for r in sorted(rows, key=lambda r: r["symbol"])]}
    tmp = p + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as fh:
        json.dump(body, fh, separators=(",", ":"))
    os.replace(tmp, p)
    rotate(root, underlying, keep)
    return True


def days(root, underlying):
    """the stored dates, ascending"""
    try:
        return sorted(n[:-8] for n in os.listdir(_dir(root, underlying)) if n.endswith(".json.gz"))
    except OSError:
        return []


def read_day(root, underlying, day):
    """{"day","spot","oi_date","contracts": {OCC: {"oi","volume","iv","gamma"}}} or None when the day is not stored or the
    file does not read (a half-written file is no archive)"""
    try:
        with gzip.open(_file(root, underlying, day), "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, EOFError):
        return None
    cols = doc.get("columns") or COLUMNS
    contracts = {r[0]: dict(zip(cols[1:], r[1:])) for r in doc.get("rows") or []}
    return {"day": doc.get("day"), "spot": doc.get("spot"), "oi_date": doc.get("oi_date"), "contracts": contracts}


def previous_day(root, underlying, before):
    """the latest stored date strictly before `before` (point in time), or None"""
    older = [d for d in days(root, underlying) if d < before]
    return older[-1] if older else None


def rotate(root, underlying, keep=KEEP_DAYS):
    """delete the oldest files beyond `keep` -> the dates removed"""
    ds = days(root, underlying)
    gone = ds[:-keep] if keep > 0 and len(ds) > keep else []
    for d in gone:
        try:
            os.remove(_file(root, underlying, d))
        except OSError:
            pass
    return gone


def status(root, underlying):
    """(count, first, last, bytes) of the stored archive"""
    ds = days(root, underlying)
    size = 0
    for d in ds:
        try:
            size += os.path.getsize(_file(root, underlying, d))
        except OSError:
            pass
    return {"days": len(ds), "first_date": ds[0] if ds else None, "last_date": ds[-1] if ds else None, "bytes": size}
