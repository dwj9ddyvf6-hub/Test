"""Code, not prompt: the gates every desk-AI answer and order intent passes (study I, sections 3.3 and 3.7).

ground()            every number in an answer must trace to a tool output this session, or its sentence is cut;
                    a cut inside the price map turns the whole answer into "No trade — data gap"
consistency_gate()  one direction, ordered levels, not already past T1, reward to risk at the minimum, no earnings
                    in the hold, every field present
risk_gate()         kill switch first (blocks everything), stop required, risk per trade, position size, total open
                    risk, sector crowding; a limits file may only tighten the ceilings; never places an order
"""
import json
import os
import re

CEILINGS = {"risk_pct": 1.0, "max_position_pct": 20.0, "max_open_risk_pct": 5.0, "max_sector_names": 2,
            "min_rr": 1.0}
PRICE_MAP = re.compile(r"^\s*(buy|stop|target|t1|t2|entry|out)\b", re.I)
# a number as written: optional sign/$, digits with commas, decimals, optional % or x
NUM = re.compile(r"(?<![\w.])([-+−]?\$?\d[\d,]*(?:\.\d+)?)(%|x\b)?")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T[\d:+\-]+)?\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
                  r"\s+\d{1,2}(?:,\s*\d{4})?\b|\b\d{1,2}:\d{2}\b")
LABELS = re.compile(r"\b(?:T[12]|C8|[A-Z]{1,5}\d?)\b")    # T1, T2, C8 and tickers carry digits that are not figures


def limits(path=None):
    """the ceilings, tightened (never loosened) by an optional limits file (state/ai/limits.json)"""
    out = dict(CEILINGS)
    p = path or os.path.join(os.environ.get("DESK_AI_DIR") or os.path.join(os.getcwd(), "state", "ai"),
                             "limits.json")
    try:
        with open(p) as f:
            extra = json.load(f)
    except (OSError, ValueError):
        return out
    for k, v in (extra or {}).items():
        if k in out and isinstance(v, (int, float)):
            out[k] = max(out[k], v) if k == "min_rr" else min(out[k], v)
    return out


def _num(tok):
    t = tok.replace("−", "-").replace("$", "").replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def _decimals(tok):
    t = tok.replace(",", "")
    return len(t.split(".", 1)[1]) if "." in t else 0


def _leaves(x, out):
    if isinstance(x, bool):
        return
    if isinstance(x, (int, float)):
        out.append(float(x))
        if 0 < abs(x) <= 1:
            out.append(float(x) * 100)        # a rate tools hold as 0.714 is written 71.4%
    elif isinstance(x, str):
        for m in NUM.finditer(DATE.sub(" ", x)):
            v = _num(m.group(1))
            if v is not None:
                out.append(v)
    elif isinstance(x, dict):
        for v in x.values():
            _leaves(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _leaves(v, out)


def _grounded(v, dec, pool):
    tol = max(0.5 * 10 ** (-dec), 1e-9)
    return any(abs(v - p) <= tol + 1e-9 or abs(abs(v) - abs(p)) <= tol + 1e-9 for p in pool)


def ground(text, outputs):
    """-> {text, cut: [{sentence, numbers}], kept, figures, cut_rate, no_trade}. outputs: the session's tool envelopes
    (or bare results). A figure counts as grounded when some tool output holds it within the figure's own rounding
    (82.07 matches 82.0712; 71% matches 0.714). Dates, clock times and labels (T1, C8, tickers) are not figures."""
    pool = []
    for o in outputs:
        _leaves(o.get("result") if isinstance(o, dict) and "result" in o else o, pool)
    lines, cut, figures, kept = text.splitlines(), [], 0, []
    no_trade = False
    for line in lines:
        parts = re.split(r"(?<=[.!?])\s+", line) if line.strip() else [line]
        keep_parts = []
        for s in parts:
            scan = LABELS.sub(" ", DATE.sub(" ", s))
            bad = []
            for m in NUM.finditer(scan):
                v = _num(m.group(1))
                if v is None:
                    continue
                figures += 1
                if not _grounded(v, _decimals(m.group(1).replace("$", "")), pool):
                    bad.append(m.group(0))
            if bad:
                cut.append({"sentence": s.strip(), "numbers": bad})
                if PRICE_MAP.match(s):
                    no_trade = True
            else:
                keep_parts.append(s)
        if keep_parts and any(p.strip() for p in keep_parts):
            kept.append(" ".join(keep_parts))
        elif not line.strip():
            kept.append(line)
    out = "\n".join(kept).strip()
    if no_trade:
        out = "No trade — data gap: a price in the plan does not trace to a desk tool."
    return {"text": out, "cut": cut, "figures": figures, "cut_rate": round(len(cut) and
            sum(len(c["numbers"]) for c in cut) / max(figures, 1), 4), "no_trade": no_trade}


def _check(key, ok, label):
    return {"key": key, "ok": bool(ok), "label": label}


def consistency_gate(intent):
    """a long plan's numbers must agree with each other before anyone sees them"""
    side = intent.get("side", "long")
    req = ("entry", "stop", "t1")
    missing = [k for k in req if not isinstance(intent.get(k), (int, float))]
    checks = [_check("fields", not missing, "every field present" if not missing else "missing: " + ", ".join(missing))]
    if missing:
        return {"ok": False, "checks": checks, "reasons": [checks[0]["label"]]}
    e, s, t1, t2 = intent["entry"], intent["stop"], intent["t1"], intent.get("t2")
    lim = limits()
    checks.append(_check("direction", side == "long", "one direction: long" if side == "long"
                         else "only long plans are carried"))
    checks.append(_check("order", s < e < t1 and (t2 is None or t1 < t2), "stop below entry below target"
                         + (" below the second target" if t2 is not None else "")))
    lo, hi = intent.get("zone_lo"), intent.get("zone_hi")
    if lo is not None and hi is not None:
        checks.append(_check("zone", s < lo <= hi < t1, "buy range sits between the stop and the target"))
    last = intent.get("last")
    if isinstance(last, (int, float)):
        checks.append(_check("not_past_t1", last < t1, "price has not already reached the target"))
    rr = (t1 - e) / (e - s) if e > s else 0
    checks.append(_check("rr", rr >= lim["min_rr"], f"reward to risk at least {lim['min_rr']:g}"))
    checks.append(_check("earnings", not intent.get("earnings_in_hold"), "no earnings report inside the hold"))
    bad = [c["label"] for c in checks if not c["ok"]]
    return {"ok": not bad, "checks": checks, "reasons": bad, "rr": round(rr, 2)}


def killed(root=None):
    if os.environ.get("DESK_AI_KILL") == "1":
        return True
    d = os.environ.get("DESK_AI_DIR") or os.path.join(root or os.getcwd(), "state", "ai")
    return os.path.exists(os.path.join(d, "KILL"))


def risk_gate(intent, root=None):
    """ordered checks with a structured verdict; the kill switch blocks every intent, exits included; exits skip the
    exposure checks; the verdict is a proposal state, never an order"""
    lim = limits()
    checks = [_check("kill_switch", not killed(root), "kill switch off")]
    if not checks[0]["ok"]:
        return {"ok": False, "state": "blocked", "checks": checks, "reasons": ["kill switch on"], "limits": lim}
    exit_ = intent.get("action") == "exit"
    if not exit_:
        eq = float(intent.get("equity") or 0)
        rd = intent.get("risk_dollars")
        if intent.get("today") is not None:
            checks.append(_check("sheet", intent["today"] == "Buy", "the morning sheet allows a buy today"
                                 if intent["today"] == "Buy" else f"the morning sheet says {intent['today']} today"))
        checks.append(_check("stop", isinstance(intent.get("stop"), (int, float)), "a stop is set"))
        checks.append(_check("size", (intent.get("shares") or 0) > 0, "size above zero"))
        rp = 100 * rd / eq if eq and rd is not None else None
        checks.append(_check("risk_per_trade", rp is not None and rp <= lim["risk_pct"] + 1e-9,
                             f"risk per trade at most {lim['risk_pct']:g}% of equity"))
        pp = 100 * (intent.get("notional") or 0) / eq if eq else None
        checks.append(_check("position", pp is not None and pp <= lim["max_position_pct"] + 1e-9,
                             f"position at most {lim['max_position_pct']:g}% of equity"))
        tot = float(intent.get("open_risk_pct") or 0) + (rp or 0)
        checks.append(_check("open_risk", tot <= lim["max_open_risk_pct"] + 1e-9,
                             f"total open risk at most {lim['max_open_risk_pct']:g}% of equity"))
        checks.append(_check("sector", (intent.get("sector_names_held") or 0) < lim["max_sector_names"],
                             f"fewer than {lim['max_sector_names']} names already held in the same sector fund"))
    bad = [c["label"] for c in checks if not c["ok"]]
    return {"ok": not bad, "state": "proposed — awaits owner approval" if not bad else "rejected",
            "checks": checks, "reasons": bad, "limits": lim}
