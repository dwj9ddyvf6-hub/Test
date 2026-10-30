# lz_s_mn_macd: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna MACD (Midna port)", type "momentum", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: MACD down exit", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Strategy card in Test: `strategies/midna/mn-macd-cci.md`; rule lines in `docs/verify/midna.md` (MACD-CCI section). The card notes the v3 reading trades a plain MACD cross with one slot and no CCI filter or chandelier; the master-desk board book adds those (kept separate below).
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A daily MACD momentum lane. The v3 form (`s_mn_macd`) buys the strongest fresh MACD(12,26,9) histogram cross up with a single $1,000 slot and sells on the cross down. The accounting type for this id is momentum, family 1d.

## Full algorithm

From `sleeves/s_mn_macd.py`, in evaluation order:

1. Compute, per name, the MACD histogram on daily closes: EMA(12) minus EMA(26) gives the line; the signal is EMA(9) of the line; the histogram is line minus signal. A name needs at least 35 bars (MIN_BARS = 35). Crosses are evaluated on the last two closed bars.
2. Exits first: a held name whose histogram crosses down (previous histogram >= 0, last histogram < 0) exits in full. The accounting record agrees: rule "MACD down exit", stop_pct 99.0 (no price stop), max_bars 0 (no time exit).
3. If anything is held (or an exit was just emitted), no entry this pass: one position at a time.
4. Entries: among names whose histogram crosses up (previous <= 0, last > 0), skipping cross-stale feeds (the ENH20 gate in the code), pick the strongest last histogram; deterministic tie-break is symbol order. Size: one slot of $1,000 (SLOT_BUDGET = 1000.0), qty = qty_for($1,000, last close). Cadence 300 seconds.

Master-desk variant (different book, recorded on the same card; code `sleeves/midna/board.py` midna_macd_cci): entry additionally requires CCI(20) > 100, ranked by CCI, up to 4 names; exit is the cross back down or the price under the peak since entry minus 3 x ATR(14); one unit = min(floor(1% of equity / ATR(14)), floor(cash / price)). That variant is not the v3 lane above.

## Files in this repo

- This doc: `docs/LZ_S_MN_MACD-RECREATE.md`
- Code (already in Test): `sleeves/s_mn_macd.py` (imports `sleeves/laz8_common.py`, present in Test at `engines/sleeves/laz8_common.py`)
- Code (already in Test, master variant): `sleeves/midna/board.py` (midna_macd_cci), `sleeves/midna/vendor/midna/board_signals.py`
- Strategy card: `strategies/midna/mn-macd-cci.md`
- Rule lines: `docs/verify/midna.md` (MACD-CCI section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: not recorded in the accounting for this id (not in the record); the v3 code evaluates every name in the delivered daily-bars dict.
- Timeframe: 1d. MACD 12 / 26 / 9. Minimum bars 35.
- Sizing: 1 slot, $1,000. Cadence: 300 s. State: the single held position.
- Accounting entry policy: midna_block, max delay 65 minutes, limit band 5.0%, limit buffer 1.0%, capped_limit_day.

## Data inputs

Completed daily bars (close and volume fields as delivered to the sleeve) for every candidate name.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_macd` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/s_mn_macd.py`; confirm the MACD construction (12, 26, 9), MIN_BARS = 35 and SLOT_BUDGET = 1000.0. Serve daily bars per name and call `signal(bars, slice_state, context)` per pass; entries and exits are the returned intents.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A name with under 35 daily bars never enters or exits on a cross.
- A held name exits exactly when the histogram moves from >= 0 to < 0 across the last two closed bars.
- No second position opens while one is held.
- When several names cross up on the same session, the one with the largest last histogram is bought (symbol order breaks ties).
- The single entry never exceeds the $1,000 slot budget.
