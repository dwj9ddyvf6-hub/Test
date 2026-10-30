# t_trullas_v04 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `t_trullas_v04`
- Canonical name: Trullas variant v04: strict swings, wide stop (pivot strictness: only a swing that stands 
- Aliases: t_trullas_v04
- Type: divergence reversal; Family: intraday_macd_divergence_fib_variant; Algorithm grade in ALL-SLEEVES accounting: PARTIAL (gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source'])
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Trullas variant v04: strict swings, wide stop (pivot strictness: only a swing that stands " (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Trullas variant v04: strict swings, wide stop (pivot strictness: only a swing that stands " (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads cited in the body below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching trullas, r19 timing hour, or killed pead path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path; the only pead-named file is an unrelated outside_ideas/code/pead_filters.py, which is not this strategy's code). Code was found in Test, so nothing was vendored.
- Accounting-versus-code note: The ALL-SLEEVES accounting description for this canonical id does not match the code in Test (the accounting was written from the md2 catalog text, and its entry/exit/sizing fields are empty). The CODE is the truth: in Test, sleeves/trullas_v04.py is a thin subclass of TrullasDivergenceSleeve in sleeves/trullas_divergence.py whose single differing joint is: S4: TP2 at 66.7 percent; PARAMS = variant_params(tp2_level=0.667). All other parameters are the frozen primary values in that file.
- The existing per-sleeve recreation package in Test for the same code is reproduced in substance below, with this canonical provenance header added.

Provenance: TRULLAS-VARIANTS-SPEC-2026-10-29 (FROZEN), variant S4: TP2 at 66.7 percent (spec doc docs/TRULLAS-VARIANTS-SPEC-2026-10-29.md in this repo; strategy header in sleeves/trullas_v04.py in this repo).

## What this sleeve is
This sleeve is variant S4 of the primary QQQ divergence method: a thin subclass of the primary whose exactly one differing joint is tp2_level=0.667 instead of 0.618, so the second target sits at the 66.7 percent Fib level. Everything else, including pivot k=5 and the 1-minute QQQ timeframe, is the primary's. It has its own $10,000 slice, state and live paper record. Sources: desk sleeves/trullas_v04.py (PARAMS = variant_params(tp2_level=0.667)) and sleeves/trullas_divergence.py.

## Full algorithm
Primary algorithm (desk sleeves/trullas_divergence.py, frozen primary arm; this sleeve's parameters: pivot k=5 (the primary PIVOT_K=5); TP2 level 0.667 (variant_params(tp2_level=0.667)); timeframe 1-minute bars). Evaluation is the TrullasDivergenceSleeve.signal() state machine, in this order:
1. State: ctx.extra trullas_state is reset when its day differs from the session (entries_today 0, realized_pnl 0.0, pending None, plan None, traded_pairs empty). Bars are QQQ RTH bars (09:30 to before 16:00 ET, zero-volume bars dropped, sorted and deduped) on 1-minute bars.
2. Open-position management comes before any entry scan. With a plan: hard flat first (at or after 12:00 ET, exit the full position at market, reason naming flat 12:00 ET); then the stop (one tick beyond the extreme: for a short, stop = second pivot high + 0.01, hit when the latest bar high is at or above it; mirrored for a long), checked before any target the same bar also spans (pessimistic ordering); then TP1 at the 38.2 percent Fib level (exit half: floor(qty/2) whole shares, at least 1, and the stop moves to entry; a 1-share position exits in full); then, after TP1, TP2 at the 0.667 (variant_params(tp2_level=0.667)) Fib level exits the remainder. With a position but no plan, only the 12:00 ET hard flat is knowable.
3. Setup detection (detect_setups): pivots are strictly highest/lowest over a 2k+1 window with k=5, usable only after the k right-side bars have closed (confirm_index = pivot index + k). Two consecutive confirmed pivots of the same kind, same trading day, 10 to 120 bars apart. Bearish (two highs): price divergence means the second high is above the first; MACD(12,26,9) divergence on the MACD line (second MACD below first) is REQUIRED; RSI(14) Wilder divergence (second RSI below first) and volume divergence (second extreme on lower bar volume, the second extreme bar's own volume) are counted. Bullish is mirrored on two lows.  Divergence count = MACD counted + RSI counted + volume counted, 1 to 3, and maps directly to risk units.
4. Fib geometry: bearish A = lowest low between the two highs, B = second pivot high, level(p) = B - p times (B - A); bullish mirrored (A = highest high between the two lows). Entry trigger at level(0.236) minus one tick (0.01) for a short, plus one tick for a long. A setup becomes pending only when its confirmation bar is on or before the latest bar, its session matches, and its pivot pair was not already traded.
5. Pending expiry and invalidation: a pending setup expires after 30 bars past its confirmation index, and is void when a bar trades beyond the extreme plus one tick (latest high above swing_b + 0.01 for a short; latest low below swing_b - 0.01 for a long).
6. Entry gates: entries only when the latest bar time is 09:30 to before 11:00 ET; at most 5 entries per day; slice equity must be available and above 0; the daily loss stop blocks entries when realized_pnl is at or below -0.75 percent of slice equity.
7. Trigger and sizing: a short triggers when the latest bar low is at or below the entry trigger; a long when its high is at or above it. Fill price is the trigger price. Risk per share = |stop - fill|. Qty = floor(min(units times 0.25 percent of equity / risk_per_share, 25 percent of equity / fill_px)), where units is the divergence count; qty at or below 0 emits nothing. The entry is an Intent with stop and TP2 as exit rules (stop rule and target rule), side sell / position_intent sell_to_open for a short and buy / buy_to_open for a long, reason naming trullas_v04, the divergence count, swing A and B, entry, stop, TP1 and TP2.

## Files in this repo
- Variant strategy: sleeves/trullas_v04.py (thin subclass of the primary; CONFIG with sleeve_id=trullas_v04, PARAMS as stated in the Full algorithm section, REASON_LABEL=trullas_v04).
- Primary strategy (all shared logic): sleeves/trullas_divergence.py (TrullasDivergenceSleeve, TrullasParams, variant_params, detect_setups, find_pivots).
- Plumbing adapter in this repo: adapters/trullas_v04.py; v3 worker entrypoint: adapters3/trullas_v04.py.
- Shared contract: sleeves/muse/core/sleeve.py (BaseSleeve, ExitRule, Intent, SleeveConfig).
- Shared v3 plumbing: adapters3/_snapshot_ctx.py (SnapshotSleeveContext) is used by the desk entrypoint and is NOT in this repo tree; take it from the desk source tree.
- Spec and build docs in this repo: docs/TRULLAS-VARIANTS-SPEC-2026-10-29.md and docs/TRULLAS-VARIANTS-BUILD.md. Tests in this repo: tests/test_trullas_variants_blockers.py. Install proof: proof/install/trullas_v04.json.
- Config: engines/config/sleeves.json (row id=trullas_v04), also at config/sleeves.json.

## Configuration
Module adapters3.trullas_v04; cadence_s 60; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; timeout_s null; params {}; inputs [bars, bars_1min, bars:QQQ:1Min, positions, quotes, session_fills]; parked false. Universe: QQQ only; timeframe 1-minute QQQ SIP bars. Strategy CONFIG in sleeves/trullas_v04.py likewise: cadence_s 60, universe (QQQ,), risk_pct 0.0025, parked False. Source: muse-desk-v3/config/sleeves.json row id=trullas_v04.

## Data inputs
Inputs are bars, the literal bars:QQQ:1Min warm product, positions, quotes and session_fills. The bars:QQQ:1Min key (added to producers_g4._BARS_TF_KEYS at install) keeps the sleeve fed on the warm QQQ SIP product at this sleeve's timeframe; bars must be RTH bars with positive volume (zero-volume bars are dropped by the strategy). Positions and session state arrive via the snapshot context: the adapter round-trips ctx.extra trullas_state in the sleeve's own state file beside its journal. No bars means no evaluation (state no_bars).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `trullas_v04` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the v3 worker module adapters3/trullas_v04.py, whose evaluate(view, ctx) rebuilds the snapshot context and delegates to adapters/trullas_v04.py, which runs sleeves/trullas_v04.py signal().
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Tests in this repo: tests/test_trullas_variants_blockers.py must pass against the recreation (it covers this variant's single differing joint).
- Golden-fixture check: on the primary's golden fixture this variant must behave identically to the primary except for the one joint named in the Full algorithm section (for trullas_v04: k=5 (the primary PIVOT_K=5); TP2 level 0.667 (variant_params(tp2_level=0.667)); timeframe 1-minute bars).
- Fixture at or after 12:00 ET with an open planned position: exactly one full exit, reason naming flat 12:00 ET.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
