"""Flow reads over the Tape's signed prints and the chain's open interest (REA work package 3). Pure functions: no I/O, no
network. tape_card.build_card hands them the day's prints; cycle writes their blocks to state/morgue/flow.json, which the
edition shows as `morgue.flow`.

A signed print (signed_print) is the Tape's own scoring of one print: contract, time, size, premium, the side against the latest
quote, the direction sign (ask +1, bid -1, flipped for puts: bullish positive), the sweep and multi-leg flags and the Tape's
tags. Multi-leg prints count in volume and never in a net or a ratio (the Tape's rule); cancelled prints never get here.

  net_drift        net call / put premium and volume per time bucket, NOT a running total (Quant Data A57)
  repeat_sweeps    the same contract swept 3+ times inside 10 minutes, tiered Rapid Fire / Swift / Steady (BlackBoxStocks A42)
  premium_ratio    bullish / bearish premium per name, for a named roster only (Quant Data A58)
  flow_ratio       call premium / put premium over the Unusual-tagged prints (GEXRadar A92)
  hiro             sign x delta x size x 100 x spot per print, bucketed, cumulative and rolling (SpotGamma HIRO, CX-sg-6)
  oi_change_top    the contracts whose open interest moved most since the last archived day (FlowAlgo CX-fa-2)
  oi_confirm       what the next session's open interest says of an alerted print: opened, closed, unchanged (Skylit B210)"""
import re
from datetime import datetime, timezone

from . import tape

SOURCE = "Alpaca option trades and chain snapshots"
DELAY = "the session's prints to the run; open interest posts the next morning"
BUCKET_MIN = 5
SWEEP_WINDOW_MIN = 10
SWEEP_MIN_COUNT = 3
# tiers by how fast the burst came (the desk's edges for the vendor's three names, which publish none)
SWEEP_TIERS = ((2.0, "Rapid Fire"), (5.0, "Swift"), (10.0, "Steady"))
HIRO_FUNDS = ("SPY", "QQQ", "IWM")
ROLLING_MIN = 30
OI_TOP_N = 20
CONFIRM_FRACTION = 0.5
_FRAC = re.compile(r"(\.\d{1,6})\d*")


def epoch(ts):
    """an RFC 3339 time as epoch seconds (nanosecond fractions trimmed), or None"""
    try:
        s = _FRAC.sub(r"\1", str(ts)).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()
    except (ValueError, TypeError):
        return None


def signed_print(r, c, spot, quote, today):
    """one raw trade {"t","p","s","c"} of contract c ({"symbol","strike","expiry","is_call","oi"}) -> the signed print dict,
    or None for a cancel or a print that does not parse (the Tape's own filters)"""
    from datetime import date
    cond = r.get("c")
    if tape.is_cancel(cond):
        return None
    try:
        price, size = float(r["p"]), int(r["s"])
    except (KeyError, TypeError, ValueError):
        return None
    t = epoch(r.get("t"))
    if not (price > 0 and size > 0) or t is None:
        return None
    dte = (date.fromisoformat(c["expiry"]) - today).days
    otm = (max(0.0, (c["strike"] - spot) / spot * 100.0) if c["is_call"]
           else max(0.0, (spot - c["strike"]) / spot * 100.0))
    premium = price * size * 100.0
    side = tape.classify_side(price, (quote or {}).get("bid"), (quote or {}).get("ask"))
    tg = tape.tags({"premium": premium, "dte": dte, "sweep": tape.is_sweep(cond), "size": size, "otm_pct": otm,
                    "oi": c.get("oi")})
    return {"t": t, "contract": c["symbol"], "is_call": c["is_call"], "strike": c["strike"], "expiry": c["expiry"],
            "size": size, "premium": premium, "side": side, "raw_side": (1 if side in tape.ASK_SIDES else
                                                                          -1 if side in tape.BID_SIDES else 0),
            "sign": tape.directional_sign(side, c["is_call"]), "sweep": tape.is_sweep(cond),
            "multileg": tape.is_multileg(cond), "unusual": tg["unusual"]}


def _bucket(t, minutes):
    return int(t // (minutes * 60)) * minutes * 60


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- A57 ----------------------------------------------------------------------------------------------------------------

def net_drift(prints, bucket_min=BUCKET_MIN):
    """[{"t","call_net_premium_usd","put_net_premium_usd","net_premium_usd","call_net_volume","put_net_volume","prints"}]
    ascending by bucket start: per bucket, the sum of sign x premium (and sign x size) of the single-leg prints, calls and
    puts apart. Each bucket stands alone (not cumulated); a bucket with only multi-leg prints shows zeros and its count."""
    out = {}
    for p in prints:
        b = out.setdefault(_bucket(p["t"], bucket_min), {"call_p": 0.0, "put_p": 0.0, "call_v": 0, "put_v": 0, "n": 0})
        b["n"] += 1
        if p["multileg"]:
            continue
        k = "call" if p["is_call"] else "put"
        b[k + "_p"] += p["sign"] * p["premium"]
        b[k + "_v"] += p["sign"] * p["size"]
    return [{"t": _iso(t), "call_net_premium_usd": round(b["call_p"], 2), "put_net_premium_usd": round(b["put_p"], 2),
             "net_premium_usd": round(b["call_p"] + b["put_p"], 2), "call_net_volume": b["call_v"],
             "put_net_volume": b["put_v"], "prints": b["n"]} for t, b in sorted(out.items())]


# ---- A42 ----------------------------------------------------------------------------------------------------------------

def repeat_sweeps(prints, window_min=SWEEP_WINDOW_MIN, min_count=SWEEP_MIN_COUNT):
    """per contract, the densest run of sweep prints that fits one `window_min`-minute window (the window's edge inclusive),
    reported when it holds at least `min_count` sweeps: {"contract","kind","count","premium_usd","span_min","tier",
    "first","last"}, the larger premium first. Tier by the run's own span: Rapid Fire <= 2 min, Swift <= 5, Steady <= 10."""
    by = {}
    for p in prints:
        if p["sweep"]:
            by.setdefault(p["contract"], []).append(p)
    out, w = [], window_min * 60.0
    for sym, ps in by.items():
        ps.sort(key=lambda p: p["t"])
        best = None
        j = 0
        for i in range(len(ps)):
            while ps[i]["t"] - ps[j]["t"] > w:
                j += 1
            n = i - j + 1
            span = ps[i]["t"] - ps[j]["t"]
            if best is None or n > best[0] or (n == best[0] and span < best[1]):
                best = (n, span, j, i)
        if best is None or best[0] < min_count:
            continue
        n, span, j, i = best
        run = ps[j:i + 1]
        span_min = span / 60.0
        tier = next((name for edge, name in SWEEP_TIERS if span_min <= edge), SWEEP_TIERS[-1][1])
        out.append({"contract": sym, "kind": "call" if run[0]["is_call"] else "put", "count": n,
                    "premium_usd": round(sum(p["premium"] for p in run), 2), "span_min": round(span_min, 2),
                    "tier": tier, "first": _iso(run[0]["t"]), "last": _iso(run[-1]["t"])})
    return sorted(out, key=lambda a: -a["premium_usd"])


# ---- A58, A92 -------------------------------------------------------------------------------------------------------------

def premium_ratio(by_name, allowed=None):
    """{"names": {name: {"bullish_usd","bearish_usd","ratio","prints"}}, "ignored": n}: bullish premium (sign > 0) over bearish
    (sign < 0), single-leg prints. Only the names in `allowed` (the board and the watching names, never the universe) are
    read; a name with no bearish premium has ratio None with the reason on its row."""
    names, ignored = {}, 0
    for name, ps in by_name.items():
        if allowed is not None and name not in allowed:
            ignored += 1
            continue
        bull = sum(p["premium"] for p in ps if not p["multileg"] and p["sign"] > 0)
        bear = sum(p["premium"] for p in ps if not p["multileg"] and p["sign"] < 0)
        row = {"bullish_usd": round(bull, 2), "bearish_usd": round(bear, 2), "prints": len(ps),
               "ratio": (round(bull / bear, 3) if bear > 0 else None)}
        if bear <= 0:
            row["reason"] = "no bearish premium to divide by" if bull > 0 else "no signed premium"
        names[name] = row
    return {"names": names, "ignored": ignored}


def flow_ratio(prints):
    """call premium / put premium over the prints the Tape tagged Unusual (cancels already out; multi-leg prints excluded as
    elsewhere) -> {"call_premium_usd","put_premium_usd","ratio","unusual_prints"}; ratio None with a reason without put premium"""
    u = [p for p in prints if p["unusual"] and not p["multileg"]]
    c = sum(p["premium"] for p in u if p["is_call"])
    q = sum(p["premium"] for p in u if not p["is_call"])
    out = {"call_premium_usd": round(c, 2), "put_premium_usd": round(q, 2), "unusual_prints": len(u),
           "ratio": (round(c / q, 3) if q > 0 else None)}
    if q <= 0:
        out["reason"] = "no unusual put premium to divide by" if c > 0 else "no unusual print"
    return out


# ---- CX-sg-6 --------------------------------------------------------------------------------------------------------------

def hiro(prints, deltas, spot, underlying, bucket_min=BUCKET_MIN, rolling_min=ROLLING_MIN):
    """The hedging impact of the day's trades: each single-leg print adds side x delta x size x 100 x spot (side +1 ask, -1
    bid, as the customer traded; the put's negative delta flips the sign of a bought put). `deltas` {OCC: delta}. Series per
    bucket: total, call, put, next-expiry (the earliest expiry in the prints), the running total, and the sum of the last
    `rolling_min` minutes. SPY, QQQ and IWM only. -> {"status","reason","series","skipped_no_delta"}; the retail-only and
    hedged-flow filters of the vendor are proprietary and not built."""
    if underlying not in HIRO_FUNDS:
        return {"status": "no_data", "reason": "HIRO is read for SPY, QQQ and IWM only", "series": []}
    use, skipped = [], 0
    for p in prints:
        if p["multileg"] or p["raw_side"] == 0:
            continue
        d = deltas.get(p["contract"])
        if d is None:
            skipped += 1
            continue
        use.append((p, p["raw_side"] * d * p["size"] * 100.0 * spot))
    if not use:
        return {"status": "no_data", "reason": "no signed print with a delta", "series": [], "skipped_no_delta": skipped}
    nxt = min(p["expiry"] for p, _ in use)
    rows = {}
    for p, v in use:
        b = rows.setdefault(_bucket(p["t"], bucket_min), {"total": 0.0, "call": 0.0, "put": 0.0, "next": 0.0})
        b["total"] += v
        b["call" if p["is_call"] else "put"] += v
        if p["expiry"] == nxt:
            b["next"] += v
    series, run, win = [], 0.0, []
    for t, b in sorted(rows.items()):
        run += b["total"]
        win.append((t, b["total"]))
        win = [(u, x) for u, x in win if u > t - rolling_min * 60]
        series.append({"t": _iso(t), "total": round(b["total"], 2), "call": round(b["call"], 2),
                       "put": round(b["put"], 2), "next_expiry": round(b["next"], 2), "cumulative": round(run, 2),
                       "rolling": round(sum(x for _, x in win), 2)})
    return {"status": "ok", "series": series, "next_expiry": nxt, "skipped_no_delta": skipped,
            "bucket_min": bucket_min, "rolling_min": rolling_min}


# ---- CX-fa-2, B210 ----------------------------------------------------------------------------------------------------------

def _oi_map(chain):
    """{OCC: oi} from a list of chain rows or an already-built mapping"""
    if isinstance(chain, dict):
        return {k: float(v) for k, v in chain.items()}
    return {c["symbol"]: float(c["oi"]) for c in chain}


def oi_change_top(chain_today, chain_prev, n=OI_TOP_N, meta=None):
    """the n contracts with the largest absolute change in open interest between two archived days: [{"contract","kind",
    "strike","expiry","oi","oi_prev","change","new"}]; a contract absent from the earlier day is new (oi_prev 0, flagged); a
    contract absent today (expired) is not listed. `meta` {OCC: row} supplies kind/strike/expiry (default: the rows of
    chain_today when it is a list)."""
    today, prev = _oi_map(chain_today), _oi_map(chain_prev)
    if meta is None and not isinstance(chain_today, dict):
        meta = {c["symbol"]: c for c in chain_today}
    meta = meta or {}
    rows = []
    for sym, oi in today.items():
        was = prev.get(sym)
        change = oi - (was or 0.0)
        if change == 0:
            continue
        m = meta.get(sym) or {}
        rows.append({"contract": sym, "kind": ("call" if m["is_call"] else "put") if "is_call" in m else None,
                     "strike": m.get("strike"), "expiry": m.get("expiry"), "oi": oi, "oi_prev": was or 0.0,
                     "change": change, "new": was is None})
    rows.sort(key=lambda r: (-abs(r["change"]), r["contract"]))
    return rows[:n]


def oi_confirm(alerts, oi_at_alert, oi_next, fraction=CONFIRM_FRACTION):
    """each alerted contract against the next session's open interest: opened when OI rose by at least `fraction` of the print's
    size, closed when it fell by that much, unchanged between, unknown when either day lacks the contract. `alerts` carry
    "contract" and "size"; the OI maps are {OCC: oi}. -> {"counts", "rows"}. A rise of half the print is the vendor's bar;
    other flow trades the same contract that day, so this is evidence for the label, not a proof of one print."""
    rows = []
    counts = {"opened": 0, "closed": 0, "unchanged": 0, "unknown": 0}
    for a in alerts:
        sym, size = a.get("contract"), a.get("size") or 0
        before, after = oi_at_alert.get(sym), oi_next.get(sym)
        if before is None or after is None or size <= 0:
            kind, delta = "unknown", None
        else:
            delta = after - before
            kind = ("opened" if delta >= fraction * size else "closed" if delta <= -fraction * size else "unchanged")
        counts[kind] += 1
        rows.append({"contract": sym, "size": size, "oi_alert_day": before, "oi_next_day": after, "change": delta,
                     "result": kind})
    return {"counts": counts, "rows": rows}
