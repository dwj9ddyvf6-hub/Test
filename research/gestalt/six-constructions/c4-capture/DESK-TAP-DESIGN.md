# C4 Desk-Side Intent-Time Capture: Design Only

Workstream W4. Typed spend: $0.00. Date: 2026-11-15 (America/New_York).
Status of this document: DESIGN ONLY. No desk code was read for
modification and none was touched. No desk strategy, threshold, sizing,
or routing behavior is changed by anything in this folder. The verdict
for this half is PARTIAL by design: the design is complete and rowed
for landing; the tap itself does not exist on the desk.

## 1. Purpose

C4-RUNFILE.md Section 9.1 decided that historical desk execution replay
is impossible: the estate holds desk fills and submissions with no
contemporaneous quotes joined to them (the desk quote cache at
~/workspace/muse-desk-v3/cache/quotes/latest.json is an empty object,
the only true NBBO archive stops at 2026-10-28 on sampled capped days,
and chain snapshots are one stale snapshot per symbol). C4 evidence for
desk flow can therefore only accrue prospectively, the same way the
book capture in this folder accrues it for book flow. This document
specifies exactly what a desk-side tap would record, where it would
attach, what it must never do, and what a landing would have to prove.

## 2. What the tap records (per intent, at intent time)

The field set is C4-RUNFILE.md Section 5, items a to k, restated for
the desk's own artifacts. One append only record per intent, written
before any outcome is known:

1. Intent identity: intent_id exactly as the dispatcher journal carries
   it, sleeve id, cycle_id where the row carries one, and the intent
   timestamp with its clock source named. Known desk limitation the
   design must cure at the source: most dispatcher rows carry no ts
   field, and the timestamp embedded in intent_id is a sleeve decision
   time, not a verified submission time (runfile Section 4.1 item A).
   The tap therefore records both the embedded intent_id timestamp
   (labeled sleeve decision time) and the tap's own observation
   timestamp (labeled journal observation time), and never relabels
   one as the other.
2. Instrument: symbol in the dispatcher's own form, the normalized
   symbol where a symbol_normalized event applies, asset class, and
   for option intents the contract symbol, strike, expiry, and right.
3. Side and quantity: side, position_intent, intended quantity Q, and
   the quantity unit, from the intent-bearing event row where it
   carries them. Where the source row is sparse (sampled
   order_submitted rows carry no price, quantity, side, or timestamp),
   the tap joins the intent's other event rows by intent_id and
   records any field no row carries as unavailable, never inferred.
4. Deadline: time_in_force from the source row where present, the
   session, and mandate type (completion required versus abstention
   permitted) as the sleeve's own registration states it. An imputed
   deadline is flagged imputed, per runfile Section 5 item d.
5. Reason: the sleeve's stated reason or fire object in the compact
   form the source provides, plus the per-sleeve journal reference
   (state/<sleeve>/journal.jsonl) for the cycle that produced it.
6. Market at intent time: bid, ask, mid, spread in currency and in
   basis points of mid, bid size and ask size, each with capture
   timestamp and source named, under the quote source rule in
   Section 3 below. Unavailable fields are recorded unavailable. No
   field is ever backfilled from a later quote, a bar, or a chain
   snapshot.
7. The volatility forecast: the numeric forecast value of runfile
   Section 5 item g, its horizon, units, producing artifact, and
   generation timestamp, joined from the desk forecast package
   (~/workspace/muse-desk-v3/desk3/forecast/, verified to exist with
   registry, ensemble, and score modules) at intent time. Tonight no
   per intent join exists (runfile Section 9 item Q8); the tap is
   what creates it, and until the forecast package emits a per intent
   value the field records unavailable with that reason.
8. Any directional forecast attached to the intent, recorded
   separately from the movement forecast.
9. Recent order flow: the desk's own submissions and fills in the
   symbol over a stated lookback ending at intent time, computed from
   the dispatcher journal and the durable fill ledger
   (~/workspace/muse-desk-v3/state/fill_ledger/, 8,930 fills), with
   lookback and source named.
10. Router state: reserved for the C4 Stage 2 routers (not built);
    the tap records the desk's actual routing facts only: submission
    event, broker_order_id where assigned, and acknowledgement or
    rejection events as they land, appended as outcome rows.
11. Outcome fields, appended later as separate rows, never edited
    into the intent row: submissions, fills with price, quantity, and
    timestamp, fees where the reconcile history records them, the
    deadline reference PT from the same quote source as P0, and the
    markout references of runfile Section 7.

## 3. Quote and depth source rule

1. Primary: the Alpaca data API latest quote for the symbol at tap
   time, feed sip, through the credential and fetch route the estate
   already uses for market data, giving consolidated NBBO with bid
   and ask sizes. Named blocker, verified tonight on the book side:
   the current subscription answers recent SIP quote queries with
   HTTP 403 (subscription does not permit querying recent SIP data).
   A landing must either cure that subscription limit or record the
   fallback on every record, exactly as the book capture does.
2. Fallback: the same endpoint at feed iex, labeled on the record as
   IEX top of book only, not consolidated NBBO, with
   is_consolidated_nbbo false. An IEX record is usable for spread
   context and is never presented as NBBO evidence.
3. Options: the TastyTrade DXLink quote route the book's expression
   selector already proves (bid and ask; that route carries no
   sizes, and sizes record as null, not zero).
4. Depth: bid and ask size at the top is the only depth recorded. No
   level 2 or order book source exists in this estate (runfile
   Section 9, Gap 2); depth_beyond_top records that fact per record
   until a lawful depth source exists.
5. Every quote block carries quote_ts from the exchange timestamp,
   quote age at capture, and a stale flag over 300 seconds, so an
   after hours quote can never masquerade as live.
6. Sources explicitly not used: the desk quote cache (an empty
   object), the options chain snapshots under cache/options/ (single
   stale snapshot per symbol, no fetch timestamp), and bars of any
   timeframe (a bar is not a quote).

## 4. Where it attaches: named components, verified to exist

Verified tonight by directory listing and by the runfile inventory,
at name and path level only:

1. The dispatcher and its journal: desk3/dispatcher.py in
   ~/workspace/muse-desk-v3/, writing
   ~/workspace/muse-desk-v3/state/dispatcher.jsonl (12,782 lines in
   the current generation, five generations, 67,612 lines total).
   This is the desk's intent and order event source of record.
2. Per-sleeve journals: ~/workspace/muse-desk-v3/state/<sleeve>/
   journal.jsonl, 339 files, the reason context for intents.
3. The durable fill ledger: ~/workspace/muse-desk-v3/state/
   fill_ledger/, the outcome join source.
4. The reconcile history: ~/workspace/muse-desk-v3/state/
   reconcile_history.jsonl, the fee corroboration source.
5. The forecast package: ~/workspace/muse-desk-v3/desk3/forecast/,
   the forecast join source of Section 2 item 7.
6. The tensor bundle: ~/workspace/muse-desk-v3/cache/tensor/
   bundle.json with dated archives, where many desk intents
   originate; its generated_at is a genuine intent-adjacent
   timestamp the tap records as context.
7. The broker boundary: desk3/broker.py, named here only as the
   component the tap must never sit inside (see Section 5).

Two attachment routes, with the discriminator named:

Route A, journal sidecar (recommended first landing). A separate
process tails the dispatcher journal append stream and the fill
ledger, builds the record of Section 2, fetches the quote of
Section 3 at observation time, and writes to a capture store outside
the desk tree (the same pattern the book watcher in this folder
proves tonight). Discriminator: Route A touches no desk code and no
order path at all, so the never list of Section 5 holds by
construction. Its cost is observation lag and the journal's sparse
timestamps, both recorded per record rather than hidden.

Route B, in-process tap (deferred, needs its own authorization). A
passive emit call inside the dispatcher's intent intake, writing the
record before routing. It would cure the timestamp sparsity at the
source, but it places capture code inside the order path, so it is
not part of this design's landing recommendation and may only be
taken up under the proof requirements of Section 6 plus a separate
ruling.

## 5. What the tap must never do

1. Never change behavior: no intent created, resized, retimed,
   reordered, suppressed, duplicated, or routed differently because
   the tap exists. The tap observes; the desk decides.
2. Never add latency in the order path: under Route A there is no
   shared code path at all. Under any future Route B, the emit must
   be fire and forget to a local queue with a hard budget, and a
   landing must prove order path latency with and without the tap.
3. Never block an order: capture is fail open in the strong sense. A
   quote outage, a full disk in the capture store, a crashed sidecar,
   or a malformed intent row degrades capture only. The desk must be
   able to lose the tap entirely, at any moment, with zero change to
   its operation, and a landing must demonstrate exactly that by
   killing the tap mid-session in a paper run.
4. Never write into desk state: the capture store lives outside
   ~/workspace/muse-desk-v3/. The tap opens desk artifacts read only.
5. Never backfill: a quote, forecast, or timestamp missed at intent
   time stays recorded as missed. Retroactive completion of a record
   is falsification of the study's primary evidence.
6. Never carry credentials or personal data: quote credentials stay
   in the estate's existing in-memory route; records hold instrument
   symbols, sleeve ids, and file paths only.

## 6. Landing route and proof requirements

Landing route: this design is rowed to the desk cure window as a
design. It lands, if it lands, as Route A first, inside a scheduled
inspection or cure pass that owns desk changes, under the desk's own
InfinityBlade and bug log law. Nothing in this document authorizes
the landing itself.

A landing must ship with all of the following, or it does not count:

1. A regression blocker test in the desk test tree, named for this
   capture, that fails on the pre-landing tree and passes after, per
   the standing bug log and regression blocker law, and an entry in
   the dated desk bug log if the landing fixes or works around any
   defect it finds (for example the dispatcher timestamp sparsity).
2. The desk regression gate (desk/run_regression_blockers.sh) green
   before and after, run by the landing pass itself.
3. Fail open proof: a paper session with the tap killed, the quote
   route blocked, and the capture store made unwritable, in three
   separate runs, with dispatcher behavior (intents, submissions,
   fills) shown unchanged against a tap-free control run.
4. Latency proof for Route A: journal observation lag distribution
   printed per record for the proof session. For any later Route B:
   order path latency with and without the tap, same session shape,
   printed side by side.
5. Record proof: the first real desk capture records written and
   read back from the capture store, with quote source, staleness,
   and unavailable fields shown on their face, and the first
   outcome_link row joining a capture record to a fill ledger row.
6. A trial ledger entry in C4-RUNFILE.md before the first graded run
   uses desk capture data, per the runfile's own trial counting rule.

## 7. Open rows

1. The SIP quote subscription limit (HTTP 403 on recent SIP quotes)
   blocks consolidated NBBO capture on both the book and desk sides;
   unblocker: a subscription change or a lawful consolidated quote
   source, decided outside this design.
2. Dispatcher timestamp sparsity is a desk defect this design records
   around but does not cure; the cure belongs to the desk cure window.
3. The per intent numeric forecast join does not exist; the forecast
   package emits no per intent value tonight.
4. Depth beyond the top of book has no lawful source in the estate.

STATUS: PARTIAL by design. Evidence pointer: this file,
DESK-TAP-DESIGN.md in this folder, with the component paths verified
as described in Section 4 and the book side capture in this folder as
the working pattern proof.
