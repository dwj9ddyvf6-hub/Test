#!/usr/bin/env python3
"""Per-name options tape collector (G6 cure, 2026-10-29).

The index tape (morgue/tape_card.py) covers SPY, QQQ and IWM only
because its universe is a constant. This collector records the same
kind of per-session tape picture for a BOUNDED watchlist universe:
the 50 tracked names carried by the Insider Wire record plus the
three index ETFs, read from that record at run time, never a second
hand-kept list.

Source: Alpaca v1beta1 options trades, the same print source the
index tape uses (chain, spot and 52-week range via morgue/map_gex
and morgue/tape_card helpers; heat and tags via morgue/tape.py, the
published scoring rule, unchanged).

Direction honesty (G7 print-time-quote fix, applied at the source
for this lane): Alpaca's historical options quotes endpoint returns
404 (proven 2026-10-29), so no print-time quote exists on hand, and
the TastyTrade DXLink stream refuses the TimeAndSales event type on
this entitlement ("Event types were requested but they are not
available: TimeAndSales", streamer level "api", proven 2026-10-29).
This lane therefore NEVER judges a print's side against a later
quote: every print's direction is stored as "unjudged" with the
reason named, net premium is stored as null (not zero), and only
gross premium, volume, heat and tags are published. The index tape's
older latest-quote join keeps its own labelled approximation; this
lane does not inherit it.

Store: ~/workspace/morgue/state/morgue/pername_tape/<SESSION>.json
(one document per session, written atomically) plus one manifest
line per run in <store>/manifest.jsonl (ok or error, never silent).
Completeness is declared per name exactly as the index tape
declares it: prints examined, contracts in scope, batches capped
(totals are a floor when capped).

Usage: python3 collect_pername_tape.py [SYM ...]
With no arguments the full bounded universe runs. A full-market
signed tape is a licensed product and is NOT attempted: that is the
named SOURCE_LIMIT remainder of G6.
"""

import json
import os
import sys
import tempfile
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
sys.path.insert(0, MORGUE)
sys.path.insert(0, os.path.expanduser(
    "~/workspace/custom-skills/local-alpaca-paper/bin"))

import tape as tape_mod  # noqa: E402
import tape_card  # noqa: E402
import map_gex  # noqa: E402

STORE_DIR = os.path.expanduser(
    "~/workspace/morgue/state/morgue/pername_tape")
INSIDER_PATH = os.path.join(HERE, "insider-wire", "data.json")
INDEX_ETFS = ["SPY", "QQQ", "IWM"]
MAX_DTE = 45
DIRECTION_BASIS = "unjudged_no_print_time_quote"
DIRECTION_REASON = (
    "no print-time quote source exists on hand: Alpaca historical "
    "options quotes return 404 and the DXLink stream refuses the "
    "TimeAndSales event type on this entitlement, so side is never "
    "judged against a later quote")


def bounded_universe():
    """The tracked 50 from the Insider Wire record plus the ETFs."""
    names = []
    if os.path.exists(INSIDER_PATH):
        doc = json.load(open(INSIDER_PATH, encoding="utf-8"))
        for n in doc.get("names") or []:
            sym = n.get("symbol")
            if sym and sym not in names:
                names.append(sym)
    for sym in INDEX_ETFS:
        if sym not in names:
            names.append(sym)
    return names


def score_name(underlying, session, now):
    """One name's tape picture for the session. Pure shaping over
    tape_card's fetchers; direction unjudged by construction."""
    from datetime import timedelta
    chain_all = map_gex.fetch_chain(underlying)
    horizon = (date.fromisoformat(session)
               + timedelta(days=MAX_DTE)).isoformat()
    chain = [c for c in chain_all if c["expiry"] <= horizon]
    by_sym = {c["symbol"]: c for c in chain}
    spot = map_gex.fetch_spot(underlying)
    hi52, lo52 = tape_card.fetch_52wk(underlying)
    start_iso = session + "T13:30:00Z"
    prints, capped = tape_card.fetch_trades(
        [c["symbol"] for c in chain], start_iso)
    prints.sort(key=lambda r: r["t"])
    avg_oi = (sum(c["oi"] for c in chain) / len(chain)) if chain else None
    state = {}
    agg = {"underlying": underlying, "spot": spot, "prints": 0,
           "cancelled_excluded": 0, "multileg_prints": 0,
           "total_premium": 0.0, "net_premium": None,
           "net_premium_state": DIRECTION_BASIS,
           "golden_sweeps": 0, "high_heat": 0, "heat_sum": 0.0,
           "alerts": []}
    for r in prints:
        cond = r.get("c")
        if tape_mod.is_cancel(cond):
            agg["cancelled_excluded"] += 1
            continue
        c = by_sym.get(r["symbol"])
        if c is None:
            continue
        st = state.setdefault(r["symbol"],
                              {"n": 0, "prem": 0.0, "size": 0.0,
                               "day_vol": 0})
        price, size = float(r["p"]), int(r["s"])
        premium = price * size * 100.0
        dte = (date.fromisoformat(c["expiry"])
               - date.fromisoformat(session)).days
        otm = (max(0.0, (c["strike"] - spot) / spot * 100.0)
               if c["is_call"]
               else max(0.0, (spot - c["strike"]) / spot * 100.0))
        st["day_vol"] += size
        base = {"avg_premium": (st["prem"] / st["n"]) if st["n"] else None,
                "avg_size": (st["size"] / st["n"]) if st["n"] else None,
                "avg_oi": avg_oi}
        p = {"premium": premium, "dte": dte,
             "sweep": tape_mod.is_sweep(cond), "size": size,
             "otm_pct": otm, "oi": c["oi"]}
        heat, _ = tape_mod.heat_score(p, base)
        tg = tape_mod.tags(p)
        agg["prints"] += 1
        agg["total_premium"] += premium
        agg["heat_sum"] += heat
        if tape_mod.is_multileg(cond):
            agg["multileg_prints"] += 1
        if tg["golden_sweep"]:
            agg["golden_sweeps"] += 1
        if heat >= tape_mod.HIGH_HEAT:
            agg["high_heat"] += 1
        if tg["golden_sweep"] or heat >= tape_mod.HIGH_HEAT:
            agg["alerts"].append({
                "ts": r["t"], "symbol": r["symbol"], "price": price,
                "size": size, "premium": round(premium, 2),
                "heat": round(heat, 2), "side": "unknown",
                "direction": "unjudged",
                "direction_basis": DIRECTION_BASIS,
                "golden_sweep": tg["golden_sweep"],
                "unusual": tg["unusual"]})
        st["n"] += 1
        st["prem"] += premium
        st["size"] += size
    agg["alerts"].sort(key=lambda a: -a["premium"])
    agg["alerts"] = agg["alerts"][:25]
    n = agg["prints"] or 1
    agg["mean_heat"] = round(agg["heat_sum"] / n, 2)
    agg["total_premium"] = round(agg["total_premium"], 2)
    agg["heat_sum"] = round(agg["heat_sum"], 2)
    agg["window"] = f"{start_iso} -> live fetch {now.isoformat()}"
    agg["contracts_in_scope"] = len(chain)
    agg["batches_capped"] = capped
    agg["completeness"] = (
        "incomplete" if capped else "complete")
    return agg


def main(argv):
    now = datetime.now(timezone.utc)
    # The session is the ET trading date, never the UTC date: after
    # 00:00Z the UTC date is one day ahead of ET, and a future-dated
    # trades window is refused by the source (403, proven 2026-10-29).
    from zoneinfo import ZoneInfo
    session = now.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    if argv and argv[0] == "--session":
        session = argv[1]
        argv = argv[2:]
    symbols = argv or bounded_universe()
    os.makedirs(STORE_DIR, exist_ok=True)
    names, errors, exclusions = {}, [], []
    for sym in symbols:
        try:
            names[sym] = score_name(sym, session, now)
            print(f"{sym}: {names[sym]['prints']:,} prints, "
                  f"{names[sym]['high_heat']} high-heat, "
                  f"capped {names[sym]['batches_capped']}")
        except Exception as e:  # loud per-name error, never silent
            err = f"{type(e).__name__}: {e}"[:300]
            # A 422 invalid-underlying answer from the contracts
            # source is a definitive universe fact, not a failed
            # capture: the source carries no options chain for
            # that tracked name (HLX, every run on record). Such
            # names are recorded as named exclusions, so one
            # non-optionable tracked name cannot mark every run
            # partial forever (HLX-EXCLUSION-20261031). Every
            # other error stays an error.
            if "422" in err and "invalid underlying symbols" in err:
                exclusions.append({"symbol": sym, "reason":
                                   "the options contracts source "
                                   "carries no chain for this "
                                   "underlying (422 invalid "
                                   "underlying symbols)"})
                print(f"{sym}: EXCLUDED {exclusions[-1]['reason']}")
                continue
            errors.append({"symbol": sym, "error": err})
            print(f"{sym}: ERROR {errors[-1]['error']}")
    doc = {
        "session": session,
        "generated_at_utc": now.isoformat(),
        "source": "Alpaca v1beta1 options trades (same print source "
                  "as the index tape), chains via Alpaca contracts",
        "direction_basis": DIRECTION_BASIS,
        "direction_reason": DIRECTION_REASON,
        "universe": {"kind": "bounded_watchlist",
                     "tracked_source": "insider-wire record names",
                     "symbols": symbols, "count": len(symbols)},
        "names": names,
        "errors": errors,
        "exclusions": exclusions,
        "counts": {"names_stored": len(names),
                   "prints": sum(v["prints"] for v in names.values()),
                   "high_heat": sum(v["high_heat"]
                                    for v in names.values()),
                   "golden_sweeps": sum(v["golden_sweeps"]
                                        for v in names.values())},
    }
    out_path = os.path.join(STORE_DIR, f"{session}.json")
    fd, tmp = tempfile.mkstemp(dir=STORE_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, out_path)
    manifest = {"ts_utc": now.isoformat(), "session": session,
                "status": "ok" if not errors else "partial",
                "names_stored": len(names), "errors": errors,
                "exclusions": exclusions,
                "counts": doc["counts"], "path": out_path}
    with open(os.path.join(STORE_DIR, "manifest.jsonl"), "a",
              encoding="utf-8") as fh:
        fh.write(json.dumps(manifest) + "\n")
    print(f"Wrote {out_path}: {len(names)} names, "
          f"{doc['counts']['prints']:,} prints, {len(errors)} errors")
    return 0 if names else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
