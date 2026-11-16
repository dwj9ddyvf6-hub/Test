"""tensor_daily20 rows producer (TENSOR-DAILY20-PHASE2-20261031).

Stands up the archive's frozen-v690 Tensor state-repair pipeline
(Ausar handoff source/backend/tensor_engine.py
extract_native_feature_rows + tensor_daily_models validator) as a
desk data producer: builds canonical daily tapes for the 1,817
anchored symbols, computes the native feature rows, verifies them,
and persists a rows store + manifest under state/daily20/.

Verification standard: PIPELINE-CONSTRUCTION PARITY (Midna ruling
2026-10-31 22:04 ET, amending ruling A). The pipeline computation
is proven exact — over the preserved AMD fixture tape it reproduces
the archive bit-for-bit (0 field diffs vs the sealed R11 exporter;
max abs diff 0.0 vs the C01 ledger oracle; the packed-CSV anchor
hash reproduces exactly). Per-symbol anchor hashes against the
frozen archive are NOT the gate: the archive froze Yahoo daily
chart data as of late September 2026 and Yahoo has since revised
it (proven on the AMD control: a fresh pull differs from the
archive in exactly the final bar's revised volume), so fresh-pull
anchor matching is unattainable from live data — a property of the
source, not of this pipeline. Each manifest entry therefore records
the computed prefix hash BESIDE the anchor hash and the match flag,
honestly, plus tape provenance. Symbols whose tape cannot be
constructed to the anchor's shape (origin / terminal-ordinal
conservation) are EXCLUDED BY NAME in the manifest, never fudged.

Tape delta finding (Phase 2, 2026-10-31): Yahoo's in-window date
set equals the true NYSE session set exactly (verified against a
full holiday calendar on sampled symbols), yet the archive's
original_rows is exactly ONE LESS than the session count for ~90%
of the basket: the archive's input preparation omitted one real
session bar for those symbols (the ABNB class from Phase 1, shown
there to be a bar null at pull time and later backfilled). Which
bar was omitted is not derivable from any record on this box, and
guessing it would be fabrication. Under the parity standard the
store therefore builds over the TRUE complete tape and records the
per-symbol tape_delta_vs_anchor (0 or +1) in the manifest; the
archive validator's row-level invariants (columns, symbol, ordinal,
origin, strictly increasing clocks, completeness) must all pass,
and only its terminal-ordinal COUNT conservation may differ, by
exactly the recorded delta. Symbols with any other shape
divergence (origin mismatch, delta outside {0, +1}, missing
terminal bar) are excluded by name. The desk consumer
(aster_batch16._d20_decision) checks origin, ordinals and columns
— all conserved here — and does not check the archive count.

Tape source: Yahoo Finance daily chart data (identified float-for-
float in Phase 1; Alpaca SIP and the DEEP panel are NOT the archive
source). Bar clocks: timestamp = Yahoo bar epoch (09:30 ET open);
completed_at = usable_at = session close (16:00 ET, 13:00 ET on
early-close days: day after Thanksgiving, Jul 3, Dec 24 — the rule
reproduces the fixture's 21 early closes exactly). AMD's original
window is taken from the archive's preserved fixture tape (proven
byte-identical to the archive tape) with fresh Yahoo bars appended
after the anchor's last timestamp.

This module is a DATA PRODUCER ONLY. It never touches the desk's
pinned v698 Tensor engine (vendor/), core/tensor_feeds.py, any
sleeve, or the bundle file. Serving the store through the cycle
snapshot is a separate step (see the program record): the full
rows map is ~4.5 GB as JSON and cannot ride the per-cycle snapshot
on this box; the store is built and verified here regardless, and
the serve state stays named in health until that lands.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF_BACKEND = ("/home/hatch/workspace/.scratch-ausar-archive/"
                   "handoff-20261024/source/backend")
HANDOFF_FIXTURE = ("/home/hatch/workspace/.scratch-ausar-archive/"
                   "handoff-20261024/source/strategies/"
                   "tensor_state_repair/engine/fixtures/"
                   "AMD-1d-completed.json")
ANCHORS_PATH = os.path.join(ROOT, "desk3", "aster_d20_assets",
                            "DAILY_SOURCE_ANCHORS.json")
STORE_DIR_NAME = "daily20"
ROWS_HASH_MJS = os.path.join(ROOT, "desk3", "daily20_rows_hash.mjs")
PARITY_REFERENCE = ("Phase 1 sample proof, "
                    "research_notes/tensor-daily20-pipeline-20261031/"
                    "BUILD-REPORT.md: pipeline exact (0 field diffs vs "
                    "sealed R11 exporter over 330 bars; max abs diff "
                    "0.0 vs C01 ledger oracle over 2,513 AMD rows); "
                    "anchor contract sha256(Node-zlib gzip level 4 "
                    "mtime 0 of exporter CSV) reproduced exactly on "
                    "AMD from its preserved fixture tape")
YAHOO_CAVEAT = ("Anchor hashes were frozen from Yahoo daily chart "
                "data as of late September 2026; Yahoo has since "
                "revised that data (final-bar preliminary volumes "
                "and rare interior backfills), so per-symbol anchor "
                "hash matching from live pulls is unattainable. "
                "Verification is by pipeline-construction parity "
                "(the AMD standard) per the 2026-10-31 22:04 ET "
                "ruling; each entry's anchor_match flag is recorded "
                "as observed, never forced.")


def _anchors():
    return json.load(open(ANCHORS_PATH))["symbols"]


def _handoff():
    if HANDOFF_BACKEND not in sys.path:
        sys.path.insert(0, HANDOFF_BACKEND)
    import tensor_engine as te
    import tensor_daily_models as tdm
    return te, tdm


# ------------------------------------------------------------------ clocks
def _thanksgiving(year):
    d = date(year, 11, 1)
    return d + timedelta(days=(3 - d.weekday()) % 7 + 21)


def session_len_s(t):
    """Session length in seconds for the bar epoch t (09:30 ET):
    12600 on early-close days, else 23400 (Phase 1 proven rule)."""
    d = datetime.fromtimestamp(t, ET).date()
    early = (d == _thanksgiving(d.year) + timedelta(days=1)
             or (d.month == 7 and d.day == 3)
             or (d.month == 12 and d.day == 24))
    return 12600 if early else 23400


# ------------------------------------------------------------------ tapes
class TapeShapeError(ValueError):
    pass


def _yahoo_pull(symbol, p1, p2):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol, safe="")
           + f"?period1={p1}&period2={p2}&interval=1d&events=div,splits")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as fh:
        chart = json.load(fh)
    res = chart["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(ts):
        o, h, l, c, v = (q["open"][i], q["high"][i], q["low"][i],
                         q["close"][i], q["volume"][i])
        if None in (o, h, l, c, v):
            continue  # preparation dropped null bars (Phase 1 proof)
        out.append((int(t), o, h, l, c, v))
    return out


def build_tape(symbol, anchor, now_ts=None):
    """Canonical daily tape [(ts, o, h, l, c, v), ...] from the
    anchor origin through the last completed session, plus its
    provenance and tape_delta_vs_anchor (in-window bars minus the
    archive's original_rows; 0 or +1 per the Phase 2 finding).
    Raises TapeShapeError on any other shape divergence."""
    now_ts = now_ts or time.time()
    raw = _yahoo_pull(symbol, anchor["first_timestamp"] - 10 * 86400,
                      int(now_ts) + 86400)
    if symbol == "AMD" and os.path.exists(HANDOFF_FIXTURE):
        fixture = json.load(open(HANDOFF_FIXTURE))["bars"]
        orig = [(int(b["timestamp_ms"] // 1000), b["open"], b["high"],
                 b["low"], b["close"], b["volume"]) for b in fixture]
        appends = [r for r in raw if r[0] > anchor["last_timestamp"]]
        tape = orig + appends
        provenance = "preserved_fixture+yahoo_appends"
    else:
        tape = [r for r in raw if r[0] >= anchor["first_timestamp"]]
        provenance = "yahoo_chart_daily"
    # completed sessions only: session close must be <= now
    tape = [r for r in tape if r[0] + session_len_s(r[0]) <= now_ts]
    if not tape or tape[0][0] != anchor["first_timestamp"]:
        raise TapeShapeError(
            f"origin: first bar {tape[0][0] if tape else None} != "
            f"anchor {anchor['first_timestamp']}")
    n = anchor["original_rows"]
    in_window = [r for r in tape if r[0] <= anchor["last_timestamp"]]
    delta = len(in_window) - n
    if delta not in (0, 1):
        raise TapeShapeError(
            f"tape delta: in-window bars={len(in_window)} "
            f"anchor original_rows={n} delta={delta}")
    if in_window[-1][0] != anchor["last_timestamp"]:
        raise TapeShapeError(
            f"terminal bar: last in-window {in_window[-1][0]} != "
            f"anchor {anchor['last_timestamp']}")
    return tape, provenance, delta


def _bars(tape):
    return [{"timestamp_ms": t * 1000,
             "completed_at_ms": (t + session_len_s(t)) * 1000,
             "usable_at_ms": (t + session_len_s(t)) * 1000,
             "open": o, "high": h, "low": l, "close": c,
             "volume": float(v)} for (t, o, h, l, c, v) in tape]


# ------------------------------------------------------------------ compute
def compute_rows(symbol, tape):
    te, _tdm = _handoff()
    bars = _bars(tape)
    hist = te.extract_native_feature_rows(
        symbol, "1d", bars, bars[-1]["usable_at_ms"],
        timeout_seconds=280)
    return list(hist.rows)


def _packed_sha256(rows, tmp_dir):
    rp = os.path.join(tmp_dir, "prefix_rows.json")
    with open(rp, "w") as fh:
        json.dump(rows, fh)
    out = subprocess.run(["node", ROWS_HASH_MJS, rp],
                         capture_output=True, text=True, timeout=180)
    if out.returncode != 0:
        raise RuntimeError(f"rows_hash failed: {out.stderr[:300]}")
    return json.loads(out.stdout)["packedSha256"]


def verify_symbol(symbol, anchor, tape, rows, tmp_dir, delta):
    """Parity-standard verification of one symbol's computed rows:
    archive validator over the full history + packed hash of the
    original prefix recorded beside the anchor hash. For delta=1
    symbols the validator's terminal-ordinal COUNT conservation is
    the one check that may fail (the archive tape omitted a bar;
    see the module docstring) — every row-level invariant precedes
    it in the validator, so reaching that exact failure proves the
    rest passed. Any other validator failure raises."""
    _te, tdm = _handoff()
    bars = _bars(tape)
    validator = "PASS"
    try:
        tdm._validate_history(symbol, rows, bars[-1]["usable_at_ms"],
                              tdm.anchor_for(symbol))
    except Exception as e:
        if delta == 1 and "endpoint ordinal differs" in str(e):
            validator = f"PASS_WITH_TAPE_DELTA: {e}"
        else:
            raise
    n = anchor["original_rows"]
    packed = _packed_sha256(rows[:n], tmp_dir)
    return {"archive_validator": validator,
            "prefix_packed_sha256": packed,
            "anchor_match": packed == anchor["native_feature_sha256"]}


def amd_parity_evidence():
    """The construction-parity proof, runnable on demand: pipeline
    over the preserved AMD fixture tape reproduces the anchor hash."""
    anchor = _anchors()["AMD"]
    fixture = json.load(open(HANDOFF_FIXTURE))["bars"]
    tape = [(int(b["timestamp_ms"] // 1000), b["open"], b["high"],
             b["low"], b["close"], b["volume"]) for b in fixture]
    rows = compute_rows("AMD", tape)
    _te, tdm = _handoff()
    try:
        tdm._validate_history("AMD", rows, tape[-1][0] * 1000
                              + session_len_s(tape[-1][0]) * 1000,
                              tdm.anchor_for("AMD"))
        validator = "PASS"
    except Exception as e:  # named, never hidden
        validator = f"FAIL: {e}"
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        packed = _packed_sha256(rows, td)
    return {"symbol": "AMD", "rows": len(rows),
            "packed_sha256": packed,
            "anchor_native_feature_sha256":
                anchor["native_feature_sha256"],
            "archive_validator_prefix": validator}


# ------------------------------------------------------------------ store
def store_dir(root=None):
    return os.path.join(root or ROOT, "state", STORE_DIR_NAME)


def _build_one(symbol, anchor, sdir, tmp_dir):
    tape, provenance, delta = build_tape(symbol, anchor)
    rows = compute_rows(symbol, tape)
    ev = verify_symbol(symbol, anchor, tape, rows, tmp_dir, delta)
    rows_dir = os.path.join(sdir, "rows")
    os.makedirs(rows_dir, exist_ok=True)
    path = os.path.join(rows_dir, symbol + ".json.gz")
    tmp = path + ".tmp"
    with gzip.open(tmp, "wt") as fh:
        json.dump(rows, fh)
    os.replace(tmp, path)
    return {"symbol": symbol, "status": "built",
            "tape_source": provenance,
            "tape_delta_vs_anchor": delta,
            "pull_date_utc": datetime.now(timezone.utc).date().isoformat(),
            "rows": len(rows),
            "original_rows": anchor["original_rows"],
            "first_timestamp": anchor["first_timestamp"],
            "last_timestamp": int(rows[-1]["timestamp"]),
            "prefix_packed_sha256": ev["prefix_packed_sha256"],
            "anchor_native_feature_sha256":
                anchor["native_feature_sha256"],
            "anchor_match": ev["anchor_match"],
            "archive_validator": ev["archive_validator"]}


def build_store(root=None, symbols=None, workers=3, build_id=None):
    """Resumable full-basket build. Per-symbol results append to
    state/daily20/build_ledger.jsonl as they land; symbols already
    built under this build_id with their rows file present are
    skipped. The manifest is (re)written from the ledger at the
    end of every run, complete or partial (built_at is stamped
    only when every anchored symbol is accounted for)."""
    from concurrent.futures import ProcessPoolExecutor, as_completed
    # Parent-side engine import is load-bearing (2026-11-02 incident,
    # BUGLOG_2026-11-02 D20-POOL-BREAK): pool workers raise
    # tensor_engine.TensorEngineError on bad tapes, and this parent
    # process must unpickle those exceptions off the result pipe.
    # _handoff() puts HANDOFF_BACKEND on sys.path and imports the
    # engine here; without it the module is unimportable in the
    # parent, the executor's result thread dies on the first engine
    # error, and every pending future is reported BrokenProcessPool
    # (the 2026-11-02 rebuilds lost 1,808 of 1,817 symbols this way
    # while each symbol built fine in-process).
    _handoff()
    root = root or ROOT
    sdir = store_dir(root)
    os.makedirs(os.path.join(sdir, "rows"), exist_ok=True)
    anchors = _anchors()
    want = symbols or sorted(anchors)
    build_id = build_id or datetime.now(timezone.utc).strftime(
        "parity-%Y%m%d")
    ledger_path = os.path.join(sdir, "build_ledger.jsonl")
    done = {}
    if os.path.exists(ledger_path):
        for line in open(ledger_path):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("build_id") == build_id:
                done[e["symbol"]] = e
    todo = []
    for s in want:
        e = done.get(s)
        if e and e.get("status") == "built" and os.path.exists(
                os.path.join(sdir, "rows", s + ".json.gz")):
            continue
        if e and e.get("status") == "excluded":
            continue
        todo.append(s)
    results = dict(done)

    def _run_pool(todo_syms):
        out = {}
        if not todo_syms:
            return out
        # D20-POOL-FALLBACK-20261104: submit in waves of 64 with a
        # FRESH executor per wave, so one hard worker death breaks
        # at most one wave instead of the whole run (the
        # 2026-11-02 disaster: a single pool, 1,808 of 1,817
        # symbols mass-excluded as BrokenProcessPool). A broken
        # wave's uncollected symbols fall back to serial in-process
        # builds with the same ledger accounting; per-symbol
        # failures stay named per symbol either way.
        from concurrent.futures.process import BrokenProcessPool
        WAVE = 64
        with open(ledger_path, "a") as lf:
            def _record(e):
                e["build_id"] = build_id
                out[e["symbol"]] = e
                lf.write(json.dumps(e) + "\n")
                lf.flush()
                if e.get("status") == "built":
                    shutil.rmtree(os.path.join(sdir, "tmp",
                                               e["symbol"]),
                                  ignore_errors=True)

            def _named(s, exc):
                if isinstance(exc, TapeShapeError):
                    return {"symbol": s, "status": "excluded",
                            "reason": f"tape_shape: {exc}"}
                return {"symbol": s, "status": "error",
                        "reason": f"{type(exc).__name__}: {exc}"}

            for start in range(0, len(todo_syms), WAVE):
                wave = todo_syms[start:start + WAVE]
                collected = {}
                try:
                    with ProcessPoolExecutor(
                            max_workers=workers) as ex:
                        futs = {}
                        for s in wave:
                            td = os.path.join(sdir, "tmp", s)
                            os.makedirs(td, exist_ok=True)
                            futs[ex.submit(_build_one, s, anchors[s],
                                           sdir, td)] = s
                        for fut in as_completed(futs):
                            s = futs[fut]
                            try:
                                collected[s] = fut.result()
                            except BrokenProcessPool:
                                raise
                            except Exception as exc:
                                collected[s] = _named(s, exc)
                except BrokenProcessPool:
                    pass  # uncollected symbols fall back below
                for s in wave:
                    if s in collected:
                        _record(collected[s])
                        continue
                    td = os.path.join(sdir, "tmp", s)
                    os.makedirs(td, exist_ok=True)
                    try:
                        e = _build_one(s, anchors[s], sdir, td)
                    except Exception as exc:
                        e = _named(s, exc)
                    _record(e)
        return out

    results.update(_run_pool(todo))
    # one retry pass over transient errors; a symbol still failing
    # is excluded BY NAME with its error as the reason, so the
    # manifest accounting is complete and honest.
    retry = [s for s, e in results.items()
             if e.get("status") == "error" and s in want]
    if retry:
        second = _run_pool(retry)
        for s, e in second.items():
            if e["status"] == "error":
                e = {"symbol": s, "status": "excluded",
                     "reason": f"unavailable_after_retry: {e['reason']}",
                     "build_id": build_id}
                with open(ledger_path, "a") as lf:
                    lf.write(json.dumps(e) + "\n")
            results[s] = e
    accounted = {s: results[s] for s in anchors if s in results}
    complete = len(accounted) == len(anchors) and all(
        e["status"] in ("built", "excluded") for e in accounted.values())
    manifest = {
        "schema": "tensor-daily20-rows-store/1",
        "verification_standard": "pipeline-construction-parity",
        "parity_reference": PARITY_REFERENCE,
        "yahoo_revision_caveat": YAHOO_CAVEAT,
        "pipeline": {"engine": HANDOFF_BACKEND + "/tensor_engine.py",
                     "transport": "frozen-v690 closure (Node), "
                                  "manifest-verified by the adapter"},
        "build_id": build_id,
        "complete": complete,
        "symbols": accounted,
    }
    if complete:
        manifest["built_at"] = datetime.now(timezone.utc).isoformat()
    mtmp = os.path.join(sdir, "manifest.json.tmp")
    with open(mtmp, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    os.replace(mtmp, os.path.join(sdir, "manifest.json"))
    return manifest


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=None,
                    help="comma-separated subset (default: full basket)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--build-id", default=None)
    a = ap.parse_args()
    syms = a.symbols.split(",") if a.symbols else None
    m = build_store(symbols=syms, workers=a.workers,
                    build_id=a.build_id)
    built = sum(1 for e in m["symbols"].values() if e["status"] == "built")
    excl = sum(1 for e in m["symbols"].values()
               if e["status"] == "excluded")
    err = sum(1 for e in m["symbols"].values() if e["status"] == "error")
    print(json.dumps({"complete": m["complete"], "built": built,
                      "excluded": excl, "errors": err,
                      "accounted": len(m["symbols"])}))
