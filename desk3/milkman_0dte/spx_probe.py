"""The SPX 0DTE chain probe, adapted to muse-desk-v3 (PORT-ADAPT).

Source: Femto-lean branch milkman-0dte, desk/data/spx_probe.py,
sha256 2aa56969b48ce4f146f55736f77e3ff20d220efb318912eae0177d4b683e83ce
(program fetch manifest, group d_milkman). The vendored sleeve
(desk3/milkman_0dte/milkman_0dte.py, byte-exact) waits on this probe's
record: it stays inert with the named reason "SPX 0DTE chain not
available" until a complete record says SPX (or SPXW) lists today's
expiry with fresh two-sided quotes, and it never falls back to SPY
options or to a model.

Adaptations (the only ones, all forced by v3's own patterns):
  * Reads go through the desk's own producer functions
    (desk3.producers.fetch_option_contracts / fetch_option_snapshots,
    the verified Alpaca path every v3 options consumer uses) instead
    of Femto-lean's desk.venues.alpaca client; credentials resolve
    through desk3.run_live.credential_env, the desk's vault route.
  * The snapshot row builder is local (the source's
    desk.data.options._alpaca_row has no v3 counterpart). OCC parsing
    reuses desk3.producers._occ_fields.
  * One honest addition: every attempt counts `with_delta` — how many
    quoted rows carry a greek delta. On this account tier options
    snapshots are served feed=indicative, which carries NO greeks
    (feed=opra answers 403; FEED-WIRE-20261025), and the authored
    contract pick refuses rows without a delta. The probe's chain
    verdict stays exactly as authored; the delta gap is recorded,
    not papered over, and it is one of the two named reasons the
    sleeve is PARKED (see PROVENANCE.md).
  * The job is a module entrypoint (python3 -m
    desk3.milkman_0dte.spx_probe) instead of a Femto-lean desk/jobs.py
    registration, which v3 does not have; the once-a-session and
    regular-session-only rules are unchanged.

The record goes to state/probes/spx_0dte.json with the source's
schema: {"probe", "version", "status", "available", "underlying",
"expiry", "at", "session", "contracts", "snapshots", "quoted",
"fresh", "with_delta", "roots", "example", "attempts", "why", "runs"}.
"incomplete" means no underlying could be read: treated as not
available. Nothing in the record carries a key or account identifier.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

PROBE_VERSION = 1
PATH = os.path.join("state", "probes", "spx_0dte.json")
UNDERLYINGS = ("SPX", "SPXW")
MIN_QUOTED = 10
FRESH_S = 600.0
RUNS = 8
MAX_AGE_SESSIONS = 5            # a record older than this is stale
INERT = "SPX 0DTE chain not available"


# ------------------------------------------------------------------ util
def _iso(ts):
    return datetime.fromtimestamp(float(ts), ET).isoformat()


def _read_json(path, default):
    try:
        with open(path) as fh:
            doc = json.load(fh)
        return doc if isinstance(doc, dict) else default
    except (OSError, ValueError):
        return default


def _write_json_atomic(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, path)


def _is_rth(now):
    dt = datetime.fromtimestamp(float(now), ET)
    return dt.weekday() < 5 and dtime(9, 30) <= dt.time() < dtime(16, 0)


def _et_date(now):
    return datetime.fromtimestamp(float(now), ET).date().isoformat()


def _trading_days_between(a, b):
    """Weekday count from session a (exclusive) to b (inclusive);
    negative when b precedes a; None on unparseable input."""
    try:
        da, db = date.fromisoformat(a), date.fromisoformat(b)
    except (TypeError, ValueError):
        return None
    if da == db:
        return 0
    sign = 1
    if db < da:
        da, db, sign = db, da, -1
    n, d = 0, da
    while d < db:
        d = date.fromordinal(d.toordinal() + 1)
        if d.weekday() < 5:
            n += 1
    return sign * n


# ------------------------------------------------------------------ rows
def _row(under, occ, snap, now):
    """One snapshot -> the probe's row shape. Delta stays None when the
    feed carries no greeks (this tier): absent, never fabricated."""
    from desk3.producers import _occ_fields
    parsed = _occ_fields(occ or "")
    if parsed is None:
        raise ValueError(f"unparseable OCC: {occ!r}")
    right, expiry, strike = parsed
    q = (snap or {}).get("latestQuote") or {}
    t = q.get("t")
    try:
        t = datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        t = 0.0
    greeks = (snap or {}).get("greeks") or {}
    delta = greeks.get("delta")
    return {"symbol": occ, "underlying": under, "root": occ[:-15],
            "expiration": expiry, "type": right, "strike": strike,
            "bid": q.get("bp"), "ask": q.get("ap"),
            "delta": float(delta) if delta is not None else None,
            "t": float(t), "source": "alpaca_indicative"}


def evaluate(under, snaps, contracts, now):
    """One underlying's read -> its attempt line: contracts listed,
    snapshots read, two-sided quotes, fresh ones, how many carry a
    delta, and the quoted contract nearest the money by delta (else
    the middle strike). Identical verdict math to the source."""
    rows = []
    for occ, sn in (snaps or {}).items():
        try:
            rows.append(_row(under, occ, sn, now))
        except (ValueError, IndexError):
            continue
    quoted = [r for r in rows if r["bid"] and r["ask"]
              and r["bid"] > 0 and r["ask"] > 0]
    fresh = [r for r in quoted if now - r["t"] <= FRESH_S]
    with_delta = [r for r in quoted if r["delta"] is not None]
    roots = {}
    for r in rows:
        roots[r["root"]] = roots.get(r["root"], 0) + 1
    example = None
    if fresh:
        withd = [r for r in fresh if r["delta"] is not None]
        pick = min(withd, key=lambda r: (abs(abs(r["delta"]) - 0.5),
                                         r["symbol"])) if withd else \
            sorted(fresh, key=lambda r: (r["strike"], r["symbol"]))[len(fresh) // 2]
        example = {"symbol": pick["symbol"], "bid": pick["bid"],
                   "ask": pick["ask"], "t": _iso(pick["t"])}
    return {"underlying": under, "contracts": len(contracts or ()),
            "snapshots": len(rows), "quoted": len(quoted),
            "fresh": len(fresh), "with_delta": len(with_delta),
            "roots": roots, "example": example}


def probe(env, session, now, contracts_fetcher=None, snapshots_fetcher=None):
    """Read SPX, then SPXW when SPX lists nothing usable ->
    (the chosen attempt or None, all attempts)."""
    if contracts_fetcher is None or snapshots_fetcher is None:
        from desk3 import producers
        contracts_fetcher = contracts_fetcher or producers.fetch_option_contracts
        snapshots_fetcher = snapshots_fetcher or producers.fetch_option_snapshots
    ref = date.fromisoformat(session)
    attempts, chosen = [], None
    for under in UNDERLYINGS:
        try:
            contracts = contracts_fetcher(under, env, ref, max_dte=0) or []
            occs = [c.get("symbol") for c in contracts
                    if isinstance(c, dict) and c.get("symbol")]
            snaps = snapshots_fetcher(occs, env) if occs else {}
            a = evaluate(under, snaps, contracts, now)
        except Exception as e:
            a = {"underlying": under,
                 "error": f"{type(e).__name__}: {str(e)[:200]}"}
        attempts.append(a)
        if a.get("fresh", 0) >= MIN_QUOTED and chosen is None:
            chosen = a
            break
    return chosen, attempts


# ------------------------------------------------------------------ record
def read(root):
    return _read_json(os.path.join(root, PATH), {})


def availability(root, session):
    """(underlying symbol or None, reason or None): the record says
    today's chain (or a recent session's) is available. The reason
    always starts with the sleeve's named reason."""
    doc = read(root)
    if not doc or doc.get("version") != PROBE_VERSION:
        return None, INERT + ": the spx_chain_probe job has not recorded a result"
    if doc.get("status") != "complete" or not doc.get("available") \
            or not doc.get("underlying"):
        return None, INERT + ": " + str(
            doc.get("why") or "the probe recorded it unavailable")[:160]
    age = _trading_days_between(doc.get("session") or "1970-01-02", session)
    if age is None or age > MAX_AGE_SESSIONS or age < 0:
        return None, INERT + f": the probe record is from {doc.get('session')}, not a recent session"
    return str(doc["underlying"]), None


def done(root, session):
    """A complete result is recorded for `session` (not due again)."""
    doc = read(root)
    return doc.get("version") == PROBE_VERSION \
        and doc.get("status") == "complete" and doc.get("session") == session


def job(root, env=None, now=None):
    """Probe once now if this is the regular session and the desk's
    credential route answers; record the attempt either way."""
    now = time.time() if now is None else float(now)
    session = _et_date(now)
    doc = read(root)
    if doc.get("version") != PROBE_VERSION:
        doc = {"runs": doc.get("runs") or []}
    if done(root, session):
        return {"skipped": "a complete result is recorded for this session",
                "available": doc.get("available")}
    run = {"at": _iso(now), "session": session}
    why = None
    if not _is_rth(now):
        why = "outside the regular session (the chains' quotes are not live)"
    if why:
        run.update(status="not run", why=why)
    else:
        if env is None:
            from desk3.run_live import credential_env
            env = credential_env()
        chosen, attempts = probe(env, session, now)
        errors = [a for a in attempts if "error" in a]
        read_ok = len(errors) < len(attempts)
        if chosen:
            reason = None
        elif not read_ok:
            reason = "every read failed: " + "; ".join(
                a["error"] for a in errors)[:160]
        else:
            reason = "no two-sided fresh quotes for today's expiration (%s)" % ", ".join(
                "%s: %d contracts, %d quoted, %d fresh" % (
                    a["underlying"], a.get("contracts", 0),
                    a.get("quoted", 0), a.get("fresh", 0))
                for a in attempts if "error" not in a)
        best = chosen or next((a for a in attempts if "error" not in a), {})
        doc.update(probe="spx_0dte_chain", version=PROBE_VERSION,
                   status="complete" if read_ok else "incomplete",
                   available=(True if chosen else (False if read_ok else None)),
                   underlying=chosen["underlying"] if chosen else None,
                   expiry=session, at=_iso(now), session=session,
                   contracts=best.get("contracts"),
                   snapshots=best.get("snapshots"),
                   quoted=best.get("quoted"), fresh=best.get("fresh"),
                   with_delta=best.get("with_delta"),
                   roots=best.get("roots"), example=best.get("example"),
                   attempts=attempts, why=reason)
        run.update(status=doc["status"], available=doc["available"],
                   underlying=doc["underlying"])
    doc.setdefault("probe", "spx_0dte_chain")
    doc.setdefault("version", PROBE_VERSION)
    doc.setdefault("status", "incomplete")
    doc.setdefault("available", None)
    doc["runs"] = (list(doc.get("runs") or []) + [run])[-RUNS:]
    _write_json_atomic(os.path.join(root, PATH), doc)
    return {k: run.get(k) for k in ("status", "available", "underlying", "why")
            if run.get(k) is not None}


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(job(root))


if __name__ == "__main__":
    main()
