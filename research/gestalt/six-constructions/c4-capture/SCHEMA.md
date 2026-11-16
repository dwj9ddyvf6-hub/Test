# C4 Capture Schema: Book Intent-Time Records

Workstream W4. Typed spend: $0.00. Date: 2026-11-15 (America/New_York).
Implements the prospective capture requirement of C4-RUNFILE.md Section 5
for Midna's book. Schema id: c4-capture/1. Storage: capture_ledger.jsonl
in this folder, append only. Corrections are new rows that name the row
they correct; no row is ever edited in place.

## What one record is

One intent_capture row per book intent, written at detection time (see
the wiring note in README.md for exactly how an intent triggers a
record), before its outcome is known. Outcome information is never
edited into the intent row; it arrives later as a separate outcome_link
row carrying the same capture_id.

## Fields

1. record_type: intent_capture or outcome_link.
2. schema: c4-capture/1.
3. synthetic: true only on demonstration records created by the capture
   code itself, labeled SYNTHETIC in their reason field. Synthetic rows
   are excluded from every C4 grade.
4. capture_id: C4CAP- plus the book intent id.
5. intent.intent_id: the book's own decision id (the J-id from
   JOURNAL.md), never a capture-invented id for a real intent.
6. intent.origin: where the intent was detected, named exactly.
7. intent.symbol, intent.asset_class (equity or option), and for option
   intents intent.option_contract (contract symbol, strike, expiry,
   right) where the book states them, else null.
8. intent.side, intent.position_intent (open or close), intent.qty,
   intent.qty_unit. A value the journal does not state in a machine
   readable line is null, with the gap named in intent.reason. Null is
   recorded, never guessed.
9. intent.decision_ts: the journal entry timestamp converted to UTC,
   with intent.decision_clock naming the clock source.
10. intent.deadline_rule and intent.deadline_imputed: the book journal
    states no per intent deadline, so the rule recorded is end of
    session, flagged imputed, per C4-RUNFILE.md Section 5 item d.
11. intent.mandate: completion expected under the book charter fill
    rule; abstention only by an explicit later journal pass.
12. intent.reason: the journal Setup and Decision lines verbatim in
    compact form, sufficient to confirm the intent was independently
    justified without this study (Section 5 item e).
13. market_at_capture: the contemporaneous quote block (below), with
    its own capture_ts.
14. detection_lag_seconds: capture time minus decision_ts. The watcher
    detects intents on its polling cadence, so this lag is a recorded
    property of every record and a graded limitation, not a hidden one.
15. forecast.movement_or_volatility_numeric: the numeric forecast of
    Section 5 item g. Tonight this is null with status unavailable and
    the reason named: no numeric per intent forecast artifact exists in
    the estate, and the book forecast log is confidence words, which
    item g excludes. The field exists from the first record so the join
    lands here the moment a numeric per intent forecast source exists.
16. forecast.directional: any directional forecast the journal entry
    itself carries, else null.
17. recent_order_flow: the pre-defined summary of Section 5 item i as
    this estate can support it: the book's own prior fills in the
    symbol from ledger.json, count and last decision timestamp, source
    named. No other flow source exists for book intents.
18. router_state: not_graded tonight. Capture is pre-router; the C4
    Stage 2 routers are not built yet, and this field is where their
    per intent action records will land.
19. outcome (on the intent row): pending at write time, always.
20. outcome_link rows: linked_at, decision_id, fill_class, and the fill
    fields exactly as the book recorded them in ledger.json (symbol,
    side, qty, decision_id, execution_id, decision_ts, bar_ts,
    bar_open, fill_price, feed, timeframe, slippage_bp). Fill class is
    stated on the row: the book's fills are simulated fills under its
    bar based charter rule, not broker executions, per the labeling
    rule of C4-RUNFILE.md Section 7.

## The quote block (market_at_capture)

1. status: ok or unavailable. Unavailable always carries reason and the
   per feed attempts list. A quote is never backfilled from a later
   quote, a bar, or a chain snapshot.
2. source and feed: the route actually used. Equity route order: Alpaca
   data API latest quote, feed sip, then feed iex as a named fallback,
   through the same credential and fetch route the book's fill engine
   uses. Option route: TastyTrade DXLink quote events via the book's
   expression selector functions.
3. quote_label and is_consolidated_nbbo: a SIP quote is labeled
   consolidated NBBO. An IEX quote is labeled IEX top of book only, not
   consolidated NBBO, and is_consolidated_nbbo is false. The label is
   part of the record because the two are not interchangeable evidence.
4. bid, ask, mid, spread, spread_bp_of_mid, bid_size, ask_size, bid and
   ask exchange where the route provides them. The DXLink route
   provides no sizes; sizes are null there, not zero.
5. quote_ts: the exchange timestamp on the quote itself.
6. quote_age_seconds_at_capture and quote_stale (age over 300
   seconds): staleness is computed and recorded on every record, so an
   after hours or halted quote can never masquerade as live.
7. depth_beyond_top: visible depth past the top of book. Tonight this
   is the fixed string recording that no level 2 or depth archive
   exists in this estate (C4-RUNFILE.md Section 9, Gap 2). Bid and ask
   sizes at the top are the only depth this estate can lawfully record.

## Grading hooks already in the schema

P0 for C4-RUNFILE.md Section 3 is the mid of market_at_capture where
status is ok, with its source and staleness carried on the same row. PT
is not in this schema: it is recorded by a later deadline pass from the
same quote route, as an outcome-side row, never by editing this row.
