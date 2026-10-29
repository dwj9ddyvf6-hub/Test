"""Transaction-cost analysis from the OMS record (state/oms.json): every child carries the decision reference
price (`ref`) and its fills [ts, vqty, px, source, ref]. Slippage is signed adverse-positive in bps (buys
paying up, sells receiving less). Sources: broker (the venue's own fills), quote_fill (labelled virtual fills
at the live quote — zero or refused replica), internal_cross (two sleeves crossed at the mid)."""
import os
import statistics

from ..util import read_json


def _kind(source):
    s = str(source or "")
    if s.startswith("quote_fill"):
        return "quote_fill"
    if s == "internal_cross":
        return "internal_cross"
    return "broker"


def fills(oms):
    out = []
    for c in (oms.get("children") or {}).values():
        ref = c.get("ref")
        for f in c.get("fills") or ():
            ts, qty, px, source = f[0], f[1], f[2], f[3]
            slip = None
            if ref and px:
                sgn = 1.0 if c.get("side") == "buy" else -1.0
                slip = sgn * (float(px) / float(ref) - 1.0) * 1e4
            out.append({"sleeve": c.get("sleeve"), "inst": c.get("inst"), "asset": c.get("asset"),
                        "venue": c.get("venue"), "side": c.get("side"), "action": c.get("action"),
                        "type": c.get("type"), "ts": ts, "qty": qty, "px": px, "ref": ref, "kind": _kind(source),
                        "slip_bps": slip, "attempts": len(c.get("parents") or []), "child": c.get("id")})
    return out


def _agg(rows):
    sl = [r["slip_bps"] for r in rows if r["slip_bps"] is not None]
    return {"fills": len(rows), "median_slip_bps": round(statistics.median(sl), 2) if sl else None,
            "mean_slip_bps": round(statistics.mean(sl), 2) if sl else None,
            "p90_slip_bps": round(sorted(sl)[int(0.9 * (len(sl) - 1))], 2) if sl else None}


def summary(root, since=None):
    oms = read_json(os.path.join(root, "state", "oms.json"), {}) or {}
    rows = [r for r in fills(oms) if since is None or float(r["ts"] or 0) >= since]
    out = {"all": _agg(rows), "by_kind": {}, "by_asset": {}, "by_sleeve": {}, "first_try": {}}
    for key, field in (("by_kind", "kind"), ("by_asset", "asset"), ("by_sleeve", "sleeve")):
        groups = {}
        for r in rows:
            groups.setdefault(r[field] or "?", []).append(r)
        out[key] = {k: _agg(v) for k, v in sorted(groups.items())}
    # marketable broker children: how often the FIRST parent filled them (the buffer calibration's signal)
    kids = {}
    for c in (oms.get("children") or {}).values():
        if c.get("type", "marketable_limit") != "marketable_limit" or c.get("status") != "filled":
            continue
        if not any(_kind(f[3]) == "broker" for f in c.get("fills") or ()):
            continue
        if since is not None and float(c.get("created") or 0) < since:
            continue
        a = c.get("asset") or "?"
        k = kids.setdefault(a, [0, 0])
        k[0] += 1
        k[1] += 1 if len(c.get("parents") or []) <= 1 else 0
    out["first_try"] = {a: {"filled": n, "first_try": f, "ratio": round(f / n, 4) if n else None}
                        for a, (n, f) in sorted(kids.items())}
    return out
