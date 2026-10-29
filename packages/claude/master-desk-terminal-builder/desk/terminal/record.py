"""The public record, in the form a reader can audit: every read call one row, losers included, graded twice.

SCOPE (S4, 2026-10-26, PLAN.md Phase 3)
  Surface: this module, its edition block `record` and the per-row `record_line` (desk/terminal/__init__.py), the
    Record tab's own file (web/terminal/record.js), state/terminal/record.json (the grades, written once each),
    state/terminal/record_corrections.jsonl (corrections, appended) and state/terminal/incubation.json (frozen hashes).
  Constraints: calls.json is never written here; a call's plan outcome stays calls.py's. No prices published.
  Outcome: one row per call (exit code, targets hit, R, give-back from its peak, 1d/5d/21d grades), losers kept, a
    break-even band kept out of the hit rate, exclusions counted with reasons, months, per-type lines, a seeded random
    baseline, and each setup type's incubation state.
  Proof: tests/test_terminal_record.py (fail-first fixtures); the edition validates.
  Edges: a grade needs the bars of its session; until then it reads "not yet graded" with its date, never a guess.

Rules
  - Plan outcome: calls.py's, as published (R in the plan's own risk unit).
  - Won / lost / even: R above +EVEN_R won, below -EVEN_R lost, between them even; the hit rate is won / (won + lost).
  - Fixed horizons: the close HORIZONS sessions after the read's session, over the read's own close, close to close,
    split-adjusted (calls.split_factor). Never a high inside the window. Written once (state/terminal/record.json) and
    never rewritten: a correction is a new row in record_corrections.jsonl, published beside the row.
  - Give-back: a closed call's best close-to-high R while held (its peak) minus its result, in R.
  - Exclusions: a buy that expired, was missed or voided is not a result; each is counted with its reason.
  - Small samples: under SMALL_N closed calls the figures carry "too few to judge" and the count to the first read.
  - Random baseline: for every filled call, RANDOM_DRAWS entries on the same name at seeded random sessions before its
    read (within RANDOM_LOOKBACK sessions), each bought at the next open and run under the call's own distances (out,
    first target, time stop; an out on a daily close sells at the next open; both on one bar: the out). Same name, same
    exits, earlier days: what the rule's timing added over buying that stock at random.
  - Incubation: a setup type (the read's form) is "proven" only once its record holds INCUBATION_SESSIONS distinct
    listing sessions and SMALL_N closed calls under one frozen rule hash (the read code versions it was listed under);
    otherwise "incubating". A flag only: it removes nothing."""
import hashlib
import json
import os
import random

from .. import calendar as cal
from ..util import read_json, write_json_atomic
from . import calls as callbook
from ..record_ext import fan as _fan, tracks as _tracks

EVEN_R = 0.05
SMALL_N = 30
HORIZONS = (1, 5, 21)
RANDOM_DRAWS = 20
RANDOM_LOOKBACK = 120
INCUBATION_SESSIONS = 60
MAX_ROWS = 200
FORM_WORDS = {"now": "Buy now", "pullback": "Pullback", "breakout": "Breakout", "turn": "Turn"}
EXIT_CODES = {"target": "target", "out": "stop", "time stop": "time"}
RESULT_STATUSES = ("closed",)
EXCLUDED = ("expired", "missed", "void")
_Q = {"p05", "p25", "p50", "p75", "p95"}
EXT_KEYS = {"fan", "overnight_day", "levels"}                    # record_ext tiles: each carries status ok / no_data
EXT_ALLOWED = {                                                  # their keys for the edition contract (terminal/__init__)
    "record.fan": {"status", "reason", "n", "paths", "block", "seed", "fan", "final", "actual_total_r", "streak"},
    "record.fan.fan[]": {"k"} | _Q, "record.fan.final": _Q, "record.fan.streak": {"observed", "p95"},
    "record.overnight_day": {"status", "reason", "window", "rows", "skipped", "all"},
    "record.overnight_day.rows[]": {"symbol", "sessions", "overnight", "day", "full"},
    "record.overnight_day.all": {"names", "overnight", "day", "full"},
    "record.levels": {"status", "reason", "n", "small_n", "kinds", "cards_waiting"},
    "record.levels.kinds[]": {"kind", "rate", "n"}}


def paths(root):
    d = os.path.join(root, "state", "terminal")
    return (os.path.join(d, "record.json"), os.path.join(d, "record_corrections.jsonl"),
            os.path.join(d, "incubation.json"))


def _day(b):
    return cal._as_date(float(b["t"])).isoformat()


def exit_code(c):
    """target / trail (a stop after the first target was trimmed) / stop / time / expired / missed / void / open /
    waiting"""
    s = c.get("status")
    if s != "closed":
        return s
    if c.get("trimmed") and c.get("exit") == "out":
        return "trail"
    return EXIT_CODES.get(c.get("exit"), "time" if "no prices" in str(c.get("exit")) else "stop")


def targets_hit(c):
    """'1/1', '0/1', '1/2', '2/2' for a closed call; None otherwise"""
    if c.get("status") != "closed":
        return None
    two = bool(c.get("trim") and c.get("t2"))
    n = (2 if c.get("exit") == "target" else 1 if c.get("trimmed") else 0) if two else \
        (1 if c.get("exit") == "target" else 0)
    return f"{n}/{2 if two else 1}"


def verdict(r):
    if r is None:
        return None
    return "won" if r > EVEN_R else "lost" if r < -EVEN_R else "even"


def horizon_grades(c, bars):
    """{'1d': pct, '5d': pct, '21d': pct} for the horizons the bars already hold, from the read's own session close;
    None when the read's session is missing from the bars"""
    f = callbook.split_factor(c, bars)
    if f is None or not c.get("ref_close"):
        return None
    after = [b for b in bars if _day(b) > c["as_of"]]
    base = float(c["ref_close"]) * f
    out = {}
    for k in HORIZONS:
        if len(after) >= k:
            out[f"{k}d"] = round((float(after[k - 1]["c"]) / base - 1) * 100, 2)
    return out


def peak_r(c, bars):
    """a closed call's best R while held: the highest high from its fill session to its close, in its own risk"""
    if c.get("status") != "closed" or not c.get("filled") or not c.get("entry"):
        return None
    f = callbook.split_factor(c, bars)
    u = callbook.risk_unit(c)
    if f is None or u <= 0:
        return None
    hs = [float(b["h"]) / f for b in bars if c["filled"] <= _day(b) <= (c.get("closed") or "9999")]
    if not hs:
        return None
    return round((max(hs) - float(c["entry"])) / u, 2)


def update_grades(store, calls, daily, today=None):
    """write each call's grades once: a horizon's grade, the peak of a closed call, the regime it was listed in
    (set by the caller for calls opened this edition). A value already stored is never replaced"""
    for c in calls:
        if c.get("kind") != "read" or c.get("published") is False:
            continue
        g = store.setdefault(c["id"], {})
        bars = daily.get(c["symbol"]) or []
        if bars:
            for k, v in (horizon_grades(c, bars) or {}).items():
                g.setdefault(k, v)
            if "peak_r" not in g:
                p = peak_r(c, bars)
                if p is not None:
                    g["peak_r"] = p
        if today and "graded_on" not in g and all(f"{k}d" in g for k in HORIZONS):
            g["graded_on"] = str(today)
    return store


def due(c):
    """the date each horizon's grade lands: the k-th session after the read's session"""
    return {f"{k}d": cal.next_trading_day(c["as_of"], k).isoformat() for k in HORIZONS}


def load_corrections(path):
    out = []
    if os.path.exists(path):
        with open(path) as fh:
            for line in fh:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def add_correction(path, call_id, field, old, new, why, at):
    """a correction is a new row, never an edit"""
    with open(path, "a") as fh:
        fh.write(json.dumps({"call": call_id, "field": field, "old": old, "new": new, "why": why, "at": at},
                            sort_keys=True) + "\n")


def row(c, g, corr):
    """one call's public row: no prices"""
    r = c.get("outcome_r")
    pk = (g or {}).get("peak_r")
    out = {"id": c["id"], "symbol": c["symbol"], "form": FORM_WORDS.get(c.get("form"), c.get("form")),
           "listed": c["opened"][:10], "status": c["status"], "code": exit_code(c), "targets": targets_hit(c),
           "pct": c.get("outcome_pct"), "r": r, "verdict": verdict(r) if c["status"] == "closed" else None,
           "give_back": round(pk - r, 2) if (pk is not None and r is not None and pk >= r) else None,
           "closed": c.get("closed"), "regime": (g or {}).get("regime")}
    for k in HORIZONS:
        out[f"h{k}"] = (g or {}).get(f"{k}d")
    if c["status"] in EXCLUDED:
        out["why"] = c.get("exit")
    if c.get("retired"):                                 # the old v2 board, frozen (calls.retire): kept, labelled
        out["retired"] = (c["retired"] or {}).get("on") if isinstance(c["retired"], dict) else str(c["retired"])
    fixes = [x for x in corr if x.get("call") == c["id"]]
    if fixes:
        out["corrections"] = len(fixes)
    return out


def summary(rows):
    closed = [x for x in rows if x["status"] == "closed"]
    won = sum(1 for x in closed if x["verdict"] == "won")
    lost = sum(1 for x in closed if x["verdict"] == "lost")
    even = sum(1 for x in closed if x["verdict"] == "even")
    rs = [x["r"] for x in closed if x["r"] is not None]
    gb = [x["give_back"] for x in closed if x["give_back"] is not None]
    n = len(closed)
    return {"calls": len(rows), "closed": n, "won": won, "lost": lost, "even": even,
            "hit_rate": round(won / (won + lost), 3) if won + lost else None,
            "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
            "total_r": round(sum(rs), 2) if rs else None,
            "avg_give_back": round(sum(gb) / len(gb), 2) if gb else None,
            "small_n": n < SMALL_N, "to_first_read": max(0, SMALL_N - n)}


def horizon_summary(rows):
    out = {}
    for k in HORIZONS:
        v = [x[f"h{k}"] for x in rows if x.get(f"h{k}") is not None]
        out[f"{k}d"] = {"n": len(v), "mean": round(sum(v) / len(v), 2) if v else None,
                        "up": sum(1 for x in v if x > 0)}
    return out


def months(rows):
    by = {}
    for x in rows:
        if x["status"] == "closed" and x.get("closed"):
            by.setdefault(x["closed"][:7], []).append(x)
    return [dict(summary(v), month=m) for m, v in sorted(by.items(), reverse=True)]


def by_type(rows):
    """per setup type (form) and per regime: the summary, or the not-yet-graded state"""
    out = {}
    for key, name in (("form", "form"), ("regime", "regime")):
        groups = {}
        for x in rows:
            groups.setdefault(x.get(key) or "not recorded", []).append(x)
        out[name] = {k: summary(v) for k, v in sorted(groups.items())}
    return out


def first_grade(cs):
    """the latest date the first result of these live calls is due: a live call resolves by its buy window's end plus
    its time stop (a buy that never fills expires and is not a result)"""
    ds = [cal.next_trading_day(c.get("window_until") or c["as_of"], int(c.get("time_stop") or 10)).isoformat()
          for c in cs if c.get("as_of") and c.get("status") in ("open", "waiting")]
    return min(ds) if ds else None


def record_line(form, calls, rows):
    """the line a card or a watching row carries for its type: its record, or when it is graded"""
    word = FORM_WORDS.get(form, form)
    mine = [x for x in rows if x["form"] == word]
    s = summary(mine)
    if not mine:
        return {"type": word, "state": "none", "text": f"{word}: no calls logged yet."}
    if not s["closed"]:
        cs = [c for c in calls if c.get("kind") == "read" and FORM_WORDS.get(c.get("form"), c.get("form")) == word]
        return {"type": word, "state": "pending", "n": s["calls"], "first": first_grade(cs),
                "text": f"{word}: not yet graded · {s['calls']} logged" +
                (f" · first result due by {first_grade(cs)}." if first_grade(cs) else ".")}
    t = (f"{word}: {s['won']} won, {s['lost']} lost" + (f", {s['even']} even" if s["even"] else "") +
         f" of {s['closed']} closed · avg {s['avg_r']:+.2f}R")
    if s["small_n"]:
        t += f" · too few to judge (first read at {SMALL_N})"
    return {"type": word, "state": "small" if s["small_n"] else "graded", "n": s["closed"],
            "hit_rate": s["hit_rate"], "avg_r": s["avg_r"], "text": t + "."}


def _walk(bars, i, out_pct, t1_pct, risk_pct, time_stop):
    """one random entry: bought at bar i's open, run under the call's distances; -> R or None"""
    if i >= len(bars):
        return None
    e = float(bars[i]["o"])
    out, t1, u = e * (1 + out_pct), e * (1 + t1_pct), e * risk_pct
    if u <= 0:
        return None
    held, pending = 0, False
    for b in bars[i:]:
        o, h, cl = float(b["o"]), float(b["h"]), float(b["c"])
        if pending:
            return (o - e) / u
        held += 1
        if cl <= out:
            pending = True
            continue
        if h >= t1:
            return (max(o, t1) - e) / u
        if held >= time_stop:
            return (cl - e) / u
    return None


def random_baseline(calls, daily, seed=1587):
    """the seeded random entries on each filled call's name before its read, under its own exits"""
    rs, names = [], 0
    for c in calls:
        if c.get("kind") != "read" or not c.get("filled") or not c.get("ref_close"):
            continue
        bars = daily.get(c["symbol"]) or []
        f = callbook.split_factor(c, bars)
        if f is None:
            continue
        idx = [j for j, b in enumerate(bars) if _day(b) <= c["as_of"]]
        if len(idx) < 2:
            continue
        ref = float(c["ref_close"])
        cap = c["zone"][1]
        out_pct, t1_pct, risk_pct = c["out"] / ref - 1, c["t1"] / ref - 1, (cap - c["out"]) / ref
        pool = idx[-RANDOM_LOOKBACK:-1]
        rng = random.Random(f"{seed}:{c['id']}")
        got = 0
        for _ in range(RANDOM_DRAWS):
            j = rng.choice(pool)
            r = _walk(bars[:idx[-1] + 1], j + 1, out_pct, t1_pct, risk_pct, int(c.get("time_stop") or 10))
            if r is not None:
                rs.append(r)
                got += 1
        names += 1 if got else 0
    if not rs:
        return {"n": 0, "names": 0, "avg_r": None, "hit_rate": None, "seed": seed}
    won = sum(1 for r in rs if r > EVEN_R)
    lost = sum(1 for r in rs if r < -EVEN_R)
    return {"n": len(rs), "names": names, "avg_r": round(sum(rs) / len(rs), 2),
            "hit_rate": round(won / (won + lost), 3) if won + lost else None, "seed": seed, "draws": RANDOM_DRAWS}


def rule_hash(cs):
    codes = sorted({str((c.get("read") or {}).get("code")) for c in cs})
    return hashlib.sha256(json.dumps(codes).encode()).hexdigest()[:16]


def incubation(calls, frozen):
    """{form word: {state, sessions, closed, hash, frozen}}; frozen: {form word: hash first seen}, extended in place"""
    out = {}
    by = {}
    for c in calls:
        if c.get("kind") == "read" and c.get("published") is not False:
            by.setdefault(FORM_WORDS.get(c.get("form"), c.get("form")), []).append(c)
    for word, cs in sorted(by.items()):
        h = rule_hash(cs)
        frozen.setdefault(word, h)
        sessions = len({c["as_of"] for c in cs})
        closed = sum(1 for c in cs if c["status"] == "closed")
        same = frozen[word] == h
        proven = same and sessions >= INCUBATION_SESSIONS and closed >= SMALL_N
        out[word] = {"state": "proven" if proven else "incubating", "sessions": sessions, "closed": closed,
                     "need_sessions": INCUBATION_SESSIONS, "need_closed": SMALL_N, "hash": h, "frozen": frozen[word],
                     "rule_changed": not same}
    return out


def excluded_why(rows):
    """the calls kept out of the hit rate, by how they ended, each with its reasons counted: [{code, n, why}]"""
    out = []
    for code in EXCLUDED:
        mine = [x for x in rows if x["status"] == code]
        if not mine:
            continue
        by = {}
        for x in mine:
            w = x.get("why") or "no reason recorded"
            by[w] = by.get(w, 0) + 1
        out.append({"code": code, "n": len(mine),
                    "why": "; ".join(f"{w} ({n})" for w, n in sorted(by.items(), key=lambda kv: (-kv[1], kv[0])))})
    return out


def edge_over_random(summ, rnd):
    """what the rule's timing added over random entries in the same names, in R: the avg per closed call less the
    random entries' avg; None when either side has no number"""
    a, b = (summ or {}).get("avg_r"), (rnd or {}).get("avg_r")
    if a is None or b is None or not (rnd or {}).get("n"):
        return None
    return round(a - b, 2)


def type_lines(calls, rows):
    """every setup type's line: its graded record, or "not yet graded, n logged, first result due by <date>" """
    words = sorted({x["form"] for x in rows if x.get("form")})
    inv = {v: k for k, v in FORM_WORDS.items()}
    return [record_line(inv.get(w, w), calls, rows) for w in words]


def build(root, calls, daily, today=None, regime=None, opened_now=()):
    """-> the edition's `record` block; writes the grades (once each) and the frozen hashes"""
    gpath, cpath, ipath = paths(root)
    store = read_json(gpath, {}) or {}
    for cid in opened_now:                               # the market the call was listed in, kept from its edition
        if regime:
            store.setdefault(cid, {}).setdefault("regime", regime)
    update_grades(store, calls, daily, today)
    os.makedirs(os.path.dirname(gpath), exist_ok=True)
    write_json_atomic(gpath, store)
    frozen = read_json(ipath, {}) or {}
    inc = incubation(calls, frozen)
    write_json_atomic(ipath, frozen)
    corr = load_corrections(cpath)
    rc = [c for c in calls if c.get("kind") == "read" and c.get("published") is not False]
    rows = [row(c, store.get(c["id"]), corr) for c in rc]
    rows.sort(key=lambda x: (x["listed"], x["id"]), reverse=True)
    excl = {}
    for x in rows:
        if x["status"] in EXCLUDED:
            excl.setdefault(x["status"], 0)
            excl[x["status"]] += 1
    s = summary(rows)
    rnd = random_baseline(rc, daily)
    rnd["edge_r"] = edge_over_random(s, rnd)
    return {"header": "Losers included", "summary": s, "horizons": horizon_summary(rows), "months": months(rows),
            "excluded": excl, "excluded_why": excluded_why(rows), "by_type": by_type(rows), "random": rnd,
            "type_lines": type_lines(rc, rows),
            "incubation": inc, "corrections": len(corr), "rows": rows[:MAX_ROWS], "rows_total": len(rows),
            "even_band": EVEN_R, "small_n": SMALL_N,
            "since": min((c["opened"][:10] for c in rc), default=None),
            "fan": _fan.record_fan(rows),
            "overnight_day": _tracks.overnight_day(daily, sorted({x["symbol"] for x in rows if x.get("symbol")})),
            "levels": _tracks.level_record(root, daily)}
