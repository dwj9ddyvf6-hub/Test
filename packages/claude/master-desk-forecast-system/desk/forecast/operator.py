"""The desk AI as operator, and the public scored record (FACTORY.md §8, §11; BSF-11, BSF-12).

Everything here proposes; nothing places an order (propose-then-approve), and nothing writes a sleeve, the OMS or a book.

OPERATE   run_day(book, todays, ...)   route every name (router.route), allocate the BUYs by breadth
                                       (portfolio.allocate) and return the day: routes, allocation, abstentions
RECORD    log_day / seal / show        every proposal, abstentions and losers included, is appended to
                                       <root>/state/forecast/record/<session>.jsonl with written_at BEFORE anything shows it;
                                       show() refuses a row that is not logged or was logged at or after the show;
                                       seal() pins a finished session file by sha256 (a sealed file takes no rows)
          grade(root, daily, ...)      each row at 1, 5 and 21 sessions (terminal/record.HORIZONS), once, appended to
                                       grades.jsonl: the return from the logged close, the mean of seeded random
                                       entries on the SAME name before the call (RANDOM_DRAWS draws in the
                                       RANDOM_LOOKBACK sessions before it, the same horizon), and the edge between them
          scorecard(root)              the public record: counts by label, per horizon the edge in the called direction
                                       (a buy or hold: above its controls; an avoid, trim or sell: below), win share,
                                       the abstentions' realized edge (what saying "don't know" cost or saved), every
                                       row with its outcome; small samples carry "too few to judge" (record.SMALL_N)
          correct(...)                 a correction is a new row (record.add_correction), published beside the row
DECAY     decay(root, book, ...)       a cell with enough forward dates runs record_ext.decay's state machine; a
                                       demotion is a row in status.jsonl, applied as an overlay on the pinned book
No filesystem path, key or host appears in a public row; no price is published."""
import hashlib
import json
import os
import random

import numpy as np

from .. import calendar as cal
from ..record_ext import decay as _decay
from ..terminal import record as _rec
from . import portfolio as PF
from . import promoted as PM
from . import router as RT

HORIZONS = _rec.HORIZONS                         # (1, 5, 21)
RANDOM_DRAWS = _rec.RANDOM_DRAWS
RANDOM_LOOKBACK = _rec.RANDOM_LOOKBACK
SMALL_N = _rec.SMALL_N
UP_LABELS = ("BUY", "HOLD", "WAIT")
DOWN_LABELS = ("AVOID", "SELL", "TRIM")
SEED = 1587
SPAN = "forecast"
RESERVED = ("shown.jsonl", "grades.jsonl", "corrections.jsonl", "status.jsonl")


class NotLogged(RuntimeError):
    pass


class Sealed(RuntimeError):
    pass


def rdir(root):
    return os.path.join(root, "state", SPAN, "record")


def _jsonl(path):
    out = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return len(rows)


def row_id(session, p):
    key = "|".join(str(x) for x in (session, p.get("sym"), p.get("as_of"), p.get("label"), (p.get("cell") or {}).get("id")))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def session_files(root):
    d = rdir(root)
    return sorted(f for f in os.listdir(d) if f.endswith(".jsonl") and f not in RESERVED) if os.path.isdir(d) else []


def sha_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------- operate
def run_day(book, todays, as_of=None, overlay=(), z=RT.Z, boot=PF.BOOT):
    """-> {as_of, routes, allocation, counts}; todays: router `today` dicts (today.snapshot)"""
    b = PM.with_overlay(book, list(overlay))
    routes = [RT.route(t, b, z=z) for t in todays]
    alloc = PF.allocate(routes, b, as_of=as_of, boot=boot)
    counts = {}
    for r in routes:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    return {"as_of": as_of, "routes": routes, "allocation": alloc, "counts": counts, "propose_only": True}


# ---------------------------------------------------------------- record: log before show
def log_day(root, session, day, closes, now):
    """append the day's proposals (every label, abstentions included) to <session>.jsonl; `closes` {sym: the close the
    row was written against}. Returns the row ids. A sealed session refuses; a repeat of a row is not written twice."""
    path = os.path.join(rdir(root), f"{session}.jsonl")
    if os.path.exists(path + ".sealed"):
        raise Sealed(f"session {session} is sealed")
    have = {r["rid"] for r in _jsonl(path)}
    items = {i["sym"]: i for i in (day.get("allocation") or {}).get("items", [])}
    rows, ids = [], []
    for p in day["routes"]:
        rid = row_id(session, p)
        ids.append(rid)
        if rid in have:
            continue
        c = p.get("cell") or {}
        rows.append({"rid": rid, "session": session, "written_at": now, "sym": p["sym"], "as_of": p["as_of"],
                     "label": p["label"], "reason": p.get("reason"), "owned": p.get("owned"),
                     "cell": c.get("id"), "n": c.get("n"), "base_rate": c.get("base_rate"), "rate": c.get("rate"),
                     "lift": c.get("lift"), "cost_side": (p.get("cost") or {}).get("own_side"),
                     "du_lb": (p.get("du") or {}).get("lb"), "matched": len(p.get("evidence") or []) or p.get("n_matched", 0),
                     "risk_budget_pct": (items.get(p["sym"]) or {}).get("risk_budget_pct"),
                     "ref_close": closes.get(p["sym"]), "due": {f"{k}d": cal.next_trading_day(p["as_of"], k).isoformat()
                                                                 for k in HORIZONS}})
    _append(path, rows)
    return ids


def seal(root, session):
    path = os.path.join(rdir(root), f"{session}.jsonl")
    if not os.path.exists(path):
        raise NotLogged(f"no session {session}")
    sha = sha_of(path)
    with open(path + ".sealed", "w") as f:
        f.write(sha)
    return sha


def verify(root, session):
    path = os.path.join(rdir(root), f"{session}.jsonl")
    with open(path + ".sealed") as f:
        return f.read().strip() == sha_of(path)


def logged(root):
    out = {}
    for fn in session_files(root):
        for r in _jsonl(os.path.join(rdir(root), fn)):
            out[r["rid"]] = r
    return out


def show(root, rids, now):
    """the public rows for these ids, after checking each was logged strictly before `now`; records the showing"""
    have = logged(root)
    miss = [r for r in rids if r not in have]
    if miss:
        raise NotLogged(f"{len(miss)} row(s) not logged: shown only after they are written")
    late = [r for r in rids if not have[r]["written_at"] < now]
    if late:
        raise NotLogged(f"{len(late)} row(s) were written at or after the time they would show")
    _append(os.path.join(rdir(root), "shown.jsonl"), [{"rid": r, "shown_at": now} for r in rids])
    return [public(have[r]) for r in rids]


def public(r, grades=None):
    keep = ("rid", "session", "sym", "as_of", "label", "reason", "owned", "cell", "n", "base_rate", "rate", "lift",
            "cost_side", "du_lb", "risk_budget_pct", "due")
    out = {k: r.get(k) for k in keep}
    out["written_at"] = r["written_at"]
    if grades is not None:
        out["grades"] = grades
    return out


# ---------------------------------------------------------------- grade
def controls(bars, as_of, k, rid, seed=SEED):
    """k-session returns (%) of seeded random entries on the same name in the RANDOM_LOOKBACK sessions before the call,
    each fully realised by the call's session (no bar after it is read)"""
    days = [_rec._day(b) for b in bars]
    if as_of not in days:
        return []
    i = days.index(as_of)
    pool = [j for j in range(max(0, i - RANDOM_LOOKBACK), i) if j + k <= i]
    if not pool:
        return []
    rng = random.Random(f"{seed}:{rid}:{k}")
    out = []
    for _ in range(RANDOM_DRAWS):
        j = rng.choice(pool)
        a, b = float(bars[j]["c"]), float(bars[j + k]["c"])
        if a > 0:
            out.append((b / a - 1) * 100)
    return out


def grade(root, daily, today=None, seed=SEED):
    """write the grades that have landed, once each (rid, horizon); -> the new rows"""
    gp = os.path.join(rdir(root), "grades.jsonl")
    done = {(g["rid"], g["k"]) for g in _jsonl(gp)}
    new = []
    for rid, r in logged(root).items():
        bars = daily.get(r["sym"]) or []
        if not bars or not r.get("ref_close"):
            continue
        c = {"as_of": r["as_of"], "ref_close": r["ref_close"], "symbol": r["sym"]}
        hg = _rec.horizon_grades(c, bars)
        if not hg:
            continue
        for k in HORIZONS:
            key = f"{k}d"
            if key not in hg or (rid, key) in done:
                continue
            ctl = controls(bars, r["as_of"], k, rid, seed)
            cm = float(np.mean(ctl)) if ctl else None
            new.append({"rid": rid, "k": key, "ret_pct": hg[key], "control_pct": None if cm is None else round(cm, 4),
                        "n_controls": len(ctl), "edge_pct": None if cm is None else round(hg[key] - cm, 4),
                        "graded_at": today})
    _append(gp, new)
    return new


def _called(label, edge):
    """the edge in the direction the label called: up labels win above their controls, down labels below"""
    if edge is None:
        return None
    return edge if label in UP_LABELS else -edge if label in DOWN_LABELS else None


def _verdict(called):
    return None if called is None else "won" if called > 0 else "lost" if called < 0 else "even"


def scorecard(root, now=None):
    """the public record; every logged row is in it, graded or not yet graded, losers included"""
    have = logged(root)
    gr = {}
    for g in _jsonl(os.path.join(rdir(root), "grades.jsonl")):
        gr.setdefault(g["rid"], {})[g["k"]] = g
    corr = _rec.load_corrections(os.path.join(rdir(root), "corrections.jsonl"))
    rows, by_label = [], {}
    h_called = {f"{k}d": [] for k in HORIZONS}
    h_abst = {f"{k}d": [] for k in HORIZONS}
    for rid, r in sorted(have.items(), key=lambda kv: (kv[1]["as_of"], kv[0]), reverse=True):
        g = gr.get(rid, {})
        gp = {}
        for k in HORIZONS:
            x = g.get(f"{k}d")
            if x is None:
                gp[f"{k}d"] = {"status": "not yet graded", "due": r["due"][f"{k}d"]}
                continue
            called = _called(r["label"], x["edge_pct"])
            gp[f"{k}d"] = {"status": "graded", "ret_pct": x["ret_pct"], "control_pct": x["control_pct"],
                           "edge_pct": x["edge_pct"], "verdict": _verdict(called)}
            if called is not None:
                h_called[f"{k}d"].append(called)
            elif r["label"] == "ABSTAIN" and x["edge_pct"] is not None:
                h_abst[f"{k}d"].append(x["edge_pct"])
        pr = public(r, gp)
        fixes = [c for c in corr if c.get("call") == rid]
        if fixes:
            pr["corrections"] = len(fixes)
        rows.append(pr)
        by_label[r["label"]] = by_label.get(r["label"], 0) + 1

    def agg(v):
        n = len(v)
        if not n:
            return {"n": 0, "status": "no_data", "reason": "nothing graded yet"}
        a = np.asarray(v, float)
        out = {"n": n, "mean_edge_pct": round(float(a.mean()), 4), "win_share": round(float((a > 0).mean()), 4)}
        if n >= 3:
            lb, _ = PF.block_bootstrap_lb(a, 1, B=1000, seed=SEED)
            out["lb_pct"] = None if lb is None else round(lb, 4)
        if n < SMALL_N:
            out["note"] = "too few to judge"
        return out
    return {"header": "Losers included", "rows_total": len(rows), "by_label": by_label,
            "horizons": {k: {"called": agg(h_called[k]), "abstained": agg(h_abst[k])} for k in h_called},
            "rows": rows, "corrections": len(corr), "small_n": SMALL_N, "random_draws": RANDOM_DRAWS,
            "since": min((r["as_of"] for r in have.values()), default=None),
            "method": "edge = the return from the logged close minus the mean of seeded random entries on the same "
                      "name before the call; the edge is signed in the direction called"}


def correct(root, rid, field, old, new, why, at):
    _rec.add_correction(os.path.join(rdir(root), "corrections.jsonl"), rid, field, old, new, why, at)


# ---------------------------------------------------------------- decay
def forward_series(root):
    """{cell id: (dates, per-date mean edge in the called direction at 5 sessions)} from the graded rows"""
    have = logged(root)
    by = {}
    for g in _jsonl(os.path.join(rdir(root), "grades.jsonl")):
        r = have.get(g["rid"])
        if g["k"] != "5d" or r is None or not r.get("cell"):
            continue
        called = _called(r["label"], g["edge_pct"])
        if called is None:
            continue
        by.setdefault(r["cell"], {}).setdefault(r["as_of"], []).append(called)
    return {c: (sorted(d), [float(np.mean(d[x])) for x in sorted(d)]) for c, d in by.items()}


def decay(root, book, window=_decay.WINDOW, as_of=None):
    """state-machine verdict per cell with a forward series; the baseline is the cell's own scored mean utility (pct)"""
    ents = PM.by_id(book)
    out, rows = {}, []
    for cid, (dates, vals) in sorted(forward_series(root).items()):
        e = ents.get(cid)
        if e is None or not e["windows"]:
            continue
        base = float(np.mean(np.asarray(e["windows"][0]["gross"], float))) * 100
        res = _decay.decay_state(vals, base, window=window)
        out[cid] = {k: v for k, v in res.items() if k != "history"}
        out[cid]["dates"] = len(dates)
        if res.get("status") == "ok" and res["state"] in ("decayed", "disabled", "monitoring"):
            rows.append({"id": cid, "status": "demoted" if res["state"] in ("decayed", "disabled") else "probation",
                         "as_of": as_of, "why": f"decay state {res['state']} after {res['scans']} scans"})
    return {"cells": out, "status_rows": rows}


def append_status(root, rows):
    return _append(os.path.join(rdir(root), "status.jsonl"), rows)


def overlay(root):
    return _jsonl(os.path.join(rdir(root), "status.jsonl"))


# ---------------------------------------------------------------- the day on disk (what the desk-AI tools read)
def day_path(root):
    return os.path.join(root, "state", SPAN, "routes.json")


def write_day(root, day):
    """state/forecast/routes.json: the latest day, atomically; the tools read it, they compute nothing"""
    from ..util import write_json_atomic
    write_json_atomic(day_path(root), day)
    return day_path(root)


def read_day(root):
    from ..util import read_json
    return read_json(day_path(root), None)


def edition_block(root):
    """the `forecast` block for a terminal edition (docs/research/forecast_block_SCHEMA.md): words and ids, no paths. It
    is NOT wired into the edition by this module; the edition owner adds the key, or reads it through the tools"""
    day = read_day(root)
    out = {"as_of": (day or {}).get("as_of"), "counts": (day or {}).get("counts"), "propose_only": True}
    al = (day or {}).get("allocation") or {}
    out["allocation"] = {k: al.get(k) for k in ("breadth_eff", "n_bets", "total_risk_pct", "delta_u", "ir", "caps_hit",
                                                "status", "reason")} if al else None
    out["record"] = scorecard(root) if os.path.isdir(rdir(root)) else None
    return out
