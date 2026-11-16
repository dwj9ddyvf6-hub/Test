"""NIGHTLY-JOIN-ARTIFACTS-20261116: the one nightly forecast-ledger
plus bars join behind CONV-86 (LS7) and CONV-87 (LS8), and the
desk-readable artifact both rows were BLOCKED-ON-WIRING for.

CONV-86's register construction, verbatim in substance: "the join
runs nightly and writes its qualifying oversold joint-below calls
(union definition, Focus-bar symbols) to a desk-readable file; no
second join was built." CONV-87's LS8 macro-window conditioner arm
rides this same join: the window state is recorded on every joined
call and the next-night overnight return splits by window. There
is exactly one join in this module; the historical reproduction
and the forward accrual share every definition in it.

Definitions, reproduced exactly from the historical computation
(pass2/stack_work/run_stacks.py, LEAD-STACKING.md LS7/LS8):

- stack cell from the call's A05/A06 axis values: bull side is
  {bull_above, mixed_above}, below side is {mixed_below,
  bear_below} (the union definition: either stack's mixed_above
  counts as bull side); joint_below when BOTH axes are below
  side, joint_bull when both are bull side, else mixed.
- oversold: A03 == "oversold_lt30".
- window: A22 == "macro_named" is macro; A22 == "none_mentioned"
  is quiet; any other value carries no window state.
- next-night overnight of the called name: the first bar session
  strictly after the call date in that symbol's bar series; the
  overnight return is that session's open over the immediately
  preceding bar's close, minus 1 (the historical PER series
  construction, which required prev close, open and close all
  positive to carry a session).
- a call joins only when its symbol carries bars (historically:
  a Focus-bar symbol with a next session inside the bar span;
  forward: a symbol with a desk bar cache series). The historical
  yield was 42 of 201 graded forecast rows; the join prints its
  own yield every run and never invents a bar.

Historical proof (the blocker test pins it): on the original
inputs (retrospective_rows.jsonl + focus_bars.json) this module
reproduces the 6-row LS7 computation exactly: n=6, mean
+156.25bp, median +152.11bp, win 0.833, t 2.08; and the LS8
split: macro n=14 +34.01bp (t 2.34), quiet n=28 -60.40bp
(t -0.89).

Forward inputs: the book's forecast ledger
(~/workspace/midna-book/FORECAST-LOG.md), whose entries from
2026-11-16 carry one GESTALT-AXIS-TAGS v1 line per call
("- Tags <SYMBOL>: A03=<v> A05=<v> A06=<v> A22=<v> ..."), joined
to the desk bar cache (cache/bars/<SYM>/1Day.jsonl). Entries
before 2026-11-16 carry no tag lines and are never reconstructed
(rule 5 of the tag schema: values come from the read at write
time, never from a later reconstruction).

Writes (desk-readable, under state/nightly_join/):
- latest.json: every joined forward call with its stack cell,
  oversold flag, window state and next-night overnight (null
  until the next session's bar exists), the qualifying oversold
  joint-below subset named separately, the LS8 window split and
  the accrual counts the CONV-86/87 grader arms read.
- ledger.jsonl: one summary row per non-dry run.

Run:  python3 -m desk3.nightly_join [--dry-run]
      python3 -m desk3.nightly_join --historical-check
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from datetime import datetime, timezone

BULL_SIDE = {"bull_above", "mixed_above"}
BELOW_SIDE = {"mixed_below", "bear_below"}
OVERSOLD = "oversold_lt30"
WINDOW_MACRO = "macro_named"
WINDOW_QUIET = "none_mentioned"
FORWARD_START = "2026-11-16"
FRICTION_BP = 5.0

BOOK_FORECAST_LOG = os.path.expanduser(
    "~/workspace/midna-book/FORECAST-LOG.md")
HIST_RETRO = os.path.expanduser(
    "~/workspace/research_notes/alpha-hunt-chaos-20261115/"
    "retrospective_rows.jsonl")
HIST_BARS = os.path.expanduser(
    "~/workspace/research_notes/decisions-api-leverage-20261114/"
    "keepgoing2/wave3/focus_bars.json")


# ---------------------------------------------------------------- stats
def _tstat(vals):
    n = len(vals)
    if n < 2:
        return None
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    sd = math.sqrt(var)
    if sd <= 0:
        return None
    return round(float(mean / (sd / math.sqrt(n))), 2)


def summ_bp(vals):
    """The historical summ_bp, same rounding: returns are fractions
    in, bp out (mean/median rounded to 2, win to 3, t to 2)."""
    vals = list(vals)
    if not vals:
        return {"n": 0}
    srt = sorted(vals)
    n = len(srt)
    median = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2
    return {"n": n,
            "mean_bp": round(float(sum(vals) / n) * 1e4, 2),
            "median_bp": round(float(median) * 1e4, 2),
            "win": round(float(sum(1 for v in vals if v > 0) / n), 3),
            "t": _tstat(vals)}


# ------------------------------------------------------------ definitions
def stack_cell(a05, a06):
    """run_stacks.stack_cell, verbatim semantics."""
    if a05 is None or a06 is None:
        return None
    if a05 in BULL_SIDE and a06 in BULL_SIDE:
        return "joint_bull"
    if a05 in BELOW_SIDE and a06 in BELOW_SIDE:
        return "joint_below"
    return "mixed"


def window_state(a22):
    if a22 == WINDOW_MACRO:
        return "macro"
    if a22 == WINDOW_QUIET:
        return "quiet"
    return None


def overnight_series(bars):
    """run_stacks.series, verbatim semantics: {date: overnight}
    where overnight is that session's open over the previous
    bar's close, carried only when prev close, open and close
    are all positive."""
    out = {}
    rows = sorted(bars, key=lambda r: r["t"])
    for a, b in zip(rows[:-1], rows[1:]):
        if a["c"] > 0 and b["o"] > 0 and b["c"] > 0:
            out[b["t"]] = b["o"] / a["c"] - 1.0
    return out


def next_on(series_by_date, date):
    """run_stacks.next_on, verbatim semantics: the overnight of
    the first carried session strictly after `date`, else None."""
    later = [d for d in sorted(series_by_date) if d > date]
    if not later:
        return None
    return series_by_date[later[0]], later[0]


def join_calls(calls, bars_by_symbol):
    """The one join. `calls`: dicts with symbol, call_date, a03,
    a05, a06, a22. `bars_by_symbol`: {symbol: [bar rows with
    t/o/c]}. Returns (joined_rows, n_unjoined): a call joins iff
    its symbol carries bars and a next session exists inside the
    bar span (the historical join's exact yield rule)."""
    series = {s: overnight_series(b) for s, b in bars_by_symbol.items()}
    joined, unjoined = [], 0
    for c in calls:
        s = series.get(c["symbol"])
        hit = next_on(s, c["call_date"]) if s else None
        if hit is None:
            unjoined += 1
            continue
        val, next_date = hit
        row = dict(c)
        row["stack_cell"] = stack_cell(c.get("a05"), c.get("a06"))
        row["oversold"] = c.get("a03") == OVERSOLD
        row["window"] = window_state(c.get("a22"))
        row["next_date"] = next_date
        row["next_on"] = val
        row["next_on_bp"] = round(val * 1e4, 2)
        row["qualifying_ls7"] = bool(row["oversold"]
                                     and row["stack_cell"] == "joint_below")
        joined.append(row)
    return joined, unjoined


def ls7_stats(joined):
    return summ_bp([r["next_on"] for r in joined if r["qualifying_ls7"]])


def ls8_split(joined):
    macro = [r["next_on"] for r in joined if r["window"] == "macro"]
    quiet = [r["next_on"] for r in joined if r["window"] == "quiet"]
    out = {"macro": summ_bp(macro), "quiet": summ_bp(quiet)}
    if macro and quiet:
        out["split_bp"] = round(
            (sum(macro) / len(macro) - sum(quiet) / len(quiet)) * 1e4, 2)
    return out


# ------------------------------------------------------------- historical
def historical_calls(retro_path=HIST_RETRO):
    """The historical forecast corpus exactly as run_stacks read
    it: FORECAST rows with a graded outcome."""
    calls = []
    with open(retro_path) as fh:
        for line in fh:
            r = json.loads(line)
            if not r["source"].startswith("FORECAST"):
                continue
            if r.get("outcome_binary") is None:
                continue
            ax = r.get("axes") or {}
            def axv(a):
                return (ax.get(a) or {}).get("value")
            calls.append({"symbol": r["symbol"],
                          "call_date": r["call_date"],
                          "a03": axv("A03"), "a05": axv("A05"),
                          "a06": axv("A06"), "a22": axv("A22")})
    return calls


def historical_bars(bars_path=HIST_BARS):
    """All bar-carrying symbols in focus_bars.json: the 29 Focus
    names plus SPY and QQQ, whose series run_stacks' PER also
    carried (SPY calls join the historical corpus; excluding the
    benchmarks would change the LS8 counts, n=14/28)."""
    return json.load(open(bars_path))


def historical_check(retro_path=HIST_RETRO, bars_path=HIST_BARS):
    calls = historical_calls(retro_path)
    joined, unjoined = join_calls(calls, historical_bars(bars_path))
    return {"corpus_calls": len(calls), "joined": len(joined),
            "unjoined": unjoined,
            "ls7_x7": ls7_stats(joined), "ls8": ls8_split(joined),
            "qualifying_rows": [
                {k: r[k] for k in ("symbol", "call_date", "next_date",
                                    "next_on_bp")}
                for r in joined if r["qualifying_ls7"]]}


# ---------------------------------------------------------------- forward
_ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} ET")
_TAG_RE = re.compile(r"^- Tags ([^:]+): (.+)$")
_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


def forward_calls(log_path=BOOK_FORECAST_LOG, start=FORWARD_START):
    """Parse the book forecast ledger's tag lines. Only entries
    dated on/after `start` (the tag schema's first lawful date)
    and only tag lines whose subject is a bare symbol are name
    calls; index/sector subjects carry no single name to join."""
    calls = []
    if not os.path.exists(log_path):
        return calls
    date = None
    with open(log_path) as fh:
        for line in fh:
            m = _ENTRY_RE.match(line)
            if m:
                date = m.group(1)
                continue
            m = _TAG_RE.match(line.rstrip("\n"))
            if not m or date is None or date < start:
                continue
            subject = m.group(1).strip()
            if not _SYMBOL_RE.match(subject):
                continue
            tags = dict(re.findall(r"(A\d{2}|ORIGIN)=(\S+)",
                                   m.group(2)))
            calls.append({"symbol": subject, "call_date": date,
                          "a03": tags.get("A03"), "a05": tags.get("A05"),
                          "a06": tags.get("A06"), "a22": tags.get("A22"),
                          "origin": tags.get("ORIGIN")})
    return calls


def forward_bars(root):
    """Desk bar cache daily bars: {symbol: [{t, o, c}]} for every
    symbol carrying a 1Day cache file (the Focus-bar rule, on the
    desk's own served bars)."""
    out = {}
    cache = os.path.join(root, "cache", "bars")
    if not os.path.isdir(cache):
        return out
    for sym in sorted(os.listdir(cache)):
        path = os.path.join(cache, sym, "1Day.jsonl")
        if not os.path.exists(path):
            continue
        rows = []
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("o") is not None and r.get("c") is not None:
                    rows.append({"t": str(r["t"])[:10],
                                 "o": float(r["o"]), "c": float(r["c"])})
        if rows:
            out[sym] = rows
    return out


def forward_join(root, log_path=BOOK_FORECAST_LOG):
    """The forward join. Unlike the historical yield rule, a call
    whose next session has not happened yet is still written to
    the artifact (next_on null, state PENDING_NEXT_SESSION): the
    artifact is the accrual surface, and a qualifying call must be
    visible the night it is called, not only after it resolves.
    Calls on symbols with no bar series at all are counted as
    unjoined and named, never dropped silently."""
    calls = forward_calls(log_path)
    bars = forward_bars(root)
    series = {s: overnight_series(b) for s, b in bars.items()}
    rows, no_bars = [], []
    for c in calls:
        s = series.get(c["symbol"])
        if s is None:
            no_bars.append(c)
            continue
        hit = next_on(s, c["call_date"])
        row = dict(c)
        row["stack_cell"] = stack_cell(c.get("a05"), c.get("a06"))
        row["oversold"] = c.get("a03") == OVERSOLD
        row["window"] = window_state(c.get("a22"))
        row["qualifying_ls7"] = bool(row["oversold"]
                                     and row["stack_cell"] == "joint_below")
        if hit is None:
            row["next_date"] = None
            row["next_on"] = None
            row["next_on_bp"] = None
            row["state"] = "PENDING_NEXT_SESSION"
        else:
            val, next_date = hit
            row["next_date"] = next_date
            row["next_on"] = val
            row["next_on_bp"] = round(val * 1e4, 2)
            row["state"] = "RESOLVED"
        rows.append(row)
    resolved = [r for r in rows if r["state"] == "RESOLVED"]
    return {"calls_tagged": len(calls),
            "calls_no_bars": len(no_bars),
            "no_bars_symbols": sorted({c["symbol"] for c in no_bars}),
            "rows": rows,
            "qualifying": [r for r in rows if r["qualifying_ls7"]],
            "ls7_resolved": ls7_stats(resolved),
            "ls8_resolved": ls8_split(resolved)}


def run(root, dry_run=False, log_path=BOOK_FORECAST_LOG):
    ts = datetime.now(timezone.utc).isoformat()
    res = forward_join(root, log_path)
    doc = {"generated_at": ts, "join": "NIGHTLY-JOIN-ARTIFACTS-20261116",
           "forward_start": FORWARD_START, "friction_bp": FRICTION_BP,
           "source_forecast_log": log_path,
           "source_bars": os.path.join(root, "cache", "bars"),
           "calls_tagged": res["calls_tagged"],
           "calls_no_bars": res["calls_no_bars"],
           "no_bars_symbols": res["no_bars_symbols"],
           "qualifying_ls7_count": len(res["qualifying"]),
           "qualifying_ls7_resolved": res["ls7_resolved"].get("n", 0),
           "ls7": res["ls7_resolved"], "ls8": res["ls8_resolved"],
           "qualifying": res["qualifying"], "rows": res["rows"]}
    if not dry_run:
        out_dir = os.path.join(root, "state", "nightly_join")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "latest.json"), "w") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
        with open(os.path.join(out_dir, "ledger.jsonl"), "a") as fh:
            fh.write(json.dumps(
                {"ts": ts, "calls_tagged": doc["calls_tagged"],
                 "calls_no_bars": doc["calls_no_bars"],
                 "qualifying_ls7_count": doc["qualifying_ls7_count"],
                 "qualifying_ls7_resolved":
                     doc["qualifying_ls7_resolved"],
                 "ls8_macro_n": doc["ls8"]["macro"].get("n", 0),
                 "ls8_quiet_n": doc["ls8"]["quiet"].get("n", 0)},
                sort_keys=True) + "\n")
    lines = [f"NIGHTLY-JOIN {ts} (forward calls from {FORWARD_START})",
             f"  tagged calls={doc['calls_tagged']} "
             f"no-bars={doc['calls_no_bars']} "
             f"qualifying LS7={doc['qualifying_ls7_count']} "
             f"(resolved {doc['qualifying_ls7_resolved']})",
             f"  LS8 resolved: macro n={doc['ls8']['macro'].get('n', 0)} "
             f"quiet n={doc['ls8']['quiet'].get('n', 0)}"]
    return "\n".join(lines), doc


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if "--historical-check" in argv:
        print(json.dumps(historical_check(), indent=1, sort_keys=True))
        return 0
    text, _doc = run(root, dry_run="--dry-run" in argv)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
