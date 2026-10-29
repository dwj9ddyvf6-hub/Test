"""The morning worksheet: the day's trade plan written before the open, then frozen.

The market's regime decides which setups are allowed (not direction): Risk-on allows every listed setup at full size;
Mixed allows them at smaller size; Risk-off allows only a pullback whose fear day has come, at smaller size, and every
other setup waits. Every row needs its buy range, stop, target, exit deadline and invalidation line, or it is "No
trade". The sheet names the trade it will not take. It is written to state/ai/worksheets.jsonl before it is shown, and
the first sheet written for a session is the one shown all day (a later edition never rewrites it).
"""
import hashlib
import json
import os

from desk.terminal import prices

from . import gates

KEYS = ("as_of", "regime", "allowed", "rows", "not_taking", "frozen", "hash")
ROW_KEYS = ("symbol", "verdict", "size", "close", "zone_lo", "zone_hi", "trigger", "out", "t1", "t2", "by",
            "invalidation", "reason")
ALLOWED = {"Risk-on": "Every listed setup, full size.",
           "Mixed": "Listed setups at smaller size.",
           "Risk-off": "Only a pullback whose fear day has come, at smaller size; everything else waits."}


def _row(s, regime):
    p = s.get("plan") or {}
    close = s.get("close")
    base = {"symbol": s.get("symbol"), "close": close, "zone_lo": p.get("zone_lo"), "zone_hi": p.get("zone_hi"),
            "trigger": p.get("trigger"), "out": p.get("out"), "t1": p.get("t1"), "t2": p.get("t2"),
            "by": p.get("window") or p.get("by"),
            "invalidation": ("Out on a daily close below the stop" + (f" ({p['why_out']})" if p.get("why_out") else "")
                             + ".") if p.get("out") is not None else None}

    def no(reason):
        return dict(base, verdict="No trade", size="No trade", reason=reason)
    if s.get("action") != "Buy":
        return no("the read does not say buy")
    need = [k for k, v in (("buy range", p.get("zone_hi") if p.get("trigger") is None else p.get("trigger")),
                           ("stop", p.get("out")), ("target", p.get("t1")), ("exit deadline", base["by"]),
                           ("close", close)) if v is None]
    if need:
        return no("missing " + ", ".join(need))
    role = prices.ROLE
    entry = prices.px(close, p["trigger"] if p.get("trigger") is not None else p["zone_hi"],
                      role["trigger"] if p.get("trigger") is not None else role["zone_hi"])
    intent = {"side": "long", "entry": entry, "stop": prices.px(close, p["out"], role["out"]),
              "t1": prices.px(close, p["t1"], role["t1"]),
              "t2": prices.px(close, p["t2"], role["t2"]) if p.get("t2") is not None else None,
              "zone_lo": prices.px(close, p["zone_lo"], role["zone_lo"]) if p.get("zone_lo") is not None else None,
              "zone_hi": prices.px(close, p["zone_hi"], role["zone_hi"]) if p.get("zone_hi") is not None else None,
              "last": close * (1 + (s.get("now_pct") or 0) / 100), "earnings_in_hold": bool(s.get("earnings"))}
    if p.get("trigger") is not None:
        intent.pop("zone_lo"), intent.pop("zone_hi")
    c = gates.consistency_gate(intent)
    if not c["ok"]:
        return no("; ".join(c["reasons"]))
    fear = (s.get("fear") or {}).get("state")
    if regime == "Risk-off":
        if fear == "came" and p.get("mode") in ("level", "reaction"):
            return dict(base, verdict="Buy", size="Smaller", reason="Risk-off, but its fear day has come")
        return dict(base, verdict="Watch", size="Watch only",
                    reason="Risk-off: waits for its fear day" if fear == "waiting" else "Risk-off: not a fear-day pullback")
    if regime == "Mixed":
        return dict(base, verdict="Buy", size="Smaller", reason="mixed market")
    if regime == "Risk-on":
        return dict(base, verdict="Buy", size="Full size", reason="risk-on market")
    return no("no market read")


def build(edition):
    mk = (edition or {}).get("market") or {}
    regime = (mk.get("badge") or {}).get("word")
    rows = [_row(s, regime) for s in (edition or {}).get("setups") or []]
    skip = next((r for r in rows if r["verdict"] != "Buy"), None)
    not_taking = (f"{skip['symbol']}: {skip['reason']}." if skip else "Anything above its buy range: no chasing.")
    out = {"as_of": mk.get("as_of"), "regime": regime or "Unknown",
           "allowed": ALLOWED.get(regime, "No market read: no trade."), "rows": rows, "not_taking": not_taking,
           "frozen": None}
    out["hash"] = hashlib.sha256(json.dumps({k: out[k] for k in ("as_of", "regime", "rows")}, sort_keys=True)
                                 .encode()).hexdigest()[:16]
    return out


def log_path(root):
    return os.path.join(os.environ.get("DESK_AI_DIR") or os.path.join(root, "state", "ai"), "worksheets.jsonl")


def freeze(root, sheet, at_iso):
    """log before show: the session's first sheet is appended and returned; a later call for the same session
    returns that first sheet unchanged"""
    path = log_path(root)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    old = json.loads(line)
                except ValueError:
                    continue
                if old.get("as_of") == sheet.get("as_of") and sheet.get("as_of"):
                    first = old
                    break
            else:
                first = None
        if first:
            return first
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rec = dict(sheet, frozen=at_iso)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return rec


def edition_block(root, edition, at_iso):
    """the edition's `brief`: the frozen sheet, in the public contract's keys"""
    rec = freeze(root, build(edition), at_iso)
    return {k: ([{rk: r.get(rk) for rk in ROW_KEYS} for r in rec["rows"]] if k == "rows" else rec.get(k))
            for k in KEYS}
