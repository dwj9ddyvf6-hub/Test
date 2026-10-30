# free_etf: Recreation package

Provenance: Source row in strategies/ausar/r19-etf.md in this repo: Family Ausar; Source Ausar R17/R18 ETF research, frozen as the R19 ETF books; Asset US ETFs; Timeframe 1d, monthly rebalance; Universe QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY; QLD for the 2x controls; Style Momentum rotation; Status 12 live, 14 waiting. That doc's Code row states free_etf executes R19 books handed to it on one $100,000 budget and ranks by return per unit of volatility by default.

## What this sleeve is
This sleeve is the execution shell for the R19 ETF books: it receives a list of books, computes each book's target weights from prior completed daily histories, and rebalances whole shares inside a short morning window. It does not choose the books itself; with no books handed to it, it only trims held rows that no plan covers. Sources: sleeves/free_etf.py and adapters3/free_etf.py on the desk.

## Full algorithm
Evaluation order in sleeves/free_etf.py signal() (bars argument unused; the receipt carries the histories):

1. Inputs and qualification: books = context.extra etf_books (each {id, fixed_weights or symbols, policy}); receipt = etf_receipt with histories, source_receipts_verified, feed and adjustment. A book is qualified only when the receipt is verified with feed sip and adjustment all, and every enrolled symbol has at least 252 sessions of history. Per-book slice = min(100000 / number of books, 10000) (BUDGET_USD 100000.0); session buys are capped by DAY_CAP_USD 25000.0 using extra spent_usd.
2. Targets (targets_for): a fixed_weights book uses those weights. A selection book scores each symbol: with the enhancement on (default; context.extra["free_etf_improve"]["vol_rank"]) the score is the 126-session log return divided by the standard deviation of the daily log returns over the same window (last 127 closes); with it off, the score is the raw log(close / close 126 sessions earlier). score_map fails the book when any symbol has fewer than 252 sessions or a nonpositive close.
3. Selection policies (the recovered R19 select backend): plain policies pick the highest score, ties broken by symbol name; EXSMH1 excludes SMH first; a policy ending in CORE25 weights the selected fund 0.25 and QQQ 0.75; INTERVAL policies combine this desk's scores with the secondary provider scores (extra etf_secondary_scores; absent them the book fails closed): the robust leader whose lower bound beats every other upper bound wins, else the incumbent if it can still lead, else QQQ.
4. Schedule: fixed-weight books trade only in the initial sessions starting at INITIAL_ORIGIN 2026-10-13 (the first 5 weekdays from that date); selection books trade in the first 5 weekdays of the month following the receipt's signal_session.
5. Clock: entries only in the entry window 09:35 to 09:40 America/New_York (etf_window). Exits are not limited to that window.
6. Quote gates for every symbol, QQQ included: freshness assess with source age at most 2 seconds (ETF_SOURCE_MAX_SECONDS 2), receipt age at most 30 seconds (RECEIPT_MAX_SECONDS 30), future tolerance 2 seconds; bid must be positive and not above ask; for ordinary entries the spread must be at most 20 bps of ask.
7. QQQ is never ordered: desired = floor(slice * weight / ask); the virtual grant = min(desired, max(0, broker_qqq_qty - attributed_others)); in the open window on a scheduled day a positive grant emits an enter intent marked VIRTUAL_ATTRIBUTION slice-only (no broker order). TQQQ and GLD are refused outright.
8. Ordinary symbols: owned qty comes from extra held_rows (row ids FREE_ETF_<book>_<symbol>); when held_rows is absent a nonzero aggregate is unattributed and that symbol fails closed for every book. Target qty = floor(slice * weight / ask); buy the shortfall at the ask (subject to the day cap), or, in the window, sell the excess at the bid; after the window, sell only the excess above target at the bid.
9. Deselection exits: a held symbol absent from the current plan (including when there are no books or the plan failed) is trimmed to zero at the bid on a fresh quote, in the open or after phases, never before the window; QQQ, TQQQ and GLD are never ordered by this route.

## Files in this repo
- Sleeve module: sleeves/free_etf.py (the strategy logic; CONFIG sleeve_id=free_etf).
- v3 adapter: adapters3/free_etf.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/ausar/r19-etf.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=free_etf).
- Rulebook the books come from: packages/ausar/ausar-archive-rulebooks/config/aurelia_free_etf_rules.json in this repo.

## Configuration
Module adapters3.free_etf; cadence_s 60; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [positions, extra, quotes]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_etf. The strategy module's own CONFIG also carries cadence_s 60 and account free_etf with BUDGET_USD 100000.0 for the whole book family (see Full algorithm).

## Data inputs
The etf_receipt producer supplies prior completed SIP daily histories (adjustment all, at least 252 sessions per enrolled symbol), source_receipts_verified, feed sip and signal_session; IEX quotes via extra quotes {sym: {t, received_at, bp, ap}}; held_rows, spent_usd, broker_qqq_qty and attributed_others from the dispatch records; secondary provider scores via etf_secondary_scores for INTERVAL books. Bars from the snapshot are not used for the signal.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_etf` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: a verified sip/all receipt, one selection book, 252+ sessions per symbol and a fresh quote inside 09:35 to 09:40 ET on a scheduled session produces target-weight intents with the vol-normalized winner selected (and the raw-return winner when vol_rank is switched off). Fixture B: the same fixture at 09:41 ET produces no entries, only any due excess or deselection exits.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
