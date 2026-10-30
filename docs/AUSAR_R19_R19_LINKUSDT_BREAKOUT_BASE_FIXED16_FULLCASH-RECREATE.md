# ausar_r19_R19_LINKUSDT_BREAKOUT_BASE_FIXED16_FULLCASH: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Price-only breakout control · LINKUSDT, 16-hour hold, available-cash sizing", type breakout, family breakout_base. Algorithm grade PARTIAL. Recorded entry text: "A completed four-hour close must exceed the highest high of the prior 20 bars. This control does not require funding." No parameters recorded for this alias entry in the accounting.
- Alias: only `ausar_r19_R19_LINKUSDT_BREAKOUT_BASE_FIXED16_FULLCASH` itself. Installed status in the accounting: installed (md2 catalog).
- Test strategy card for the family: `strategies/ausar/r19-crypto-breakout.md`.

## What this strategy is

Price-only breakout control on LINKUSDT: a completed 4-hour close must exceed the highest high of the prior 20 bars. This control does not require funding. Exit policy fixed16 (16-hour hold), sizing available-cash sizing (fullcash), fee 10 bps per side where the accounting records it.

## Full algorithm

Master-desk design (Test card `strategies/ausar/r19-crypto-breakout.md`): a completed UTC 4h close above the highest high of the prior 20 bars; buys 4 h after the signal bar closes, inside a 5-minute window, on a fresh quote (spread <= 100 bps, last trade <= 60 s old); long only, one position per book, only signals after the book's activation; fixed16 sells 16 h after the entry time; no stop; fullcash = all book cash at the ask net of the 10 bps fee; volume1pct = capped at 1% of the volume of the 4h bar that completes at entry; floored to the venue lot. The card notes the v3 translation differs: it buys at the signal bar's close when it evaluates, its deadlines count from the fill, and volume1pct reads the bar before the signal bar. The v3 engine text in Files governs the installed form below.

Installed v3 algorithm, in evaluation order (from the engine in Files):

Engine `desk3/aster_b11_crypto.py`, `evaluate(sid, view, ctx)` with SPECS entry for this sleeve (sym LINKUSDT, fam breakout_base, cap fullcash, hold_h 16):
1. Exits first: for each held position, held hours from `opened_at` / `entry_time` (or `age_hours`); if held >= 16, emit a sell exit (deadline fires even when bars are missing). If any position is held, return after the exit pass.
2. Trigger: `_breakout(brs)`: at least 21 bars and the latest bar close > highest high of the prior 20 bars. No funding gate for breakout_base.
3. Stale-signal gate (default on, ENH-B8): refuse entry when the signal bar closed more than 4.0 h before now; off restores the pre-change rule.
4. Sizing (fullcash): qty = slice cash x (1 - 0.001 fee) / latest close; qty <= 0 is no entry; quantity rounded to 8 decimals.

Accounting gaps: the accounting records "exit rule not recorded" for this entry; the fixed16 exit above is recorded in the sleeve id, the card, and the engine SPECS in Files. Sizing gaps in the accounting are likewise resolved by the engine text in Files. Anything beyond those sources is not in the record.

## Files in this repo

- This doc: `docs/AUSAR_R19_R19_LINKUSDT_BREAKOUT_BASE_FIXED16_FULLCASH-RECREATE.md`
- Strategy card: `strategies/ausar/r19-crypto-breakout.md`
- Sleeve wrapper: `sleeves/aster_r19_linkusdt_breakout_base_fixed16_fullcash.py` (delegates to the engine)
- Engine (the logic): `desk3/aster_b11_crypto.py` (SPECS entry `aster_r19_linkusdt_breakout_base_fixed16_fullcash`: sym LINKUSDT, fam breakout_base, cap fullcash, hold_h 16)
- Adapters: `adapters3/aster_r19_linkusdt_breakout_base_fixed16_fullcash.py`, `integration/aster_r19_linkusdt_breakout_base_fixed16_fullcash_adapter.py`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Searched for code outside Test: Silicon, quant-research-backup and Midna trees were searched for R19 breakout code; no distinct original was found there. The code above in Test is the home used.

## Configuration

- Symbol: LINKUSDT. Timeframe: 4h (native UTC bars). Family: breakout_base. Exit: fixed16, hold 16 h.
- Capacity: fullcash. Fee: 10 bps each side (accounting parameters where recorded; engine FEE = 0.001).
- Cadence: not in the record in the wrapper/engine text fetched (engine config cadence not recorded there). Slice cash default in the engines: $10,000 when no slice cash is supplied (engine text).
- Universe / asset class in the accounting: not recorded in consulted sources (the card records Binance spot, universe ADAUSDT / ENJUSDT / LINKUSDT).

## Data inputs

- Per the card: Binance spot 4h klines (340), depth and last trade; the accounting filter text for the deployed ADA forms records "Native spot OHLCV and received bid/ask", and for the installed-alias forms "posted r19 data adapters". No funding input for breakout_base.

## Install and run

1. Clone the Test repo.
2. Read `strategies/ausar/r19-crypto-breakout.md`.
3. Import `sleeves/aster_r19_linkusdt_breakout_base_fixed16_fullcash.py`; it delegates to `desk3/aster_b11_crypto.py` `evaluate` with its SPECS entry.
4. Provide completed LINKUSDT 4h bars, positions and slice cash in the view shape the engine expects.
5. Run on the recorded cadence and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No entry unless the latest completed 4h close is strictly above the highest high of the prior 20 bars (at least 21 bars present where the engine requires them).
- No funding value, present or absent, changes the breakout_base decision.
- A held position exits at or after 16 h from entry and not before; exits are not blocked by missing bars where the engine says deadlines survive.
- Sizing matches the fullcash rule in the engine text, net of the 10 bps fee, and quantity <= 0 produces no entry.
