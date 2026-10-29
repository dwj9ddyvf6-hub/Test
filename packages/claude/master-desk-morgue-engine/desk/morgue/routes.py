"""The data routes' last verdicts (state/morgue/routes.json): which public source answered, which refused, and why. A
refused route is a state of the world the page shows, not a reason to invent a number. Each job records the routes it
touched; the edition lists them (morgue.institutional.routes)."""
import os

from ..util import read_json, write_json_atomic
from . import state_path

PATH = "routes.json"
# probed 2026-10-26 by Silicon's route probe and recorded here as the documented route; a later success replaces it
KNOWN = {
    "FINRA short interest bulk file": ("no_data", "HTTP 403 without credentials (probed 2026-10-26); its query API "
                                                  "answered HTTP 404; the Nasdaq republication is used", "2026-10-26"),
}


def record(root, route, status, reason=None, as_of=None):
    p = state_path(root, PATH)
    doc = read_json(p, {}) or {}
    doc[route] = {"status": status, "reason": reason, "as_of": as_of}
    os.makedirs(os.path.dirname(p), exist_ok=True)
    write_json_atomic(p, doc)


def listing(root):
    """[{"route","status","reason","as_of"}] sorted by route, the documented routes included"""
    doc = dict(read_json(state_path(root, PATH), {}) or {})
    for k, (st, why, day) in KNOWN.items():
        doc.setdefault(k, {"status": st, "reason": why, "as_of": day})
    out = []
    for k in sorted(doc):
        v = doc[k] if isinstance(doc[k], dict) else {}
        row = {"route": k, "status": v.get("status") if v.get("status") in ("ok", "stale", "no_data") else "no_data",
               "as_of": v.get("as_of")}
        if row["status"] != "ok":
            row["reason"] = v.get("reason") or "no verdict recorded"
        out.append(row)
    return out
