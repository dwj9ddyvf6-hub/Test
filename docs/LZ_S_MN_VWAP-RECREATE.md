# lz_s_mn_vwap: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna VWAP (Midna port)", type "trend following", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: VWAP down exit", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Strategy card in Test for the master variant: `strategies/midna/mn-ema4-vwap.md`; rule lines in `docs/verify/midna.md` (EMA4 rising VWAP section), which names `sleeves/s_mn_vwap.py` as the v3 reading.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A daily VWAP-cross trend lane. The v3 form (`s_mn_vwap`) buys when price crosses above the 20-session rolling VWAP and sells when it crosses back below, one $1,000 slot. The accounting type for this id is trend following, family 1d.

## Full algorithm

From `sleeves/s_mn_vwap.py`, in evaluation order:

1. VWAP definition: the 20-session rolling VWAP on daily bars (WINDOW = 20): over the last 20 bars, sum of (typical price x volume) / sum of volume, typical price = (high + low + close) / 3. A bar window with any non-positive volume yields no VWAP. At least 21 bars are needed for a cross (WINDOW + 1).
2. Crosses use the last two closed bars: up = previous close <= previous VWAP and last close > last VWAP; down = previous close >= previous VWAP and last close < last VWAP.
3. Exits first: a held name with a down cross exits in full (the accounting record agrees: "VWAP down exit", stop_pct 99.0, max_bars 0: no price stop and no time exit beyond the cross).
4. If anything is held, no entry. Entries: the first name in symbol order with an up cross, skipping cross-stale feeds (ENH20 gate). Size: one slot of $1,000 (SLOT_BUDGET = 1000.0). Cadence 300 seconds.

Master-desk variant (different book, recorded on the card; code `sleeves/midna/board.py` midna_ema4_vwap): entry is EMA(4) crossing above the same 20-session volume-weighted typical price while that VWAP is above its value 5 sessions earlier, alphabetical, up to 4 names; exit is the cross back or a 3 x ATR(14) chandelier under the peak since entry; one unit = min(floor(1% of equity / ATR(14)), floor(cash / price)). That variant is not the v3 lane above.

## Files in this repo

- This doc: `docs/LZ_S_MN_VWAP-RECREATE.md`
- Code (already in Test): `sleeves/s_mn_vwap.py` (imports from `sleeves/laz8_common.py`, present in Test at `engines/sleeves/laz8_common.py`)
- Code (already in Test, master variant): `sleeves/midna/board.py` (midna_ema4_vwap), `sleeves/midna/vendor/midna/board_signals.py`
- Strategy card: `strategies/midna/mn-ema4-vwap.md`
- Rule lines: `docs/verify/midna.md` (EMA4 rising VWAP section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: not recorded in the accounting for this id (not in the record); the v3 code evaluates every name in the delivered daily-bars dict, in symbol order.
- Timeframe: 1d. VWAP window: 20 sessions (typical price, volume-weighted).
- Sizing: 1 slot, $1,000. Cadence: 300 s. State: the single held position.
- Accounting entry policy: midna_block, max delay 65 minutes, limit band 5.0%, limit buffer 1.0%, capped_limit_day.

## Data inputs

Completed daily bars with high, low, close and volume for every candidate name (a zero-volume bar in the 20-session window voids that name's VWAP).

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_vwap` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/s_mn_vwap.py`; confirm WINDOW = 20, the typical-price VWAP and SLOT_BUDGET = 1000.0. Serve daily bars per name and call `signal(bars, slice_state, context)` per pass.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A name with under 21 bars, or with a zero-volume bar inside the last 20, produces no cross.
- Entry happens only on the bar where the close moves from at or below VWAP to above it, not while merely above.
- A held name exits on the symmetric down cross and on nothing else.
- No second position opens while one is held; the first up-cross in symbol order wins.
- The entry never exceeds the $1,000 slot budget.
