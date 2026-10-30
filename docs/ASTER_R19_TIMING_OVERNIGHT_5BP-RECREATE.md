# aster_r19_timing_overnight_5bp: Recreation package

Provenance: Ausar R18 overnight research (Source row in strategies/ausar/r19-timing-overnight.md in this repo).

## What this sleeve is
This is an overnight timing sleeve over a fixed 42-symbol universe: on a day whose 12:30-to-14:30 ET 30-minute return ranks at or above the 80th percentile of its own history, it buys near the close (15:30-15:35 ET) and holds overnight to the next session's 09:30 ET open, with a 5 bp per-side fee assumption. It is a thin wrapper: adapters3/aster_r19_timing_overnight_5bp.py delegates to desk3/aster_batch16.py, which calls desk3/aster_batch15.py _eval_timing with the aster_r19_timing_overnight_25bp spec copied and fee_bps changed to 5. Sources: desk adapters3/aster_r19_timing_overnight_5bp.py, desk3/aster_batch16.py (SPECS entry, TIMING_INPUTS, PRODUCERS, SLICE=10000.0), desk3/aster_batch15.py (overnight_signal, UNIVERSE42), and docs/ASTER_R19_TIMING_OVERNIGHT_5BP-ALGORITHM.md in this repo.

## Full algorithm
Spec (desk3/aster_batch15.py SPECS via desk3/aster_batch16.py): kind=overnight, risk=0.0025, notional=0.1, fee_bps=5, slots=8, inputs=(bars, positions, quotes), cadence_s=300, session=rth, slice $10,000. Universe (UNIVERSE42 in desk3/aster_batch15.py): AAOI, AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ, CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR, LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ, SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC, WYFI.
1. Exits first; if any exit is emitted the evaluation returns with no entry.
2. Entry window: only 15:30 <= ET clock < 15:35.
3. Signal (overnight_signal in desk3/aster_batch15.py, computed from 30-minute bars): the day must be a weekday session in the session list; the day's 12:30-to-14:30 ET return (14:30 close / 12:30 close - 1) must be at or above the 80th percentile of the same return over the prior sessions (at least 126 history values required; the last 252 are used). At least 252 30-minute bars are required per symbol.
4. Actionable time: the end of the 14:30 bar plus 30 minutes; the entry is emitted only while now is within 5 minutes of actionable_at.
5. Price: the buy quote when available, else the last 30-minute bar close; a missing or non-positive price skips the symbol. The overnight signal records no stop or target, so no stop/target geometry check applies to entries.
6. Sizing: fee = 5 / 10000; budget = min(cash, $10,000 x 0.1) = up to $1,000; qty = floor(budget / (price x (1 + fee))); qty at or below 0 emits nothing. At most 8 slots.
7. Execution enhancement (ENH entry-mid, switch default ON): when a two-sided quote exists, the entry becomes a limit order at the quote mid (rounded to 2 decimals) instead of a market order at the ask, with a paired spread-saved record on the intent. The entry intent carries exit_at = the next session's 09:30 ET.
8. Exits: evaluated on the witnessed bid (sell quote, else the last 30-minute close): a bid at or below a recorded stop triggers observed_stop_trigger and a bid at or above a recorded target triggers observed_target (the overnight signal records neither, so in practice the scheduled exit governs). Scheduled time exit: at or after the position's exit_at (next session 09:30 ET) the position is sold in full, reason scheduled_time_exit. The scheduled exit uses the same default-ON mid-limit enhancement when a two-sided quote exists. Exits are sell_to_close intents, in full.

## Files in this repo
- v3 adapter: adapters3/aster_r19_timing_overnight_5bp.py (SLEEVE_ID=aster_r19_timing_overnight_5bp; evaluate delegates to desk3/aster_batch16.evaluate with TIMING_INPUTS and PRODUCERS imported from that engine).
- Adapter mirror: integration/aster_r19_timing_overnight_5bp_adapter.py in this repo.
- Shared engine files: desk3/aster_batch16.py (SPECS entry for this sleeve, evaluate, producers) and desk3/aster_batch15.py (the overnight spec it copies with fee_bps=5, overnight_signal, UNIVERSE42).
- Existing docs: strategies/ausar/r19-timing-overnight.md and docs/ASTER_R19_TIMING_OVERNIGHT_5BP-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=aster_r19_timing_overnight_5bp), also at config/sleeves.json.

## Configuration
Module adapters3.aster_r19_timing_overnight_5bp; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, positions, quotes]; parked false. Universe: the fixed UNIVERSE42 list above; timeframe 30-minute bars. Source: muse-desk-v3/config/sleeves.json row id=aster_r19_timing_overnight_5bp.

## Data inputs
Inputs are bars, positions and quotes. Producers named in desk3/aster_batch16.py PRODUCERS: bars (freshness_sla_s 900), quotes (freshness_sla_s 60) and broker_readback (freshness_sla_s 900, outputs positions). The batch-16 note states run_live registers only bars and broker_readback today, so the quotes input has no live producer yet and the sleeve is visibly UNFED on that input rather than fake-fed; without quotes the price falls back to the last 30-minute close as the algorithm states. The existing doc's Data section names IEX 30-minute regular-session bars.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `aster_r19_timing_overnight_5bp` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/aster_r19_timing_overnight_5bp.py, whose evaluate(view, ctx) calls desk3/aster_batch16.evaluate(SLEEVE_ID, view, ctx), which dispatches to desk3/aster_batch15.py _eval_timing with this sleeve's spec.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture at 15:32 ET on a weekday session with a symbol carrying 252+ 30-minute bars whose 12:30-to-14:30 return is at or above the 80th percentile of at least 126 prior values, no held positions and cash at least $1,000: exactly one entry for that symbol, qty floor(1000 / (price x 1.0005)), exit_at set to the next session's 09:30 ET; the same fixture at 15:36 ET emits no entry.
- Fixture with the day's return below the 80th percentile, or with fewer than 126 history values: no entry.
- Fixture with a held position at or after its exit_at: exactly one full sell_to_close exit, reason scheduled_time_exit, and no entry in the same call.
- Fixture with 8 positions already held: no further entries (slots=8).
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
