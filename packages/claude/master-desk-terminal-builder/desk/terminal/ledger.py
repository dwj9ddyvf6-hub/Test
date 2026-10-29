"""The forward ledger: every roster read, scored forward. The board lists five names a session; the roster job reads
about 1,800. The ledger writes down every one of those reads once, when the session's read completes, and scores it
on the desk's daily bars by the record's own rules (calls.open_read_call and calls.resolve_reads), as if every read
were a call. So every part of the read (a plan source, a form, the take, the conviction) earns its weight in the open.
No backtest: nothing is scored on bars from before its read, and every row keeps the read's version, so a change to
the read starts new evidence and never rewrites the old.

An honest sample. Reads of one name on consecutive sessions often repeat one plan; scored every session they would
count one idea many times. A read starts an episode when the name's read in the previous ledger session had another
form or plan source, or an out line or buy cap more than EPISODE_ATR away; only the first read of an episode is scored.

Files (state/terminal/ledger/, pushed with the record):
  reads-<as_of>.jsonl.gz     every read of the session: its plan in prices, its take, conviction, evidence and facts;
                             written once
  outcomes-<as_of>.json.gz   the session's scored episodes once final (each expired, missed, void or closed, or the
                             session FINAL sessions old); written once, never recomputed
  summary.json               the scorecard: overall and by plan source, form, take and conviction: episodes, filled,
                             closed, hits, the hit rate with its 95% Wilson interval, mean R with its standard error,
                             final and still live; rewritten each session"""
import gzip
import json
import math
import os
from datetime import date, datetime
from datetime import time as dtime

from .. import calendar as cal
from ..util import ET, write_json_atomic
from . import calls as C

FINAL = 60                     # sessions after which a read's outcome is final whatever its state: a buy window of
                               # at most 15 sessions and a time stop of at most 40 leave nothing open by then
EPISODE_ATR = 0.5              # an out line or cap this far from the previous read's starts a new episode
CONVICTION = {3: "High conviction", 2: "Solid", 1: "Speculative"}
TERMINAL = ("closed", "expired", "missed", "void")
Z95 = 1.96


def folder(root):
    return os.path.join(root, "state", "terminal", "ledger")


def _write_gz(path, text):
    tmp = path + ".tmp"
    with open(tmp, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as f:
        f.write(text.encode("utf-8"))
    os.replace(tmp, path)


def _read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.read()


def row_of(sym, pub, rec):
    """a read as a ledger row: its plan in prices (as the record keeps it), its take, conviction, evidence and facts"""
    pl = pub["plan"]
    row = {"s": sym, "v": rec.get("v"), "code": rec.get("code"), "as_of": rec["as_of"], "form": rec["form"], "source": rec["source"],
           "mode": rec.get("mode") or "level", "close": rec["close"], "atr": rec["atr"], "zone": list(rec["zone"]),
           "trigger": rec["trigger"], "out": rec["out"], "t1": rec["t1"], "t2": rec["t2"], "window": pl["window"],
           "sessions": pl["sessions"], "take": rec["gut"], "conviction": rec["conviction"],
           "evidence": round(float(rec["evidence"]), 2), "points": rec.get("points"),
           "gut_points": rec.get("gut_points"), "facts": rec.get("facts") or []}
    if rec.get("trim"):
        row.update(trim=rec["trim"], time_stop=rec.get("time_stop"))
    if rec.get("cautions"):                            # ChartsLector's warnings it carried: scored forward by key
        row["cautions"] = list(rec["cautions"])
    return row


def record_session(root, as_of, reads, records):
    """write the session's reads once: -> the number of rows, or None when the session is already in the ledger"""
    d = folder(root)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"reads-{as_of}.jsonl.gz")
    if os.path.exists(path):
        return None
    rows = [row_of(s, reads[s], records[s]) for s in sorted(records)      # a read that stands aside makes no call
            if s in reads and records[s].get("as_of") == as_of and records[s].get("form") != "wait"]
    _write_gz(path, "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows))
    return len(rows)


def load_rows(root, as_of):
    path = os.path.join(folder(root), f"reads-{as_of}.jsonl.gz")
    return [json.loads(line) for line in _read_gz(path).splitlines() if line.strip()]


def sessions(root):
    d = folder(root)
    if not os.path.isdir(d):
        return []
    return sorted(n[len("reads-"):-len(".jsonl.gz")] for n in os.listdir(d)
                  if n.startswith("reads-") and n.endswith(".jsonl.gz"))


def new_episode(row, prev):
    """True when `row` starts an episode: no read of the name in the previous ledger session, or that read had another
    form or plan source, or its out line or buy cap sat more than EPISODE_ATR away"""
    if prev is None or prev["form"] != row["form"] or prev["source"] != row["source"]:
        return True
    tol = EPISODE_ATR * float(row["atr"] or 0)
    return abs(row["out"] - prev["out"]) > tol or abs(row["zone"][1] - prev["zone"][1]) > tol


def shadow(row):
    """the read as the call the record would have opened for it, listed at its session's close: the same dict
    calls.open_read_call builds, so it fills and closes by exactly the record's rules"""
    pub = {"symbol": row["s"], "form": row["form"], "conviction": {"word": CONVICTION.get(row["conviction"], "")},
           "gut": {"word": row["take"]}, "plan": {"window": row["window"], "sessions": row["sessions"]}}
    rec = {"v": row.get("v"), "code": row.get("code"), "as_of": row["as_of"], "zone": row["zone"], "trigger": row["trigger"], "out": row["out"],
           "t1": row["t1"], "t2": row["t2"], "close": row["close"], "mode": row["mode"], "source": row["source"],
           "evidence": row["evidence"], "points": row.get("points"), "gut_points": row.get("gut_points"),
           "facts": row.get("facts"), "trim": row.get("trim"), "time_stop": row.get("time_stop")}
    opened = datetime.fromtimestamp(cal.session_close(row["as_of"]), tz=ET).isoformat()
    calls = []
    C.open_read_call(calls, pub, rec, opened)
    calls[0]["id"] = f"L-{row['as_of']}-{row['s']}"
    return calls[0]


OUT_KEYS = ("status", "exit", "filled", "entry", "closed", "outcome_pct", "outcome_r")


def outcome(row, call):
    o = {"s": row["s"], "v": row.get("v"), "code": row.get("code"), "source": row["source"], "form": row["form"], "take": row["take"],
         "conviction": row["conviction"], "mode": row["mode"]}
    o.update({k: call.get(k) for k in OUT_KEYS})
    if call.get("trimmed"):
        o["trimmed"] = True
    if row.get("cautions"):
        o["cautions"] = list(row["cautions"])
    return o


def update(root, bars_for, today, batch=200):
    """score every ledger session whose outcomes are not final yet on the bars `bars_for(symbols)` returns, write the
    sessions that became final, and rewrite summary.json -> the summary. today: the latest session the bars hold"""
    names = sessions(root)
    d = folder(root)
    prev_rows, pending, done = None, [], []
    for s in names:
        rows = load_rows(root, s)
        by_prev = {r["s"]: r for r in prev_rows} if prev_rows is not None else {}
        firsts = [r for r in rows if new_episode(r, by_prev.get(r["s"]) if prev_rows is not None else None)]
        prev_rows = rows
        out_path = os.path.join(d, f"outcomes-{s}.json.gz")
        if os.path.exists(out_path):
            done += json.loads(_read_gz(out_path))["rows"]
            continue
        pending.append((s, firsts))
    by_sym = {}
    for s, rows in pending:
        for r in rows:
            by_sym.setdefault(r["s"], []).append((s, r))
    calls = {}
    syms = sorted(by_sym)
    for i in range(0, len(syms), batch):
        part = syms[i:i + batch]
        bars = bars_for(part) or {}
        for sym in part:
            if not bars.get(sym):
                continue
            first = min(s for s, _ in by_sym[sym])
            # the bars from the earliest pending read's session on: the record's walk filters every bar per call
            since = datetime.combine(date.fromisoformat(first), dtime(0), ET).timestamp() - 12 * 3600
            mine = [b for b in bars[sym] if float(b["t"]) >= since]
            cs = [shadow(r) for _, r in by_sym[sym]]
            C.resolve_reads(cs, {sym: mine}, today=today)
            for (s, _), c in zip(by_sym[sym], cs):
                calls[(s, sym)] = c
    live = []
    for s, rows in pending:
        outs = [outcome(r, calls[(s, r["s"])]) for r in rows if (s, r["s"]) in calls]
        old = _sessions_between(s, today) >= FINAL
        if outs and (old or all(o["status"] in TERMINAL for o in outs)):
            _write_gz(os.path.join(d, f"outcomes-{s}.json.gz"),
                      json.dumps({"as_of": s, "final": True, "rows": outs}, separators=(",", ":")))
            done += outs
        else:
            live += outs
    summary = summarize(done, live, names, today)
    write_json_atomic(os.path.join(d, "summary.json"), summary)
    return summary


def _sessions_between(a, b):
    """trading sessions after a up to and including b"""
    n, d, end = 0, cal._as_date(a), cal._as_date(b)
    while d < end:
        d = cal.next_trading_day(d)
        n += 1
    return n


def wilson(hits, n, z=Z95):
    """the 95% Wilson score interval of a proportion: (low, high), or None for n = 0"""
    if n <= 0:
        return None
    p = hits / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return round(mid - half, 3), round(mid + half, 3)


def stats(outs):
    """episodes, filled, closed, hits (a closed result over 0R), the hit rate with its Wilson interval, mean R with its
    standard error, and how many are still live"""
    closed = [o for o in outs if o["status"] == "closed" and o.get("outcome_r") is not None]
    rs = [float(o["outcome_r"]) for o in closed]
    hits = sum(1 for r in rs if r > 0)
    n = len(rs)
    mean = sum(rs) / n if n else None
    se = math.sqrt(sum((r - mean) ** 2 for r in rs) / (n - 1) / n) if n > 1 else None
    return {"episodes": len(outs), "filled": sum(1 for o in outs if o.get("filled")), "closed": n, "hits": hits,
            "hit_rate": round(hits / n, 3) if n else None, "hit_ci": wilson(hits, n),
            "mean_r": round(mean, 3) if mean is not None else None, "mean_r_se": round(se, 3) if se else None,
            "live": sum(1 for o in outs if o["status"] in ("waiting", "open"))}


def summarize(done, live, names, today):
    allo = done + live
    groups = {"all": stats(allo)}
    for key in ("source", "form", "take", "conviction", "code"):
        for val in sorted({str(o.get(key)) for o in allo}):
            groups[f"{key}:{val}"] = stats([o for o in allo if str(o.get(key)) == val])
    for val in sorted({k for o in allo for k in o.get("cautions") or ()}):     # each caution, forward
        groups[f"caution:{val}"] = stats([o for o in allo if val in (o.get("cautions") or ())])
    return {"as_of": str(today), "sessions": len(names), "first": names[0] if names else None,
            "final_episodes": len(done), "live_episodes": len(live), "groups": groups,
            "note": "Every roster read scored forward by the record's rules; an episode is a name's plan counted once "
                    "while it repeats; a hit is a closed result over 0R; intervals are 95%."}
