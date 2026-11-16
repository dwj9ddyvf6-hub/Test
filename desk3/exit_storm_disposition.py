"""EXIT-STORM-CURE-20261116 — disposition of the beatendown /
confluence phantom derived positions (Mon 2026-11-16 total audit,
EXIT-STORM-ROOT-20261116).

Root cause (proven by the forensic lane, BUGLOG_2026-11-16): the
two sleeves' config rows carried no own_book_view, so cycle.py
served them the AGGREGATE broker book. Their adapters converted
the aggregate BTC/USD lot (a lot neither sleeve ever bought) into
sleeve state with entry_date=None and no exit_due_date, and the
frozen sleeve law (missing due date = DUE) emitted a 13-week time
exit every cycle. In the 2026-10-31..2026-11-07 phase — and again
in isolated fills since, e.g. beatendown ASAN/COST on 2026-11-16 —
those phantom exits FILLED against aggregate positions other
sleeves owned, leaving phantom derived positions on the two
sleeves' journal books: derived quantities built ONLY from exit
fills, on symbols the sleeve never entered.

This module is the disposition MECHANISM. It:

1. Traces every derived position of the two sleeves per symbol
   from the dispatcher journal's fill rows (epoch-scoped exactly
   as journal_derived is). A position is PHANTOM iff the trace
   proves (a) exit fills are present (sell_to_close /
   buy_to_close), (b) NO entry fill exists for that symbol in
   either direction (buy_to_open / sell_to_open), and (c) the
   net derived quantity (fills plus any prior disposition rows)
   is nonzero. A position with a genuine entry fill is NOT
   phantom and is never touched, however it is mixed.
2. Builds one journal correction row per phantom position, in
   the estate's recovery-row shape (ORDER-SUBMITTED-RECOVERY-
   20261108 precedent: rows appended to the dispatcher journal
   carrying their provenance on the row). Each row carries this
   cure's id and the intent id of EVERY phantom exit fill behind
   the position.
3. Appends the rows to the live dispatcher journal through
   desk3.journal.append_line (the journal's own O_APPEND path).

The rows are event "phantom_disposition" and are applied by
desk3.reconcile.journal_derived / journal_open_costs as a
position-only TRANSFER: the phantom sleeve's book is offset to
zero and the identical position is booked to HOLDER_SLEEVE, a
named bookkeeping book with no config row (it is never evaluated
and never dispatched). The aggregate derived position and every
spend figure are therefore unchanged — the phantom fills really
executed at the broker against the aggregate book, and deleting
them from the aggregate would manufacture a false discrepancy
against the broker of exactly the dispositioned quantity. What
changes is attribution: the two real sleeves read clean, and the
phantom book sits under one named holder where any reconcile
halt scope names it instead of them.

Idempotent: a re-run dispositions only the residual net a later
phantom fill recreated (the trace is recomputed from the live
journal, prior disposition rows netted in), and appends nothing
when the books already read clean.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

CURE_ID = "EXIT-STORM-CURE-20261116"
EVENT = "phantom_disposition"
HOLDER_SLEEVE = "exit_storm_disposition_20261116"
SLEEVES = ("beatendown", "confluence")
ENTRY_INTENTS = ("buy_to_open", "sell_to_open")
EXIT_INTENTS = ("sell_to_close", "buy_to_close")
QTY_TOL = 1e-9


def phantom_census(rows, epoch_start=None, sleeves=SLEEVES):
    """Per-symbol phantom trace over dispatcher journal rows.

    Returns {sleeve: {symbol: {derived_qty, offset_qty,
    exit_fill_count, phantom_intent_ids, exit_weighted_avg_price,
    entry_intents, exit_intents}}} for PHANTOM positions only
    (see module docstring for the proof rule). derived_qty nets
    fills AND prior phantom_disposition rows for the sleeve, so
    the census is exact both before the first disposition and on
    any re-run after it.
    """
    from .reconcile import _parse_ts
    fills = {}        # (sid, sym) -> [fill rows]
    net = {}          # (sid, sym) -> signed qty, fills + dispositions
    for r in rows:
        sid = r.get("sleeve")
        if sid not in sleeves:
            continue
        sym = r.get("symbol")
        if not sym:
            continue
        if epoch_start is not None:
            ts = _parse_ts(r.get("ts"))
            if ts is None or ts < epoch_start:
                continue
        if r.get("event") == "fill":
            fills.setdefault((sid, sym), []).append(r)
            qty = float(r.get("qty") or 0)
            signed = qty if r.get("side") == "buy" else -qty
            net[(sid, sym)] = net.get((sid, sym), 0.0) + signed
        elif r.get("event") == EVENT and r.get("cure_id") == CURE_ID:
            net[(sid, sym)] = net.get((sid, sym), 0.0) \
                + float(r.get("qty") or 0)
    out = {}
    for (sid, sym), frows in sorted(fills.items()):
        intents = [f.get("position_intent") for f in frows]
        entry = sorted({i for i in intents if i in ENTRY_INTENTS})
        exits = [f for f in frows
                 if f.get("position_intent") in EXIT_INTENTS]
        qty = net.get((sid, sym), 0.0)
        if entry or not exits or abs(qty) <= QTY_TOL:
            continue  # genuine entry, no exit, or already clean
        ex_qty = sum(float(f.get("qty") or 0) for f in exits)
        wavg = (sum(float(f.get("qty") or 0) * float(f.get("price") or 0)
                    for f in exits) / ex_qty) if ex_qty else 0.0
        out.setdefault(sid, {})[sym] = {
            "derived_qty": qty,
            "offset_qty": -qty,
            "exit_fill_count": len(exits),
            "phantom_intent_ids": [f.get("intent_id") for f in exits],
            "exit_weighted_avg_price": wavg,
            "entry_intents": entry,
            "exit_intents": sorted({f.get("position_intent")
                                    for f in exits}),
        }
    return out


def build_disposition_rows(census, ts=None):
    """One phantom_disposition journal row per census position,
    each carrying its full provenance (cure id + every phantom
    exit fill's intent id)."""
    if ts is None:
        ts = datetime.now(timezone.utc).isoformat()
    rows = []
    for sid in sorted(census):
        for sym in sorted(census[sid]):
            c = census[sid][sym]
            rows.append({
                "event": EVENT,
                "cure_id": CURE_ID,
                "correction": CURE_ID,
                "provenance": CURE_ID,
                "sleeve": sid,
                "holder_sleeve": HOLDER_SLEEVE,
                "symbol": sym,
                "qty": c["offset_qty"],
                "price": c["exit_weighted_avg_price"],
                "derived_qty_before": c["derived_qty"],
                "phantom_fill_count": c["exit_fill_count"],
                "phantom_intent_ids": c["phantom_intent_ids"],
                "basis": ("entry fills absent, exit fills present: "
                          "per-symbol journal trace, "
                          "EXIT-STORM-CURE-20261116"),
                "ts": ts,
            })
    return rows


def disposition_for_journal(djournal_path, ts=None):
    """(census, rows) for a dispatcher journal path, epoch-scoped
    from the journal's own state dir exactly as journal_derived
    is. Pure read: appends nothing."""
    from .reconcile import journal_rows, load_epoch_start
    epoch = load_epoch_start(
        os.path.dirname(os.path.abspath(djournal_path)))
    census = phantom_census(journal_rows(djournal_path),
                            epoch_start=epoch)
    return census, build_disposition_rows(census, ts=ts)


def apply_disposition(djournal_path, ts=None):
    """Append the disposition rows for the journal's current
    phantom census via the journal's own append path. Returns
    (census, rows_appended)."""
    from .journal import append_line
    census, rows = disposition_for_journal(djournal_path, ts=ts)
    for row in rows:
        append_line(djournal_path, row)
    return census, rows


if __name__ == "__main__":  # pragma: no cover - operator entry
    import json
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "state", "dispatcher.jsonl")
    _census, _rows = apply_disposition(path)
    print(json.dumps({"dispositioned": {
        sid: sorted(book) for sid, book in _census.items()},
        "rows_appended": len(_rows)}, indent=1))
