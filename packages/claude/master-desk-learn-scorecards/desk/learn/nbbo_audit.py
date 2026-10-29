"""The sim's equity fills re-priced against the consolidated NBBO at each fill instant (the research brief's item 12:
the fill model's own bias, measured; broker paper is only another simulator).

For every equity fill at the sim venue at least DELAY_S old (the free plan serves SIP data older than 15 minutes):
the last SIP quote at or before the fill (Alpaca historical quotes, feed=sip, one request per distinct fill, cached in
state/nbbo_audit.json). Per fill, side-signed so that positive means the sim charged more than the market did:
  vs_touch_bps  buys (px - NBO) / mid, sells (NBB - px) / mid  (0 = filled at the real touch)
  paid_bps      buys (px - mid) / mid, sells (mid - px) / mid  (the half-spread the fill paid)
  nbbo_half_bps the NBBO's own half-spread then
Summaries by symbol and overall: the evidence the calibration reads (desk/learn/calibrate.py); nothing is changed by
it."""
import os
import statistics
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

DELAY_S = 17 * 60
PATH = os.path.join("state", "nbbo_audit.json")
KEEP_S = 10 * 86400


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _epoch(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def equity_fills(oms, since, until):
    """[(key, sym, side, ts, px)] of the distinct equity fills in [since, until] (children of one parent share it)."""
    out = {}
    for c in (oms.get("children") or {}).values():
        inst = str(c.get("inst") or "")
        if not inst.startswith("EQ:") or str(c.get("venue") or "") not in ("alpaca", "sim:alpaca_sim", "sim:alpaca_equity"):
            continue
        for f in c.get("fills") or ():
            ts, px = float(f[0]), float(f[2] or 0)
            if px > 0 and since <= ts <= until and not str(f[3] or "").startswith("internal_cross"):
                key = "%s|%s|%.3f|%.6f" % (inst[3:], c.get("side"), ts, px)
                out[key] = (key, inst[3:], c.get("side"), ts, px)
    return sorted(out.values(), key=lambda r: r[3])


def nbbo_at(client, sym, ts):
    """(bid, ask) of the last SIP quote at or before ts within the minute before it, or None."""
    from ..venues.alpaca import DATA
    r = client._get("/v2/stocks/quotes", {"symbols": sym, "start": _iso(ts - 60), "end": _iso(ts), "feed": "sip",
                                         "limit": 1000}, host=DATA) or {}
    qs = [q for q in (r.get("quotes") or {}).get(sym) or [] if (q.get("bp") or 0) > 0 and (q.get("ap") or 0) >= q["bp"]]
    if not qs:
        return None
    q = max(qs, key=lambda q: _epoch(q["t"]))
    return float(q["bp"]), float(q["ap"])


def audit(root, client, now, since=None, max_requests=400):
    st = read_json(os.path.join(root, PATH), {}) or {}
    rows = st.setdefault("fills", {})
    oms = read_json(os.path.join(root, "state", "oms.json"), {}) or {}
    since = since if since is not None else now - KEEP_S
    n = 0
    for key, sym, side, ts, px in equity_fills(oms, since, now - DELAY_S):
        if key in rows:
            continue
        if n >= max_requests:
            break
        n += 1
        try:
            q = nbbo_at(client, sym, ts)
        except Exception as e:
            rows[key] = {"sym": sym, "ts": ts, "error": type(e).__name__}
            continue
        if q is None:
            rows[key] = {"sym": sym, "ts": ts, "error": "no_quote"}
            continue
        bid, ask = q
        mid = (bid + ask) / 2.0
        sgn = 1.0 if side == "buy" else -1.0
        touch = ask if side == "buy" else bid
        rows[key] = {"sym": sym, "side": side, "ts": ts, "px": px, "bid": bid, "ask": ask,
                     "vs_touch_bps": round(sgn * (px - touch) / mid * 1e4, 3),
                     "paid_bps": round(sgn * (px - mid) / mid * 1e4, 3),
                     "nbbo_half_bps": round((ask - bid) / mid / 2 * 1e4, 3)}
    for k in [k for k, v in rows.items() if now - float(v.get("ts") or 0) > KEEP_S]:
        rows.pop(k)
    st["summary"] = summarize(rows)
    st["at"] = now
    write_json_atomic(os.path.join(root, PATH), st)
    return dict(st["summary"], requests=n)


def _agg(vals):
    vals = sorted(vals)
    if not vals:
        return None
    return {"n": len(vals), "median": round(statistics.median(vals), 2), "mean": round(statistics.mean(vals), 2),
            "p10": round(vals[int(0.1 * (len(vals) - 1))], 2), "p90": round(vals[int(0.9 * (len(vals) - 1))], 2)}


def summarize(rows):
    ok = [r for r in rows.values() if "vs_touch_bps" in r]
    by = {}
    for r in ok:
        by.setdefault(r["sym"], []).append(r)
    return {"fills": len(ok), "errors": sum(1 for r in rows.values() if "error" in r),
            "vs_touch_bps": _agg([r["vs_touch_bps"] for r in ok]), "paid_bps": _agg([r["paid_bps"] for r in ok]),
            "nbbo_half_bps": _agg([r["nbbo_half_bps"] for r in ok]),
            "optimistic_share": round(sum(1 for r in ok if r["vs_touch_bps"] < -0.01) / len(ok), 3) if ok else None,
            "by_symbol": {s: {"n": len(v), "vs_touch_bps": round(statistics.median([x["vs_touch_bps"] for x in v]), 2)}
                          for s, v in sorted(by.items())}}
