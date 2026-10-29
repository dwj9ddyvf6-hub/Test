"""The promoted book: the cells a router may act on, with their evidence (FACTORY.md §5, §6).

An entry is one forecaster x target x context cell that replicated on the second dataset (grade A,
desk/forecast/replicate.py), with its cards (cards.py) from every window the cell was scored on:
  {id, fid, target, cell, sign, binary, h, direction (up | down), grade, status (promoted | probation | demoted),
   dims {dim: value}, windows [card]}
A cell's direction is `down` for a flag with sign -1 (an avoid: the names it flags under-perform) and `up` otherwise
(the application set is the names the forecaster likes). Only status `promoted` entries are acted on; `probation`
(the forward record is thin or a CUSUM warning is open) and `demoted` are shown, never routed.

build()  entries from a replicate.compare() result and cards per cell; the file is pinned by sha256 (freeze.py), so a
         router never runs on a moved book. load() refuses bytes that do not match the pin."""
from . import cards as CD
from . import freeze as FZ

GRADE_ROUTES = ("A",)
ACTED = ("promoted",)
BOOK = "promoted-book-1"


def cell_id(fid, target, cell):
    return f"{fid}|{target}|{cell}"


def direction(sign, binary):
    return "down" if binary and sign < 0 else "up"


def _round(w, series):
    out = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in w.items() if k not in ("dates", "gross")}
    if series:
        out["dates"] = list(w["dates"])
        out["gross"] = [round(float(x), 6) for x in w["gross"]]
    return out


def entry(fid, target, cell, sign, binary, h, windows, grade="A", status="promoted"):
    """series are kept for the cells a router may act on (status promoted); a probation or demoted entry keeps its
    counts and rates only, since it is shown and never routed"""
    series = status == "promoted"
    return {"id": cell_id(fid, target, cell), "fid": fid, "target": target, "cell": cell, "sign": int(sign),
            "binary": bool(binary), "h": int(h), "direction": direction(sign, binary), "grade": grade,
            "status": status, "dims": CD.context_of(cell).dims,
            "windows": [_round(w, series) for w in windows if w.get("status") == "ok"]}


def build(entries, name=BOOK, root=FZ.HERE):
    """-> (payload, sha256); the payload is written once under root/<name>.json (an existing file with other bytes is
    refused by freeze.freeze)"""
    payload = {"version": name, "entries": sorted(entries, key=lambda e: e["id"])}
    return payload, FZ.freeze(name, payload, root=root)


def load(name=BOOK, pin=None, root=FZ.HERE):
    return FZ.load(name, pin=pin or FZ.PINS.get(name), root=root)


def by_id(book):
    return {e["id"]: e for e in book["entries"]}


def with_overlay(book, rows):
    """the book with each entry's status replaced by its latest row in an append-only status log
    ([{id, status, as_of, why}]); the pinned file is never edited, a demotion is a row"""
    last = {}
    for r in rows:
        last[r["id"]] = r
    entries = [dict(e, status=last[e["id"]]["status"]) if e["id"] in last else e for e in book["entries"]]
    return dict(book, entries=entries)
