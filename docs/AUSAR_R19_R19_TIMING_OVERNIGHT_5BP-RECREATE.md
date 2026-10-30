# ausar_r19_R19_TIMING_OVERNIGHT_5BP — Recreation Package

## Provenance

- Canonical name: Strong-afternoon continuation; algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: ausar_r19_R19_TIMING_OVERNIGHT_5BP.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Strong-afternoon continuation" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

## What this strategy is

Strong-afternoon continuation (R19 causal overnight hold): on a day whose early-afternoon 30-minute return ranks at or above the 80th percentile of its own history, it buys near the close and holds overnight to the next session's open, at a 5 bp per-side fee assumption. Family overnight; type momentum; universe the frozen 42-name list (UNIVERSE42 in desk3/aster_batch15.py); timeframe 30-minute bars.

## Full algorithm

Spec: kind=overnight, risk=0.0025, notional=0.1, fee_bps=5, slots=8, inputs=(bars, positions, quotes), cadence_s=300, session=rth, slice $10,000. Universe42: AAOI, AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ, CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR, LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ, SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC, WYFI.
Evaluation order (desk3/aster_batch15.py _eval_timing for kind=overnight; the 5bp form is copied by desk3/aster_batch16.py with fee_bps changed, see the variant section):
1. Exits first; if any exit is emitted the evaluation returns with no entry. Exits are evaluated on the witnessed bid (sell quote, else the last 30-minute close): a bid at or below a recorded stop triggers observed_stop_trigger and a bid at or above a recorded target triggers observed_target (the overnight signal records neither, so the scheduled exit governs). Scheduled time exit: at or after the position's exit_at (next session 09:30 ET) the position is sold in full, reason scheduled_time_exit.
2. Entry window: only 15:30 <= ET clock < 15:35.
3. Signal (overnight_signal in desk3/aster_batch15.py, from completed 30-minute bars): the day must be a weekday session in the session list; compute the day's 12:30-to-14:30 ET return (14:30 close / 12:30 close - 1) and the same return over prior sessions; at least 126 history values are required and the last 252 are used; the day's return must be at or above the 80th percentile (linear interpolation) of that history. At least 252 30-minute bars are required per symbol. (The archive/all-sleeves text describes the window as 13:00-to-15:00; the code computes 12:30-to-14:30, and the code is the truth. Early-close days are excluded in the archive text; the code gates on the regular-session list it is handed.)
4. Actionable time: the end of the 14:30 bar plus 30 minutes; the entry is emitted only while now is within 5 minutes of actionable_at.
5. Price: the buy quote when available, else the last 30-minute bar close; a missing or non-positive price skips the symbol. No stop or target is recorded, so no stop/target geometry check applies.
6. Sizing: fee = fee_bps / 10000; budget = min(cash, $10,000 x 0.1) = up to $1,000; qty = floor(budget / (price x (1 + fee))); qty at or below 0 emits nothing. At most 8 slots (held plus new entries).
7. Entry intent carries exit_at = the next session's 09:30 ET. Entry-mid enhancement (default ON in the engine): when a two-sided quote exists, the entry becomes a limit order at the quote mid (rounded to 2 decimals) instead of a market order, with a paired spread-saved record; the scheduled exit uses the same default-ON mid-limit enhancement for the 5bp sleeve.
Variant: This canonical id is the md2-catalog form of the 5bp overnight book; its code form in this repo is the aster_r19_timing_overnight_5bp adapter delegating to desk3/aster_batch16.py, which copies desk3/aster_batch15.py's aster_r19_timing_overnight_25bp spec and changes fee_bps to 5. md2 catalog status for the alias: blocked.
Accounting gaps: the accounting records no exit rule and (for the ausar-prefixed form) no sizing; the code above supplies both (scheduled 09:30 next-session exit; sizing in step 6).

## Files in this repo

- This package: `docs/AUSAR_R19_R19_TIMING_OVERNIGHT_5BP-RECREATE.md`
- Adapter: `adapters3/aster_r19_timing_overnight_5bp.py`
- Engines: `desk3/aster_batch15.py` (SPECS, overnight_signal, UNIVERSE42, _eval_timing) and `desk3/aster_batch16.py` (copies the batch-15 overnight spec with fee_bps=5 for aster_r19_timing_overnight_5bp)
- Existing packages for the same engines: `docs/ASTER_R19_TIMING_OVERNIGHT_5BP-RECREATE.md`, `docs/ASTER_R19_TIMING_OVERNIGHT_25BP-RECREATE.md`, `docs/ASTER_R19_TIMING_OVERNIGHT_5BP-ALGORITHM.md`, `strategies/ausar/r19-timing-overnight.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md` (strategy entry "Strong-afternoon continuation")
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: adapters3/aster_r19_timing_overnight_5bp.py, adapters3/aster_r19_timing_overnight_25bp.py, desk3/aster_batch15.py and desk3/aster_batch16.py in this repo, plus the existing docs/ASTER_R19_TIMING_OVERNIGHT_5BP-RECREATE.md and docs/ASTER_R19_TIMING_OVERNIGHT_25BP-RECREATE.md packages for the same engines); dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna trees carry no r19 timing module. Code was already in Test, so nothing was vendored.

## Configuration

- This canonical id is the md2-catalog form of the 5bp overnight book; its code form in this repo is the aster_r19_timing_overnight_5bp adapter delegating to desk3/aster_batch16.py, which copies desk3/aster_batch15.py's aster_r19_timing_overnight_25bp spec and changes fee_bps to 5. md2 catalog status for the alias: blocked.
- cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; inputs [bars, positions, quotes]; params {} in the roster row for the aster adapter form; the ausar_map parameters for the R19_ forms are kind overnight, slots 8, notional 0.1, fee_bps 5.

## Data inputs

- Completed 30-minute bars (regular session), the actual exchange/session calendar (session list), positions, and quotes. Producers named in the engines: bars (freshness_sla_s 900), quotes (freshness_sla_s 60), broker_readback (freshness_sla_s 900, outputs positions); without quotes the price falls back to the last 30-minute close as the algorithm states.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place the adapter at `adapters3/aster_r19_timing_overnight_5bp.py` and the engines at `desk3/aster_batch15.py` and `desk3/aster_batch16.py`.
3. Register the sleeve with the spec in the Full algorithm (kind overnight, fee_bps 5, slots 8, notional 0.1, slice $10,000, cadence 300, session rth).
4. Wire bars, positions and quotes into the cycle snapshot in the shapes the algorithm describes.
5. First evaluation: run one cycle on the fixture in Verification and confirm the expected entry intent before enabling live paper routing.

## Verification

- Fixture at 15:32 ET on a weekday session with a symbol carrying 252+ 30-minute bars whose 12:30-to-14:30 return is at or above the 80th percentile of at least 126 prior values, no held positions and cash at least $1,000: exactly one entry, qty floor(1000 / (price x (1 + 5/10000))), exit_at set to the next session's 09:30 ET; the same fixture at 15:36 ET emits no entry.
- Fixture with the day's return below the 80th percentile, or with fewer than 126 history values: no entry.
- Fixture with a held position at or after its exit_at: exactly one full sell_to_close exit, reason scheduled_time_exit, and no entry in the same call.
- Fixture with 8 positions already held: no further entries (slots=8).
