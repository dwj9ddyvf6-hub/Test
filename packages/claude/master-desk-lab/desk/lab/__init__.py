"""The Execution Lab: the forward test as an experiment on execution (docs/research/2026-10-18-lab/DESIGN.md).

Every completed session's stock / ETF entry signals (state/ledger.jsonl, desk/lab/record.py) are executed again under
the policies of desk/lab/policies.py on the cached bars that followed their decision times, beside a seeded placebo of
liquid genome names at the same times and beside the desk's real executions (desk/lab/facts.py); one immutable outcome
file per session and the analysis land in state/lab/ (desk/lab/store.py, desk/lab/report.py). Each signal row carries
`research.engine`, its name's analysis-engine screen row (desk/lab/research.py, read from state/analysis/), and `arms`,
the improvement arms' facts (desk/lab/arms.py: each a paired shadow variant with its contract and rejection rule).

The lab only measures and recommends: no sleeve, order, fill or book is touched, no network is read (bars come from the
hub cache_only), nothing outside state/lab/ is written. A session stays open (recomputed every run, its resolved
outcomes counted as provisional) until all its outcomes are final or it is MAX_AGE sessions old; then its file is
written once. The nightly job `lab` (desk/jobs.py) runs `run`; `build` takes explicit inputs (tests, a run over a
ledger's copy)."""
import csv
import os
import random
import time

from .. import calendar as cal
from ..util import iso, read_jsonl
from . import arms, facts, fidelity, funding, intraday, lazarus, options, policies, record, report, research, store
from .tape import Tape, in_session, nbo_source, session_for

LAB_VERSION = 1
RED_INDEXES = ("SPY", "QQQ")                # the red-day and fear-day entries' indexes (policies.py red5*, fear5*)
# a name's own index: QQQ for semis (memory included), tech and internet names, SPY for the rest. The sector proxy
# map is Author's (winners/code/mine.py), the one lc2's red-day rule used; the owner (2026-10-18): "the semi and
# memory and tech names usually follow QQQ". A 120-session return correlation was tried instead and is noise for
# most names (QQQ and SPY move together), so the map stays. The map files each name under the sector fund its daily
# returns tracked best since 2023-09 (winners/code/prep.py sector_tables), not by industry: the owner's rule is about
# the names, so the tech names it files elsewhere and the semi / tech funds it never mapped are listed here.
SECTOR_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "Author_research",
                          "winners", "out", "sector_proxy_map.csv")
QQQ_SECTORS = ("SMH", "XLK", "XLC")
QQQ_FAMILY = ("QQQ", "QQQM", "TQQQ", "QLD", "SMH", "SOXX", "SOXL", "XLK", "TECL", "XLC",
              "XSD", "PSI", "SOXQ", "USD", "FTEC", "IYW", "IGM", "FDN", "QTEC", "ONEQ", "ROM", "WCLD")
QQQ_NAMES = ("AAPL", "AMZN", "TSLA",              # the Magnificent Seven the map files under XLY
             "CHKP", "MNDY", "SHOP", "VTEX")      # software names the desk signalled, filed under XLF / XLY / none
SPY_FAMILY = ("SPY", "VOO", "IVV", "SPLG", "VTI", "SSO", "UPRO", "SPXL", "RSP", "DIA", "IWM", "TNA")  # broad funds
#                                                   are SPY's whatever the map says (SPY, VOO and VTI sit under XLK)
TREND_DAYS = 230                            # daily bars a signal's tape holds: its trend flag needs a 200-day average
WARMUP = 30                                 # sessions of the canonical store's bars kept before the first open session
#                                             (390 half hours: EMA20's seed weighs (19/21)^390, about 1e-17, after them)
SOURCE = "equity_split"                  # the hub resolves it: alpaca_split with keys (the host), else yahoo
MAX_AGE = 30                             # sessions: an open session is frozen at this age, unresolved rows as they are
SETTLE_S = 1800                          # a session is complete 30 minutes after its close
K_PLACEBO = 30
MIN_DV = 20e6                            # the placebo's liquidity: 20-session median dollar volume
DEADLINE_S = 150.0                       # past it no further symbol is evaluated (the job's 3-minute bound)
WHOLE = 100_000                          # bars: a cached series whole (the cache keeps at most 5,000 a series)
ROSTER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "universes", "old_desk",
                      "genome_universe_1838.txt")


def engine_of(row):
    """the manifest type, every Tensor type one engine (as the terminal counts agreement)"""
    t = (row or {}).get("type") or (row or {}).get("family") or "Unlisted"
    return "Tensor engine" if "tensor" in t.lower() else t


def class_of(sid):
    return "control" if sid.startswith("killed_") else "research" if sid.startswith("ro_") else "trading"


def declared(sleeves):
    """{sleeve: the finest interval of its declared bars}"""
    out = {}
    for s in sleeves:
        f = facts.finest(b.get("interval") for b in ((s.CONFIG.needs or {}).get("bars") or ()))
        if f:
            out[s.CONFIG.sleeve_id] = f
    return out


def roster(path=ROSTER):
    with open(path) as f:
        return list(dict.fromkeys(line.strip().upper() for line in f if line.strip() and not line.startswith("#")))


def last_complete(now):
    """the last session closed at least SETTLE_S before now"""
    d = cal._as_date(float(now))
    if not (cal.is_trading_day(d) and now >= cal.session_close(d) + SETTLE_S):
        d = cal.prev_trading_day(d)
    return d


def window(asof, first_at):
    """the sessions the lab may still evaluate: the last MAX_AGE + 1, none that closed before the ledger's first pass"""
    out, d = [], asof
    for _ in range(MAX_AGE + 1):
        if first_at is not None and cal.session_close(d) < first_at:
            break
        out.append(d.isoformat())
        d = cal.prev_trading_day(d)
    return sorted(out)


def run(engine, now):
    """the nightly job: the engine's root, its hub's resolution of equity_split, its sleeves' declared bars and their
    cadences (the option arm's passes)"""
    return build(engine.root, engine.hub, now, intervals=declared(engine.sleeves.values()),
                 cadences={s.CONFIG.sleeve_id: s.CONFIG.cadence_s for s in engine.sleeves.values()})


def cache_root(hub):
    """the directory holding the hub's bar cache and the canonical 1H store (<root>/cache), or None"""
    r = getattr(getattr(hub, "cache", None), "root", None)
    return os.path.dirname(r) if r else None


def build(root, hub, now, intervals=None, ledger=None, out_dir=None, names=None, deadline_s=DEADLINE_S,
          clock=time.monotonic, canonical=None, cadences=None):
    """canonical: the directory holding canonical/ (the roster's 1H store, desk/lab/intraday.py); default the hub's
    cache root. cadences: {sleeve: its pass cadence in seconds} (the option arm's passes; default 600)"""
    t_start = clock()
    canonical = canonical if canonical is not None else cache_root(hub)
    ledger = ledger or os.path.join(root, "state", "ledger.jsonl")
    out_dir = out_dir or store.lab_dir(root)
    manifest = {r["sleeve_id"]: r for r in read_jsonl(os.path.join(root, "config", "manifest", "sleeves.jsonl"))}
    asof = last_complete(now)
    first = record.first_at(ledger)
    sessions = window(asof, first) if first is not None else []
    done = store.written(out_dir)
    open_s = [d for d in sessions if d not in done]
    rows, wrote, notes, cut = {}, [], [], False
    if open_s:
        rec = record.read(ledger, cal.session_close(cal.prev_trading_day(open_s[0])))
        if rec.truncated:
            notes.append("the ledger read stopped at its byte cap before the window's start")
        recorded = {session_for(t) for t in rec.passes}
        live = [d for d in open_s if d in recorded]
        notes += [f"{d}: no pass recorded in its decision window" for d in open_s if d not in recorded]
        work = _work(rec, set(live), manifest, intervals or {})
        for sym, js in lazarus.jobs(rec, set(live), LAB_VERSION).items():      # FEED-05/06: every Lazarus fire
            work["jobs"].setdefault(sym, []).extend(("lazarus", j) for j in js)
        try:                                   # gate G1: the desk's own fills replayed on the decision tape
            replays = fidelity.replay_fills(root, rec, live)
        except Exception as e:                 # the gate's read never stops the lab
            replays = {}
            notes.append(f"fidelity: {type(e).__name__}: {str(e)[:120]}")
        cut = _evaluate(work, hub, now, asof, live, names, rows, t_start, deadline_s, clock, replays, canonical,
                        arms.Windows(root))
        screens = research.Screens(root)             # each signal row carries its name's screen (desk/lab/research.py)
        for r in (r for rs in rows.values() for r in rs if r["arm"] in ("signal", "placebo")):
            got = research.engine(r, screens)
            if r["arm"] == "signal":
                r["research"] = got
            e = got.get("engine") or {}                 # the HAR sizing arm's forecast, a placebo row's too
            r["arms"]["size"]["sigma"] = e.get("sigma_mean") if e.get("scored") else None
        for d, rs in options.option_rows(rec, root, live, cadences, LAB_VERSION).items():   # the option arms' rows
            rows.setdefault(d, []).extend(rs)
        if cut:
            notes.append("deadline: not every symbol was evaluated; no session was finalized this run")
        for d in live:
            rs = rows.get(d, [])
            if not cut and (all(_final(r) for r in rs) or cal.trading_days_between(d, asof) >= MAX_AGE):
                if store.write_once(out_dir, d, rs):
                    wrote.append(d)
    final = sorted(store.written(out_dir))
    still_open = [d for d in open_s if d not in final]
    all_rows = [r for d in final for r in store.read(out_dir, d)] + [r for d in still_open for r in rows.get(d, [])]
    meta = {"lab_version": LAB_VERSION, "at": iso(now), "asof": asof.isoformat(), "source": hub.resolve(SOURCE),
            "sessions": {"final": final, "open": still_open, "written_now": wrote}, "open_sessions": still_open,
            "deadline_hit": cut, "notes": notes, "wall_s": round(clock() - t_start, 2)}
    summ = report.summary(all_rows, manifest, meta)
    try:                                      # CRY-E2a: the funding signs side by side, logged, then reported
        funding.pair(root, now)
        summ["arms"]["cry_e2a_funding_signs"] = funding.report(funding.read(root))
    except Exception as e:                    # noqa: BLE001 - logging only: never the lab's
        notes.append(f"funding signs: {type(e).__name__}: {str(e)[:120]}")
    store.write_summary(out_dir, summ)
    ev = summ["evidence"]
    return {"asof": meta["asof"], "open": still_open, "written": wrote, "signals": ev["signals"],
            "resolved_reference": ev["resolved_reference"], "recommendations": len(summ["recommendations"]),
            "deadline_hit": cut, "wall_s": round(clock() - t_start, 2)}


def _work(rec, live, manifest, intervals):
    """the per-symbol jobs of the open sessions: their entry signals (the first emission of each sleeve, symbol, side
    and session) and their other intents (exit / target: freshness only, first emission likewise)"""
    idx = facts.Index(rec)
    sig, other = {}, {}
    for at, sid, it in rec.intents:
        d = session_for(at)
        if d not in live:
            continue
        k = (d, sid, it["symbol"], it["side"], it["kind"])
        (sig if it["kind"] == "enter" else other).setdefault(k, (at, sid, it))
    jobs = {}
    for (d, sid, sym, side, kind), (at, _, it) in sig.items():
        px, src = it.get("price"), "hint"
        if not px:
            made = idx.made_by(at, sid, sym, "enter")
            px, src = (made[0].get("ref"), "child_ref") if made else (None, None)
        row = manifest.get(sid) or {}
        jobs.setdefault(sym, []).append(("signal", {
            "v": LAB_VERSION, "session": d, "arm": "signal", "sleeve": sid, "class": class_of(sid),
            "engine": engine_of(row), "symbol": sym, "side": side, "decided_at": at, "key": it.get("key"),
            "px": px, "px_source": src, "own": facts.own_interval(intervals.get(sid), it.get("key"), it.get("reason")),
            "_reason": it.get("reason")}))
    for (d, sid, sym, side, kind), (at, _, it) in other.items():
        jobs.setdefault(sym, []).append(("intent", {
            "v": LAB_VERSION, "session": d, "arm": "intent", "kind": kind, "sleeve": sid, "class": class_of(sid),
            "engine": engine_of(manifest.get(sid)), "symbol": sym, "side": side, "decided_at": at,
            "key": it.get("key"), "px": it.get("price"), "_reason": it.get("reason"),
            "own": facts.own_interval(intervals.get(sid), it.get("key"), it.get("reason"))}))
    return {"jobs": jobs, "idx": idx, "signals": [j for v in jobs.values() for t, j in v if t == "signal"]}


def _draws(signals, liquid):
    """the seeded placebo: per session, K_PLACEBO liquid names at decision times drawn from that session's signals"""
    out = []
    for d in sorted({s["session"] for s in signals}):
        pool = sorted(liquid.get(d) or ())
        times = sorted(s["decided_at"] for s in signals if s["session"] == d)
        if not pool or not times:
            continue
        rng = random.Random(f"lab-placebo|v{LAB_VERSION}|{d}")
        for j, sym in enumerate(rng.sample(pool, min(K_PLACEBO, len(pool)))):
            out.append({"v": LAB_VERSION, "session": d, "arm": "placebo", "sleeve": "placebo", "class": "placebo",
                        "engine": "placebo", "symbol": sym, "side": "long", "key": f"placebo:{d}:{j}",
                        "decided_at": times[rng.randrange(len(times))], "px": None, "px_source": "last_close",
                        "own": None})
    return out


def _evaluate(work, hub, now, asof, live, names, rows, t_start, deadline_s, clock, replays=None, canonical=None,
              windows=None):
    """every open session's rows, one symbol at a time (one series in memory at once) -> True when the deadline cut
    it. A symbol with a decision inside a session its hub hourly bars do not cover reads the canonical 1H store too
    (EQ-06), once"""
    if not live:
        return False
    first = cal._as_date(live[0])
    n_days = cal.trading_days_between(cal.prev_trading_day(first, 25), asof) + 5
    n_hours, n_fine = 16 * (n_days - 20) + 32, 192 * (n_days - 20) + 192
    jobs, idx = work["jobs"], work["idx"]
    with_signals = sorted({s["session"] for s in work["signals"]})
    liquid = {}
    if with_signals:
        for sym in names if names is not None else roster():
            if clock() - t_start > deadline_s:
                return True
            tape = Tape(_series(hub, "1d", sym, n_days, now), until=now)
            for d in with_signals:
                dv = tape.median_dv(d)
                if dv is not None and dv >= MIN_DV:
                    liquid.setdefault(d, []).append(sym)
    for p in _draws(work["signals"], liquid):
        jobs.setdefault(p["symbol"], []).append(("placebo", p))
    since = cal.session_open(cal.prev_trading_day(first, WARMUP))     # the intraday series' start (a warm-up)
    ctx = {"red": {ix: red_sessions(Tape(_series(hub, "1d", ix, n_days, now), until=now)) for ix in RED_INDEXES},
           "qqq": _tape(hub, "QQQ", n_days, n_hours, n_fine, now, canonical, since),  # EQ-01's market control
           "spy": arms.closes(Tape(_series(hub, "1d", "SPY", max(n_days, TREND_DAYS), now), until=now)),  # beta63
           "windows": windows}                     # the entry windows the decision tape noted (the intraday arms)
    for sym in sorted(jobs):
        if clock() - t_start > deadline_s:
            return True
        tape = _tape(hub, sym, max(n_days, TREND_DAYS, arms.avoid.LISTING_DAYS), n_hours, n_fine, now, canonical, since)
        for t, j in jobs[sym]:
            if t == "lazarus":                          # a fire as a zero-capital entry (desk/lab/lazarus.py)
                j = lazarus.row(tape, j, policies.evaluate, {"nso_t20": policies.POLICIES["nso_t20"]})
                j["final"] = _final(j)
                rows.setdefault(j["session"], []).append(j)
                continue
            rows.setdefault(j["session"], []).append(_intent(tape, idx, j) if t == "intent" else
                                                     _row(tape, idx, j, ctx, replays))
    return False


def _tape(hub, sym, n_days, n_hours, n_fine, now, canonical=None, since=None):
    """one symbol's tape: the hub's cached daily, hourly and 5-minute bars, and the canonical 1H store's hours and
    half hours (desk/lab/intraday.py) where it holds the name, from `since` (WARMUP sessions before the first open
    session: the store keeps a year, the lab needs its open sessions and the pivot's EMA20 warm-up)"""
    got = intraday.canonical(canonical, sym, now, since) if canonical else None
    return Tape(_series(hub, "1d", sym, n_days, now), _series(hub, "1h", sym, n_hours, now),
                _series(hub, "5m", sym, n_fine, now), until=now, hourly_alt=(got or {}).get("1h") or (),
                m30=(got or {}).get("30m") or ())


def _series(hub, iv, sym, n, until):
    """the last n bars of a cached series stamped at or before `until` (a replay's cache may hold later ones; the tape
    then drops a bar not yet complete at `until`)"""
    bars = hub.bars(SOURCE, iv, [sym], WHOLE, cache_only=True).get(sym) or ()
    return [b for b in bars if float(b["t"]) <= until][-n:]


_SECTORS = {}


def own_index(sym):
    """the index a name follows: QQQ for the map's SMH / XLK / XLC names, the listed tech names and the QQQ family,
    else SPY"""
    if sym in SPY_FAMILY:
        return "SPY"
    if sym in QQQ_FAMILY or sym in QQQ_NAMES:
        return "QQQ"
    if not _SECTORS and os.path.exists(SECTOR_MAP):
        with open(SECTOR_MAP) as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0]:
                    _SECTORS[row[0]] = row[1]
    return "QQQ" if _SECTORS.get(sym) in QQQ_SECTORS else "SPY"


def red_sessions(tape):
    """the sessions an index closed below its previous close"""
    return {d[0] for a, d in zip(tape.days, tape.days[1:]) if d[6] < a[6]}


def _row(tape, idx, j, ctx=None, replays=None):
    t0, px, side = j["decided_at"], j["px"], j["side"]
    reason = j.pop("_reason", None)
    if j["arm"] == "placebo":
        last = tape.last_close(t0)
        px = j["px"] = None if last is None else round(last[0], 6)
    atr = tape.atr(t0)
    live = in_session(t0)
    hourly = bool(live) and tape.covers_hours(live)
    own = own_index(j["symbol"])
    win = arms.window(j, tape, (ctx or {}).get("windows")) if side == "long" else None
    outs = policies.evaluate(tape, t0, side, px, atr, hourly, tape.prev_close(t0), ctx=dict(ctx or {}, own=own),
                             window=win)
    nbo = outs["nbo_t5"]
    src, h1 = nbo_source(tape, t0)
    j.update(atr=None if atr is None else round(atr, 6), iv="1h" if hourly else "1d", outcomes=outs,
             ctx={"uptrend": tape.uptrend(t0), "index": own}, nbo_src=src, h1=h1)
    if win:
        j["window"] = {k: win[k] for k in ("session", "start", "end", "src")}
    if j["arm"] == "signal":
        cap = facts.capture(idx, j["sleeve"], j["symbol"], side, t0, j["session"], px, nbo.get("entry_px"))
        ex = (cap["fill_px"], cap["fill_at"]) if cap.get("filled") else (nbo.get("entry_px"), nbo.get("entry_at"))
        j["capture"] = cap
        j["fresh"] = facts.freshness(tape, t0, px, atr, j["own"], ex[0], ex[1], reason)
        rp = fidelity.for_signal(cap.get("fill_seqs"), replays or {}, atr)
        if rp:
            j["replay"] = rp
    j["arms"] = arms.facts(tape, j, ctx)              # the improvement arms' per-row facts (desk/lab/arms.py)
    j["id"] = "%s:%s:%s:%s:%s" % (j["session"], j["sleeve"], j["symbol"], j["side"], round(t0))
    j["final"] = _final(j)
    return j


def _intent(tape, idx, j):
    """an exit / target intent's price basis (its freshness only: it is no signal)"""
    at, reason = j["decided_at"], j.pop("_reason", None)
    made = idx.made_by(at, j["sleeve"], j["symbol"], j["kind"])
    j["px"] = j["px"] or (made[0].get("ref") if made else None)
    fills = idx.fills_of(made)
    ex = (idx.price(fills[0]), fills[0]["at"]) if fills else (None, None)
    j["fresh"] = facts.freshness(tape, at, j["px"], tape.atr(at), j["own"], ex[0], ex[1], reason)
    j["id"] = "%s:%s:%s:%s:%s" % (j["session"], j["sleeve"], j["symbol"], j["kind"], round(at))
    j["final"] = True
    return j


def _final(row):
    """every outcome final and, for a filled one, every MAE / MFE window complete"""
    for o in (row.get("outcomes") or {}).values():
        if o.get("state") not in ("done", "nodata"):
            return False
        if o.get("filled") and None in (o.get("mae") or []) + (o.get("mfe") or []):
            return False
    return True
