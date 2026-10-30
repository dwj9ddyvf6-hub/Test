# aster_breakout_ada_vol1pct: Recreation Package

## Provenance

Provenance: Ausar R17/R18 crypto research, run as the R19 native-spot books (Source row in `strategies/ausar/r19-crypto-breakout.md`).

## What this sleeve is

This sleeve trades ADAUSDT spot on 4-hour bars under the breakout_base family with volume1pct sizing. It is a thin wrapper: `aster_sleeves/aster_breakout_ada_vol1pct.py` sets FAMILY='breakout_base', CAPACITY='volume1pct' and delegates to `evaluate_crypto` in the shared engine `aster_sleeves/_common.py`. It holds one position at a time and exits only on its fixed 16-hour deadline.

## Full algorithm

Evaluation order in `evaluate_crypto` (engine `aster_sleeves/_common.py`), as applied to this sleeve:

1. Exits first. For each held ADAUSDT position for this sleeve: the exit deadline is the position's `exit_due_at` if present, otherwise `opened_at` + 16 hours (HOLD). If `now` is at or after the deadline, emit a market sell exit for the full held quantity (time_in_force 'gtc'). If no deadline is on record, no exit is invented. If any position is held, return only the exit list (or nothing) and never evaluate an entry.
2. Bars: read completed ADAUSDT bars under key `ADAUSDT|4Hour`, sorted by time. Fewer than 22 bars emits nothing.
3. Entry window: the signal bar is the second-to-last completed bar and the entry bar is the last completed bar. The entry bar close time is its timestamp + 4 hours; entry fires only when `now` minus that close time is between 0 and 300 seconds (ENTRY_WINDOW_S). This sleeve is not in the engine's extended-window set, so the 300-second rule applies exactly.
4. Bar continuity: the signal bar close time (its timestamp + 4 hours) must equal the entry bar close time minus 4 hours; a native-bar gap fails closed.
5. Breakout trigger: boundary = the highest high of the 20 bars immediately before the signal bar. Triggered only if the signal bar close is above that boundary. The breakout_base family requires no funding condition.
6. Entry revalidation (enhancement, on by default for breakout_base): the entry bar close must also be above the same boundary; if it has fallen back to or below the boundary, the entry is refused.
7. Sizing: price = the entry bar close (must be above 0). Target quantity = slice cash / (price x 1.001), where 0.001 is the 10 bp fee each side, capped for volume1pct at 1% of the entry bar volume: target = min(target, entry bar volume x 0.01). Quantity is floored to whole ADA units; a quantity at or below 0 emits nothing.
8. Entry intent: market buy, time_in_force 'gtc', quantity as above, price_hint = entry bar close, reason `aster_breakout_base_volume1pct`. No price stop and no price target are part of this sleeve.

## Files in this repo

- Sleeve module / adapter (same wrapper content in the repo):
- `aster_sleeves/aster_breakout_ada_vol1pct.py`
- `sleeves/aster/aster_breakout_ada_vol1pct.py`
- `integration/aster_breakout_ada_vol1pct_adapter.py`
- Shared engine: `engines/aster_sleeves/_common.py` (desk path `aster_sleeves/_common.py`)
- Config: `config/sleeves.json` and `engines/config/sleeves.json` (row id `aster_breakout_ada_vol1pct`)
- Existing family doc: see the Provenance source doc path named in the audit record for this sleeve.

## Configuration

- Universe and symbol: ADAUSDT spot only. Timeframe: 4-hour bars.
- Module: `aster_sleeves.aster_breakout_ada_vol1pct`; cadence_s 3600; session '24h'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}.
- Inputs declared in config: bars, positions. Parked: false.

## Data inputs

Declared inputs: bars, positions (wrapper INPUTS = ('bars', 'positions')). The code consumes completed ADAUSDT 4-hour bars in `view['bars']` and this sleeve's open positions in `view['positions']`, plus `view['now']` (a timezone-aware timestamp is required) and the slice cash in `view['slice']`. No funding input is used by the breakout_base family.

## Install and run

1. Place the files listed in 'Files in this repo' at their repo paths in a fresh desk tree, keeping `desk3/`, `adapters3/`, `sleeves/` and `integration/` side by side so the wrapper imports resolve exactly as in the repo.
2. Register the config row for `aster_breakout_ada_vol1pct` from `config/sleeves.json` (also vendored as `engines/config/sleeves.json`) with the exact values in the Configuration section; do not change cadence, slice or parked state.
3. Wire the producers named in 'Data inputs' so the declared inputs are present in the evaluation `view` at the stated freshness; a missing input must leave the sleeve unfed, never fake-fed.
4. Specific entry point: `from aster_sleeves.aster_breakout_ada_vol1pct import evaluate; intents = evaluate(view, ctx)`, where `view` carries `now`, `bars` (`ADAUSDT|4Hour`), `positions` and `slice`.
5. First evaluation: call the wrapper entry point `evaluate(view, ctx)` for this sleeve (see the specific call in the preceding step), confirm no intent is emitted outside the stated window / gates, then let the desk dispatcher call it on its cadence and route returned intents to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- A held position past its 16-hour deadline emits one full market sell exit and no entry; a held position before its deadline emits nothing.
- With at least 22 bars, a signal close at or below the prior 20-bar high emits nothing; a signal close above it, inside the 300-second entry window, with the entry bar close also above the boundary, emits one entry.
- An evaluation more than 300 seconds after the entry bar closes, a gap between signal and entry bars, or fewer than 22 bars emits nothing.
- Entry quantity equals floor(min(cash / (price x 1.001), 0.01 x entry bar volume)) whole units.
- The wrapper delegates to the named shared engine with the exact sleeve id, and no rule, threshold or sizing value differs from the values stated above.
- A missing or stale declared input emits no entry intent.
