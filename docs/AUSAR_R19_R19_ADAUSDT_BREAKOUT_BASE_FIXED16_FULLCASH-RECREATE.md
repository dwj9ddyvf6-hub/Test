# ausar_r19_R19_ADAUSDT_BREAKOUT_BASE_FIXED16_FULLCASH: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Price-only breakout control · ADAUSDT, 16-hour hold, available-cash sizing", type breakout, family breakout_base. Algorithm grade PARTIAL. Recorded entry text: "A completed four-hour close must exceed the highest high of the prior 20 bars. This control does not require funding." No parameters recorded for this alias entry in the accounting.
- Alias: only `ausar_r19_R19_ADAUSDT_BREAKOUT_BASE_FIXED16_FULLCASH` itself. Installed status in the accounting: installed (md2 catalog). This is the installed-alias entry for the same ADAUSDT fullcash form; it shares the code in Files.
- Test strategy card for the family: `strategies/ausar/r19-crypto-breakout.md`.

## What this strategy is

Price-only breakout control on ADAUSDT: a completed 4-hour close must exceed the highest high of the prior 20 bars. This control does not require funding. Exit policy fixed16 (16-hour hold), sizing available-cash sizing (fullcash), fee 10 bps per side where the accounting records it.

## Full algorithm

Master-desk design (Test card `strategies/ausar/r19-crypto-breakout.md`): a completed UTC 4h close above the highest high of the prior 20 bars; buys 4 h after the signal bar closes, inside a 5-minute window, on a fresh quote (spread <= 100 bps, last trade <= 60 s old); long only, one position per book, only signals after the book's activation; fixed16 sells 16 h after the entry time; no stop; fullcash = all book cash at the ask net of the 10 bps fee; volume1pct = capped at 1% of the volume of the 4h bar that completes at entry; floored to the venue lot. The card notes the v3 translation differs: it buys at the signal bar's close when it evaluates, its deadlines count from the fill, and volume1pct reads the bar before the signal bar. The v3 engine text in Files governs the installed form below.

Installed v3 algorithm, in evaluation order (from the engine in Files):

Engine `engines/aster_sleeves/_common.py`, `evaluate_crypto(view, ctx, sid, family="breakout_base", capacity)` (also at `aster_sleeves/_common.py`):
1. Exits first: for each held position, due = saved `exit_due_at`, else `opened_at` + 16 h (HOLD); if now >= due, emit a sell intent for the full quantity. If any position is held, return after the exit pass.
2. Bars: completed `ADAUSDT|4Hour` bars sorted by time; fewer than 22 bars is no entry. Signal bar = second-to-last bar, entry bar = last bar.
3. Entry window: entry fires only when now is within the entry window after the entry bar closes (archive window 300 s; the `_common` window enhancement applies only to the listed absorption sleeve ids, so breakout keeps 300 s). A gap between signal and entry bar closes fails closed.
4. Trigger: boundary = highest high of the 20 bars before the signal bar; triggered when the signal bar close > boundary. No funding is read for breakout_base.
5. Enhancement (default on): revalidate on the entry bar: if the entry bar close is not above the boundary, refuse the stale breakout.
6. Sizing: price = entry bar close; target = slice cash / (price x (1 + 0.001 fee)); for volume1pct, target = min(target, 1% of the entry bar's volume); quantity floored to whole units; quantity <= 0 is no entry.

Accounting gaps: the accounting records "exit rule not recorded" for this entry; the fixed16 exit above is recorded in the sleeve id, the card, and the engine SPECS in Files. Sizing gaps in the accounting are likewise resolved by the engine text in Files. Anything beyond those sources is not in the record.

## Files in this repo

- This doc: `docs/AUSAR_R19_R19_ADAUSDT_BREAKOUT_BASE_FIXED16_FULLCASH-RECREATE.md`
- Strategy card: `strategies/ausar/r19-crypto-breakout.md`
- Sleeve wrapper: `sleeves/aster/aster_breakout_ada_fullcash.py` (SLEEVE_ID `aster_breakout_ada_fullcash`, FAMILY breakout_base, CAPACITY fullcash, CADENCE_S 3600; also at `aster_sleeves/aster_breakout_ada_fullcash.py`)
- Engine (the logic): `engines/aster_sleeves/_common.py`, `evaluate_crypto` (also at `aster_sleeves/_common.py`)
- Adapters: `integration/aster_breakout_ada_fullcash_adapter.py`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Searched for code outside Test: Silicon, quant-research-backup and Midna trees were searched for R19 breakout code; no distinct original was found there. The code above in Test is the home used.

## Configuration

- Symbol: ADAUSDT. Timeframe: 4h (native UTC bars). Family: breakout_base. Exit: fixed16, hold 16 h.
- Capacity: fullcash. Fee: 10 bps each side (accounting parameters where recorded; engine FEE = 0.001).
- Cadence: 3600 s (wrapper CADENCE_S). Slice cash default in the engines: $10,000 when no slice cash is supplied (engine text).
- Universe / asset class in the accounting: not recorded in consulted sources (the card records Binance spot, universe ADAUSDT / ENJUSDT / LINKUSDT).

## Data inputs

- Per the card: Binance spot 4h klines (340), depth and last trade; the accounting filter text for the deployed ADA forms records "Native spot OHLCV and received bid/ask", and for the installed-alias forms "posted r19 data adapters". No funding input for breakout_base.

## Install and run

1. Clone the Test repo.
2. Read `strategies/ausar/r19-crypto-breakout.md`.
3. Import `sleeves/aster/aster_breakout_ada_fullcash.py`; its `evaluate(view, ctx)` calls `evaluate_crypto` in `engines/aster_sleeves/_common.py` with family breakout_base and capacity fullcash.
4. Provide completed ADAUSDT 4h bars, positions and slice cash in the view shape the engine expects.
5. Run on the recorded cadence and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No entry unless the latest completed 4h close is strictly above the highest high of the prior 20 bars (at least 21 bars present where the engine requires them).
- No funding value, present or absent, changes the breakout_base decision.
- A held position exits at or after 16 h from entry and not before; exits are not blocked by missing bars where the engine says deadlines survive.
- Sizing matches the fullcash rule in the engine text, net of the 10 bps fee, and quantity <= 0 produces no entry.
