"""The decision tape: the live quotes around every stock / ETF decision, kept so that any execution timeline can be
replayed at the sim's own fidelity (docs/research/2026-10-18-lab/PROPOSALS.md section 2).

The sim fills a US equity from Alpaca's quote (IEX's top of book and last print) and the name's measured NBBO
half-spread (desk/engine.py _equity_touch, desk/venues/sim.py equity_touch). Bars cannot say what a passive order at
the mid, an entry 20 minutes later or a skip on a 1-ATR gap would have filled; the quotes the desk read can.

- watch:   an enter, target or exit intent on a US equity puts its symbol on the watch for WATCH_S (the desk's own
           state, so a restart keeps it).
- prefetch: the engine adds the watched symbols to the pass's one batched quote read of that source.
- record:  at the pass's end, every watched symbol the pass quoted appends its raw quote and the half-spread the spread
           book holds to state/lab/tape/<session>.jsonl:
           {"t": read time, "sym", "bid", "ask", "last", "q_t": the quote's stamp, "last_t": the print's stamp,
            "half_bps": the NBBO half-spread or null, "half_at": when it was measured}.
           The half-spread is kept whatever its age: SpreadBook.half_bps prices a fill on a stale measurement while a
           re-measure fails, and a fresh one replaces it in the book before the pass ends.
           A session's file is gzipped once a later session's first row is written, and is then never rewritten.
- replay:  touch / replay_market / replay_order price a tape row as the sim does (desk/runner.py: equity_touch on the
           quote, with the half-spread only beside a last print, then SimVenue's fill rule).
- windows: every US-equity enter intent's own order window, noted as the sleeve decides it (exp1, 2026-10-26: the
           intraday arms act "inside the sleeve's own entry window", and the ledger records no child's deadline). The
           note is the intent's OrderSpec as the sleeve wrote it: {"t": the pass's clock, "sym", "key", "side",
           "not_before", "not_after", "window_s"} (None for no order spec: the engine's default window then). The
           pass's record() appends the notes to state/lab/tape/windows/<the pass's ET date>.jsonl; windows() reads
           them. Nothing about the intent, its child or its order changes.
- options (OPT-08, AUDIT_OPT.md; exp1 2026-10-26): an option or package intent puts each decided contract (a package:
           every leg) on the option watch until its window ends (not_after, else the decision + window_s, else +
           WATCH_OPT_S). Each pass's record() appends, for every watched contract the pass read, the quote as the hub
           cached it: state/lab/tape/options/<session>.jsonl, {"t": the read time, "occ", "bid", "ask", "last", "q_t":
           the quote's own time, "src": its source, "iv", "delta"}. Cache-only like the equity rows: a contract no
           reader quoted this pass (no live child, no held position to mark) gets no row, and the gap is the
           record's (OPT-08's own rule counts it). CBOE's delayed quote as a second reference would need a fetch in
           the pass: not built.
- funding (CRY-E2a): record() also hands desk/lab/funding.py capture() the pass's clock, which keeps the Kraken
           funding prints the loop's own feed already holds (no fetch).

Nothing here fetches, changes an order or raises into the pass: the engine calls it under try/except."""
import gzip
import json
import os
import shutil

from ..venues.sim import SimVenue, equity_touch, session_floor

WATCH_S = 3600
MAX_WATCH = 600                      # a runaway sleeve cannot grow the pass's read
MAX_WINDOWS = 5000                   # window notes held between two records (a failing record cannot grow the state)
MAX_OPT_WATCH = 400                  # contracts on the option watch at once
WATCH_OPT_S = 6 * 3600               # an option decision's window when its order names none (the engine's default)
SOURCE = "alpaca"


def watch(state, intents, now):
    """put each US-equity decision's symbol on the watch, and note each enter intent's own order window; state is the
    desk's dict (persisted with the pass)"""
    w = state.setdefault("tape_watch", {})
    for i in intents or ():
        if i.kind in ("enter", "exit", "target") and i.asset == "equity" and not i.legs and "/" not in i.symbol:
            w[i.symbol] = float(now) + WATCH_S
            if i.kind == "enter":
                _note_window(state, i, now)
        elif i.kind in ("enter", "exit") and i.asset in ("option", "mleg"):
            _watch_option(state, i, now)
    if len(w) > MAX_WATCH:
        for s, _ in sorted(w.items(), key=lambda kv: kv[1])[:len(w) - MAX_WATCH]:
            del w[s]


def _note_window(state, i, now):
    o = i.order
    pend = state.setdefault("tape_windows", [])
    if len(pend) < MAX_WINDOWS:
        pend.append({"t": round(float(now), 6), "sym": i.symbol, "key": i.signal_key, "side": i.side,
                     "not_before": getattr(o, "not_before", None), "not_after": getattr(o, "not_after", None),
                     "window_s": getattr(o, "window_s", None)})


def _watch_option(state, i, now):
    o = i.order
    until = getattr(o, "not_after", None) or (float(now) + float(o.window_s) if getattr(o, "window_s", None) else
                                             float(now) + WATCH_OPT_S)
    w = state.setdefault("tape_opt_watch", {})
    for occ in ([l.symbol for l in i.legs] if i.asset == "mleg" else [i.symbol]):
        w[occ] = max(float(until), float(w.get(occ) or 0))
    if len(w) > MAX_OPT_WATCH:
        for s, _ in sorted(w.items(), key=lambda kv: kv[1])[:len(w) - MAX_OPT_WATCH]:
            del w[s]


def option_watching(state, now):
    """the contracts on the option watch now (expired ones leave it)"""
    w = state.get("tape_opt_watch") or {}
    for s in [s for s, until in w.items() if float(until) < float(now)]:
        del w[s]
    return sorted(w)


def options_dir(root):
    return os.path.join(tape_dir(root), "options")


def _record_options(root, hub, state, now, session, since):
    """append this pass's cached quotes of the watched contracts -> the number of rows"""
    get = getattr(hub, "cached_quote", None)
    occs = option_watching(state, now)
    if get is None or not occs or not session:
        return 0
    rows = []
    for occ in occs:
        q = get("options", occ)
        if not q or float(q.get("_at") or 0) < float(since):
            continue
        rows.append({"t": round(float(q["_at"]), 3), "occ": occ, "bid": q.get("bid"), "ask": q.get("ask"),
                     "last": q.get("last"), "q_t": q.get("t"), "src": q.get("source"), "iv": q.get("iv"),
                     "delta": q.get("delta")})
    if not rows:
        return 0
    d = options_dir(root)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{session}.jsonl")
    if not os.path.exists(path):
        _seal_older(d, session)
    with open(path, "a") as f:
        f.write("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows))
    return len(rows)


def option_rows(root, session):
    """a session's option tape rows, sealed or open"""
    d = options_dir(root)
    for name, opener in ((f"{session}.jsonl.gz", gzip.open), (f"{session}.jsonl", open)):
        p = os.path.join(d, name)
        if os.path.exists(p):
            with opener(p, "rt") as f:
                return [r for r in map(parse, f) if r is not None]
    return []


def windows_dir(root):
    return os.path.join(tape_dir(root), "windows")


def _flush_windows(root, state, session):
    """append the window notes of this pass to its session's file; the notes leave the state once written"""
    pend = state.get("tape_windows")
    if not pend or not session:
        return 0
    d = windows_dir(root)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{session}.jsonl"), "a") as f:
        f.write("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in pend))
    n = len(pend)
    state["tape_windows"] = []
    return n


def windows(root, session):
    """{(pass time to the millisecond, symbol, key): note} of one ET date's enter intents (the last note of a key)"""
    out = {}
    try:
        with open(os.path.join(windows_dir(root), f"{session}.jsonl")) as f:
            for line in f:
                r = parse(line)
                if r and r.get("sym"):
                    out[(round(float(r["t"]), 3), r["sym"], r.get("key") or "")] = r
    except OSError:
        pass
    return out


def watching(state, now):
    """the symbols on the watch now (expired ones leave it)"""
    w = state.get("tape_watch") or {}
    for s in [s for s, until in w.items() if float(until) <= float(now)]:
        del w[s]
    return sorted(w)


def tape_dir(root):
    return os.path.join(root, "state", "lab", "tape")


def _seal_older(d, session):
    """gzip every earlier session's file (once; the .jsonl goes only after its .gz is whole)"""
    for name in sorted(os.listdir(d)):
        if name.endswith(".jsonl") and name[:-len(".jsonl")] < session:
            src = os.path.join(d, name)
            tmp = src + ".gz.part"
            with open(src, "rb") as f, gzip.open(tmp, "wb") as g:
                shutil.copyfileobj(f, g)
            os.replace(tmp, src + ".gz")
            os.remove(src)


def record(root, hub, state, now, session, since):
    """append the quotes this pass read (since its start) for the watched symbols -> the number of rows written (the
    pass's window notes go to their own file first, whatever the quotes)"""
    try:
        _flush_windows(root, state, session)
    except OSError:                          # the notes stay for the next pass (bounded by MAX_WINDOWS)
        pass
    try:
        _record_options(root, hub, state, now, session, since)
    except OSError:
        pass
    try:                                     # CRY-E2a: the Kraken funding prints the loop's feed already holds
        from . import funding
        funding.capture(root, now)
    except Exception:                        # noqa: BLE001 - logging only: never the pass's
        pass
    get = getattr(hub, "cached_quote", None)
    syms = watching(state, now)
    if get is None or not syms or not session:
        return 0
    sp = getattr(hub, "spreads", None)
    spreads = sp.rows() if sp is not None and hasattr(sp, "rows") else {}
    rows = []
    for s in syms:
        q = get(SOURCE, s)
        if not q or float(q.get("_at") or 0) < float(since):
            continue
        sr = spreads.get(s) or {}
        rows.append({"t": round(float(q["_at"]), 3), "sym": s, "bid": q.get("bid"), "ask": q.get("ask"),
                     "last": q.get("last"), "q_t": q.get("t"), "last_t": q.get("last_t"),
                     "half_bps": sr.get("half_bps"), "half_at": sr.get("at")})
    if not rows:
        return 0
    d = tape_dir(root)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{session}.jsonl")
    if not os.path.exists(path):
        _seal_older(d, session)
    with open(path, "a") as f:
        f.write("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows))
    return len(rows)


def _path(root, session):
    """(path, opener) of a session's tape, sealed or open, or (None, None)"""
    d = tape_dir(root)
    for name, opener in ((f"{session}.jsonl.gz", gzip.open), (f"{session}.jsonl", open)):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p, opener
    return None, None


def has_tape(root, session):
    return _path(root, session)[0] is not None


def lines(root, session):
    """a session's raw lines, streamed"""
    p, opener = _path(root, session)
    if p is None:
        return
    with opener(p, "rt") as f:
        yield from f


def parse(line):
    """one row, or None for a line that does not parse (an open file's last line may be mid-write)"""
    try:
        return json.loads(line)
    except ValueError:
        return None


def read(root, session):
    """a session's rows, sealed or open"""
    return [r for r in map(parse, lines(root, session)) if r is not None]


def sim_touch(row, floor_bps=5.0, now=None):
    """the quote the desk's sim venue prices a fill on, for one tape row: desk/runner.py sim_equity_quote's
    equity_touch on the quote, with the name's half-spread only beside a last print, at `now` (default: the row's
    read time)"""
    q = {"bid": row.get("bid"), "ask": row.get("ask"), "last": row.get("last"), "t": row.get("q_t"),
         "last_t": row.get("last_t")}
    half = row.get("half_bps") if row.get("last") else None
    now = row["t"] if now is None else now
    return equity_touch(q, floor_bps, half, now, not_before=session_floor(now))


def touch(row, floor_bps=5.0, max_age_s=300.0, now=None):
    """the sim's equity touch on one tape row (sim_touch) where SimVenue would fill on it (two-sided, fresh) ->
    {"bid", "ask"} or None"""
    now = row["t"] if now is None else now
    t = sim_touch(row, floor_bps, now)
    try:
        bid, ask = float(t["bid"]), float(t["ask"])
    except (TypeError, KeyError, ValueError):
        return None
    if not (bid > 0 and ask >= bid) or now - float(t.get("t") or now) > max_age_s:
        return None
    return {"bid": bid, "ask": ask}


def replay_order(row, order, now, floor_bps=5.0, max_age_s=300.0):
    """an order the desk sent, replayed on a tape row: a SimVenue built as desk/runner.py builds the alpaca sim venue
    (no slip, no fee), its clock at `now`, its quote the row's sim_touch -> (fill price or None, why). order:
    {"symbol", "side", "qty", "limit_price" (None: market)}"""
    tch = sim_touch(row, floor_bps, now)
    v = SimVenue("sim:lab_replay", lambda s: tch, orders={}, fee_bps=0.0, max_quote_age_s=max_age_s,
                 clock=lambda: now)
    lim = order.get("limit_price")
    o = v.submit({"client_order_id": "replay", "symbol": order["symbol"], "side": order["side"],
                  "qty": order.get("qty") or 1, "type": "market" if lim is None else "limit", "limit_price": lim,
                  "time_in_force": "day"})
    if o.get("status") != "filled" or o.get("filled_avg_price") is None:
        return None, o.get("why") or "not filled"
    return float(o["filled_avg_price"]), ""


def replay_market(rows, sym, at, side, floor_bps=5.0, within_s=600.0):
    """a marketable order on sym routed at `at`, replayed: the first tape row of sym at or after `at` (within
    within_s) that the sim would fill on -> (price, the row's time), or None. A buy pays the touch's ask, a sell
    receives its bid (the sim's alpaca_equity venue: no slippage beyond the touch, no fee)"""
    for r in sorted((r for r in rows if r.get("sym") == sym and at <= r["t"] <= at + within_s), key=lambda r: r["t"]):
        tch = touch(r, floor_bps)
        if tch:
            return (tch["ask"] if side == "buy" else tch["bid"]), r["t"]
    return None
