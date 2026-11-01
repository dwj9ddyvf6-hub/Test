#!/usr/bin/env python3
"""Refresh the Aperture proof gate states (DEEP-PASS 3.2 item 2).

Computes the per name provisional proof state over the DEEP
panel (per name daily history at the depth already held),
applies the Benjamini-Hochberg correction across the scanned
universe before any name may print SUPPORTED, publishes the
states to site/proof-gate/data.json for the scanner surfaces
and for Engines 19 and 20, and appends one forward ledger
record per scanned name under Engine 19 (the frozen rule's
ledger engine) so each provisional state is later checked
against what the name actually did over the next 10 sessions.

The episode rule comes from the registry (proof_gate_rule on
Engines 19 and 20, which must be identical), never from this
script. States are provisional in every output. Names with too
little history are OBSERVING with their episode count printed,
never filled in. The forward horizon close is the 10th weekday
after the scan session as a scheduling date for the forward
check; the check itself grades from the bars, by index, when
that horizon has actually traded (proof_gate.forward_return
returns None until it has).

Usage: refresh_proofgate.py [--max-names N] [--no-ledger]
The bounded and no ledger forms exist for verification runs;
the daily refresh runs unbounded with the ledger.
"""
import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FORECAST = os.path.join(ROOT, "forecast")
sys.path.insert(0, FORECAST)
sys.path.insert(0, HERE)
try:
    import terminal_common as _tc
except ImportError:
    _tc = None

from ledger import Ledger, file_sha256  # noqa: E402
from registry import Registry  # noqa: E402
import proof_gate as PG  # noqa: E402

DEEP_PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/deep_bars.json")
OUT_DIR = os.path.join(HERE, "proof-gate")
LEDGER_PATH = os.path.join(FORECAST, "ledger.jsonl")
CONSUMING_ENGINES = ("engine_19", "engine_20")


def fail(msg):
    raise SystemExit(f"proof-gate refresh FAILED CLOSED: {msg}")


def forward_close_date(as_of, sessions):
    """The scheduling date `sessions` weekdays after as_of."""
    d = date.fromisoformat(as_of)
    left = sessions
    while left:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d.isoformat()


def load_rule():
    reg = Registry(os.path.join(FORECAST, "registry.json"))
    rules = {eid: reg.proof_gate_rule(eid) for eid in CONSUMING_ENGINES}
    if rules["engine_19"] != rules["engine_20"]:
        fail("Engines 19 and 20 carry different frozen proof gate "
             "rules; the gate has one rule or it does not run")
    return reg, rules["engine_19"]


def build(closes_by_symbol, rule):
    """Pure scan over {symbol: close series}. Returns the
    universe results with BH applied."""
    return PG.compute_proof_universe(closes_by_symbol, rule)


def load_panel_closes(path, max_names=None):
    """Stream the DEEP panel symbol by symbol, keeping only
    closes. The panel is 413 MB of JSON; loading it whole builds
    several GB of row lists and was OOM killed on this box in
    the build pass, so the file is read as one text and each
    symbol's array is sliced and parsed on its own (top level
    keys are the only `"<name>": [` occurrences in the file:
    bar dates are quoted but never followed by a colon bracket).
    Returns ({symbol: [closes]}, freshest_session)."""
    import re
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    matches = list(re.finditer(r'"([^"]+)": \[', text))
    decoder = json.JSONDecoder()
    closes_by_symbol = {}
    freshest = None
    for match in matches:
        symbol = match.group(1)
        # Parse exactly one value at the array start and ignore
        # whatever separator follows: the panel's separators are
        # not uniform (the first symbol boundary carries no space
        # after its comma, later ones do), and fixed offset
        # slicing broke on both forms during the build pass.
        rows, _end = decoder.raw_decode(text, match.end() - 1)
        if not rows:
            continue
        closes_by_symbol[symbol] = [float(r[4]) for r in rows]
        last = rows[-1][0]
        if freshest is None or last > freshest:
            freshest = last
        if max_names and len(closes_by_symbol) >= max_names:
            break
    return closes_by_symbol, freshest


def recount_forward_record():
    """Cumulative forward record on the ledger, per distinct name.

    The published forward_ledger counts are cumulative (cured
    2026-10-30, RC-05): created counts the distinct names with a
    forward row on record, so a rerun that creates nothing does
    not zero the published record, and the per run figures ride
    beside it as created_this_run and duplicates. ledger_rows and
    duplicate_rows name the superseded rows the append only
    record keeps (19 names were written twice when the full
    scan's Benjamini-Hochberg correction changed their values
    against the first partial scan's rows).
    """
    subjects = set()
    rows = 0
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or PG.FORWARD_QUANTITY not in line:
                    continue
                row = json.loads(line)
                if row.get("type") == "forecast" \
                        and row.get("quantity") == PG.FORWARD_QUANTITY:
                    rows += 1
                    subjects.add(row.get("subject"))
    return {"created": len(subjects), "ledger_rows": rows,
            "duplicate_rows": rows - len(subjects)}


def publish(results, as_of, rule, ledger_counts):
    counts = {s: 0 for s in PG.PROOF_STATES}
    for r in results.values():
        counts[r["proof_state"]] += 1
    data = {
        "tool": "Aperture Proof Gate",
        "as_of": as_of,
        "state_language": "provisional",
        "idea_words": (
            "Each name earns a proof state from its own past: the "
            "times its own entry pattern appeared before, and what "
            "the name did in the 10 trading days after each one, "
            "split into an earlier training part and a later "
            "holdout part, with a small cost taken off every "
            "episode. Every state here is provisional: it is built "
            "from the name's own history at scan time, not from a "
            "forward record, and it is written to the forward "
            "record so it can be checked against what the name "
            "does next."),
        "bh_words": (
            "Scanning many names guarantees some pass by chance. "
            "Before any name may show SUPPORTED, its episode "
            "record is corrected for how many names were scanned "
            "(a Benjamini-Hochberg correction across the whole "
            "scan); a name that passes its own bars but not the "
            "correction is shown as MIXED, with the reason kept."),
        "rule_id": rule["id"],
        "consuming_engines": list(CONSUMING_ENGINES),
        "counts": {"names_scanned": len(results), "by_state": counts},
        "forward_ledger": ledger_counts,
        "names": [
            {"symbol": r["symbol"], "proof_state": r["proof_state"],
             "provisional": True,
             "display_state": r["display_state"],
             "episodes": r["episodes"], "hits": r["hits"],
             "train": r["train"], "holdout": r["holdout"],
             "p_value": r["p_value"], "bh_q_value": r["bh_q_value"],
             "bh_significant": r["bh_significant"],
             "downgrade_reason": r["downgrade_reason"]}
            for _sym, r in sorted(results.items())],
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "data.json")
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, out)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    max_names = None
    no_ledger = "--no-ledger" in argv
    if "--max-names" in argv:
        max_names = int(argv[argv.index("--max-names") + 1])
    reg, rule = load_rule()
    if not os.path.exists(DEEP_PANEL_PATH):
        fail(f"DEEP panel absent at {DEEP_PANEL_PATH}; no state "
             f"is published from an absent input")
    closes_by_symbol, as_of = load_panel_closes(
        DEEP_PANEL_PATH, max_names=max_names)
    if not closes_by_symbol:
        fail("DEEP panel yielded no symbols; refusing to publish "
             "an empty proof scan")
    results = build(closes_by_symbol, rule)
    horizon_close = forward_close_date(
        as_of, int(rule["forward_check"]["horizon_sessions"]))
    ledger_counts = dict(
        recount_forward_record(), created_this_run=0, duplicates=0,
        skipped=no_ledger)
    if not no_ledger:
        led = Ledger(LEDGER_PATH, registry=reg)
        if not led.verify_chain():
            fail("forecast ledger hash chain does not verify")
        clocks = {c: as_of for c in (
            "event_time", "publication_time", "first_available_time",
            "ingestion_time", "decision_as_of")}
        lineage = {"clocks": clocks, "source_artifacts": [
            {"path": DEEP_PANEL_PATH, "sha256": file_sha256(DEEP_PANEL_PATH)},
            {"path": os.path.abspath(__file__),
             "sha256": file_sha256(os.path.abspath(__file__))}]}
        created, duplicates = PG.record_forward_records(
            led, results=results, issued_ts=as_of,
            horizon_open=as_of, horizon_close=horizon_close,
            lineage=lineage, rule=rule)
        cumulative = recount_forward_record()
        ledger_counts = {"created": cumulative["created"],
                         "created_this_run": created,
                         "duplicates": duplicates,
                         "ledger_rows": cumulative["ledger_rows"],
                         "duplicate_rows": cumulative["duplicate_rows"],
                         "skipped": False}
    out = publish(results, as_of, rule, ledger_counts)
    counts = {}
    for r in results.values():
        counts[r["proof_state"]] = counts.get(r["proof_state"], 0) + 1
    print(f"proof-gate: as_of {as_of}, names {len(results)}, "
          f"states {counts}, ledger {ledger_counts}, wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
