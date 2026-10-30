# t_trullas_v09: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): see the variant paragraph below for this id's accounting record. Algorithm grade PARTIAL in the accounting, gaps: entry, exit and sizing not recorded in the accounting's consulted sources (sources: md2 catalog entry/exit/strategy text). The algorithm here is filled from the Test strategy card, the frozen specs and the code in this repo (see Files).
- No Test catalog entry (`docs/CATALOG.json`) for this id in the accounting (test_entries empty). The strategy's Test card is `strategies/muse/muse-trullas-divergence.md` (family Muse, status: Midna's desk only), with frozen specs `docs/TRULLAS-SPEC-2026-10-25.md` and, for variants, `docs/TRULLAS-VARIANTS-SPEC-2026-10-29.md`.
- Alias: `t_trullas_v09`.

## Variant record for this id

- Accounting canonical name (truncated in the accounting): "Trullas variant v09: triple divergence only (confluence: takes only the full 3-lot setups ..." with description "Trullas variant v09: triple divergence only (confluence: takes only the full 3-lot setups (MACD + RSI + v)". Type divergence reversal, family intraday_macd_divergence_fib_variant; status history md2_catalog "installed".
- Test frozen variant record (the code's own record, which this package follows for the algorithm): variant `trullas_v09` in `docs/TRULLAS-VARIANTS-SPEC-2026-10-29.md` varies how volume at an extreme is read: primary value is the single extreme bar's volume; variant value is the sum of volume over a centred 5-bar window [i-2, i+2] around the extreme bar i, at both extremes (`vol_window=2` in code). Volume never gates a trade in the primary, so this joint changes the divergence count, and therefore unit size only. The frozen spec's all-three-divergences-required gate is variant v10, not v09.
- Discrepancy named, not reconciled: the accounting's md2 description for `t_trullas_v09` ("triple divergence only, full 3-lot setups") does not match the Test frozen spec / code joint above. No source in Test reconciles the two descriptions for this id; this package does not invent a reconciliation. A recreation following the code in Files implements the volume-window joint.

## What this strategy is

A QQQ 1-minute MACD-divergence Fibonacci scalp: trades a divergence between two same-day swing pivots, entering on a 23.6% retrace and scaling out at 38.2% and 61.8%, per the frozen primary spec, with the variant joint (if any) named in Provenance.

## Full algorithm

Common primary algorithm (from `strategies/muse/muse-trullas-divergence.md`, `docs/TRULLAS-SPEC-2026-10-25.md` and `sleeves/trullas_divergence.py`), in evaluation order:

1. Instrument and data: QQQ, 1-minute Alpaca SIP bars, regular session only (09:30-16:00 ET); zero-volume bars dropped.
2. Pivots: a bar strictly highest (or lowest) over 5 bars each side (k = 5), usable only once those 5 right-side bars have closed (anti-repaint).
3. Setup: two consecutive same-kind pivots of the same day, 10-120 bars apart, with a regular divergence against the MACD(12, 26, 9) line (MACD divergence is required); RSI(14) divergence and lower volume on the second extreme add to the divergence count (1-3).
4. Trigger (bearish): A = the lowest low between the highs, B = the second high; entry when price trades through B - 0.236 times (B - A) - 1 tick ($0.01); bullish mirrored. The day's newest untraded setup is the pending one.
5. Cancellation / expiry: after 30 bars, or by a trade more than a tick beyond B. Entries 09:30-11:00 ET only, at most 5 a day, none after a -0.75% day (daily loss stop).
6. Exit: stop one tick beyond B, checked before the targets on the same bar (pessimistic ordering). TP1 at 38.2%: half off and the stop moves to the entry. TP2 at 61.8%: the rest. Flat at 12:00 ET.
7. Sizing: divergence count times 0.25% of the slice at risk to the stop, capped at 25% of the slice in notional; whole shares.

## Files in this repo

- This doc: `docs/T_TRULLAS_V09-RECREATE.md`
- Strategy card: `strategies/muse/muse-trullas-divergence.md`
- Code (already in Test): `sleeves/trullas_v09.py` (thin subclass, `variant_params(vol_window=2)`), primary `sleeves/trullas_divergence.py`, plumbing `adapters/trullas_v09.py`, `adapters3/trullas_v09.py`
- Install proof: `proof/install/trullas_v09.json`
- Specs: `docs/TRULLAS-SPEC-2026-10-25.md`, `docs/TRULLAS-VARIANTS-SPEC-2026-10-29.md`, `docs/TRULLAS-VARIANTS-BUILD.md`, `docs/TRULLAS-SLEEVE-BUILD.md`
- Tests: `integration/test_trullas_divergence.py`, `tests/test_trullas_variants_blockers.py` (variants), `tests/test_trullas_blockers.py` (primary, per the build record)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. No Trullas sleeve code was found in Silicon, quant-research-backup or Midna trees; the code above in Test is the home used.

## Configuration

- Universe: QQQ only. Timeframe: 1-minute bars. Asset: QQQ shares, long and short (per the card).
- Slice: $10,000 capital / $10,000 cash per variant (per the variants spec); cadence 60 seconds; session RTH; the sleeve owns its 12:00 ET flat (config flat_by_close false, flatten_time_et null, per the variants spec).
- State: pending setup, plan and day counters in the sleeve's own state file (`trullas_state.json` beside its journal, per the adapters).

## Data inputs

- QQQ 1-minute bars from Alpaca SIP via the desk's warm bars product (4000 bars requested by the adapters).

## Install and run

1. Clone the Test repo.
2. Read `strategies/muse/muse-trullas-divergence.md`, `docs/TRULLAS-SPEC-2026-10-25.md` and (for a variant) its section of `docs/TRULLAS-VARIANTS-SPEC-2026-10-29.md`.
3. Open the code files listed in Files for this id; the variant sleeves are thin subclasses of the primary in `sleeves/trullas_divergence.py`.
4. Provide QQQ 1-minute SIP bars on a 60-second cadence in RTH and the sleeve's own $10,000 slice and state directory.
5. Run the tests in Files and verify against the Verification checklist before any live (paper) use. No backtest: the frozen variant spec rules the live paper record is the test.

## Verification

Tests in Test: `tests/test_trullas_variants_blockers.py` includes the v09 volume-window count test. Behaviour checklist:

- Golden fixture (per `docs/TRULLAS-SLEEVE-BUILD.md`): a hand-built bearish triple divergence (pivot highs 110.0 to 111.0, swing low A = 103.8, volumes 5000 to 2000) must produce entry 109.2908, stop 111.01, TP1 108.2496, TP2 106.5504, qty 22 on a $10,000 slice, computed independently in the test.
- No setup or entry before the second pivot's confirmation bar; a bar spanning both stop and TP1 exits fully at the stop; TP1 exits half and moves the stop to entry; 12:00 ET flat exits everything.
- The 5-entries-per-day cap, the -0.75% daily loss stop and the 30-bar expiry each block a trigger as recorded.
